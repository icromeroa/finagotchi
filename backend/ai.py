"""Proveedor de transcripcion de audio con Gemini.

Reglas del proyecto:
- El backend es el unico que ve la API key.
- La key vive FUERA del repositorio, en ``%USERPROFILE%/.finagotchi/gemini.env``.
  Asi un ``git clean -xdf`` no puede borrarla.
- El audio se procesa en memoria y nunca se guarda en disco ni en la base.
- Gemini solo transcribe. La interpretacion de montos, categorias y cuentas
  sigue a cargo de ``backend/nlp.py`` por reglas.
"""

import base64
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARPETA_PERSONAL = Path.home() / ".finagotchi"
ARCHIVO_EXTERNO = CARPETA_PERSONAL / "gemini.env"
MODELO_POR_DEFECTO = "gemini-3.8-flash"
MODELOS_RESPALDO = ("gemini-3.5-flash", "gemini-3.5-flash-lite")
IDIOMA_POR_DEFECTO = "es-CO"
TIMEOUT_S = 60
MAX_INTENTOS = 2
PLAZO_TOTAL_S = 90
ESPERA_INICIAL_S = 1.5
MAX_TEXTO = 2000

PROMPT_TRANSCRIPCION = (
    "Transcribe literalmente el audio en espanol colombiano. "
    "Devuelve solo el texto transcrito, sin resumen, sin explicaciones y sin "
    "inventar datos. Conserva los montos, los nombres de cuentas y las "
    "expresiones tal como se dicen, con tildes y signos de puntuacion naturales."
)


class ErrorSTT(RuntimeError):
    """Error generico del proveedor de transcripcion."""

    codigo = "STT_ERROR"
    estado_http = 502

    def __init__(self, mensaje, codigo=None, estado_http=None, detalles=None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        if codigo:
            self.codigo = codigo
        if estado_http:
            self.estado_http = estado_http
        self.detalles = detalles or {}


class STTNoConfigurado(ErrorSTT):
    """Falta la API key o el paquete de Google."""

    codigo = "STT_NO_CONFIGURADO"
    estado_http = 503


class STTCuota(ErrorSTT):
    """El proveedor rechazo la peticion por limite de cuota."""

    codigo = "STT_CUOTA"
    estado_http = 429


class STTNoDisponible(ErrorSTT):
    """El proveedor no esta disponible en este momento."""

    codigo = "STT_NO_DISPONIBLE"
    estado_http = 502


class STTSinTexto(ErrorSTT):
    """El audio se proceso pero no se obtuvo texto utilizable."""

    codigo = "STT_SIN_TEXTO"
    estado_http = 422


def rutas_env():
    """Rutas donde puede estar la configuracion, en orden de prioridad.

    1. ``backend/.env`` dentro del repo (ignorado por git, se puede borrar).
    2. ``.env`` en la raiz del repo (ignorado por git, se puede borrar).
    3. ``%USERPROFILE%/.finagotchi/gemini.env`` FUERA del repo (a salvo de
       ``git clean`` y de reinstalar el proyecto).

    La variable de entorno del sistema gana sobre todas: si ya esta definida,
    no se toca.
    """
    return (
        Path(__file__).resolve().parent / ".env",
        ROOT / ".env",
        ARCHIVO_EXTERNO,
    )


def _cargar_env():
    """Carga los archivos .env disponibles sin sobrescribir variables ya fijadas."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return []
    cargados = []
    for candidate in rutas_env():
        if candidate.exists():
            try:
                load_dotenv(candidate, override=False)
            except Exception:  # noqa: BLE001 - un .env roto no debe tumbar el backend
                continue
            cargados.append(candidate)
    return cargados


_KEY_DEL_ENTORNO = bool(os.environ.get("GEMINI_API_KEY"))
ARCHIVOS_CARGADOS = _cargar_env()


def origen_de_la_key():
    """De donde viene la API key: 'variable de entorno', la ruta del archivo o None."""
    if _KEY_DEL_ENTORNO:
        return "variable de entorno"
    for candidate in rutas_env():
        if candidate.exists():
            try:
                # utf-8-sig tolera el BOM que agregan algunos editores.
                for linea in candidate.read_text(encoding="utf-8-sig").splitlines():
                    if linea.strip().startswith("GEMINI_API_KEY="):
                        if linea.split("=", 1)[1].strip():
                            return str(candidate)
            except OSError:
                continue
    return None


def api_key():
    return (os.environ.get("GEMINI_API_KEY") or "").strip()


def modelo():
    return (os.environ.get("GEMINI_MODEL") or MODELO_POR_DEFECTO).strip()


def timeout_s():
    try:
        return float(os.environ.get("GEMINI_TIMEOUT_S") or TIMEOUT_S)
    except ValueError:
        return TIMEOUT_S


def plazo_total_s():
    try:
        return float(os.environ.get("GEMINI_PLAZO_S") or PLAZO_TOTAL_S)
    except ValueError:
        return PLAZO_TOTAL_S


def esta_configurado():
    return bool(api_key())


def _cliente():
    try:
        from google import genai
    except ImportError as exc:  # pragma: no cover - depende del entorno
        raise STTNoConfigurado(
            "El paquete google-genai no esta instalado", detalles={"motivo": str(exc)}
        ) from exc

    return genai.Client(api_key=api_key())


def cadena_modelos(model=None):
    """Modelos a probar en orden: el configurado y sus respaldos."""
    principal = (model or modelo()).strip()
    cadena = [principal]
    extras = os.environ.get("GEMINI_MODEL_FALLBACKS") or ""
    for candidato in extras.split(","):
        candidato = candidato.strip()
        if candidato and candidato not in cadena:
            cadena.append(candidato)
    for defecto in MODELOS_RESPALDO:
        if defecto not in cadena:
            cadena.append(defecto)
    return cadena


def _es_error_transitorio(exc):
    codigo = getattr(exc, "code", None)
    if isinstance(codigo, int) and codigo in (500, 502, 503, 504):
        return True
    nombre = type(exc).__name__
    if "ServerError" in nombre or "ServiceUnavailable" in nombre:
        return True
    if "Timeout" in nombre or "Connect" in nombre:
        return True
    texto = str(exc).upper()
    return "UNAVAILABLE" in texto or "HIGH DEMAND" in texto


def _es_modelo_no_disponible(exc):
    codigo = getattr(exc, "code", None)
    if codigo == 404:
        return True
    return "NO LONGER AVAILABLE" in str(exc).upper()


def _es_error_de_argumento(exc):
    codigo = getattr(exc, "code", None)
    if codigo in (400, 422):
        return True
    nombre = type(exc).__name__
    return "InvalidArgument" in nombre or "BadRequest" in nombre


def _tokens(usage):
    if usage is None:
        return None, None
    entrada = getattr(usage, "total_input_tokens", None)
    salida = getattr(usage, "total_output_tokens", None)
    return entrada, salida


def _limpiar_texto(texto):
    if not texto:
        return ""
    limpio = texto.strip()
    if limpio.startswith("```"):
        limpio = limpio.strip("`")
        if limpio.lower().startswith("text"):
            limpio = limpio[4:]
    if limpio.startswith('"') and limpio.endswith('"') and len(limpio) > 1:
        limpio = limpio[1:-1]
    limpio = " ".join(limpio.split())
    return limpio[:MAX_TEXTO]


def _llamar_gemini(cliente, audio_bytes, mime_type, language, model, con_transcription_config):
    payload = [
        {"type": "text", "text": PROMPT_TRANSCRIPCION},
        {
            "type": "audio",
            "data": base64.b64encode(audio_bytes).decode("ascii"),
            "mime_type": mime_type,
        },
    ]
    kwargs = {"model": model, "input": payload, "timeout": timeout_s()}
    if con_transcription_config:
        kwargs["generation_config"] = {
            "transcription": {"language_codes": [language], "mode": "verbatim"}
        }
    return cliente.interactions.create(**kwargs)


def _intentar_modelo(cliente, audio_bytes, mime_type, idioma, model):
    """Llama a Gemini con un modelo. Reintenta sin bloque de transcripcion
    cuando el modelo no acepta ese parametro."""
    try:
        return _llamar_gemini(cliente, audio_bytes, mime_type, idioma, model, True)
    except Exception as exc:  # noqa: BLE001
        if _es_error_de_argumento(exc):
            return _llamar_gemini(cliente, audio_bytes, mime_type, idioma, model, False)
        raise


def transcribe_audio(
    audio_bytes,
    mime_type="audio/wav",
    language=IDIOMA_POR_DEFECTO,
    model=None,
):
    """Transcribe el audio y devuelve un diccionario con la trazabilidad.

    Lanza una subclase de ``ErrorSTT`` si el proveedor no esta disponible o no
    devuelve texto utilizable.
    """
    if not api_key():
        raise STTNoConfigurado(
            "Falta configurar GEMINI_API_KEY en el backend",
            detalles={"archivo": "backend/.env"},
        )
    if not audio_bytes:
        raise STTNoConfigurado("No se recibio audio para transcribir")

    cliente = _cliente()
    idioma = (language or IDIOMA_POR_DEFECTO).strip()
    cadena = cadena_modelos(model)

    started = time.perf_counter()
    ultimo_error = None
    modelo_usado = cadena[0]
    interaccion = None

    for intento in range(1, MAX_INTENTOS + 1):
        for candidato in cadena:
            if time.perf_counter() - started > plazo_total_s():
                raise STTNoDisponible(
                    "El proveedor de transcripcion tardo demasiado en responder",
                    detalles={"modelo": modelo_usado, "plazo_s": plazo_total_s()},
                )
            modelo_usado = candidato
            try:
                interaccion = _intentar_modelo(
                    cliente, audio_bytes, mime_type, idioma, candidato
                )
            except Exception as exc:  # noqa: BLE001 - se clasifica mas abajo
                ultimo_error = exc
                if _es_modelo_no_disponible(exc) or _es_error_transitorio(exc):
                    continue
                _convertir_error(exc, candidato)
            else:
                break
        else:
            if intento < MAX_INTENTOS:
                _esperar(intento)
                continue
            _convertir_error(ultimo_error, modelo_usado)
        break

    latencia_ms = int((time.perf_counter() - started) * 1000)
    texto = _limpiar_texto(getattr(interaccion, "output_text", None))
    if not texto:
        raise STTSinTexto(
            "El modelo no devolvio texto para este audio",
            detalles={"modelo": modelo_usado, "latencia_ms": latencia_ms},
        )

    tokens_entrada, tokens_salida = _tokens(getattr(interaccion, "usage", None))
    return {
        "texto": texto,
        "modelo": modelo_usado,
        "proveedor": "google",
        "latencia_ms": latencia_ms,
        "tokens_entrada": tokens_entrada,
        "tokens_salida": tokens_salida,
        "idioma": idioma,
    }


def _esperar(intento):
    espera = ESPERA_INICIAL_S * (2 ** (intento - 1))
    time.sleep(min(espera, 8))


def _convertir_error(exc, modelo_usado):
    codigo = getattr(exc, "code", None)
    if codigo == 429 or "RESOURCE_EXHAUSTED" in str(exc).upper():
        raise STTCuota(
            "El proveedor alcanzo su limite de peticiones",
            detalles={"modelo": modelo_usado},
        ) from exc
    if codigo in (500, 502, 503, 504) or "UNAVAILABLE" in str(exc).upper():
        raise STTNoDisponible(
            "El proveedor de transcripcion no esta disponible",
            detalles={"modelo": modelo_usado},
        ) from exc
    raise ErrorSTT(
        "El proveedor de transcripcion fallo",
        detalles={"modelo": modelo_usado, "motivo": str(exc)[:300]},
    ) from exc
