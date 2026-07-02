"""
Sincronización de precios y stock con Peptaura.

Peptaura no tiene API pública documentada — este script usa web scraping
sobre las páginas de producto. Ejecutar con:

    python manage.py shell < automation/peptaura_sync.py

O como tarea cron semanal en el VPS:

    0 6 * * 1 cd /home/peptidos/app && source venv/bin/activate && python manage.py shell < automation/peptaura_sync.py >> /var/log/peptaura_sync.log 2>&1

IMPORTANTE: Antes de usar en producción, verificar que el scraping
cumple con los términos de servicio de Peptaura. Alternativa: contactar
a Peptaura para pedir acceso a su API o feed de precios.
"""

import sys
import os
import django

# Solo si se ejecuta directamente (no desde manage.py shell)
if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

import logging
import time
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError
from html.parser import HTMLParser

logger = logging.getLogger(__name__)

# Mapa: nombre_en_nuestra_bd -> URL producto en Peptaura
# Rellenar con las URLs reales de cada producto tras revisar el catálogo
PEPTAURA_PRODUCTS = {
    'Retatrutide': None,   # TODO: añadir URL de Peptaura
    'Semaglutide': None,
    'BPC-157': None,
    'TB-500': None,
    'BAC Water': None,
}


class PeptauraPriceParser(HTMLParser):
    """Parser HTML simple para extraer precio de Peptaura."""

    def __init__(self):
        super().__init__()
        self.prices = []
        self._in_price = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        # Peptaura suele usar clases como 'price', 'product-price', etc.
        # Ajustar según la estructura real del HTML de Peptaura
        classes = attrs_dict.get('class', '')
        if tag in ('span', 'p', 'div') and any(kw in classes for kw in ('price', 'precio', 'cost')):
            self._in_price = True

    def handle_endtag(self, tag):
        self._in_price = False

    def handle_data(self, data):
        if self._in_price:
            data = data.strip()
            if data and any(c.isdigit() for c in data):
                self.prices.append(data)


def fetch_peptaura_price(url: str) -> float | None:
    """Obtiene el precio más bajo de un producto en Peptaura."""
    if not url:
        return None

    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (research price tracker)'})
        with urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')

        parser = PeptauraPriceParser()
        parser.feed(html)

        prices = []
        for p in parser.prices:
            # Limpiar string de precio: "29,90 €" -> 29.90
            cleaned = p.replace('€', '').replace(',', '.').strip()
            try:
                prices.append(float(cleaned))
            except ValueError:
                pass

        return min(prices) if prices else None

    except URLError as e:
        logger.warning(f"Error fetching {url}: {e}")
        return None


def sync_prices():
    """Sincroniza precios de Peptaura con la base de datos."""
    from store.models import Peptide, PeptideVariant

    results = {'updated': 0, 'skipped': 0, 'errors': 0}
    print(f"\n[{datetime.now():%Y-%m-%d %H:%M}] Iniciando sincronización con Peptaura...")

    for product_name, url in PEPTAURA_PRODUCTS.items():
        if not url:
            print(f"  ⏭  {product_name}: URL no configurada, saltando")
            results['skipped'] += 1
            continue

        try:
            peptide = Peptide.objects.get(name__icontains=product_name)
        except Peptide.DoesNotExist:
            print(f"  ⚠  {product_name}: no encontrado en base de datos")
            results['errors'] += 1
            continue

        price = fetch_peptaura_price(url)
        if price is None:
            print(f"  ⚠  {product_name}: no se pudo obtener precio de Peptaura")
            results['errors'] += 1
        else:
            # Aplicar margen del 40% sobre el precio de Peptaura
            our_price = round(price * 1.40, 2)
            variants = PeptideVariant.objects.filter(peptide=peptide, is_active=True)
            for variant in variants:
                old_price = float(variant.price)
                variant.price = our_price
                variant.save()
                print(f"  ✓  {product_name} {variant.size_mg}mg: {old_price}€ → {our_price}€")
            results['updated'] += 1

        time.sleep(2)  # Rate limiting educado

    print(f"\nResultados: {results['updated']} actualizados, {results['skipped']} saltados, {results['errors']} errores")
    return results


if __name__ == '__main__':
    sync_prices()
