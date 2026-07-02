from django.urls import path
from . import views

urlpatterns = [
    path('carrito/', views.cart_view, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('confirmacion/<str:order_number>/', views.order_confirmation, name='order_confirmation'),
    path('seguimiento/', views.order_tracking, name='order_tracking'),
    path('pago/<str:order_number>/', views.mollie_payment, name='mollie_payment'),
    path('mollie-webhook/', views.mollie_webhook, name='mollie_webhook'),
]
