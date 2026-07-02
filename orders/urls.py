from django.urls import path
from . import views

urlpatterns = [
    path('carrito/', views.cart_view, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('confirmacion/<str:order_number>/', views.order_confirmation, name='order_confirmation'),
]
