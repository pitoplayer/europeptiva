# Automatizaciones de EuroPeptiva

## Resumen

| Automatización | Frecuencia | Comando | Qué hace |
|----------------|-----------|---------|----------|
| Recordatorio de pago | Diario 10:00 | `recordatorio_pago` | Email a clientes con pedido pendiente 24-47h |
| Cancelación automática | 09:00 y 21:00 | `cancelar_pedidos_sin_pago` | Cancela pedidos +48h sin pago y restaura stock |
| Informe diario | Diario 08:00 | `informe_diario` | Email al admin: pedidos, ingresos, stock bajo |
| Sync precios Peptaura | Lunes 06:00 | `peptaura_sync.py` | Actualiza precios con margen 40% sobre Peptaura |
| Limpieza sesiones | Domingo 03:00 | `clearsessions` | Limpia sesiones expiradas de Django |

## Configuración en el VPS

### 1. Crear directorio de logs

```bash
sudo mkdir -p /var/log/europeptiva
sudo chown peptidos:peptidos /var/log/europeptiva
```

### 2. Instalar crontab

```bash
crontab -e
# Pegar el contenido de automation/crontab_vps.txt
```

### 3. Verificar que funciona

```bash
# Probar manualmente (modo dry-run)
python manage.py recordatorio_pago --dry-run
python manage.py cancelar_pedidos_sin_pago --dry-run

# Ver logs en tiempo real
tail -f /var/log/europeptiva/recordatorios.log
```

## Flujo de un pedido por transferencia

```
Cliente hace pedido
    ↓
Email de confirmación con datos bancarios (inmediato)
    ↓
24h después → recordatorio_pago → Email de recordatorio
    ↓
48h después → cancelar_pedidos_sin_pago → Cancelado + stock restaurado + email al cliente
    ↓
Admin ve en informe_diario cuántos pedidos siguen pendientes
```

## Sincronización con Peptaura

El script `peptaura_sync.py` aplica un **margen del 40%** sobre el precio de Peptaura.

### Configuración

1. Visitar Peptaura y buscar las URLs de cada producto
2. Rellenar `PEPTAURA_PRODUCTS` en `automation/peptaura_sync.py`
3. Probar manualmente: `python manage.py shell < automation/peptaura_sync.py`

### Estrategia de precios (ajustable)

| Coste Peptaura | Margen | Nuestro precio |
|----------------|--------|----------------|
| 20€ | 40% | 28€ |
| 50€ | 40% | 70€ |
| 100€ | 40% | 140€ |

Si Peptaura ofrece API o feed CSV, contactarles directamente — sería más fiable que scraping.

## Futuras automatizaciones (ideas)

- **Restock automático**: cuando el stock baja de X unidades, enviar email de pedido a Peptaura
- **Email de seguimiento de envío**: cuando el admin marca el pedido como "Enviado", enviar número de seguimiento al cliente
- **Review request**: 7 días después de "Entregado", pedir valoración al cliente
- **Precio dinámico**: ajustar margen según demanda (más stock → menor margen para rotar)
