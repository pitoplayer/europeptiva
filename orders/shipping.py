from decimal import Decimal

SHIPPING_RATES = {
    'ESP': {
        'standard': Decimal('5.90'),
        'express': Decimal('9.90'),
        'free_threshold': Decimal('80.00'),
    },
    'EU': {
        'standard': Decimal('14.90'),
        'free_threshold': Decimal('150.00'),
    },
}


def calculate_shipping(country_code, subtotal):
    rates = SHIPPING_RATES.get(country_code, SHIPPING_RATES['EU'])
    if subtotal >= rates['free_threshold']:
        return Decimal('0.00')
    return rates['standard']
