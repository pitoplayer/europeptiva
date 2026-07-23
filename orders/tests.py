from datetime import timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.core import mail
from django.core.management import call_command
from django.utils import timezone
from django.test import TestCase, override_settings
from django.urls import reverse

from store.models import Bundle, BundleItem, Category, Peptide, PeptideVariant

from .models import Order
from .shipping import amount_missing_for_free_shipping, calculate_shipping


def crear_variante(name='BPC-157', size_mg=10, price='49.90', stock=10):
    category, _ = Category.objects.get_or_create(name='Recuperación')
    peptide, _ = Peptide.objects.get_or_create(
        name=name,
        defaults={
            'category': category,
            'short_description': f'{name} para investigación',
            'description': f'Descripción completa de {name}.',
        },
    )
    return PeptideVariant.objects.create(
        peptide=peptide, size_mg=size_mg, price=Decimal(price), stock=stock,
    )


DATOS_CHECKOUT = {
    'first_name': 'Ana',
    'last_name': 'García',
    'email': 'ana@example.com',
    'address': 'Calle Mayor 1',
    'city': 'Madrid',
    'postal_code': '28001',
    'country': 'ESP',
    'payment_method': 'bank_transfer',
    'research_disclaimer': 'on',
    'terms': 'on',
    'rgpd': 'on',
}


class EnvioTest(TestCase):
    def test_espana_estandar(self):
        self.assertEqual(calculate_shipping('ESP', Decimal('50.00')), Decimal('7.99'))

    def test_espana_no_gratis_por_debajo_del_umbral(self):
        self.assertEqual(calculate_shipping('ESP', Decimal('149.99')), Decimal('7.99'))

    def test_espana_gratis_desde_150(self):
        self.assertEqual(calculate_shipping('ESP', Decimal('150.00')), Decimal('0.00'))

    def test_eu_estandar(self):
        self.assertEqual(calculate_shipping('DEU', Decimal('100.00')), Decimal('12.99'))

    def test_eu_gratis_desde_150(self):
        self.assertEqual(calculate_shipping('FRA', Decimal('150.00')), Decimal('0.00'))

    def test_pais_desconocido_usa_tarifa_eu(self):
        self.assertEqual(calculate_shipping('OTHER', Decimal('50.00')), Decimal('12.99'))

    def test_falta_para_envio_gratis(self):
        self.assertEqual(amount_missing_for_free_shipping(Decimal('120.00')), Decimal('30.00'))

    def test_no_falta_nada_si_se_alcanza_el_umbral(self):
        self.assertIsNone(amount_missing_for_free_shipping(Decimal('150.00')))


class CarritoTest(TestCase):
    def setUp(self):
        self.variant = crear_variante()

    def test_anadir_producto(self):
        resp = self.client.post(reverse('cart'), {'action': 'add', 'variant_id': self.variant.id})
        self.assertRedirects(resp, reverse('cart'))
        resp = self.client.get(reverse('cart'))
        self.assertContains(resp, 'BPC-157')

    def test_anadir_dos_veces_incrementa_cantidad(self):
        for _ in range(2):
            self.client.post(reverse('cart'), {'action': 'add', 'variant_id': self.variant.id})
        cart = self.client.session['cart']
        self.assertEqual(cart[str(self.variant.id)]['quantity'], 2)

    def test_actualizar_cantidad(self):
        self.client.post(reverse('cart'), {'action': 'add', 'variant_id': self.variant.id})
        self.client.post(reverse('cart'), {'action': 'update', 'variant_id': self.variant.id, 'quantity': 3})
        cart = self.client.session['cart']
        self.assertEqual(cart[str(self.variant.id)]['quantity'], 3)

    def test_actualizar_a_cero_elimina(self):
        self.client.post(reverse('cart'), {'action': 'add', 'variant_id': self.variant.id})
        self.client.post(reverse('cart'), {'action': 'update', 'variant_id': self.variant.id, 'quantity': 0})
        self.assertEqual(self.client.session['cart'], {})

    def test_eliminar_producto(self):
        self.client.post(reverse('cart'), {'action': 'add', 'variant_id': self.variant.id})
        self.client.post(reverse('cart'), {'action': 'remove', 'variant_id': self.variant.id})
        self.assertEqual(self.client.session['cart'], {})

    def test_cantidad_no_numerica_se_ignora(self):
        self.client.post(reverse('cart'), {'action': 'add', 'variant_id': self.variant.id})
        resp = self.client.post(reverse('cart'), {'action': 'update', 'variant_id': self.variant.id, 'quantity': 'abc'})
        self.assertRedirects(resp, reverse('cart'))
        cart = self.client.session['cart']
        self.assertEqual(cart[str(self.variant.id)]['quantity'], 1)

    def test_variante_inexistente_no_revienta(self):
        resp = self.client.post(reverse('cart'), {'action': 'add', 'variant_id': 99999})
        self.assertRedirects(resp, reverse('cart'))
        self.assertEqual(self.client.session.get('cart', {}), {})

    def test_se_pueden_anadir_dos_variantes_de_golpe(self):
        """El upsell de la ficha manda el péptido y el agua en el mismo POST."""
        agua = crear_variante(name='BAC Water', size_mg=3, price='6.90')
        resp = self.client.post(reverse('cart'), {
            'action': 'add', 'variant_id': [self.variant.id, agua.id],
        })
        self.assertRedirects(resp, reverse('cart'))
        cart = self.client.session['cart']
        self.assertEqual(len(cart), 2)
        self.assertEqual(cart[str(agua.id)]['quantity'], 1)

    def test_una_variante_mala_no_tumba_a_la_buena(self):
        resp = self.client.post(reverse('cart'), {
            'action': 'add', 'variant_id': [self.variant.id, 99999],
        })
        self.assertRedirects(resp, reverse('cart'))
        self.assertEqual(list(self.client.session['cart']), [str(self.variant.id)])


class CheckoutTest(TestCase):
    def setUp(self):
        self.variant = crear_variante(stock=10)

    def _llenar_carrito(self, quantity=1):
        self.client.post(reverse('cart'), {'action': 'add', 'variant_id': self.variant.id})
        if quantity > 1:
            self.client.post(reverse('cart'), {'action': 'update', 'variant_id': self.variant.id, 'quantity': quantity})

    def test_checkout_con_carrito_vacio_redirige_al_catalogo(self):
        resp = self.client.get(reverse('checkout'))
        self.assertRedirects(resp, reverse('catalog'))

    def test_checkout_get_muestra_resumen(self):
        self._llenar_carrito()
        resp = self.client.get(reverse('checkout'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'BPC-157')

    def test_pedido_valido_crea_order_y_descuenta_stock(self):
        self._llenar_carrito(quantity=2)
        resp = self.client.post(reverse('checkout'), DATOS_CHECKOUT)

        order = Order.objects.get()
        self.assertRedirects(resp, reverse('order_confirmation', args=[order.order_number]))
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.payment_method, 'bank_transfer')
        self.assertEqual(order.subtotal, Decimal('99.80'))
        self.assertEqual(order.shipping_cost, Decimal('7.99'))  # <150€, España
        self.assertEqual(order.total, Decimal('107.79'))
        self.assertEqual(order.items.count(), 1)

        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 8)
        self.assertEqual(self.client.session.get('cart', {}), {})

    def test_pedido_envia_emails_de_confirmacion_y_admin(self):
        self._llenar_carrito()
        with override_settings(ADMIN_EMAIL='admin@europeptiva.com'):
            self.client.post(reverse('checkout'), DATOS_CHECKOUT)
        destinatarios = sorted(m.to[0] for m in mail.outbox)
        self.assertEqual(destinatarios, ['admin@europeptiva.com', 'ana@example.com'])
        # El email al cliente incluye los datos de transferencia
        cliente = next(m for m in mail.outbox if m.to == ['ana@example.com'])
        self.assertIn('TRANSFERENCIA BANCARIA', cliente.body)
        self.assertIn(Order.objects.get().order_number, cliente.body)

    def test_formulario_sin_consentimientos_no_crea_pedido(self):
        self._llenar_carrito()
        datos = {k: v for k, v in DATOS_CHECKOUT.items() if k != 'rgpd'}
        resp = self.client.post(reverse('checkout'), datos)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)

    def test_envio_a_eu_aplica_tarifa_eu(self):
        self._llenar_carrito()
        datos = dict(DATOS_CHECKOUT, country='DEU')
        self.client.post(reverse('checkout'), datos)
        order = Order.objects.get()
        self.assertEqual(order.shipping_cost, Decimal('12.99'))
        self.assertEqual(order.total, Decimal('62.89'))

    def test_pedido_desde_150_lleva_envio_gratis(self):
        self._llenar_carrito(quantity=4)  # 4 × 49,90 = 199,60
        self.client.post(reverse('checkout'), DATOS_CHECKOUT)
        order = Order.objects.get()
        self.assertEqual(order.subtotal, Decimal('199.60'))
        self.assertEqual(order.shipping_cost, Decimal('0.00'))
        self.assertEqual(order.total, Decimal('199.60'))

    def test_stock_no_baja_de_cero(self):
        self.variant.stock = 1
        self.variant.save()
        self._llenar_carrito(quantity=3)
        self.client.post(reverse('checkout'), DATOS_CHECKOUT)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 0)

    def test_variante_borrada_del_catalogo_no_revienta_el_checkout(self):
        self._llenar_carrito()
        self.variant.delete()
        resp = self.client.post(reverse('checkout'), DATOS_CHECKOUT)
        self.assertRedirects(resp, reverse('cart'))
        self.assertEqual(Order.objects.count(), 0)

    def test_pago_mollie_redirige_al_flujo_de_pago(self):
        self._llenar_carrito()
        datos = dict(DATOS_CHECKOUT, payment_method='mollie')
        resp = self.client.post(reverse('checkout'), datos)
        order = Order.objects.get()
        self.assertRedirects(
            resp, reverse('mollie_payment', args=[order.order_number]),
            target_status_code=302,  # sin API key redirige a checkout
        )
        # Sin pagar todavía: no se envía email de confirmación
        self.assertEqual(len(mail.outbox), 0)


class SeguimientoTest(TestCase):
    def setUp(self):
        self.order = Order.objects.create(
            shipping_first_name='Ana', shipping_last_name='García',
            shipping_email='ana@example.com', shipping_address='Calle Mayor 1',
            shipping_city='Madrid', shipping_postal_code='28001',
            subtotal=Decimal('49.90'), shipping_cost=Decimal('5.90'), total=Decimal('55.80'),
        )

    def test_encuentra_pedido_con_numero_y_email(self):
        resp = self.client.post(reverse('order_tracking'), {
            'order_number': self.order.order_number.lower(),  # case-insensitive
            'email': 'ANA@example.com',
        })
        self.assertContains(resp, self.order.order_number)

    def test_email_incorrecto_no_revela_el_pedido(self):
        resp = self.client.post(reverse('order_tracking'), {
            'order_number': self.order.order_number,
            'email': 'otro@example.com',
        })
        self.assertContains(resp, 'No encontramos')


class MollieTest(TestCase):
    def _crear_pedido_mollie(self):
        return Order.objects.create(
            shipping_first_name='Ana', shipping_last_name='García',
            shipping_email='ana@example.com', shipping_address='Calle Mayor 1',
            shipping_city='Madrid', shipping_postal_code='28001',
            payment_method='mollie', total=Decimal('55.80'),
        )

    def test_sin_api_key_redirige_a_checkout_con_aviso(self):
        order = self._crear_pedido_mollie()
        resp = self.client.get(reverse('mollie_payment', args=[order.order_number]))
        self.assertRedirects(resp, reverse('checkout'), target_status_code=302)

    def test_pedido_ya_pagado_no_vuelve_a_mollie(self):
        order = self._crear_pedido_mollie()
        order.status = 'paid'
        order.save()
        resp = self.client.get(reverse('mollie_payment', args=[order.order_number]))
        self.assertRedirects(resp, reverse('order_confirmation', args=[order.order_number]))

    def test_webhook_solo_acepta_post(self):
        self.assertEqual(self.client.get(reverse('mollie_webhook')).status_code, 405)

    def test_webhook_sin_id_da_400(self):
        self.assertEqual(self.client.post(reverse('mollie_webhook'), {}).status_code, 400)

    @override_settings(MOLLIE_API_KEY='test_key')
    @patch('mollie.api.client.Client')
    def test_webhook_marca_pedido_como_pagado_y_envia_email(self, MockClient):
        order = self._crear_pedido_mollie()
        order.mollie_payment_id = 'tr_test123'
        order.save()

        mock = MockClient.return_value
        mock.payments.get.return_value = {'status': 'paid'}

        resp = self.client.post(reverse('mollie_webhook'), {'id': 'tr_test123'})
        self.assertEqual(resp.status_code, 200)

        order.refresh_from_db()
        self.assertEqual(order.status, 'paid')
        self.assertEqual(order.payment_reference, 'tr_test123')
        self.assertEqual(len(mail.outbox), 1)  # confirmación al cliente (sin ADMIN_EMAIL)

    @override_settings(MOLLIE_API_KEY='test_key')
    @patch('mollie.api.client.Client')
    def test_webhook_es_idempotente(self, MockClient):
        order = self._crear_pedido_mollie()
        order.mollie_payment_id = 'tr_test123'
        order.status = 'paid'
        order.save()

        mock = MockClient.return_value
        mock.payments.get.return_value = {'status': 'paid'}

        resp = self.client.post(reverse('mollie_webhook'), {'id': 'tr_test123'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)  # no reenvía emails


class PedidoConPaqueteTest(TestCase):
    """Un paquete entra en el pedido desglosado: una línea por componente."""

    def setUp(self):
        self.bpc = crear_variante(name='BPC-157', size_mg=10, price='64.95', stock=10)
        self.tb = crear_variante(name='TB-500', size_mg=10, price='64.95', stock=10)
        self.agua = crear_variante(name='BAC Water', size_mg=10, price='9.95', stock=10)
        self.pack = Bundle.objects.create(
            name='Pack Recuperación', short_description='x', price=Decimal('119.95'))
        for variante in (self.bpc, self.tb, self.agua):
            BundleItem.objects.create(bundle=self.pack, variant=variante)

    def _comprar(self, unidades=1):
        for _ in range(unidades):
            self.client.post(reverse('cart'), {'action': 'add_bundle', 'bundle_id': self.pack.id})
        return self.client.post(reverse('checkout'), DATOS_CHECKOUT)

    def test_el_paquete_llega_al_carrito_a_su_precio(self):
        self.client.post(reverse('cart'), {'action': 'add_bundle', 'bundle_id': self.pack.id})
        cart = self.client.session['cart']
        self.assertEqual(list(cart), [f'bundle:{self.pack.id}'])
        self.assertEqual(cart[f'bundle:{self.pack.id}']['price'], '119.95')

    def test_el_pedido_se_desglosa_y_las_lineas_suman_el_precio(self):
        self._comprar()
        order = Order.objects.get()
        self.assertEqual(order.items.count(), 3)
        self.assertEqual(sum(i.line_total for i in order.items.all()), Decimal('119.95'))
        self.assertEqual(order.subtotal, Decimal('119.95'))
        self.assertTrue(all(i.bundle_name == 'Pack Recuperación' for i in order.items.all()))

    def test_descuenta_el_stock_de_cada_componente(self):
        self._comprar(unidades=2)
        for variante in (self.bpc, self.tb, self.agua):
            variante.refresh_from_db()
            self.assertEqual(variante.stock, 8, variante.peptide.name)

    def test_paquete_y_producto_suelto_conviven(self):
        self.client.post(reverse('cart'), {'action': 'add_bundle', 'bundle_id': self.pack.id})
        self.client.post(reverse('cart'), {'action': 'add', 'variant_id': self.bpc.id})
        self.client.post(reverse('checkout'), DATOS_CHECKOUT)
        order = Order.objects.get()
        self.assertEqual(order.subtotal, Decimal('119.95') + Decimal('64.95'))
        # 3 del pack + 1 suelto, y el BPC del pack no se mezcla con el suelto
        self.assertEqual(order.items.count(), 4)
        self.bpc.refresh_from_db()
        self.assertEqual(self.bpc.stock, 8)

    def test_cancelar_devuelve_el_stock_del_paquete(self):
        self._comprar()
        order = Order.objects.get()
        order.created_at = timezone.now() - timedelta(hours=72)
        order.save()
        call_command('cancelar_pedidos_sin_pago')
        for variante in (self.bpc, self.tb, self.agua):
            variante.refresh_from_db()
            self.assertEqual(variante.stock, 10, variante.peptide.name)

    def test_paquete_inexistente_no_revienta(self):
        resp = self.client.post(reverse('cart'), {'action': 'add_bundle', 'bundle_id': 99999})
        self.assertRedirects(resp, reverse('cart'))
        self.assertEqual(self.client.session.get('cart', {}), {})
