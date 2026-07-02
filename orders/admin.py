from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ['product_name', 'variant_size_mg', 'unit_price', 'quantity', 'line_total']
    extra = 0

    def line_total(self, obj):
        return f"{obj.line_total}€"
    line_total.short_description = "Subtotal"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'shipping_email', 'status', 'payment_method', 'total', 'created_at']
    list_filter = ['status', 'payment_method', 'shipping_country']
    search_fields = ['order_number', 'shipping_email', 'shipping_last_name']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    list_editable = ['status']
    inlines = [OrderItemInline]

    fieldsets = (
        ('Pedido', {'fields': ('order_number', 'status', 'payment_method', 'payment_reference')}),
        ('Cliente', {'fields': ('user', 'shipping_first_name', 'shipping_last_name', 'shipping_email', 'shipping_phone')}),
        ('Envío', {'fields': ('shipping_address', 'shipping_city', 'shipping_postal_code', 'shipping_country')}),
        ('Totales', {'fields': ('subtotal', 'shipping_cost', 'total')}),
        ('Legal', {'fields': ('research_disclaimer_accepted', 'terms_accepted', 'rgpd_accepted')}),
        ('Notas', {'fields': ('notes', 'created_at', 'updated_at')}),
    )
