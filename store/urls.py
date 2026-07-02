from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('catalogo/', views.catalog, name='catalog'),
    path('producto/<slug:slug>/', views.product_detail, name='product_detail'),
    path('contacto/', views.contact, name='contact'),
]
