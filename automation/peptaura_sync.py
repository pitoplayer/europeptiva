"""
Vigilancia de precios de Peptaura (informativo — NO actualiza precios solo).

Peptaura no tiene API pública documentada, pero cada página de catálogo
incluye un bloque <script type="application/ld+json"> con schema.org
Product/Offer que lista precio, disponibilidad y proveedor de cada
listado — mucho más fiable de parsear que el HTML visible.

LIMITACIÓN IMPORTANTE (verificada manualmente en julio 2026): en la misma
página conviven listados por "1 vial" y por "Box of 10 vials" según el
proveedor, y esa unidad de venta NO aparece en el JSON-LD — solo en un
texto renderizado por React que no se puede correlacionar de forma fiable
con cada oferta por scraping simple. Por eso este script NO calcula ni
aplica un precio de venta automáticamente: solo informa del precio mínimo
en bruto encontrado por talla y el enlace al listado, para que se revise
a mano en la web antes de tocar los precios de la tienda.

Uso:
    python manage.py shell < automation/peptaura_sync.py

Si en el futuro se verifica la unidad de venta de forma fiable (por
ejemplo tras confirmarlo con Peptaura o inspeccionando el DOM manualmente
producto a producto), se puede extender este script para proponer un
precio de venta automático — hasta entonces, tratarlo solo como alerta.
"""

import sys
import os
import django

# Solo si se ejecuta directamente (no desde manage.py shell)
if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

import json
import logging
import re
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError

logger = logging.getLogger(__name__)

# Mapa: nombre_en_nuestra_bd -> URL del catálogo del producto en Peptaura
PEPTAURA_PRODUCTS = {
    'Retatrutide': 'https://www.peptaura.com/catalog/Retatrutide',
    'Semaglutide': 'https://www.peptaura.com/catalog/SEMAGLUTIDE',
    'BPC-157': 'https://www.peptaura.com/catalog/BPC-157',
    'TB-500': 'https://www.peptaura.com/catalog/TB500',
    'BAC Water': 'https://www.peptaura.com/catalog/BAC%20WATER',
}

SIZE_RE = re.compile(r'-(\d+)(?:mg|ml)-', re.IGNORECASE)
JSON_LD_RE = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.DOTALL)


def fetch_peptaura_offers(url: str) -> dict[int, dict]:
    """Devuelve {tamaño: {'price_usd': min, 'url': oferta, 'seller': nombre}}.

    price_usd es el precio en bruto tal cual lo publica Peptaura — puede
    ser por vial suelto o por caja de 10 según el proveedor (ver docstring
    del módulo). Verificar la unidad abriendo 'url' antes de usarlo.
    """
    if not url:
        return {}

    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (research price tracker)'})
        with urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
    except URLError as e:
        logger.warning(f"Error obteniendo {url}: {e}")
        return {}

    best_by_size: dict[int, dict] = {}

    for block in JSON_LD_RE.findall(html):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        if data.get('@type') != 'Product':
            continue

        for offer in data.get('offers', []):
            offer_url = offer.get('url', '')
            price_raw = offer.get('price')
            match = SIZE_RE.search(offer_url)
            if not match or price_raw is None:
                continue
            try:
                size = int(match.group(1))
                price = float(price_raw)
            except (ValueError, TypeError):
                continue

            if size not in best_by_size or price < best_by_size[size]['price_usd']:
                best_by_size[size] = {
                    'price_usd': price,
                    'url': offer_url,
                    'seller': (offer.get('seller') or {}).get('name', '?'),
                }

    return best_by_size


def check_prices():
    """Informa del precio mínimo publicado por Peptaura para cada variante,
    comparado con nuestro precio actual. No modifica la base de datos."""
    from store.models import Peptide

    print(f"\n[{datetime.now():%Y-%m-%d %H:%M}] Comprobando precios en Peptaura (solo informativo)...")

    for product_name, url in PEPTAURA_PRODUCTS.items():
        try:
            peptide = Peptide.objects.get(name__icontains=product_name)
        except Peptide.DoesNotExist:
            print(f"  ⚠  {product_name}: no encontrado en base de datos")
            continue

        offers = fetch_peptaura_offers(url)
        if not offers:
            print(f"  ⚠  {product_name}: no se pudieron obtener precios de Peptaura")
            continue

        for variant in peptide.variants.filter(is_active=True):
            offer = offers.get(variant.size_mg)
            if offer is None:
                print(f"  —  {product_name} {variant.size_mg}mg: sin listado equivalente en Peptaura")
                continue
            print(
                f"  ·  {product_name} {variant.size_mg}mg: nuestro precio {variant.price}€ "
                f"| Peptaura desde ${offer['price_usd']:.2f} ({offer['seller']}) — {offer['url']}"
            )

    print("\nRevisa manualmente los enlaces antes de cambiar cualquier precio de la tienda.")


if __name__ == '__main__':
    check_prices()
