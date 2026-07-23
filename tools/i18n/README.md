# Traducciones

Este entorno no tiene `gettext` (ni permisos para instalarlo), así que
`makemessages` y `compilemessages` no funcionan. En su lugar:

```bash
# 1. Extraer literales nuevos al .po (conserva lo ya traducido)
python tools/i18n/extract_po.py en

# 2. Rellenar los msgstr vacíos en locale/en/LC_MESSAGES/django.po

# 3. Compilar el .mo
python -c "import polib; po=polib.pofile('locale/en/LC_MESSAGES/django.po'); po.save_as_mofile('locale/en/LC_MESSAGES/django.mo')"
```

El `.mo` se commitea al repo: así el VPS tampoco necesita `gettext`.

## Dos trampas que cuestan horas

1. **Django duplica los `%` de los msgid**, tanto en `{% translate %}` como en
   `{% blocktranslate %}`, y los deshace al renderizar. Un msgid con `≥99%`
   debe estar en el catálogo como `≥99%%`, y su traducción también. El
   extractor ya lo hace.
2. **`{% blocktranslate %}` convierte `{{ var }}` en `%(var)s`** y respeta los
   espacios literalmente. Por eso los bloques se marcan en una sola línea.

Si `gettext` llega a estar disponible, se puede volver a `makemessages` sin
más: el formato del `.po` es estándar.
