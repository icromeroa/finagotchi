"""Pruebas automáticas de la API de consulta (Guía 4).

Usan una base SQLite temporal: no dependen de finagotchi.db.
Ejecutar desde la raíz del proyecto:  python3 -m pytest -q
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import server  # noqa: E402
from database.init_db import init_sqlite  # noqa: E402

DEV_A = "TEST-DEVICE-A"
DEV_B = "TEST-DEVICE-B"


def _post(client, device, seq, text):
    return client.post(
        "/api/v1/finagotchi/telemetry",
        json={
            "message_id": f"{device}-{seq}",
            "device_id": device,
            "timestamp": "2026-10-25T10:00:00Z",
            "sequence": seq,
            "measurements": {"button_state": True, "raw_voice_text": text},
        },
    )


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db = str(tmp_path / "test.db")
    init_sqlite(db)
    monkeypatch.setattr(server, "DB_PATH", db)
    c = server.app.test_client()
    for i in range(1, 13):  # 12 lecturas del dispositivo A
        assert _post(c, DEV_A, i, f"gasté {1000 * i} en el almuerzo").status_code == 201
    for i in range(1, 4):  # 3 lecturas del dispositivo B
        assert _post(c, DEV_B, i, "me pagaron 50000 por un trabajo").status_code == 201
    return c


def test_measurements_returns_200_and_json_list(client):
    r = client.get("/api/measurements")
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list) and len(data) == 15
    assert {"device_id", "sequence", "measurements", "message_id"} <= set(data[0])
    assert isinstance(data[0]["measurements"], dict)


def test_limit_restricts_results(client):
    assert len(client.get("/api/measurements?limit=5").get_json()) == 5


def test_offset_skips_rows(client):
    first = client.get("/api/measurements?limit=5&offset=0").get_json()
    second = client.get("/api/measurements?limit=5&offset=5").get_json()
    assert {m["id"] for m in first}.isdisjoint({m["id"] for m in second})


def test_device_filter(client):
    data = client.get(f"/api/measurements?device_id={DEV_B}").get_json()
    assert len(data) == 3
    assert all(m["device_id"] == DEV_B for m in data)


def test_filter_without_matches_returns_empty_list(client):
    r = client.get("/api/measurements?device_id=NO-EXISTE")
    assert r.status_code == 200
    assert r.get_json() == []


def test_devices_list(client):
    data = client.get("/api/devices").get_json()
    counts = {d["device_id"]: d["measurement_count"] for d in data}
    assert counts == {DEV_A: 12, DEV_B: 3}


def test_device_detail_ok(client):
    r = client.get(f"/api/devices/{DEV_A}")
    assert r.status_code == 200
    assert r.get_json()["measurement_count"] == 12


def test_unknown_device_returns_404(client):
    assert client.get("/api/devices/NO-EXISTE").status_code == 404


@pytest.mark.parametrize("query", ["limit=0", "limit=500", "limit=abc", "offset=-1"])
def test_invalid_params_return_422(client, query):
    assert client.get(f"/api/measurements?{query}").status_code == 422


def test_unknown_route_returns_json_404(client):
    r = client.get("/api/no-existe")
    assert r.status_code == 404
    assert r.get_json()["status"] == "error"


def test_post_still_works_and_duplicate_is_409(client):
    assert _post(client, DEV_A, 99, "gasté 3000 en transporte").status_code == 201
    assert _post(client, DEV_A, 99, "gasté 3000 en transporte").status_code == 409


def test_sequence_is_persisted(client):
    data = client.get(f"/api/measurements?device_id={DEV_A}&limit=1").get_json()
    assert data[0]["sequence"] == 12
