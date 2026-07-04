#!/usr/bin/env python3
"""
Generador de imágenes de producto EuroPeptiva usando Imagen 3 (Google AI).
Uso:
    python tools/generar_imagenes.py                    # genera todos los productos
    python tools/generar_imagenes.py --producto bpc-157 # genera uno solo
    python tools/generar_imagenes.py --subir            # genera y sube al VPS
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
}

# ── Generador de prompts ─────────────────────────────────────────────────────

def construir_prompt(producto: dict) -> str:
    nombre = producto["nombre"]
    dosis = producto["dosis"]
    tipo = producto["tipo"]
    cas = producto["cas"]
    tapon = producto["tapon"]
    color_texto = producto.get("color_texto", "dark navy (#111f2d)")

    cas_line = f'"CAS: {cas}" in small gray text' if cas else ""

    return f"""Professional pharmaceutical product photography for a scientific research company.
This is one image in a fixed-camera product catalog series — framing must be IDENTICAL to the
other shots in the series, as if the camera and objects were never moved between shots.

CAMERA & COMPOSITION (match exactly, same for every product in the series):
- Fixed eye-level camera, object distance constant, lens equivalent to ~85mm (no wide-angle distortion)
- Box rotated 25° from frontal, showing front face and left side face
- Box occupies the left ~62% of the frame width; vial occupies the right ~30%; ~8% empty gap between them
- Box height fills 78% of frame height, vertically centered, equal margin above and below
- Vial stands upright directly to the right of the box, its base on the exact same ground line as the box's base
- Vial total height (including cap) is about 10% taller than the box, so the cap top sits slightly above the box top
- Vial width is narrow: about half the height-to-width ratio of a standard 10ml glass vial
- Both objects fully in frame with even white margin on all sides — nothing cropped, nothing touching frame edges
- Soft studio lighting from top-left, subtle contact shadow under both objects, pure white seamless background, no gradients, no props, no extra elements

Scene: one white matte branded box on the left and one clear glass research vial on the right,
arranged together on a pure white seamless background with soft studio lighting and subtle drop shadow.

BOX design (white soft-touch matte cardboard):
- Top left corner: small green circle with molecular nodes logo + "EuroPeptiva" in {color_texto} Inter Bold font
- Center large text: "{nombre}" in {color_texto}, Inter Bold, prominent
- Below: "{dosis} · {tipo}" in medium gray, Inter Regular, smaller
- Green rounded pill badge: "≥98% pureza HPLC" in forest green (#1b5e38) on mint (#f0fdf4) background. Render the "≥" (greater-than-or-equal-to) glyph crisply and correctly — do not distort it, drop it, or replace it with another character.
- Bottom small text: "For Research Use Only" in gray
- Left side face: thin vertical green (#1b5e38) stripe accent
- Side face visible: {cas_line}

VIAL design (clear borosilicate glass, upright):
- {tapon} rubber stopper with matching aluminum crimp cap
- White matte label showing: "EuroPeptiva" logo top, "{nombre}" bold in {color_texto}, "{dosis}" gray, "≥98%" green badge (same "≥" glyph requirement as above)
- Small text: "For Research Use Only"

STYLE requirements:
- Color palette strictly: white, {color_texto}, forest green (#1b5e38), mint (#f0fdf4)
- Typography: Inter font family only, no serif fonts
- Background: pure white seamless, no gradients
- Lighting: soft diffused studio light, clean shadows
- Ultra-sharp focus on labels, 4K quality
- Commercial pharmaceutical product photography aesthetic
- No blurry elements, no lens flare, no props
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
    parser.add_argument("--producto", help="Slug del producto (ej: bpc-157). Sin esto genera todos.")
    parser.add_argument("--subir", action="store_true", help="Subir imágenes al VPS tras generar")
    args = parser.parse_args()

    if not API_KEY:
        print("ERROR: Define la variable GOOGLE_API_KEY")
        print("  export GOOGLE_API_KEY=tu_clave_aqui")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.producto:
        if args.producto not in PRODUCTOS:
            print(f"Producto no encontrado: {args.producto}")
            print(f"Disponibles: {', '.join(PRODUCTOS.keys())}")
            sys.exit(1)
        seleccion = {args.producto: PRODUCTOS[args.producto]}
    else:
        seleccion = PRODUCTOS

    generadas = []
    slugs = list(seleccion.items())
    for i, (slug, datos) in enumerate(slugs):
        path = generar_imagen(slug, datos, OUTPUT_DIR)
        if path:
            generadas.append(path)
        if i < len(slugs) - 1:
            import time
            print("  Pausa 15s entre peticiones...")
            time.sleep(15)

    print(f"\n✓ {len(generadas)}/{len(seleccion)} imágenes generadas")

    if args.subir and generadas:
        subir_al_vps(generadas)


if __name__ == "__main__":
    main()
