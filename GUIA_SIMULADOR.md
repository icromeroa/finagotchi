# 🕹️ Guía de Uso e Instalación: Simulador FinaGotchi (PC)

Este documento detalla los requisitos, pasos de instalación y el procedimiento paso a paso para ejecutar el servidor local y el simulador de hardware por voz del proyecto **FinaGotchi**.

---

## 📋 Requisitos Previos

1. **Python 3.10 o superior** instalado en el sistema.
2. Micrófono operativo conectado a la computadora.
3. Conexión a Internet (requerida por el servicio Google Speech Recognition para transcribir el audio).

---

## 🛠️ Instalación de Dependencias

Abre una terminal de PowerShell y ejecuta el siguiente comando para instalar las librerías necesarias (mantenimiento optimizado con `sounddevice` para evitar errores de compilación C++):

```powershell
py -m pip install flask requests keyboard SpeechRecognition sounddevice scipy numpy
```

### Paquetes instalados

- `flask`: Framework web para la API REST del servidor backend.
- `requests`: Cliente HTTP para el envío de peticiones JSON desde el simulador.
- `keyboard`: Detección del evento de presionar/soltar la tecla ESPACIO.
- `sounddevice` & `scipy`: Captura de audio del micrófono en tiempo real.
- `SpeechRecognition`: Procesamiento e interpretación de voz a texto en español (`es-CO`).

---

## 🔓 Cómo abrir PowerShell en Modo Administrador

El simulador requiere permisos de administrador para capturar globalmente la tecla ESPACIO mediante la librería `keyboard`.

### Opción A: Desde Visual Studio Code (Recomendada)

Abre tu terminal integrada en VS Code (`Ctrl + Shift + ~`).

Ejecuta el comando:

```powershell
Start-Process powershell -Verb RunAs
```

Acepta el mensaje emergente de confirmación de Windows (UAC).

### Opción B: Desde el Menú Inicio de Windows

Presiona la tecla Windows y busca PowerShell.

Haz clic derecho sobre Windows PowerShell y selecciona **Ejecutar como administrador**.

---

## 🚀 Guía de Ejecución Paso a Paso

Para probar el flujo completo necesitas tener dos terminales abiertas simultáneamente.

### Paso 1: Iniciar el Servidor Backend (`server.py`)

Abre tu Terminal 1 (no requiere permisos de administrador).

Navega a la carpeta de tu proyecto:

```powershell
cd "ruta/a/tu/proyecto/finagotchi"
```

Ejecuta el servidor Flask:

```powershell
py backend/server.py
```

Deberás ver el mensaje que confirma que el backend escucha en `http://127.0.0.1:5000`.

### Paso 2: Iniciar el Simulador de Hardware (`simulador.py`)

Abre la Terminal 2 (Ejecutada como Administrador).

Navega a la carpeta del proyecto:

```powershell
cd "ruta/a/tu/proyecto/finagotchi"
```

Ejecuta el archivo del simulador:

```powershell
py simulator/simulator.py
```

---

## 🎙️ Interacción y Comandos de Voz

Una vez cargado el simulador, puedes interactuar manteniendo presionada la barra espaciadora.

### Modo de Uso

- Mantén presionada la barra espaciadora **[ESPACIO]**.   
- Habla al micrófono pronunciando una frase de prueba, por ejemplo:   
    - Gasto: "Gasté 14000 pesos en el almuerzo"   
    - Ingreso: "Me pagaron 50000 por un trabajo"   
    - Balance: "¿Cómo me fue el día de hoy?"   
- Suelta la barra espaciadora **[ESPACIO]** para finalizar la grabación.
El simulador transcribirá el audio y enviará la telemetría vía HTTP POST al servidor, donde verás reflejada la transacción y el estado de la mascota.

---

## 💬 Ejemplos de Frases Soportadas

### Registro de Gasto

*(Disminuye presupuesto / Afecta salud si se excede)*

- "Gasté 14000 en el almuerzo"
- "Pagué 8000 pesos de transporte"
- "Compré un café por 5 mil"

### Registro de Ingreso

*(Aumenta saldo / Restaura salud del Tamagotchi)*

- "Me pagaron 24000 por un trabajo"
- "Recibí 50000 pesos de mesada"
- "Ingresaron 15k a mi cuenta"

### Consulta de Balance General

*(Muestra totales del día y estado de la mascota)*

- "¿Cómo me fue el día de hoy?"
- "Dame mi balance"
- "¿Cuánto me queda?"

---

## 📂 Estructura de Datos (Contrato HTTP POST API)

El simulador empaqueta el evento capturado y transmite la siguiente estructura JSON a `http://127.0.0.1:5000/api/v1/finagotchi/telemetry`:

```json
{
  "device_info": {
    "device_id": "FINAGOTCHI-PC-SIMULATOR-01",
    "firmware_version": "v1.0-SIM",
    "battery_level_pct": 95,
    "timestamp": "2026-09-14 00:00:00"
  },
  "telemetry_hardware": {
    "button_state": true,
    "audio_duration_sec": 3.5,
    "device_status": "transmitting"
  },
  "audio_payload": {
    "raw_voice_text": "Me pagaron 24000 por un trabajo",
    "tipo_detectado": "ingreso",
    "monto_detectado": 24000.0,
    "categoria_detectada": "ingresos"
  }
}
```

---

## ❓ Solución de Problemas Frecuentes

### Error: `[Errno 2] No such file or directory`

Ocurre porque la terminal no está posicionada en la carpeta del proyecto. Usa el comando `cd "ruta_de_tu_carpeta"` antes de ejecutar `py simulador.py`.

### Error: `PermissionError` o `keyboard` no detecta la tecla Espacio

Asegúrate de abrir la ventana de PowerShell en **Modo Administrador**.

### La app reconoce montos pequeños o incorrectos

El reconocedor entiende modismos colombianos como "10k" o "10 mil". Si pronuncias un número menor a 100 (ej. "15"), la lógica lo interpretará automáticamente en contexto de miles de pesos ($15,000 COP).
