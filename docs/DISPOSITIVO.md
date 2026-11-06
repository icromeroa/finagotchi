# FinaGotchi · Brief de diseño del dispositivo

Versión: 1.1  
Estado: **EN STAND-BY hasta recibir el diseño de la diseñadora**  
Documento base: `docs/ESPECIFICACIONES.md`  
Aplicación de referencia: Figma de FinaGotchi  
Hardware objetivo: ESP32-S3 SuperMini, pantalla TFT 240x320 de 7 pines sin BLK, 3 botones, micrófono I2S, amplificador I2S y batería 18650

Cambios de la v1.1: la voz es la entrada principal del dispositivo; la
confirmación se responde con frases naturales; el simulador implementa y
documenta D14-D17 (plan de ahorro y respuesta de Nancy, error y prueba de
micrófono).

---

## 1. Objetivo del dispositivo

FinaGotchi debe funcionar como un compañero físico de la aplicación, no como una copia completa de ella. El dispositivo sirve para:

1. Registrar ingresos, gastos y ahorros por voz.
2. Confirmar o cancelar lo que Nancy entendió, hablando.
3. Mostrar el estado emocional de Nancy y el avance del día.
4. Consultar un resumen breve, por voz o texto.
5. Guardar mensajes cuando no haya conexión.
6. Avisar sobre batería baja, errores y dispositivos sin vincular.

**La voz es la entrada principal.** El menú del simulador es informativo e informa a la persona de qué puede decir; no es el camino normal de uso. Quien no pueda hablar dispone de `[T] Escribir`: el texto sigue exactamente el mismo flujo conversacional que la voz. El simulador también ofrece `[A] Probar micrófono`, que reporta el pico y el RMS de la señal para explicar si el problema es del dispositivo o del entorno.

La edición detallada, las metas, las cuentas, las categorías, el perfil y las métricas completas se quedan en la aplicación web. Las operaciones habituales que el dispositivo ya ejecuta por voz confirmando con el usuario son: registrar y corregir movimientos; eliminar movimientos; crear o eliminar metas; crear cuentas y categorías; ajustar el presupuesto diario y el ingreso mensual declarado. El dispositivo debe ser rápido, claro y usable con tres botones.

---

## 2. Coherencia con la aplicación

El dispositivo debe usar el mismo lenguaje visual y verbal de la app. No se debe crear una identidad nueva.

### 2.1 Elementos que deben coincidir

- Nancy y sus expresiones.
- Los cuatro estados oficiales: `FELIZ`, `PREOCUPADO`, `TRISTE`, `CRITICO`.
- La paleta de color de la app.
- La tipografía o una variante compatible con pantalla pequeña.
- Los iconos y el estilo de ilustración.
- Los textos en español, con tratamiento de “tú”.
- El formato de dinero colombiano: `$42.000`.
- El concepto de cupo diario, no “saldo disponible” cuando se trate de presupuesto.
- La diferencia entre gasto, ingreso y ahorro.
- El tono de Nancy: cercano, breve, sin regaños y sin tecnicismos.

### 2.2 Pantallas de la app que sirven de referencia

| Pantalla del dispositivo | Referencia en la app |
|---|---|
| D01 Arranque | V01.1 Splash con Nancy |
| D02 Sin vincular | V03.1 Elegir método, V03.4 Resultado |
| D03 Reposo | V06.1 Nancy y estado del día |
| D04 Grabando | V07.1 Voz |
| D05 Procesando | V07.1 Voz, V08.1 Movimientos cargando |
| D06 Confirmar | V07.2 Confirmar o editar datos |
| D07 Resultado | V06.1 Nancy y estado del día |
| D08 Consulta | V11.1 Resumen de flujo de caja, V09.1 Diario |
| D09 Cierre del día | V09.1 Diario |
| D10 Sin conexión | V03.4 Conexión perdida, V08.1 Movimientos |
| D11 No entendí | V07.4 No entendí |
| D12 Bloqueado | V18 Eliminar perfil, desvinculación |
| D14 Plan de ahorro | V16.1 Plan de metas |
| D15 Respuesta de Nancy | V07.2 Confirmar o editar datos |
| D16 Error explicado | V07.4 No entendí |
| D17 Prueba de micrófono | V07.1 Voz |

---

## 3. Restricciones físicas y técnicas

### 3.1 Pantalla

- Tamaño físico: 2.4 pulgadas.
- Resolución: 240 x 320 píxeles.
- Orientación: vertical.
- Color: 16 bits, RGB565.
- Conexión: SPI.
- Sin táctil.
- Modelo declarado: TFT 240x320 SPI GMT024-10 v2.1.
- Módulo de 7 pines: `VCC`, `GND`, `CS`, `RST`, `DC`, `MOSI` y `SCLK`.
- Sin pin `BLK`/`BL`: el backlight no se controla por GPIO.
- **Pendiente:** confirmar el controlador real de la pantalla, el orden físico de los 7 pines y su secuencia de inicialización.

### 3.2 Procesador

- ESP32-S3 SuperMini.
- Doble núcleo Xtensa LX7 hasta 240 MHz.
- 512 KB de SRAM.
- 16 MB de flash externa.
- La ficha declarada no incluye PSRAM; no asumir PSRAM hasta verificar la variante física.
- Wi-Fi 2.4 GHz y Bluetooth Low Energy 5.
- 11 GPIO, 4 ADC, 2 UART, 1 SPI y 1 I2C.
- USB-C de 5 V y lógica de 3.3 V.
- Sin sistema operativo visual; la interfaz se dibuja directamente sobre la pantalla.

### 3.3 Controles

- Tres botones pulsadores físicos.
- Sin teclado, sin touch y sin rueda.
- Los botones deben tener etiqueta o icono visible junto a su función en pantalla.
- Un botón puede despertar el dispositivo de suspensión ligera.

### 3.4 Audio

- Micrófono digital I2S. El componente declarado es `INPM441`; se asume que corresponde a **INMP441**.
- Amplificador I2S. El componente declarado es `MAX9835`; se asume que corresponde a **MAX98357A**.
- Altavoz de 80 ohmios y 0.5 W.
- El dispositivo captura voz y reproduce avisos cortos.
- La transcripción y la clasificación de categoría las hace la IA del backend, no el dispositivo.
- El dispositivo solo envía audio corto, recibe el resultado y muestra la notificación de “registro guardado”.
- No se almacena audio de forma permanente; se conservan transcripción, categoría y metadatos.
- El bus I2S se comparte entre micrófono y amplificador para no superar los 11 GPIO. Validar que el ESP32-S3 pueda usar relojes compartidos en recepción y reproducción.

### 3.5 Energía

- Batería de litio 18650.
- Módulo BMS y cargador.
- Portapila.
- Switch físico de encendido y apagado.
- Regulador de 3.3 V para ESP32, pantalla, micrófono y botones.
- Medición de batería por ADC con divisor de voltaje.
- **Pendiente:** confirmar el modelo exacto del BMS, cargador y regulador.

### 3.6 Almacenamiento

- 16 MB de flash externa permiten recursos visuales, frases y una partición OTA.
- 512 KB de SRAM son el límite real; no hay PSRAM confirmada.
- Usar buffers parciales de pantalla, no un framebuffer completo de 240x320x2 bytes.
- El audio se envía por bloques; no se conserva completo en RAM.
- Los recursos visuales y las frases pregrabadas deben ser livianos.
- La cola offline debe tener un límite definido.
- **Decisión pendiente:** incluir o no actualización OTA. La flash de 16 MB ya permite evaluarla, pero el MVP puede lanzarse sin OTA.

---

## 4. Pinout propuesto

Con 11 GPIO no caben 15 señales si se conectan por separado. Para que el diseño cierre se aplican tres reducciones:

1. Relojes I2S compartidos entre micrófono y amplificador.
2. `TFT_RST` conectado a `EN` de la placa, no a un GPIO.
3. Los tres botones comparten una escalera resistiva en un solo ADC.

El pinout usa 10 GPIO y deja `GPIO3` libre. Debe validarse contra la placa física y el orden real de los 7 pines de la TFT.

### 4.1 Pantalla TFT de 7 pines

| Señal | GPIO propuesto | Dirección | Nota |
|---|---:|---|---|
| TFT_SCLK | GPIO7 | Salida | Reloj SPI |
| TFT_MOSI | GPIO6 | Salida | Datos SPI |
| TFT_CS | GPIO5 | Salida | Chip select |
| TFT_DC | GPIO4 | Salida | Data/Command |
| TFT_RST | GPIO8 | Reset | Reset |
| TFT_VCC | 3V3 | Alimentación | Confirmar que el módulo acepte 3.3 V |
| TFT_GND | GND | Tierra | Común con el resto del sistema |
| TFT_BL | — | — | No existe pin BLK/BL; el backlight queda fijo |

Reglas:

- No hay control de brillo por PWM.
- Si el módulo expone un pad `LED`/`BL` interno, conectarlo a 3V3 mediante la resistencia que indique el fabricante.
- Si `TFT_RST` no puede soldarse a `EN`, usar un reset RC de encendido o liberar un GPIO reduciendo otra función.

Reglas:

- Validar que el ESP32-S3 pueda compartir BCLK y WS entre recepción y reproducción.
- Si el driver no permite relojes compartidos, usar el bus en modo half-duplex: primero grabar y luego reproducir.
- Mantener el amplificador separado de la alimentación sensible del micrófono.

### o en su defecto:

### 4.2 Micrófono INMP441

| Señal | GPIO propuesto | Dirección | Nota |
|---|---:|---|---|
| MIC_SCK | GPIO3 | Salida | Reloj I2S |
| MIC_WS | GPIO2 | Salida | Word select |
| MIC_SD | GPIO9 | Entrada | Datos del micrófono |
| MIC_L/R | GND | — | Canal izquierdo |
| MIC_VDD | 3V3 | Alimentación | Con condensador de desacople |
| MIC_GND | GND | Tierra | Común |

### 4.3 Amplificador MAX98357A

| Señal | GPIO propuesto | Dirección | Nota |
|---|---:|---|---|
| AMP_BCLK | GPIO11 | Salida | Reloj I2S |
| AMP_LRC | GPIO12 | Salida | Word select |
| AMP_DIN | GPIO17 | Salida | Datos hacia el amplificador |
| AMP_VIN | VBAT o 5V | Alimentación | Verificar límite del módulo; no alimentar desde un GPIO |
| AMP_GND | GND | Tierra | Común |
| SPK+ / SPK- | Altavoz | Salida | Altavoz de 80 ohmios |
| GAIN / SD | Según módulo | Configuración | Definir ganancia y canal |

### 4.4 Botones

| Señal | GPIO propuesto | Modo | Nota |
|---|---:|---|---|
| BTN_BACK | GPIO1 | Entrada pull-up | Activo en bajo |
| BTN_OK | GPIO21 | Entrada pull-up | Activo en bajo |
| BTN_PTT | GPIO47 | Entrada pull-up | Mantener para hablar; activo en bajo |
| GND | GND | Tierra | Un terminal del pulsador a GND |

Si GPIO47 no está disponible en la placa, usar GPIO2 como alternativa y actualizar este documento. Evitar GPIO0, GPIO45 y GPIO46 porque son pines de arranque.

### 4.5 Batería y alimentación

| Señal | GPIO propuesto | Nota |
|---|---:|---|
| BAT_ADC | GPIO1 | ADC1. Divisor 100k/100k y condensador de 100 nF a GND |
| VBAT | — | Salida protegida de la batería, 3.0 a 4.2 V |
| 3V3 | — | Regulador para ESP32, TFT, micrófono y lógica |
| GND | — | Tierra común |

Cadena de alimentación propuesta:

```text
USB-C 5V -> cargador/BMS -> batería 18650 -> switch -> VBAT
VBAT -> regulador 3V3 -> ESP32-S3, TFT, INMP441, botones
VBAT -> VIN del MAX98357A, si el módulo lo permite
GND común en todo el sistema
```

Reglas:

- No conectar la batería directamente a un GPIO.
- No medir la batería sin divisor de voltaje.
- Verificar la corriente pico del amplificador y del backlight.
- Mantener el amplificador separado de la alimentación sensible del micrófono.
- Agregar condensadores de desacople cerca de la pantalla, el micrófono y el amplificador.
- El switch debe cortar la alimentación de potencia, no solo una señal lógica.

### 4.6 Pines reservados y precauciones

- GPIO0, GPIO45 y GPIO46: pines de arranque; no usar para botones ni pantalla.
- GPIO19 y GPIO20: pueden estar conectados al USB nativo; evitar si la placa los usa para programación.
- GPIO43 y GPIO44: pueden ser UART de consola; evitar si se necesita depuración serial.
- Confirmar que la placa exponga GPIO47.
- Confirmar que la pantalla y el amplificador funcionen a 3.3 V o prever nivel lógico adecuado.

---

## 5. Sistema visual para 240x320

### 5.1 Lienzo y zonas

- Lienzo: 240 x 320 px.
- Margen seguro: 12 px.
- Barra de estado superior: 28 px.
- Área de contenido: 240 x 252 px.
- Pie de ayuda de botones: 40 px.
- Contenido útil: 216 x 252 px dentro de márgenes.

### 5.2 Tokens que debe entregar la diseñadora

Tomar los valores desde el Figma de la app y entregar una tabla con:

- Color de fondo principal.
- Color de superficie o tarjeta.
- Color de texto principal.
- Color de texto secundario.
- Color primario de marca.
- Color de éxito.
- Color de advertencia.
- Color de error.
- Color de cada ánimo: feliz, preocupado, triste, crítico.
- Color de batería y señal.
- Tipografía principal y alternativa.
- Tamaños: título, subtítulo, cuerpo, número grande, texto de botón.
- Radios de borde.
- Espaciado base.
- Estilo de iconos: línea, relleno, grosor.
- Estilo de ilustración de Nancy.

### 5.3 Tipografía

- Usar la misma familia de la app si tiene buen renderizado a tamaño pequeño.
- Si no, usar una variante compatible y aprobarla con el equipo.
- Tamaños mínimos recomendados:
  - Título: 20 a 24 px.
  - Texto principal: 16 px.
  - Texto secundario: 14 px.
  - Números de dinero o salud: 28 a 34 px.
  - Texto de ayuda de botones: 12 a 14 px.
- No usar textos menores a 12 px.
- Evitar párrafos largos.

### 5.4 Iconografía

- Iconos simples, de alto contraste, con trazo grueso.
- Tamaño base: 24 x 24 px.
- Tamaño pequeño: 16 x 16 px.
- No usar iconos que dependan solo del color.
- Mantener el mismo estilo de la app.

### 5.5 Nancy

- Nancy debe ser el foco visual de la pantalla de reposo.
- Expresiones mínimas:
  - Feliz.
  - Preocupada.
  - Triste.
  - Crítica.
  - Neutral o pensando.
- Tamaño recomendado: 120 x 120 px a 140 x 140 px.
- Debe existir una versión estática para cada ánimo y una animación breve de reposo.
- No usar animaciones pesadas ni videos.
- Mantener los rasgos y colores de la Nancy de la app.

---

## 6. Estructura general de pantalla

Todas las pantallas deben respetar esta estructura, salvo splash y pairing:

```text
+--------------------------------+
| Estado: señal, batería, hora   |  28 px
+--------------------------------+
|                                |
| Contenido principal            |
| Nancy / mensaje / lista        | 252 px
|                                |
+--------------------------------+
| [Atrás]      [OK]      [Hablar]|  40 px
+--------------------------------+
```

- La barra de estado no debe tapar contenido.
- El pie debe mostrar la función real de cada botón.
- Los botones deben tener una etiqueta corta: `Atrás`, `OK`, `Hablar`, `Cancelar`, `Reintentar`.
- No mostrar más de tres acciones a la vez.

---

## 7. Pantallas que debe diseñar la diseñadora

### D01 · Arranque

**Objetivo:** mostrar que el dispositivo está encendiendo.

**Contenido:**
- Logo de FinaGotchi.
- Nancy en estado neutral.
- Texto: “FinaGotchi”.
- Indicador de carga o arranque.
- Versión de firmware discreta, opcional.

**Duración:** 1 a 2 segundos.

**Botones:** ninguno.

---

### D02 · Dispositivo sin vincular

**Objetivo:** permitir que el usuario vincule el dispositivo desde la app.

**Contenido:**
- Título: “Vincula tu FinaGotchi”.
- Instrucción: “Abre la app y escanea este código”.
- Espacio para QR de 140 x 140 px o código PIN de 6 dígitos.
- Código PIN visible y legible a distancia.
- Texto de expiración: “Vence en 09:59”.
- Estado de error si el código vence.
- Botón de reintento si aplica.

**Botones:**
- `Atrás`: volver al estado de espera.
- `OK`: generar un código nuevo.
- `Hablar`: deshabilitado.

**Estados:**
- Generando código.
- Código listo.
- Código vencido.
- Vinculación exitosa.
- Error de vinculación.

---

### D03 · Reposo

**Objetivo:** mostrar el estado principal de Nancy y del día.

**Contenido:**
- Nancy según el ánimo actual.
- Nombre: “Nancy”.
- Ánimo oficial: `FELIZ`, `PREOCUPADO`, `TRISTE` o `CRITICO`.
- Barra o indicador de salud de 0 a 100.
- Cupo del día: “Te quedan $X de $Y”.
- Gasto de hoy o balance del día.
- Puntos o racha, si aportan claridad.
- Estado de conexión.
- Batería.
- Ayuda: “Mantén para hablar”.

**Botones:**
- `Atrás`: abrir ajustes mínimos o volver al reposo.
- `OK`: consultar estado.
- `Hablar`: mantener para grabar.

**Estados:**
- Reposo normal.
- Sin conexión.
- Mensajes pendientes.
- Batería baja.
- Batería crítica.
- Dispositivo bloqueado.

---

### D04 · Grabando

**Objetivo:** indicar que el dispositivo está escuchando.

**Contenido:**
- Título: “Te escucho”.
- Indicador de grabación animado.
- Forma de onda o barras de audio.
- Tiempo transcurrido: “00:03”.
- Instrucción: “Suelta para enviar”.
- Cancelación visible: “Atrás para cancelar”.

**Botones:**
- `Atrás`: cancelar la grabación.
- `OK`: deshabilitado.
- `Hablar`: mantener presionado; al soltar se envía.

**Estados:**
- Grabando.
- Micrófono sin señal.
- Tiempo máximo alcanzado.

---

### D05 · Procesando

**Objetivo:** indicar que el audio se está transcribiendo o interpretando.

**Contenido:**
- Nancy pensando.
- Texto: “Entendiendo tu mensaje”.
- Indicador de progreso no determinado.
- No mostrar un porcentaje si no es real.

**Botones:**
- `Atrás`: cancelar y volver al reposo.
- `OK`: deshabilitado.
- `Hablar`: deshabilitado.

---

### D06 · Confirmar registro

**Objetivo:** confirmar una o varias transacciones antes de guardarlas.

**Contenido:**
- Título: “¿Registro esto?”.
- Lista de una a tres transacciones.
- Cada ítem debe mostrar:
  - Tipo: gasto, ingreso o ahorro.
  - Monto: `$42.000`.
  - Categoría.
  - Cuenta, si aplica.
  - Concepto corto.
- Si hay más de tres ítems, mostrar paginación “1 de 2”.
- Si algún dato falta, indicar “Falta un dato”.
- Texto de ayuda: “Di sí, está bien, ok o confirmo”.

**Botones:**
- `Atrás`: cancelar y volver.
- `OK`: confirmar todas. Solo es la ruta del botón físico; la ruta principal es responder por voz.
- `Hablar`: deshabilitado.

**Estados:**
- Una transacción.
- Varias transacciones.
- Dato faltante.
- Error al confirmar.
- Confirmación exitosa.

**Nota de decisión:** se mantiene la confirmación humana. La IA no guarda automáticamente; D06 se conserva y D07 muestra “Registro guardado” solo cuando el backend confirma la persistencia. La confirmación se acepta con frases naturales: “sí”, “ok”, “correcto”, “está bien”, “confirmo”, “dale”. Para descartar se usa “no”, “cancela”, “olvídalo” o “descarta”. Para corregir, basta con decir el dato nuevo ("cambia el monto a 25 mil") y Nancy muestra la propuesta corregida antes de guardar.

Una frase larga solo confirma si empieza por una palabra afirmativa corta; “gasté 20 mil” nunca se toma como confirmación aunque haya una acción pendiente.

---

### D07 · Resultado

**Objetivo:** mostrar el efecto del registro.

**Contenido:**
- Nancy contenta o con el ánimo correspondiente.
- Texto: “Listo”.
- Puntos ganados: “+1 punto” o “+N puntos”.
- Salud proyectada, si cambió.
- Cupo restante del día.
- Racha actual, si aplica.
- Texto de cierre: “Mantén para hablar” o “OK para volver”.

**Botones:**
- `Atrás`: volver al reposo.
- `OK`: volver al reposo.
- `Hablar`: mantener para grabar otro mensaje.

---

### D08 · Consulta de estado

**Objetivo:** responder “¿cómo voy?” sin entrar a la app.

**Contenido:**
- Título: “Así vas hoy”.
- Ingresos del día.
- Gastos del día.
- Ahorro del día.
- Balance neto.
- Cupo restante.
- Salud y ánimo.
- Mensaje breve de Nancy.

**Botones:**
- `Atrás`: volver.
- `OK`: actualizar.
- `Hablar`: mantener para otra consulta.

---

### D09 · Cierre del día

**Objetivo:** mostrar el resumen cuando se cierra la jornada.

**Contenido:**
- Título: “Cerramos el día”.
- Total de ingresos.
- Total de gastos.
- Total de ahorro.
- Balance neto.
- Salud final.
- Ánimo final.
- Mensaje breve: “Mañana seguimos”.

**Botones:**
- `Atrás`: volver.
- `OK`: confirmar cierre.
- `Hablar`: deshabilitado.

**Estados:**
- Cierre exitoso.
- Cierre pendiente.
- Error de conexión.

---

### D10 · Sin conexión y cola

**Objetivo:** informar que el mensaje se guardó localmente.

**Contenido:**
- Icono de Wi-Fi tachado.
- Título: “Sin conexión”.
- Texto: “Guardé tu mensaje”.
- Número de mensajes pendientes.
- Texto: “Se enviarán cuando vuelva la conexión”.
- Opción de reintentar.

**Botones:**
- `Atrás`: volver.
- `OK`: reintentar.
- `Hablar`: permitir grabar y encolar.

**Estados:**
- Sin conexión.
- Reintentando.
- Cola llena.
- Sincronización exitosa.

---

### D11 · No entendí

**Objetivo:** permitir repetir la captura sin frustración.

**Contenido:**
- Nancy preocupada o neutral.
- Título: “No entendí”.
- Texto: “Intenta decir el monto y el tipo de movimiento”.
- Ejemplo: “Gasté 10.000 en almuerzo”.
- Opción de cancelar y usar la app.

**Botones:**
- `Atrás`: cancelar.
- `OK`: reintentar.
- `Hablar`: mantener para grabar de nuevo.

---

### D12 · Bloqueado o desvinculado

**Objetivo:** informar que el dispositivo ya no tiene acceso.

**Contenido:**
- Título: “Dispositivo desvinculado”.
- Texto: “Vuelve a vincularlo desde la app”.
- Código de error corto, si ayuda al soporte.
- Sin datos financieros visibles.

**Botones:**
- `Atrás`: volver al inicio.
- `OK`: reintentar vinculación.
- `Hablar`: deshabilitado.

---

### D13 · Avisos superpuestos

Diseñar como capas, no como pantallas completas:

- Batería baja: “Batería baja”.
- Batería crítica: “Conecta el cargador”.
- Sin conexión.
- Mensaje en cola.
- Error de guardado.
- Vinculación exitosa.

Deben desaparecer solas o con `OK`.

---

### D14 · Plan de ahorro

**Objetivo:** mostrar el plan de metas calculado con programación lineal, sin escribir nada.

**Contenido:**
- Título: “Plan de ahorro”.
- Capacidad mensual del primer mes.
- Número de metas y cumplimiento ponderado.
- Hasta 4 metas con porcentaje de cumplimiento y aporte mensual recomendado.
- Diagnóstico cuando la capacidad no alcanza: a qué meta asigna primero y cuánto falta.
- Si no hay metas: “Aún no tienes metas.” y el mensaje de cómo crear una por voz.

**Botones:**
- `Atrás`: volver al reposo.
- `OK`: actualizar el plan.
- `Hablar`: mantener para preguntar por el plan.

**Nota:** el plan solo propone. La persona confirma cualquier cambio por voz; el dispositivo nunca mueve dinero.

---

### D15 · Respuesta de Nancy

**Objetivo:** mostrar lo que Nancy dijo, tanto para voz como para texto.

**Contenido:**
- Tira superior: “NANCY dice:”.
- El mensaje de Nancy en máximo 7 líneas, con salto automático de línea.
- Si la respuesta describe un movimiento pendiente o una meta candidata, muestra el monto y el estado conversacional (`confirmando_movimiento`, `recopilando_meta`, `confirmando_meta`, `confirmando_accion`, `inactiva`).
- Si la respuesta pide confirmación, muestra “Di sí, está bien, ok o no”.
- Si la respuesta ejecuta una acción, muestra “Estado: inactiva”.

**Botones:**
- `Atrás`: volver al reposo.
- `OK`: repetir o volver al reposo.
- `Hablar`: mantener para seguir hablando.

**Nota:** D15 es la pantalla de información principal del dispositivo voz-primero.

---

### D16 · Error explicado

**Objetivo:** cuando algo falla, explicar el motivo en una frase corta y proponer la alternativa.

**Contenido:**
- Título con el código breve del error (`STT_SIN_TEXTO`, `STT_NO_DISPONIBLE`, “No escuché tu voz”).
- Mensaje explicado (`pico 1`, “El micrófono casi no recibió señal”).
- Detalle técnico opcional, máximo 3 líneas.
- Pie: “[T] Escribir o [H] Hablar”.

**Botones:**
- `Atrás`: volver al reposo.
- `OK`: reintentar.
- `Hablar`: grabar de nuevo.

---

### D17 · Prueba de micrófono

**Objetivo:** comprobar si el micrófono llega señal antes de culpar al STT.

**Contenido:**
- Título: “Prueba de micrófono”.
- Dispositivo elegido, pico y RMS medidos.
- “Señal detectada.” o “Casi no hay señal.”.
- Si no hay señal: revisar la entrada de sonido en Windows, subir el volumen y cambiar el índice en `input_device` de `simulator/config.json`.

**Botones:**
- `Atrás`: volver al reposo.
- `OK`: repetir la prueba.
- `Hablar`: grabar una frase de prueba.

---

## 8. Matriz de botones

| Pantalla | Atrás | OK | Hablar |
|---|---|---|---|
| D01 Arranque | — | — | — |
| D02 Sin vincular | Volver | Nuevo código | Deshabilitado |
| D03 Reposo | Ajustes | Consultar | Grabar |
| D04 Grabando | Cancelar | Deshabilitado | Enviar al soltar |
| D05 Procesando | Cancelar | Deshabilitado | Deshabilitado |
| D06 Confirmar | Cancelar | Confirmar | Deshabilitado |
| D07 Resultado | Volver | Volver | Grabar |
| D08 Consulta | Volver | Actualizar | Nueva consulta |
| D09 Cierre | Volver | Confirmar | Deshabilitado |
| D10 Sin conexión | Volver | Reintentar | Grabar y encolar |
| D11 No entendí | Cancelar | Reintentar | Grabar |
| D12 Bloqueado | Volver | Reintentar | Deshabilitado |
| D14 Plan de ahorro | Volver | Actualizar plan | Preguntar por el plan |
| D15 Respuesta de Nancy | Volver | Repetir | Seguir hablando |
| D16 Error explicado | Volver | Reintentar | Grabar de nuevo |
| D17 Prueba de micrófono | Volver | Repetir prueba | Frase de prueba |

Reglas:

- Mantener presionado `Hablar` inicia la grabación.
- Soltar `Hablar` termina la grabación y envía.
- Una pulsación corta de `Hablar` en reposo puede abrir la ayuda de voz, si el producto lo decide.
- `OK` nunca debe ejecutar una acción destructiva.
- `Atrás` nunca debe borrar datos sin confirmación.
- Las acciones destructivas se hacen en la app.

---

## 9. Audio y feedback

### 9.1 Sonidos

Diseñar o seleccionar:

- Inicio de grabación.
- Fin de grabación.
- Envío exitoso.
- Error.
- Sin conexión.
- Batería baja.
- Confirmación.
- Cancelación.

Los sonidos deben ser cortos, suaves y no invasivos. No usar alarmas fuertes.

### 9.2 Frases pregrabadas

Máximo 2 segundos por frase. Deben existir al menos:

- “Te escucho”.
- “Listo”.
- “No entendí”.
- “Sin conexión”.
- “Guardé tu mensaje”.
- “Batería baja”.
- “Conecta el cargador”.
- “Dispositivo desvinculado”.

### 9.3 Transcripción y notificación

La transcripción y la categoría las procesa la IA del backend. La pantalla no muestra el texto completo, solo el estado:

- “Entendiendo”.
- “No entendí”.
- “Falta el monto”.
- “Registro guardado”, cuando el backend confirme la persistencia.
- “¿Confirmas?”.

El dispositivo no transcribe localmente. Envía el audio, espera la respuesta y muestra la notificación final. La confirmación humana es obligatoria. Las notificaciones de guardado se consultan por polling HTTP cada 3–5 segundos y se acusan con `POST /device/notifications/{id}/ack`.

---

## 10. Movimiento y animación

- La interfaz debe sentirse viva, pero no distraída.
- Animaciones permitidas:
  - Respiración de Nancy.
  - Parpadeo.
  - Onda de audio.
  - Aparición de tarjetas.
  - Cambio de ánimo.
- Duración recomendada: 150 a 300 ms.
- Frecuencia máxima: 10 a 15 fps.
- Evitar animaciones de pantalla completa.
- Evitar destellos rápidos.
- La pantalla no debe parpadear entre estados.

---

## 11. Recursos visuales que debe entregar la diseñadora

### 11.1 Nancy

- 4 expresiones oficiales.
- 1 expresión neutral.
- 1 expresión pensando.
- Animación de reposo.
- Animación de grabación.
- Formato editable y exportación PNG con fondo transparente.
- Tamaños base: 120 x 120 px y 160 x 160 px.

### 11.2 Iconos

- Wi-Fi.
- Sin Wi-Fi.
- Batería llena.
- Batería media.
- Batería baja.
- Batería cargando.
- Micrófono.
- Altavoz.
- Gasto.
- Ingreso.
- Ahorro.
- Meta.
- OK.
- Error.
- Atrás.
- Reloj.
- Puntos.
- Racha.

### 11.3 Ilustraciones y estados

- QR de vinculación.
- PIN de vinculación.
- Pantalla de error.
- Pantalla de sin conexión.
- Pantalla de cola.
- Pantalla de batería baja.
- Fondo o textura de la app, si existe.

### 11.4 Formatos de entrega

- Fuente editable.
- Mockups en 240 x 320 px.
- Exportación 1x, sin escalado.
- Assets PNG transparentes.
- Bitmaps RGB565 si el equipo de firmware los necesita.
- Tabla de colores y tipografías.
- Prototipo navegable con los tres botones.
- Especificaciones de medidas y márgenes.

---

## 12. Contenido y tono

### 12.1 Reglas de texto

- Frases cortas.
- Máximo 2 líneas por mensaje.
- Sin tecnicismos.
- Sin regaños.
- Sin promesas de rendimiento financiero.
- Usar “Nancy” para la mascota.
- Usar “tú”.
- Mostrar dinero como `$42.000`.
- No mostrar montos con decimales.
- No mostrar información financiera sensible en la pantalla de bloqueo.

### 12.2 Textos base

- “Mantén para hablar”.
- “Suelta para enviar”.
- “Te escucho”.
- “Entendiendo tu mensaje”.
- “¿Registro esto?”.
- “Di sí, está bien, ok o confirmo”.
- “Listo”.
- “No entendí”.
- “Intenta decir el monto y el tipo de movimiento”.
- “Entendí un GASTO de $20.000 en Alimentación. ¿Está correcto? Puedes decir sí, ok o corregirlo.”
- “¿Cómo me fue hoy?” / “Balance de esta semana” / “¿Cómo van mis metas?”
- “Quiero crear una meta para comprar unos audífonos.”
- “Lista para crear la meta. Di sí, está bien u ok.”
- “Di no, cancela o olvídalo para descartar.”
- “El micrófono casi no recibió señal; revisa la entrada de sonido.”
- “Sin conexión”.
- “Guardé tu mensaje”.
- “Mensajes pendientes”.
- “Batería baja”.
- “Conecta el cargador”.
- “Vincula tu FinaGotchi”.
- “Abre la app y escanea este código”.
- “Dispositivo desvinculado”.
- “Vuelve a vincularlo desde la app”.

---

## 13. Accesibilidad

- Contraste mínimo 4.5:1 para texto.
- No usar color como único indicador.
- Textos legibles a 30 cm de distancia.
- Iconos acompañados de texto cuando la acción no sea obvia.
- No usar animaciones que puedan causar molestia.
- No usar más de tres acciones por pantalla.
- Mantener áreas de toque y botones físicos bien etiquetados.
- El estado de batería debe ser visible sin entrar a menús.
- El estado de conexión debe ser visible sin entrar a menús.

---

## 14. Entregables para el equipo de firmware

La diseñadora debe entregar:

1. Mockups finales de D01 a D17 en 240 x 320 px.
2. Prototipo navegable de los flujos principales.
3. Assets de Nancy e iconos.
4. Tabla de colores, tipografías, tamaños y márgenes.
5. Especificación de animaciones y transiciones.
6. Especificación de sonidos y frases.
7. Guía de estados: normal, vacío, cargando, error, sin conexión, batería baja y bloqueado.
8. Lista de assets con nombre, tamaño y uso.
9. Revisión de que el diseño cabe en 16 MB de flash externa y 512 KB de SRAM, sin PSRAM confirmada.

---

## 15. Criterios de aceptación del diseño

El diseño se considera listo cuando:

1. Todas las pantallas caben en 240 x 320 px sin cortes.
2. Cada pantalla tiene una acción clara para los tres botones.
3. Nancy se reconoce como la misma de la app.
4. Los cuatro ánimos son visualmente distintos.
5. El usuario entiende qué hacer sin leer un manual.
6. Los estados de error, vacío, cargando y sin conexión están diseñados.
7. El flujo de voz se entiende con solo tres botones.
8. La pantalla de confirmación soporta una o varias transacciones. La confirmación se responde con frases naturales ("sí", "ok", "correcto", "está bien", "confirmo"). Una acción pendiente se resuelve por voz, texto o endpoint de confirmación; en los tres casos el estado conversacional se invalida.
9. La pantalla de batería baja no bloquea la operación normal.
10. La pantalla de dispositivo bloqueado no muestra datos financieros.
11. Los textos están en español y usan el formato de dinero colombiano.
12. Los assets tienen tamaños y formatos compatibles con el firmware.
13. El diseño es consistente con el Figma de la aplicación.
14. El diseño no depende de touch, teclado ni scroll táctil.
15. El diseño puede implementarse con las limitaciones de 16 MB de flash externa y 512 KB de SRAM.

---

## 16. Decisiones antes de firmware

Decisiones cerradas:

- La confirmación humana es obligatoria; la IA no guarda automáticamente.
- La notificación al dispositivo se entrega por polling HTTP con `after_id` y acuse explícito.
- Se usa la tabla `dispositivos_notificaciones` con estados `pendiente`, `entregada` y `leida`.
- La voz es la entrada principal; el menú informa y el texto `[T]` es alternativa equivalente.
- La confirmación por voz acepta frases naturales; ninguna respuesta larga se toma como confirmación.
- Una acción pendiente confirmada fuera del agente (por endpoint) invalida el estado conversacional.

Pendientes:

- Confirmar el controlador exacto de la pantalla GMT024-10 v2.1 y el orden de sus 7 pines.
- Confirmar que el micrófono es INMP441.
- Confirmar que el amplificador es MAX98357A.
- Confirmar el módulo BMS y cargador de la batería.
- Confirmar el regulador de 3.3 V y la corriente disponible.
- Confirmar si el amplificador se alimenta desde VBAT o desde un boost de 5 V.
- Confirmar que la placa expone `GPIO1` a `GPIO11` y el pad `EN`.
- Confirmar que la TFT funciona con `CS` por GPIO y `RST` conectado a `EN`.
- Definir si habrá OTA en el MVP.
- Definir proveedor de IA, formato de audio, límite de duración y latencia aceptable.
- Definir el límite de mensajes en cola offline.
- Definir la duración máxima de grabación.
- Definir el volumen y la ganancia del amplificador.
- Validar el pinout con la placa física antes de soldar.

---

## 17. Estado del paso

Este documento queda **en stand-by** hasta que la diseñadora entregue los mockups, tokens, assets y especificaciones.

Mientras tanto, el siguiente paso del proyecto continúa con la implementación del backend v2. El firmware del dispositivo no debe comenzar hasta cerrar los puntos de la sección 16 y recibir el diseño.
