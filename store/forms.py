from django import forms

from .bulk import BULK_MIN_UNITS
from .models import BulkEnquiry


class BulkEnquiryForm(forms.ModelForm):
    INPUT_CLASS = ('w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm '
                   'focus:outline-none focus:ring-2 focus:ring-accent')

    class Meta:
        model = BulkEnquiry
        fields = ['name', 'organization', 'email', 'phone', 'message']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': f'Ej.: 20 viales de Retatrutide 10mg y 10 de BPC-157 5mg. '
                               f'Mínimo {BULK_MIN_UNITS} unidades por producto.',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = self.INPUT_CLASS


class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    subject = forms.CharField(max_length=200)
    message = forms.CharField(widget=forms.Textarea)
