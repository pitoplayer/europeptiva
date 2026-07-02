# STATUS — EuroPeptiva

## Estado actual

**Fase:** Semana 1, Días 1-2 completados ✓  
**Próximo:** Día 3 — modelos de pedidos (`orders/models.py`)

## Lo que está hecho

- Proyecto Django 5 inicializado con Python 3.11 (via uv)
- Apps: `store`, `accounts`, `orders`
- `settings.py` configurado con django-environ, idioma español, zona horaria Madrid
- SQLite para desarrollo local (PostgreSQL en producción/Hetzner)
- Modelos: `Category`, `Peptide`, `PeptideVariant` con stock, SKU, variantes por tamaño
- Migraciones aplicadas
- Admin Django configurado con gestión visual de productos y stock
- Superusuario: `admin` / `admin123` (solo local, cambiar en producción)

## Para arrancar el servidor local

```bash
cd /home/kaliuser/europeptiva
source .venv/bin/activate
python manage.py runserver
# Abrir http://localhost:8000/admin
```

## Próximos pasos

1. **Día 3:** Modelos de pedidos (`orders/models.py`) — Order, OrderItem
2. **Día 4:** Admin de pedidos
3. **Semana 2:** Frontend (templates, views, URLs del catálogo)

## Timeline

| Semana | Objetivo | Estado |
|--------|----------|--------|
| 1 | Modelos + admin Django | 🔄 En progreso |
| 2 | Frontend del catálogo | ⏳ Pendiente |
| 3 | Checkout + pagos + emails | ⏳ Pendiente |
| 4 | Legal, SEO, despliegue Hetzner | ⏳ Pendiente |
| **28 jul** | **Lanzamiento** | 🎯 |
