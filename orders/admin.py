from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ['product_name', 'variant_size_mg', 'bundle_name', 'unit_price', 'quantity', 'line_total']
    extra = 0

    def line_total(self, obj):
        return f"{obj.line_total}€"
    line_total.short_description = "Subtotal"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'shipping_full_name', 'shipping_email', 'colored_status', 'payment_badge', 'total_display', 'created_at']
    list_filter = ['status', 'payment_method', 'shipping_country', 'created_at']
    search_fields = ['order_number', 'shipping_email', 'shipping_last_name', 'shipping_first_name']
    readonly_fields = ['order_number', 'mollie_payment_id', 'created_at', 'updated_at']
    list_editable = ['status'] if False else []  # disabled — use actions instead
    actions = ['mark_paid', 'mark_processing', 'mark_shipped', 'mark_cancelled']
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]

    fieldsets = (
        ('Pedido', {'fields': ('order_number', 'status', 'payment_method', 'payment_reference', 'mollie_payment_id')}),
        ('Cliente', {'fields': ('user', 'shipping_first_name', 'shipping_last_name', 'shipping_email', 'shipping_phone')}),
        ('Dirección de envío', {'fields': ('shipping_address', 'shipping_city', 'shipping_postal_code', 'shipping_country')}),
        ('Importes', {'fields': ('subtotal', 'shipping_cost', 'total')}),
        ('Legal', {'fields': ('research_disclaimer_accepted', 'terms_accepted', 'rgpd_accepted')}),
        ('Notas y fechas', {'fields': ('notes', 'created_at', 'updated_at')}),
    )

    def shipping_full_name(self, obj):
        return f"{obj.shipping_first_name} {obj.shipping_last_name}"
    shipping_full_name.short_description = "Cliente"

    def colored_status(self, obj):
        colors = {
            'pending': '#f59e0b',
            'paid': '#10b981',
            'processing': '#3b82f6',
            'shipped': '#8b5cf6',
            'delivered': '#059669',
            'cancelled': '#ef4444',
            'refunded': '#6b7280',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="color:{}; font-weight:600;">● {}</span>',
            color, obj.get_status_display()
        )
    colored_status.short_description = "Estado"

    def payment_badge(self, obj):
        icons = {'bank_transfer': '🏦', 'mollie': '💳', 'crypto': '₿'}
        icon = icons.get(obj.payment_method, '?')
        return format_html('{} {}', icon, obj.get_payment_method_display())
    payment_badge.short_description = "Pago"

    def total_display(self, obj):
        return format_html('<strong>{}€</strong>', obj.total)
    total_display.short_description = "Total"

    @admin.action(description="Marcar como PAGADO")
    def mark_paid(self, request, queryset):
        queryset.update(status='paid')

    @admin.action(description="Marcar como EN PREPARACIÓN")
    def mark_processing(self, request, queryset):
        queryset.update(status='processing')

    @admin.action(description="Marcar como ENVIADO")
    def mark_shipped(self, request, queryset):
        queryset.update(status='shipped')

    @admin.action(description="Marcar como CANCELADO")
    def mark_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
