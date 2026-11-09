"""Especificación OpenAPI mostrada por Swagger UI en /docs."""

_ERROR = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "example": "error"},
        "message": {"type": "string"},
    },
}


def _err(desc):
    return {
        "description": desc,
        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}},
    }


OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "FinaGotchi API REST",
        "version": "1.0.0",
        "description": "Consulta de histórico de telemetría (transacciones por voz).",
    },
    "paths": {
        "/health": {
            "get": {
                "summary": "Estado del servicio",
                "responses": {"200": {"description": "Servicio activo"}},
            }
        },
        "/api/measurements": {
            "get": {
                "summary": "Lista mediciones (más recientes primero)",
                "parameters": [
                    {"name": "device_id", "in": "query", "schema": {"type": "string"}, "description": "Filtra por dispositivo"},
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20}},
                    {"name": "offset", "in": "query", "schema": {"type": "integer", "minimum": 0, "default": 0}},
                ],
                "responses": {
                    "200": {
                        "description": "Lista (puede ser vacía)",
                        "content": {"application/json": {"schema": {"type": "array", "items": {"$ref": "#/components/schemas/Measurement"}}}},
                    },
                    "422": _err("limit u offset fuera de rango"),
                },
            }
        },
        "/api/devices": {
            "get": {
                "summary": "Lista dispositivos detectados",
                "responses": {
                    "200": {
                        "description": "Lista de dispositivos",
                        "content": {"application/json": {"schema": {"type": "array", "items": {"$ref": "#/components/schemas/Device"}}}},
                    }
                },
            }
        },
        "/api/devices/{device_id}": {
            "get": {
                "summary": "Resumen de un dispositivo",
                "parameters": [{"name": "device_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {
                    "200": {
                        "description": "Dispositivo encontrado",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Device"}}},
                    },
                    "404": _err("Dispositivo no encontrado"),
                },
            }
        },
    },
    "components": {
        "schemas": {
            "Error": _ERROR,
            "Device": {
                "type": "object",
                "properties": {
                    "device_id": {"type": "string"},
                    "measurement_count": {"type": "integer"},
                    "last_timestamp": {"type": "string"},
                    "last_received_at": {"type": "string", "nullable": True},
                },
            },
            "Measurement": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "message_id": {"type": "string"},
                    "device_id": {"type": "string"},
                    "timestamp": {"type": "string"},
                    "sequence": {"type": "integer", "nullable": True},
                    "measurements": {
                        "type": "object",
                        "properties": {
                            "raw_voice_text": {"type": "string"},
                            "transaction_type": {"type": "string", "enum": ["income", "expense"]},
                            "amount": {"type": "number"},
                            "category": {"type": "string"},
                        },
                    },
                    "received_at": {"type": "string", "nullable": True},
                },
            },
        }
    },
}
