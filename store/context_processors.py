from django.conf import settings

from orders.shipping import (
    FREE_SHIPPING_THRESHOLD,
    SAME_DAY_CUTOFF_HOUR,
    SAME_DAY_DAYS_LONG,
    SAME_DAY_DAYS_SHORT,
    SHIPPING_RATES,
)


def shipping_info(request):
    """Condiciones de envío para las plantillas.

    Salen de orders/shipping.py, que es lo que cobra el checkout: así lo que
    anunciamos y lo que cobramos no pueden desincronizarse.
    """
    return {
        'shipping_free_from': FREE_SHIPPING_THRESHOLD,
        'shipping_cost_es': SHIPPING_RATES['ESP']['standard'],
        'shipping_cost_eu': SHIPPING_RATES['EU']['standard'],
        'shipping_cutoff_hour': SAME_DAY_CUTOFF_HOUR,
        'shipping_cutoff_days': SAME_DAY_DAYS_SHORT,
        'shipping_cutoff_days_long': SAME_DAY_DAYS_LONG,
    }


def cart_count(request):
    cart = request.session.get('cart', {})
    count = sum(item.get('quantity', 0) for item in cart.values())
    return {'cart_count': count}


def legal_data(request):
    """Datos fiscales del titular para el aviso legal y la política de privacidad."""
    return {
        'legal_name': settings.LEGAL_NAME,
        'legal_nif': settings.LEGAL_NIF,
        'legal_address': settings.LEGAL_ADDRESS,
        'legal_postcode': settings.LEGAL_POSTCODE,
        'legal_city': settings.LEGAL_CITY,
        'legal_email': settings.LEGAL_EMAIL,
        # Los defaults van entre corchetes: si queda alguno, los datos siguen sin rellenar
        'legal_data_configured': '[' not in (
            settings.LEGAL_NAME + settings.LEGAL_NIF + settings.LEGAL_ADDRESS
        ),
    }
