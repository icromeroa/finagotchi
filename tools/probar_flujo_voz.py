"""Prueba real del flujo de voz contra un backend en ejecucion.

Uso:
    py -3 tools/probar_flujo_voz.py ruta\al\audio.wav

El script registra un usuario de prueba, vincula un dispositivo, envia el WAV
por multipart, confirma el mensaje, consulta las notificaciones y las acusa.
Al final muestra la auditoria registrada en ``interacciones_ia``.
"""

import argparse
import os
import sys
import uuid
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def parse_args():
    parser = argparse.ArgumentParser(description="Prueba del flujo de voz")
    parser.add_argument("audio", help="Archivo WAV de 16 kHz mono")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("FINAGOTCHI_BASE_URL", "http://127.0.0.1:5000/api/v1"),
    )
    parser.add_argument("--correo", default="prueba-voz@finagotchi.local")
    parser.add_argument("--password", default="pruebavoz123")
    return parser.parse_args()


def main():
    args = parse_args()
    audio_bytes = Path(args.audio).read_bytes()
    base = args.base_url.rstrip("/")

    credenciales = {"correo": args.correo, "password": args.password}
    response = requests.post(
        f"{base}/auth/login", json=credenciales, timeout=(5, 30)
    )
    if response.status_code == 401:
        response = requests.post(
            f"{base}/auth/register",
            json={
                "nombre": "Prueba de voz",
                "correo": args.correo,
                "password": args.password,
            },
            timeout=(5, 30),
        )
    response.raise_for_status()
    token = response.json()["data"]["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("1. Sesion iniciada")

    device_uid = f"PRUEBA-VOZ-{uuid.uuid4().hex[:8]}"
    registration = requests.post(
        f"{base}/device/register",
        json={"device_uid": device_uid, "modelo": "Script", "firmware": "0.1"},
        timeout=(5, 30),
    )
    registration.raise_for_status()
    pin = registration.json()["data"]["pin"]
    paired = requests.post(
        f"{base}/device/pair",
        json={"device_uid": device_uid, "pin": pin},
        headers=headers,
        timeout=(5, 30),
    )
    paired.raise_for_status()
    device_headers = {"X-Device-Token": paired.json()["data"]["device_token"]}
    print(f"2. Dispositivo vinculado: {device_uid}")

    message_id = str(uuid.uuid4())
    response = requests.post(
        f"{base}/device/messages",
        headers=device_headers,
        files={"audio": (Path(args.audio).name, audio_bytes, "audio/wav")},
        data={"message_id": message_id, "idioma": "es-CO"},
        timeout=(5, 120),
    )
    print(f"3. Envio de audio: HTTP {response.status_code}")
    if response.status_code != 201:
        print(response.text)
        return 1
    payload = response.json()["data"]
    print(f"   Transcripcion: {payload.get('texto_transcrito')}")
    for transaction in payload.get("transacciones", []):
        print(
            f"   Transaccion: {transaction['tipo']} ${transaction['monto']:,} "
            f"categoria={transaction.get('categoria')} cuenta={transaction.get('cuenta')}"
        )

    confirmed = requests.post(
        f"{base}/device/messages/{payload['id']}/confirm",
        json={},
        headers=device_headers,
        timeout=(5, 30),
    )
    confirmed.raise_for_status()
    print(f"4. Mensaje confirmado. Puntos: {confirmed.json()['data'].get('puntos_otorgados')}")

    notifications = requests.get(
        f"{base}/device/notifications",
        headers=device_headers,
        timeout=(5, 30),
    )
    notifications.raise_for_status()
    rows = notifications.json()["data"]["notificaciones"]
    for row in rows:
        print(f"5. Notificacion #{row['id']}: {row['titulo']} - {row.get('mensaje')}")
        requests.post(
            f"{base}/device/notifications/{row['id']}/ack",
            json={"estado": "leida"},
            headers=device_headers,
            timeout=(5, 30),
        )
    print(f"   Notificaciones confirmadas: {len(rows)}")

    from backend import services  # noqa: E402
    from backend.db import get_db, init_app  # noqa: E402
    from flask import Flask  # noqa: E402

    app = Flask(__name__)
    app.config["DATABASE"] = str(ROOT / "finagotchi.db")
    init_app(app)
    with app.app_context():
        conn = get_db()
        row = conn.execute(
            "SELECT * FROM interacciones_ia ORDER BY id DESC LIMIT 1"
        ).fetchone()
        print("6. Auditoria de la ultima llamada a la IA:")
        if row is None:
            print("   No hay auditoria registrada")
        else:
            print(f"   proveedor={row['proveedor']} modelo={row['modelo']}")
            print(f"   latencia_ms={row['latencia_ms']} tokens={row['tokens_entrada']}")
            print(f"   entrada={row['entrada_json']}")
            print(f"   salida={row['salida_json']}")
        audio_rows = conn.execute(
            "SELECT COUNT(*) FROM mensajes_dispositivo WHERE texto_transcrito IS NOT NULL"
        ).fetchone()[0]
        print(f"7. Mensajes con texto guardado: {audio_rows} (el audio nunca se guarda)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
