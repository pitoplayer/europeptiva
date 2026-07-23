"""Reparto del precio de un paquete entre sus componentes.

Un paquete se guarda en el pedido como una línea por componente, no como una
línea suelta: así el stock se descuenta y se devuelve con el mismo código que
ya existía para los productos normales, y el albarán dice exactamente qué viales
van en la caja.

Eso obliga a repartir el precio cerrado del paquete entre los componentes, y el
reparto tiene que sumar exactamente el precio del paquete. Ni un céntimo de más:
el subtotal del pedido sale de las líneas.
"""

from decimal import Decimal, ROUND_HALF_UP

CENTIMO = Decimal('0.01')


def prorratear(total, pesos):
    """Reparte `total` en proporción a `pesos`, sumando exactamente `total`.

    El último trozo absorbe el resto del redondeo, que es como se reparte
    cualquier importe que no divide limpio.
    """
    suma_pesos = sum(pesos)
    if suma_pesos <= 0:
        return [Decimal('0')] * len(pesos)

    trozos = []
    repartido = Decimal('0')
    for peso in pesos[:-1]:
        trozo = (total * peso / suma_pesos).quantize(CENTIMO, rounding=ROUND_HALF_UP)
        trozos.append(trozo)
        repartido += trozo
    trozos.append(total - repartido)
    return trozos


def desglosar_paquete(bundle, quantity=1):
    """Convierte un paquete en las líneas de pedido que lo representan.

    Devuelve tuplas (variante, unidades, precio_unitario). El reparto se hace
    por unidad y no por componente: si un componente lleva dos viales y el
    precio no divide limpio entre ellos, salen dos líneas de esa variante que
    se diferencian en un céntimo, en lugar de un total que no cuadra.
    """
    items = list(bundle.items.select_related('variant').all())
    if not items:
        return []

    # Una entrada por vial físico, para poder repartir unidad a unidad.
    unidades = [item.variant for item in items for _ in range(item.quantity * quantity)]
    pesos = [variante.price for variante in unidades]
    trozos = prorratear(bundle.price * quantity, pesos)

    # Se reagrupan las unidades que hayan quedado al mismo precio.
    agrupado = {}
    for variante, precio in zip(unidades, trozos):
        clave = (variante.id, precio)
        if clave not in agrupado:
            agrupado[clave] = [variante, 0, precio]
        agrupado[clave][1] += 1

    return [(v, n, precio) for v, n, precio in agrupado.values()]
