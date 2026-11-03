import io
import time
import keyboard
import requests
import scipy.io.wavfile as wav
import sounddevice as sd
import speech_recognition as sr
from datetime import datetime, timezone

API_URL = "http://127.0.0.1:5000/api/v1/finagotchi/telemetry"
DEVICE_ID = "FINAGOTCHI-PC-SIMULATOR-01"
SAMPLE_RATE = 16000
secuencia = 0


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

    import numpy as np

    audio_np = np.concatenate(audio_data, axis=0)
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
            print(f'📝 [VOZ TRANSCRIBIDA]: "{transcripcion}"')
    except Exception as e:
        print(f"⚠️ Error al transcribir: {e}")
        transcripcion = "Sin transcripción"

    return transcripcion, duration


def send_telemetry():
    global secuencia
    secuencia += 1
    raw_text, duration = capturar_y_transcribir_voz()

    timestamp_utc = (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )
    unique_id = f"{DEVICE_ID}-{int(time.time())}-{secuencia:04d}"

    payload = {
        "message_id": unique_id,
        "device_id": DEVICE_ID,
        "timestamp": timestamp_utc,
        "sequence": secuencia,
        "measurements": {
            "button_state": True,
            "audio_duration_sec": duration,
            "raw_voice_text": raw_text,
        },
    }

    try:
        response = requests.post(
            API_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=(3, 5),
        )

        if response.status_code in [200, 201]:
            data = response.json()
            print("\n✅ ¡RESPUESTA RECIBIDA CON ÉXITO DEL BACKEND!")
            tipo = data.get("tipo")

            if tipo == "cierre_dia":
                print(
                    "🔒 --- CIERRE DE JORNADA (LA SALUD SE MANTIENE PARA EL"
                    " SIGUIENTE DÍA) ---"
                )
                print(
                    f"   ├─ 📥 Ingresos Cierre:"
                    f" ${data.get('total_ingresos', 0.0):,.1f}"
                )
                print(
                    f"   ├─ 💸 Gastos Cierre:  "
                    f" ${data.get('total_gastos', 0.0):,.1f}"
                )
                print(
                    f"   ├─ 💰 Neto Cierre:    "
                    f" ${data.get('balance_neto', 0.0):,.1f}"
                )
                print(
                    f"   └─ 🐶 FinaGotchi inicia el nuevo día con Salud="
                    f"{data.get('salud_heredada')}% | Ánimo={data.get('animo')}\n"
                )

            else:
                if tipo == "consulta_estado":
                    print("📊 --- ESTADO PARCIAL DE LA JORNADA ---")
                else:
                    tipo_tx = data.get("transaction_type", "expense")
                    etiqueta = "📥 INGRESO" if tipo_tx == "income" else "💸 GASTO"
                    print(
                        f"   ├─ {etiqueta} REGISTRADO:"
                        f" Monto=${data.get('monto', 0.0):,.1f} |"
                        f" Categoria={data.get('category')}"
                    )

                print(
                    f"   ├─ 📊 Balance Neto: ${data.get('balance_neto', 0.0):,.1f}"
                )
                print(
                    f"   └─ 🐶 Estado Mascota: Salud={data.get('salud')}% |"
                    f" Ánimo={data.get('animo')}"
                )

                # Mostrar Presupuestos por Categoría
                categorias = data.get("categorias", {})
                if categorias:
                    print("\n   🏷️  [PRESUPUESTOS POR CATEGORÍA]:")
                    for cat, info in categorias.items():
                        alerta = " ⚠️ (EXCEDIDO)" if info["superado"] else ""
                        print(
                            f"      • {cat.capitalize():<14}: Gastado"
                            f" ${info['gastado']:,.0f} / Limite"
                            f" ${info['limite']:,.0f} (Disponible:"
                            f" ${info['restante']:,.0f}){alerta}"
                        )
                print()

        else:
            print(f"❌ ERROR EN SERVIDOR: {response.status_code}")

    except Exception as e:
        print(f"❌ ERROR DE CONEXIÓN: {e}")


if __name__ == "__main__":
    while True:
        send_telemetry()
        time.sleep(1)