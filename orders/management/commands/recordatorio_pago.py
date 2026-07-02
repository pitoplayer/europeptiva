"""
Comando: python manage.py recordatorio_pago

Envía un email de recordatorio a los clientes con pedidos pendientes
de transferencia bancaria que llevan entre 24h y 47h sin pago.

Configurar en cron del VPS:
    0 10 * * * cd /home/peptidos/app && source venv/bin/activate && python manage.py recordatorio_pago
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from orders.models import Order


class Command(BaseCommand):
    help = 'Envía recordatorio de pago a pedidos pendientes de 24-47h'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Solo muestra a quién enviaría el recordatorio')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        ahora = timezone.now()
        desde = ahora - timedelta(hours=47)
        hasta = ahora - timedelta(hours=24)

        pedidos = Order.objects.filter(
            status='pending',
            payment_method='bank_transfer',
            created_at__range=(desde, hasta),
        )

        if not pedidos.exists():
            self.stdout.write('No hay pedidos que necesiten recordatorio en este momento.')
            return

        self.stdout.write(f'Enviando recordatorios a {pedidos.count()} clientes...')
        iban = getattr(settings, 'BANK_IBAN', '[IBAN pendiente]')
        holder = getattr(settings, 'BANK_HOLDER', '[Titular pendiente]')

        for order in pedidos:
            if dry_run:
                self.stdout.write(f'  [DRY RUN] Recordatorio a: {order.shipping_email} — {order.order_number}')
                continue

            try:
                send_mail(
                    subject=f'Recordatorio: tu pedido {order.order_number} espera tu transferencia',
                    message=f"""Hola {order.shipping_first_name},

Te recordamos que tu pedido {order.order_number} en EuroPeptiva está pendiente de pago por transferencia bancaria.

DATOS DE PAGO:
Titular: {holder}
IBAN: {iban}
Concepto: {order.order_number}
Importe: {order.total}€

Una vez recibamos la transferencia, procesaremos tu pedido en 24h.

⚠️ Si no recibimos el pago en las próximas 24h, el pedido será cancelado automáticamente.

¿Ya has realizado la transferencia? No te preocupes, puede tardar 1-2 días hábiles en procesarse.
¿Tienes algún problema? Escríbenos a info@europeptiva.com.

EuroPeptiva
""",
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@europeptiva.com'),
                    recipient_list=[order.shipping_email],
                    fail_silently=False,
                )
                self.stdout.write(f'  ✓ Recordatorio enviado a {order.shipping_email}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error enviando a {order.shipping_email}: {e}'))

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f'✓ {pedidos.count()} recordatorios enviados.'))
