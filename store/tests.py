from datetime import date
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from django.core import mail
from django.test import override_settings
from django.utils import translation

from .models import (BulkEnquiry, Bundle, BundleItem, Category, Certificate,
                     Peptide, PeptideVariant)
from .pricing import desglosar_paquete


def crear_peptido(name='BPC-157', category=None, **kwargs):
    category = category or Category.objects.create(name='Recuperación')
    return Peptide.objects.create(
        name=name,
        category=category,
        short_description=f'{name} para investigación',
        description=f'Descripción completa de {name}.',
        **kwargs,
    )


class ModelosTest(TestCase):
    def test_slug_de_categoria_y_peptido_se_generan_solos(self):
        cat = Category.objects.create(name='Pérdida de grasa')
        pep = crear_peptido(name='Semaglutide GLP-1', category=cat)
        self.assertEqual(cat.slug, 'perdida-de-grasa')
        self.assertEqual(pep.slug, 'semaglutide-glp-1')

    def test_sku_de_variante_se_genera_solo(self):
        pep = crear_peptido()
        variant = PeptideVariant.objects.create(peptide=pep, size_mg=10, price=Decimal('49.90'))
        self.assertEqual(variant.sku, 'bpc-157-10mg')

    def test_get_cheapest_variant_ignora_inactivas_y_sin_stock(self):
        pep = crear_peptido()
        PeptideVariant.objects.create(peptide=pep, size_mg=5, price=Decimal('10.00'), stock=0)
        PeptideVariant.objects.create(peptide=pep, size_mg=10, price=Decimal('20.00'), stock=5, is_active=False)
        buena = PeptideVariant.objects.create(peptide=pep, size_mg=20, price=Decimal('30.00'), stock=3)
        self.assertEqual(pep.get_cheapest_variant(), buena)

    def test_needs_reorder(self):
        pep = crear_peptido()
        v = PeptideVariant.objects.create(peptide=pep, size_mg=10, price=Decimal('49.90'), stock=6, reorder_point=5)
        self.assertFalse(v.needs_reorder)
        v.stock = 5
        self.assertTrue(v.needs_reorder)


class VistasCatalogoTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cat_recuperacion = Category.objects.create(name='Recuperación')
        cls.cat_grasa = Category.objects.create(name='Pérdida de grasa')
        cls.bpc = crear_peptido(name='BPC-157', category=cls.cat_recuperacion)
        cls.reta = crear_peptido(name='Retatrutide', category=cls.cat_grasa, is_featured=True)
        cls.oculto = crear_peptido(name='NAD+', category=cls.cat_grasa, is_active=False)
        PeptideVariant.objects.create(peptide=cls.bpc, size_mg=10, price=Decimal('49.90'), stock=10)
        PeptideVariant.objects.create(peptide=cls.reta, size_mg=10, price=Decimal('89.90'), stock=10)

    def test_index_carga(self):
        resp = self.client.get(reverse('index'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Retatrutide')  # destacado

    def test_catalogo_muestra_solo_activos(self):
        resp = self.client.get(reverse('catalog'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'BPC-157')
        self.assertNotContains(resp, 'NAD+')

    def test_catalogo_filtra_por_categoria(self):
        # Se comprueba el enlace de la tarjeta (el nombre aparece también en las metas SEO)
        resp = self.client.get(reverse('catalog'), {'category': self.cat_recuperacion.slug})
        self.assertContains(resp, f'/producto/{self.bpc.slug}/')
        self.assertNotContains(resp, f'/producto/{self.reta.slug}/')

    def test_catalogo_busca_por_nombre(self):
        resp = self.client.get(reverse('catalog'), {'q': 'retatru'})
        self.assertContains(resp, f'/producto/{self.reta.slug}/')
        self.assertNotContains(resp, f'/producto/{self.bpc.slug}/')

    def test_ficha_de_producto_con_json_ld(self):
        resp = self.client.get(reverse('product_detail', args=[self.bpc.slug]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'application/ld+json')
        self.assertContains(resp, 'schema.org/InStock')

    def test_producto_inactivo_da_404(self):
        resp = self.client.get(reverse('product_detail', args=[self.oculto.slug]))
        self.assertEqual(resp.status_code, 404)

    def test_sitemap_y_robots(self):
        self.assertEqual(self.client.get('/sitemap.xml').status_code, 200)
        self.assertEqual(self.client.get('/robots.txt').status_code, 200)


class CertificadosTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.pep = crear_peptido(name='Retatrutide')
        cls.inactivo = crear_peptido(name='NAD+', category=cls.pep.category, is_active=False)
        pdf = SimpleUploadedFile('coa.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        Certificate.objects.create(
            peptide=cls.pep, lab_name='Lab Test', lot_number='L123',
            tested_date=date(2026, 6, 1), purity='99.5%', file=pdf,
        )
        Certificate.objects.create(
            peptide=cls.inactivo, lab_name='Lab Test', lot_number='L999',
            tested_date=date(2026, 6, 1), purity='99.1%', file=pdf,
        )

    def test_pagina_certificados_solo_muestra_peptidos_activos(self):
        resp = self.client.get(reverse('certificates'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Retatrutide')
        self.assertNotContains(resp, 'NAD+')

    def test_ficha_producto_enlaza_su_certificado(self):
        resp = self.client.get(reverse('product_detail', args=[self.pep.slug]))
        self.assertContains(resp, 'certificates/')


DATOS_BULK = {
    'name': 'Laura Vidal',
    'organization': 'Instituto de Bioquímica',
    'email': 'laura@instituto.example',
    'phone': '+34600111222',
    'message': '20 viales de Retatrutide 10mg y 15 de BPC-157 5mg.',
}


class CompraAlPorMayorTest(TestCase):
    def test_pagina_carga_con_los_tramos(self):
        resp = self.client.get(reverse('bulk'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Compra al por mayor')
        for tier in resp.context['bulk_tiers']:
            self.assertContains(resp, f'-{tier["discount"]}%')

    def test_solicitud_valida_se_guarda_y_avisa_por_email(self):
        with override_settings(ADMIN_EMAIL='admin@europeptiva.com'):
            resp = self.client.post(reverse('bulk'), DATOS_BULK)

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context['bulk_sent'])

        enquiry = BulkEnquiry.objects.get()
        self.assertEqual(enquiry.email, 'laura@instituto.example')
        self.assertEqual(enquiry.status, 'new')

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['admin@europeptiva.com'])
        self.assertIn('Retatrutide', mail.outbox[0].body)

    def test_solicitud_se_guarda_aunque_no_haya_admin_email(self):
        """El lead no se puede perder porque el aviso no salga."""
        with override_settings(ADMIN_EMAIL=''):
            self.client.post(reverse('bulk'), DATOS_BULK)
        self.assertEqual(BulkEnquiry.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_solicitud_sin_email_no_se_guarda(self):
        datos = {k: v for k, v in DATOS_BULK.items() if k != 'email'}
        resp = self.client.post(reverse('bulk'), datos)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context['bulk_sent'])
        self.assertEqual(BulkEnquiry.objects.count(), 0)

    def test_empresa_y_telefono_son_opcionales(self):
        datos = {k: v for k, v in DATOS_BULK.items() if k not in ('organization', 'phone')}
        self.client.post(reverse('bulk'), datos)
        self.assertEqual(BulkEnquiry.objects.count(), 1)

    def test_aparece_en_el_sitemap(self):
        resp = self.client.get('/sitemap.xml')
        self.assertContains(resp, '/al-por-mayor/')


class DevolucionesTest(TestCase):
    def test_pagina_carga_en_ambos_idiomas(self):
        for url in ('/devoluciones/', '/en/returns/'):
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_recoge_la_excepcion_de_48h_y_la_base_legal(self):
        html = self.client.get('/devoluciones/').content.decode()
        self.assertIn('48 horas', html)
        self.assertIn('103', html)          # arts. 103.d/103.e del RDL 1/2007

    def test_enlazada_desde_el_pie_y_el_aviso_legal(self):
        for url in ('/', '/aviso-legal/'):
            self.assertIn('/devoluciones/', self.client.get(url).content.decode(), url)

    def test_aparece_en_el_sitemap(self):
        self.assertContains(self.client.get('/sitemap.xml'), '/devoluciones/')



class ContenidoTraducidoTest(TestCase):
    """El catálogo vive en la BD, así que traducir las plantillas no basta."""

    @classmethod
    def setUpTestData(cls):
        cls.categoria = Category.objects.create(
            name='Recuperación', name_en='Recovery',
            description='Péptidos para regeneración.', description_en='Peptides for regeneration.',
        )
        cls.bpc = crear_peptido(name='BPC-157', category=cls.categoria)
        cls.bpc.short_description_en = 'Peptide researched in tissue regeneration.'
        cls.bpc.description_en = 'BPC-157 is a widely studied peptide.'
        cls.bpc.save()
        cls.sin_traducir = crear_peptido(name='TB-500', category=cls.categoria)
        PeptideVariant.objects.create(peptide=cls.bpc, size_mg=10, price=Decimal('49.90'), stock=10)
        PeptideVariant.objects.create(peptide=cls.sin_traducir, size_mg=10, price=Decimal('39.90'), stock=10)

    def setUp(self):
        # Pedir una URL /en/ deja el idioma activo en el hilo, así que sin esto
        # el test siguiente arranca en inglés y hasta reverse() da URLs /en/.
        translation.activate('es')

    def test_ficha_en_ingles_usa_el_texto_ingles(self):
        resp = self.client.get(f'/en/product/{self.bpc.slug}/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'BPC-157 is a widely studied peptide.')
        self.assertNotContains(resp, 'Descripción completa de BPC-157.')

    def test_ficha_en_espanol_no_cambia(self):
        resp = self.client.get(reverse('product_detail', args=[self.bpc.slug]))
        self.assertContains(resp, 'Descripción completa de BPC-157.')

    def test_categoria_traducida_en_el_catalogo(self):
        self.assertContains(self.client.get(reverse('catalog')), 'Recuperación')
        self.assertContains(self.client.get('/en/catalog/'), 'Recovery')

    def test_sin_traduccion_cae_al_espanol(self):
        # Si nadie ha traducido un producto todavía, la ficha inglesa enseña el
        # texto español antes que un hueco en blanco.
        resp = self.client.get(f'/en/product/{self.sin_traducir.slug}/')
        self.assertContains(resp, 'Descripción completa de TB-500.')

    def test_busqueda_en_ingles_encuentra_por_texto_ingles(self):
        resp = self.client.get('/en/catalog/', {'q': 'tissue regeneration'})
        self.assertContains(resp, f'/en/product/{self.bpc.slug}/')
        self.assertNotContains(resp, f'/en/product/{self.sin_traducir.slug}/')


class FichaEstructuradaTest(TestCase):
    """Bloques nuevos de la ficha: secciones, upsell y relacionados."""

    @classmethod
    def setUpTestData(cls):
        cls.recuperacion = Category.objects.create(name='Recuperación')
        cls.disolventes = Category.objects.create(name='Disolventes')
        cls.bpc = crear_peptido(name='BPC-157', category=cls.recuperacion)
        cls.tb = crear_peptido(name='TB-500', category=cls.recuperacion)
        cls.semax = crear_peptido(name='Semax', category=cls.recuperacion,
                                  product_format=Peptide.FORMAT_SPRAY)
        cls.agua = crear_peptido(name='BAC Water', category=cls.disolventes,
                                 product_format=Peptide.FORMAT_SOLVENT)
        cls.agua.slug = 'bac-water'
        cls.agua.save()
        for peptido in (cls.bpc, cls.tb, cls.semax):
            PeptideVariant.objects.create(peptide=peptido, size_mg=10, price=Decimal('49.90'), stock=10)
        cls.agua_3ml = PeptideVariant.objects.create(
            peptide=cls.agua, size_mg=3, price=Decimal('6.90'), stock=10)

    def test_liofilizado_ofrece_agua_bacteriostatica(self):
        resp = self.client.get(reverse('product_detail', args=[self.bpc.slug]))
        self.assertContains(resp, 'Completa tu pedido')
        self.assertContains(resp, f'value="{self.agua_3ml.id}"')

    def test_el_spray_no_ofrece_agua_ni_habla_de_reconstituir(self):
        resp = self.client.get(reverse('product_detail', args=[self.semax.slug]))
        self.assertNotContains(resp, 'Completa tu pedido')
        self.assertContains(resp, 'Manipulación')
        self.assertNotContains(resp, 'Reconstitución y manipulación')

    def test_el_agua_no_se_ofrece_a_si_misma(self):
        resp = self.client.get(reverse('product_detail', args=[self.agua.slug]))
        self.assertNotContains(resp, 'Completa tu pedido')

    def test_agua_agotada_no_se_ofrece(self):
        self.agua_3ml.stock = 0
        self.agua_3ml.save()
        resp = self.client.get(reverse('product_detail', args=[self.bpc.slug]))
        self.assertNotContains(resp, 'Completa tu pedido')

    def test_relacionados_priorizan_la_misma_categoria(self):
        resp = self.client.get(reverse('product_detail', args=[self.bpc.slug]))
        self.assertContains(resp, 'Se investigan a menudo junto a este')
        self.assertContains(resp, f'/producto/{self.tb.slug}/')
        # Contra el contexto y no contra el HTML: el propio producto aparece
        # enlazado en el selector de idioma de la cabecera.
        self.assertIn(self.tb, resp.context['related'])
        self.assertNotIn(self.bpc, resp.context['related'])

    def test_contexto_cae_a_la_descripcion_mientras_este_vacio(self):
        resp = self.client.get(reverse('product_detail', args=[self.bpc.slug]))
        self.assertContains(resp, 'Descripción completa de BPC-157.')
        self.bpc.research_background = 'Lo que se ha estudiado de BPC-157.'
        self.bpc.save()
        resp = self.client.get(reverse('product_detail', args=[self.bpc.slug]))
        self.assertContains(resp, 'Lo que se ha estudiado de BPC-157.')
        self.assertNotContains(resp, 'Descripción completa de BPC-157.')

    def test_no_se_escapa_sintaxis_de_plantilla_al_html(self):
        """Django solo trata {# #} como comentario si cabe en una línea.

        Uno de dos líneas se renderiza tal cual y el visitante se lo come.
        """
        for url in (reverse('index'), reverse('catalog'),
                    reverse('product_detail', args=[self.bpc.slug])):
            html = self.client.get(url).content.decode()
            for resto in ('{#', '#}', '{%', '%}'):
                self.assertNotIn(resto, html, f'{url} deja escapar "{resto}"')

    def test_el_disolvente_se_mide_en_ml(self):
        self.assertEqual(self.agua_3ml.size_display, '3 ml')
        self.assertEqual(self.bpc.variants.first().size_display, '10 mg')


class PaquetesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cat = Category.objects.create(name='Recuperación')
        cls.bpc = crear_peptido(name='BPC-157', category=cat)
        cls.tb = crear_peptido(name='TB-500', category=cat)
        cls.agua = crear_peptido(name='BAC Water', category=cat,
                                 product_format=Peptide.FORMAT_SOLVENT)
        cls.v_bpc = PeptideVariant.objects.create(peptide=cls.bpc, size_mg=10, price=Decimal('64.95'), stock=10)
        cls.v_tb = PeptideVariant.objects.create(peptide=cls.tb, size_mg=10, price=Decimal('64.95'), stock=4)
        cls.v_agua = PeptideVariant.objects.create(peptide=cls.agua, size_mg=10, price=Decimal('9.95'), stock=50)
        cls.pack = Bundle.objects.create(
            name='Pack Recuperación', short_description='BPC y TB juntos',
            price=Decimal('119.95'))
        for variante in (cls.v_bpc, cls.v_tb, cls.v_agua):
            BundleItem.objects.create(bundle=cls.pack, variant=variante)

    def test_cuentas_del_paquete(self):
        self.assertEqual(self.pack.components_total(), Decimal('139.85'))
        self.assertEqual(self.pack.savings(), Decimal('19.90'))
        self.assertEqual(self.pack.savings_percent(), 14)

    def test_el_stock_lo_marca_el_componente_mas_escaso(self):
        self.assertEqual(self.pack.available_units(), 4)  # el TB-500
        self.assertTrue(self.pack.in_stock)

    def test_sin_stock_de_un_componente_el_paquete_se_agota(self):
        self.v_tb.stock = 0
        self.v_tb.save()
        self.assertEqual(self.pack.available_units(), 0)
        self.assertFalse(self.pack.in_stock)

    def test_componente_desactivado_agota_el_paquete(self):
        self.tb.is_active = False
        self.tb.save()
        self.assertEqual(self.pack.available_units(), 0)

    def test_el_desglose_suma_exactamente_el_precio(self):
        """El subtotal del pedido sale de las líneas: no puede sobrar un céntimo."""
        for unidades in (1, 2, 3, 7):
            lineas = desglosar_paquete(self.pack, unidades)
            total = sum(precio * n for _, n, precio in lineas)
            self.assertEqual(total, self.pack.price * unidades, f'{unidades} packs')

    def test_el_desglose_cuadra_con_precios_que_no_dividen_limpio(self):
        feo = Bundle.objects.create(name='Pack feo', short_description='x', price=Decimal('100.01'))
        BundleItem.objects.create(bundle=feo, variant=self.v_bpc, quantity=3)
        BundleItem.objects.create(bundle=feo, variant=self.v_tb, quantity=2)
        lineas = desglosar_paquete(feo)
        self.assertEqual(sum(precio * n for _, n, precio in lineas), Decimal('100.01'))
        # Se reparten las 5 unidades, aunque haga falta partirlas en dos líneas.
        self.assertEqual(sum(n for _, n, _ in lineas), 5)

    def test_pagina_de_packs(self):
        resp = self.client.get(reverse('bundles'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Pack Recuperación')

    def test_ficha_de_pack(self):
        resp = self.client.get(reverse('bundle_detail', args=[self.pack.slug]))
        self.assertEqual(resp.status_code, 200)
        # Django localiza los decimales: en español van con coma.
        self.assertContains(resp, '139,85')          # tachado
        self.assertContains(resp, '119,95')          # precio
        self.assertContains(resp, 'Un pack no es un blend')
        self.assertContains(resp, f'/producto/{self.bpc.slug}/')

    def test_pack_inactivo_da_404(self):
        self.pack.is_active = False
        self.pack.save()
        self.assertEqual(
            self.client.get(reverse('bundle_detail', args=[self.pack.slug])).status_code, 404)

    def test_pack_en_el_sitemap(self):
        self.assertContains(self.client.get('/sitemap.xml'), f'/pack/{self.pack.slug}/')
