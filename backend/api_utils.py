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


def datos_entrantes():
    """Devuelve los datos del request tanto en JSON como en formulario.

    Permite que un mismo endpoint acepte ``application/json`` y
    ``multipart/form-data`` (audio). Los campos de texto del formulario
    ganan sobre el JSON porque solo hay un tipo de contenido por request.
    """
    from flask import request

    data = dict(request.get_json(silent=True) or {})
    for key in request.form:
        data.setdefault(key, request.form.get(key))
    return data


def require_fields(data, fields):
    missing = [field for field in fields if data.get(field) in (None, "")]
    return missing
