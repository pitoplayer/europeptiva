# Logística EuroPeptiva — Modelo de fulfillment

## Resumen ejecutivo

El plan original (stock propio para 5 productos + "dropshipping con nuestra etiqueta" para el resto)
es viable, pero **el dropship transaccional puro (pedido a pedido, directo desde el vendedor de
Peptaura al cliente final) tiene un problema de fondo que hay que resolver antes de construirlo**:

> Peptaura es un **marketplace multivendedor**, no un proveedor único. La mayoría de sus vendedores
> (Welon/Lumira, Pepturion, RETA LUXE, etc.) son **fabricantes chinos sin almacén en la UE**. Un envío
> pedido-a-pedido desde China a un cliente final en España cruza aduana española/UE **en cada paquete
> individual**: retrasos habituales de 1 a 4 semanas, riesgo real de retención/inspección (los péptidos
> de investigación generan más escrutinio aduanero que un producto genérico), y la documentación
> aduanera de cada paquete (factura comercial, remite) revela al fabricante real — lo que **contradice
> la idea de "nuestra etiqueta"**, salvo que el vendedor ofrezca específicamente "blind dropshipping".

Esto no significa descartar el modelo — significa que **"dropship" aquí no puede ser en tiempo real
pedido-a-pedido desde China**, sino en lotes. Ver la sección "Decisión pendiente" al final: hay dos
caminos razonables y la elección depende de cuánto capital queréis inmovilizar en stock.

---

## Nivel 1 — Stock propio (los 5 productos estrella)

Ya decidido y ya reflejado en el catálogo y en `automation/peptaura_sync.py`:

- **Retatrutide, Semaglutide, BPC-157, TB-500, BAC Water**

Criterio: son los productos con más demanda esperada (pérdida de grasa + recuperación, las dos
categorías con más tracción en el nicho) y los que más se benefician de entrega rápida (24-72h) porque
suelen comprarse con intención de empezar un protocolo ya.

**Cómo funciona:**
1. Compra periódica en lote a Peptaura (a un vendedor concreto, no "al marketplace" en abstracto —
   elegir uno fijo por producto y mantener la relación, para no depender de qué vendedor esté más
   barato cada semana).
2. Una única importación por lote → una única gestión aduanera/IVA de importación, mucho más simple
   y barata que muchas importaciones pequeñas.
3. Stock físico en casa (o un pequeño almacén/trastero climatizado si el volumen crece).
4. Envío nacional/UE desde España: Correos o GLS, 24-72h, ya integrado en `orders/shipping.py`.
5. Reposición: definir un **punto de pedido** (ej. cuando quedan menos de N viales, se lanza el
   siguiente lote) — esto se puede automatizar con un informe desde el admin de Django o ampliando
   `informe_diario` para avisar de stock bajo.

**Almacenamiento** (importante, no es solo logística de envío):
- Los péptidos liofilizados (polvo) son estables a temperatura ambiente durante el transporte y el
  almacenamiento corto/medio plazo — no necesitan cadena de frío para el envío nacional en 24-72h.
- Sí conviene guardarlos en nevera (2-8°C) una vez en casa para maximizar estabilidad si el stock dura
  semanas, y siempre protegidos de luz directa.
- BAC Water (agua bacteriostática) no necesita refrigeración, solo lugar fresco.
- Esto es guía general de estabilidad de péptidos — al recibir cada lote, seguir la ficha técnica/COA
  que entregue el fabricante, que puede tener indicaciones específicas por producto.

---

## Nivel 2 — Los otros 6 productos (Tesamorelin, GHK-Cu, Melanotan I, Melanotan II, Semax, Selank)

Aquí es donde hay que decidir el modelo. Dos opciones reales:

### Opción A — Lotes periódicos con marca blanca + stock mínimo propio (recomendada por coste)

En vez de dropship en tiempo real, se negocia con el vendedor de Peptaura (o un proveedor de private
label dedicado — existen varios especializados en esto: Wholesale-Peptides.com, PeptideDropship,
YourPeptideBrand, Evolve Peptides, SmartMD Labs) que:
- Fabrique/reetiquete el producto **con la etiqueta de EuroPeptiva ya puesta en fábrica**.
- Envíe el lote completo a la dirección de EuroPeptiva de una sola vez (una sola aduana, un solo IVA
  de importación, no 6 productos × N pedidos individuales).

EuroPeptiva mantiene un **stock mínimo de seguridad** (pocas unidades, no como los 5 estrella) de estos
6 productos, reponiendo por lotes cada 3-4 semanas. Técnicamente deja de ser "dropship" y pasa a ser
stock propio también, pero con nivel bajo y rotación más lenta — el cliente sigue recibiendo en 24-72h
como los productos estrella.

- **Ventajas:** entrega rápida y fiable para el cliente, una gestión aduanera predecible y barata, control
  total de calidad antes de vender.
- **Desventajas:** requiere capital inmovilizado (aunque bajo) en estos 6 productos también, y gestión
  activa de cuándo reponer.

### Opción B — Dropship real con proveedor con almacén en la UE

Existen proveedores de péptidos de investigación con **almacén físico en la UE** (Alemania, Países
Bajos, países bálticos) que sí pueden hacer dropship pedido-a-pedido con marca blanca sin problemas de
aduana, porque el envío es intracomunitario (2-5 días, sin controles aduaneros al ser movimiento dentro
del mercado único). Esto cumple mejor la idea original ("que el proveedor mande directo con nuestra
etiqueta, sin que nosotros toquemos stock").

- **Ventajas:** cero inventario, cero capital inmovilizado, cero gestión de reposición.
- **Desventajas:** normalmente precio por unidad más alto que comprar directo a fabricante chino vía
  Peptaura; hay que evaluar/negociar con un proveedor nuevo (fuera de Peptaura) que ofrezca
  específicamente private label + fulfillment con almacén UE; menos control de calidad porque nunca
  tocáis el producto físicamente antes de que llegue al cliente.

### Decisión pendiente

La elección entre A y B depende de: cuánto margen tenéis por unidad en estos 6 productos (si es alto,
absorbe bien el precio mayor de la opción B), y cuánto capital queréis destinar a stock además de los 5
principales. Con el presupuesto inicial de 500€, probablemente la Opción A (lotes + stock mínimo) es
más realista para empezar, migrando a B más adelante si un producto concreto tiene rotación demasiado
baja para justificar tener stock.

**Siguiente paso concreto:** decidir modelo y, en consecuencia, o bien (A) contactar al vendedor actual
de Peptaura para negociar reetiquetado en fábrica + envío en lote, o bien (B) contactar 2-3 proveedores
UE con private label (ej. Baltic BioLabs, PulsePeptides, eupeptideshop.org) y pedir condiciones de
dropship/fulfillment y precios mayoristas.

---

## Flujo operativo de un pedido (una vez decidido el modelo)

1. Cliente hace el pedido en la web → puede mezclar productos de Nivel 1 y Nivel 2 en el mismo carrito.
2. Si el pedido solo tiene productos con stock propio (Nivel 1 o Nivel 2 con stock mínimo disponible):
   se prepara y envía como hasta ahora, un solo paquete, 24-72h.
3. Si un producto de Nivel 2 está agotado en el momento del pedido (stock mínimo a cero, a la espera
   del siguiente lote): el pedido pasa a estado "en preparación" con plazo estimado más largo — hay que
   comunicarlo claramente en la ficha de producto y en el email de confirmación (ej. "Disponibilidad
   5-10 días laborables" en vez de "Envío en 24-72h").
4. Pedidos mixtos (un producto con stock ya listo + otro agotado): decidir si se envían juntos cuando
   llegue el que falta, o se hacen dos envíos (mejor experiencia pero coste de envío duplicado) — se
   puede dejar como opción configurable en el checkout más adelante.

## Cambios técnicos necesarios (cuando se decida el modelo)

- Añadir a `PeptideVariant` un campo tipo `fulfillment_type` (`stock_alto` / `stock_minimo` /
  `bajo_pedido`) para diferenciar mensajes de plazo de entrega en la ficha de producto.
- Ampliar `informe_diario` (o crear un nuevo comando) para avisar cuando el stock de un producto de
  Nivel 2 baja del punto de pedido, y así lanzar el siguiente lote a tiempo.
- Mensaje dinámico de plazo de envío en `product_detail.html` según `fulfillment_type`.
- Si se opta por pedidos mixtos con envíos separados: lógica en `orders/views.py` para dividir el
  `Order` en sub-envíos con su propio tracking.

No voy a implementar esto todavía — son cambios que dependen de qué modelo (A o B) elijáis para el
Nivel 2, así que antes de tocar código conviene cerrar esa decisión.

## Aspectos legales/fiscales a tener en cuenta

- **Factura del proveedor a EuroPeptiva**, y **factura de EuroPeptiva al cliente** — cadena normal de
  reventa B2B→B2C, sin complicaciones de IOSS si la importación se hace en lote a nombre de EuroPeptiva
  (el IOSS solo aplica cuando el destinatario final del envío internacional es el consumidor directo).
- Si en el futuro se explora la Opción B con un proveedor fuera de la UE que envíe directo al cliente,
  ahí sí entraría en juego el régimen IOSS (envíos ≤150€) y quién es el importador de registro —
  pero con proveedor UE (intracomunitario) esto no aplica.
- Revisar con el gestor/asesor fiscal ya contactado para el alta de autónomo cómo se registran estas
  compras en lote a efectos de IVA soportado e IVA repercutido.
