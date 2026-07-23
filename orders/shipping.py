from decimal import Decimal

# Umbral único de envío gratis para todos los destinos.
FREE_SHIPPING_THRESHOLD = Decimal('150.00')

# Hora límite (24h) para que un pedido salga el mismo día, y días en que aplica.
SAME_DAY_CUTOFF_HOUR = 12
SAME_DAY_DAYS_SHORT = 'L–S'
SAME_DAY_DAYS_LONG = 'de lunes a sábado'

SHIPPING_RATES = {
    'ESP': {
        'standard': Decimal('7.99'),
        'free_threshold': FREE_SHIPPING_THRESHOLD,
    },
    'EU': {
        'standard': Decimal('12.99'),
        'free_threshold': FREE_SHIPPING_THRESHOLD,
    },
}


def calculate_shipping(country_code, subtotal):
    rates = SHIPPING_RATES.get(country_code, SHIPPING_RATES['EU'])
    if subtotal >= rates['free_threshold']:
        return Decimal('0.00')
    return rates['standard']


def amount_missing_for_free_shipping(subtotal):
    """Cuánto falta para el envío gratis, o None si ya se ha alcanzado."""
    missing = FREE_SHIPPING_THRESHOLD - subtotal
    return missing if missing > 0 else None
