"""Reorganiza las categorías con la estructura de PurityBase.

PurityBase separa dos ejes que aquí estaban mezclados en uno solo:

  - **Formato** (nivel de arriba): Peptides, Nasal Sprays, Research Supplies…
  - **Objetivo** (filtro dentro de Peptides): Weight Management, Hair & Skin,
    Recovery & Repair, Healthy Aging, Cognitive, Blends…

El formato ya lo teníamos en `Peptide.product_format`, así que esta migración
solo toca el eje de objetivo: `Category` deja de mezclar ambos (tenía
"Spray Nasal", que es formato, junto a "Pérdida de Grasa", que es objetivo) y
pasa a ser exclusivamente el objetivo, con los nombres de PurityBase.

Dos consecuencias:
  - "Spray Nasal" desaparece como categoría: Semax y Selank pasan a "Cognitivo"
    y se siguen agrupando por formato vía `product_format='spray'`.
  - Los blends salen de la categoría de su ingrediente principal y se juntan en
    "Blends", igual que en PurityBase.

Ojo con modeltranslation: el `name` que lee el ORM sale de `name_es`/`name_en`,
no de la columna `name`. Escribir solo `name` deja el cambio invisible en la
web — hay que escribir las tres.

Los slugs cambian. No hacen falta redirecciones: el lanzamiento está aplazado y
la web no tiene tráfico indexado todavía.
"""
from django.db import migrations


# slug viejo -> (slug nuevo, es, en, descripcion_es, descripcion_en)
# Los nombres en inglés son los de PurityBase tal cual; los españoles, su
# equivalente. "Blends" se deja igual en ambos: es como se llama el formato en
# el sector y traducirlo por "Mezclas" lo haría menos reconocible.
RENOMBRAR = {
    'perdida-de-grasa': (
        'control-de-peso', 'Control de peso', 'Weight Management',
        'Péptidos investigados en el ámbito del metabolismo, la composición corporal y el control de peso.',
        'Peptides researched in the fields of metabolism, body composition and weight management.',
    ),
    'recuperacion': (
        'recuperacion-y-reparacion', 'Recuperación y reparación', 'Recovery & Repair',
        None, None,
    ),
    'cabello-piel': (
        'cabello-y-piel', 'Cabello y piel', 'Hair & Skin',
        None, None,
    ),
    'longevidad-antienvejecimiento': (
        'envejecimiento-saludable', 'Envejecimiento saludable', 'Healthy Aging',
        None, None,
    ),
    'disolventes-auxiliares': (
        'suministros-de-investigacion', 'Suministros de investigación', 'Research Supplies',
        None, None,
    ),
}

# slug -> (es, en, descripcion_es, descripcion_en)
NUEVAS = {
    'cognitivo': (
        'Cognitivo', 'Cognitive',
        'Péptidos investigados en señalización del sistema nervioso central y función cognitiva.',
        'Peptides researched in central nervous system signalling and cognitive function.',
    ),
    'blends': (
        'Blends', 'Blends',
        'Viales que combinan varios péptidos en una sola preparación liofilizada.',
        'Vials combining several peptides in a single lyophilised preparation.',
    ),
}

REASIGNAR = {
    'Semax': 'cognitivo',
    'Selank': 'cognitivo',
    'Wolverine Blend': 'blends',
    'Glow70 Blend': 'blends',
}

ELIMINAR = ['spray-nasal']

# Estado anterior, para poder revertir.
ORIGINAL = {
    'perdida-de-grasa': ('Pérdida de Grasa', 'Fat Loss'),
    'recuperacion': ('Recuperación', 'Recovery'),
    'cabello-piel': ('Cabello y Piel', 'Hair and Skin'),
    'longevidad-antienvejecimiento': ('Longevidad y Antienvejecimiento', 'Longevity and Anti-Aging'),
    'disolventes-auxiliares': ('Disolventes y Auxiliares', 'Solvents and Accessories'),
}


def aplicar(apps, schema_editor):
    Category = apps.get_model('store', 'Category')
    Peptide = apps.get_model('store', 'Peptide')

    for viejo, (nuevo, es, en, desc_es, desc_en) in RENOMBRAR.items():
        campos = {'slug': nuevo, 'name': es, 'name_es': es, 'name_en': en}
        if desc_es is not None:
            campos['description'] = desc_es
            campos['description_es'] = desc_es
            campos['description_en'] = desc_en
        Category.objects.filter(slug=viejo).update(**campos)

    for slug, (es, en, desc_es, desc_en) in NUEVAS.items():
        Category.objects.update_or_create(
            slug=slug,
            defaults={'name': es, 'name_es': es, 'name_en': en,
                      'description': desc_es, 'description_es': desc_es,
                      'description_en': desc_en, 'is_active': True},
        )

    for nombre_producto, slug_destino in REASIGNAR.items():
        destino = Category.objects.filter(slug=slug_destino).first()
        if destino:
            Peptide.objects.filter(name=nombre_producto).update(category=destino)

    # El FK es PROTECT: si algo quedó dentro, se deja estar en vez de reventar.
    for slug in ELIMINAR:
        cat = Category.objects.filter(slug=slug).first()
        if cat and not Peptide.objects.filter(category=cat).exists():
            cat.delete()


def revertir(apps, schema_editor):
    Category = apps.get_model('store', 'Category')
    Peptide = apps.get_model('store', 'Peptide')

    spray, _ = Category.objects.get_or_create(
        slug='spray-nasal',
        defaults={'name': 'Spray Nasal', 'name_es': 'Spray Nasal',
                  'name_en': 'Nasal Spray', 'is_active': True},
    )
    for nombre_producto in ('Semax', 'Selank'):
        Peptide.objects.filter(name=nombre_producto).update(category=spray)

    recup = Category.objects.filter(slug='recuperacion-y-reparacion').first()
    if recup:
        Peptide.objects.filter(name='Wolverine Blend').update(category=recup)
    cabello = Category.objects.filter(slug='cabello-y-piel').first()
    if cabello:
        Peptide.objects.filter(name='Glow70 Blend').update(category=cabello)

    for slug in NUEVAS:
        cat = Category.objects.filter(slug=slug).first()
        if cat and not Peptide.objects.filter(category=cat).exists():
            cat.delete()

    for viejo, (nuevo, *_resto) in RENOMBRAR.items():
        es, en = ORIGINAL[viejo]
        Category.objects.filter(slug=nuevo).update(
            slug=viejo, name=es, name_es=es, name_en=en)


class Migration(migrations.Migration):

    dependencies = [('store', '0013_destacar_paquetes')]

    operations = [migrations.RunPython(aplicar, revertir)]
