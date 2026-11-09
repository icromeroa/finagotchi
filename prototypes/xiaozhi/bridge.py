"""Puente HTTP aislado entre Xiaozhi y el backend FinaGotchi.

Este archivo **no forma parte del backend**. Su único trabajo es traducir un
turno de texto ya reconocido por Xiaozhi al contrato de dispositivo de
FinaGotchi y devolver la respuesta de Nancy lista para hablar.

Flujo:

    Xiaozhi (STT) -> POST /turno -> FinaGotchi /device/messages
                                  -> {texto_voz, mensaje_nancy, ...}
    Xiaozhi (TTS) -> POST /sintetizar -> FinaGotchi /device/voice/synthesize
                                       -> audio/wav en memoria

El audio nunca se escribe en disco. El token del dispositivo se lee de una
configuración local que no se versiona.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import error, request
from urllib.parse import urljoin

DEFAULT_BASE_URL = "http://127.0.0.1:5000/api/v1"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787
DEFAULT_TIMEOUT = 90
CONFIG_LOCAL = Path(__file__).with_name("config.local.json")

CAMPOS_CONFIG = (
    "finagotchi_base_url",
    "device_token",
    "bridge_host",
    "bridge_port",
    "timeout_s",
)

VARIABLES_ENTORNO = {
    "finagotchi_base_url": "FINAGOTCHI_BASE_URL",
    "device_token": "FINAGOTCHI_DEVICE_TOKEN",
    "bridge_host": "XIAOZHI_BRIDGE_HOST",
    "bridge_port": "XIAOZHI_BRIDGE_PORT",
    "timeout_s": "FINAGOTCHI_TIMEOUT_S",
}


class ErrorPuente(Exception):
    """Fallo de configuración o de red del puente."""


def cargar_config(ruta=None, entorno=None):
    """Carga la configuración con precedencia: entorno > archivo > defaults.

    ``ruta`` permite inyectar un archivo en pruebas. Si no existe, se usan los
    valores por defecto. Nunca se versiona ``config.local.json``.
    """
    entorno = os.environ if entorno is None else entorno
    ruta = Path(ruta) if ruta else CONFIG_LOCAL
    config = {
        "finagotchi_base_url": DEFAULT_BASE_URL,
        "device_token": "",
        "bridge_host": DEFAULT_HOST,
        "bridge_port": DEFAULT_PORT,
        "timeout_s": DEFAULT_TIMEOUT,
    }

    if ruta.exists():
        try:
            datos = json.loads(ruta.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ErrorPuente(f"No pude leer {ruta}: {exc}") from exc
        if not isinstance(datos, dict):
            raise ErrorPuente(f"{ruta} debe contener un objeto JSON")
        for campo in CAMPOS_CONFIG:
            if datos.get(campo) not in (None, ""):
                config[campo] = datos[campo]

    for campo, variable in VARIABLES_ENTORNO.items():
        valor = entorno.get(variable)
        if valor not in (None, ""):
            config[campo] = valor

    try:
        config["bridge_port"] = int(config["bridge_port"])
        config["timeout_s"] = int(config["timeout_s"])
    except (TypeError, ValueError) as exc:
        raise ErrorPuente("bridge_port y timeout_s deben ser números enteros") from exc

    config["finagotchi_base_url"] = str(config["finagotchi_base_url"]).rstrip("/")
    config["device_token"] = str(config["device_token"]).strip()
    return config


def _decodificar_json(cuerpo):
    if not cuerpo:
        return None
    try:
        return json.loads(cuerpo.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None


def normalizar_respuesta(payload):
    """Aplana el sobre ``{"ok": true, "data": ...}`` de FinaGotchi.

    Devuelve un diccionario con los campos que Xiaozhi necesita y conserva la
    respuesta original en ``finagotchi`` para depuración.
    """
    if not isinstance(payload, dict):
        return {
            "ok": False,
            "hablar": "No recibí una respuesta válida de FinaGotchi.",
            "error": {"codigo": "RESPUESTA_INVALIDA"},
        }

    if payload.get("ok") is False:
        return {
            "ok": False,
            "hablar": "FinaGotchi no pudo procesar el mensaje.",
            "error": payload.get("error") or {"codigo": "ERROR_FINAGOTCHI"},
            "finagotchi": payload,
        }

    datos = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    hablar = datos.get("texto_voz") or datos.get("mensaje_nancy") or ""
    return {
        "ok": True,
        "hablar": hablar,
        "texto_voz": datos.get("texto_voz"),
        "mensaje_nancy": datos.get("mensaje_nancy"),
        "tipo_respuesta": datos.get("tipo_respuesta"),
        "requiere_confirmacion": bool(datos.get("requiere_confirmacion")),
        "intent": datos.get("intent"),
        "datos": datos.get("datos") or {},
        "finagotchi": datos,
    }


def texto_de_sintesis(payload):
    """Acepta el nombre de campo de FinaGotchi y el de TTS personalizado."""
    if not isinstance(payload, dict):
        return ""
    for campo in ("texto", "prompt_text", "input", "text"):
        valor = payload.get(campo)
        if isinstance(valor, str) and valor.strip():
            return valor.strip()
    return ""


class ClienteFinaGotchi:
    """Cliente mínimo del contrato de dispositivo de FinaGotchi."""

    def __init__(self, base_url, device_token, timeout=DEFAULT_TIMEOUT):
        self.base_url = base_url.rstrip("/") + "/"
        self.device_token = (device_token or "").strip()
        self.timeout = timeout

    def _peticion(self, metodo, ruta, payload=None):
        if not self.device_token:
            raise ErrorPuente(
                "Falta FINAGOTCHI_DEVICE_TOKEN. Ejecuta provisionar.py y "
                "guarda el token en config.local.json."
            )

        url = urljoin(self.base_url, ruta.lstrip("/"))
        headers = {
            "Accept": "application/json",
            "X-Device-Token": self.device_token,
        }
        cuerpo = None
        if payload is not None:
            cuerpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"

        peticion = request.Request(url, data=cuerpo, headers=headers, method=metodo)
        try:
            with request.urlopen(peticion, timeout=self.timeout) as respuesta:
                return (
                    respuesta.status,
                    respuesta.headers.get("Content-Type", ""),
                    respuesta.read(),
                )
        except error.HTTPError as exc:
            try:
                return (
                    exc.code,
                    exc.headers.get("Content-Type", "") if exc.headers else "",
                    exc.read(),
                )
            finally:
                exc.close()
        except error.URLError as exc:
            raise ErrorPuente(
                f"No pude conectar con FinaGotchi en {self.base_url}: {exc.reason}"
            ) from exc

    def turno(self, texto, message_id=None):
        """Envía un turno de texto y devuelve la respuesta normalizada."""
        texto = (texto or "").strip()
        if not texto:
            raise ValueError("El campo texto es obligatorio")

        payload = {
            "texto": texto,
            "message_id": message_id or f"xiaozhi-{uuid.uuid4().hex}",
        }
        estado, _tipo, cuerpo = self._peticion(
            "POST", "device/messages", payload
        )
        return estado, normalizar_respuesta(_decodificar_json(cuerpo))

    def confirmar(self, message_id):
        """Confirma un mensaje pendiente de forma explícita."""
        if message_id in (None, ""):
            raise ValueError("El campo message_id es obligatorio")
        estado, _tipo, cuerpo = self._peticion(
            "POST", f"device/messages/{message_id}/confirm"
        )
        return estado, normalizar_respuesta(_decodificar_json(cuerpo))

    def sintetizar(self, texto):
        """Pide a FinaGotchi el WAV de una frase. No lo guarda."""
        texto = (texto or "").strip()
        if not texto:
            raise ValueError("El campo texto es obligatorio")
        return self._peticion(
            "POST", "device/voice/synthesize", {"texto": texto}
        )


class ManejadorPuente(BaseHTTPRequestHandler):
    server_version = "FinaGotchiXiaozhiBridge/0.1"

    # --- utilidades de respuesta ---------------------------------------
    def _enviar_bytes(self, estado, tipo, cuerpo):
        self.send_response(estado)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(cuerpo)

    def _enviar_json(self, estado, payload):
        cuerpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._enviar_bytes(estado, "application/json; charset=utf-8", cuerpo)

    def _leer_json(self):
        largo = int(self.headers.get("Content-Length") or 0)
        if largo <= 0:
            return {}
        crudo = self.rfile.read(largo)
        try:
            datos = json.loads(crudo.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise ValueError("El cuerpo debe ser JSON válido") from exc
        if not isinstance(datos, dict):
            raise ValueError("El cuerpo debe ser un objeto JSON")
        return datos

    # --- rutas ---------------------------------------------------------
    def do_GET(self):
        if self.path.split("?", 1)[0] == "/salud":
            config = self.server.config
            self._enviar_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "servicio": "puente-xiaozhi-finagotchi",
                    "version": self.server_version,
                    "finagotchi": config["finagotchi_base_url"],
                    "token_configurado": bool(config["device_token"]),
                },
            )
            return
        self._enviar_json(
            HTTPStatus.NOT_FOUND,
            {"ok": False, "error": {"codigo": "RUTA_NO_ENCONTRADA"}},
        )

    def do_POST(self):
        ruta = self.path.split("?", 1)[0]
        try:
            datos = self._leer_json()
        except ValueError as exc:
            self._enviar_json(
                HTTPStatus.BAD_REQUEST,
                {"ok": False, "error": {"codigo": "JSON_INVALIDO", "mensaje": str(exc)}},
            )
            return

        cliente = self.server.cliente
        try:
            if ruta == "/turno":
                estado, respuesta = cliente.turno(datos.get("texto"), datos.get("message_id"))
                self._enviar_json(estado, respuesta)
                return

            if ruta == "/confirmar":
                estado, respuesta = cliente.confirmar(datos.get("message_id"))
                self._enviar_json(estado, respuesta)
                return

            if ruta == "/sintetizar":
                texto = texto_de_sintesis(datos)
                estado, tipo, cuerpo = cliente.sintetizar(texto)
                if "audio" in (tipo or "").lower():
                    self._enviar_bytes(estado, tipo or "audio/wav", cuerpo)
                else:
                    self._enviar_bytes(
                        estado,
                        tipo or "application/json; charset=utf-8",
                        cuerpo,
                    )
                return
        except ValueError as exc:
            self._enviar_json(
                HTTPStatus.UNPROCESSABLE_ENTITY,
                {"ok": False, "error": {"codigo": "CAMPOS_REQUERIDOS", "mensaje": str(exc)}},
            )
            return
        except ErrorPuente as exc:
            self._enviar_json(
                HTTPStatus.SERVICE_UNAVAILABLE,
                {"ok": False, "error": {"codigo": "PUENTE_NO_DISPONIBLE", "mensaje": str(exc)}},
            )
            return

        self._enviar_json(
            HTTPStatus.NOT_FOUND,
            {"ok": False, "error": {"codigo": "RUTA_NO_ENCONTRADA"}},
        )

    def log_message(self, formato, *args):
        # Log compacto en una línea; nunca imprime el token.
        sys.stderr.write(
            "[puente] %s - %s\n" % (self.address_string(), formato % args)
        )


def crear_servidor(config):
    cliente = ClienteFinaGotchi(
        config["finagotchi_base_url"],
        config["device_token"],
        timeout=config["timeout_s"],
    )
    servidor = ThreadingHTTPServer(
        (config["bridge_host"], config["bridge_port"]), ManejadorPuente
    )
    servidor.daemon_threads = True
    servidor.config = config
    servidor.cliente = cliente
    return servidor


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Puente HTTP aislado entre Xiaozhi y FinaGotchi."
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Archivo JSON de configuración (por defecto config.local.json).",
    )
    parser.add_argument(
        "--host", default=None, help="Host de escucha; sobrescribe la configuración."
    )
    parser.add_argument(
        "--port", type=int, default=None, help="Puerto de escucha; sobrescribe la configuración."
    )
    args = parser.parse_args(argv)

    try:
        config = cargar_config(args.config)
    except ErrorPuente as exc:
        print(f"Error de configuración: {exc}", file=sys.stderr)
        return 2

    if args.host:
        config["bridge_host"] = args.host
    if args.port:
        config["bridge_port"] = args.port

    servidor = crear_servidor(config)
    host, puerto = servidor.server_address[:2]
    print(f"Puente Xiaozhi escuchando en http://{host}:{puerto}")
    print(f"FinaGotchi: {config['finagotchi_base_url']}")
    if not config["device_token"]:
        print(
            "Aviso: falta el token del dispositivo. /turno y /sintetizar "
            "responderán 503 hasta configurarlo.",
            file=sys.stderr,
        )
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nPuente detenido.")
    finally:
        servidor.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
