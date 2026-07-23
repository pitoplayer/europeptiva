"""Marca el formato de cada producto y saca la conservación de la descripción.

Hasta ahora cada descripción terminaba con su párrafo de conservación
("Conservar refrigerado y protegido de la luz…"). Ese texto pasa a ser un
bloque propio de la ficha, generado desde `store/product_content.py` según el
formato del producto, así que dejarlo también en `description` lo pintaría dos
veces en la misma página.

El formato solo se marca para las excepciones: el default del campo ya es
`vial`, que es lo que son 15 de los 18 productos.
"""

from django.db import migrations

FORMATOS = {
    'semax': 'spray',
    'selank': 'spray',
    'bac-water': 'solvent',
}

# Para poder deshacer la migración sin perder el texto.
CONSERVACION = {
    'vial': {
        'es': "Conservar refrigerado y protegido de la luz. Reconstituir con BAC Water estéril.",
        'en': "Store refrigerated and protected from light. Reconstitute with sterile BAC Water.",
    },
    'spray': {
        'es': "Conservar refrigerado y protegido de la luz.",
        'en': "Store refrigerated and protected from light.",
    },
    'solvent': {
        'es': "Conservar en lugar fresco y protegido de la luz. Usar dentro de los 28 días tras abrir el vial.",
        'en': "Store in a cool place, protected from light. Use within 28 days of opening the vial.",
    },
}

CAMPOS = ['description', 'description_es', 'description_en']

# Se corta por el arranque del párrafo y no por el texto exacto: así un
# producto al que le hayan retocado la frase a mano también queda limpio.
INICIOS = ('Conservar ', 'Store ')


def sin_parrafo_de_conservacion(texto):
    if not texto:
        return texto
    parrafos = texto.split('\n\n')
    if len(parrafos) > 1 and parrafos[-1].strip().startswith(INICIOS):
        return '\n\n'.join(parrafos[:-1]).rstrip()
    return texto


def limpiar(apps, schema_editor):
    Peptide = apps.get_model('store', 'Peptide')
    for peptide in Peptide.objects.all():
        peptide.product_format = FORMATOS.get(peptide.slug, 'vial')
        for campo in CAMPOS:
            setattr(peptide, campo, sin_parrafo_de_conservacion(getattr(peptide, campo)))
        peptide.save(update_fields=['product_format'] + CAMPOS)


def restaurar(apps, schema_editor):
    Peptide = apps.get_model('store', 'Peptide')
    for peptide in Peptide.objects.all():
        textos = CONSERVACION[peptide.product_format or 'vial']
        for campo, idioma in (('description', 'es'), ('description_es', 'es'), ('description_en', 'en')):
            actual = getattr(peptide, campo)
            if actual and not actual.rstrip().endswith(textos[idioma]):
                setattr(peptide, campo, f"{actual.rstrip()}\n\n{textos[idioma]}")
        peptide.save(update_fields=CAMPOS)


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0008_peptide_product_format_peptide_research_background_and_more'),
    ]

    operations = [
        migrations.RunPython(limpiar, restaurar),
    ]
