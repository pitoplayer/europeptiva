import json
import logging

from django.shortcuts import render, get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from django.utils.translation import gettext as _
from django.utils.safestring import mark_safe
from .models import Category, Peptide, PeptideVariant, Certificate
from .bulk import BULK_MIN_UNITS, BULK_TIERS
from .forms import BulkEnquiryForm, ContactForm
from .product_content import handling_block, storage_block

logger = logging.getLogger(__name__)


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
    # Las 3 imágenes del hero salen de la BD para que enlacen a su ficha y no
    # queden apuntando a un producto desactivado. Si falta alguno, se rellena
    # con destacados para no dejar el hueco vacío.
    hero_slugs = ['retatrutide', 'semaglutide', 'bpc-157']
    by_slug = {p.slug: p for p in Peptide.objects.filter(slug__in=hero_slugs, is_active=True)
               if p.main_image}
    hero_peptides = [by_slug[s] for s in hero_slugs if s in by_slug]
    if len(hero_peptides) < 3:
        chosen = {p.pk for p in hero_peptides}
        for p in featured:
            if len(hero_peptides) == 3:
                break
            if p.pk not in chosen and p.main_image:
                hero_peptides.append(p)
                chosen.add(p.pk)
    return render(request, 'store/index.html', {
        'featured_peptides': featured,
        'categories': categories,
        'latest_certificate': latest_certificate,
        'hero_peptides': hero_peptides,
        'page_title': _('Péptidos de Investigación'),
        'page_description': _('Péptidos de investigación de alta pureza (≥99% HPLC): Retatrutide, Semaglutide, BPC-157, TB-500 y más. Certificado de análisis por lote, stock en España y envío refrigerado.'),
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
        'page_title': _('Catálogo de Péptidos'),
        'page_description': _('Catálogo completo de péptidos de investigación EuroPeptiva: Retatrutide, Semaglutide, BPC-157, TB-500, BAC Water. Pureza ≥99% verificada por HPLC, con certificado de análisis por lote.'),
    })


BAC_WATER_SLUG = 'bac-water'
RELATED_COUNT = 4


def related_products(peptide):
    """Primero la misma categoría; si no llega a cuatro, se completa con el resto."""
    related = list(
        Peptide.objects.filter(is_active=True, category=peptide.category)
        .exclude(pk=peptide.pk)
        .order_by('-is_featured', 'name')[:RELATED_COUNT]
    )
    if len(related) < RELATED_COUNT:
        related += list(
            Peptide.objects.filter(is_active=True)
            .exclude(pk__in=[peptide.pk] + [p.pk for p in related])
            .order_by('-is_featured', 'name')[:RELATED_COUNT - len(related)]
        )
    return related


def bac_water_offer(peptide):
    """Variantes de agua bacteriostática que ofrecer junto a un liofilizado.

    Vacío si el producto no hay que reconstituirlo, si es el agua misma, o si
    está agotada: el bloque no se pinta.
    """
    if not peptide.needs_bac_water() or peptide.slug == BAC_WATER_SLUG:
        return []
    return list(
        PeptideVariant.objects.filter(
            peptide__slug=BAC_WATER_SLUG, peptide__is_active=True,
            is_active=True, stock__gt=0,
        ).select_related('peptide').order_by('size_mg')
    )


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
        'handling': handling_block(peptide.product_format),
        'storage': storage_block(peptide.product_format),
        'bac_water_variants': bac_water_offer(peptide),
        'related': related_products(peptide),
        'page_title': peptide.name,
        'page_description': peptide.short_description or _('%(name)s — péptido de investigación de pureza ≥99%%, verificado por HPLC. Certificado de análisis disponible.') % {'name': peptide.name},
        'product_schema_json': mark_safe(json.dumps(product_schema).replace('</', '<\\/')),
    })


def certificates(request):
    certs = Certificate.objects.filter(is_active=True, peptide__is_active=True).select_related('peptide')
    return render(request, 'store/certificates.html', {
        'certificates': certs,
        'page_title': _('Certificados de Análisis (CoA)'),
        'page_description': _('Certificados de análisis (CoA) por lote de los péptidos de investigación EuroPeptiva: identidad confirmada y pureza verificada por HPLC en laboratorios independientes.'),
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
        'page_title': _('Contacto'),
        'page_description': _('¿Tienes dudas sobre nuestros péptidos de investigación o certificados de análisis? Contacta con el equipo de EuroPeptiva.'),
    })


def bulk(request):
    """Compra al por mayor: tramos orientativos y solicitud de presupuesto."""
    sent = False
    if request.method == 'POST':
        form = BulkEnquiryForm(request.POST)
        if form.is_valid():
            # Se guarda primero: una solicitud al por mayor es un lead con
            # dinero detrás y no se puede perder si falla el SMTP.
            enquiry = form.save()
            admin_email = getattr(settings, 'ADMIN_EMAIL', '')
            if admin_email:
                try:
                    send_mail(
                        subject=f'[EuroPeptiva Al por mayor] {enquiry.name}',
                        message=(
                            f'Nombre: {enquiry.name}\n'
                            f'Empresa: {enquiry.organization or "—"}\n'
                            f'Email: {enquiry.email}\n'
                            f'Teléfono: {enquiry.phone or "—"}\n\n'
                            f'{enquiry.message}\n\n'
                            f'Gestiónala en /gestion-interna/store/bulkenquiry/{enquiry.pk}/change/'
                        ),
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@europeptiva.com'),
                        recipient_list=[admin_email],
                        fail_silently=True,
                    )
                except Exception:
                    logger.exception('No se pudo enviar el aviso de la solicitud al por mayor %s', enquiry.pk)
            sent = True
            form = BulkEnquiryForm()
    else:
        form = BulkEnquiryForm()

    return render(request, 'pages/bulk.html', {
        'form': form,
        'bulk_sent': sent,
        'bulk_tiers': BULK_TIERS,
        'bulk_min_units': BULK_MIN_UNITS,
        'page_title': _('Compra al por mayor'),
        'page_description': (
            'Precios por volumen en péptidos de investigación para laboratorios, '
            'centros de I+D y distribuidores. Descuentos desde 10 unidades por producto, '
            'presupuesto a medida en 24-48h.'
        ),
    })
