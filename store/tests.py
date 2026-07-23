from datetime import date
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from django.core import mail
from django.test import override_settings

from .models import BulkEnquiry, Category, Certificate, Peptide, PeptideVariant


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

