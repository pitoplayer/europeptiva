from django.urls import path
from django.utils.translation import gettext_lazy as _
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path(_('catalogo/'), views.catalog, name='catalog'),
    path(_('producto/<slug:slug>/'), views.product_detail, name='product_detail'),
    path(_('certificados/'), views.certificates, name='certificates'),
    path(_('contacto/'), views.contact, name='contact'),
    path(_('al-por-mayor/'), views.bulk, name='bulk'),
]
