"""Consultas SELECT de la Guía 4 (equivalente a backend/database.py de la guía).

Se llama queries.py para no chocar con la carpeta database/ del proyecto.
"""
import sqlite3


def _connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _to_measurement(row):
    """Convierte una fila de 'transacciones' al formato JSON del contrato."""
    return {
        "id": row["id"],
        "message_id": row["message_id"],
        "device_id": row["device_id"],
        "timestamp": row["timestamp"],
        "sequence": row["sequence"],
        "measurements": {
            "raw_voice_text": row["raw_text"],
            "transaction_type": row["transaction_type"],
            "amount": row["amount"],
            "category": row["category"],
        },
        "received_at": row["received_at"],
    }


def list_measurements(db_path, device_id=None, limit=20, offset=0):
    sql = """
        SELECT id, message_id, device_id, timestamp, sequence, raw_text,
               transaction_type, amount, category, received_at
        FROM transacciones
    """
    params = []
    if device_id:
        sql += " WHERE device_id = ?"
        params.append(device_id)
    sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    conn = _connect(db_path)
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [_to_measurement(r) for r in rows]


_DEVICE_SQL = """
    SELECT device_id,
           COUNT(*) AS measurement_count,
           MAX(timestamp) AS last_timestamp,
           MAX(received_at) AS last_received_at
    FROM transacciones
"""


def list_devices(db_path):
    conn = _connect(db_path)
    rows = conn.execute(
        _DEVICE_SQL + " GROUP BY device_id ORDER BY device_id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_device_summary(db_path, device_id):
    conn = _connect(db_path)
    row = conn.execute(
        _DEVICE_SQL + " WHERE device_id = ? GROUP BY device_id", (device_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None
