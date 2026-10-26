"""Ejecuta la matriz de pruebas manuales (A4 y A6) y muestra los resultados.

Requiere el backend corriendo.  Uso:  python3 tests/probar_api_manual.py
"""
import sys

import requests

BASE = "http://127.0.0.1:8000"
DEV = "FINAGOTCHI-PC-SIMULATOR-01"

A6 = [
    ("GET /api/measurements", "Consulta válida", 200),
    (f"GET /api/measurements?device_id={DEV}&limit=10", "Filtro por device_id real", 200),
    ("GET /api/measurements?device_id=NO-EXISTE", "Sin coincidencias -> []", 200),
    ("GET /api/devices", "Listar dispositivos", 200),
    (f"GET /api/devices/{DEV}", "Dispositivo real", 200),
    ("GET /api/devices/NO-EXISTE", "Dispositivo inexistente", 404),
    ("GET /api/measurements?limit=0", "Caso negativo: limit=0", 422),
    ("GET /api/measurements?limit=500", "Caso negativo: limit=500", 422),
]
A4 = [
    ("GET /api/measurements?limit=5", "Máximo 5 lecturas", 200),
    ("GET /api/measurements?limit=5&offset=5", "Saltar 5 y traer 5", 200),
    (f"GET /api/measurements?device_id={DEV}&limit=10", "Filtro device_id", 200),
    ("GET /api/measurements?limit=500", "Límite fuera de rango", 422),
]


def correr(titulo, casos):
    print(f"\n=== {titulo} ===")
    print(f"{'SOLICITUD':<68}{'ESP':>5}{'OBT':>5}{'REG':>5}  RESULTADO")
    fallos = 0
    for req, objetivo, esperado in casos:
        r = requests.get(BASE + req.split(" ", 1)[1], timeout=5)
        j = r.json()
        n = len(j) if isinstance(j, list) else (1 if r.status_code == 200 else 0)
        ok = r.status_code == esperado
        fallos += not ok
        print(f"{req:<68}{esperado:>5}{r.status_code:>5}{n:>5}  {'OK' if ok else 'FALLO'}  ({objetivo})")
    return fallos


f = correr("A4 - Filtros y paginación", A4) + correr("A6 - Matriz de pruebas manuales", A6)
a = requests.get(f"{BASE}/api/measurements?limit=5&offset=0").json()
b = requests.get(f"{BASE}/api/measurements?limit=5&offset=5").json()
print("\nids offset=0:", [m["id"] for m in a])
print("ids offset=5:", [m["id"] for m in b])
print("\nRESULTADO FINAL:", "TODO OK" if f == 0 else f"{f} caso(s) fallaron")
sys.exit(1 if f else 0)
