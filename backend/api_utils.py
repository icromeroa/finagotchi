from flask import jsonify


def ok(data=None, status=200, **extra):
    payload = {"ok": True, "data": data if data is not None else {}}
    payload.update(extra)
    return jsonify(payload), status


def error(code, message, status=400, details=None):
    return (
        jsonify(
            {
                "ok": False,
                "error": {
                    "codigo": code,
                    "mensaje": message,
                    "detalles": details or {},
                },
            }
        ),
        status,
    )


def body():
    from flask import request

    return request.get_json(silent=True) or {}


def require_fields(data, fields):
    missing = [field for field in fields if data.get(field) in (None, "")]
    return missing
