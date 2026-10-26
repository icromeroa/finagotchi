"""Envía N lecturas al backend SIN micrófono, con el mismo contrato JSON de simulator.py.

Uso:  python3 simulator/enviar_lecturas.py --n 10
"""
import argparse
import time
from datetime import datetime, timezone

import requests

DEVICE_ID = "FINAGOTCHI-PC-SIMULATOR-01"
FRASES = [
    "gasté 12000 en el almuerzo",
    "me pagaron 50000 por un trabajo",
    "pagué 3000 de transporte",
    "compré un café por 5000",
    "gasté 8000 en el cine",
    "gasté 6000 en la farmacia",
    "pagué 2800 de pasaje en transmilenio",
    "me gasté 15000 en una cerveza",
    "recibí 20000 de mesada",
    "gasté 4000 en una empanada",
]

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=10)
ap.add_argument("--start", type=int, default=101, help="primer sequence")
ap.add_argument("--url", default="http://127.0.0.1:8000/api/v1/finagotchi/telemetry")
args = ap.parse_args()

ultimo = None
for i in range(args.n):
    seq = args.start + i
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    mid = f"{DEVICE_ID}-{int(time.time())}-{seq:04d}"
    payload = {
        "message_id": mid,
        "device_id": DEVICE_ID,
        "timestamp": ts,
        "sequence": seq,
        "measurements": {
            "button_state": True,
            "audio_duration_sec": 2.5,
            "raw_voice_text": FRASES[i % len(FRASES)],
        },
    }
    r = requests.post(args.url, json=payload, timeout=(3, 5))
    d = r.json()
    print(f"[{i+1:02d}] POST -> HTTP {r.status_code} | sequence={seq} | "
          f"{d.get('transaction_type')} ${d.get('monto', 0):,.0f} {d.get('category')}")
    print(f"     message_id={mid}")
    ultimo = mid
    time.sleep(1.1)  # evita message_id repetido

print("\nComandos para trazar la última lectura (A7):")
print(f"  sqlite3 -header -column finagotchi.db \"SELECT id,message_id,device_id,sequence,transaction_type,amount,category FROM transacciones WHERE message_id='{ultimo}';\"")
print(f"  curl -s \"http://127.0.0.1:8000/api/measurements?device_id={DEVICE_ID}&limit=10\" | python3 -m json.tool")
