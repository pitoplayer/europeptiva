from django.contrib import admin
from django.utils.html import format_html
from .models import BulkEnquiry, Category, Peptide, PeptideVariant, Certificate


class PeptideVariantInline(admin.TabularInline):
    model = PeptideVariant
    extra = 1
    fields = ['size_mg', 'price', 'stock', 'fulfillment_level', 'reorder_point', 'sku', 'is_active']


class CertificateInline(admin.TabularInline):
    model = Certificate
    extra = 0
    fields = ['lab_name', 'lot_number', 'tested_date', 'purity', 'file', 'is_active']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Peptide)
class PeptideAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'purity', 'is_active', 'is_featured', 'stock_status']
    list_filter = ['category', 'is_active', 'is_featured']
    search_fields = ['name', 'cas_number']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [PeptideVariantInline, CertificateInline]

    def stock_status(self, obj):
        variants = obj.variants.filter(is_active=True)
        total = sum(v.stock for v in variants)
        if total == 0:
            color = 'red'
        elif any(v.needs_reorder for v in variants):
            color = 'orange'
        else:
            color = 'green'
        return format_html('<span style="color: {};">{} uds</span>', color, total)
    stock_status.short_description = 'Stock total'


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['peptide', 'lab_name', 'lot_number', 'tested_date', 'purity', 'is_active']
    list_filter = ['lab_name', 'is_active']
    search_fields = ['peptide__name', 'lot_number']


@admin.register(BulkEnquiry)
class BulkEnquiryAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'name', 'organization', 'email', 'phone', 'colored_status']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'organization', 'email', 'message']
    list_editable = []
    readonly_fields = ['created_at']
    fieldsets = [
        ('Contacto', {'fields': ('name', 'organization', 'email', 'phone')}),
        ('Solicitud', {'fields': ('message', 'created_at')}),
        ('Seguimiento', {'fields': ('status',)}),
    ]

    def colored_status(self, obj):
        colors = {'new': 'red', 'quoted': 'orange', 'won': 'green', 'lost': 'gray'}
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.status, 'black'), obj.get_status_display())
    colored_status.short_description = 'Estado'
