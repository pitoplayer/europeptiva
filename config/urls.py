from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.contrib.sitemaps.views import sitemap
from store.sitemaps import PeptideSitemap, StaticSitemap

urlpatterns = [
    path('gestion-interna/', admin.site.urls),
    path('', include('store.urls')),
    path('pedidos/', include('orders.urls')),
    path('sobre-nosotros/', TemplateView.as_view(template_name='pages/about.html', extra_context={
        'page_title': 'Sobre nosotros',
        'page_description': 'EuroPeptiva: proveedor especializado en péptidos de investigación científica de origen europeo, con pureza certificada y envío refrigerado a España y la UE.',
    }), name='about'),
    path('faq/', TemplateView.as_view(template_name='pages/faq.html', extra_context={
        'page_title': 'Preguntas frecuentes',
        'page_description': 'Resolvemos tus dudas sobre pureza, envío, almacenamiento y reconstitución de péptidos de investigación EuroPeptiva.',
    }), name='faq'),
    path('privacidad/', TemplateView.as_view(template_name='pages/privacy.html', extra_context={
        'page_title': 'Política de privacidad',
        'page_description': 'Política de privacidad de EuroPeptiva: cómo tratamos tus datos personales conforme al RGPD.',
    }), name='privacy'),
    path('aviso-legal/', TemplateView.as_view(template_name='pages/legal.html', extra_context={
        'page_title': 'Aviso legal',
        'page_description': 'Aviso legal e información sobre el responsable del sitio web europeptiva.com.',
    }), name='legal'),
    path('cookies/', TemplateView.as_view(template_name='pages/cookies.html', extra_context={
        'page_title': 'Política de cookies',
        'page_description': 'Información sobre las cookies técnicas necesarias que utiliza EuroPeptiva para el funcionamiento de la tienda.',
    }), name='cookies'),
    path('sitemap.xml', sitemap, {'sitemaps': {'peptides': PeptideSitemap, 'static': StaticSitemap}}, name='sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain'), name='robots'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
