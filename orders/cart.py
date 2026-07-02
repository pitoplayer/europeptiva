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
                'slug': variant.peptide.slug,
            }
        self.cart[variant_id]['quantity'] += quantity
        self.save()

    def remove(self, variant_id):
        variant_id = str(variant_id)
        if variant_id in self.cart:
            del self.cart[variant_id]
            self.save()

    def update(self, variant_id, quantity):
        variant_id = str(variant_id)
        if variant_id in self.cart:
            if quantity <= 0:
                self.remove(variant_id)
            else:
                self.cart[variant_id]['quantity'] = quantity
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
        for variant_id, data in self.cart.items():
            items.append({
                'variant_id': variant_id,
                'name': data['name'],
                'size_mg': data['size_mg'],
                'price': Decimal(data['price']),
                'quantity': data['quantity'],
                'slug': data['slug'],
                'line_total': Decimal(data['price']) * data['quantity'],
            })
        return items
