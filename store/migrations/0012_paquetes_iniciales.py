"""Crea los cuatro paquetes de lanzamiento.

Precios cerrados, no porcentajes: permiten redondear a 129,95 y ajustar el
margen paquete a paquete. Los descuentos se quedan **por debajo del 15 %** a
propósito, que es el primer tramo de `store/bulk.py`: un pack de tres viales
que descontara más que un pedido mayorista de diez unidades dejaría los tramos
de mayoristas sin sentido.

Margen: con los costes de proveedor del `.xlsx` (79-90 % en casi todo el
catálogo), cualquiera de estos cuatro se queda por encima del 85 %.

Los componentes se buscan por slug y tamaño. Si alguno no existe en la base de
datos —MOTS-c y NAD+ están desactivados por el CoA fallido, por ejemplo— el
paquete no se crea, en lugar de reventar la migración.
"""

from decimal import Decimal

from django.db import migrations
from django.utils.text import slugify

PAQUETES = [
    {
        'slug': 'pack-spray-nasal',
        'name': ("Pack Spray Nasal", "Nasal Spray Pack"),
        'price': Decimal('129.95'),
        'components': [('semax', 10, 1), ('selank', 10, 1)],
        'short_description': (
            "Semax y Selank, los dos péptidos nasales del catálogo, en un solo pedido y "
            "listos para usar.",
            "Semax and Selank, the catalog's two nasal peptides, in a single order and ready "
            "to use.",
        ),
        'description': (
            "Semax y Selank comparten origen y formato: los dos son heptapéptidos "
            "estabilizados con la misma cola Pro-Gly-Pro, los dos se desarrollaron en Rusia y "
            "los dos llegan en solución, sin nada que reconstituir.\n\n"
            "Lo que se ha estudiado de cada uno va por caminos distintos —Semax alrededor de "
            "los factores neurotróficos y la cognición, Selank alrededor del efecto "
            "ansiolítico y la modulación GABAérgica—, y por eso aparecen juntos en la "
            "literatura con tanta frecuencia.",

            "Semax and Selank share an origin and a format: both are heptapeptides stabilized "
            "with the same Pro-Gly-Pro tail, both were developed in Russia, and both arrive in "
            "solution with nothing to reconstitute.\n\n"
            "What has been studied about each runs along different paths — Semax around "
            "neurotrophic factors and cognition, Selank around anxiolytic effect and GABAergic "
            "modulation — which is why they turn up together in the literature so often.",
        ),
    },
    {
        'slug': 'pack-recuperacion',
        'name': ("Pack Recuperación", "Recovery Pack"),
        'price': Decimal('119.95'),
        'components': [('bpc-157', 10, 1), ('tb-500', 10, 1), ('bac-water', 10, 1)],
        'short_description': (
            "BPC-157 y TB-500 en viales separados, con el agua bacteriostática para "
            "reconstituirlos.",
            "BPC-157 and TB-500 in separate vials, with the bacteriostatic water to "
            "reconstitute them.",
        ),
        'description': (
            "Es la combinación con más literatura preclínica en reparación de tejidos, y "
            "actúan por vías distintas: TB-500 sobre la dinámica de la actina y la migración "
            "celular, BPC-157 sobre la angiogénesis y la señalización del óxido nítrico.\n\n"
            "Si buscas los dos mezclados en un mismo vial, eso es el Wolverine Blend y sale "
            "más barato. Este pack existe para lo contrario: tener cada compuesto por "
            "separado y poder reconstituirlos de forma independiente o usar uno sin el otro.",

            "This is the combination with the most preclinical literature in tissue repair, "
            "and the two act through different pathways: TB-500 on actin dynamics and cell "
            "migration, BPC-157 on angiogenesis and nitric oxide signaling.\n\n"
            "If what you want is the two of them mixed in a single vial, that is the Wolverine "
            "Blend and it costs less. This pack exists for the opposite reason: having each "
            "compound separately, to reconstitute them independently or use one without the "
            "other.",
        ),
    },
    {
        'slug': 'pack-comparativa-glp-1',
        'name': ("Pack Comparativa GLP-1", "GLP-1 Comparison Pack"),
        'price': Decimal('109.95'),
        'components': [('semaglutide', 10, 1), ('tirzepatide', 10, 1), ('bac-water', 10, 1)],
        'short_description': (
            "Semaglutida y tirzepatida en paralelo: un agonista GLP-1 puro frente a uno dual "
            "GLP-1/GIP.",
            "Semaglutide and tirzepatide side by side: a pure GLP-1 agonist against a dual "
            "GLP-1/GIP one.",
        ),
        'description': (
            "La diferencia entre los dos es exactamente un receptor. La semaglutida actúa solo "
            "sobre el de GLP-1; la tirzepatida activa además el de GIP, cuyo papel en el "
            "metabolismo sigue siendo objeto de discusión: hay trabajo publicado que sostiene "
            "que agonizarlo y trabajo que sostiene que antagonizarlo producen efectos "
            "parecidos sobre el peso corporal.\n\n"
            "Tenerlos los dos permite montar la comparación en las mismas condiciones, que es "
            "el uso natural de este par. Incluye el agua bacteriostática para reconstituir "
            "ambos viales.",

            "The difference between the two is exactly one receptor. Semaglutide acts only on "
            "the GLP-1 receptor; tirzepatide also activates the GIP receptor, whose role in "
            "metabolism remains under discussion: there is published work arguing that "
            "agonizing it and work arguing that antagonizing it produce similar effects on "
            "body weight.\n\n"
            "Having both makes it possible to set up that comparison under the same "
            "conditions, which is the natural use for this pair. Bacteriostatic water to "
            "reconstitute both vials is included.",
        ),
    },
    {
        'slug': 'pack-piel',
        'name': ("Pack Piel", "Skin Pack"),
        'price': Decimal('94.95'),
        'components': [('ghk-cu', 50, 1), ('melanotan-1', 10, 1), ('bac-water', 10, 1)],
        'short_description': (
            "GHK-Cu y Melanotan I, dos vías distintas de la biología cutánea, con el agua para "
            "reconstituirlos.",
            "GHK-Cu and Melanotan I, two different routes into skin biology, with the water to "
            "reconstitute them.",
        ),
        'description': (
            "Entran en la piel por sitios distintos. El GHK-Cu se estudia en la matriz "
            "extracelular: síntesis de colágeno, remodelado tisular y expresión génica en "
            "fibroblastos. Melanotan I actúa sobre el receptor MC1R y la producción de "
            "eumelanina, que es una línea de fotoprotección.\n\n"
            "El Glow70 Blend lleva estos dos más BPC-157 mezclados en un vial. Este pack los "
            "deja sueltos, para poder trabajar cada vía por separado.",

            "They enter the skin at different points. GHK-Cu is studied in the extracellular "
            "matrix: collagen synthesis, tissue remodeling and gene expression in fibroblasts. "
            "Melanotan I acts on the MC1R receptor and eumelanin production, which is a "
            "photoprotection line.\n\n"
            "The Glow70 Blend carries these two plus BPC-157 mixed into one vial. This pack "
            "keeps them separate, so each route can be worked on independently.",
        ),
    },
]


def crear_paquetes(apps, schema_editor):
    Bundle = apps.get_model('store', 'Bundle')
    BundleItem = apps.get_model('store', 'BundleItem')
    PeptideVariant = apps.get_model('store', 'PeptideVariant')

    for datos in PAQUETES:
        variantes = []
        for slug, size_mg, unidades in datos['components']:
            variante = PeptideVariant.objects.filter(
                peptide__slug=slug, size_mg=size_mg
            ).first()
            if variante is None:
                break
            variantes.append((variante, unidades))
        else:
            name_es, name_en = datos['name']
            short_es, short_en = datos['short_description']
            desc_es, desc_en = datos['description']
            bundle, creado = Bundle.objects.get_or_create(
                slug=datos['slug'],
                defaults={
                    'name': name_es, 'name_es': name_es, 'name_en': name_en,
                    'short_description': short_es, 'short_description_es': short_es,
                    'short_description_en': short_en,
                    'description': desc_es, 'description_es': desc_es,
                    'description_en': desc_en,
                    'price': datos['price'],
                },
            )
            if creado:
                for variante, unidades in variantes:
                    BundleItem.objects.create(
                        bundle=bundle, variant=variante, quantity=unidades)


def borrar_paquetes(apps, schema_editor):
    Bundle = apps.get_model('store', 'Bundle')
    Bundle.objects.filter(slug__in=[d['slug'] for d in PAQUETES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0011_bundle_bundleitem'),
    ]

    operations = [
        migrations.RunPython(crear_paquetes, borrar_paquetes),
    ]
