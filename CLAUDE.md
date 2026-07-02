# EuroPeptiva

Tienda online de péptidos de investigación en España. Dominio: europeptiva.com + europeptiva.es.

## Sincronización (multi-dispositivo)

**Al empezar sesión:** ejecuta siempre `git pull` antes de hacer cualquier cosa.
**Al terminar sesión:** ejecuta `git add -A && git commit -m "session: <resumen de 1 línea>" && git push`.

## Estado actual

Lee `STATUS.md` al empezar — se mantiene actualizado con el estado y los próximos pasos.

## Contexto del negocio

- **Productos iniciales:** Retatrutide, Semaglutide, BPC-157, TB-500, BAC Water
- **Proveedor:** Peptaura (marketplace)
- **Socio:** se da de alta como autónomo a su nombre
- **Presupuesto inicial:** 500€
- **Fecha objetivo de lanzamiento:** 28 julio / primera semana de agosto 2026

## Stack técnico (decidido, no cambiar sin motivo)

- **Backend:** Django 5 + PostgreSQL
- **Frontend:** Templates Django + Tailwind CSS via CDN (sin Node) + HTMX
- **Hosting:** Hetzner VPS Alemania (CX21, ~6€/mes) — RGPD compliant
- **Pagos:** Mollie (principal) + transferencia bancaria + Redsys
- **Descartados:** Shopify, Klarna, Stripe

## Plan de trabajo

El plan detallado semana a semana está en `plan.md` — 4 semanas, ~17 días de trabajo.

## Notas del usuario

- Programa en Python pero conocimiento web nulo (no sabe HTML/CSS/Django).
- La IA genera el HTML y los templates; él configura URLs y lógica de negocio.
- Prefiere que no se pidan permisos salvo estrictamente necesario.
- Reunión con socio realizada 30/06/2026, planning completado.
