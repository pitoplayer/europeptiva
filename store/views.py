from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Category, Peptide


def index(request):
    featured = Peptide.objects.filter(is_active=True, is_featured=True).prefetch_related('variants')[:8]
    categories = Category.objects.filter(is_active=True)
    return render(request, 'store/index.html', {
        'featured_peptides': featured,
        'categories': categories,
        'page_title': 'Péptidos de Investigación — EuroPeptiva',
    })


def catalog(request):
    peptides = Peptide.objects.filter(is_active=True).prefetch_related('variants')
    category_slug = request.GET.get('category')
    query = request.GET.get('q', '').strip()

    if category_slug:
        peptides = peptides.filter(category__slug=category_slug)
    if query:
        peptides = peptides.filter(Q(name__icontains=query) | Q(cas_number__icontains=query))

    categories = Category.objects.filter(is_active=True)
    return render(request, 'store/catalog.html', {
        'peptides': peptides,
        'categories': categories,
        'current_category': category_slug,
        'query': query,
        'page_title': 'Catálogo de Péptidos',
    })


def product_detail(request, slug):
    peptide = get_object_or_404(Peptide, slug=slug, is_active=True)
    variants = peptide.variants.filter(is_active=True).order_by('size_mg')
    return render(request, 'store/product_detail.html', {
        'peptide': peptide,
        'variants': variants,
        'page_title': peptide.name,
    })
