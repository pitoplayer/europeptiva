from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Peptide, PeptideVariant


class PeptideVariantInline(admin.TabularInline):
    model = PeptideVariant
    extra = 1
    fields = ['size_mg', 'price', 'stock', 'fulfillment_level', 'reorder_point', 'sku', 'is_active']


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
    inlines = [PeptideVariantInline]

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
