"""Renombra el segundo nivel de categorías por clase molecular / área de estudio.

La 0014 copió los nombres de PurityBase ("Weight Management", "Hair & Skin",
"Healthy Aging"…). Son lenguaje de beneficio para consumo humano, que contradice
el aviso "solo investigación in vitro" y es justo el patrón que un underwriter de
Mollie busca en esta categoría de alto riesgo. Aquí se sustituyen por la clase
molecular o el área de investigación, que dice lo mismo del producto sin prometer
un efecto en personas.

Solo cambian nombre, slug y descripción; la asignación de productos no se toca.
"Blends" se queda igual (describe la composición, no un beneficio). La categoría
de disolventes pasa de "Suministros de investigación" a "Disolventes y auxiliares"
para no duplicar el rótulo del primer nivel (el formato solvent ya se llama así).
"""
from django.db import migrations


# slug viejo -> (slug nuevo, es, en, desc_es, desc_en)
RENOMBRAR = {
    'control-de-peso': (
        'peptidos-metabolicos', 'Péptidos metabólicos', 'Metabolic peptides',
        'Agonistas de los receptores de incretinas (GLP-1, GIP, glucagón) y análogos '
        'relacionados, investigados en homeostasis de la glucosa y metabolismo energético.',
        'Incretin receptor agonists (GLP-1, GIP, glucagon) and related analogues, '
        'researched in glucose homeostasis and energy metabolism.',
    ),
    'recuperacion-y-reparacion': (
        'senalizacion-y-reparacion', 'Señalización y reparación', 'Signalling & repair',
        'Péptidos y factores de crecimiento investigados en vías de señalización celular, '
        'angiogénesis y regeneración tisular in vitro.',
        'Peptides and growth factors researched in cell-signalling pathways, angiogenesis '
        'and tissue regeneration in vitro.',
    ),
    'cabello-y-piel': (
        'melanocortinas-y-cobre', 'Melanocortinas y péptidos de cobre',
        'Melanocortins & copper peptides',
        'Agonistas del receptor de melanocortina y tripéptidos de cobre, investigados en '
        'pigmentación y matriz extracelular.',
        'Melanocortin receptor agonists and copper tripeptides, researched in pigmentation '
        'and extracellular matrix.',
    ),
    'envejecimiento-saludable': (
        'metabolismo-celular', 'Metabolismo celular y antioxidantes',
        'Cellular metabolism & antioxidants',
        'Péptidos mitocondriales, coenzimas y antioxidantes investigados en metabolismo '
        'celular y estrés oxidativo.',
        'Mitochondrial peptides, coenzymes and antioxidants researched in cellular '
        'metabolism and oxidative stress.',
    ),
    'cognitivo': (
        'neuropeptidos', 'Neuropéptidos', 'Neuropeptides',
        'Neuropéptidos investigados en la señalización del sistema nervioso central.',
        'Neuropeptides researched in central nervous system signalling.',
    ),
    'suministros-de-investigacion': (
        'disolventes-y-auxiliares', 'Disolventes y auxiliares', 'Solvents & accessories',
        'Agua bacteriostática y otros auxiliares para la reconstitución de péptidos.',
        'Bacteriostatic water and other accessories for reconstituting peptides.',
    ),
}

# Estado que dejó la 0014, para revertir.
ORIGINAL = {
    'control-de-peso': (
        'Control de peso', 'Weight Management',
        'Péptidos investigados en el ámbito del metabolismo, la composición corporal y el control de peso.',
        'Peptides researched in the fields of metabolism, body composition and weight management.',
    ),
    'recuperacion-y-reparacion': (
        'Recuperación y reparación', 'Recovery & Repair',
        'Péptidos para investigación en regeneración tisular y recuperación.',
        'Peptides for research into tissue regeneration and recovery.',
    ),
    'cabello-y-piel': (
        'Cabello y piel', 'Hair & Skin',
        'Péptidos investigados en regeneración cutánea, pigmentación y crecimiento del folículo piloso.',
        'Peptides researched in skin regeneration, pigmentation and hair follicle growth.',
    ),
    'envejecimiento-saludable': (
        'Envejecimiento saludable', 'Healthy Aging',
        'Péptidos y coenzimas investigados en metabolismo celular, estrés oxidativo y envejecimiento.',
        'Peptides and coenzymes researched in cellular metabolism, oxidative stress and aging.',
    ),
    'cognitivo': (
        'Cognitivo', 'Cognitive',
        'Péptidos investigados en señalización del sistema nervioso central y función cognitiva.',
        'Peptides researched in central nervous system signalling and cognitive function.',
    ),
    'suministros-de-investigacion': (
        'Suministros de investigación', 'Research Supplies',
        'Agua bacteriostática y otros auxiliares para reconstitución de péptidos.',
        'Bacteriostatic water and other accessories for reconstituting peptides.',
    ),
}


def _rename(Category, mapping):
    for viejo, (nuevo, es, en, des_es, des_en) in mapping.items():
        Category.objects.filter(slug=viejo).update(
            slug=nuevo, name=es, name_es=es, name_en=en,
            description=des_es, description_es=des_es, description_en=des_en)


def aplicar(apps, schema_editor):
    _rename(apps.get_model('store', 'Category'), RENOMBRAR)


def revertir(apps, schema_editor):
    Category = apps.get_model('store', 'Category')
    # slug nuevo -> estado original completo
    inverso = {}
    for viejo, (nuevo, *_r) in RENOMBRAR.items():
        es, en, des_es, des_en = ORIGINAL[viejo]
        inverso[nuevo] = (viejo, es, en, des_es, des_en)
    _rename(Category, inverso)


class Migration(migrations.Migration):

    dependencies = [('store', '0014_categorias_estilo_puritybase')]

    operations = [migrations.RunPython(aplicar, revertir)]
