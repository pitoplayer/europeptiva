#!/usr/bin/env python3
"""
Generador de imágenes de producto EuroPeptiva usando Imagen 3 (Google AI).

Para que las 5 fotos tengan EXACTAMENTE el mismo encuadre (mismo ángulo,
tamaños, márgenes), solo se genera una imagen "maestra" (retatrutide) desde
cero. El resto de productos se generan editando esa imagen maestra —
pidiéndole al modelo que cambie solo el texto/color de la etiqueta y
mantenga la composición y la cámara idénticas.

Uso:
    python tools/generar_imagenes.py --master            # genera la imagen maestra (retatrutide)
    python tools/generar_imagenes.py                     # genera/edita todos los productos a partir de la maestra
    python tools/generar_imagenes.py --producto bpc-157  # genera/edita uno solo
    python tools/generar_imagenes.py --subir              # además, sube al VPS
"""

import argparse
import base64
import os
import subprocess
import sys
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Instala el SDK: pip install google-genai")
    sys.exit(1)

# ── Configuración ────────────────────────────────────────────────────────────

API_KEY = os.environ.get("GOOGLE_API_KEY", "")

VPS_HOST = "root@167.233.169.95"
VPS_SSH_KEY = str(Path.home() / ".ssh/europeptiva_vps")
VPS_MEDIA_PATH = "/home/peptidos/app/media/peptides/"

OUTPUT_DIR = Path(__file__).parent.parent / "media" / "peptides"

MASTER_SLUG = "retatrutide"

# ── Catálogo de productos ────────────────────────────────────────────────────

PRODUCTOS = {
    "retatrutide": {
        "nombre": "Retatrutide",
        "dosis": "10mg",
        "tipo": "Liofilizado",
        "cas": "2381089-83-2",
        "tapon": "dark navy",
    },
    "semaglutide": {
        "nombre": "Semaglutide",
        "dosis": "5mg",
        "tipo": "Liofilizado",
        "cas": "910463-68-2",
        "tapon": "matte black",
        "color_texto": "forest green (#1b5e38)",
    },
    "bpc-157": {
        "nombre": "BPC-157",
        "dosis": "5mg",
        "tipo": "Liofilizado",
        "cas": "137525-51-0",
        "tapon": "dark navy",
    },
    "tb-500": {
        "nombre": "TB-500",
        "dosis": "5mg",
        "tipo": "Liofilizado",
        "cas": "885340-08-9",
        "tapon": "dark navy",
    },
    "bac-water": {
        "nombre": "Bacteriostatic Water",
        "dosis": "10ml",
        "tipo": "Agua bacteriostática 0.9%",
        "cas": None,
        "tapon": "silver",
    },
    "ghk-cu": {
        "nombre": "GHK-Cu",
        "dosis": "50mg",
        "tipo": "Liofilizado",
        "cas": "49557-75-7",
        "tapon": "copper",
    },
    "melanotan-1": {
        "nombre": "Melanotan I",
        "dosis": "10mg",
        "tipo": "Liofilizado",
        "cas": "75921-69-6",
        "tapon": "dark navy",
    },
    "melanotan-2": {
        "nombre": "Melanotan II",
        "dosis": "10mg",
        "tipo": "Liofilizado",
        "cas": "121062-08-6",
        "tapon": "matte black",
        "color_texto": "forest green (#1b5e38)",
    },
    "tesamorelin": {
        "nombre": "Tesamorelin",
        "dosis": "10mg",
        "tipo": "Liofilizado",
        "cas": "218949-48-5",
        "tapon": "dark navy",
    },
    "semax": {
        "nombre": "Semax",
        "dosis": "10mg",
        "tipo": "Spray nasal",
        "cas": "80714-61-0",
        "tapon": "silver",
    },
    "selank": {
        "nombre": "Selank",
        "dosis": "10mg",
        "tipo": "Spray nasal",
        "cas": "129954-34-3",
        "tapon": "silver",
    },
}

# ── Generador de prompts ─────────────────────────────────────────────────────

def construir_prompt(producto: dict) -> str:
    nombre = producto["nombre"]
    dosis = producto["dosis"]
    tipo = producto["tipo"]
    cas = producto["cas"]
    tapon = producto["tapon"]
    color_texto = producto.get("color_texto", "dark navy (#111f2d)")

    cas_line = f'Small gray text near the bottom of the label: "CAS: {cas}"' if cas else ""

    return f"""Professional pharmaceutical product photography for a scientific research company.
This is one image in a fixed-camera product catalog series — framing must be IDENTICAL to the
other shots in the series, as if the camera and object were never moved between shots.

CAMERA & COMPOSITION (match exactly, same for every product in the series):
- Fixed eye-level camera, object distance constant, lens equivalent to ~85mm (no wide-angle distortion)
- Single clear glass research vial, standing upright, centered horizontally in the frame
- Vial rotated very slightly (~10°) so the label reads naturally while a hint of the round glass body shows
- Vial height (including cap) fills about 80% of the frame height, vertically centered with equal margin above and below
- Vial fully in frame with even white margin on all sides — nothing cropped, nothing touching frame edges
- Soft studio lighting from top-left, subtle contact shadow under the vial, pure white seamless background, no gradients, no props, no extra elements, no box, no packaging of any kind

Scene: one clear glass research vial alone on a pure white seamless background with soft studio
lighting and a subtle drop shadow.

VIAL design (clear borosilicate glass, upright):
- {tapon} rubber stopper with matching aluminum crimp cap
- White matte label wrapped around the vial showing, top to bottom: small green circle with molecular
  nodes logo + "EuroPeptiva" in {color_texto} Inter Bold font; "{nombre}" bold in {color_texto}, Inter
  Bold, prominent; "{dosis} · {tipo}" in medium gray, Inter Regular, smaller; a green rounded pill badge
  "≥98% pureza HPLC" in forest green (#1b5e38) on mint (#f0fdf4) background (render the "≥" glyph
  crisply and correctly — do not distort it, drop it, or replace it with another character); small
  gray text "For Research Use Only" near the bottom
- {cas_line}

STYLE requirements:
- Color palette strictly: white, {color_texto}, forest green (#1b5e38), mint (#f0fdf4)
- Typography: Inter font family only, no serif fonts
- Background: pure white seamless, no gradients
- Lighting: soft diffused studio light, clean shadows
- Ultra-sharp focus on the label, 4K quality
- Commercial pharmaceutical product photography aesthetic
- No blurry elements, no lens flare, no props, no box or packaging visible anywhere in the frame
"""


def construir_prompt_edicion(producto: dict, master: dict) -> str:
    nombre = producto["nombre"]
    dosis = producto["dosis"]
    tipo = producto["tipo"]
    cas = producto["cas"]
    tapon = producto["tapon"]
    color_texto = producto.get("color_texto", "dark navy (#111f2d)")

    master_nombre = master["nombre"]
    master_dosis = master["dosis"]
    master_tipo = master["tipo"]
    master_cas = master["cas"]
    master_tapon = master["tapon"]
    master_color = master.get("color_texto", "dark navy (#111f2d)")

    cas_instruccion = (
        f'Replace the CAS text on the label with "CAS: {cas}", same small gray font and position.'
        if cas
        else 'Remove the CAS text from the label entirely, leave that area blank white.'
    )

    cambios = [
        f'Replace every occurrence of the product name "{master_nombre}" with "{nombre}" on the vial label, same font, weight and position.',
        f'Replace the dosage line "{master_dosis} · {master_tipo}" with "{dosis} · {tipo}" on the vial label.',
        cas_instruccion,
    ]
    if color_texto != master_color:
        cambios.append(
            f'Change the label/text color from {master_color} to {color_texto} everywhere it appears on the vial label (logo wordmark, product name, "EuroPeptiva" text) — keep every other color (green badge, gray subtext, mint background) unchanged.'
        )
    if tapon != master_tapon:
        cambios.append(
            f'Change the vial rubber stopper and aluminum crimp cap material/color from {master_tapon} to {tapon}, keeping the same cap shape and size.'
        )

    cambios_texto = "\n".join(f"- {c}" for c in cambios)

    return f"""Edit this reference product photo for "EuroPeptiva" pharmaceutical research products.

CRITICAL: Do NOT change the camera angle, vial tilt, object proportions, position, spacing,
margins, lighting, shadows, or white background in any way. The composition must stay pixel-for-pixel
identical to the reference image — this is one shot in a fixed-camera catalog series and every
product must look like it was photographed in the exact same setup. Do NOT add a box or any
packaging — only the single vial from the reference image.

Only make these text/label changes:
{cambios_texto}

Render the "≥" (greater-than-or-equal-to) glyph crisply and correctly wherever it appears — do not
distort it, drop it, or replace it with another character.

Everything else — vial shape, logo icon, badge shape, layout, fonts, lighting, shadow,
background — must remain exactly as in the reference image.
"""


# ── Generación con Gemini Image ──────────────────────────────────────────────

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SIGNATURE = b"\xff\xd8\xff"
MIN_IMAGE_BYTES = 20_000  # una foto de producto real no baja de esto


def _es_imagen_valida(data: bytes) -> bool:
    return data.startswith(PNG_SIGNATURE) or data.startswith(JPEG_SIGNATURE)


def _a_png(data: bytes) -> bytes:
    """El modelo a veces devuelve JPEG; el proyecto sirve todo como .png."""
    if data.startswith(PNG_SIGNATURE):
        return data
    import io
    from PIL import Image
    buf = io.BytesIO()
    Image.open(io.BytesIO(data)).convert("RGB").save(buf, format="PNG")
    return buf.getvalue()


def _extraer_imagen(response) -> bytes | None:
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            data = part.inline_data.data
            # El SDK a veces entrega bytes ya decodificados y a veces un
            # string base64; si ya trae una firma de imagen conocida no hay
            # que volver a decodificar (evita corromper la imagen).
            if isinstance(data, bytes) and _es_imagen_valida(data):
                return data
            import base64
            try:
                decoded = base64.b64decode(data)
            except Exception:
                return None
            return decoded
    return None


def generar_imagen(slug: str, producto: dict, output_dir: Path) -> Path | None:
    print(f"\n→ Generando: {producto['nombre']}...")

    prompt = construir_prompt(producto)
    client = genai.Client(api_key=API_KEY)

    for intento in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-image",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                ),
            )
        except Exception as e:
            if "429" in str(e) and intento < 2:
                espera = 30 * (intento + 1)
                print(f"  Límite de velocidad, esperando {espera}s...")
                import time
                time.sleep(espera)
                continue
            print(f"  ERROR al generar {slug}: {e}")
            return None

        img_data = _extraer_imagen(response)

        if not img_data:
            print(f"  Sin imagen generada para {slug} (intento {intento + 1}/3)")
        elif not _es_imagen_valida(img_data) or len(img_data) < MIN_IMAGE_BYTES:
            print(f"  Respuesta invalida/corrupta para {slug} ({len(img_data)} bytes, intento {intento + 1}/3)")
        else:
            png_data = _a_png(img_data)
            output_path = output_dir / f"{slug}.png"
            output_path.write_bytes(png_data)
            print(f"  Guardada: {output_path} ({len(png_data) // 1024} KB)")
            return output_path

        if intento < 2:
            import time
            time.sleep(10)

    print(f"  FALLO: no se pudo generar una imagen valida para {slug} tras 3 intentos")
    return None


def editar_imagen(slug: str, producto: dict, master: dict, referencia_bytes: bytes, output_dir: Path) -> Path | None:
    print(f"\n→ Editando a partir de la maestra: {producto['nombre']}...")

    prompt = construir_prompt_edicion(producto, master)
    client = genai.Client(api_key=API_KEY)
    imagen_ref = types.Part.from_bytes(data=referencia_bytes, mime_type="image/png")

    for intento in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-image",
                contents=[imagen_ref, prompt],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                ),
            )
        except Exception as e:
            if "429" in str(e) and intento < 2:
                espera = 30 * (intento + 1)
                print(f"  Límite de velocidad, esperando {espera}s...")
                import time
                time.sleep(espera)
                continue
            print(f"  ERROR al editar {slug}: {e}")
            return None

        img_data = _extraer_imagen(response)

        if not img_data:
            print(f"  Sin imagen generada para {slug} (intento {intento + 1}/3)")
        elif not _es_imagen_valida(img_data) or len(img_data) < MIN_IMAGE_BYTES:
            print(f"  Respuesta invalida/corrupta para {slug} ({len(img_data)} bytes, intento {intento + 1}/3)")
        else:
            png_data = _a_png(img_data)
            output_path = output_dir / f"{slug}.png"
            output_path.write_bytes(png_data)
            print(f"  Guardada: {output_path} ({len(png_data) // 1024} KB)")
            return output_path

        if intento < 2:
            import time
            time.sleep(10)

    print(f"  FALLO: no se pudo editar una imagen valida para {slug} tras 3 intentos")
    return None


# ── Subida al VPS ─────────────────────────────────────────────────────────────

def subir_al_vps(paths: list[Path]) -> None:
    print("\n→ Subiendo al VPS...")
    for path in paths:
        cmd = [
            "scp", "-i", VPS_SSH_KEY,
            str(path),
            f"{VPS_HOST}:{VPS_MEDIA_PATH}{path.name}",
        ]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0:
            print(f"  OK: {path.name}")
        else:
            print(f"  ERROR: {path.name} — {result.stderr.decode()}")

    # Asignar en Django (solo las que se subieron con exito)
    print("\n→ Asignando imágenes en Django...")
    script = "from store.models import Peptide\n"
    for path in paths:
        slug = path.stem
        img_path = f"peptides/{slug}.png"
        script += (
            f'p = Peptide.objects.filter(slug="{slug}").first()\n'
            f'p and (setattr(p, "main_image", "{img_path}") or p.save()) and print("OK: {slug}")\n'
        )

    # Se pasa el script por stdin en vez de -c para evitar romper el quoting
    # anidado (bash -c '...' + python -c "...") cuando el script contiene comillas.
    cmd = [
        "ssh", "-i", VPS_SSH_KEY, VPS_HOST,
        "sudo -u peptidos bash -c 'cd /home/peptidos/app && venv/bin/python manage.py shell'",
    ]
    subprocess.run(cmd, input=script.encode())


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generador de imágenes EuroPeptiva")
    parser.add_argument("--producto", help="Slug del producto (ej: bpc-157). Sin esto genera/edita todos.")
    parser.add_argument("--master", action="store_true", help=f"Regenerar desde cero la imagen maestra ({MASTER_SLUG})")
    parser.add_argument("--subir", action="store_true", help="Subir imágenes al VPS tras generar")
    args = parser.parse_args()

    if not API_KEY:
        print("ERROR: Define la variable GOOGLE_API_KEY")
        print("  export GOOGLE_API_KEY=tu_clave_aqui")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.producto and args.producto not in PRODUCTOS:
        print(f"Producto no encontrado: {args.producto}")
        print(f"Disponibles: {', '.join(PRODUCTOS.keys())}")
        sys.exit(1)

    # Slugs a procesar en esta tirada.
    if args.producto:
        objetivo = [args.producto]
    else:
        objetivo = list(PRODUCTOS.keys())

    generadas = []
    pendientes = 0

    # La maestra se genera desde cero (texto→imagen); el resto se edita a
    # partir de ella para que el encuadre sea idéntico en todo el catálogo.
    if MASTER_SLUG in objetivo or args.master:
        pendientes += 1
        path = generar_imagen(MASTER_SLUG, PRODUCTOS[MASTER_SLUG], OUTPUT_DIR)
        if path:
            generadas.append(path)

    a_editar = [slug for slug in objetivo if slug != MASTER_SLUG]

    if a_editar:
        master_path = OUTPUT_DIR / f"{MASTER_SLUG}.png"
        if not master_path.exists():
            print(f"ERROR: no existe la imagen maestra ({master_path}). Genérala primero con --master.")
            sys.exit(1)
        referencia_bytes = master_path.read_bytes()

        for i, slug in enumerate(a_editar):
            pendientes += 1
            path = editar_imagen(slug, PRODUCTOS[slug], PRODUCTOS[MASTER_SLUG], referencia_bytes, OUTPUT_DIR)
            if path:
                generadas.append(path)
            if i < len(a_editar) - 1:
                import time
                print("  Pausa 15s entre peticiones...")
                time.sleep(15)

    print(f"\n✓ {len(generadas)}/{pendientes} imágenes generadas")

    if args.subir and generadas:
        subir_al_vps(generadas)


if __name__ == "__main__":
    main()
