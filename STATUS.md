# STATUS — EuroPeptiva

## Estado actual

**Fase:** Semanas 1-4 completadas ✓ + infraestructura deploy ✓ + Mollie integrado ✓  
**Próximo:** Diseño visual (en proceso con Claude Design), configurar SMTP y datos reales, desplegar en Hetzner

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
- Context processor para contador del carrito en header

### Semana 3 — Checkout y pagos ✓
- `orders/forms.py` — formulario de checkout con consentimientos RGPD
- `orders/views.py` — cart_view, checkout, order_confirmation
- `orders/shipping.py` — cálculo de gastos de envío (España/EU, gratis desde 80€)
- Templates: cart.html, checkout.html, confirmation.html mejorado
- Email de confirmación al cliente (transferencia bancaria o Mollie)
- Email de notificación al admin
- Flash messages Django integrados en base.html

### Semana 4 — Completa ✓
- requirements.txt limpio
- .env.example documentado con todas las variables
- Páginas legales skeleton (privacidad, aviso legal, cookies)
- Páginas estáticas (about, contact)
- Configuración de email en settings.py
- Datos bancarios configurables vía .env

### FASE EXTRA completada ✓

**Automatizaciones:**
- `cancelar_pedidos_sin_pago` — cancela transferencias pendientes a las 48h
- `recordatorio_pago` — email de recordatorio a las 24h
- `informe_diario` — resumen diario al admin
- `automation/peptaura_sync.py` — scraper de precios Peptaura
- `automation/crontab_vps.txt` — cron para el VPS

**Productos iniciales cargados (fixture):**
- Retatrutide (2mg/5mg/10mg)
- Semaglutide (2mg/5mg/10mg)
- BPC-157 (5mg/10mg/20mg)
- TB-500 (2mg/5mg/10mg)
- BAC Water (10ml)

**SEO:**
- sitemap.xml en /sitemap.xml
- robots.txt en /robots.txt
- django.contrib.sitemaps instalado

**Mollie (pagos con tarjeta):**
- Integración completa: flujo de pago + webhook
- Vista `mollie_payment` y `mollie_webhook`
- Campo `mollie_payment_id` en Order
- Solo necesita `MOLLIE_API_KEY` en .env para activarse

**Deploy:**
- `deploy.sh` — script de deploy con git pull + migrate + collectstatic + restart
- `deploy/nginx.conf` — configuración Nginx con SSL
- `deploy/europeptiva.service` — servicio systemd Gunicorn
- `deploy/setup_vps.sh` — setup inicial completo del VPS

## Para arrancar el servidor local

```bash
cd /home/kaliuser/europeptiva
source .venv/bin/activate
python manage.py runserver
```
Abre http://localhost:8000 y http://localhost:8000/admin (admin/admin123)

## Pendiente antes de lanzar

### Alta prioridad
- [x] Configurar SMTP en .env — IONOS (smtp.ionos.es:587, buzón info@europeptiva.com), probado end-to-end en producción
- [ ] Rellenar BANK_IBAN y BANK_HOLDER en .env con datos reales del autónomo (aplazado por ahora)
- [x] Rellenar URLs de Peptaura en automation/peptaura_sync.py — las 5 URLs reales están puestas. El script ya NO calcula ni aplica precios automáticamente: Peptaura mezcla listados "1 vial" y "Box of 10 vials" en la misma página sin forma fiable de distinguirlos por scraping, así que ahora solo informa (precio mínimo + enlace) para revisión manual. Ver docstring de automation/peptaura_sync.py.
- [ ] Darse de alta en Mollie → obtener API key → añadir a .env
- [x] Crear VPS Hetzner CX21 (Ubuntu 22.04, datacenter Alemania) — ya está en producción (europeptiva.com, SSL válido)
- [x] Ejecutar deploy/setup_vps.sh + deploy.sh — VPS desplegado y funcionando

### Diseño visual
- [x] Recoger resultado de Claude Design y aplicar al frontend
- [x] Generar imágenes de producto con Gemini (`tools/generar_imagenes.py`) y asignarlas en la home y en los 5 productos (`media/peptides/*.png`)
- [ ] Subir las imágenes generadas al VPS de producción (`python tools/generar_imagenes.py --subir` o `scp` manual) — solo están en local por ahora

### Legal (antes del lanzamiento)
- [ ] Rellenar datos fiscales reales en pages/privacy.html y legal.html
- [ ] Revisar textos legales con abogado/gestor
- [ ] Configurar Google Search Console

### Post-lanzamiento
- [ ] Cambiar URL del admin: /admin/ → /gestion-interna/
- [ ] Configurar dominio DNS en Hetzner (europeptiva.com + europeptiva.es)
- [ ] Conectar dominos .com y .es al VPS

## Timeline

| | Objetivo | Estado |
|--------|----------|--------|
| Semana 1 | Modelos + admin | ✅ Completo |
| Semana 2 | Frontend catálogo | ✅ Completo |
| Semana 3 | Checkout + pagos | ✅ Completo |
| Semana 4 | Legal, SEO, infra | ✅ Completo |
| Extras | Automatizaciones + Mollie + deploy | ✅ Completo |
| **28 jul** | **Lanzamiento** | 🎯 26 días |
