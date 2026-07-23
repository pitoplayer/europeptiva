"""Bloques de reconstitución y conservación de la ficha de producto.

Son protocolo, no marketing: el mismo para todos los productos del mismo
formato. Duplicarlos en la BD significaría mantener el mismo párrafo en 15
filas y en dos idiomas, así que viven aquí y la ficha elige el bloque con
`Peptide.product_format`.

Todo en pasado/impersonal y sin dosis ni instrucciones de uso humano: se
describe cómo se maneja un reactivo de laboratorio, no cómo se administra.
"""

from django.utils.translation import gettext_lazy as _


HANDLING = {
    'vial': [
        _("Trabaja sobre superficie limpia y desinfecta el tapón del vial con una toallita de alcohol antes de perforarlo."),
        _("Añade el agua bacteriostática despacio, dejándola resbalar por la pared interior del vial en lugar de caer sobre el polvo."),
        _("No agites. Gira el vial con suavidad hasta que el liofilizado se disuelva del todo: la agitación fuerte degrada el péptido."),
        _("La solución debe quedar transparente. Si sale turbia o con partículas en suspensión, no la utilices."),
    ],
    'spray': [
        _("Llega en solución y listo para usar: no hay que reconstituir nada."),
        _("No lo diluyas ni lo mezcles con otras soluciones."),
        _("Mantén la boquilla limpia y no la intercambies entre viales."),
    ],
    'solvent': [
        _("Desinfecta el tapón con una toallita de alcohol antes de cada extracción."),
        _("Extrae solo el volumen que vayas a usar, siempre con aguja y jeringa estériles nuevas."),
        _("El 0,9 % de alcohol bencílico es lo que permite perforar el mismo vial varias veces sin que se contamine."),
    ],
}

STORAGE = {
    'vial': [
        _("Sin reconstituir: refrigerado entre 2 y 8 °C, protegido de la luz y de la humedad."),
        _("Ya reconstituido: en nevera y a resguardo de la luz. En solución el péptido aguanta mucho menos que en polvo, así que conviene usarlo pronto."),
        _("Evita los ciclos de congelación y descongelación."),
    ],
    'spray': [
        _("Refrigerado entre 2 y 8 °C y protegido de la luz."),
        _("Devuélvelo a la nevera después de cada uso. No lo congeles."),
    ],
    'solvent': [
        _("En lugar fresco y protegido de la luz. Sin abrir no necesita nevera."),
        _("Una vez perforado el vial, utilízalo dentro de los 28 días siguientes."),
    ],
}

# Etiqueta corta para las tarjetas del catálogo, debajo de los mg.
FORMAT_LABEL = {
    'vial': _("liofilizado"),
    'spray': _("spray listo para usar"),
    'solvent': _("estéril"),
}

# Título del bloque de manipulación: en el spray y en el disolvente no se
# reconstituye nada, así que llamarlo "Reconstitución" sería mentira.
HANDLING_TITLE = {
    'vial': _("Reconstitución y manipulación"),
    'spray': _("Manipulación"),
    'solvent': _("Manipulación"),
}


def handling_block(product_format):
    return {
        'title': HANDLING_TITLE.get(product_format, HANDLING_TITLE['vial']),
        'items': HANDLING.get(product_format, HANDLING['vial']),
    }


def storage_block(product_format):
    return {
        'title': _("Conservación y estabilidad"),
        'items': STORAGE.get(product_format, STORAGE['vial']),
    }
