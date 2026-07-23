from django.utils.translation import gettext_lazy as _
from django import forms

COUNTRY_CHOICES = [
    ('ESP', 'España'),
    ('PRT', 'Portugal'),
    ('FRA', 'Francia'),
    ('DEU', 'Alemania'),
    ('ITA', 'Italia'),
    ('NLD', 'Países Bajos'),
    ('BEL', 'Bélgica'),
    ('POL', 'Polonia'),
    ('OTHER', 'Otro país UE'),
]


class CheckoutForm(forms.Form):
    first_name = forms.CharField(label=_('Nombre'), max_length=100, widget=forms.TextInput(attrs={'class': 'form-input'}))
    last_name = forms.CharField(label=_('Apellidos'), max_length=100, widget=forms.TextInput(attrs={'class': 'form-input'}))
    email = forms.EmailField(label=_('Email'), widget=forms.EmailInput(attrs={'class': 'form-input'}))
    phone = forms.CharField(label=_('Teléfono'), max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-input'}))
    address = forms.CharField(label=_('Dirección completa'), max_length=250, widget=forms.TextInput(attrs={'class': 'form-input'}))
    city = forms.CharField(label=_('Ciudad'), max_length=100, widget=forms.TextInput(attrs={'class': 'form-input'}))
    postal_code = forms.CharField(label=_('Código Postal'), max_length=10, widget=forms.TextInput(attrs={'class': 'form-input'}))
    country = forms.ChoiceField(label=_('País'), choices=COUNTRY_CHOICES, widget=forms.Select(attrs={'class': 'form-input'}))
    notes = forms.CharField(label=_('Notas del pedido (opcional)'), required=False, widget=forms.Textarea(attrs={'class': 'form-input', 'rows': 3}))

    payment_method = forms.ChoiceField(
        label=_('Método de pago'),
        choices=[
            ('bank_transfer', 'Transferencia bancaria (procesamos en 1-2 días hábiles)'),
            ('mollie', 'Tarjeta de crédito/débito (Mollie)'),
        ],
        widget=forms.RadioSelect,
    )

    research_disclaimer = forms.BooleanField(
        required=True,
        label=_('Confirmo que los productos son exclusivamente para investigación científica y no para consumo humano.'),
    )
    terms = forms.BooleanField(
        required=True,
        label=_('Acepto los términos y condiciones de venta.'),
    )
    rgpd = forms.BooleanField(
        required=True,
        label=_('Acepto la política de privacidad y el tratamiento de mis datos personales (RGPD).'),
    )
