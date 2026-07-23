from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def euros(value):
    """Formatea un importe al estilo español: 7,99 € y 150 € (sin decimales si son cero)."""
    try:
        amount = Decimal(value)
    except (TypeError, ValueError, InvalidOperation):
        return value
    if amount == amount.to_integral_value():
        return f'{amount.to_integral_value():.0f} €'
    return f'{amount:.2f}'.replace('.', ',') + ' €'
