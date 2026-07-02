# STATUS — EuroPeptiva

## Estado actual

**Fase:** Semana 1, Día 1 — pendiente de empezar  
**Proyecto:** Recién inicializado en GitHub (pitoplayer/europeptiva)

## Próximos pasos

1. Crear entorno virtual e instalar Django 5 + dependencias (ver `plan.md` Día 1)
2. Crear proyecto Django con apps: `store`, `accounts`, `orders`
3. Configurar PostgreSQL local
4. Objetivo de la semana: admin Django funcional con modelos de productos

## Timeline

| Semana | Objetivo |
|--------|----------|
| 1 (actual) | Modelos de datos + admin Django |
| 2 | Frontend del catálogo (templates + views) |
| 3 | Checkout + pagos + emails |
| 4 | Legal, SEO, despliegue en Hetzner |
| **28 jul** | **Lanzamiento** |

## Decisiones tomadas (no reabrir)

- Stack: Django 5 + PostgreSQL + Tailwind CDN + HTMX
- Hosting: Hetzner Alemania
- Pagos: Mollie + transferencia + Redsys
- Sin Shopify, sin Klarna, sin Stripe
