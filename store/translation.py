"""Campos de la base de datos que se traducen.

Registrar un campo aquí hace que modeltranslation añada una columna por idioma
(`description_es`, `description_en`) y que `obj.description` devuelva la del
idioma activo. El campo original se queda en la tabla y modeltranslation lo usa
como fallback cuando la traducción está vacía.

No se traducen los nombres de producto: son nombres químicos (Retatrutide,
BPC-157, GHK-Cu) idénticos en cualquier idioma. Tampoco `purity`, `cas_number`
ni `molecular_formula`, que son valores, no texto.
"""

from modeltranslation.translator import TranslationOptions, register

from .models import Category, Peptide


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('name', 'description')


@register(Peptide)
class PeptideTranslationOptions(TranslationOptions):
    fields = ('short_description', 'description', 'research_background')
