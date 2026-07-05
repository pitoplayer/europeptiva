import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string
from django.conf import settings as django_settings
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from .cart import Cart
from .forms import CheckoutForm
from .models import Order, OrderItem
from .shipping import calculate_shipping
from store.models import PeptideVariant

logger = logging.getLogger(__name__)


def cart_view(request):
    cart = Cart(request)
    if request.method == 'POST':
        variant_id = request.POST.get('variant_id')
        action = request.POST.get('action')
        if action == 'add' and variant_id:
            cart.add(variant_id)
            messages.success(request, 'Producto añadido al carrito.')
        elif action == 'remove' and variant_id:
            cart.remove(variant_id)
        elif action == 'update' and variant_id:
            try:
                qty = int(request.POST.get('quantity', 1))
                cart.update(variant_id, qty)
            except (ValueError, TypeError):
                pass
        return redirect('cart')

    return render(request, 'orders/cart.html', {
        'items': cart.get_items(),
        'total': cart.get_total(),
        'page_title': 'Tu carrito',
    })


def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect('catalog')

    cart_items = cart.get_items()
    subtotal = cart.get_total()

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            shipping_cost = calculate_shipping(data['country'], subtotal)
            total = subtotal + shipping_cost

            order = Order.objects.create(
                shipping_first_name=data['first_name'],
                shipping_last_name=data['last_name'],
                shipping_email=data['email'],
                shipping_phone=data.get('phone', ''),
                shipping_address=data['address'],
                shipping_city=data['city'],
                shipping_postal_code=data['postal_code'],
                shipping_country=data['country'],
                notes=data.get('notes', ''),
                payment_method=data['payment_method'],
                research_disclaimer_accepted=data['research_disclaimer'],
                terms_accepted=data['terms'],
                rgpd_accepted=data['rgpd'],
                subtotal=subtotal,
                shipping_cost=shipping_cost,
                total=total,
            )

            for item in cart_items:
                variant = PeptideVariant.objects.get(id=item['variant_id'])
                OrderItem.objects.create(
                    order=order,
                    variant=variant,
                    product_name=item['name'],
                    variant_size_mg=item['size_mg'],
                    unit_price=item['price'],
                    quantity=item['quantity'],
                )
                variant.stock = max(0, variant.stock - item['quantity'])
                variant.save()

            cart.clear()
            if order.payment_method == 'mollie':
                return redirect('mollie_payment', order_number=order.order_number)
            _send_order_confirmation(order)
            _send_admin_notification(order)
            return redirect('order_confirmation', order_number=order.order_number)
    else:
        form = CheckoutForm()

    shipping_preview = calculate_shipping('ESP', subtotal)
    return render(request, 'orders/checkout.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_preview': shipping_preview,
        'form': form,
        'page_title': 'Finalizar pedido',
    })


def order_confirmation(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, 'orders/confirmation.html', {
        'order': order,
        'bank_iban': getattr(django_settings, 'BANK_IBAN', ''),
        'bank_holder': getattr(django_settings, 'BANK_HOLDER', ''),
        'page_title': f'Pedido {order_number} confirmado',
    })


def _send_order_confirmation(order):
    bank_iban = getattr(django_settings, 'BANK_IBAN', '')
    bank_holder = getattr(django_settings, 'BANK_HOLDER', '')
    from_email = getattr(django_settings, 'DEFAULT_FROM_EMAIL', 'noreply@europeptiva.com')

    context = {
        'order': order,
        'bank_iban': bank_iban,
        'bank_holder': bank_holder,
    }
    subject = f'Pedido {order.order_number} recibido — EuroPeptiva'
    html_body = render_to_string('emails/order_confirmation.html', context)
    text_body = (
        f"Hola {order.shipping_first_name},\n\n"
        f"Hemos recibido tu pedido {order.order_number} por {order.total}€.\n\n"
        f"Método de pago: {order.get_payment_method_display()}\n"
    )
    if order.payment_method == 'bank_transfer':
        text_body += f"\nTRANSFERENCIA BANCARIA:\nTitular: {bank_holder}\nIBAN: {bank_iban}\nConcepto: {order.order_number}\nImporte: {order.total}€\n"

    try:
        msg = EmailMultiAlternatives(subject, text_body, from_email, [order.shipping_email])
        msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=True)
    except Exception:
        logger.exception("Fallo al enviar email de confirmación para el pedido %s", order.order_number)


def order_tracking(request):
    order = None
    error = None
    if request.method == 'POST':
        order_num = request.POST.get('order_number', '').strip().upper()
        email = request.POST.get('email', '').strip().lower()
        if order_num and email:
            try:
                order = Order.objects.get(
                    order_number=order_num,
                    shipping_email__iexact=email
                )
            except Order.DoesNotExist:
                error = 'No encontramos ningún pedido con esos datos. Comprueba el número de pedido y el email.'
        else:
            error = 'Por favor, introduce el número de pedido y el email.'

    return render(request, 'orders/tracking.html', {
        'order': order,
        'error': error,
        'page_title': 'Seguimiento de pedido',
    })


def mollie_payment(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if order.status != 'pending' or order.payment_method != 'mollie':
        return redirect('order_confirmation', order_number=order_number)

    api_key = getattr(django_settings, 'MOLLIE_API_KEY', '')
    site_url = getattr(django_settings, 'SITE_URL', 'http://localhost:8000')

    if not api_key:
        messages.error(request, 'Pago con tarjeta no disponible en este momento. Por favor elige transferencia bancaria.')
        return redirect('checkout')

    try:
        from mollie.api.client import Client
        mollie = Client()
        mollie.set_api_key(api_key)

        payment = mollie.payments.create({
            'amount': {'currency': 'EUR', 'value': f'{order.total:.2f}'},
            'description': f'EuroPeptiva — Pedido {order.order_number}',
            'redirectUrl': f'{site_url}/pedidos/confirmacion/{order.order_number}/',
            'webhookUrl': f'{site_url}/pedidos/mollie-webhook/',
            'metadata': {'order_number': order.order_number},
        })
        order.mollie_payment_id = payment['id']
        order.save()
        return redirect(payment['_links']['checkout']['href'])
    except Exception:
        logger.exception("Fallo al crear el pago Mollie para el pedido %s", order.order_number)
        messages.error(request, 'Error al procesar el pago. Inténtalo de nuevo.')
        return redirect('order_confirmation', order_number=order_number)


@csrf_exempt
def mollie_webhook(request):
    if request.method != 'POST':
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['POST'])

    payment_id = request.POST.get('id')
    if not payment_id:
        from django.http import HttpResponse
        return HttpResponse(status=400)

    api_key = getattr(django_settings, 'MOLLIE_API_KEY', '')
    if not api_key:
        from django.http import HttpResponse
        return HttpResponse(status=200)

    try:
        from mollie.api.client import Client
        from django.http import HttpResponse
        mollie = Client()
        mollie.set_api_key(api_key)

        payment = mollie.payments.get(payment_id)
        order = Order.objects.filter(mollie_payment_id=payment_id).first()

        if order and payment['status'] == 'paid' and order.status == 'pending':
            order.status = 'paid'
            order.payment_reference = payment_id
            order.save()
            _send_order_confirmation(order)
            _send_admin_notification(order)

        return HttpResponse(status=200)
    except Exception:
        logger.exception("Fallo procesando webhook de Mollie para payment_id %s", payment_id)
        from django.http import HttpResponse
        return HttpResponse(status=200)


def _send_admin_notification(order):
    admin_email = getattr(django_settings, 'ADMIN_EMAIL', None)
    if not admin_email:
        return
    try:
        send_mail(
            subject=f'NUEVO PEDIDO: {order.order_number} — {order.total}€',
            message=f"Nuevo pedido de {order.shipping_email}.\nMétodo de pago: {order.get_payment_method_display()}\nTotal: {order.total}€",
            from_email=getattr(django_settings, 'DEFAULT_FROM_EMAIL', 'noreply@europeptiva.com'),
            recipient_list=[admin_email],
            fail_silently=True,
        )
    except Exception:
        logger.exception("Fallo al enviar notificación de admin para el pedido %s", order.order_number)
