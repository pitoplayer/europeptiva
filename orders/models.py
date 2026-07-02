import uuid
from django.db import models
from django.contrib.auth.models import User
from store.models import PeptideVariant


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente de pago'),
        ('paid', 'Pago recibido'),
        ('processing', 'En preparación'),
        ('shipped', 'Enviado'),
        ('delivered', 'Entregado'),
        ('cancelled', 'Cancelado'),
        ('refunded', 'Reembolsado'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('bank_transfer', 'Transferencia bancaria'),
        ('mollie', 'Tarjeta (Mollie)'),
        ('crypto', 'Criptomoneda'),
    ]

    order_number = models.CharField(max_length=20, unique=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='orders')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='bank_transfer')
    payment_reference = models.CharField(max_length=100, blank=True, verbose_name="Referencia de pago")

    shipping_first_name = models.CharField(max_length=100, verbose_name="Nombre")
    shipping_last_name = models.CharField(max_length=100, verbose_name="Apellidos")
    shipping_email = models.EmailField(verbose_name="Email")
    shipping_phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    shipping_address = models.CharField(max_length=250, verbose_name="Dirección")
    shipping_city = models.CharField(max_length=100, verbose_name="Ciudad")
    shipping_postal_code = models.CharField(max_length=10, verbose_name="Código Postal")
    shipping_country = models.CharField(max_length=3, default='ESP', verbose_name="País")

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    research_disclaimer_accepted = models.BooleanField(default=False)
    terms_accepted = models.BooleanField(default=False)
    rgpd_accepted = models.BooleanField(default=False)

    notes = models.TextField(blank=True, verbose_name="Notas del cliente")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"PEP-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pedido {self.order_number} — {self.shipping_email}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(PeptideVariant, on_delete=models.PROTECT)

    product_name = models.CharField(max_length=200)
    variant_size_mg = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"
