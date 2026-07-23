"""Rellena las columnas de idioma que creó la migración 0006.

Dos cosas:

1. `*_es` se copia del campo original. Las columnas por idioma nacen vacías y
   modeltranslation reescribe los filtros y el `ordering` al campo del idioma
   activo (`name` → `name_es`), así que un catálogo con `name_es` vacío
   ordenaría y buscaría sobre nada aunque la web se viera bien.
2. `*_en` se rellena con la traducción inglesa del catálogo, indexada por slug
   para no depender de los PKs (producción y local no tienen por qué coincidir).

Se traduce solo lo que es texto de marketing. Los nombres de producto no están
aquí: son nombres químicos idénticos en los dos idiomas.
"""

from django.db import migrations

STORAGE = "Store refrigerated and protected from light. Reconstitute with sterile BAC Water."
STORAGE_NO_RECONSTITUTION = "Store refrigerated and protected from light."

CATEGORIES_EN = {
    'perdida-de-grasa': (
        "Fat Loss",
        "Peptides researched in the fields of metabolism, body composition and fat loss.",
    ),
    'recuperacion': (
        "Recovery",
        "Peptides for research into tissue regeneration and recovery.",
    ),
    'disolventes-auxiliares': (
        "Solvents and Accessories",
        "Bacteriostatic water and other accessories for reconstituting peptides.",
    ),
    'cabello-piel': (
        "Hair and Skin",
        "Peptides researched in skin regeneration, pigmentation and hair follicle growth.",
    ),
    'spray-nasal': (
        "Nasal Spray",
        "Neurotrophic peptides commonly researched through intranasal administration.",
    ),
    'longevidad-antienvejecimiento': (
        "Longevity and Anti-Aging",
        "Peptides and coenzymes researched in cellular metabolism, oxidative stress and aging.",
    ),
}

PEPTIDES_EN = {
    'retatrutide': (
        "Research peptide acting on three metabolic pathways at once (GLP-1, GIP and glucagon).",
        "Retatrutide is a synthetic peptide studied for its combined effect on three receptors "
        "linked to metabolism, appetite and body weight. It is one of the most researched "
        "peptides in the metabolic field today.\n\n" + STORAGE,
    ),
    'semaglutide': (
        "Long-acting peptide, one of the most studied in research on type 2 diabetes and weight control.",
        "Semaglutide is a benchmark GLP-1 peptide in metabolic research, known for its lasting "
        "effect on appetite and glucose levels.\n\n" + STORAGE,
    ),
    'bpc-157': (
        "Peptide derived from gastric juice, researched for its role in tissue regeneration.",
        "BPC-157 is a widely studied peptide for its possible role in tissue repair, reducing "
        "inflammation and forming new blood vessels.\n\n" + STORAGE,
    ),
    'tb-500': (
        "Synthetic fragment of a natural protein, researched in muscle and tissue regeneration.",
        "TB-500 is a peptide derived from Thymosin Beta-4, studied for its role in tissue repair, "
        "cell motility and the formation of new blood vessels.\n\n" + STORAGE,
    ),
    'bac-water': (
        "Sterile water with preservative, to dissolve lyophilized peptides safely.",
        "Bacteriostatic Water (BAC Water) is the standard solvent for reconstituting lyophilized "
        "peptides. Its 0.9% benzyl alcohol lets the same vial be used several times without risk "
        "of contamination.\n\nStore in a cool place, protected from light. Use within 28 days of "
        "opening the vial.",
    ),
    'ghk-cu': (
        "Copper peptide researched for its role in skin and hair regeneration.",
        "GHK-Cu is a natural peptide widely studied in dermatological research for its effect on "
        "collagen production, tissue repair and hair follicle growth.\n\n" + STORAGE,
    ),
    'melanotan-1': (
        "Peptide researched for its effect on pigmentation and protection from the sun.",
        "Melanotan I is a peptide that mimics a hormone the body produces naturally, and is "
        "researched for its ability to stimulate melanin production, protecting the skin from UV "
        "radiation.\n\n" + STORAGE,
    ),
    'melanotan-2': (
        "Peptide researched in skin pigmentation and appetite regulation.",
        "Melanotan II is a more stable version of a natural hormone, studied for its effect on "
        "skin pigmentation and its influence on appetite and energy balance.\n\n" + STORAGE,
    ),
    'tesamorelin': (
        "Peptide researched for its ability to stimulate growth hormone.",
        "Tesamorelin is a peptide studied for its effect on the natural release of growth hormone, "
        "with particular interest in research on fat metabolism and body composition.\n\n" + STORAGE,
    ),
    'semax': (
        "Nootropic peptide in nasal spray, researched for its effect on memory and neuronal protection.",
        "Semax is a peptide studied for its possible effect on memory, attention and the protection "
        "of neurons. It comes as a nasal spray, ready to use.\n\n" + STORAGE_NO_RECONSTITUTION,
    ),
    'selank': (
        "Anxiolytic peptide in nasal spray, researched for its calming effect without sedation.",
        "Selank is a peptide derived from a natural protein of the immune system, studied for its "
        "anxiolytic effect and its influence on mood. It comes as a nasal spray, ready to use.\n\n"
        + STORAGE_NO_RECONSTITUTION,
    ),
    'tirzepatide': (
        "Dual GLP-1/GIP agonist peptide, one of the most sought-after in metabolic research today.",
        "Tirzepatide is a synthetic peptide that activates the GLP-1 and GIP receptors at the same "
        "time, and is today one of the benchmark reagents in research on metabolism, appetite and "
        "weight control.\n\n" + STORAGE,
    ),
    'mots-c': (
        "Peptide derived from mitochondrial DNA, researched for its role in cellular metabolism and longevity.",
        "MOTS-c is a 16-amino-acid peptide encoded in the mitochondrial genome itself, studied as a "
        "metabolic regulator and for its role in the communication between the mitochondria and the "
        "cell nucleus.\n\n" + STORAGE,
    ),
    'wolverine-blend': (
        "Blend of TB-500 and BPC-157 in a single vial (10 mg + 10 mg), meant for researching their combined effect.",
        "Wolverine Blend puts two of the most studied peptides in tissue regeneration into a single "
        "vial: TB-500 and BPC-157, to research their possible synergistic effect in one model.\n\n"
        + STORAGE,
    ),
    'glow70-blend': (
        "Blend of GHK-Cu, Melanotan I and BPC-157, researched in skin regeneration and protection.",
        "Glow70 Blend puts three benchmark peptides in skin biology into a single vial: GHK-Cu, "
        "Melanotan I and BPC-157, to research their combined effects on the skin.\n\n" + STORAGE,
    ),
    'igf-1-lr3': (
        "Long-acting analog of IGF-1, researched in muscle growth and repair.",
        "IGF-1 LR3 is a synthetic analog of human IGF-1 modified to resist degradation better, "
        "widely used in research on cell growth and muscle tissue repair.\n\n" + STORAGE,
    ),
    'glutation': (
        "The body's master antioxidant, researched for its role in cellular detoxification.",
        "Glutathione (GSH) is a natural tripeptide with a central role in the antioxidant balance "
        "of cells, studied in research on cellular detoxification and oxidative stress.\n\n" + STORAGE,
    ),
    'nad-plus': (
        "Essential coenzyme for cellular energy, researched in aging and DNA repair.",
        "NAD+ is a coenzyme present in every cell, studied for its role in energy production, DNA "
        "repair and the mechanisms associated with cellular aging.\n\n" + STORAGE,
    ),
}


def rellenar_traducciones(apps, schema_editor):
    Category = apps.get_model('store', 'Category')
    Peptide = apps.get_model('store', 'Peptide')

    for category in Category.objects.all():
        category.name_es = category.name
        category.description_es = category.description
        traduccion = CATEGORIES_EN.get(category.slug)
        if traduccion:
            category.name_en, category.description_en = traduccion
        category.save(update_fields=[
            'name_es', 'description_es', 'name_en', 'description_en',
        ])

    for peptide in Peptide.objects.all():
        peptide.short_description_es = peptide.short_description
        peptide.description_es = peptide.description
        traduccion = PEPTIDES_EN.get(peptide.slug)
        if traduccion:
            peptide.short_description_en, peptide.description_en = traduccion
        peptide.save(update_fields=[
            'short_description_es', 'description_es',
            'short_description_en', 'description_en',
        ])


def vaciar_traducciones(apps, schema_editor):
    """Al revertir se dejan las columnas vacías; el campo original no se toca."""
    apps.get_model('store', 'Category').objects.update(
        name_es='', description_es='', name_en='', description_en='',
    )
    apps.get_model('store', 'Peptide').objects.update(
        short_description_es='', description_es='',
        short_description_en='', description_en='',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0006_category_description_en_category_description_es_and_more'),
    ]

    operations = [
        migrations.RunPython(rellenar_traducciones, vaciar_traducciones),
    ]
