from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Peptide


class PeptideSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Peptide.objects.filter(is_active=True)

    def location(self, obj):
        return f'/producto/{obj.slug}/'


class StaticSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5

    def items(self):
        return ['index', 'catalog', 'certificates', 'about', 'contact']

    def location(self, item):
        return reverse(item)
