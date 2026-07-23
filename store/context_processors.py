from django.conf import settings


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
