import io
import json
import time
import uuid
from pathlib import Path

import keyboard
import requests
import scipy.io.wavfile as wav
import sounddevice as sd

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
    "stt_provider": "gemini",
    "request_timeout_s": 90,
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

    def request(self, method, path, headers=None, expected=(200, 201), timeout=None, **kwargs):
        response = requests.request(
            method,
            BASE_URL + path,
            headers=headers,
            timeout=timeout or (3, self.config.get("request_timeout_s", 90)),
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

    def send_audio(self, wav_bytes, duration, message_id):
        """Envia el WAV al backend. La transcripcion la hace el servidor."""
        return self.request(
            "POST",
            "/device/messages",
            headers=self.device_headers(),
            files={"audio": ("audio.wav", wav_bytes, "audio/wav")},
            data={
                "message_id": message_id,
                "audio_duracion_s": f"{float(duration):.1f}",
                "idioma": self.config.get("language", "es-CO"),
            },
        )

    def notifications(self, after_id=0, limit=20):
        return self.request(
            "GET",
            f"/device/notifications?after_id={int(after_id)}&limit={int(limit)}",
            headers=self.device_headers(),
        )

    def ack_notification(self, notification_id, estado="leida"):
        return self.request(
            "POST",
            f"/device/notifications/{notification_id}/ack",
            headers=self.device_headers(),
            json={"estado": estado},
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
    """Graba el microfono y devuelve los bytes WAV y la duracion.

    El simulador no transcribe: solo captura y envia el audio al backend,
    igual que hara el firmware de la ESP32.
    """
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
    print(f"[GRABACIÓN FINALIZADA] {duration}s. Enviando audio al backend...")

    if not audio_data:
        return b"", duration

    import numpy as np

    audio_np = np.concatenate(audio_data, axis=0)
    wav_bytes = io.BytesIO()
    wav.write(wav_bytes, CONFIG["sample_rate"], audio_np)
    return wav_bytes.getvalue(), duration


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


def print_notifications(client, last_id=0):
    """Consulta las notificaciones pendientes y las acusa."""
    payload = client.notifications(after_id=last_id)
    rows = payload.get("notificaciones") or []
    for row in rows:
        print(f"  [NOTIFICACIÓN] {row.get('titulo')}: {row.get('mensaje') or ''}")
        client.ack_notification(row["id"], "leida")
    return payload.get("ultima_id", last_id) or last_id


def handle_message(client, message, last_notification_id=0):
    intent = message.get("intent")
    transactions = message.get("transacciones") or []
    texto = message.get("texto_transcrito")
    if texto:
        print(f'[VOZ TRANSCRITA]: "{texto}"')

    if intent == "cerrar_dia":
        print_closure(client.close_day())
        return last_notification_id
    if intent == "consulta_estado":
        print_home(client.home())
        return last_notification_id
    if not transactions:
        print(f"No se pudo interpretar: {message.get('error')}")
        return last_notification_id

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
        return last_notification_id

    confirmed = client.confirm_message(message["id"])
    print(f"Registro confirmado. Puntos otorgados: {confirmed.get('puntos_otorgados', 0)}")
    print_home(client.home())

    print("\nNOTIFICACIONES DEL DISPOSITIVO")
    last_notification_id = print_notifications(client, last_notification_id)
    return last_notification_id


def main():
    client = FinaGotchiClient(CONFIG)
    user = client.login_or_register()
    print(f"Sesión iniciada como {user['correo']}")
    client.ensure_device()
    print(f"Dispositivo vinculado: {client.device_uid}")
    client.telemetry()
    print(f"Proveedor de transcripción: {CONFIG.get('stt_provider', 'gemini')}")

    last_notification_id = 0
    while True:
        wav_bytes, duration = capture_voice()
        if not wav_bytes:
            print("No se grabó audio válido.")
            continue
        message_id = str(uuid.uuid4())
        try:
            message = client.send_audio(wav_bytes, max(duration, 0.5), message_id)
            if message.get("duplicado"):
                print("El mensaje ya se había procesado. Se devuelve el resultado guardado.")
            last_notification_id = handle_message(client, message, last_notification_id)
        except ApiError as exc:
            print(f"ERROR DE API ({exc.status}): {exc}")
        except Exception as exc:
            print(f"ERROR: {exc}")


if __name__ == "__main__":
    main()
