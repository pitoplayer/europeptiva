from django import template
from django.urls import translate_url as _translate_url

register = template.Library()


@register.simple_tag
def translate_url(url, lang_code):
    """Misma página en otro idioma.

    django.urls.translate_url resuelve la URL, la vuelve a construir con el
    idioma pedido y devuelve la original si no hay equivalente. Django trae la
    función pero no la etiqueta de plantilla, de ahí este envoltorio: lo usan
    los hreflang de base.html y el selector de idioma de la cabecera.
    """
    return _translate_url(url, lang_code)
