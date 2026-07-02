# Plan: Tienda Online de Peptidos de Investigacion (España)

**Objetivo:** Construir una tienda online funcional para venta de peptidos de investigacion en España,
con Django, cumplimiento RGPD, y procesadores de pago compatibles con el nicho.

**Arquitectura:**
- Backend: Django 5 + PostgreSQL como base de datos relacional
- Frontend: Templates Django + Tailwind CSS + HTMX (sin React ni Vue, la IA genera el HTML)
- Hosting: Hetzner VPS en Alemania (RGPD compliant), Nginx + Gunicorn
- Pagos: Transferencia bancaria como base, Paycomet/Redsys como segunda capa

**Stack tecnico:**
- Python 3.11+, Django 5, django-allauth, Pillow, django-crispy-forms
- PostgreSQL 16, Redis (sesiones y cache)
- Tailwind CSS via CDN (sin Node), HTMX
- Nginx + Gunicorn + Certbot (SSL)
- Hetzner VPS (CX21: 2 vCPU, 4GB RAM, 40GB SSD ~6€/mes)

---

## ANTES DE EMPEZAR: Prerrequisitos

- [ ] Cuenta en Hetzner: https://www.hetzner.com/cloud
- [ ] Dominio registrado (Namecheap, Ionos, Arsys) apuntando al VPS
- [ ] Python 3.11+ instalado en local
- [ ] Git instalado
- [ ] Editor: VSCode + extension Cursor o Copilot para asistencia IA
- [ ] Cuenta en Paycomet (opcional semana 3): https://www.paycomet.com

---

## SEMANA 1: Fundamentos del Proyecto

**Meta:** Proyecto Django corriendo en local con modelos de datos completos y admin funcional.
Al final de la semana podras gestionar productos, categorias e inventario desde el admin de Django.

---

### Dia 1 — Entorno de desarrollo y estructura del proyecto

**Objetivo:** Django corriendo en local con base de datos creada.

Paso 1: Crear entorno virtual e instalar dependencias

```bash
mkdir peptidos-store && cd peptidos-store
python3 -m venv venv
source venv/bin/activate
pip install django==5.0 psycopg2-binary pillow django-environ
pip freeze > requirements.txt
```

Paso 2: Crear proyecto Django

```bash
django-admin startproject config .
python manage.py startapp store
python manage.py startapp accounts
python manage.py startapp orders
```

Paso 3: Estructura final esperada

```
peptidos-store/
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── store/          # Productos, catalogo, carrito
├── accounts/       # Registro, login, perfil
├── orders/         # Pedidos, checkout, pagos
├── templates/      # HTML global
├── static/         # CSS, JS, imagenes
├── media/          # Fotos de productos subidas
├── requirements.txt
└── manage.py
```

Paso 4: Configurar settings.py con variables de entorno

Crear archivo `.env` en la raiz:
```
SECRET_KEY=cambia-esto-por-una-clave-larga-aleatoria
DEBUG=True
DATABASE_URL=postgresql://user:password@localhost/peptidos_db
ALLOWED_HOSTS=localhost,127.0.0.1
```

Editar `config/settings.py`:
```python
import environ
env = environ.Env()
environ.Env.read_env()

SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

DATABASES = {
    'default': env.db('DATABASE_URL')
}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'store',
    'accounts',
    'orders',
]

LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'Europe/Madrid'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

Paso 5: Crear base de datos PostgreSQL

```bash
sudo -u postgres psql
CREATE DATABASE peptidos_db;
CREATE USER peptidos_user WITH PASSWORD 'tu_password_seguro';
GRANT ALL PRIVILEGES ON DATABASE peptidos_db TO peptidos_user;
\q
```

Verificacion: `python manage.py check` debe retornar "System check identified no issues."

---

### Dia 2 — Modelo de datos: Productos e Inventario

**Objetivo:** Modelos completos para catalogo de peptidos con inventario por lotes.

Archivo: `store/models.py`

```python
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Peptide(models.Model):
    # Identidad
    name = models.CharField(max_length=200, verbose_name="Nombre")
    slug = models.SlugField(unique=True, blank=True)
    cas_number = models.CharField(max_length=50, blank=True, verbose_name="Numero CAS")
    category = models.ForeignKey(Category, on_delete=models.PROTECT,
                                  related_name='peptides')

    # Descripcion
    short_description = models.CharField(max_length=300,
                                          verbose_name="Descripcion corta")
    description = models.TextField(verbose_name="Descripcion completa")
    molecular_formula = models.CharField(max_length=100, blank=True,
                                          verbose_name="Formula molecular")
    molecular_weight = models.DecimalField(max_digits=10, decimal_places=2,
                                            null=True, blank=True,
                                            verbose_name="Peso molecular (Da)")
    purity = models.CharField(max_length=20, default=">98%",
                               verbose_name="Pureza")

    # Media
    main_image = models.ImageField(upload_to='peptides/', blank=True,
                                    null=True, verbose_name="Imagen principal")

    # Estado
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    is_featured = models.BooleanField(default=False, verbose_name="Destacado")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Peptido"
        verbose_name_plural = "Peptidos"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_cheapest_variant(self):
        return self.variants.filter(is_active=True,
                                     stock__gt=0).order_by('price').first()


class PeptideVariant(models.Model):
    """
    Un peptido puede tener varias presentaciones: 2mg, 5mg, 10mg, etc.
    Cada variante tiene su propio precio y stock.
    """
    peptide = models.ForeignKey(Peptide, on_delete=models.CASCADE,
                                 related_name='variants')
    size_mg = models.PositiveIntegerField(verbose_name="Cantidad (mg)")
    price = models.DecimalField(max_digits=10, decimal_places=2,
                                 verbose_name="Precio (EUR)")
    stock = models.PositiveIntegerField(default=0, verbose_name="Stock")
    sku = models.CharField(max_length=50, unique=True, blank=True,
                            verbose_name="SKU")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Variante"
        verbose_name_plural = "Variantes"
        ordering = ['size_mg']
        unique_together = ['peptide', 'size_mg']

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = f"{self.peptide.slug}-{self.size_mg}mg"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.peptide.name} - {self.size_mg}mg - {self.price}€"

    @property
    def in_stock(self):
        return self.stock > 0
```

Verificacion:
```bash
python manage.py makemigrations store
python manage.py migrate
```

---

### Dia 3 — Modelo de datos: Pedidos y Clientes

Archivo: `orders/models.py`

```python
import uuid
from django.db import models
from django.contrib.auth.models import User
from store.models import PeptideVariant


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente de pago'),
        ('paid', 'Pago recibido'),
        ('processing', 'En preparacion'),
        ('shipped', 'Enviado'),
        ('delivered', 'Entregado'),
        ('cancelled', 'Cancelado'),
        ('refunded', 'Reembolsado'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('bank_transfer', 'Transferencia bancaria'),
        ('paycomet', 'Tarjeta (Paycomet)'),
        ('crypto', 'Criptomoneda'),
    ]

    # Identificador publico (para mostrar al cliente, no el ID interno)
    order_number = models.CharField(max_length=20, unique=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT,
                              null=True, blank=True, related_name='orders')

    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                               default='pending')
    payment_method = models.CharField(max_length=20,
                                       choices=PAYMENT_METHOD_CHOICES,
                                       default='bank_transfer')
    payment_reference = models.CharField(max_length=100, blank=True,
                                          verbose_name="Referencia de pago")

    # Datos de envio (copia en el momento del pedido, no FK)
    shipping_first_name = models.CharField(max_length=100)
    shipping_last_name = models.CharField(max_length=100)
    shipping_email = models.EmailField()
    shipping_phone = models.CharField(max_length=20, blank=True)
    shipping_address = models.CharField(max_length=250)
    shipping_city = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=10)
    shipping_country = models.CharField(max_length=3, default='ESP')

    # Totales
    subtotal = models.DecimalField(max_digits=10, decimal_places=2,
                                    default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2,
                                         default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Disclaimer: obligatorio antes de finalizar pedido
    research_disclaimer_accepted = models.BooleanField(default=False)
    terms_accepted = models.BooleanField(default=False)
    rgpd_accepted = models.BooleanField(default=False)

    notes = models.TextField(blank=True, verbose_name="Notas del cliente")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"PEP-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pedido {self.order_number} - {self.shipping_email}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE,
                               related_name='items')
    variant = models.ForeignKey(PeptideVariant, on_delete=models.PROTECT)

    # Copia de precios en el momento del pedido
    product_name = models.CharField(max_length=200)
    variant_size_mg = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"
```

---

### Dia 4 — Admin de Django: gestion visual del negocio

**Objetivo:** Interface de administracion completa sin codigo frontend.

Archivo: `store/admin.py`

```python
from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Peptide, PeptideVariant


class PeptideVariantInline(admin.TabularInline):
    model = PeptideVariant
    extra = 1
    fields = ['size_mg', 'price', 'stock', 'sku', 'is_active']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Peptide)
class PeptideAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'purity', 'is_active',
                    'is_featured', 'stock_status']
    list_filter = ['category', 'is_active', 'is_featured']
    search_fields = ['name', 'cas_number']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [PeptideVariantInline]

    def stock_status(self, obj):
        variants = obj.variants.filter(is_active=True)
        total_stock = sum(v.stock for v in variants)
        color = 'green' if total_stock > 0 else 'red'
        return format_html(
            '<span style="color: {};">{} uds</span>', color, total_stock
        )
    stock_status.short_description = 'Stock total'
```

Archivo: `orders/admin.py`

```python
from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ['product_name', 'variant_size_mg',
                        'unit_price', 'quantity', 'line_total']
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'shipping_email', 'status',
                    'payment_method', 'total', 'created_at']
    list_filter = ['status', 'payment_method']
    search_fields = ['order_number', 'shipping_email']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    list_editable = ['status']
```

Verificacion final semana 1:
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
# Abrir http://localhost:8000/admin y crear categorias + peptidos de prueba
```

---

## SEMANA 2: Frontend del Catalogo

**Meta:** Tienda visible con catalogo, busqueda y ficha de producto.
La IA (Cursor/Claude) genera el HTML. Tu solo configuras las URLs y views.

---

### Dia 5 — Layout base y pagina de inicio

**Objetivo:** Template base con header, footer y disclaimer visible.

Estructura de templates:

```
templates/
├── base.html              # Layout global
├── partials/
│   ├── header.html
│   ├── footer.html
│   └── disclaimer_banner.html
├── store/
│   ├── index.html         # Pagina de inicio
│   ├── catalog.html       # Listado de productos
│   └── product_detail.html
├── orders/
│   ├── cart.html
│   └── checkout.html
└── pages/
    ├── about.html
    ├── privacy.html
    ├── legal.html
    └── cookies.html
```

Contenido obligatorio en `templates/partials/disclaimer_banner.html`:
```html
<div class="bg-yellow-100 border-l-4 border-yellow-500 p-4 text-sm">
  <strong>AVISO IMPORTANTE:</strong>
  Todos los productos vendidos en esta tienda estan destinados EXCLUSIVAMENTE
  para uso en investigacion cientifica. NO son aptos para consumo humano,
  uso veterinario ni diagnostico. Al comprar, el cliente acepta estos terminos.
</div>
```

Prompt para Cursor/Claude para generar el base.html:
```
Genera un template Django base.html con:
- Tailwind CSS via CDN
- HTMX via CDN
- Header con logo, menu (Inicio, Catalogo, Contacto), carrito con contador
- Banner de disclaimer en amarillo
- Footer con links (Privacidad, Aviso Legal, Cookies, Contacto)
- Estilo minimalista, colores: blanco fondo, azul oscuro texto, verde para CTAs
- Variables de template: page_title, cart_count
No uses Node.js ni npm. Solo CDN.
```

---

### Dia 6 — Views y URLs del catalogo

Archivo: `store/views.py`

```python
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Category, Peptide


def index(request):
    featured = Peptide.objects.filter(is_active=True,
                                       is_featured=True)[:8]
    categories = Category.objects.filter(is_active=True)
    return render(request, 'store/index.html', {
        'featured_peptides': featured,
        'categories': categories,
        'page_title': 'Peptidos de Investigacion'
    })


def catalog(request):
    peptides = Peptide.objects.filter(is_active=True).prefetch_related('variants')
    category_slug = request.GET.get('category')
    query = request.GET.get('q')

    if category_slug:
        peptides = peptides.filter(category__slug=category_slug)
    if query:
        peptides = peptides.filter(
            Q(name__icontains=query) | Q(cas_number__icontains=query)
        )

    categories = Category.objects.filter(is_active=True)
    return render(request, 'store/catalog.html', {
        'peptides': peptides,
        'categories': categories,
        'current_category': category_slug,
        'query': query,
        'page_title': 'Catalogo de Peptidos'
    })


def product_detail(request, slug):
    peptide = get_object_or_404(Peptide, slug=slug, is_active=True)
    variants = peptide.variants.filter(is_active=True).order_by('size_mg')
    return render(request, 'store/product_detail.html', {
        'peptide': peptide,
        'variants': variants,
        'page_title': peptide.name
    })
```

Archivo: `store/urls.py`

```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('catalogo/', views.catalog, name='catalog'),
    path('producto/<slug:slug>/', views.product_detail,
          name='product_detail'),
]
```

Archivo: `config/urls.py`

```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('store.urls')),
    path('pedidos/', include('orders.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

### Dia 7 — Carrito de compra con sesiones

**Objetivo:** Carrito funcional sin base de datos, usando sesion de Django.

Archivo: `orders/cart.py` (clase reutilizable)

```python
from decimal import Decimal
from store.models import PeptideVariant


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart

    def add(self, variant_id, quantity=1):
        variant_id = str(variant_id)
        if variant_id not in self.cart:
            variant = PeptideVariant.objects.get(id=variant_id)
            self.cart[variant_id] = {
                'quantity': 0,
                'price': str(variant.price),
                'name': variant.peptide.name,
                'size_mg': variant.size_mg,
            }
        self.cart[variant_id]['quantity'] += quantity
        self.save()

    def remove(self, variant_id):
        variant_id = str(variant_id)
        if variant_id in self.cart:
            del self.cart[variant_id]
            self.save()

    def save(self):
        self.session.modified = True

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total(self):
        return sum(
            Decimal(item['price']) * item['quantity']
            for item in self.cart.values()
        )

    def get_items(self):
        return self.cart.values()

    def clear(self):
        del self.session['cart']
        self.save()
```

---

### Dia 8 — Templates del catalogo (generados con IA)

Prompt para Cursor para generar `store/catalog.html`:
```
Genera un template Django que extiende base.html con:
- Grid de productos 3 columnas (responsive: 1 col movil, 2 tablet, 3 desktop)
- Cada tarjeta: imagen del producto, nombre, precio desde X€, boton "Ver producto"
- Sidebar izquierdo con filtro por categorias (links ?category=slug)
- Barra de busqueda superior con input ?q=
- Si no hay productos: mensaje "No se encontraron peptidos"
- Variables Django: peptides, categories, current_category, query
- Tailwind CSS, sin JavaScript excepto HTMX si es necesario
```

Prompt para `store/product_detail.html`:
```
Genera un template Django para ficha de producto con:
- Imagen grande izquierda, info derecha
- Nombre, formula molecular, peso molecular, pureza, CAS number
- Selector de variante (botones de 2mg/5mg/10mg con precio)
- Boton "Añadir al carrito" (POST con HTMX, sin recargar pagina)
- Tabla de especificaciones tecnicas
- Seccion de descripcion completa
- Disclaimer: "Solo para investigacion cientifica"
- Variables Django: peptide, variants
```

---

## SEMANA 3: Checkout y Pagos

**Meta:** Flujo de compra completo con transferencia bancaria y emails automaticos.

---

### Dia 9 — Formulario de checkout

Archivo: `orders/forms.py`

```python
from django import forms


class CheckoutForm(forms.Form):
    first_name = forms.CharField(label='Nombre', max_length=100)
    last_name = forms.CharField(label='Apellidos', max_length=100)
    email = forms.EmailField(label='Email')
    phone = forms.CharField(label='Telefono', max_length=20, required=False)
    address = forms.CharField(label='Direccion', max_length=250)
    city = forms.CharField(label='Ciudad', max_length=100)
    postal_code = forms.CharField(label='Codigo Postal', max_length=10)

    payment_method = forms.ChoiceField(
        label='Metodo de pago',
        choices=[
            ('bank_transfer', 'Transferencia bancaria (mas rapido para peptidos)'),
            ('paycomet', 'Tarjeta de credito/debito'),
        ]
    )

    # Consentimientos obligatorios RGPD + legal
    research_disclaimer = forms.BooleanField(
        required=True,
        label='Confirmo que los productos son para investigacion '
              'cientifica exclusivamente y no para consumo humano.'
    )
    terms = forms.BooleanField(
        required=True,
        label='Acepto los terminos y condiciones de venta.'
    )
    rgpd = forms.BooleanField(
        required=True,
        label='Acepto la politica de privacidad y el tratamiento '
              'de mis datos personales (RGPD).'
    )
```

---

### Dia 10 — View de checkout y creacion de pedidos

Archivo: `orders/views.py`

```python
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from .cart import Cart
from .forms import CheckoutForm
from .models import Order, OrderItem


def cart_view(request):
    cart = Cart(request)
    if request.method == 'POST':
        variant_id = request.POST.get('variant_id')
        action = request.POST.get('action')
        if action == 'add' and variant_id:
            cart.add(variant_id)
        elif action == 'remove' and variant_id:
            cart.remove(variant_id)
    return render(request, 'orders/cart.html', {
        'cart': cart,
        'page_title': 'Tu carrito'
    })


def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect('catalog')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            order = Order.objects.create(
                shipping_first_name=data['first_name'],
                shipping_last_name=data['last_name'],
                shipping_email=data['email'],
                shipping_phone=data.get('phone', ''),
                shipping_address=data['address'],
                shipping_city=data['city'],
                shipping_postal_code=data['postal_code'],
                payment_method=data['payment_method'],
                research_disclaimer_accepted=data['research_disclaimer'],
                terms_accepted=data['terms'],
                rgpd_accepted=data['rgpd'],
                subtotal=cart.get_total(),
                shipping_cost=5,  # Ajustar segun logistica
                total=cart.get_total() + 5,
            )

            for variant_id, item in cart.cart.items():
                from store.models import PeptideVariant
                variant = PeptideVariant.objects.get(id=variant_id)
                OrderItem.objects.create(
                    order=order,
                    variant=variant,
                    product_name=item['name'],
                    variant_size_mg=item['size_mg'],
                    unit_price=item['price'],
                    quantity=item['quantity'],
                )
                # Reducir stock
                variant.stock -= item['quantity']
                variant.save()

            # Enviar emails
            _send_order_confirmation(order)
            _send_admin_notification(order)

            cart.clear()
            return redirect('order_confirmation', order_number=order.order_number)
    else:
        form = CheckoutForm()

    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'form': form,
        'page_title': 'Finalizar pedido'
    })


def order_confirmation(request, order_number):
    order = Order.objects.get(order_number=order_number)
    return render(request, 'orders/confirmation.html', {
        'order': order,
        'page_title': f'Pedido {order_number} confirmado'
    })


def _send_order_confirmation(order):
    if order.payment_method == 'bank_transfer':
        payment_instructions = f"""
INSTRUCCIONES DE PAGO POR TRANSFERENCIA:
Banco: CaixaBank (o el tuyo)
IBAN: ES00 0000 0000 0000 0000 0000
Concepto: {order.order_number}
Importe: {order.total}€

Tu pedido se procesara en cuanto recibamos la transferencia (1-2 dias habiles).
        """
    else:
        payment_instructions = "Procesando pago con tarjeta..."

    send_mail(
        subject=f'Pedido {order.order_number} recibido - [Tu tienda]',
        message=f"""
Hola {order.shipping_first_name},

Hemos recibido tu pedido {order.order_number}.

{payment_instructions}

Gracias por tu compra.
        """,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.shipping_email],
        fail_silently=False,
    )


def _send_admin_notification(order):
    send_mail(
        subject=f'NUEVO PEDIDO: {order.order_number} - {order.total}€',
        message=f"Nuevo pedido de {order.shipping_email}. Ver en admin.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.ADMIN_EMAIL],
        fail_silently=True,
    )
```

---

### Dia 11 — Email con SMTP (Gmail o Mailjet)

Añadir a `config/settings.py`:

```python
# Opcion 1: Gmail (solo para pruebas, limite bajo)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')  # App Password de Google
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@tutienda.com')
ADMIN_EMAIL = env('ADMIN_EMAIL')

# Opcion 2: Mailjet (recomendado para produccion, 6000 emails/mes gratis)
# EMAIL_HOST = 'in-v3.mailjet.com'
# EMAIL_PORT = 587
# EMAIL_HOST_USER = env('MAILJET_API_KEY')
# EMAIL_HOST_PASSWORD = env('MAILJET_SECRET_KEY')
```

Anadir al `.env`:
```
EMAIL_HOST_USER=tuemail@gmail.com
EMAIL_HOST_PASSWORD=xxxx-xxxx-xxxx-xxxx  # App Password Gmail
DEFAULT_FROM_EMAIL=Peptidos Investigacion <noreply@tutienda.com>
ADMIN_EMAIL=tuemail@gmail.com
```

---

### Dia 12 — Envio: calculo de costes (correos, MRW, GLS)

Archivo: `orders/shipping.py`

```python
from decimal import Decimal


SHIPPING_RATES = {
    'ESP': {
        'standard': Decimal('5.90'),   # Correos 24-72h
        'express': Decimal('9.90'),    # MRW/GLS 24h
        'free_threshold': Decimal('80.00'),  # Envio gratis desde 80€
    },
    'EU': {
        'standard': Decimal('14.90'),
        'free_threshold': Decimal('150.00'),
    }
}


def calculate_shipping(country_code, subtotal, method='standard'):
    rates = SHIPPING_RATES.get(country_code, SHIPPING_RATES['EU'])
    if subtotal >= rates['free_threshold']:
        return Decimal('0.00')
    return rates.get(method, rates['standard'])
```

---

## SEMANA 4: Legal, SEO y Despliegue en Produccion

**Meta:** Sitio en produccion en tu dominio con HTTPS, RGPD compliant y optimizado para buscadores.

---

### Dia 13 — Paginas legales obligatorias (RGPD España)

Estas paginas son OBLIGATORIAS por ley. Usar IA para generarlas, luego revisar con abogado.

Prompts para generar con IA:

Para `templates/pages/privacy.html`:
```
Genera una politica de privacidad RGPD para una tienda online española que vende
peptidos de investigacion. Incluye: responsable del tratamiento, finalidad,
base juridica, destinatarios, derechos del usuario (acceso, rectificacion,
supresion, portabilidad), plazo de conservacion, y datos de contacto.
Nombre empresa: [TU EMPRESA]. CIF: [TU CIF]. Email: [TU EMAIL].
```

Para `templates/pages/legal.html`:
```
Genera un aviso legal para tienda online española que vende peptidos de
investigacion. Incluye: datos del titular, objeto, terminos de uso,
propiedad intelectual, responsabilidad, legislacion aplicable (España/UE).
Incluir clausula clara: productos solo para investigacion, no consumo humano.
```

Para `templates/pages/cookies.html`:
```
Genera una politica de cookies RGPD para tienda online española.
Cookies propias: sesion de Django, carrito. Cookies de terceros: ninguna.
Sin Google Analytics ni redes sociales. Banner de consentimiento obligatorio.
```

Banner de cookies en `templates/partials/cookie_banner.html`:
```html
<div id="cookie-banner" class="fixed bottom-0 w-full bg-gray-900 text-white p-4"
     style="display: none;">
  <p>Usamos cookies tecnicas necesarias para el funcionamiento de la tienda.
     <a href="/cookies/" class="underline">Mas informacion</a></p>
  <button onclick="acceptCookies()"
          class="bg-green-500 px-4 py-2 rounded ml-4">Aceptar</button>
</div>
<script>
  if (!localStorage.getItem('cookies_accepted')) {
    document.getElementById('cookie-banner').style.display = 'block';
  }
  function acceptCookies() {
    localStorage.setItem('cookies_accepted', 'true');
    document.getElementById('cookie-banner').style.display = 'none';
  }
</script>
```

---

### Dia 14 — SEO basico

Archivo: `store/seo.py` (meta tags dinamicos)

```python
def get_meta_tags(peptide=None, category=None):
    base = {
        'site_name': 'Tu Tienda - Peptidos de Investigacion España',
        'robots': 'index, follow',
    }
    if peptide:
        base.update({
            'title': f"{peptide.name} - Peptido de Investigacion | Tu Tienda",
            'description': peptide.short_description[:155],
            'canonical': f"https://tudominio.com/producto/{peptide.slug}/",
        })
    return base
```

En cada template, en el `<head>`:
```html
<meta name="description" content="{{ meta.description }}">
<meta name="robots" content="{{ meta.robots }}">
<link rel="canonical" href="{{ meta.canonical }}">
```

Archivo `sitemap.xml` (Django tiene esto integrado):

```python
# config/urls.py - añadir
from django.contrib.sitemaps.views import sitemap
from store.sitemaps import PeptideSitemap

sitemaps = {'peptides': PeptideSitemap}
urlpatterns += [
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}),
]
```

```python
# store/sitemaps.py
from django.contrib.sitemaps import Sitemap
from .models import Peptide

class PeptideSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Peptide.objects.filter(is_active=True)

    def location(self, obj):
        return f'/producto/{obj.slug}/'
```

---

### Dia 15 — Preparar servidor Hetzner

Paso 1: Crear VPS en Hetzner

```
- Plan: CX21 (2 vCPU, 4GB RAM) = 5.83€/mes
- OS: Ubuntu 22.04
- Datacenter: Nuremberg (Alemania, dentro UE)
- Activar backups: +20% precio
- Anadir tu clave SSH publica
```

Paso 2: Configuracion inicial del servidor

```bash
# Conectar al VPS
ssh root@TU_IP_DEL_VPS

# Actualizar sistema
apt update && apt upgrade -y

# Crear usuario no-root
adduser peptidos
usermod -aG sudo peptidos
rsync --archive --chown=peptidos:peptidos ~/.ssh /home/peptidos

# Instalar dependencias
apt install -y python3.11 python3.11-venv python3-pip postgresql \
    postgresql-contrib nginx certbot python3-certbot-nginx git

# Firewall basico
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw enable
```

Paso 3: Configurar PostgreSQL en produccion

```bash
sudo -u postgres psql
CREATE DATABASE peptidos_prod;
CREATE USER peptidos_prod_user WITH PASSWORD 'password_muy_seguro';
GRANT ALL PRIVILEGES ON DATABASE peptidos_prod TO peptidos_prod_user;
\q
```

Paso 4: Clonar y configurar el proyecto

```bash
su - peptidos
git clone https://github.com/tuusuario/peptidos-store.git /home/peptidos/app
cd /home/peptidos/app
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# Crear .env de produccion (DEBUG=False, DB de prod, etc.)
nano .env
```

---

### Dia 16 — Nginx, Gunicorn y SSL

Archivo: `/etc/systemd/system/peptidos.service`

```ini
[Unit]
Description=Peptidos Store Gunicorn
After=network.target

[Service]
User=peptidos
Group=www-data
WorkingDirectory=/home/peptidos/app
ExecStart=/home/peptidos/app/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/run/peptidos.sock \
    config.wsgi:application
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl start peptidos
sudo systemctl enable peptidos
```

Archivo: `/etc/nginx/sites-available/peptidos`

```nginx
server {
    server_name tudominio.com www.tudominio.com;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        root /home/peptidos/app;
    }

    location /media/ {
        root /home/peptidos/app;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/peptidos.sock;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/peptidos /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# SSL gratuito con Let's Encrypt
sudo certbot --nginx -d tudominio.com -d www.tudominio.com
```

---

### Dia 17 — Script de deployment automatico

Archivo: `deploy.sh` (ejecutar en local para actualizar produccion)

```bash
#!/bin/bash
set -e

echo "Desplegando en produccion..."

ssh peptidos@TU_IP << 'ENDSSH'
    cd /home/peptidos/app
    git pull origin main
    source venv/bin/activate
    pip install -r requirements.txt --quiet
    python manage.py migrate --noinput
    python manage.py collectstatic --noinput
    sudo systemctl restart peptidos
    echo "Despliegue completado"
ENDSSH

echo "Listo. Sitio actualizado en https://tudominio.com"
```

```bash
chmod +x deploy.sh
```

---

## CHECKLIST FINAL ANTES DE LANZAR

Legal y compliance:
- [ ] Aviso legal publicado y accesible desde footer
- [ ] Politica de privacidad RGPD publicada
- [ ] Politica de cookies + banner de consentimiento
- [ ] Disclaimer de investigacion visible en TODAS las paginas
- [ ] Disclaimer obligatorio en el checkout antes de confirmar pedido
- [ ] Datos fiscales del negocio visibles (nombre, CIF, direccion)

Tecnico:
- [ ] HTTPS funcionando (SSL certbot)
- [ ] DEBUG=False en produccion
- [ ] Secret key diferente en produccion
- [ ] Backups de base de datos activados en Hetzner
- [ ] Emails de confirmacion llegando al cliente
- [ ] Admin protegido con password fuerte
- [ ] Cambiar URL del admin (por seguridad): /admin/ -> /gestion-interna/

SEO y marketing:
- [ ] sitemap.xml accesible
- [ ] robots.txt configurado
- [ ] Google Search Console registrado
- [ ] Meta descriptions en todos los productos

---

## RECURSOS Y HERRAMIENTAS IA PARA ACELERAR

Generacion de HTML/CSS (lo que menos sabes):
- Cursor IDE: editor con IA integrada, entiende tu proyecto completo
- v0.dev: genera componentes Tailwind desde descripcion en texto
- Claude.ai: genera templates Django completos con un buen prompt

Generacion de textos de productos:
- Usar Claude/ChatGPT para: descripciones tecnicas, meta descriptions SEO

Procesadores de pago alternativos (si Paycomet no funciona):
- Redsys via tu banco (pedir TPV virtual a BBVA/Sabadell/CaixaBank)
- Stripe solo si productos catalogados como "laboratorio/quimica de investigacion"
- Transferencia bancaria siempre como fallback (lo mas seguro)

---

## COSTES ESTIMADOS MENSUALES EN PRODUCCION

Hetzner CX21 VPS: ~6€/mes
Dominio (.com): ~12€/año = ~1€/mes
Email transaccional (Mailjet free hasta 6000/mes): 0€
SSL (Let's Encrypt): 0€
TOTAL: ~7-8€/mes

Sin comisiones de plataforma (Shopify cobra 2-3% por transaccion).
