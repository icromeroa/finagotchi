"""Simulador del dispositivo FinaGotchi para escritorio.

Reproduce el flujo de pantallas definido en docs/DISPOSITIVO.md (D01 a D13)
contra el backend real: graba el audio, lo transcribe, interpreta la frase con
la IA, confirma, y muestra el resultado.

    py -3 simulator/main.py

El archivo se llama main.py y no simulator.py a proposito: si el modulo se
llamara igual que el paquete, al ejecutarlo directamente el archivo se
sombrearia a si mismo y el import de las pantallas fallaria.
"""

import io
import json
import os
import sys
import time
import uuid
from pathlib import Path

import requests
import scipy.io.wavfile as wav

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from simulator import pantallas  # noqa: E402

# El teclado y el microfono son opcionales: si falta alguno, el simulador
# avisa que instalar y sigue funcionando con la alternativa disponible.
try:
    import keyboard

    TECLADO_DISPONIBLE = True
except Exception:  # noqa: BLE001 - la libreria puede fallar al importar
    keyboard = None
    TECLADO_DISPONIBLE = False

try:
    import sounddevice as sd

    MICROFONO_DISPONIBLE = True
except Exception:  # noqa: BLE001 - falta PortAudio o no hay microfono
    sd = None
    MICROFONO_DISPONIBLE = False

CONFIG_PATH = Path(__file__).with_name("config.json")
DEFAULT_CONFIG = {
    "http_base_url": "http://127.0.0.1:5000/api/v1",
    "device_uid": "FINAGOTCHI-PC-SIMULATOR-01",
    "email": "simulador@finagotchi.local",
    "password": "simulador123",
    "nombre": "Simulador",
    # La confirmacion es siempre humana: no hay guardado automatico.
    "sample_rate": 16000,
    "language": "es-CO",
    "stt_provider": "gemini",
    "input_device": None,
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
    # Permite apuntar a otro backend sin tocar el archivo de configuracion.
    config["http_base_url"] = os.environ.get("FINAGOTCHI_BASE_URL", config["http_base_url"])
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

    def send_text(self, texto, message_id=None):
        """Envia texto por el mismo camino conversacional que la voz."""
        return self.request(
            "POST",
            "/device/messages",
            headers=self.device_headers(),
            json={
                "texto": texto,
                "message_id": message_id or str(uuid.uuid4()),
                "origen": "app_voz",
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

    def goal_plan(self, meses=12):
        return self.request(
            "GET",
            f"/goals/plan?meses={int(meses)}",
            headers=self.user_headers(),
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


NIVEL_SILENCIO = 30


def _estadisticas_audio(muestras):
    """Pico y RMS de las muestras. Sirve para explicar el silencio."""
    import numpy as np

    if muestras is None or len(muestras) == 0:
        return {"pico": 0, "rms": 0.0, "muestras": 0}
    datos = np.asarray(muestras).astype(np.int32)
    pico = int(np.max(np.abs(datos)))
    rms = round(float(np.sqrt(np.mean(datos.astype(np.float64) ** 2))), 2)
    return {"pico": pico, "rms": rms, "muestras": int(len(muestras))}


def _entrada_elegida():
    """Indice y nombre del microfono configurado o del predeterminado."""
    indice = CONFIG.get("input_device")
    try:
        if indice is None:
            indice = sd.default.device[0]
        info = sd.query_devices(indice)
        return indice, info.get("name") or f"dispositivo {indice}"
    except Exception:  # noqa: BLE001 - sin microfono o indice invalido
        return None, "microfono predeterminado"


def listar_microfonos():
    if not MICROFONO_DISPONIBLE:
        print("  No se pudo cargar sounddevice / PortAudio.")
        return []
    entradas = []
    for indice, dispositivo in enumerate(sd.query_devices()):
        if dispositivo.get("max_input_channels", 0) > 0:
            entradas.append((indice, dispositivo.get("name") or "sin nombre"))
            print(f"  [{indice:>2}] {dispositivo.get('name')}")
    return entradas


def probar_microfono(segundos=3):
    """Graba unos segundos y muestra si llega señal. No envia nada al backend."""
    if not MICROFONO_DISPONIBLE:
        print("  Instala las dependencias: py -3 -m pip install -r requirements-simulator.txt")
        return False
    print("\n  Microfonos disponibles:")
    listar_microfonos()
    indice, nombre = _entrada_elegida()
    print(f"\n  Probando: {nombre}")
    print(f"  Habla durante {segundos} segundos...")
    try:
        import numpy as np

        grabacion = sd.rec(
            int(segundos * CONFIG["sample_rate"]),
            samplerate=CONFIG["sample_rate"],
            channels=1,
            dtype="int16",
            device=indice,
        )
        sd.wait()
        muestras = np.asarray(grabacion).reshape(-1)
    except Exception as exc:  # noqa: BLE001
        print(f"  No se pudo grabar: {exc}")
        return False
    stats = _estadisticas_audio(muestras)
    correcto = stats["pico"] >= NIVEL_SILENCIO
    print(pantallas.d17_microfono(nombre, stats["pico"], stats["rms"], correcto))
    if not correcto:
        print(
            "  Consejo: revisa Configuracion > Sistema > Sonido > Entrada,\n"
            "  sube el volumen y elige otro indice con \"input_device\" en\n"
            "  simulator/config.json."
        )
    return correcto


def capture_voice(duracion_maxima=40):
    """Graba el microfono mientras se mantenga la tecla ESPACIO.

    Si el hook de teclado no esta disponible (en Windows suele hacer falta
    ejecutar como administrador), se graba con la tecla ENTER: una pulsacion
    empieza a grabar y la siguiente la detiene.

    Devuelve ``(wav_bytes, duracion, estadisticas)``. El simulador no
    transcribe: solo captura y envia el audio al backend, igual que el
    firmware. Si no llega señal, avisa antes de gastar una llamada al STT.
    """
    if not MICROFONO_DISPONIBLE:
        print()
        print("  No se pudo cargar el microfono (falta PortAudio o sounddevice).")
        print("  Instala las dependencias del simulador:")
        print("      py -3 -m pip install -r requirements-simulator.txt")
        return b"", 0.0, {"pico": 0, "rms": 0.0, "muestras": 0}

    indice, nombre = _entrada_elegida()
    usar_teclado = TECLADO_DISPONIBLE
    if usar_teclado:
        print(f"\n  Microfono: {nombre}")
        print("  Mantén presionada la tecla [ESPACIO] y habla.")
        print("  Suelta para enviar. [Atrás para cancelar]")
    else:
        print("\n  El hook de teclado no esta disponible (se necesita ejecutar")
        print("  como administrador). Se graba con la tecla ENTER:")
        print("  una pulsacion empieza a grabar y la siguiente la detiene.")

    if usar_teclado:
        while not keyboard.is_pressed("space"):
            time.sleep(0.05)

    bloques = []
    inicio = time.time()
    detener = False

    def callback(indata, frames, time_info, status):
        if not detener:
            bloques.append(indata.copy())

    with sd.InputStream(
        samplerate=CONFIG["sample_rate"],
        channels=1,
        dtype="int16",
        device=indice,
        callback=callback,
    ):
        if usar_teclado:
            while keyboard.is_pressed("space"):
                time.sleep(0.05)
                if time.time() - inicio > duracion_maxima:
                    print(f"  Tiempo máximo alcanzado ({duracion_maxima}s).")
                    break
        else:
            input("  [ENTER] para empezar a grabar... ")
            while True:
                time.sleep(0.05)
                if time.time() - inicio > duracion_maxima:
                    print(f"  Tiempo máximo alcanzado ({duracion_maxima}s).")
                    break
                if not input("  [ENTER] para detener la grabación: ").strip():
                    break

    detener = True
    duracion = round(time.time() - inicio, 1)
    if not bloques:
        return b"", 0.0, {"pico": 0, "rms": 0.0, "muestras": 0}

    import numpy as np

    muestras = np.concatenate(bloques, axis=0)
    stats = _estadisticas_audio(muestras)
    print(
        f"  Audio: {duracion}s · {stats['muestras']} muestras · "
        f"pico {stats['pico']} · RMS {stats['rms']}"
    )
    if stats["pico"] < NIVEL_SILENCIO:
        print(pantallas.d17_microfono(nombre, stats["pico"], stats["rms"], False))
        print("  No envie el audio: casi no llego sonido del microfono.")
        return b"", duracion, stats

    buffer = io.BytesIO()
    wav.write(buffer, CONFIG["sample_rate"], muestras)
    return buffer.getvalue(), duracion, stats


class Simulador:
    """Maquina de estados del dispositivo simulado."""

    def __init__(self, client):
        self.client = client
        self.ultima_frase = None
        self.ultima_respuesta = None
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
    def _detalle_error(self, exc):
        payload = exc.payload if isinstance(exc.payload, dict) else {}
        error = payload.get("error") or {}
        return (
            error.get("codigo"),
            error.get("mensaje") or str(exc),
            error.get("detalles"),
        )

    def _procesar_respuesta(self, respuesta):
        """Muestra la respuesta de Nancy sin decidir por el usuario."""
        self.ultima_respuesta = respuesta
        texto = respuesta.get("texto_transcrito")
        if texto:
            self.ultima_frase = texto
            print(f'\n  Escuché: "{texto}"')
        print(pantallas.d15_conversacion(respuesta))
        if respuesta.get("intent") == "cerrar_dia" and (respuesta.get("datos") or {}).get("cierre"):
            print(pantallas.d09_cierre(respuesta["datos"]["cierre"]))

    def hablar(self):
        wav_bytes, duracion, stats = capture_voice()
        if not wav_bytes:
            if stats.get("pico", 0) < NIVEL_SILENCIO:
                print(pantallas.d16_error(
                    "No escuché tu voz",
                    "El micrófono casi no recibió señal. Revisa el dispositivo o usa [T] para escribir.",
                ))
            else:
                print(pantallas.d16_error("Audio vacío", "No se pudo capturar la frase."))
            return
        if duracion > 40:
            print(pantallas.d16_error("Audio muy largo", "Intenta frases de menos de 40 segundos."))
            return

        print(pantallas.d05_procesando())
        message_id = str(uuid.uuid4())
        try:
            message = self.client.send_audio(wav_bytes, duracion, message_id)
        except ApiError as exc:
            codigo, mensaje, detalles = self._detalle_error(exc)
            if exc.status in (429, 502, 503, 504):
                print(pantallas.d10_sin_conexion())
            else:
                detalle = None
                if isinstance(detalles, dict):
                    detalle = detalles.get("motivo") or detalles.get("mensaje")
                print(pantallas.d16_error(codigo or "Error al procesar", mensaje, detalle))
            return
        self._procesar_respuesta(message)

    def escribir(self):
        """Entrada de texto equivalente a la voz, para cuando no se puede hablar."""
        try:
            texto = input("\n  Escribe tu frase: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not texto:
            return
        self.escribir_texto(texto)

    def escribir_texto(self, texto):
        message_id = str(uuid.uuid4())
        print(pantallas.d05_procesando())
        try:
            message = self.client.send_text(texto, message_id)
        except ApiError as exc:
            codigo, mensaje, detalles = self._detalle_error(exc)
            detalle = None
            if isinstance(detalles, dict):
                detalle = detalles.get("motivo") or detalles.get("mensaje")
            print(pantallas.d16_error(codigo or "Error al procesar", mensaje, detalle))
            return
        self._procesar_respuesta(message)

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

    # --- D14 -------------------------------------------------------------
    def ver_plan(self):
        try:
            plan = self.client.goal_plan(12)
        except ApiError as exc:
            print(pantallas.d13_aviso("Sin plan", str(exc)))
            return
        print(pantallas.d14_plan_ahorro(plan))


def verificar_backend():
    """Comprueba que el backend responda y explica que hacer si no."""
    try:
        respuesta = requests.get(f"{BASE_URL}/health", timeout=5)
        if respuesta.status_code == 200:
            return True
    except requests.RequestException:
        pass
    print()
    print("  ! No se pudo conectar con el backend.")
    print(f"    Direccion: {BASE_URL}")
    print()
    print("  Levanta el backend en otra terminal, desde la raiz del proyecto:")
    print("      py -3 backend/server.py")
    print()
    print("  Si el backend esta en otra maquina, cambia la direccion en")
    print("  simulator/config.json o en la variable FINAGOTCHI_BASE_URL.")
    return False


def main():
    print("  ==============================================")
    print("     SIMULADOR FINAGOTCHI (dispositivo virtual)")
    print("  ==============================================")
    print(f"  Backend: {BASE_URL}")
    if not TECLADO_DISPONIBLE:
        print("  Teclado: sin hook (usa ENTER para grabar). Ejecuta como administrador para la ESPACIO.")
    if not MICROFONO_DISPONIBLE:
        print("  Microfono: NO disponible. Instala requirements-simulator.txt")
    if not verificar_backend():
        return 1

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
        if opcion in ("h", "hablar", ""):
            # La voz es la entrada principal: Enter tambien inicia la captura.
            simulador.hablar()
        elif opcion in ("t", "texto", "escribir"):
            simulador.escribir()
        elif opcion in ("a", "audio", "microfono", "micrófono"):
            probar_microfono()
        elif opcion in ("e", "estado"):
            simulador.estado_del_dia()
        elif opcion in ("p", "plan"):
            simulador.ver_plan()
        elif opcion in ("c", "cerrar", "cierre"):
            simulador.cerrar_dia()
        elif opcion in ("n", "notificaciones"):
            simulador.ver_notificaciones()
        elif opcion in ("r", "repetir"):
            if simulador.ultima_respuesta:
                print(pantallas.d15_conversacion(simulador.ultima_respuesta))
            elif simulador.ultima_frase:
                print(f"  Última frase: {simulador.ultima_frase}")
            else:
                print("  Todavia no has hablado.")
        else:
            # Cualquier frase natural escrita se envia por el mismo agente.
            simulador.escribir_texto(opcion)


if __name__ == "__main__":
    main()
