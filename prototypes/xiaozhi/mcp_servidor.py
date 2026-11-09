"""Herramienta MCP que conecta Xiaozhi con el puente de FinaGotchi.

Xiaozhi puede cargar este módulo con su ``mcp_pipe.py``. El módulo expone una
sola herramienta conversacional: ``finagotchi_turno``. Xiaozhi le pasa el texto
ya transcrito y recibe la frase que Nancy debe decir.

El backend FinaGotchi sigue siendo la fuente de verdad financiera. Este módulo
solo habla HTTP con ``bridge.py``.

Requisitos:
    pip install "mcp[cli]"

Uso (con el pipe de Xiaozhi):
    python mcp_pipe.py mcp_servidor.py

Variable de entorno:
    XIAOZHI_BRIDGE_URL=http://127.0.0.1:8787
"""

from __future__ import annotations

import json
import os
import sys
from urllib import error, request

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover - solo ocurre sin la dependencia
    FastMCP = None

DEFAULT_BRIDGE_URL = "http://127.0.0.1:8787"
TIMEOUT_S = 90


def _bridge_url():
    return (
        os.environ.get("XIAOZHI_BRIDGE_URL") or DEFAULT_BRIDGE_URL
    ).rstrip("/")


def _llamar(ruta, payload=None):
    url = f"{_bridge_url()}{ruta}"
    cuerpo = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        cuerpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    peticion = request.Request(url, data=cuerpo, headers=headers, method="POST")
    try:
        with request.urlopen(peticion, timeout=TIMEOUT_S) as respuesta:
            return json.loads(respuesta.read().decode("utf-8"))
    except error.HTTPError as exc:
        crudo = exc.read().decode("utf-8", "replace")
        try:
            return json.loads(crudo)
        except ValueError:
            return {
                "ok": False,
                "hablar": "El puente de FinaGotchi respondió con un error.",
                "error": {"codigo": f"HTTP_{exc.code}", "mensaje": crudo},
            }
    except error.URLError as exc:
        return {
            "ok": False,
            "hablar": "No pude conectar con el puente de FinaGotchi.",
            "error": {"codigo": "PUENTE_NO_DISPONIBLE", "mensaje": str(exc.reason)},
        }


def _resultado_hablado(payload):
    """Devuelve solo lo que el agente necesita para hablar y confirmar."""
    return json.dumps(
        {
            "respuesta": payload.get("hablar")
            or payload.get("texto_voz")
            or payload.get("mensaje_nancy")
            or "No recibí respuesta de FinaGotchi.",
            "detalle": payload.get("mensaje_nancy"),
            "tipo_respuesta": payload.get("tipo_respuesta"),
            "requiere_confirmacion": bool(payload.get("requiere_confirmacion")),
            "intent": payload.get("intent"),
            "ok": bool(payload.get("ok", True)),
        },
        ensure_ascii=False,
    )


if FastMCP is not None:
    mcp = FastMCP("FinaGotchi")

    @mcp.tool()
    def finagotchi_turno(texto: str) -> str:
        """Registra, consulta o corrige finanzas en FinaGotchi.

        Envía a FinaGotchi la frase del usuario ya transcrita (por ejemplo
        "gasté 20 mil en almuerzo", "sí", "¿cuánto gasté ayer?" o "cancela").
        Devuelve un JSON. Di literalmente el campo "respuesta" y no inventes
        montos ni fechas. Si "requiere_confirmacion" es true, espera la
        respuesta natural del usuario antes de continuar.
        """
        return _resultado_hablado(_llamar("/turno", {"texto": texto}))

    @mcp.tool()
    def finagotchi_salud() -> str:
        """Comprueba si el puente y el token de FinaGotchi están disponibles."""
        try:
            with request.urlopen(f"{_bridge_url()}/salud", timeout=10) as respuesta:
                return respuesta.read().decode("utf-8")
        except (error.URLError, error.HTTPError) as exc:
            return json.dumps(
                {
                    "ok": False,
                    "error": {
                        "codigo": "PUENTE_NO_DISPONIBLE",
                        "mensaje": str(getattr(exc, "reason", exc)),
                    },
                },
                ensure_ascii=False,
            )


def main():
    if FastMCP is None:
        print(
            "Falta la dependencia MCP. Instala con: pip install \"mcp[cli]\"",
            file=sys.stderr,
        )
        return 2
    mcp.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
