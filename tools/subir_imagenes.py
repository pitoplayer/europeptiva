#!/usr/bin/env python3
"""
Sube imágenes de productos al VPS y las asigna en Django.
Uso: pon los archivos en /home/kaliuser/agentes-ia/europeptiva/ con nombre:
    retatrutide.png, semaglutide.png, bpc-157.png, tb-500.png, bac-water.png
Luego ejecuta: python3 tools/subir_imagenes.py
"""

import subprocess
from pathlib import Path

VPS_HOST = "root@167.233.169.95"
VPS_SSH_KEY = str(Path.home() / ".ssh/europeptiva_vps")
VPS_MEDIA_PATH = "/home/peptidos/app/media/peptides/"
ORIGEN = Path("/home/kaliuser/agentes-ia/europeptiva")

SLUGS = ["retatrutide", "semaglutide", "bpc-157", "tb-500", "bac-water"]

def subir():
    subidas = []
    for slug in SLUGS:
        for ext in ["png", "jpg", "jpeg", "webp"]:
            src = ORIGEN / f"{slug}.{ext}"
            if src.exists():
                print(f"→ Subiendo {src.name}...")
                r = subprocess.run(
                    ["scp", "-i", VPS_SSH_KEY, str(src), f"{VPS_HOST}:{VPS_MEDIA_PATH}{slug}.png"],
                    capture_output=True
                )
                if r.returncode == 0:
                    print(f"  OK")
                    subidas.append(slug)
                else:
                    print(f"  ERROR: {r.stderr.decode()}")
                break
        else:
            print(f"  Sin archivo para: {slug}")

    if not subidas:
        print("\nNada que subir.")
        return

    print(f"\n→ Asignando en Django ({len(subidas)} productos)...")
    lines = ["from store.models import Peptide"]
    for slug in subidas:
        lines.append(f'p = Peptide.objects.filter(slug="{slug}").first()')
        lines.append(f'p and (setattr(p, "main_image", "peptides/{slug}.png") or p.save()) and print("OK: {slug}")')
    script = "\n".join(lines) + "\n"

    # Se pasa el script por stdin en vez de -c para evitar romper el quoting
    # anidado (bash -c '...' + python -c "...") cuando el script contiene comillas.
    subprocess.run(
        ["ssh", "-i", VPS_SSH_KEY, VPS_HOST,
         "sudo -u peptidos bash -c 'cd /home/peptidos/app && venv/bin/python manage.py shell'"],
        input=script.encode(),
    )
    print("\nListo. Verifica en https://europeptiva.com/catalogo")

if __name__ == "__main__":
    subir()
