from django.contrib import admin
from django.utils.html import format_html
from modeltranslation.admin import TranslationAdmin
from .models import BulkEnquiry, Bundle, BundleItem, Category, Peptide, PeptideVariant, Certificate


class PeptideVariantInline(admin.TabularInline):
    model = PeptideVariant
    extra = 1
    fields = ['size_mg', 'price', 'stock', 'fulfillment_level', 'reorder_point', 'sku', 'is_active']


class CertificateInline(admin.TabularInline):
    model = Certificate
    extra = 0
    fields = ['lab_name', 'lot_number', 'tested_date', 'purity', 'file', 'is_active']


# TranslationAdmin en vez de ModelAdmin: pinta un campo por idioma en los que
# están registrados en store/translation.py y reescribe prepopulated_fields al
# campo del idioma por defecto (slug se sigue generando desde el nombre en
# español, que es el que va en la URL).
@admin.register(Category)
class CategoryAdmin(TranslationAdmin):
    list_display = ['name', 'slug', 'is_active']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Peptide)
class PeptideAdmin(TranslationAdmin):
    list_display = ['name', 'category', 'product_format', 'purity', 'is_active', 'is_featured', 'stock_status']
    list_filter = ['category', 'product_format', 'is_active', 'is_featured']
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


class BundleItemInline(admin.TabularInline):
    model = BundleItem
    extra = 2


@admin.register(Bundle)
class BundleAdmin(TranslationAdmin):
    list_display = ['name', 'price', 'components_total', 'savings', 'savings_percent',
                    'available_units', 'is_active', 'is_featured']
    list_filter = ['is_active', 'is_featured']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [BundleItemInline]

    # Los tres son cálculos sobre los componentes, no columnas: sin esto el
    # admin no sabe cómo etiquetarlos en la lista.
    @admin.display(description='Suelto')
    def components_total(self, obj):
        return f'{obj.components_total()} €'

    @admin.display(description='Ahorro')
    def savings(self, obj):
        return f'{obj.savings()} €'

    @admin.display(description='%')
    def savings_percent(self, obj):
        return f'{obj.savings_percent()} %'

    @admin.display(description='Packs armables')
    def available_units(self, obj):
        return obj.available_units()


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
