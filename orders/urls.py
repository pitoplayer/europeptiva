from django.urls import path
from django.utils.translation import gettext_lazy as _
from . import views

urlpatterns = [
    path(_('carrito/'), views.cart_view, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path(_('confirmacion/<str:order_number>/'), views.order_confirmation, name='order_confirmation'),
    path(_('seguimiento/'), views.order_tracking, name='order_tracking'),
    path(_('pago/<str:order_number>/'), views.mollie_payment, name='mollie_payment'),
]
# Ojo: mollie_webhook NO está aquí. Mollie lo llama con una URL fija que no
# puede depender del idioma activo, así que vive en config/urls.py, fuera de
# i18n_patterns.
