from django.db import models
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


class Peptide(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nombre")
    slug = models.SlugField(unique=True, blank=True)
    cas_number = models.CharField(max_length=50, blank=True, verbose_name="Número CAS")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='peptides')

    short_description = models.CharField(max_length=300, verbose_name="Descripción corta")
    description = models.TextField(verbose_name="Descripción completa")
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


class PeptideVariant(models.Model):
    peptide = models.ForeignKey(Peptide, on_delete=models.CASCADE, related_name='variants')
    size_mg = models.PositiveIntegerField(verbose_name="Cantidad (mg)")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio (EUR)")
    stock = models.PositiveIntegerField(default=0, verbose_name="Stock")
    sku = models.CharField(max_length=50, unique=True, blank=True, verbose_name="SKU")
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
