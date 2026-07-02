"""
Comando: python manage.py cancelar_pedidos_sin_pago

Cancela pedidos por transferencia bancaria que llevan más de 48h
sin confirmación de pago y restaura el stock.

Configurar en cron del VPS para ejecutar 2 veces al día:
    0 9,21 * * * cd /home/peptidos/app && source venv/bin/activate && python manage.py cancelar_pedidos_sin_pago
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from orders.models import Order


class Command(BaseCommand):
    help = 'Cancela pedidos por transferencia sin pago después de 48h'

    def add_arguments(self, parser):
        parser.add_argument('--horas', type=int, default=48, help='Horas de espera antes de cancelar (default: 48)')
        parser.add_argument('--dry-run', action='store_true', help='Solo muestra qué cancelaría, sin ejecutar')

    def handle(self, *args, **options):
        horas = options['horas']
        dry_run = options['dry_run']
        limite = timezone.now() - timedelta(hours=horas)

        pedidos_a_cancelar = Order.objects.filter(
            status='pending',
            payment_method='bank_transfer',
            created_at__lt=limite,
        )

        if not pedidos_a_cancelar.exists():
            self.stdout.write('No hay pedidos pendientes de cancelar.')
            return

        self.stdout.write(f'Pedidos a cancelar ({horas}h sin pago): {pedidos_a_cancelar.count()}')

        for order in pedidos_a_cancelar:
            if dry_run:
                self.stdout.write(f'  [DRY RUN] Cancelaría: {order.order_number} ({order.shipping_email}) — {order.total}€')
                continue

            # Restaurar stock
            for item in order.items.all():
                item.variant.stock += item.quantity
                item.variant.save()

            order.status = 'cancelled'
            order.save()

            # Notificar al cliente
            try:
                send_mail(
                    subject=f'Tu pedido {order.order_number} ha sido cancelado — EuroPeptiva',
                    message=f"""Hola {order.shipping_first_name},

Tu pedido {order.order_number} ha sido cancelado porque no recibimos la transferencia bancaria en el plazo de {horas} horas.

Si deseas realizar el pedido de nuevo, puedes hacerlo en europeptiva.com.
Si ya has realizado la transferencia y crees que hay un error, contáctanos en info@europeptiva.com indicando tu número de pedido.

EuroPeptiva
""",
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@europeptiva.com'),
                    recipient_list=[order.shipping_email],
                    fail_silently=True,
                )
            except Exception:
                pass

            self.stdout.write(self.style.WARNING(f'  Cancelado: {order.order_number} ({order.shipping_email})'))

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f'✓ {pedidos_a_cancelar.count()} pedidos cancelados y stock restaurado.'))
