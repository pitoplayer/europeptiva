from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def representative_image(self):
        peptide = self.peptides.filter(is_active=True).exclude(main_image='').first()
        return peptide.main_image if peptide else None

    def active_product_count(self):
        return self.peptides.filter(is_active=True).count()

    def cheapest_price(self):
        variant = PeptideVariant.objects.filter(
            peptide__category=self, peptide__is_active=True, is_active=True, stock__gt=0
        ).order_by('price').first()
        return variant.price if variant else None


class Peptide(models.Model):
    # El formato decide qué bloques de reconstitución y conservación se pintan
    # en la ficha. Son idénticos para todos los productos del mismo formato, así
    # que viven en store/product_content.py y no duplicados en cada fila.
    FORMAT_VIAL = 'vial'
    FORMAT_SPRAY = 'spray'
    FORMAT_SOLVENT = 'solvent'
    FORMAT_CHOICES = [
        (FORMAT_VIAL, "Vial liofilizado (hay que reconstituir)"),
        (FORMAT_SPRAY, "Spray nasal líquido (listo para usar)"),
        (FORMAT_SOLVENT, "Disolvente o auxiliar"),
    ]

    name = models.CharField(max_length=200, verbose_name="Nombre")
    slug = models.SlugField(unique=True, blank=True)
    cas_number = models.CharField(max_length=50, blank=True, verbose_name="Número CAS")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='peptides')

    short_description = models.CharField(max_length=300, verbose_name="Descripción corta")
    description = models.TextField(verbose_name="Descripción completa")
    research_background = models.TextField(
        blank=True, verbose_name="Contexto de investigación",
        help_text="Qué se ha estudiado de esta molécula. Si se deja vacío, la ficha "
                  "enseña la descripción completa en su lugar. Sin afirmaciones de "
                  "eficacia, dosis ni uso humano.",
    )
    product_format = models.CharField(
        max_length=10, choices=FORMAT_CHOICES, default=FORMAT_VIAL,
        verbose_name="Formato",
    )
    molecular_formula = models.CharField(max_length=100, blank=True, verbose_name="Fórmula molecular")
    molecular_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Peso molecular (Da)")
    purity = models.CharField(max_length=20, default=">98%", verbose_name="Pureza")

    main_image = models.ImageField(upload_to='peptides/', blank=True, null=True, verbose_name="Imagen principal")

    is_active = models.BooleanField(default=True, verbose_name="Activo")
    is_featured = models.BooleanField(default=False, verbose_name="Destacado")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Péptido"
        verbose_name_plural = "Péptidos"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_cheapest_variant(self):
        return self.variants.filter(is_active=True, stock__gt=0).order_by('price').first()

    def format_label(self):
        """Etiqueta corta del formato, para las tarjetas del catálogo."""
        from .product_content import FORMAT_LABEL
        return FORMAT_LABEL.get(self.product_format, FORMAT_LABEL[self.FORMAT_VIAL])

    def needs_bac_water(self):
        return self.product_format == self.FORMAT_VIAL


class PeptideVariant(models.Model):
    FULFILLMENT_CHOICES = [
        ('stock_alto', 'Stock alto (los 5 productos estrella)'),
        ('stock_minimo', 'Stock mínimo (reposición por lotes)'),
    ]

    peptide = models.ForeignKey(Peptide, on_delete=models.CASCADE, related_name='variants')
    size_mg = models.PositiveIntegerField(verbose_name="Cantidad (mg)")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio (EUR)")
    stock = models.PositiveIntegerField(default=0, verbose_name="Stock")
    sku = models.CharField(max_length=50, unique=True, blank=True, verbose_name="SKU")
    is_active = models.BooleanField(default=True)

    fulfillment_level = models.CharField(
        max_length=20, choices=FULFILLMENT_CHOICES, default='stock_alto',
        verbose_name="Nivel de fulfillment",
    )
    reorder_point = models.PositiveIntegerField(
        default=5, verbose_name="Punto de pedido",
        help_text="Cuando el stock cae a este nivel o por debajo, hay que lanzar el siguiente lote al proveedor.",
    )

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
    def size_display(self):
        """El campo se llama size_mg, pero los disolventes se venden por volumen.

        El SKU se sigue generando con "mg" para no romper los que ya existen.
        """
        unit = 'ml' if self.peptide.product_format == Peptide.FORMAT_SOLVENT else 'mg'
        return f"{self.size_mg} {unit}"

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def needs_reorder(self):
        return self.stock <= self.reorder_point


class Certificate(models.Model):
    peptide = models.ForeignKey(Peptide, on_delete=models.CASCADE, related_name='certificates')
    lab_name = models.CharField(max_length=150, verbose_name="Laboratorio")
    lot_number = models.CharField(max_length=100, blank=True, verbose_name="Nº de lote")
    tested_date = models.DateField(null=True, blank=True, verbose_name="Fecha de análisis")
    purity = models.CharField(max_length=20, blank=True, verbose_name="Pureza (HPLC)")
    file = models.FileField(upload_to='certificates/', verbose_name="Archivo (PDF)")
    is_active = models.BooleanField(default=True, verbose_name="Publicado")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Certificado de análisis"
        verbose_name_plural = "Certificados de análisis"
        ordering = ['peptide__name', '-tested_date']

    def __str__(self):
        return f"{self.peptide.name} — {self.lab_name} ({self.lot_number})"


class BulkEnquiry(models.Model):
    STATUS_CHOICES = [
        ('new', _('Sin atender')),
        ('quoted', _('Presupuesto enviado')),
        ('won', _('Convertida en pedido')),
        ('lost', _('Descartada')),
    ]

    name = models.CharField(max_length=120, verbose_name=_("Nombre y apellidos"))
    organization = models.CharField(max_length=150, blank=True, verbose_name=_("Empresa / laboratorio"))
    email = models.EmailField(verbose_name=_("Email"))
    phone = models.CharField(max_length=40, blank=True, verbose_name=_("Teléfono / WhatsApp"))
    message = models.TextField(verbose_name=_("Productos y cantidades"))
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='new', verbose_name=_("Estado"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Solicitud al por mayor")
        verbose_name_plural = _("Solicitudes al por mayor")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.email}) — {self.get_status_display()}"
