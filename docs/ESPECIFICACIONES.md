# FinaGotchi · Especificaciones funcionales y técnicas

Versión del documento: 2.0  
Estado: vigente para implementación  
Base de datos: SQLite 3.31+ · portable a PostgreSQL 12+  
Moneda: peso colombiano (COP), enteros sin decimales  
Zona horaria por defecto: `America/Bogota`  
Documentos relacionados: `database/sql/001_schema.sql`, `database/sql/002_views.sql`, `database/sql/003_seed.sql`

---

## 1. Objetivo y alcance

FinaGotchi es una mascota virtual llamada Nancy que ayuda a una persona a registrar sus ingresos, gastos y ahorros por voz, entender su presupuesto y construir hábitos financieros durante un diagnóstico de 28 días.

El sistema es multiusuario. Cada usuario tiene su propia mascota, sus cuentas, categorías, metas, presupuesto, historial, dispositivo y notificaciones.

La aplicación se compone de:

1. Backend HTTP en Python/Flask.
2. Base de datos SQLite.
3. Agente IA con transcripción de audio, interpretación y clasificación por proveedor intercambiable.
4. Dispositivo físico ESP32-S3 y simulador de PC.
5. Aplicación frontend.
6. Panel de notificaciones y bienestar.

Esta versión prioriza:

- Registro rápido por voz con confirmación humana.
- Separación estricta entre dinero real, ahorro y presupuesto.
- Salud de Nancy explicable y auditable.
- Recuperación ante ediciones de días ya cerrados.
- Aislamiento de datos entre usuarios.
- Operación del dispositivo con red intermitente.

### Fuera de alcance de esta versión

- Conexión bancaria automática.
- Transferencias o pagos reales.
- Asesoría financiera regulada.
- Autenticación biométrica.
- Aplicación móvil nativa.
- Sincronización multi-dispositivo en tiempo real.
- Las pantallas V12 a V16 no están en el Figma entregado; se documentan como trabajo futuro.

---

## 2. Actores

| Actor | Responsabilidad |
|---|---|
| Usuario | Registra movimientos, define presupuesto, metas y confirma lo que Nancy entendió. |
| Nancy | Representa el estado emocional derivado de la salud financiera del usuario. No es una fuente de verdad. |
| Dispositivo | Captura voz, envía audio, muestra estados y notificaciones, almacena mensajes offline y ejecuta comandos. |
| Backend | Valida, calcula, persiste, notifica y expone la información. |
| Agente IA | Transcribe audio, detecta la categoría e interpreta una o varias transacciones. |
| Administrador técnico | Ejecuta migraciones, respaldos y tareas de mantenimiento. No existe panel administrativo en esta versión. |

---

## 3. Glosario

| Término | Definición |
|---|---|
| Transacción | Gasto, ingreso o ahorro confirmado. |
| Movimiento | Término visual para una transacción. |
| Ahorro | Dinero separado del disponible, asociado o no a una meta. |
| Balance neto | Ingresos menos gastos de un periodo. El ahorro se muestra aparte. |
| Cupo diario | Presupuesto máximo de gasto para un día. |
| Saldo acumulado | Ingresos históricos menos gastos históricos. |
| Cierre | Foto inmutable de un día financiero. |
| Salud | Valor 0-100 que representa el bienestar financiero de Nancy. |
| Ánimo | Etiqueta visual derivada de la salud. |
| Punto | Unidad de progreso por transacción confirmada. |
| Racha | Días consecutivos con al menos una transacción confirmada. |
| Bienestar | Índice 0-100 calculado con la encuesta del perfil. No es la salud de Nancy. |
| Mensaje | Texto transcrito de una captura de voz o de un registro manual agrupado. Puede generar varias transacciones. |
| Pendiente | Transacción propuesta que aún no afecta balances, salud, puntos ni metas. |
| Anulada | Transacción en papelera. No afecta cálculos; se puede restaurar. |
| Dispositivo vinculado | Dispositivo asociado a un único usuario mediante QR o PIN. |

---

## 4. Reglas transversales

### 4.1 Dinero

- Todos los montos se almacenan como `INTEGER` en COP.
- No se usa `FLOAT` ni `REAL` para dinero.
- El backend convierte expresiones como `10.000`, `10,000`, `10k`, `10 mil` y `diez mil` a `10000`.
- Un monto debe ser mayor que cero.
- Si el agente no identifica un monto, no se inventa un valor por defecto. El mensaje queda pendiente de aclaración.
- Los valores mostrados usan separador de miles colombiano: `$42.000`.

### 4.2 Estados de una transacción

| Estado | Afecta balances | Afecta puntos | Afecta salud | Afecta metas | Visible |
|---|---:|---:|---:|---:|---:|
| `pendiente` | No | No | No | No | Sí, con badge Pendiente |
| `confirmado` | Sí | Sí | Sí, al cierre | Sí | Sí |
| Anulada (`is_deleted=1`) | No | No | No | No | Solo en papelera |
| Restaurada | Sí | Sí | Se recalcula | Sí | Sí |

Una transacción anulada conserva su vínculo con el mensaje para que un reintento del dispositivo no la duplique.

### 4.3 Mensajes y múltiples transacciones

- Un mensaje se identifica con `mensaje_id` y es único por usuario.
- Un mensaje puede producir cero, una o varias transacciones.
- La idempotencia se aplica al mensaje, no a cada transacción.
- Si el dispositivo reenvía el mismo `message_id`, el backend devuelve el resultado ya procesado y no crea registros nuevos.
- La tabla `mensajes_dispositivo` conserva el texto original, la confianza, el estado y el error de procesamiento.
- Las transacciones pendientes pueden agruparse y confirmarse en lote.

### 4.4 Confirmación

- Toda captura por voz se muestra al usuario antes de afectar el dinero.
- La confirmación puede ser total o por transacción.
- El usuario puede editar tipo, monto, categoría, cuenta, meta y concepto.
- Después de guardar, existe una ventana de 10 segundos para deshacer.
- El registro manual usa la misma validación que el registro por voz.
- La confirmación del dispositivo solo se muestra cuando el backend confirma la persistencia.
- Al confirmar un mensaje originado en un dispositivo, se crea una notificación `movimiento_registrado` en `dispositivos_notificaciones`.
- El dispositivo consulta sus notificaciones por polling HTTP y confirma recepción con un acuse.

### 4.5 Fechas

- `fecha_hora` se guarda en UTC con formato ISO-8601 terminado en `Z`.
- `fecha_local` se guarda como `YYYY-MM-DD` en la zona horaria del usuario.
- La zona horaria inicial es `America/Bogota` (UTC-05:00, sin horario de verano).
- El día financiero cambia a las 00:00 locales.
- Si el usuario registra un movimiento de un día anterior, se debe indicar explícitamente; por defecto se usa el día local actual.

### 4.6 Aislamiento por usuario

- Todas las tablas de datos incluyen `usuario_id`.
- Las referencias entre entidades usan claves foráneas compuestas `(usuario_id, entidad_id)`.
- Un usuario no puede asociar una transacción a una cuenta, categoría o meta de otro usuario.
- Toda consulta de aplicación filtra por `usuario_id`.
- Las vistas no aíslan por sí solas; el backend siempre agrega el filtro.
- `usuario_id` es inmutable en transacciones, cuentas, categorías y metas.

### 4.7 Papelera

- Eliminar un movimiento es una eliminación lógica.
- El movimiento conserva `deleted_at` y `eliminado_via`.
- Se puede restaurar durante 30 días.
- La purga definitiva se ejecuta por tarea programada después del periodo de retención.
- Las vistas de balance, puntos, metas y salud excluyen movimientos eliminados.

---

## 5. Flujos funcionales

### 5.1 Inicio y presentación

Pantallas: V01.1, V01.2.1, V01.2.2, V01.2.3.

1. El usuario abre la aplicación y ve a Nancy.
2. Se presenta el proyecto en tres pasos.
3. El usuario puede crear cuenta o iniciar sesión.

No se solicita información financiera antes del consentimiento.

### 5.2 Creación de cuenta

Pantallas: V02.1, V02.1 Restricciones, V02.3.

Campos:

- Nombre o apodo con el que Nancy llamará al usuario.
- Nombre completo opcional.
- Correo.
- Contraseña.
- Aceptación de términos y política de datos.
- Consentimiento opcional para datos anónimos de estudio.

Reglas:

- El correo es único sin distinguir mayúsculas.
- La contraseña se almacena con hash seguro; nunca en texto plano.
- El correo debe verificarse antes de operaciones sensibles.
- El usuario puede autenticarse con correo, Google o Apple.
- Los consentimientos se guardan con versión y fecha.
- La cuenta inicia con presupuesto diario de `$30.000`, editable.
- Al crear el usuario se ejecuta el seed de perfil, preferencias, progreso, mascota, secciones, categorías, cuentas y palabras.

### 5.3 Inicio de sesión

Pantallas: V02.2, V02.2 Clave olvidada, V02.2 Restricciones.

- Correo y contraseña, o proveedor externo.
- Mensajes de error genéricos para no revelar si un correo existe.
- Recuperación por enlace con token de un solo uso y expiración.
- Límite de intentos por cuenta e IP.
- Sesión con token de acceso corto y token de refresco revocable.

### 5.4 Consentimiento

Pantallas: V02.3.

- Se registra `terminos`, `privacidad` y, si aplica, `datos_estudio_anonimo`.
- Cada aceptación guarda versión, fecha y valor.
- El usuario puede retirar el consentimiento de estudio sin perder la cuenta.

### 5.5 Vinculación del dispositivo

Pantallas: V03.1, V03.4 éxito, V03.4 error, V03.4 conexión perdida.

1. El dispositivo genera un QR o PIN temporal.
2. El código expira en 10 minutos.
3. La aplicación autenticada envía el código.
4. El backend valida, vincula el dispositivo y entrega un token de dispositivo una sola vez.
5. El dispositivo guarda el token y se conecta por BLE o Wi-Fi.
6. Si el código es inválido o vencido, se muestra error y se permite reintentar.
7. Máximo 5 intentos por código.
8. Un dispositivo pertenece a un solo usuario.
9. Al desvincular o eliminar la cuenta, el dispositivo vuelve a estado de fábrica y su token se revoca.

### 5.6 Ruta de tres etapas

Pantallas: V04.1, V04.2.1, V04.2.2, V04.2.3.

| Etapa | Nombre | Duración | Resultado |
|---|---|---|---|
| 1 | Diagnóstico | 28 días | Perfil financiero y meta de registros |
| 2 | Plan y presupuesto | 2-3 meses | Presupuesto aprobado por categoría |
| 3 | Seguimiento | Permanente | Cuidado diario y ajustes |

Reglas:

- La duración oficial del diagnóstico es de 28 días.
- Los textos que digan “30 días” deben corregirse a 28.
- La etapa 1 inicia al crear la cuenta o al terminar el test inicial.
- La etapa 2 inicia al aprobar un presupuesto.
- La etapa 3 no está completamente diseñada en el Figma; se implementa después del MVP.

### 5.7 Test inicial

Pantallas: V05.1, V05.3, V05.4, V05.5, V05.5.1, V05.6.

Secciones:

1. Sobre ti.
2. Tus ingresos.
3. Tus gastos y hábitos.
4. Cómo llevas tus cuentas.
5. Deudas y ahorro.
6. Bienestar financiero.

Reglas:

- Todos los campos son opcionales.
- Cada sección tiene estado `pendiente`, `en_progreso` o `completo`.
- El usuario puede omitir una sección y completarla después.
- Al final se calcula una meta de registros semanales.
- El resultado sugiere un presupuesto diario inicial.
- La meta de registros se guarda en `progreso_etapa.meta_registros`.
- La sección completada actualiza `perfil_secciones` y `perfil_financiero`.

### 5.8 Inicio del día

Pantalla: V06.1.

Debe mostrar:

- Nombre de Nancy.
- Salud y ánimo.
- Etapa actual y día del diagnóstico.
- Progreso de puntos.
- Presupuesto diario.
- Disponible hoy.
- Porcentaje gastado.
- Categorías con cupo restante.
- Botón “Mantén para hablar”.
- Botón “Escribir”.
- Botón “Finaliza tu día”.

Reglas:

- `disponible_hoy = presupuesto_diario_del_dia - gastos_confirmados_del_dia`.
- El presupuesto no gastado no se acumula automáticamente al día siguiente.
- El saldo neto sí se acumula históricamente.
- El ahorro se muestra separado y no reduce el cupo diario.
- Si el día anterior quedó abierto, el backend lo cierra de forma perezosa antes de mostrar el día actual.
- La salud mostrada durante el día es una proyección; solo se persiste al cerrar.

### 5.9 Registro por voz

Pantallas: V07.1, V07.2.

1. El usuario mantiene presionado para hablar.
2. El dispositivo o la app captura audio y lo envía al backend.
3. La IA del backend transcribe el audio.
4. La IA detecta la categoría y propone una o varias transacciones.
5. La app o el dispositivo muestra “¿Lo entendí bien?”.
6. El usuario confirma, edita o descarta.
7. Al guardar, se crea el movimiento, se actualiza el cupo y se encola una notificación para el dispositivo.
8. El dispositivo recibe “Registro guardado” cuando el backend confirma la persistencia.
9. Durante 10 segundos puede deshacer.
10. El dispositivo muestra la animación de confirmación.

Reglas:

- El dispositivo no transcribe audio localmente; solo captura y envía.
- La IA del backend hace transcripción y clasificación de categoría.
- La confirmación humana es obligatoria: la IA propone y el usuario confirma antes de afectar el dinero.
- Si no hay monto, no se asume `$10.000`.
- Si hay varias transacciones, se muestran agrupadas.
- La categoría sugerida muestra el impacto en Nancy.
- El guardado de una transacción confirmada otorga 1 punto.
- El guardado de varias transacciones otorga 1 punto por cada una.

### 5.10 Registro manual

Pantallas: V07.3 gasto, V07.3 ingreso, V07.3 ahorro, V07.3 respaldo.

Pestañas:

- Gasto.
- Ingreso.
- Ahorro.

Campos:

- Monto.
- Categoría, excepto en ahorro.
- Cuenta.
- Meta, solo en ahorro.
- Concepto opcional.
- Fecha y hora.

Reglas:

- En ahorro, la meta es opcional.
- En gasto e ingreso, la categoría es obligatoria.
- En gasto e ingreso, la meta debe estar vacía.
- La cuenta es obligatoria.
- Si el usuario no elige cuenta, se usa la cuenta por defecto.
- El tipo de la categoría debe coincidir con el tipo del movimiento.

### 5.11 Movimientos

Pantallas: V08.1, V08.1 cargando, V08.1 filtros, V08.1 detalle, V08.1 editada, V08.1 anulada.

Debe mostrar:

- Ingresos, gastos y saldo del periodo.
- Lista de movimientos.
- Filtros por periodo, tipo, categoría, cuenta, monto y estado.
- Badge Pendiente, Editada o Anulada.
- Detalle con fecha, hora, monto, categoría, cuenta y concepto.
- Acciones editar, anular y restaurar.

Reglas:

- Editar una transacción crea una versión anterior en `transacciones_versiones`.
- La versión aumenta y la transacción se marca como editada.
- Anular no borra físicamente.
- Restaurar devuelve la transacción a los cálculos.
- El filtro por defecto excluye la papelera.
- El filtro “Anulados” consulta `v_papelera`.

### 5.12 Cierre del día

Pantallas: V06.1 “Finaliza tu día”, V11.1.

1. El usuario solicita cerrar el día.
2. El backend verifica que no haya transacciones pendientes sin resolver.
3. Calcula totales confirmados.
4. Calcula salud y racha.
5. Guarda el cierre.
6. Devuelve el resumen.
7. Actualiza la salud persistida de Nancy.

Reglas:

- El cierre es idempotente por usuario y fecha.
- Se puede cerrar un día sin movimientos; en ese caso aplica inactividad.
- El cierre guarda una foto del presupuesto vigente.
- El cierre no elimina ni modifica transacciones.
- Un día cerrado puede reabrirse lógicamente si se agrega, edita, anula o restaura un movimiento de esa fecha.
- Al reabrir, se recalculan el cierre y todos los días posteriores.
- El recálculo es determinista y reconstruye salud, puntos y racha.

### 5.13 Métricas

Pantallas: V09.1 diario, V09.2 semanal, V09.3 mensual, V10.1, V10.2, V10.3, V11.1.

Vistas:

- Diario: ingresos, gastos, ahorro, balance, cupo, categorías.
- Semanal: balance, capacidad libre de ahorro, guardados, ritmo de gasto.
- Mensual: ingresos, gastos, ahorro, categorías y presupuesto.
- Diagnóstico: días, racha, puntos, resultados.
- Flujo de caja: salud, rango seguro, presupuesto diario, margen libre.

Definiciones:

- Capacidad libre de ahorro = `ingresos - gastos - ahorros`.
- Ritmo semanal:
  - `súper sano`: gasto menor o igual al 70% del presupuesto acumulado.
  - `en ritmo`: 71% a 100%.
  - `alto`: 101% a 120%.
  - `excedido`: más de 120%.
- Rango seguro: gasto diario menor o igual al presupuesto.
- Margen libre: presupuesto menos gasto, sin valores negativos en la visualización.

### 5.14 Metas

Pantallas: V14, V14 Nueva Meta paso 1, 2, 3, V14.3.

Campos:

- Nombre.
- Icono.
- Monto objetivo.
- Fecha límite.
- Frecuencia de ahorro.
- Aporte periódico.
- Día de aporte.
- Hora de recordatorio.
- Prioridad.

Reglas:

- El ahorrado no se almacena; se calcula con transacciones de tipo ahorro confirmadas.
- El estado `Vas bien` o `Atrasada` se deriva del avance esperado.
- El avance esperado se calcula con los aportes programados vencidos.
- Tolerancia de cumplimiento: 95% del esperado.
- Una meta se completa cuando el ahorrado iguala o supera el monto objetivo.
- El evento de meta cumplida se registra una sola vez.
- El evento de meta atrasada se registra una sola vez por periodo.
- Eliminar una meta es lógico; las transacciones históricas conservan su referencia.
- Los recordatorios se envían según la hora configurada.
- Al cumplir una meta, Nancy muestra felicidad y se registra el evento.

### 5.15 Cuentas

Pantallas: V14.1, V14.1 Crear cuenta, V17 Detalle Cuentas, V17 Editar cuenta, V17 Eliminar Cuenta, modales.

Tipos:

- Efectivo.
- Billetera digital.
- Tarjeta.
- Cuenta de ahorros.
- Inversión.

Reglas:

- Las tarjetas no tienen saldo.
- Solo existe una cuenta por defecto por usuario.
- La cuenta por defecto se usa cuando el usuario no menciona una cuenta.
- La cuenta por defecto no puede ocultarse.
- Ocultar una cuenta no elimina sus movimientos.
- Eliminar una cuenta mueve todos sus movimientos, incluidos los de papelera, a otra cuenta.
- Una cuenta por defecto no se puede eliminar.
- Las cuentas del sistema se marcan como “Predet.”.
- `ultimos_4` guarda máximo cuatro dígitos; nunca el número completo.
- El saldo actual = saldo inicial + ingresos - gastos - ahorros.
- Las cuentas ocultas siguen sumando a los totales.

### 5.16 Categorías

Pantallas: V17 Categorías gastos, V17 Categorías ingresos, V17 Detalle, V17 Editar, V17 Agregar.

Categorías iniciales de gasto:

1. Alimentación.
2. Transporte.
3. Familia y detalles.
4. Ocio y gustos.
5. Vivienda y fijos.
6. Suscripciones.
7. Salud y aseo.
8. Deudas.
9. Finanzas.
10. Préstamos.
11. Ahorro e inversión.
12. Otros.

Categorías iniciales de ingreso:

1. Trabajo.
2. Apoyo familiar.
3. Beca.
4. Otros ingresos.

Reglas:

- Las categorías del sistema no se renombran ni cambian de tipo.
- Las categorías del sistema se pueden desactivar.
- Las categorías personalizadas se desactivan, no se eliminan.
- Las categorías inactivas no aparecen en nuevos registros, pero conservan su historial.
- `es_fija` marca la etiqueta “FIJO”.
- Cada categoría puede tener palabras asociadas.
- Una palabra no puede apuntar a dos categorías del mismo usuario.
- El límite mensual se define en el presupuesto aprobado.

### 5.17 Presupuesto

Pantallas: V05.6, V13, V17 Detalle categoría.

Reglas:

- El presupuesto diario es un valor por usuario.
- El historial de cambios se guarda por fecha en `presupuesto_diario_historial`.
- El presupuesto diario no se acumula.
- El presupuesto por categoría es mensual.
- El cupo diario de una categoría se calcula como `limite_mensual / dias_del_mes`.
- Un presupuesto de categoría solo aplica si el presupuesto padre está aprobado y cubre el mes.
- El usuario debe aprobar el presupuesto de 2-3 meses antes de usarlo.
- Los gastos fijos generan recordatorios, no movimientos automáticos.

### 5.18 Perfil y bienestar

Pantallas: V18.1 Perfil, V18.1 Sobre ti, V18.1 Tus ingresos, V18.1 Tus gastos y hábitos, V18.1 Cómo llevas tus cuentas, V18.1 Deudas y ahorro, V18.1 Bienestar, V18.1 Mejora tus métricas, V18.1.2 Datos personales, V18.1.2 Seguridad y Clave.

El perfil muestra:

- Racha actual.
- Ahorro del mes.
- Salud de Nancy.
- Bienestar financiero.
- Porcentaje de perfil completo.
- Secciones completas.
- Acceso a datos personales y seguridad.

El índice de bienestar se calcula con seis componentes:

| Componente | Peso | Cálculo |
|---|---:|---|
| Estrés financiero | 25% | `(10 - estres) / 9 * 100` |
| Sensación de seguridad | 20% | `100` si se siente seguro, `0` si no |
| Dificultad para llevar cuentas | 15% | `(5 - dificultad) / 4 * 100` |
| Deuda de tarjeta | 15% | `100` sin deuda, `50` si paga a cuotas, `0` si no paga |
| Fondo de emergencia | 15% | `100` si tiene, `0` si no |
| Capacidad de ahorro | 10% | `min(100, ahorro_mensual / (10% del ingreso))` |

Reglas:

- Si un componente no tiene dato, se excluye del promedio y se reduce la cobertura.
- `cobertura` indica qué porcentaje del índice está respaldado por datos.
- El bienestar no modifica la salud de Nancy.
- Completar secciones mejora la cobertura y las recomendaciones.
- Las recomendaciones muestran impacto estimado, por ejemplo “Salud +7” o “Bienestar +10”.
- Los impactos son proyecciones, no valores garantizados.

### 5.19 Notificaciones

Pantallas: V18.4, V18.4 al día, V18.4 cargando, V18.4 vacías, V18.4 error, V18.4 borrar movimiento.

Tipos:

- Movimiento registrado.
- Movimientos agrupados.
- Movimiento editado.
- Movimiento eliminado.
- Confirmación de entendimiento.
- Presupuesto diario excedido.
- Presupuesto por categoría excedido.
- Salud crítica.
- Meta atrasada.
- Meta cumplida.
- Racha en riesgo.
- Recordatorio diario.
- Sincronización.
- Batería baja.
- Dispositivo desconectado.
- Dispositivo vinculado o desvinculado.
- Resumen semanal.
- Perfil incompleto.

Reglas:

- Cada aviso tiene leído/no leído.
- Se puede marcar todo como leído.
- Se puede eliminar un aviso.
- El filtro por defecto muestra todos.
- Los avisos de presupuesto se deduplican por usuario, tipo, fecha y categoría.
- La hora del recordatorio diario es configurable.
- El modo silencio respeta una franja horaria.
- Las notificaciones push y correo quedan para una fase posterior.

### 5.20 Eliminación de cuenta

Pantallas: V18 Eliminar Perfil, V18 Eliminar Perfil definitivo.

Reglas:

- La eliminación tiene un periodo de gracia de 14 días.
- El usuario puede cancelar la solicitud.
- El usuario puede conservar datos anónimos para estudio.
- Al ejecutar la eliminación, se desvincula el dispositivo.
- Se eliminan o anonimizan datos según el consentimiento.
- Los registros financieros no se conservan asociados a una persona identificable.

---

## 6. Salud de Nancy

### 6.1 Principios

- La salud es un valor entero de 0 a 100.
- La salud no se modifica por cada transacción individual.
- La salud se consolida al cerrar el día.
- Durante el día se muestra una proyección calculada con las reglas del cierre.
- Cada cambio se registra en `salud_log`.
- `estado_mascota.salud` es una caché del último cierre; se puede reconstruir.
- El ánimo nunca se almacena; se deriva de la salud.
- La salud no puede subir por encima de 100 ni bajar por debajo de 0.
- Un día con salud 0 deja a Nancy en estado crítico, pero puede recuperarse en días posteriores.

### 6.2 Reglas diarias

| Código | Condición | Cambio | Tope |
|---|---|---:|---:|
| `EXCESO_DIARIO` | Gastos del día mayores al presupuesto diario | -2 por cada $5.000 o fracción excedida | -20 por día |
| `EXCESO_CATEGORIA` | Gasto de una categoría mayor a su cupo diario | -2 por categoría excedida | -15 por día |
| `BALANCE_POSITIVO` | Balance neto positivo y sin excesos | +2 por cada $20.000 | +15 por día |
| `AHORRO` | Ahorro confirmado del día | +1 por cada $20.000 | +10 por día |
| `INACTIVIDAD` | Día cerrado sin transacciones confirmadas | -5 por día | -20 acumulado por ausencia |
| `RACHA` | Racha que alcanza 7, 14 o 30 días | +5, +10, +15 | Una vez por hito |
| `META_CUMPLIDA` | Meta completada | +5 | +15 por mes |
| `META_ATRASADA` | Meta atrasada en el periodo | -5 | -15 por mes |

Reglas adicionales:

- El tope global por día es `-35` a `+25`.
- Si la suma de reglas excede el tope, se registra un ajuste con código `TOPE_GLOBAL`.
- El cupo diario de categoría se calcula con el límite mensual aprobado dividido entre los días del mes.
- Si una categoría no tiene límite mensual, no genera penalización por categoría.
- Una categoría con límite 0 y gasto mayor que 0 se considera excedida.
- La inactividad se evalúa por días consecutivos sin movimientos.
- La racha solo cuenta días cerrados con al menos una transacción confirmada.
- Las metas se evalúan al cierre del día.
- Las penalizaciones se aplican antes que los bonos.
- La salud final se calcula como `clamp(salud_inicio + delta_dia, 0, 100)`.

### 6.3 Ánimo

| Salud | Ánimo | Alias visual |
|---:|---|---|
| 81-100 | `FELIZ` | radiante, feliz, óptima |
| 51-80 | `PREOCUPADO` | normal, atenta |
| 21-50 | `TRISTE` | decaída, triste |
| 0-20 | `CRITICO` | alerta, crítica, enferma |

El alias visual puede cambiar sin modificar el valor oficial.

### 6.4 Proyección y persistencia

- La proyección usa los mismos cálculos del cierre sobre las transacciones confirmadas del día en curso.
- La proyección no crea filas en `salud_log`.
- Al cerrar, se crean las filas de `salud_log` y se actualiza `estado_mascota`.
- Al editar un día cerrado, se eliminan los cierres y registros de salud desde esa fecha y se reconstruyen.
- La reconstrucción debe ser idempotente.

### 6.5 Registro de salud

Cada fila de `salud_log` contiene:

- Usuario.
- Fecha local.
- Código de regla.
- Motivo.
- Salud anterior.
- Salud nueva.
- Delta calculado.
- Tipo y referencia del hecho.
- Detalle JSON.
- Fecha de creación.

El delta se calcula automáticamente como `salud_nueva - salud_anterior`.

---

## 7. Puntos y racha

### 7.1 Puntos

- Cada transacción confirmada otorga 1 punto.
- Las transacciones pendientes no otorgan puntos.
- Las transacciones anuladas dejan de sumar.
- Al restaurar una transacción, sus puntos vuelven a contar.
- No se usa XP ni niveles.
- Los puntos se pueden ajustar manualmente con motivo `ajuste`.
- Los bonos por semana, hito o meta quedan reservados para versiones futuras; en la versión actual no se otorgan automáticamente.

### 7.2 Racha

- La racha cuenta días consecutivos con al menos una transacción confirmada.
- Un día sin movimientos rompe la racha.
- La racha actual y la mejor racha se guardan en `progreso_etapa`.
- La racha se recalcula al cerrar y al reconstruir días.
- Los hitos de 7, 14 y 30 días generan salud, no puntos.

---

## 8. Metas y planes

### 8.1 Cálculo del avance

- `ahorrado` = suma de transacciones de ahorro confirmadas y no eliminadas.
- `faltante` = monto objetivo menos ahorrado.
- `porcentaje` = ahorrado / monto objetivo.
- `esperado` = aportes programados vencidos, limitado al monto objetivo.
- `atrasada` si `ahorrado < esperado * 0.95`.
- `vas_bien` si no está atrasada y no está completa.
- `completada` si `ahorrado >= monto objetivo`.

### 8.2 Frecuencias

- Diaria: aportes por cada día transcurrido.
- Semanal: aportes por cada semana transcurrida.
- Quincenal: aportes por cada 15 días.
- Mensual: aportes por cada mes calendario.

### 8.3 Eventos

- `cumplida` se registra una vez por meta.
- `atrasada` se registra una vez por periodo.
- `recordatorio` se registra según la programación.
- `aporte` se registra cuando se confirma un ahorro asociado.

La clave de periodo evita duplicados.

---

## 9. Agente IA

### 9.1 Interfaz

El backend expone un proveedor de transcripción con estas operaciones:

- `transcribe_audio(audio_bytes, mime_type, language) -> texto`.
- `interpretar(texto, contexto_usuario) -> propuesta`.
- `clasificar_categoria(texto, categorias_usuario) -> categoria_id`.
- `esta_configurado() -> estado`.

**Decisión vigente.** La transcripción la hace un proveedor de STT en el backend (`backend/ai.py`) y la interpretación de montos, categorías y cuentas sigue con las **reglas locales** de `backend/nlp.py`. El proveedor solo transcribe: nunca decide montos ni confirmaciones.

Hay dos proveedores:

| Proveedor | Qué es | Clave | Cuota | Latencia |
|---|---|---|---|---|
| `gemini` | Gemini Flash por la API de Google | `GEMINI_API_KEY` | 3 peticiones/min en la capa gratuita | 3–5 s |
| `local` | faster-whisper corriendo en el PC del backend | no | ninguna | ~1 s |

`STT_PROVEEDOR` decide el comportamiento:

- `auto` (por defecto): usa Gemini si hay clave y responde. Si la clave está rota, no hay cuota o el proveedor falla, cae al modelo local y deja constancia del motivo en `interacciones_ia`.
- `gemini`: solo la API de Google. Si falla, el endpoint responde error.
- `local`: solo el modelo local del PC. No necesita clave ni conexión.

**Por qué existe el proveedor local.** Desde el 28 de mayo de 2026 Google AI Studio solo emite "Auth keys" (`AQ.Ab...`) en lugar de las estándar (`AIza...`), y hay un problema abierto de compatibilidad: esas claves responden `401 UNAUTHENTICATED` con motivo `ACCESS_TOKEN_TYPE_UNSUPPORTED` en `generativelanguage.googleapis.com`. El modelo local garantiza que el proyecto se pueda demostrar sin depender de ese servicio.

El modelo se configura con `GEMINI_MODEL` y admite una cadena de respaldo con `GEMINI_MODEL_FALLBACKS`, porque la API de Google puede responder con `503` por demanda alta o dejar de ofrecer un modelo. El modelo local se configura con `STT_MODELO_LOCAL` (`tiny`, `base`, `small`, `medium`).

Los modelos locales (whisper, Ollama, llama.cpp, Gemma) se ejecutan en el **PC o servidor del backend**, nunca en la ESP32. La ESP32 solo graba, envía y muestra.

### 9.1.1 Interpretación: el modelo de lenguaje

Transcribir no basta. Hay un paso aparte donde un modelo de lenguaje decide **qué tipo de movimiento es, el monto, la categoría y la cuenta**. Ese paso lo hace `nlp.interpretar_con_ia`.

| Proveedor | Clave | Latencia | Notas |
|---|---|---|---|
| `ollama` | no | 2–8 s | Modelo local. `qwen3:4b` por defecto. Gratis, offline, sin cuota. |
| `gemini` | sí | 1–3 s | Solo si la API key funciona. |

El modelo recibe el catálogo real del usuario (sus categorías con su tipo y sus cuentas) y debe responder un JSON:

```json
{
  "tipo": "gasto",
  "monto": 20000,
  "categoria": "Alimentación",
  "cuenta": "Nequi",
  "concepto": "almuerzo del viernes"
}
```

**La respuesta se valida contra la base de datos antes de aceptarla:**

| Campo | Regla de validación |
|---|---|
| `tipo` | Debe ser `gasto`, `ingreso` o `ahorro`. |
| `monto` | Entero positivo. Si falta, se usa el monto que sale de las reglas. |
| `categoria` | Debe existir en las categorías del usuario y ser del mismo tipo que el movimiento. Si no, se deja vacía. |
| `cuenta` | Debe existir en las cuentas del usuario. Si no, se usa la cuenta por defecto. |

Así el modelo puede equivocarse sin romper nada: lo que no cuadra con el catálogo del usuario se descarta y se completa con las reglas.

Si no hay ningún LLM disponible, `nlp.interpret` usa las reglas por palabra clave (`NLP_USAR_IA=off` las fuerza).

### 9.1.2 Hotwords de transcripción

El modelo de transcripción recibe los nombres de cuentas y categorías del usuario como `initial_prompt`. Sin esto, los modelos de ASR escriben las marcas de forma aproximada:

| Frase | Sin hotwords | Con hotwords |
|---|---|---|
| "gasté 20.000 por nequi" | "por Nike" | "por Nequi" |
| "compré 5.000 con daviplata" | "con David Plata" | "con Daviplata" |
| "me pagaron 800.000 a la cuenta nu" | "a la cuenta no" | "a la cuenta Nu" |

La lista se arma con `nlp.palabras_clave_usuario` a partir de las cuentas y categorías activas del usuario.

### 9.2 Contexto permitido

- Texto transcrito.
- Fecha y hora local.
- Categorías activas del usuario.
- Cuentas activas del usuario.
- Metas activas.
- Presupuesto del día.
- Historial reciente de movimientos, solo si el usuario lo autoriza.

No se envían correos, teléfonos, números completos de tarjeta ni tokens.

### 9.3 Salida esperada

```json
{
  "texto_entendido": "pagué 14.000 en el almuerzo y 3.000 de bus",
  "requiere_confirmacion": true,
  "transacciones": [
    {
      "tipo": "gasto",
      "monto": 14000,
      "categoria_id": 1,
      "cuenta_id": 1,
      "meta_id": null,
      "concepto": "almuerzo",
      "confianza": 0.94
    },
    {
      "tipo": "gasto",
      "monto": 3000,
      "categoria_id": 2,
      "cuenta_id": 1,
      "meta_id": null,
      "concepto": "bus",
      "confianza": 0.91
    }
  ]
}
```

### 9.4 Reglas

- La transcripción y la clasificación de categoría se ejecutan en el backend.
- El dispositivo no envía texto transcrito; envía audio y recibe el resultado.
- Siempre se requiere confirmación humana antes de guardar; la IA solo propone.
- Al confirmar, se crea una notificación `movimiento_registrado` asociada al dispositivo de origen.
- Si falta el monto, no se asigna uno por defecto.
- Si falta la categoría, se propone la más probable y se marca para revisión.
- Si falta la cuenta, se usa la cuenta por defecto.
- Si el texto menciona una meta, se propone `meta_id`.
- Si el texto contiene varias acciones, se devuelven varias transacciones.
- La confianza se guarda por transacción y por interacción.
- Si el proveedor de transcripción falla, no se crea el mensaje: el dispositivo reintenta con el mismo `message_id`.
- Si el intérprete de reglas falla, el mensaje queda pendiente de revisión.
- Si el guardado fue exitoso, se encola una notificación para el dispositivo y para la app.
- Las interacciones se auditan en `interacciones_ia`, guardando solo metadatos: el audio nunca se persiste.
- El texto transcrito puede traer el monto en cifras (`14.000`) o en palabras (`catorce mil`); el intérprete de reglas entiende ambas formas y también los millones (`1.5 millones`).

---

## 10. Dispositivo ESP32

El diseño visual y el pinout del dispositivo se documentan en `docs/DISPOSITIVO.md`. Ese paso queda en stand-by hasta recibir los mockups, tokens y assets de la diseñadora; el firmware no debe comenzar antes.

### 10.1 Estados

- `reposo`.
- `grabando`.
- `subiendo_audio`.
- `procesando`.
- `notificado`.
- `bloqueado`.

### 10.2 Conexión

- BLE para configuración inicial.
- Wi-Fi para operación normal, incluido el envío del audio.
- Token de dispositivo en cada petición.
- El audio se sube al backend; la transcripción no ocurre en el dispositivo.
- La notificación de “registro guardado” se recibe por polling HTTP cada 3–5 segundos.
- El polling usa `after_id` para no repetir notificaciones y envía acuse al mostrarlas.
- Reintentos con backoff.
- El dispositivo trabaja con conexión permanente: si la red falla, reintenta con el mismo `message_id` en lugar de guardar audio en cola.
- Confirmación visual al recibir respuesta del backend.

### 10.3 Contrato de audio y telemetría

El audio viaja como `multipart/form-data`; la telemetría solo lleva metadatos. Contrato propuesto:

```json
{
  "device_id": "FINAGOTCHI-PC-SIMULATOR-01",
  "message_id": "9e4f0d7a-3a2b-4c7d-8e1f-123456789abc",
  "sequence": 42,
  "timestamp": "2026-11-02T18:40:00Z",
  "firmware_version": "v1.0",
  "battery_level_pct": 85,
  "hardware": {
    "button_state": true,
    "device_status": "subiendo_audio",
    "audio_duration_sec": 3.5
  },
  "audio": {
    "format": "wav",
    "sample_rate": 16000,
    "channels": 1,
    "sha256": "..."
  }
}
```

Respuesta del procesamiento (aún sin guardar):

```json
{
  "ok": true,
  "data": {
    "id": 1,
    "message_id": "9e4f0d7a-3a2b-4c7d-8e1f-123456789abc",
    "estado": "pendiente",
    "texto_transcrito": "gasté 14.000 en el almuerzo",
    "transacciones": [],
    "requiere_confirmacion": true
  }
}
```

Respuesta al confirmar:

```json
{
  "ok": true,
  "data": {
    "id": 1,
    "estado": "confirmado",
    "puntos_otorgados": 1,
    "notificacion": {
      "id": 12,
      "tipo": "movimiento_registrado",
      "titulo": "Registro guardado",
      "estado": "pendiente",
      "duplicado": false
    }
  }
}
```

### 10.4 Reglas

- El backend acepta audio corto y ejecuta transcripción y clasificación con la IA.
- El texto directo se mantiene solo como compatibilidad temporal y para pruebas.
- El mensaje se procesa una sola vez por `message_id`.
- La batería menor o igual a 20% genera aviso.
- La batería menor o igual a 10% genera aviso crítico.
- La pérdida de conexión muestra los registros pendientes.
- El comando de desvinculación revoca el token y restaura el estado de fábrica.
- El comando de sincronización solicita los mensajes pendientes.
- Los comandos se guardan en `dispositivos_comandos`.
- La telemetría se guarda en `dispositivos_telemetria`.
- Las notificaciones se entregan por polling HTTP; el dispositivo consulta primero `pendiente` y luego marca `entregada` o `leida`.
- La confirmación del mensaje crea como máximo una notificación `movimiento_registrado` por mensaje y dispositivo.

---

## 11. API HTTP

Base: `/api/v1`

### 11.1 Formato de respuesta

Éxito:

```json
{
  "ok": true,
  "data": {}
}
```

Error:

```json
{
  "ok": false,
  "error": {
    "codigo": "VALIDACION",
    "mensaje": "El monto debe ser mayor que cero",
    "detalles": {}
  }
}
```

Códigos:

- `400` validación.
- `401` no autenticado.
- `403` sin permiso.
- `404` no existe.
- `409` conflicto o duplicado.
- `422` regla de negocio.
- `429` demasiadas solicitudes.
- `500` error interno.

### 11.2 Autenticación

| Método | Ruta | Uso |
|---|---|---|
| POST | `/auth/register` | Crear cuenta |
| POST | `/auth/login` | Iniciar sesión |
| POST | `/auth/refresh` | Renovar token |
| POST | `/auth/logout` | Revocar sesión |
| POST | `/auth/forgot-password` | Solicitar recuperación |
| POST | `/auth/reset-password` | Cambiar clave con token |
| POST | `/auth/verify-email` | Verificar correo |

### 11.3 Usuario y perfil

| Método | Ruta | Uso |
|---|---|---|
| GET | `/me` | Datos de cuenta |
| PATCH | `/me` | Editar datos personales |
| GET | `/me/profile` | Perfil financiero |
| PATCH | `/me/profile` | Actualizar sección |
| GET | `/me/wellbeing` | Índice de bienestar |
| GET | `/me/consents` | Consultar consentimientos |
| POST | `/me/consents` | Registrar consentimiento |

### 11.4 Dispositivo

| Método | Ruta | Uso |
|---|---|---|
| POST | `/device/pair` | Vincular por QR o PIN |
| GET | `/device` | Estado del dispositivo |
| POST | `/device/unlink` | Desvincular |
| POST | `/device/commands` | Crear comando |
| GET | `/device/commands` | Consultar comandos pendientes |
| POST | `/device/telemetry` | Recibir telemetría del dispositivo |
| POST | `/device/messages` | Procesar audio o texto desde el dispositivo |
| POST | `/device/messages/{id}/confirm` | Confirmar transacciones desde el dispositivo |
| GET | `/device/notifications` | Consultar notificaciones pendientes por polling |
| POST | `/device/notifications/{id}/ack` | Acusar recibo de una notificación |
| POST | `/device/notifications/ack` | Acusar recibo de varias notificaciones |

### 11.5 Movimientos y mensajes

| Método | Ruta | Uso |
|---|---|---|
| POST | `/messages` | Registrar texto o audio |
| GET | `/messages/{id}` | Consultar procesamiento |
| POST | `/messages/{id}/confirm` | Confirmar transacciones |
| GET | `/transactions` | Listar movimientos |
| POST | `/transactions` | Crear movimiento manual |
| GET | `/transactions/{id}` | Detalle |
| PATCH | `/transactions/{id}` | Editar |
| DELETE | `/transactions/{id}` | Anular |
| POST | `/transactions/{id}/restore` | Restaurar |
| GET | `/trash` | Papelera |
| POST | `/transactions/bulk-confirm` | Confirmar varias pendientes |

### 11.6 Días y métricas

| Método | Ruta | Uso |
|---|---|---|
| GET | `/home` | Resumen del día |
| POST | `/days/{fecha}/close` | Cerrar día |
| GET | `/days/{fecha}` | Resumen de un día |
| GET | `/metrics/daily` | Métricas diarias |
| GET | `/metrics/weekly` | Métricas semanales |
| GET | `/metrics/monthly` | Métricas mensuales |
| GET | `/metrics/health` | Salud y ánimo |
| GET | `/metrics/diagnosis` | Progreso del diagnóstico |

### 11.7 Metas, cuentas, categorías y presupuesto

| Método | Ruta | Uso |
|---|---|---|
| GET | `/goals` | Listar metas |
| POST | `/goals` | Crear meta |
| GET | `/goals/{id}` | Detalle |
| PATCH | `/goals/{id}` | Editar |
| DELETE | `/goals/{id}` | Eliminar lógicamente |
| GET | `/accounts` | Listar cuentas |
| POST | `/accounts` | Crear cuenta |
| PATCH | `/accounts/{id}` | Editar |
| DELETE | `/accounts/{id}` | Eliminar y mover movimientos |
| GET | `/categories` | Listar categorías |
| POST | `/categories` | Crear categoría |
| PATCH | `/categories/{id}` | Editar |
| POST | `/categories/{id}/deactivate` | Desactivar |
| GET | `/budgets` | Consultar presupuestos |
| POST | `/budgets` | Crear presupuesto |
| POST | `/budgets/{id}/approve` | Aprobar |
| GET | `/budget` | Presupuesto diario |
| PATCH | `/budget` | Cambiar presupuesto diario |

### 11.8 Notificaciones

| Método | Ruta | Uso |
|---|---|---|
| GET | `/notifications` | Listar avisos |
| PATCH | `/notifications/{id}/read` | Marcar leído |
| POST | `/notifications/read-all` | Marcar todo leído |
| DELETE | `/notifications/{id}` | Descartar aviso |
| GET | `/notification-preferences` | Consultar preferencias |
| PATCH | `/notification-preferences` | Actualizar preferencias |

### 11.9 Audio y notificaciones del dispositivo

Los endpoints de esta sección usan `X-Device-Token`. Los equivalentes de app usan `Authorization: Bearer <token>`. Todas las respuestas siguen el sobre `{"ok": true, "data": ...}` o `{"ok": false, "error": {...}}`.

#### `POST /device/messages`

Procesa audio o texto enviado por el dispositivo. El audio se transcribe en el backend con Gemini Flash y luego se clasifica con las reglas locales; el dispositivo nunca transcribe.

Estado de implementación: **operativo**. El endpoint recibe `audio` (multipart) o `texto` (JSON o multipart). Con audio se valida el WAV, se transcribe, se registra la auditoría en `interacciones_ia` y se crea el mensaje con sus transacciones pendientes.

- Autenticación: `X-Device-Token`.
- `Content-Type`: `multipart/form-data` para audio o `application/json` para texto.
- Campos:

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `audio` | archivo | Sí, si no hay `texto` | WAV, 16 kHz, mono, 16 bits, 0.5–40 s, máximo 2 MB. |
| `texto` | texto | Sí, si no hay `audio` | Fallback de pruebas o cuando el STT corre en el cliente. |
| `message_id` | UUID | Sí, si hay `audio` | Idempotencia; un mismo `message_id` no se procesa dos veces. |
| `audio_duracion_s` | número | No | Informativo. La duración real la calcula el servidor a partir del WAV. |
| `idioma` | texto | No | `es-CO` por defecto. |

Orden de procesamiento:

1. Si el `message_id` ya existe, se devuelve el mensaje guardado con `duplicado: true` **sin volver a llamar a la IA**.
2. Se valida el WAV: 16 kHz, mono, 16 bits, 0.5–40 s y máximo 2 MB.
3. Se transcribe con Gemini Flash.
4. Se interpretan montos, categoría y cuenta con `backend/nlp.py`.
5. Se guarda el texto, la duración y la auditoría. El audio no se persiste en ningún sitio.

Respuesta `201` en el primer procesamiento y `200` si el mensaje es duplicado:

```json
{
  "ok": true,
  "data": {
    "id": 1,
    "message_id": "9e4f0d7a-3a2b-4c7d-8e1f-123456789abc",
    "estado": "pendiente",
    "texto_transcrito": "gasté 14.000 en el almuerzo",
    "duracion_audio_s": 3.84,
    "transacciones": [],
    "puntos_otorgados": 0,
    "requiere_confirmacion": true,
    "duplicado": false
  }
}
```

Errores:

| Código | HTTP | Cuándo ocurre |
|---|---|---|
| `CAMPOS_REQUERIDOS` | 422 | Falta `audio` y `texto`, o falta `message_id` cuando hay audio. |
| `AUDIO_INVALIDO` | 422 | El WAV no cumple el formato o la duración (0.5–40 s). |
| `AUDIO_MUY_GRANDE` | 413 | El archivo supera los 2 MB. |
| `STT_NO_CONFIGURADO` | 503 | Falta la API key y no hay proveedor local disponible. |
| `STT_KEY_INVALIDA` | 502 | Google rechazó la credencial (401). Ocurre con las "Auth keys" (`AQ.Ab...`). |
| `STT_SIN_PERMISOS` | 502 | La credencial es válida pero no tiene acceso al modelo (403). |
| `STT_CUOTA` | 429 | Google rechazó la petición por límite de cuota. |
| `STT_NO_DISPONIBLE` | 502 | Google no responde o el modelo no está disponible. |
| `STT_ERROR` | 502 | Cualquier otro fallo del proveedor. |
| `STT_SIN_TEXTO` | 422 | El modelo no devolvió texto para el audio recibido. |

Cuando la transcripción falla no se crea el mensaje ni la transacción: el dispositivo puede reintentar con el mismo `message_id`.

#### `POST /messages`

Equivalente para la app. Usa `Authorization: Bearer <token>`. Acepta los mismos campos y además `device_id` y `origen` (`app_voz` por defecto). Mismo contrato de respuesta.

#### Configuración del proveedor de transcripción

La transcripción se configura en `backend/.env` (copiar `backend/.env.example`). La clave nunca viaja al dispositivo ni al frontend.

| Variable | Default | Descripción |
|---|---|---|
| `GEMINI_API_KEY` | vacío | Clave de la API de Gemini. Sin ella el audio responde `STT_NO_CONFIGURADO`. |
| `GEMINI_MODEL` | `gemini-3.8-flash` | Modelo principal de transcripción. |
| `GEMINI_MODEL_FALLBACKS` | `gemini-3.5-flash,gemini-3.5-flash-lite` | Modelos alternos cuando el principal no responde. |
| `GEMINI_TIMEOUT_S` | `60` | Tiempo máximo de espera de una llamada. |
| `GEMINI_PLAZO_S` | `90` | Tiempo máximo total de todos los reintentos. |
| `STT_PROVEEDOR` | `auto` | `auto`, `gemini` o `local`. |
| `STT_MODELO_LOCAL` | `base` | Modelo de faster-whisper: `tiny`, `base`, `small`, `medium`. |

La API de Google puede responder `503` por demanda alta o retirar un modelo. El backend reintenta con el siguiente modelo de la cadena antes de devolver un error, y el dispositivo puede reintentar con el mismo `message_id`.

**Límites de la capa gratuita.** Google limita a 3 peticiones por minuto y por modelo. Al agotarse la cuota la latencia de transcripción sube de 3–5 segundos a 16–18 segundos y las peticiones responden `429`. El backend tiene un plazo total (`GEMINI_PLAZO_S`, 90 segundos por defecto) para no dejar la petición colgada. Para una demo frente a la docencia o para producción se recomienda una cuenta de pago; la clave sigue siendo la misma.

#### Auditoría de las llamadas a la IA

Cada llamada al proveedor se registra en `interacciones_ia`:

| Columna | Contenido |
|---|---|
| `proveedor` | `google`. |
| `modelo` | Modelo que respondió. |
| `version_prompt` | Prompt de transcripción usado. |
| `entrada_json` | Metadatos del audio: `mime_type`, `duracion_s` e `idioma`. |
| `salida_json` | Texto transcrito o el error de la llamada. |
| `latencia_ms` | Tiempo de la llamada. |
| `tokens_entrada` / `tokens_salida` | Consumo de tokens. |
| `mensaje_id` | Mensaje resultante. Es `NULL` si la transcripción falló. |

El audio no se guarda ni en la base ni en disco, ni siquiera de forma temporal: se procesa en memoria durante la petición.

#### `POST /device/messages/{id}/confirm` y `POST /messages/{id}/confirm`

Confirman todas las transacciones pendientes del mensaje. No requieren cuerpo. Solo después de este paso el movimiento afecta balances, salud, puntos y metas. Si el mensaje se originó en un dispositivo, se crea una notificación `movimiento_registrado` en estado `pendiente`.

Respuesta:

```json
{
  "ok": true,
  "data": {
    "id": 1,
    "estado": "confirmado",
    "puntos_otorgados": 1,
    "transacciones": [],
    "notificacion": {
      "id": 12,
      "tipo": "movimiento_registrado",
      "titulo": "Registro guardado",
      "estado": "pendiente",
      "duplicado": false
    }
  }
}
```

Errores: `401`, `403`, `404` mensaje inexistente.

#### `GET /device/notifications`

Consulta la cola de notificaciones del dispositivo por polling. Por defecto devuelve las que están en `pendiente` o `entregada` y no han sido leídas.

- Autenticación: `X-Device-Token`.
- Parámetros de consulta:

| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| `after_id` | entero | `0` | Devuelve solo notificaciones con `id` mayor. |
| `limit` | entero | `20` | Máximo 100. |
| `estado` | texto | vacío | Filtra por `pendiente`, `entregada` o `leida`. |

Respuesta:

```json
{
  "ok": true,
  "data": {
    "notificaciones": [
      {
        "id": 12,
        "dispositivo_id": 3,
        "mensaje_id": 1,
        "transaccion_id": 8,
        "tipo": "movimiento_registrado",
        "titulo": "Registro guardado",
        "mensaje": "Se guardo el registro en FinaGotchi",
        "payload_json": "{\"message_id\": \"...\", \"transacciones\": 1}",
        "estado": "pendiente",
        "creado_en": "2026-11-02T18:40:00Z",
        "entregado_en": null,
        "leido_en": null
      }
    ],
    "ultima_id": 12
  }
}
```

El dispositivo guarda `ultima_id` y lo envía como `after_id` en el siguiente polling. Intervalo recomendado: 3–5 segundos.

#### `POST /device/notifications/{id}/ack`

Marca una notificación como recibida o leída.

- Cuerpo: `{"estado": "entregada"}` o `{"estado": "leida"}`; por defecto `leida`.
- `entregada`: solo aplica desde `pendiente`.
- `leida`: aplica desde `pendiente` o `entregada` y completa `entregado_en` y `leido_en`.

Respuesta:

```json
{
  "ok": true,
  "data": {
    "id": 12,
    "estado": "leida",
    "entregado_en": "2026-11-02T18:40:05Z",
    "leido_en": "2026-11-02T18:40:05Z"
  }
}
```

Errores: `400` estado inválido, `401`, `403`, `404` notificación inexistente para ese dispositivo.

#### `POST /device/notifications/ack`

Acuse en lote.

- Cuerpo: `{"ids": [12, 13], "estado": "leida"}`.
- Respuesta: `{"ok": true, "data": {"actualizadas": 2}}`.
- Los ids que no pertenecen al dispositivo se ignoran. Si la lista está vacía o no es una lista, responde `422`.

#### Máquina de estados de la notificación

`pendiente` → `entregada` → `leida`.

- Se crea siempre en `pendiente`.
- El polling no cambia el estado; el cambio ocurre con el acuse.
- Una notificación ya `leida` no se vuelve a entregar salvo que se consulte con `estado=leida`.
- El CHECK de la tabla impide combinaciones incoherentes entre `estado`, `entregado_en` y `leido_en`.

---

## 12. Modelo de datos

El esquema se divide en:

- `001_schema.sql`: tablas, índices, restricciones y triggers.
- `002_views.sql`: vistas de cálculo.
- `003_seed.sql`: catálogos iniciales y versión.

### 12.1 Tablas principales

| Tabla | Propósito |
|---|---|
| `usuarios` | Cuenta, credenciales y presupuesto diario vigente. |
| `consentimientos` | Evidencia de términos y privacidad. |
| `perfil_financiero` | Respuestas del test y encuesta. |
| `perfil_secciones` | Estado de completitud por sección. |
| `dispositivos` | Estado, token y batería del hardware. |
| `vinculacion_codigos` | QR/PIN temporales. |
| `cuentas` | Medios de pago y saldos iniciales. |
| `categorias` | Categorías de gasto e ingreso. |
| `metas` | Objetivos de ahorro. |
| `mensajes_dispositivo` | Capturas y procesamiento idempotente. |
| `transacciones` | Movimientos financieros. |
| `transacciones_versiones` | Historial de ediciones. |
| `interacciones_ia` | Auditoría del agente. |
| `gastos_fijos` | Gastos recurrentes. |
| `presupuestos` | Presupuesto de 2-3 meses. |
| `presupuesto_categoria` | Límite mensual por categoría. |
| `presupuesto_diario_historial` | Cambios del presupuesto diario. |
| `cierres_dia` | Foto de cada día cerrado. |
| `estado_mascota` | Salud persistida. |
| `salud_log` | Cambios de salud explicados. |
| `puntos_log` | Puntos otorgados. |
| `metas_eventos` | Eventos de metas. |
| `alertas_log` | Notificaciones y avisos. |
| `dispositivos_notificaciones` | Cola de notificaciones por dispositivo con estados `pendiente`, `entregada` y `leida`. |
| `dispositivos_telemetria` | Telemetría del hardware. |
| `dispositivos_comandos` | Comandos hacia el hardware. |
| `schema_migrations` | Versión del esquema. |

### 12.2 Vistas

| Vista | Propósito |
|---|---|
| `v_movimientos` | Historial activo. |
| `v_papelera` | Movimientos anulados. |
| `v_presupuesto_diario_actual` | Presupuesto vigente hoy. |
| `v_balance_diario` | Totales y cupo por día. |
| `v_balance_mensual` | Totales por mes. |
| `v_cuentas_resumen` | Saldo y número de movimientos por cuenta. |
| `v_gasto_categoria_mes` | Gasto y límite mensual por categoría. |
| `v_gasto_categoria_dia` | Gasto diario por categoría. |
| `v_puntos_usuario` | Puntos válidos. |
| `v_progreso_etapa` | Registros, días, puntos y cierres. |
| `v_estado_mascota` | Salud y ánimo derivado. |
| `v_perfil_completitud` | Porcentaje de perfil. |
| `v_bienestar_financiero` | Índice de bienestar y cobertura. |
| `v_metas_progreso` | Ahorro, faltante y porcentaje. |
| `v_metas_estado` | Estado del plan de ahorro. |

### 12.3 Invariantes

- Una transacción confirmada siempre tiene cuenta.
- Un gasto o ingreso siempre tiene categoría del mismo tipo.
- Un ahorro no tiene categoría y puede tener meta.
- Un gasto o ingreso no tiene meta.
- Una tarjeta no tiene saldo inicial.
- Solo hay una cuenta por defecto por usuario.
- Una cuenta por defecto no puede estar oculta.
- Una categoría del sistema no se renombra.
- Un mensaje es único por usuario.
- Un mensaje puede tener varias transacciones.
- Las transacciones anuladas no afectan cálculos.
- La salud está entre 0 y 100.
- Los cierres son únicos por usuario y fecha.
- Los puntos por transacción se otorgan una sola vez.
- Los eventos de meta se deduplican por periodo.

---

## 13. Seguridad y privacidad

- Contraseñas con `scrypt`, `bcrypt` o `argon2`.
- Tokens de recuperación, verificación y refresco guardados como hash.
- Token de dispositivo guardado como hash.
- Validación de entrada en todos los endpoints.
- Consultas parametrizadas.
- Límite de intentos de autenticación y vinculación.
- CORS restringido al frontend conocido.
- HTTPS obligatorio en producción.
- No registrar tokens, contraseñas ni texto financiero completo en logs.
- Datos de tarjeta: solo últimos cuatro dígitos.
- Consentimiento explícito para datos de estudio.
- Retención de papelera: 30 días.
- Gracia de eliminación de cuenta: 14 días.
- Respaldos cifrados en producción.
- Separación de secretos mediante variables de entorno.

---

## 14. Requisitos no funcionales

- SQLite con `foreign_keys=ON`, WAL y `busy_timeout`.
- Respuesta de API menor a 500 ms en operaciones locales normales.
- Procesamiento de voz menor a 5 segundos con proveedor disponible.
- Funcionamiento offline del dispositivo con cola local.
- Migraciones versionadas y reversibles mediante respaldo.
- Registro de errores sin datos sensibles.
- Pruebas automatizadas de esquema, reglas y API.
- Compatibilidad con Python 3.10+.
- Compatibilidad con SQLite 3.31+.
- Portabilidad documentada a PostgreSQL 12+.

---

## 15. Trazabilidad con Figma

| Pantalla | Regla principal | Tablas | Endpoint |
|---|---|---|---|
| V01 | Presentación | — | — |
| V02.1 | Registro y consentimiento | `usuarios`, `consentimientos` | `/auth/register` |
| V02.2 | Login y recuperación | `usuarios`, `tokens_recuperacion`, `sesiones_refresco` | `/auth/login` |
| V02.3 | Consentimiento | `consentimientos` | `/me/consents` |
| V03 | Vinculación QR/PIN | `dispositivos`, `vinculacion_codigos` | `/device/pair` |
| V04 | Tres etapas | `progreso_etapa` | `/metrics/diagnosis` |
| V05 | Test inicial | `perfil_financiero`, `perfil_secciones` | `/me/profile` |
| V06.1 | Inicio del día | `v_balance_diario`, `v_estado_mascota` | `/home` |
| V07.1 | Voz | `mensajes_dispositivo`, `interacciones_ia` | `/messages` |
| V07.2 | Confirmación y edición | `transacciones` | `/transactions` |
| V07.3 | Registro manual | `transacciones` | `/transactions` |
| V08.1 | Movimientos y papelera | `transacciones`, `v_movimientos`, `v_papelera` | `/transactions` |
| V09 | Métricas | `v_balance_diario`, `v_balance_mensual` | `/metrics/*` |
| V10 | Puntos y racha | `puntos_log`, `progreso_etapa` | `/metrics/diagnosis` |
| V11.1 | Flujo de caja | `v_balance_diario`, `v_estado_mascota` | `/metrics/daily` |
| V14 | Metas | `metas`, `metas_eventos`, `v_metas_estado` | `/goals` |
| V14.1 | Cuentas | `cuentas`, `v_cuentas_resumen` | `/accounts` |
| V17 | Categorías y cuentas | `categorias`, `cuentas` | `/categories`, `/accounts` |
| V18.1 | Perfil y bienestar | `perfil_financiero`, `v_bienestar_financiero` | `/me/profile` |
| V18.4 | Notificaciones | `alertas_log` | `/notifications` |
| V18 | Eliminación de cuenta | `solicitudes_eliminacion_cuenta` | `/me` |

---

## 16. Criterios de aceptación

1. Un usuario nuevo recibe 16 categorías, 5 cuentas, perfil, preferencias, progreso y mascota.
2. Un usuario no puede usar una categoría, cuenta o meta de otro usuario.
3. Un mensaje con el mismo `message_id` no crea transacciones duplicadas.
4. Un mensaje puede crear dos o más transacciones.
5. Una transacción pendiente no afecta balance, puntos, metas ni salud.
6. Una transacción anulada no afecta cálculos.
7. Restaurar una transacción recupera sus efectos.
8. El cierre de un día es idempotente.
9. Editar un día cerrado reconstruye salud y cierres posteriores.
10. La salud siempre está entre 0 y 100.
11. El ánimo corresponde a los umbrales definidos.
12. Los puntos se otorgan una sola vez por transacción.
13. La racha se rompe con un día sin movimientos.
14. Una meta se marca atrasada según el avance esperado.
15. Solo existe una cuenta por defecto.
16. Las tarjetas no muestran saldo.
17. Las categorías del sistema no se renombran.
18. Las cuentas ocultas siguen sumando a los totales.
19. El dispositivo se desvincula y vuelve a fábrica al eliminar la cuenta.
20. La telemetría duplicada no se procesa dos veces.
21. Las notificaciones se pueden leer, marcar y eliminar.
22. El índice de bienestar devuelve cobertura cuando faltan datos.
23. El esquema se aplica en una base vacía sin errores.
24. El esquema se puede validar con `PRAGMA foreign_key_check`.
25. Una notificación de dispositivo nace en `pendiente` sin fechas de entrega ni lectura.
26. El CHECK de `dispositivos_notificaciones` impide estados incoherentes con `entregado_en` y `leido_en`.
27. Un mismo mensaje no genera dos notificaciones `movimiento_registrado` para el mismo dispositivo.
28. Un WAV de 16 kHz mono entre 0.5 y 40 s se transcribe y crea el mensaje con sus transacciones pendientes.
29. Un WAV con otra frecuencia, en estéreo, con menos de 0.5 s o con más de 40 s se rechaza con `AUDIO_INVALIDO`.
30. Un `message_id` repetido con audio devuelve el mensaje guardado y no vuelve a llamar al proveedor.
31. Si el proveedor de transcripción falla no queda ningún mensaje ni transacción creados.
32. La llamada al proveedor queda auditada en `interacciones_ia` con modelo, latencia y tokens.
33. El audio no queda almacenado en la base ni en el disco.
34. El texto transcrito en palabras (`catorce mil`) y en cifras (`14.000`) producen el mismo monto, incluidos los millones.

---

## 17. Decisiones

| Tema | Estado | Propuesta |
|---|---|---|
| Proveedor de IA/STT | Decidido | Gemini Flash (API de Google) con cadena de modelos de respaldo y caída automática a faster-whisper local; interpretación de montos y categorías por reglas locales en `backend/nlp.py`. |
| Duración máxima del audio | Decidido | 40 segundos, validada por el servidor. |
| Transmisión del audio | Decidido | Wi-Fi por HTTP multipart. BLE queda solo para configuración inicial. |
| SLM local | Decidido | Se ejecuta en el PC o servidor del backend, nunca en la ESP32. Queda para el agente consejero. |
| Modelo local en el dispositivo | Descartado | La ESP32-S3 no puede ejecutar un SLM: 512 KB de SRAM y 16 MB de flash. |
| Guardado automático vs confirmación | Decidido | Se mantiene la confirmación humana: la IA propone y el usuario confirma antes de afectar el dinero. |
| Notificación al dispositivo | Decidido | Polling HTTP cada 3–5 segundos con `after_id` y acuse explícito. |
| Persistencia de notificaciones | Decidido | Tabla `dispositivos_notificaciones` con estados `pendiente`, `entregada` y `leida`. |
| Fórmula de bienestar | Propuesta | Seis componentes ponderados; validar con producto. |
| Reglas de salud | Propuesta | Ajustar topes después de pruebas con usuarios. |
| Notificaciones push | Futuro | Requiere servicio externo. |
| Pantallas V12-V16 | Futuro | No están en el Figma entregado. |
| Etapa 3 | Futuro | Seguimiento permanente después del MVP. |
| Integración BLE real | Futuro | El MVP usa Wi-Fi y simulador. |

---

## 18. Operación

### 18.1 Instalar dependencias y configurar la IA

```powershell
py -3 -m pip install -r requirements.txt
py -3 tools/configurar_api_key.py
```

La API key se guarda **fuera del repositorio**, en `%USERPROFILE%\.finagotchi\gemini.env`, para que ningún `git clean -xdf` ni una reinstalación la borren. El asistente también la verifica contra la API real antes de terminar.

El backend busca la configuración en este orden:

| Prioridad | Origen | Nota |
|---|---|---|
| 1 | Variable de entorno del sistema | `GEMINI_API_KEY` gana sobre todo lo demás. |
| 2 | `backend/.env` | Ignorado por git, se puede borrar. |
| 3 | `.env` en la raíz | Ignorado por git, se puede borrar. |
| 4 | `%USERPROFILE%/.finagotchi/gemini.env` | Fuera del repo, a salvo de `git clean`. |

`backend/.env.example` **sí está versionado**: es una plantilla y nunca debe llevar una clave real. `tests/test_seguridad.py` falla si encuentra una clave con formato de Google en cualquier archivo del repositorio.

Diagnóstico del entorno:

```powershell
py -3 tools/verificar_entorno.py
```

Revisa Python y las dependencias, el esquema de la base, el origen de la clave, si la API responde y si hay micrófono disponible. Devuelve 1 si hay algo que arreglar.

### 18.2 Inicializar una base nueva

```powershell
py -3 database/init_db.py
```

### 18.3 Reiniciar la base desde cero

No se migran datos legacy. Para descartar el dataset anterior y crear una base limpia:

```powershell
Remove-Item finagotchi.db, finagotchi.db-wal, finagotchi.db-shm -Force -ErrorAction SilentlyContinue
py -3 database/init_db.py
```

La base nueva contiene solo catálogos y estructuras; no crea usuarios, transacciones ni mascotas hasta que se registre el primer usuario.

### 18.4 Validación

```powershell
py -3 -m unittest discover -s tests -v
py -3 -m compileall -q backend simulator tests
```

### 18.5 Prueba real del flujo de voz

Con el backend levantado (`py -3 backend/server.py`) y un WAV de 16 kHz mono:

```powershell
py -3 tools/probar_flujo_voz.py ruta\al\audio.wav
```

El script registra un usuario de prueba, vincula un dispositivo, envía el audio, confirma el mensaje, consulta y acusa las notificaciones, y muestra la auditoría de `interacciones_ia`.

### 18.6 Dataset de evaluación de audio

El manifiesto `datasets/eval_audio/manifest.csv` define 30 casos de prueba con su verdad conocida:

| Columna | Descripción |
|---|---|
| `id` | Identificador del clip. |
| `archivo` | WAV dentro de `datasets/eval_audio/audio`. |
| `transcripcion` | Texto esperado. |
| `intent` | `registrar`, `consulta_estado`, `cerrar_dia` o `requiere_aclaracion`. |
| `monto_esperado` | Monto esperado en pesos enteros. |
| `categoria_esperada` | Categoría esperada. |
| `cuenta_esperada` | Cuenta esperada. |
| `duracion_s` | Se completa al grabar. |
| `ruido` | `bajo`, `medio` o `alto`. |
| `notas` | Observaciones del caso. |

Los casos cubren montos en cifras (`14.000`) y en palabras (`catorce mil`), millones (`1.5 millones`), ingresos, gastos y ahorro, consultas, frases sin monto, correcciones, ruido y variantes de la frase de cierre.

Herramientas:

```powershell
py -3 tools/grabar_dataset.py      # graba los clips pendientes con el micrófono
py -3 tools/evaluar_dataset.py     # transcribe y genera datasets/eval_audio/reporte.json
```

Métricas del reporte: WER promedio, exactitud de montos, exactitud de intención, latencia promedio y máxima, y tokens consumidos.

| Objetivo | Umbral |
|---|---|
| WER promedio | menor a 15 % |
| Montos exactos | al menos 90 % |
| Latencia | menor a 5 segundos en el 95 % de los casos |

La capa gratuita de Gemini limita a 3 peticiones por minuto y por modelo, así que la evaluación pausa entre clips y reintenta cuando recibe `429`.

### 18.7 Respaldo

- Copiar `finagotchi.db` con el servicio detenido.
- Copiar también `finagotchi.db-wal` y `finagotchi.db-shm` si existen.
- Verificar el respaldo con `PRAGMA integrity_check`.
