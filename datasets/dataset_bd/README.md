# Dataset de FinaGotchi

Dataset sintetico y reproducible para probar la app, el simulador y la
API de FinaGotchi. Se genera dentro de `finagotchi.db` y se exporta a CSV.

- Generado: 2026-11-04T17:18:14
- Semilla: `20261104`
- Fecha de referencia: 2026-11-04
- Rango de movimientos: 2026-07-08 a 2026-11-04

## Contenido

| Recurso | Cantidad |
| --- | ---: |
| Usuarios | 25 |
| Usuarios con dispositivo | 18 |
| Usuarios solo app | 7 |
| Dispositivos | 18 |
| Transacciones | 500 |
| Transacciones confirmadas | 481 |
| Transacciones pendientes | 19 |
| Transacciones en papelera | 22 |
| Mensajes de dispositivo/app | 343 |
| Interacciones de IA | 575 |
| Metas | 81 |
| Metas cumplidas | 15 |
| Puntos otorgados | 1151 |
| Cierres de dia | 151 |
| Alertas | 173 |
| Vistas disponibles | 15 |

Cada usuario tiene como maximo un dispositivo y siempre hay menos
dispositivos que usuarios. Los usuarios sin dispositivo representan
cuentas que solo usan la app (por ejemplo, iPhone o navegador).

## Cuentas demo

| Correo | Contrasena | Rol |
| --- | --- | --- |
| `simulador@finagotchi.local` | `simulador123` | Cuenta del simulador de PC |
| `demo01@finagotchi.local` ... `demo24@finagotchi.local` | `Demo1234` | Usuarios demo |

Las 25 cuentas usan `America/Bogota`, moneda COP y correo ya verificado.

## Casos limite incluidos

- 2 solicitudes de eliminacion de cuenta pendientes (estado
  `pendiente_eliminacion`).
- 1 solicitud de eliminacion cancelada.
- Transacciones pendientes de confirmacion y transacciones en papelera.
- Movimientos agrupados en un mismo mensaje de voz.
- Ediciones de movimientos con historial en `transacciones_versiones`.
- Metas activas y completadas, con eventos y puntos.
- Alertas leidas/no leidas y eliminadas logicamente.
- Dispositivos con bateria baja, sin conexion y comandos en distintos estados.
- Tokens de recuperacion usados/vencidos y sesiones revocadas.

## Archivos

`manifest.json` contiene el conteo, tamano y SHA-256 de cada CSV.
`csv/` tiene un archivo por tabla, con encabezados y UTF-8 sin BOM.

Los valores `NULL` se exportan como campo vacio. Las columnas generadas
(`ingreso_total_mensual`, `delta_salud`, `delta`) son de solo lectura.

## Exportacion consolidada

`consolidado/dataset_completo.csv` reune todas las tablas en formato largo:
`tabla;id_registro;usuario_id;fecha;columna_fecha;campo;valor`. Usa UTF-8
con BOM y separador `;` para abrirlo en Excel, incluye las celdas vacias y
tiene su propio `consolidado/manifest_consolidado.json` con SHA-256.

```powershell
py -3 tools/exportar_csv_consolidado.py
py -3 tools/exportar_csv_consolidado.py --separador "," --sin-bom --omitir-vacios
```

## Regenerar

```powershell
py -3 tools/generar_dataset_bd.py
py -3 tools/generar_dataset_bd.py --semilla 1234 --transacciones 200
py -3 tools/generar_dataset_bd.py --db C:\ruta\copia.db --no-exportar
```

El generador respalda la base en `backups/` antes de borrar los datos
existentes. Conserva `plantilla_*` y `schema_migrations`.
