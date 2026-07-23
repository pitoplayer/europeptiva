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

**Contenido del catálogo traducido (2026-07-23):** con `django-modeltranslation`. Se registran en `store/translation.py` los campos de texto de marketing: `Category.name`, `Category.description`, `Peptide.short_description` y `Peptide.description`. **No** se traducen los nombres de producto (Retatrutide, GHK-Cu… son nombres químicos iguales en cualquier idioma) ni `purity`/`cas_number`/`molecular_formula`, que son valores. La migración `0006` crea las columnas por idioma y la `0007` las rellena: `*_es` copiando el campo original y `*_en` con la traducción de las 6 categorías y los 18 productos, indexada por slug para no depender de los PKs. Dos detalles que importan: (1) modeltranslation sustituye el manager de los modelos registrados, así que `filter(name__icontains=…)` y el `ordering` del Meta se reescriben al campo del idioma activo — por eso hay que rellenar `*_es` aunque la web en español ya se viera bien; (2) el admin usa `TranslationAdmin`, que pinta un campo por idioma y reescribe `prepopulated_fields` al idioma por defecto (el slug se sigue generando del nombre español, que es el que va en la URL). El fixture `initial_products.json` lleva ya los campos `*_es`/`*_en`. 5 tests nuevos en `store/tests.py` (`ContenidoTraducidoTest`) cubren ficha ES/EN, categoría traducida, búsqueda en inglés y el fallback al español de un producto sin traducir. **Ojo con la versión:** `django-modeltranslation` 0.20+ exige `django>=5.1` y rompe el deploy contra el `Django==5.0` pinneado (`ResolutionImpossible` en pip); está fijada la **0.19.17**, última serie compatible. Instalar la 0.20 en local sube Django a 6.0.x por la puerta de atrás y los tests dejan de correr sobre la versión de producción. Desplegado a producción y verificado con curl: `/en/catalog/` da las 6 categorías en inglés, las fichas inglesas no filtran ni una palabra en español, la búsqueda inglesa filtra de verdad (`?q=tissue` → 3 productos) y el catálogo español no ha cambiado.

**Ficha de producto reestructurada al estilo PurityBase (2026-07-23):** la ficha tenía un único bloque plano de "Descripción técnica" al final. Ahora, debajo de la caja de compra, van tres secciones: **Contexto de investigación** (campo nuevo `Peptide.research_background`, traducible; **está vacío a propósito** — mientras lo esté, la ficha enseña `description`, que es lo que había antes, así que se puede ir rellenando producto a producto desde el admin sin romper nada), **Reconstitución y manipulación** y **Conservación y estabilidad**. Estas dos últimas **no están en la BD**: son protocolo idéntico para todos los productos del mismo formato, así que viven en `store/product_content.py` y la ficha elige el bloque con el campo nuevo `Peptide.product_format` (`vial` liofilizado / `spray` nasal listo / `solvent` disolvente). Por eso la migración `0009` también **quita el párrafo de conservación del final de cada `description`**: si no, saldría dos veces en la misma página. Añadido además: **upsell de agua bacteriostática** en los liofilizados (`orders/views.py` acepta ya varias `variant_id` en el mismo POST, así que péptido y agua entran al carrito de una vez; no se ofrece si el agua está agotada ni en la ficha del agua misma) y **productos relacionados** al pie (misma categoría primero, completando con el resto hasta cuatro). La tarjeta de producto se sacó a `templates/partials/product_card.html`, que ahora comparten catálogo y relacionados. De paso: `PeptideVariant.size_display` — el campo se llama `size_mg` pero el agua se vende en ml, y el catálogo y el selector la anunciaban como "3mg". El SKU se sigue generando con `mg` para no romper los que ya existen. 9 tests nuevos.

**Contexto de investigación de los 18 productos (2026-07-23):** escritos en español e inglés en la migración `0010` (indexada por slug, como las demás). Reglas que sigue el texto, por si hay que ampliarlo o revisarlo: qué es la molécula y qué se ha estudiado de ella, sin eficacia, dosis ni uso humano; y **se dice siempre de dónde viene la evidencia**. Donde es solo preclínica (BPC-157, TB-500, MOTS-c) el texto lo afirma explícitamente; donde la literatura procede casi toda de un país (Semax y Selank, desarrollo ruso) también; y los dos blends dicen que lo publicado va de cada componente por separado, no de la mezcla. Esa distinción entre "estudiado en roedores" y "con ensayos clínicos amplios" es lo que impide que la ficha se lea como una promesa, y conviene mantenerla si se editan los textos. Falta que el usuario los revise.

**Packs de productos (2026-07-23):** cuatro paquetes con página propia en `/packs/` y `/pack/<slug>/` (`/en/bundles/`, `/en/bundle/<slug>/` — en inglés es "bundle", que es el término del sector), en el sitemap, en el menú y con los tres destacados en portada. Modelos `Bundle` + `BundleItem` en `store/models.py`, traducibles (el nombre **sí** se traduce, al revés que el de los productos: "Pack Recuperación" es marketing, no un nombre químico).

Decisiones que conviene no deshacer sin pensarlo:

- **Precio fijo escrito a mano, no porcentaje.** Permite redondear a 129,95 y ajustar el margen paquete a paquete.
- **Los descuentos se quedan por debajo del 15 %** (salen al 12-14 %), que es el primer tramo de `store/bulk.py`. Un pack de tres viales que descontara más que un pedido mayorista de diez unidades dejaría los tramos de mayoristas sin sentido. Si se tocan los tramos, revisar esto.
- **En el pedido un pack se guarda desglosado**, una línea por componente con el precio repartido (`store/pricing.py`), no como una línea suelta. Así el stock se descuenta y se **restaura** con el código que ya existía —`cancelar_pedidos_sin_pago` funciona sin tocarlo— y el albarán dice qué viales van en la caja. El reparto se hace por unidad y el último trozo absorbe el redondeo, de modo que la suma de líneas es exactamente el precio del pack; hay test que lo comprueba con precios que no dividen limpio.
- **El stock de un pack lo marca su componente más escaso**, y si alguno se desactiva el pack se agota entero.
- **Cada ficha explica que un pack no es un blend.** No es adorno: el Pack Recuperación (119,95 €) cuesta más que el Wolverine Blend (110 €), que lleva lo mismo mezclado en un vial, y sin esa explicación parece un timo. Por eso el Pack Piel, que solapa con Glow70, no va en portada.

Margen: con los costes de proveedor del `.xlsx` (columna "Precio supplier", 79-90 % de margen en casi todo el catálogo salvo Tesamorelina al 58,7 %) los cuatro packs se quedan por encima del 85 %.

Un pack de longevidad hoy es imposible: MOTS-c y NAD+ siguen desactivados por el CoA fallido y en esa categoría solo queda Glutatión. Un "kit de inicio" completo al estilo de la competencia tampoco, porque no se venden jeringas ni toallitas.

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

- [x] **Internacionalización (i18n) — inglés completo.** Plantillas (436 literales en `locale/en/`), URLs traducidas (`/catalogo/` ↔ `/en/catalog/`), `hreflang`, selector de idioma en el header **y el contenido del catálogo, que está en la BD** (ver más abajo). Pendiente: alemán.
- [ ] **Confirmar los tramos de `store/bulk.py`** (15/20/25 %) contra el margen real de Peptaura antes de que la página reciba tráfico.
- [ ] **Decidir el valor real de `purity`.** El modelo y las fixtures traen `>98%` mientras los badges de marketing dicen ≥99%: la ficha de producto se contradice consigo misma.
- [ ] **Revisar la política de distribuidores** de `/al-por-mayor/`: vender para reventa expone a EuroPeptiva si el intermediario lo revende para consumo humano.
- [ ] **Confirmar que el transportista recoge los sábados**, que es lo que promete el mensaje de envío el mismo día (L–S).
