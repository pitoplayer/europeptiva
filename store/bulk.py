"""Configuración de la compra al por mayor.

Los descuentos son ORIENTATIVOS: el precio final siempre sale de un
presupuesto manual, no se aplican solos en el carrito. Para cambiarlos basta
con tocar esta lista.
"""

BULK_TIERS = [
    {'min_units': 10, 'discount': 15},
    {'min_units': 20, 'discount': 20},
    {'min_units': 30, 'discount': 25},
]

# Unidades mínimas para pedir presupuesto (el primer tramo).
BULK_MIN_UNITS = BULK_TIERS[0]['min_units']
