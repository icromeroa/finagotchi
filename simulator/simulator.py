import io
import time
import requests
from datetime import datetime, timezone
import keyboard
import scipy.io.wavfile as wav
import sounddevice as sd
import speech_recognition as sr

API_URL = "http://127.0.0.1:5000/api/v1/finagotchi/telemetry"
DEVICE_ID = "FINAGOTCHI-PC-SIMULATOR-01"
SAMPLE_RATE = 16000
secuencia = 0


def import_numpy_and_concat(data):
    import numpy as np
    return np.concatenate(data, axis=0)


def capturar_y_transcribir_voz():
    print("\n------------------------------------------------")
    print("  🕹️ SIMULADOR DE HARDWARE FINAGOTCHI (PC)")
    print("------------------------------------------------")
    print("👉 MANTÉN PRESIONADA la tecla [ESPACIO] para hablar...")

    while not keyboard.is_pressed("space"):
        time.sleep(0.05)

    print("\n🎙️ [GRABANDO...] Habla ahora hacia el micrófono...")
    audio_data = []
    start_time = time.time()

    def callback(indata, frames, time_info, status):
        audio_data.append(indata.copy())

    with sd.InputStream(
        samplerate=SAMPLE_RATE, channels=1, dtype="int16", callback=callback
    ):
        while keyboard.is_pressed("space"):
            time.sleep(0.05)

    duration = round(time.time() - start_time, 1)
    print("🛑 [GRABACIÓN FINALIZADA] Transcribiendo voz...")

    if not audio_data:
        return "Sin transcripción", duration

    audio_np = import_numpy_and_concat(audio_data)
    wav_bytes = io.BytesIO()
    wav.write(wav_bytes, SAMPLE_RATE, audio_np)
    wav_bytes.seek(0)

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(wav_bytes) as source:
            audio = recognizer.record(source)
            transcripcion = recognizer.recognize_google(
                audio, language="es-CO"
            )
            print(f'📝 [VOZ TRANSCRIBA]: "{transcripcion}"')
    except sr.UnknownValueError:
        print("⚠️ No se pudo reconocer el audio.")
        transcripcion = "Sin transcripción"
    except Exception as e:
        print(f"⚠️ Error en procesamiento de audio: {e}")
        transcripcion = "Sin transcripción"

    return transcripcion, duration


def build_payload():
    global secuencia
    secuencia += 1
    raw_text, duration = capturar_y_transcribir_voz()

    # Formato UTC según Guía Estándar (RFC 3339)
    timestamp_utc = (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )

    return {
        "message_id": f"{DEVICE_ID}-{secuencia:06d}",
        "device_id": DEVICE_ID,
        "timestamp": timestamp_utc,
        "sequence": secuencia,
        "measurements": {
            "button_state": True,
            "audio_duration_sec": duration,
            "raw_voice_text": raw_text,
        },
    }


def send_telemetry():
    payload = build_payload()
    print(f"\n[SIMULADOR] 📡 Enviando POST a {API_URL}...")

    try:
        response = requests.post(
            API_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=(3, 5),
        )
        response.raise_for_status()
        data = response.json()

        print("✅ ¡RESPUESTA RECIBIDA CON ÉXITO DEL BACKEND!")
        if data.get("tipo") == "consulta_balance":
            print("📊 --- BALANCE GENERAL DIARIO ---")
            print(f"   ├─ 📥 Ingresos: ${data.get('total_ingresos', 0.0):,.1f}")
            print(f"   ├─ 💸 Gastos:   ${data.get('total_gastos', 0.0):,.1f}")
            print(f"   ├─ 💰 Neto:     ${data.get('balance_neto', 0.0):,.1f}")
            print(
                f"   └─ 🐶 Mascotas: Salud={data.get('salud')}% |"
                f" Ánimo={data.get('animo').upper()}\n"
            )
        else:
            tipo = data.get("transaction_type", "expense")
            etiqueta = "📥 INGRESO" if tipo == "income" else "💸 GASTO"
            print(
                f"   ├─ {etiqueta} REGISTRADO: Monto=${data.get('monto', 0.0):,.1f}"
                f" | Cat={data.get('category')}"
            )
            print(
                f"   └─ 🐶 Mascotas: Salud={data.get('salud')}% |"
                f" Ánimo={data.get('animo').upper()}"
            )

        if data.get("alerta_activa"):
            print(
                "   ⚠️ ¡ALERTA CRÍTICA ACTIVADA! (Presupuesto diario superado o"
                " Salud < 20%)\n"
            )

    except requests.exceptions.Timeout:
        print("❌ ERROR: Tiempo de espera agotado (Timeout) al conectar con el Backend.")
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Servidor Backend no encontrado. Verifica que `server.py` esté activo.")
    except requests.exceptions.HTTPError as err:
        print(f"❌ ERROR HTTP {err.response.status_code}: {err.response.text}")


if __name__ == "__main__":
    while True:
        send_telemetry()
        time.sleep(1)