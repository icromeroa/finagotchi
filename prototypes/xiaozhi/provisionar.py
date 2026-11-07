"""Provisiona un dispositivo virtual para el prototipo Xiaozhi.

Hace el mismo flujo que el simulador, pero por HTTP y sin tocar la base:

1. Inicia sesión (o registra la cuenta si no existe).
2. Registra un ``device_uid`` y obtiene un PIN de 6 dígitos.
3. Vincula el dispositivo con la cuenta y obtiene ``device_token``.
4. Guarda el token en ``config.local.json`` (ignorado por git).

El token es un secreto: no lo pegues en documentación ni en capturas.
"""

from __future__ import annotations

import argparse
import getpass
import json
import sys
from pathlib import Path
from urllib import error, request
from urllib.parse import urljoin

DEFAULT_BASE_URL = "http://127.0.0.1:5000/api/v1"
DEFAULT_DEVICE_UID = "FINAGOTCHI-XIAOZHI-01"
CONFIG_LOCAL = Path(__file__).with_name("config.local.json")


class ErrorProvision(Exception):
    pass


def _peticion(base_url, metodo, ruta, payload=None, token=None, timeout=30):
    url = urljoin(base_url.rstrip("/") + "/", ruta.lstrip("/"))
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    cuerpo = None
    if payload is not None:
        cuerpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    peticion = request.Request(url, data=cuerpo, headers=headers, method=metodo)
    try:
        with request.urlopen(peticion, timeout=timeout) as respuesta:
            return respuesta.status, json.loads(respuesta.read().decode("utf-8"))
    except error.HTTPError as exc:
        crudo = exc.read()
        try:
            datos = json.loads(crudo.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            datos = {"error": {"codigo": "HTTP_%s" % exc.code, "mensaje": crudo.decode("utf-8", "replace")}}
        return exc.code, datos
    except error.URLError as exc:
        raise ErrorProvision(
            f"No pude conectar con FinaGotchi en {base_url}: {exc.reason}"
        ) from exc


def _codigo_error(payload):
    return ((payload or {}).get("error") or {}).get("codigo")


def _mensaje_error(payload):
    return ((payload or {}).get("error") or {}).get("mensaje") or payload


def autenticar(base_url, correo, password, nombre):
    estado, payload = _peticion(
        base_url, "POST", "auth/login", {"correo": correo, "password": password}
    )
    if estado == 200:
        token = ((payload.get("data") or {}).get("tokens") or {}).get("access_token")
        if not token:
            raise ErrorProvision("El login no devolvió access_token")
        return token, "login"

    if _codigo_error(payload) != "CREDENCIALES_INVALIDAS":
        raise ErrorProvision(f"Error al iniciar sesión: {_mensaje_error(payload)}")

    estado, payload = _peticion(
        base_url,
        "POST",
        "auth/register",
        {"nombre": nombre, "correo": correo, "password": password},
    )
    if estado not in (200, 201):
        raise ErrorProvision(f"Error al registrar la cuenta: {_mensaje_error(payload)}")
    token = ((payload.get("data") or {}).get("tokens") or {}).get("access_token")
    if not token:
        raise ErrorProvision("El registro no devolvió access_token")
    return token, "registro"


def registrar_dispositivo(base_url, device_uid, modelo, firmware):
    estado, payload = _peticion(
        base_url,
        "POST",
        "device/register",
        {"device_uid": device_uid, "modelo": modelo, "firmware": firmware},
    )
    if estado not in (200, 201):
        codigo = _codigo_error(payload)
        if codigo == "DISPOSITIVO_VINCULADO":
            raise ErrorProvision(
                "Ese device_uid ya está vinculado a una cuenta. Usa otro "
                "device_uid o desvincúlalo desde la app antes de continuar."
            )
        raise ErrorProvision(
            f"Error al registrar el dispositivo: {_mensaje_error(payload)}"
        )
    datos = payload.get("data") or {}
    pin = datos.get("pin")
    if not pin:
        raise ErrorProvision("El registro no devolvió PIN")
    return pin


def vincular_dispositivo(base_url, access_token, device_uid, pin):
    estado, payload = _peticion(
        base_url,
        "POST",
        "device/pair",
        {"device_uid": device_uid, "pin": pin},
        token=access_token,
    )
    if estado != 200:
        raise ErrorProvision(f"Error al vincular: {_mensaje_error(payload)}")
    device_token = (payload.get("data") or {}).get("device_token")
    if not device_token:
        raise ErrorProvision("La vinculación no devolvió device_token")
    return device_token


def guardar_config(ruta, base_url, device_uid, device_token):
    ruta = Path(ruta)
    datos = {}
    if ruta.exists():
        try:
            datos = json.loads(ruta.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            datos = {}
    if not isinstance(datos, dict):
        datos = {}
    datos.update(
        {
            "finagotchi_base_url": base_url.rstrip("/"),
            "device_uid": device_uid,
            "device_token": device_token,
        }
    )
    ruta.write_text(
        json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return ruta


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Obtiene un device_token de FinaGotchi para el prototipo Xiaozhi."
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--device-uid", default=DEFAULT_DEVICE_UID)
    parser.add_argument("--modelo", default="Xiaozhi ESP32-S3")
    parser.add_argument("--firmware", default="prototipo-xiaozhi-0.1")
    parser.add_argument("--correo", required=True, help="Correo de la cuenta FinaGotchi.")
    parser.add_argument(
        "--password",
        default=None,
        help="Contraseña. Si se omite, se pide de forma interactiva.",
    )
    parser.add_argument(
        "--nombre",
        default="Xiaozhi",
        help="Nombre de la cuenta si hay que registrarla.",
    )
    parser.add_argument(
        "--pin",
        default=None,
        help="Usa un PIN ya generado en vez de registrar el dispositivo otra vez.",
    )
    parser.add_argument(
        "--config",
        default=str(CONFIG_LOCAL),
        help="Archivo de salida (por defecto config.local.json).",
    )
    parser.add_argument(
        "--no-guardar",
        action="store_true",
        help="Solo imprime el token; no escribe configuración.",
    )
    args = parser.parse_args(argv)

    password = args.password
    if not password:
        password = getpass.getpass("Contraseña de FinaGotchi: ")
    if not password:
        print("Error: la contraseña es obligatoria.", file=sys.stderr)
        return 2

    try:
        access_token, modo = autenticar(
            args.base_url, args.correo, password, args.nombre
        )
        print(f"Cuenta lista ({modo}).")
        pin = args.pin or registrar_dispositivo(
            args.base_url, args.device_uid, args.modelo, args.firmware
        )
        if not args.pin:
            print(f"PIN generado: {pin} (válido 10 minutos).")
        device_token = vincular_dispositivo(
            args.base_url, access_token, args.device_uid, pin
        )
    except ErrorProvision as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print()
    print(f"device_uid:   {args.device_uid}")
    print(f"device_token: {device_token}")
    print()
    print("Guarda este token como secreto; no lo subas al repositorio.")

    if args.no_guardar:
        return 0

    ruta = guardar_config(args.config, args.base_url, args.device_uid, device_token)
    print(f"Configuración escrita en {ruta} (ignorada por git).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
