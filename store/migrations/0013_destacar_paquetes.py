"""Marca en portada los tres packs que no solapan con un blend existente.

El Pack Piel se queda fuera: el Glow70 Blend cubre casi lo mismo y ponerlos
juntos en la home obliga a explicar la diferencia antes de que nadie la haya
preguntado. En /packs/ sigue estando.
"""

from django.db import migrations

DESTACADOS = ['pack-recuperacion', 'pack-spray-nasal', 'pack-comparativa-glp-1']


def destacar(apps, schema_editor):
    apps.get_model('store', 'Bundle').objects.filter(slug__in=DESTACADOS).update(is_featured=True)


def quitar(apps, schema_editor):
    apps.get_model('store', 'Bundle').objects.update(is_featured=False)


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0012_paquetes_iniciales'),
    ]

    operations = [
        migrations.RunPython(destacar, quitar),
    ]
