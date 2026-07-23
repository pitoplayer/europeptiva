from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.contrib.sitemaps.views import sitemap
from django.utils.translation import gettext_lazy as _
from orders.views import mollie_webhook
from store.sitemaps import PeptideSitemap, StaticSitemap

# Fuera de i18n_patterns: no dependen del idioma y no deben llevar prefijo.
urlpatterns = [
    path('gestion-interna/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    # Mollie llama a esta URL desde sus servidores: debe ser fija y sin
    # prefijo de idioma, por eso está fuera de i18n_patterns.
    path('pedidos/mollie-webhook/', mollie_webhook, name='mollie_webhook'),
    path('sitemap.xml', sitemap, {'sitemaps': {'peptides': PeptideSitemap, 'static': StaticSitemap}}, name='sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain'), name='robots'),
]

# prefix_default_language=False deja el español en la raíz: /catalogo/ sigue
# siendo /catalogo/ y solo el inglés lleva prefijo (/en/catalog/).
urlpatterns += i18n_patterns(
    path('', include('store.urls')),
    path(_('pedidos/'), include('orders.urls')),
    path(_('sobre-nosotros/'), TemplateView.as_view(template_name='pages/about.html', extra_context={
        'page_title': _('Sobre nosotros'),
        'page_description': _('EuroPeptiva: proveedor especializado en péptidos de investigación científica de origen europeo, con pureza certificada y envío refrigerado a España y la UE.'),
    }), name='about'),
    path(_('faq/'), TemplateView.as_view(template_name='pages/faq.html', extra_context={
        'page_title': _('Preguntas frecuentes'),
        'page_description': _('Resolvemos tus dudas sobre pureza, envío, almacenamiento y reconstitución de péptidos de investigación EuroPeptiva.'),
    }), name='faq'),
    path(_('privacidad/'), TemplateView.as_view(template_name='pages/privacy.html', extra_context={
        'page_title': _('Política de privacidad'),
        'page_description': _('Política de privacidad de EuroPeptiva: cómo tratamos tus datos personales conforme al RGPD.'),
    }), name='privacy'),
    path(_('aviso-legal/'), TemplateView.as_view(template_name='pages/legal.html', extra_context={
        'page_title': _('Aviso legal'),
        'page_description': _('Aviso legal e información sobre el responsable del sitio web europeptiva.com.'),
    }), name='legal'),
    path('cookies/', TemplateView.as_view(template_name='pages/cookies.html', extra_context={
        'page_title': _('Política de cookies'),
        'page_description': _('Información sobre las cookies técnicas necesarias que utiliza EuroPeptiva para el funcionamiento de la tienda.'),
    }), name='cookies'),
    prefix_default_language=False,
)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
