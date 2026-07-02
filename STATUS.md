# STATUS — EuroPeptiva

## Estado actual

**Fase:** Semanas 1-3 completadas ✓ + páginas legales skeleton ✓  
**Próximo:** Configurar SMTP, datos bancarios reales, cargar productos en admin, desplegar en Hetzner

## Lo que está hecho

### Semana 1 — Modelos ✓
- Django 5 + Python 3.11 (via uv)
- Apps: store, accounts, orders
- Models: Category, Peptide, PeptideVariant (con stock, SKU, variantes)
- Models: Order, OrderItem (con estados, métodos de pago, datos de envío)
- Admin completo para productos y pedidos
- Superusuario: admin / admin123

### Semana 2 — Frontend ✓
- `store/views.py` — index, catálogo, ficha de producto
- `orders/cart.py` — carrito en sesión (add/remove/update)
- Templates completos: base.html, header, footer, disclaimer, cookie banner
- Páginas: inicio (hero + destacados + por qué nosotros), catálogo con filtros y búsqueda, ficha de producto con selector de variante y añadir al carrito

### Semana 3 — Checkout y pagos ✓
- `orders/forms.py` — formulario de checkout con consentimientos RGPD
- `orders/views.py` — cart_view, checkout, order_confirmation
- `orders/shipping.py` — cálculo de gastos de envío (España/EU, gratis desde 80€)
- Templates: cart.html, checkout.html, confirmation.html
- Email de confirmación al cliente (transferencia bancaria o Mollie)
- Email de notificación al admin

### Semana 4 — Parcial ✓
- requirements.txt limpio
- .env.example documentado
- Páginas legales skeleton (privacidad, aviso legal, cookies)
- Páginas estáticas (about, contact)
- Configuración de email en settings.py
- Datos bancarios configurables vía .env

## Para arrancar el servidor local

```bash
cd /home/kaliuser/europeptiva
source .venv/bin/activate
python manage.py runserver
```
Abre http://localhost:8000 y http://localhost:8000/admin (admin/admin123)

## Pendiente antes de lanzar

### Técnico
- [ ] Configurar SMTP en .env (Gmail App Password o Mailjet)
- [ ] Rellenar BANK_IBAN y BANK_HOLDER en .env
- [ ] Cargar productos iniciales en /admin (Retatrutide, Semaglutide, BPC-157, TB-500, BAC Water)
- [ ] Crear VPS en Hetzner (CX21, Ubuntu 22.04, Alemania)
- [ ] Configurar PostgreSQL en producción
- [ ] Desplegar con Nginx + Gunicorn + Certbot (ver plan.md Días 15-16)
- [ ] Cambiar URL del admin: /admin/ → /gestion-interna/

### Legal (antes del lanzamiento)
- [ ] Rellenar datos fiscales reales en templates/pages/privacy.html y legal.html
- [ ] Revisar con abogado
- [ ] Configurar Google Search Console

### Mollie (pagos con tarjeta)
- [ ] Darse de alta en Mollie (mollie.com)
- [ ] Instalar mollie-api-python y conectar webhook
- [ ] O como alternativa: solo transferencia bancaria en el lanzamiento v1

## Timeline

| | Objetivo | Estado |
|--------|----------|--------|
| Semana 1 | Modelos + admin | ✅ Completo |
| Semana 2 | Frontend catálogo | ✅ Completo |
| Semana 3 | Checkout + pagos | ✅ Completo |
| Semana 4 | Legal, SEO, Hetzner | 🔄 Parcial |
| **28 jul** | **Lanzamiento** | 🎯 26 días |
