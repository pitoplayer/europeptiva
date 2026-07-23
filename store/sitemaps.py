from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Bundle, Peptide


class PeptideSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Peptide.objects.filter(is_active=True)

    def location(self, obj):
        return f'/producto/{obj.slug}/'


class BundleSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return Bundle.objects.filter(is_active=True)

    def location(self, obj):
        return reverse('bundle_detail', args=[obj.slug])


class StaticSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5

    def items(self):
        return ['index', 'catalog', 'bundles', 'certificates', 'bulk', 'about', 'contact', 'returns']

    def location(self, item):
        return reverse(item)
