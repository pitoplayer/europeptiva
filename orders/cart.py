from decimal import Decimal

from store.models import Bundle, PeptideVariant

# El carrito de sesión guarda variantes y paquetes en el mismo diccionario. Las
# variantes conservan su clave de siempre ("12") para no invalidar los carritos
# que ya estén abiertos en el navegador de alguien; los paquetes van con prefijo.
BUNDLE_PREFIX = 'bundle:'


def bundle_key(bundle_id):
    return f'{BUNDLE_PREFIX}{bundle_id}'


def is_bundle_key(key):
    return str(key).startswith(BUNDLE_PREFIX)


def bundle_id_from_key(key):
    return int(str(key)[len(BUNDLE_PREFIX):])


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
                # Ya formateada: el agua se vende en ml y los sprays no son
                # liofilizados, así que la plantilla no puede suponer "mg".
                'size_display': variant.size_display,
                'format_label': str(variant.peptide.format_label()),
                'slug': variant.peptide.slug,
            }
        self.cart[variant_id]['quantity'] += quantity
        self.save()

    def add_bundle(self, bundle_id, quantity=1):
        bundle = Bundle.objects.get(id=bundle_id, is_active=True)
        key = bundle_key(bundle.id)
        if key not in self.cart:
            self.cart[key] = {
                'quantity': 0,
                'price': str(bundle.price),
                'name': bundle.name,
                'size_mg': None,
                'slug': bundle.slug,
                'is_bundle': True,
            }
        self.cart[key]['quantity'] += quantity
        self.save()

    def remove(self, key):
        key = str(key)
        if key in self.cart:
            del self.cart[key]
            self.save()

    def update(self, key, quantity):
        key = str(key)
        if key in self.cart:
            if quantity <= 0:
                self.remove(key)
            else:
                self.cart[key]['quantity'] = quantity
                self.save()

    def save(self):
        self.session.modified = True

    def clear(self):
        self.session.pop('cart', None)
        self.save()

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def get_items(self):
        items = []
        for key, data in self.cart.items():
            items.append({
                # variant_id se conserva por compatibilidad con las plantillas
                # y el checkout; en un paquete es la clave con prefijo.
                'variant_id': key,
                'is_bundle': bool(data.get('is_bundle')),
                'name': data['name'],
                'size_mg': data.get('size_mg'),
                # Los carritos abiertos antes de este campo no lo traen: se
                # reconstruye a partir de los mg para no dejarlos en blanco.
                'size_display': data.get('size_display') or (
                    f"{data['size_mg']} mg" if data.get('size_mg') else ''),
                'format_label': data.get('format_label', ''),
                'price': Decimal(data['price']),
                'quantity': data['quantity'],
                'slug': data['slug'],
                'line_total': Decimal(data['price']) * data['quantity'],
            })
        return items
