import json

from django.shortcuts import render, get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from django.utils.safestring import mark_safe
from .models import Category, Peptide, Certificate
from .forms import ContactForm


def index(request):
    featured = Peptide.objects.filter(is_active=True, is_featured=True).prefetch_related('variants')[:8]
    categories = Category.objects.filter(is_active=True)
    # Lote real para el badge del hero: el CoA publicado más reciente
    latest_certificate = (Certificate.objects
                          .filter(is_active=True, peptide__is_active=True)
                          .exclude(lot_number='')
                          .exclude(purity='')
                          .order_by('-tested_date')
                          .first())
    return render(request, 'store/index.html', {
        'featured_peptides': featured,
        'categories': categories,
        'latest_certificate': latest_certificate,
        'page_title': 'Péptidos de Investigación',
        'page_description': 'Péptidos de investigación de alta pureza (≥99% HPLC): Retatrutide, Semaglutide, BPC-157, TB-500 y más. Sintetizados en la UE, con certificado de análisis por lote y envío refrigerado.',
    })


def catalog(request):
    from django.core.paginator import Paginator
    peptides = Peptide.objects.filter(is_active=True).prefetch_related('variants')
    category_slug = request.GET.get('category')
    query = request.GET.get('q', '').strip()

    if category_slug:
        peptides = peptides.filter(category__slug=category_slug)
    if query:
        peptides = peptides.filter(
            Q(name__icontains=query) |
            Q(cas_number__icontains=query) |
            Q(short_description__icontains=query)
        )

    paginator = Paginator(peptides, 12)
    page = request.GET.get('page')
    peptides_page = paginator.get_page(page)

    categories = Category.objects.filter(is_active=True)
    return render(request, 'store/catalog.html', {
        'peptides': peptides_page,
        'categories': categories,
        'current_category': category_slug,
        'query': query,
        'page_title': 'Catálogo de Péptidos',
        'page_description': 'Catálogo completo de péptidos de investigación EuroPeptiva: Retatrutide, Semaglutide, BPC-157, TB-500, BAC Water. Pureza ≥99% verificada por HPLC, con certificado de análisis por lote.',
    })


def product_detail(request, slug):
    peptide = get_object_or_404(Peptide, slug=slug, is_active=True)
    variants = list(peptide.variants.filter(is_active=True).order_by('size_mg'))
    certificate = peptide.certificates.filter(is_active=True).order_by('-tested_date').first()

    product_schema = {
        '@context': 'https://schema.org',
        '@type': 'Product',
        'name': peptide.name,
        'description': peptide.short_description,
        'sku': variants[0].sku if variants else peptide.slug,
        'brand': {'@type': 'Brand', 'name': 'EuroPeptiva'},
        'offers': [
            {
                '@type': 'Offer',
                'sku': v.sku,
                'price': str(v.price),
                'priceCurrency': 'EUR',
                'availability': 'https://schema.org/InStock' if v.in_stock else 'https://schema.org/OutOfStock',
                'url': request.build_absolute_uri(),
            }
            for v in variants
        ],
    }
    if peptide.main_image:
        product_schema['image'] = request.build_absolute_uri(peptide.main_image.url)

    return render(request, 'store/product_detail.html', {
        'peptide': peptide,
        'variants': variants,
        'certificate': certificate,
        'page_title': peptide.name,
        'page_description': peptide.short_description or f'{peptide.name} — péptido de investigación de pureza ≥99%, verificado por HPLC. Certificado de análisis disponible.',
        'product_schema_json': mark_safe(json.dumps(product_schema).replace('</', '<\\/')),
    })


def certificates(request):
    certs = Certificate.objects.filter(is_active=True, peptide__is_active=True).select_related('peptide')
    return render(request, 'store/certificates.html', {
        'certificates': certs,
        'page_title': 'Certificados de Análisis (CoA)',
        'page_description': 'Certificados de análisis (CoA) por lote de los péptidos de investigación EuroPeptiva: identidad confirmada y pureza verificada por HPLC en laboratorios independientes.',
    })


def contact(request):
    sent = False
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            admin_email = getattr(settings, 'ADMIN_EMAIL', '')
            if admin_email:
                try:
                    send_mail(
                        subject=f'[EuroPeptiva Contacto] {d["subject"]}',
                        message=f'De: {d["name"]} <{d["email"]}>\n\n{d["message"]}',
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@europeptiva.com'),
                        recipient_list=[admin_email],
                        fail_silently=True,
                    )
                except Exception:
                    pass
            sent = True

    return render(request, 'pages/contact.html', {
        'contact_sent': sent,
        'page_title': 'Contacto',
        'page_description': '¿Tienes dudas sobre nuestros péptidos de investigación o certificados de análisis? Contacta con el equipo de EuroPeptiva.',
    })
