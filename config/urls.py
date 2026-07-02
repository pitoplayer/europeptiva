from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.contrib.sitemaps.views import sitemap
from store.sitemaps import PeptideSitemap, StaticSitemap

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('store.urls')),
    path('pedidos/', include('orders.urls')),
    path('sobre-nosotros/', TemplateView.as_view(template_name='pages/about.html', extra_context={'page_title': 'Sobre nosotros'}), name='about'),
    path('contacto/', TemplateView.as_view(template_name='pages/contact.html', extra_context={'page_title': 'Contacto'}), name='contact'),
    path('privacidad/', TemplateView.as_view(template_name='pages/privacy.html', extra_context={'page_title': 'Política de privacidad'}), name='privacy'),
    path('aviso-legal/', TemplateView.as_view(template_name='pages/legal.html', extra_context={'page_title': 'Aviso legal'}), name='legal'),
    path('cookies/', TemplateView.as_view(template_name='pages/cookies.html', extra_context={'page_title': 'Política de cookies'}), name='cookies'),
    path('sitemap.xml', sitemap, {'sitemaps': {'peptides': PeptideSitemap, 'static': StaticSitemap}}, name='sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain'), name='robots'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
