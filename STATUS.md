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

**Catálogo actual (fixture `store/fixtures/initial_products.json`), 18 productos en 6 categorías** — precios y variantes tomados de `Catalogo europeptiva.xlsx` (columna "Precio Venta") y de datos enviados por proveedor (Tayeb Sanca, 2026-07-09), descripciones de `descripciones_europeptiva.txt` y reescritas al estilo corto del sitio:
- Pérdida de grasa: Retatrutide (10/20/30/40mg), Semaglutide (10/20mg), Tesamorelin (10mg), Tirzepatide (10/20mg)
- Recuperación: BPC-157 (10mg), TB-500 (10mg), Wolverine Blend — TB-500+BPC-157 (10+10mg), IGF-1 LR3 (1mg)
- Disolventes y auxiliares: BAC Water (3ml/10ml)
- Cabello y piel: GHK-Cu (50/100mg), Melanotan I (10mg), Melanotan II (10mg), Glow70 Blend — GHK-Cu+Melanotan I+BPC-157 (70mg)
- Spray nasal: Semax (10mg, líquido listo para usar), Selank (10mg, líquido listo para usar)
- **Longevidad y Antienvejecimiento** (categoría nueva, 2026-07-09): MOTS-c (10/40mg), Glutatión (1500mg), NAD+ (500/1000mg)

**Ampliación 2026-07-09 (7 productos nuevos, datos del proveedor vía Tayeb Sanca):** CAS/fórmula molecular/peso molecular verificados por búsqueda web (no inventados) para Tirzepatide, MOTS-c, IGF-1 LR3, Glutatión y NAD+; los dos blends (Wolverine, Glow70) se dejan sin fórmula/CAS propios por ser mezclas de varios péptidos. Precio de cada variante = el mayor de los dos que dio el proveedor (el menor parece ser coste/mayorista). Investigado y confirmado que los 7 son formato vial/liofilizado (no spray nasal) — los tamaños en mg dados coinciden con el estándar de mercado para polvo liofilizado. Imágenes generadas editando la misma maestra de vial (`retatrutide.png`) para mantener el encuadre idéntico al resto del catálogo. Desplegado a producción: `loaddata` del fixture (solo añade filas nuevas, no toca las 11 existentes) + imágenes subidas y asignadas + servicios reiniciados. Verificado con curl: los 7 productos nuevos dan 200, aparecen en su categoría correcta y las imágenes cargan.

**Certificados de análisis (CoA) — 2026-07-12:** nuevo modelo `Certificate` (laboratorio, lote, fecha, pureza, PDF) ligado a `Peptide`, página pública `/certificados/` (enlace en menú/footer), y enlace directo al CoA desde cada ficha de producto. Se revisaron los 11 PDFs entregados por el usuario en `Certificados/` (carpeta local, no versionada): 9 con identidad confirmada y pureza >99% ya están publicados — Retatrutide, Tirzepatide, Tesamorelin, Melanotan II, Selank, Semax, Glow70 Blend, BPC-157, IGF-1 LR3. **Los otros 2 (MOTS-c y NAD+) dieron "Identity: Failed / No Analyte Detected"** en el lote analizado — a petición del usuario se desactivaron ambos productos del catálogo (`is_active=False`) hasta tener un lote con certificado válido. Detalle del laboratorio/proveedor de ese lote fallido: preguntar directamente, no se deja por escrito aquí por ser repo público. Desplegado a producción: PDFs subidos por SCP a `media/certificates/` + migración de datos (`store/migrations/0004_certificados_iniciales.py`) que crea los 9 Certificate y desactiva los 2 productos + collectstatic + reinicio. Verificado con curl: `/certificados/` da 200 con las 9 fichas, `/producto/mots-c/` y `/producto/nad-plus/` dan 404.

**Tests (2026-07-15):** suite de 42 tests en `store/tests.py` y `orders/tests.py` cubriendo los caminos críticos: modelos (slugs, SKU, cheapest variant, punto de pedido), catálogo (filtros, búsqueda, productos inactivos, JSON-LD, certificados), carrito (add/update/remove, entradas inválidas), envío (tarifas ESP/EU y umbrales de gratis), checkout completo (creación de pedido, descuento de stock, emails, consentimientos RGPD), seguimiento de pedido y Mollie (webhook idempotente, pedido pagado, sin API key). Ejecutar con `python manage.py test`. Al escribirlos se detectaron y corrigieron 2 bugs de error 500: añadir al carrito un `variant_id` inexistente, y hacer checkout con una variante borrada del catálogo (además ahora la creación del pedido va en `transaction.atomic` para no dejar pedidos a medias).

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
- [x] Rellenar BANK_IBAN y BANK_HOLDER en .env con datos reales del autónomo — configurado en local y en producción (VPS), servicio reiniciado (2026-07-09)
- [x] Rellenar URLs de Peptaura en automation/peptaura_sync.py — las 5 URLs reales están puestas. El script ya NO calcula ni aplica precios automáticamente: Peptaura mezcla listados "1 vial" y "Box of 10 vials" en la misma página sin forma fiable de distinguirlos por scraping, así que ahora solo informa (precio mínimo + enlace) para revisión manual. Ver docstring de automation/peptaura_sync.py.
- [ ] Darse de alta en Mollie → obtener API key → añadir a .env
- [x] Crear VPS Hetzner CX21 (Ubuntu 22.04, datacenter Alemania) — ya está en producción (europeptiva.com, SSL válido)
- [x] Ejecutar deploy/setup_vps.sh + deploy.sh — VPS desplegado y funcionando

### Diseño visual
- [x] Recoger resultado de Claude Design y aplicar al frontend
- [x] Generar imágenes de producto con Gemini (`tools/generar_imagenes.py`) y asignarlas en la home y en los 5 productos (`media/peptides/*.png`)
- [x] Subir las imágenes generadas al VPS de producción — confirmado en producción (europeptiva.com), las 11 imágenes cargan en catálogo
- [x] Generar imágenes para los 6 productos nuevos (GHK-Cu, Melanotan I, Melanotan II, Tesamorelin, Semax, Selank) — confirmado en producción

### Legal (antes del lanzamiento)
- [ ] Rellenar datos fiscales reales — ya NO se editan las plantillas: se definen `LEGAL_NAME`, `LEGAL_NIF`, `LEGAL_ADDRESS`, `LEGAL_POSTCODE`, `LEGAL_CITY` en el `.env` (local y VPS). El aviso amarillo de "pendiente" en /aviso-legal/ y /privacidad/ desaparece solo cuando están puestos. Modelo 036 presentado el 23/07/2026; falta el alta en RETA
- [ ] Revisar textos legales con abogado/gestor
- [ ] Configurar Google Search Console

### Post-lanzamiento
- [x] Cambiar URL del admin: /admin/ → /gestion-interna/
- [ ] Configurar dominio DNS en Hetzner (europeptiva.com + europeptiva.es) — el `.com` ya resuelve y sirve con SSL; el `.es` no resuelve todavía (comprobado 23/07/2026)
- [ ] Conectar dominos .com y .es al VPS. Ojo al hacerlo: ambos servirían contenido idéntico y el `canonical` de `base.html` se genera con `request.get_host`, así que cada dominio se declararía canónico de sí mismo y Google lo leería como contenido duplicado. Hay que decidir dominio principal y resolverlo con redirect o canonical fijo

## Timeline

| | Objetivo | Estado |
|--------|----------|--------|
| Semana 1 | Modelos + admin | ✅ Completo |
| Semana 2 | Frontend catálogo | ✅ Completo |
| Semana 3 | Checkout + pagos | ✅ Completo |
| Semana 4 | Legal, SEO, infra | ✅ Completo |
| Extras | Automatizaciones + Mollie + deploy | ✅ Completo |
| — | **Lanzamiento** | ⏸️ Aplazado indefinidamente (23/07/2026). Sin fecha objetivo. |

## Trabajo desbloqueado por el aplazamiento

Sin fecha de lanzamiento entran en juego cosas que antes no cabían:

- [ ] **Internacionalización (i18n).** La web es solo español: 0 usos de `{% trans %}`, sin `locale/`, sin `LocaleMiddleware`, `lang="es"` fijo y sin `hreflang`. Se vende a toda la UE, así que el mercado no hispanohablante aterriza en una página que no entiende y acepta el descargo de "solo investigación in vitro" a través de la traducción automática del navegador. Orden sugerido: inglés primero, alemán después. Alcance real: ~15 plantillas + los textos de producto, que están en la BD y necesitan solución aparte (django-modeltranslation o campos por idioma).
- [ ] **Confirmar los tramos de `store/bulk.py`** (15/20/25 %) contra el margen real de Peptaura antes de que la página reciba tráfico.
- [ ] **Decidir el valor real de `purity`.** El modelo y las fixtures traen `>98%` mientras los badges de marketing dicen ≥99%: la ficha de producto se contradice consigo misma.
- [ ] **Revisar la política de distribuidores** de `/al-por-mayor/`: vender para reventa expone a EuroPeptiva si el intermediario lo revende para consumo humano.
- [ ] **Confirmar que el transportista recoge los sábados**, que es lo que promete el mensaje de envío el mismo día (L–S).
