"""Simulador del dispositivo FinaGotchi para escritorio.

Reproduce el flujo de pantallas definido en docs/DISPOSITIVO.md (D01 a D13)
contra el backend real: graba el audio, lo transcribe, interpreta la frase con
la IA, confirma, y muestra el resultado.

    py -3 simulator/simulator.py
"""

import io
import json
import sys
import time
import uuid
from pathlib import Path

import keyboard
import requests
import scipy.io.wavfile as wav
import sounddevice as sd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from simulator import pantallas  # noqa: E402

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
        credenciales = {"correo": self.config["email"], "password": self.config["password"]}
        try:
            payload = self.request("POST", "/auth/login", json=credenciales)
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
                payload = self.request("POST", "/auth/login", json=credenciales)
        self.user_token = payload["tokens"]["access_token"]
        return payload["usuario"]

    def user_headers(self):
        return {"Authorization": "Bearer " + self.user_token}

    def ensure_device(self):
        body = {
            "device_uid": self.device_uid,
            "modelo": "Simulador PC",
            "firmware": "sim-v3",
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
                "bateria": 87,
                "estado_dispositivo": "reposo",
                "tipo": "latido",
                "firmware": "sim-v3",
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


def capture_voice(duracion_maxima=40):
    """Graba el microfono mientras se mantenga la tecla ESPACIO.

    Devuelve los bytes WAV y la duracion. El simulador no transcribe: solo
    captura y envia el audio al backend, igual que hara el firmware.
    """
    print("\n  Mantén presionada la tecla [ESPACIO] y habla.")
    print("  Suelta para enviar. [Atrás para cancelar]")

    while not keyboard.is_pressed("space"):
        time.sleep(0.05)

    bloques = []
    inicio = time.time()

    def callback(indata, frames, time_info, status):
        bloques.append(indata.copy())

    with sd.InputStream(
        samplerate=CONFIG["sample_rate"], channels=1, dtype="int16", callback=callback
    ):
        while keyboard.is_pressed("space"):
            time.sleep(0.05)
            if time.time() - inicio > duracion_maxima:
                print(f"  Tiempo máximo alcanzado ({duracion_maxima}s).")
                break

    duracion = round(time.time() - inicio, 1)
    if not bloques:
        return b"", 0.0

    import numpy as np

    muestras = np.concatenate(bloques, axis=0)
    buffer = io.BytesIO()
    wav.write(buffer, CONFIG["sample_rate"], muestras)
    return buffer.getvalue(), duracion


class Simulador:
    """Maquina de estados del dispositivo simulado."""

    def __init__(self, client):
        self.client = client
        self.ultima_frase = None
        self.ultimo_id_notificacion = 0
        self.ultimo_home = {}

    # --- D03 -------------------------------------------------------------
    def pantalla_reposo(self):
        try:
            self.ultimo_home = self.client.home()
        except ApiError:
            self.ultimo_home = {}
        pendientes = len(self.client.notifications(self.ultimo_id_notificacion).get("notificaciones", []))
        print(pantallas.d03_reposo(self.ultimo_home, conectado=True, pendientes=pendientes))

    # --- D04 a D07 -------------------------------------------------------
    def hablar(self):
        wav_bytes, duracion = capture_voice()
        if not wav_bytes:
            print(pantallas.d11_no_entendio())
            return
        if duracion > 40:
            print(pantallas.d11_no_entendio())
            return

        print(pantallas.d05_procesando())
        message_id = str(uuid.uuid4())
        try:
            message = self.client.send_audio(wav_bytes, duracion, message_id)
        except ApiError as exc:
            if exc.status == 422:
                print(pantallas.d11_no_entendio())
            elif exc.status in (429, 502, 503):
                print(pantallas.d10_sin_conexion())
            else:
                print(pantallas.d10_sin_conexion())
                print(f"  Detalle: {exc}")
            return

        texto = message.get("texto_transcrito")
        self.ultima_frase = texto
        intent = message.get("intent")

        if intent == "cerrar_dia":
            print(pantallas.d09_cierre(self.client.close_day()))
            self.pantalla_reposo()
            return
        if intent == "consulta_estado":
            print(pantallas.d08_consulta(self.client.home()))
            self.ultimo_home = self.client.home()
            return

        transacciones = message.get("transacciones") or []
        if not transacciones:
            print(pantallas.d11_no_entendio())
            return

        print(pantallas.d06_confirmar(transacciones, texto or ""))

        should_confirm = CONFIG.get("auto_confirm", True)
        if not should_confirm:
            answer = input("  ¿Confirmar? [S/n]: ").strip().lower()
            should_confirm = answer in ("", "s", "si", "sí")
        if not should_confirm:
            print("  Registro descartado.")
            self.pantalla_reposo()
            return

        confirmado = self.client.confirm_message(message["id"])
        home = self.client.home()
        self.ultimo_home = home
        print(pantallas.d07_resultado(confirmado.get("puntos_otorgados", 0), home))

    # --- D09 -------------------------------------------------------------
    def cerrar_dia(self):
        try:
            cierre = self.client.close_day()
        except ApiError as exc:
            print(f"  No se pudo cerrar el día: {exc}")
            return
        print(pantallas.d09_cierre(cierre))
        self.pantalla_reposo()

    # --- D13 -------------------------------------------------------------
    def ver_notificaciones(self):
        payload = self.client.notifications(self.ultimo_id_notificacion)
        rows = payload.get("notificaciones") or []
        if not rows:
            print(pantallas.d13_aviso("Sin avisos", "No hay notificaciones nuevas."))
            return
        for row in rows:
            print(pantallas.d13_aviso(row.get("titulo") or "Aviso", row.get("mensaje") or ""))
            self.client.ack_notification(row["id"], "leida")
        self.ultimo_id_notificacion = payload.get("ultima_id", self.ultimo_id_notificacion)

    # --- D08 -------------------------------------------------------------
    def estado_del_dia(self):
        print(pantallas.d08_consulta(self.client.home()))
        self.ultimo_home = self.client.home()


def main():
    client = FinaGotchiClient(CONFIG)
    user = client.login_or_register()
    print(f"  Sesión iniciada como {user['correo']}")
    client.ensure_device()
    print(f"  Dispositivo vinculado: {client.device_uid}")
    client.telemetry()
    print(f"  Proveedor de transcripción: {CONFIG.get('stt_provider', 'gemini')}")

    simulador = Simulador(client)
    print(pantallas.d01_arranque())
    simulador.pantalla_reposo()

    while True:
        print(pantallas.menu())
        try:
            opcion = input("\n  Opción: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n  Hasta luego.")
            return

        if opcion in ("s", "salir", "q"):
            print("  Hasta luego.")
            return
        if opcion in ("h", "hablar"):
            simulador.hablar()
        elif opcion in ("e", "estado"):
            simulador.estado_del_dia()
        elif opcion in ("c", "cerrar", "cierre"):
            simulador.cerrar_dia()
        elif opcion in ("n", "notificaciones"):
            simulador.ver_notificaciones()
        elif opcion in ("r", "repetir"):
            if simulador.ultima_frase:
                print(f"  Última frase: {simulador.ultima_frase}")
            else:
                print("  Todavia no has hablado.")
        elif opcion == "":
            continue
        else:
            print("  Opción no reconocida.")


if __name__ == "__main__":
    main()
