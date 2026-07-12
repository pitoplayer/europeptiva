from django.db import migrations

CERTIFICADOS = [
    {
        'slug': 'retatrutide', 'lab_name': 'BTLabs', 'lot_number': 'WL-RT10-P00521',
        'tested_date': '2026-06-08', 'purity': '99.6%', 'file': 'certificates/retatrutide.pdf',
    },
    {
        'slug': 'melanotan-2', 'lab_name': 'BTLabs', 'lot_number': 'WL-ML10-P00518',
        'tested_date': '2026-06-08', 'purity': '99.8%', 'file': 'certificates/melanotan-2.pdf',
    },
    {
        'slug': 'tesamorelin', 'lab_name': 'BTLabs', 'lot_number': 'WL-TSM10-P00520',
        'tested_date': '2026-06-08', 'purity': '99.6%', 'file': 'certificates/tesamorelin.pdf',
    },
    {
        'slug': 'semax', 'lab_name': 'BTLabs', 'lot_number': 'WL-SX10-P00519',
        'tested_date': '2026-06-08', 'purity': '99.8%', 'file': 'certificates/semax.pdf',
    },
    {
        'slug': 'selank', 'lab_name': 'BTLabs', 'lot_number': 'WL-SK10-P00519',
        'tested_date': '2026-06-08', 'purity': '99.8%', 'file': 'certificates/selank.pdf',
    },
    {
        'slug': 'tirzepatide', 'lab_name': 'BTLabs', 'lot_number': 'WL-TR10-P00519',
        'tested_date': '2026-06-08', 'purity': '99.7%', 'file': 'certificates/tirzepatide.pdf',
    },
    {
        'slug': 'glow70-blend', 'lab_name': 'BTLabs', 'lot_number': 'WL-GLOW-P00520',
        'tested_date': '2026-06-08', 'purity': '99.7%', 'file': 'certificates/glow70-blend.pdf',
    },
    {
        'slug': 'bpc-157', 'lab_name': 'Krause Analytical', 'lot_number': 'xzgt3gk',
        'tested_date': '2026-02-11', 'purity': '99.78%', 'file': 'certificates/bpc-157.pdf',
    },
    {
        'slug': 'igf-1-lr3', 'lab_name': 'ILS Laboratories', 'lot_number': '10128',
        'tested_date': '2026-07-07', 'purity': '99.68%', 'file': 'certificates/igf-1-lr3.pdf',
    },
]

# MOTS-c y NAD+: el COA del lote analizado dio
# "Identity: Failed / No Analyte Detected". Se ocultan del catálogo hasta
# tener un lote con certificado válido.
SLUGS_SIN_CERTIFICADO_VALIDO = ['mots-c', 'nad-plus']


def crear_certificados(apps, schema_editor):
    Peptide = apps.get_model('store', 'Peptide')
    Certificate = apps.get_model('store', 'Certificate')

    for data in CERTIFICADOS:
        peptide = Peptide.objects.filter(slug=data['slug']).first()
        if not peptide:
            continue
        Certificate.objects.get_or_create(
            peptide=peptide,
            lot_number=data['lot_number'],
            defaults={
                'lab_name': data['lab_name'],
                'tested_date': data['tested_date'],
                'purity': data['purity'],
                'file': data['file'],
                'is_active': True,
            },
        )

    Peptide.objects.filter(slug__in=SLUGS_SIN_CERTIFICADO_VALIDO).update(is_active=False)


def revertir(apps, schema_editor):
    Peptide = apps.get_model('store', 'Peptide')
    Certificate = apps.get_model('store', 'Certificate')
    Certificate.objects.filter(lot_number__in=[c['lot_number'] for c in CERTIFICADOS]).delete()
    Peptide.objects.filter(slug__in=SLUGS_SIN_CERTIFICADO_VALIDO).update(is_active=True)


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0003_certificate'),
    ]

    operations = [
        migrations.RunPython(crear_certificados, revertir),
    ]
