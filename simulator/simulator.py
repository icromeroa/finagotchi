import io
import json
import time
import uuid
from pathlib import Path

import keyboard
import requests
import scipy.io.wavfile as wav
import sounddevice as sd
import speech_recognition as sr

CONFIG_PATH = Path(__file__).with_name("config.json")
DEFAULT_CONFIG = {
    "http_base_url": "http://127.0.0.1:5000/api/v1",
    "device_uid": "FINAGOTCHI-PC-SIMULATOR-01",
    "email": "simulador@finagotchi.local",
    "password": "simulador123",
    "nombre": "Simulador",
    "auto_confirm": True,
    "sample_rate": 16000,
    "language": "es-CO",
}


class ApiError(RuntimeError):
    def __init__(self, status, payload):
        self.status = status
        self.payload = payload
        message = payload.get("error", {}).get("mensaje") if isinstance(payload, dict) else None
        super().__init__(message or f"HTTP {status}")


def load_config():
    config = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        config.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
    return config


CONFIG = load_config()
BASE_URL = CONFIG["http_base_url"].rstrip("/")


class FinaGotchiClient:
    def __init__(self, config):
        self.config = config
        self.user_token = None
        self.device_token = None
        self.device_uid = config["device_uid"]

    def request(self, method, path, headers=None, expected=(200, 201), **kwargs):
        response = requests.request(
            method,
            BASE_URL + path,
            headers=headers,
            timeout=(3, 15),
            **kwargs,
        )
        try:
            payload = response.json()
        except ValueError:
            payload = {"raw": response.text}
        if response.status_code not in expected:
            raise ApiError(response.status_code, payload)
        return payload.get("data", payload)

    def login_or_register(self):
        credentials = {
            "correo": self.config["email"],
            "password": self.config["password"],
        }
        try:
            payload = self.request("POST", "/auth/login", json=credentials)
        except ApiError as exc:
            if exc.status != 401:
                raise
            try:
                payload = self.request(
                    "POST",
                    "/auth/register",
                    json={
                        "nombre": self.config.get("nombre") or "Simulador",
                        "correo": self.config["email"],
                        "password": self.config["password"],
                    },
                )
            except ApiError as register_error:
                if register_error.status != 409:
                    raise
                payload = self.request("POST", "/auth/login", json=credentials)
        self.user_token = payload["tokens"]["access_token"]
        return payload["usuario"]

    def user_headers(self):
        return {"Authorization": "Bearer " + self.user_token}

    def ensure_device(self):
        body = {
            "device_uid": self.device_uid,
            "modelo": "Simulador PC",
            "firmware": "sim-v2",
        }
        try:
            registration = self.request("POST", "/device/register", json=body)
        except ApiError as exc:
            if exc.status != 409:
                raise
            devices = self.request("GET", "/device", headers=self.user_headers())
            if not any(device["device_uid"] == self.device_uid for device in devices):
                raise RuntimeError("El dispositivo está vinculado a otra cuenta") from exc
            self.request(
                "POST",
                "/device/unlink",
                headers=self.user_headers(),
                json={"device_uid": self.device_uid},
            )
            registration = self.request("POST", "/device/register", json=body)

        paired = self.request(
            "POST",
            "/device/pair",
            headers=self.user_headers(),
            json={"device_uid": self.device_uid, "pin": registration["pin"]},
        )
        self.device_token = paired["device_token"]
        return self.device_token

    def device_headers(self):
        return {"X-Device-Token": self.device_token}

    def telemetry(self):
        return self.request(
            "POST",
            "/device/telemetry",
            headers=self.device_headers(),
            json={
                "bateria": 95,
                "estado_dispositivo": "reposo",
                "tipo": "latido",
                "firmware": "sim-v2",
            },
        )

    def send_message(self, text, duration):
        return self.request(
            "POST",
            "/device/messages",
            headers=self.device_headers(),
            json={
                "texto": text,
                "message_id": str(uuid.uuid4()),
                "audio_duracion_s": duration,
            },
        )

    def confirm_message(self, message_id):
        return self.request(
            "POST",
            f"/device/messages/{message_id}/confirm",
            headers=self.device_headers(),
            json={},
        )

    def close_day(self):
        return self.request(
            "POST",
            "/device/close-day",
            headers=self.device_headers(),
            json={},
        )

    def home(self):
        return self.request("GET", "/home", headers=self.user_headers())


def capture_voice():
    print("\n------------------------------------------------")
    print("  SIMULADOR DE HARDWARE FINAGOTCHI (PC)")
    print("------------------------------------------------")
    print("Mantén presionada la tecla [ESPACIO] para hablar...")

    while not keyboard.is_pressed("space"):
        time.sleep(0.05)

    print("\n[GRABANDO] Habla ahora hacia el micrófono...")
    audio_data = []
    start_time = time.time()

    def callback(indata, frames, time_info, status):
        audio_data.append(indata.copy())

    with sd.InputStream(
        samplerate=CONFIG["sample_rate"], channels=1, dtype="int16", callback=callback
    ):
        while keyboard.is_pressed("space"):
            time.sleep(0.05)

    duration = round(time.time() - start_time, 1)
    print("[GRABACIÓN FINALIZADA] Transcribiendo voz...")

    if not audio_data:
        return "", duration

    import numpy as np

    audio_np = np.concatenate(audio_data, axis=0)
    wav_bytes = io.BytesIO()
    wav.write(wav_bytes, CONFIG["sample_rate"], audio_np)
    wav_bytes.seek(0)

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(wav_bytes) as source:
            audio = recognizer.record(source)
            transcription = recognizer.recognize_google(audio, language=CONFIG["language"])
            print(f'[VOZ TRANSCRITA]: "{transcription}"')
            return transcription, duration
    except Exception as exc:
        print(f"[ERROR DE TRANSCRIPCIÓN]: {exc}")
        return "", duration


def print_home(data):
    mascot = data.get("mascota", {})
    today = data.get("hoy", {})
    print("\nESTADO DE FINAGOTCHI")
    print(f"  Nancy: salud={mascot.get('salud')}% ánimo={mascot.get('animo')}")
    print(
        f"  Hoy: gastos=${today.get('gastos', 0):,} cupo=${today.get('cupo_restante', 0):,}"
    )
    print(f"  Puntos: {data.get('puntos', 0)}")


def print_closure(data):
    print("\nCIERRE DEL DÍA")
    print(f"  Ingresos: ${data.get('total_ingresos', 0):,}")
    print(f"  Gastos:   ${data.get('total_gastos', 0):,}")
    print(f"  Ahorro:   ${data.get('total_ahorrado', 0):,}")
    print(f"  Salud:    {data.get('salud_fin')}% ({data.get('animo')})")


def handle_text(client, text, duration):
    message = client.send_message(text, duration)
    intent = message.get("intent")
    transactions = message.get("transacciones") or []

    if intent == "cerrar_dia":
        print_closure(client.close_day())
        return
    if intent == "consulta_estado":
        print_home(client.home())
        return
    if not transactions:
        print(f"No se pudo interpretar: {message.get('error')}")
        return

    print("\nPROPUESTA DE REGISTRO")
    for transaction in transactions:
        print(
            f"  {transaction['tipo'].upper()}: ${transaction['monto']:,} "
            f"| categoría={transaction.get('categoria') or 'ahorro'} "
            f"| cuenta={transaction.get('cuenta')}"
        )

    should_confirm = CONFIG.get("auto_confirm", True)
    if not should_confirm:
        answer = input("¿Confirmar? [S/n]: ").strip().lower()
        should_confirm = answer in ("", "s", "si", "sí")
    if not should_confirm:
        print("Registro descartado.")
        return

    confirmed = client.confirm_message(message["id"])
    print(f"Registro confirmado. Puntos otorgados: {confirmed.get('puntos_otorgados', 0)}")
    print_home(client.home())


def main():
    client = FinaGotchiClient(CONFIG)
    user = client.login_or_register()
    print(f"Sesión iniciada como {user['correo']}")
    client.ensure_device()
    print(f"Dispositivo vinculado: {client.device_uid}")
    client.telemetry()

    while True:
        text, duration = capture_voice()
        if not text:
            print("No se recibió una transcripción válida.")
            continue
        try:
            handle_text(client, text, max(duration, 0.5))
        except ApiError as exc:
            print(f"ERROR DE API ({exc.status}): {exc}")
        except Exception as exc:
            print(f"ERROR: {exc}")


if __name__ == "__main__":
    main()
