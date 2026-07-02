"""
Comando: python manage.py informe_diario

Envía al admin un resumen diario del negocio: pedidos, ingresos, stock bajo.

Configurar en cron del VPS:
    0 8 * * * cd /home/peptidos/app && source venv/bin/activate && python manage.py informe_diario
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from decimal import Decimal
from orders.models import Order
from store.models import PeptideVariant


class Command(BaseCommand):
    help = 'Envía informe diario al admin'

    def handle(self, *args, **options):
        admin_email = getattr(settings, 'ADMIN_EMAIL', None)
        if not admin_email:
            self.stdout.write('ADMIN_EMAIL no configurado. Saltando informe.')
            return

        hoy = timezone.now().date()
        ayer = hoy - timedelta(days=1)

        # Pedidos de ayer
        pedidos_ayer = Order.objects.filter(created_at__date=ayer)
        ingresos_ayer = sum(p.total for p in pedidos_ayer.filter(status='paid')) or Decimal('0')
        pendientes = pedidos_ayer.filter(status='pending').count()

        # Pedidos del mes
        inicio_mes = hoy.replace(day=1)
        pedidos_mes = Order.objects.filter(created_at__date__gte=inicio_mes, status='paid')
        ingresos_mes = sum(p.total for p in pedidos_mes) or Decimal('0')

        # Stock bajo (menos de 5 unidades)
        stock_bajo = PeptideVariant.objects.filter(is_active=True, stock__lt=5, stock__gt=0)
        sin_stock = PeptideVariant.objects.filter(is_active=True, stock=0)

        # Construir informe
        lineas = [
            f"=== INFORME DIARIO EUROPEPTIVA — {ayer} ===\n",
            f"PEDIDOS AYER:",
            f"  Total: {pedidos_ayer.count()}",
            f"  Cobrados: {pedidos_ayer.filter(status='paid').count()} ({ingresos_ayer}€)",
            f"  Pendientes de pago: {pendientes}",
            f"\nMES EN CURSO ({inicio_mes} — hoy):",
            f"  Pedidos cobrados: {pedidos_mes.count()} ({ingresos_mes}€)",
        ]

        if stock_bajo.exists():
            lineas.append("\n⚠️  STOCK BAJO (< 5 uds):")
            for v in stock_bajo:
                lineas.append(f"  - {v.peptide.name} {v.size_mg}mg: {v.stock} uds")

        if sin_stock.exists():
            lineas.append("\n❌ SIN STOCK:")
            for v in sin_stock:
                lineas.append(f"  - {v.peptide.name} {v.size_mg}mg")

        # Pedidos pendientes de revisión
        pedidos_pendientes_pago = Order.objects.filter(status='pending', payment_method='bank_transfer')
        if pedidos_pendientes_pago.exists():
            lineas.append(f"\n📋 PEDIDOS ESPERANDO TRANSFERENCIA ({pedidos_pendientes_pago.count()}):")
            for p in pedidos_pendientes_pago[:10]:
                horas = (timezone.now() - p.created_at).total_seconds() / 3600
                lineas.append(f"  - {p.order_number} | {p.shipping_email} | {p.total}€ | {horas:.0f}h esperando")

        informe = '\n'.join(lineas)
        self.stdout.write(informe)

        try:
            send_mail(
                subject=f'[EuroPeptiva] Informe diario — {ayer}',
                message=informe,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@europeptiva.com'),
                recipient_list=[admin_email],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Informe enviado a {admin_email}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error enviando informe: {e}'))
