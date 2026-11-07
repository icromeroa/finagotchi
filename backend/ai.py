"""Proveedor de transcripcion de audio.

Reglas del proyecto:
- El backend es el unico que ve la API key.
- La key vive FUERA del repositorio, en ``%USERPROFILE%/.finagotchi/gemini.env``.
  Asi un ``git clean -xdf`` no puede borrarla.
- El audio se procesa en memoria y nunca se guarda en disco ni en la base.
- El proveedor solo transcribe. La interpretacion de montos, categorias y
  cuentas sigue a cargo de ``backend/nlp.py`` por reglas.

Proveedores:

- ``gemini``: API de Google. Necesita ``GEMINI_API_KEY``.
- ``local``: faster-whisper corriendo en el PC del backend. No necesita clave,
  ni cuota, ni conexion a Internet.
- ``auto`` (por defecto): usa Gemini si hay clave y responde; si la clave
  esta rota, no hay cuota o el proveedor falla, cae al modelo local.
"""

import base64
import io
import os
import time
import wave
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

PROVEEDOR_GEMINI = "gemini"
PROVEEDOR_LOCAL = "local"
PROVEEDOR_AUTO = "auto"
MODELOS_LOCALES = ("tiny", "base", "small", "medium", "large-v3")
IDIOMA_WHISPER = {"es-CO": "es", "es": "es"}

PROVEEDOR_LLM_OLLAMA = "ollama"
PROVEEDOR_LLM_GEMINI = "gemini"
OLLAMA_URL_POR_DEFECTO = "http://127.0.0.1:11434"
MODELO_OLLAMA_POR_DEFECTO = "qwen3:4b"

PROMPT_TRANSCRIPCION = (
    "Transcribe literalmente el audio en espanol colombiano. "
    "Devuelve solo el texto transcrito, sin resumen, sin explicaciones y sin "
    "inventar datos. Conserva los montos, los nombres de cuentas y las "
    "expresiones tal como se dicen, con tildes y signos de puntuacion naturales."
)


def prompt_con_hotwords(initial_prompt=None):
    """Prompt de transcripcion con las palabras del usuario como pista."""
    if not initial_prompt:
        return PROMPT_TRANSCRIPCION
    return (
        f"{PROMPT_TRANSCRIPCION} "
        f"Estos nombres pueden aparecer en el audio, escribelos tal cual: {initial_prompt}."
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


class STTKeyInvalida(ErrorSTT):
    """Google rechazo la credencial.

    Desde el 28 de mayo de 2026 AI Studio emite "Auth keys" (``AQ.Ab...``) en
    lugar de las estandar (``AIza...``). Hay un problema abierto de
    compatibilidad: esas claves responden ``401 UNAUTHENTICATED`` con motivo
    ``ACCESS_TOKEN_TYPE_UNSUPPORTED`` en ``generativelanguage.googleapis.com``.
    """

    codigo = "STT_KEY_INVALIDA"
    estado_http = 502


class STTSinPermisos(ErrorSTT):
    """La credencial es valida pero no tiene acceso al modelo."""

    codigo = "STT_SIN_PERMISOS"
    estado_http = 502


class STTNoDisponible(ErrorSTT):

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


def proveedor_preferido():
    """Proveedor de transcripcion elegido por configuracion."""
    return (os.environ.get("STT_PROVEEDOR") or PROVEEDOR_AUTO).strip().lower()


def modelo_local():
    return (os.environ.get("STT_MODELO_LOCAL") or "base").strip()


def local_disponible():
    """True si faster-whisper esta instalado en el equipo."""
    try:
        import faster_whisper  # noqa: F401
    except ImportError:
        return False
    return True


def url_ollama():
    return (os.environ.get("OLLAMA_URL") or OLLAMA_URL_POR_DEFECTO).rstrip("/")


def modelo_ollama():
    return (os.environ.get("OLLAMA_MODEL") or MODELO_OLLAMA_POR_DEFECTO).strip()


def ollama_disponible():
    """True si hay un servidor de Ollama escuchando con el modelo configurado."""
    try:
        import json
        import urllib.request

        with urllib.request.urlopen(f"{url_ollama()}/api/tags", timeout=3) as respuesta:
            datos = json.loads(respuesta.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 - si no hay Ollama, simplemente no esta
        return False
    nombres = {modelo.get("name", "") for modelo in datos.get("models", [])}
    if not nombres:
        return False
    objetivo = modelo_ollama()
    return any(nombre == objetivo or nombre.startswith(objetivo + ":") for nombre in nombres)


def proveedor_llm():
    """Devuelve el proveedor de LLM disponible: 'ollama', 'gemini' o None."""
    preferido = (os.environ.get("LLM_PROVEEDOR") or "auto").strip().lower()
    if preferido == PROVEEDOR_LLM_OLLAMA:
        return PROVEEDOR_LLM_OLLAMA if ollama_disponible() else None
    if preferido == PROVEEDOR_LLM_GEMINI:
        return PROVEEDOR_LLM_GEMINI if esta_configurado() else None

    if ollama_disponible():
        return PROVEEDOR_LLM_OLLAMA
    if esta_configurado():
        return PROVEEDOR_LLM_GEMINI
    return None


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


def _llamar_gemini(cliente, audio_bytes, mime_type, language, model, con_transcription_config, initial_prompt=None):
    payload = [
        {"type": "text", "text": prompt_con_hotwords(initial_prompt)},
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


def _intentar_modelo(cliente, audio_bytes, mime_type, idioma, model, initial_prompt=None):
    """Llama a Gemini con un modelo. Reintenta sin bloque de transcripcion
    cuando el modelo no acepta ese parametro."""
    try:
        return _llamar_gemini(
            cliente, audio_bytes, mime_type, idioma, model, True, initial_prompt
        )
    except Exception as exc:  # noqa: BLE001
        if _es_error_de_argumento(exc):
            return _llamar_gemini(
                cliente, audio_bytes, mime_type, idioma, model, False, initial_prompt
            )
        raise


def transcribe_audio(
    audio_bytes,
    mime_type="audio/wav",
    language=IDIOMA_POR_DEFECTO,
    model=None,
    initial_prompt=None,
):
    """Transcribe el audio y devuelve un diccionario con la trazabilidad.

    Con ``STT_PROVEEDOR=auto`` usa Gemini cuando hay clave y, si la clave esta
    rota o el proveedor no responde, cae al modelo local del PC.

    ``initial_prompt`` son las "hotwords" del usuario (cuentas y categorias):
    hacen que el modelo escriba bien las marcas y los nombres propios.

    Lanza una subclase de ``ErrorSTT`` si ningun proveedor puede transcribir.
    """
    if not audio_bytes:
        raise STTNoConfigurado("No se recibio audio para transcribir")

    proveedor = proveedor_preferido()
    idioma = (language or IDIOMA_POR_DEFECTO).strip()

    if proveedor == PROVEEDOR_LOCAL:
        return transcribe_local(audio_bytes, idioma, initial_prompt)
    if proveedor == PROVEEDOR_GEMINI:
        return transcribe_gemini(audio_bytes, mime_type, idioma, model, initial_prompt)

    # Modo automatico.
    if not esta_configurado():
        if local_disponible():
            return transcribe_local(audio_bytes, idioma, initial_prompt)
        raise STTNoConfigurado(
            "No hay API key de Gemini ni faster-whisper instalado. "
            "Configura la clave con tools/configurar_api_key.py o instala "
            "faster-whisper para usar el modelo local.",
            detalles={"proveedor_local_disponible": False},
        )

    try:
        return transcribe_gemini(
            audio_bytes, mime_type, idioma, model, initial_prompt
        )
    except (
        STTKeyInvalida,
        STTSinPermisos,
        STTNoConfigurado,
        STTNoDisponible,
        STTCuota,
    ) as exc:
        if not local_disponible():
            raise
        resultado = transcribe_local(audio_bytes, idioma, initial_prompt)
        resultado["motivo_fallback"] = exc.mensaje
        resultado["error_proveedor"] = exc.codigo
        return resultado


PROMPT_EXTRACCION = """Eres un asistente que convierte frases de finanzas personales en datos estructurados.

Categorias disponibles:
{categorias}

Cuentas disponibles:
{cuentas}

Metas activas:
{metas}

Frase del usuario: "{texto}"

Responde SOLO con un JSON valido, sin texto antes ni despues:
{{"tipo": "gasto|ingreso|ahorro", "monto": <numero entero o null>, "categoria": "<nombre exacto de la lista o null>", "cuenta": "<nombre exacto de la lista o null>", "meta": "<nombre exacto de la lista o null>", "concepto": "<resumen breve en menos de 8 palabras>"}}

Reglas:
- "tipo" es "gasto", "ingreso" o "ahorro".
- "monto" es el valor total en pesos enteros, sin punto ni signo. Si la frase no menciona un monto, pon null.
- "categoria" y "cuenta" deben ser EXACTAMENTE un nombre de las listas de arriba, en minúsculas. Si la frase no lo menciona, pon null. Si no sabes con certeza, pon null.
- "meta" solo aplica cuando el usuario dice que el ahorro es para una meta. Debe ser EXACTAMENTE un nombre de la lista de metas. Si no hay coincidencia segura, pon null.
- Si la frase menciona varias categorias, cuentas o metas, escoge la mas probable.
- No inventes categorias, cuentas ni metas que no esten en las listas.
"""


def _armar_prompt_extraccion(texto, categorias, cuentas, metas=None):
    lineas_categorias = "\n".join(
        f"- {categoria['nombre']} ({categoria['tipo']})" for categoria in categorias
    )
    lineas_cuentas = "\n".join(f"- {cuenta['nombre']}" for cuenta in cuentas)
    lineas_metas = "\n".join(f"- {meta['nombre']}" for meta in (metas or []))
    return PROMPT_EXTRACCION.format(
        categorias=lineas_categorias or "(ninguna)",
        cuentas=lineas_cuentas or "(ninguna)",
        metas=lineas_metas or "(ninguna)",
        texto=str(texto).replace('"', "'"),
    )


def _json_de_texto(texto):
    """Saca el JSON de una respuesta del modelo, aunque venga con texto extra."""
    import json

    if not texto:
        return None
    limpio = texto.strip()
    if limpio.startswith("```"):
        limpio = limpio.strip("`")
        if limpio.lower().startswith("json"):
            limpio = limpio[4:]
    limpio = limpio.strip()
    try:
        return json.loads(limpio)
    except ValueError:
        pass
    inicio = limpio.find("{")
    fin = limpio.rfind("}")
    if inicio != -1 and fin > inicio:
        try:
            return json.loads(limpio[inicio : fin + 1])
        except ValueError:
            return None
    return None


def extraer_estructura(texto, categorias, cuentas, metas=None, modelo=None):
    """Pide a un LLM que extraiga tipo, monto, categoria, cuenta y meta.

    Devuelve un diccionario con los datos crudos del modelo, o None si no hay
    ningun LLM disponible o si la respuesta no es utilizable.
    """
    proveedor = proveedor_llm()
    if proveedor is None:
        return None

    prompt = _armar_prompt_extraccion(texto, categorias, cuentas, metas)
    started = time.perf_counter()

    if proveedor == PROVEEDOR_LLM_OLLAMA:
        respuesta = _extraer_con_ollama(prompt, modelo)
    else:
        respuesta = _extraer_con_gemini(prompt)

    if not respuesta:
        return None

    respuesta["proveedor"] = proveedor
    respuesta["latencia_ms"] = int((time.perf_counter() - started) * 1000)
    return respuesta


INTENCIONES_CONVERSACION = (
    "registrar_movimiento",
    "crear_meta",
    "actualizar_meta",
    "consultar_balance",
    "consultar_metas",
    "consultar_plan",
    "consultar_cuentas",
    "consultar_categorias",
    "consultar_movimientos",
    "consultar_presupuesto",
    "consultar_perfil",
    "editar_movimiento",
    "eliminar_movimiento",
    "crear_cuenta",
    "crear_categoria",
    "actualizar_presupuesto",
    "actualizar_perfil",
    "eliminar_meta",
    "confirmar",
    "cancelar",
    "corregir",
    "cerrar_dia",
    "ayuda",
    "desconocido",
)

PROMPT_CONVERSACION = """Eres el interprete de FinaGotchi, un asistente financiero por voz.
No respondes al usuario: solo clasificas la frase y extraes datos.

Fecha local actual: {fecha}
Estado de la conversacion: {estado}
Accion pendiente: {accion_pendiente}
Borrador de meta: {borrador}

Metas del usuario:
{metas}

Cuentas del usuario:
{cuentas}

Categorias del usuario:
{categorias}

Frase del usuario: "{texto}"

Responde SOLO con un JSON valido, sin texto antes ni despues:
{{"intent": "<intencion>", "entidades": {{...}}, "confianza": <numero entre 0 y 1>}}

Intenciones permitidas:
- registrar_movimiento: gasto, ingreso o ahorro con un monto.
- crear_meta: el usuario quiere plantear una meta nueva.
- actualizar_meta: el usuario responde con un dato de la meta que se esta creando.
- consultar_balance: como me fue, balance, totales de un dia o rango. Copia la expresion temporal en entidades.fecha_texto.
- consultar_metas: como van mis metas.
- consultar_plan: cuanto debo ahorrar o que plan recomienda.
- consultar_cuentas, consultar_categorias, consultar_movimientos,
  consultar_presupuesto, consultar_perfil: consultas del catalogo o del perfil.
  En consultar_movimientos copia en entidades.fecha_texto la expresion temporal
  si el usuario la menciona ("ayer", "esta semana", "del 3 al 5 de mayo").
- editar_movimiento: cambiar monto, categoria, cuenta o meta de un movimiento.
- eliminar_movimiento: borrar o anular un movimiento.
- crear_cuenta: crear una cuenta nueva.
- crear_categoria: crear una categoria nueva.
- actualizar_presupuesto: cambiar el presupuesto diario.
- actualizar_perfil: cambiar el ingreso mensual declarado.
- eliminar_meta: borrar una meta existente.
- confirmar: acepta la accion o propuesta pendiente.
- cancelar: descarta la accion pendiente.
- corregir: quiere cambiar un dato de la accion pendiente.
- cerrar_dia: cerrar o terminar el dia.
- ayuda: pide saber que puede decir.
- desconocido: no se entiende.

Entidades posibles (usa null cuando no aparezcan):
tipo ("gasto", "ingreso" o "ahorro"), monto (entero en pesos), categoria,
cuenta, meta, nombre (de la meta), plazo_meses (entero), plazo_dias (entero),
frecuencia ("diaria", "semanal", "quincenal" o "mensual"), prioridad (1 a 5),
periodo ("hoy", "semana" o "mes"), fecha_texto (la expresion temporal tal como
la dijo el usuario), alcance ("dia", "semana", "mes" o "rango"), concepto,
tipo_cuenta ("efectivo", "billetera_digital", "tarjeta", "cuenta_ahorros" o
"inversion").

Reglas:
- No inventes montos, fechas, nombres, cuentas ni metas.
- No calcules fechas ni aportes: solo extrae lo que el usuario dijo en fecha_texto.
  El backend convierte esa expresion a fechas reales.
- "esta semana" siempre significa de lunes a hoy; "la semana pasada" es la
  semana anterior completa.
- Si dice "gaste ayer", "que gaste ayer" o "mis gastos de ayer" sin monto, es
  consultar_movimientos (o consultar_balance si pide el total) con
  fecha_texto = "ayer". Si incluye un monto, es registrar_movimiento con
  fecha_texto = "ayer".
- Si la frase es una respuesta corta a una pregunta pendiente, usa el estado y el borrador para clasificarla.
- "ahorre", "guarde" o "separe" con monto es registrar_movimiento con tipo "ahorro".
- Si el usuario dice "para mi meta de ..." incluye meta y tipo "ahorro".
- Los nombres de categoria, cuenta y meta deben copiarse exactamente de las listas.
"""


def _armar_prompt_conversacion(texto, contexto=None):
    import json

    contexto = contexto or {}
    metas = contexto.get("metas") or []
    cuentas = contexto.get("cuentas") or []
    categorias = contexto.get("categorias") or []
    return PROMPT_CONVERSACION.format(
        fecha=contexto.get("fecha") or "",
        estado=contexto.get("estado") or "inactiva",
        accion_pendiente=json.dumps(
            contexto.get("accion_pendiente"), ensure_ascii=False, default=str
        ),
        borrador=json.dumps(contexto.get("borrador"), ensure_ascii=False, default=str),
        metas="\n".join(f"- {item['nombre']}" for item in metas) or "(ninguna)",
        cuentas="\n".join(f"- {item['nombre']}" for item in cuentas) or "(ninguna)",
        categorias="\n".join(
            f"- {item['nombre']} ({item.get('tipo')})" for item in categorias
        )
        or "(ninguna)",
        texto=str(texto).replace('"', "'"),
    )


def interpretar_conversacion(texto, contexto=None, modelo=None):
    """Clasifica una frase conversacional y extrae sus entidades.

    El LLM solo interpreta. La validacion, el calculo de fechas y la ejecucion
    quedan a cargo de ``backend/conversation.py``.

    Devuelve ``None`` si no hay proveedor disponible o si la respuesta no es
    un objeto JSON utilizable.
    """
    proveedor = proveedor_llm()
    if proveedor is None:
        return None

    prompt = _armar_prompt_conversacion(texto, contexto)
    started = time.perf_counter()
    try:
        if proveedor == PROVEEDOR_LLM_OLLAMA:
            respuesta = _extraer_con_ollama(prompt, modelo)
        else:
            respuesta = _conversar_con_gemini(prompt)
    except ErrorSTT:
        return None

    if not isinstance(respuesta, dict):
        return None
    intent = str(respuesta.get("intent") or "").strip().lower()
    if intent not in INTENCIONES_CONVERSACION:
        return None
    entidades = respuesta.get("entidades")
    if not isinstance(entidades, dict):
        entidades = {}
    try:
        confianza = float(respuesta.get("confianza"))
    except (TypeError, ValueError):
        confianza = None
    return {
        "intent": intent,
        "entidades": entidades,
        "confianza": max(0.0, min(1.0, confianza)) if confianza is not None else None,
        "proveedor": proveedor,
        "modelo": modelo or (modelo_ollama() if proveedor == PROVEEDOR_LLM_OLLAMA else None),
        "latencia_ms": int((time.perf_counter() - started) * 1000),
    }


def _conversar_con_gemini(prompt):
    if not api_key():
        return None
    try:
        from google import genai
        from google.genai import types

        cliente = genai.Client(api_key=api_key())
        respuesta = cliente.models.generate_content(
            model=modelo(),
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0,
            ),
        )
    except Exception as exc:  # noqa: BLE001
        raise ErrorSTT(
            "Gemini no pudo interpretar la conversacion",
            detalles={"proveedor": PROVEEDOR_LLM_GEMINI, "motivo": str(exc)[:300]},
        ) from exc
    return _json_de_texto(getattr(respuesta, "text", None))


def _extraer_con_ollama(prompt, modelo=None):
    import json
    import urllib.request

    cuerpo = {
        "model": modelo or modelo_ollama(),
        "messages": [{"role": "user", "content": prompt}],
        "format": "json",
        "stream": False,
        # Sin esto los modelos con "modo pensar" se demoran 30 s o mas.
        "think": False,
        # Mantiene el modelo en memoria entre peticiones.
        "keep_alive": "10m",
        "options": {"temperature": 0, "num_predict": 200},
    }

    def enviar(cuerpo_enviado):
        peticion = urllib.request.Request(
            f"{url_ollama()}/api/chat",
            data=json.dumps(cuerpo_enviado).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(peticion, timeout=120) as respuesta:
            return json.loads(respuesta.read().decode("utf-8"))

    try:
        datos = enviar(cuerpo)
    except urllib.error.HTTPError as exc:
        if exc.code == 400:
            # Versiones antiguas de Ollama no conocen el parametro think.
            cuerpo.pop("think", None)
            try:
                datos = enviar(cuerpo)
            except Exception as exc2:  # noqa: BLE001
                raise ErrorSTT(
                    "Ollama no pudo responder",
                    detalles={
                        "proveedor": PROVEEDOR_LLM_OLLAMA,
                        "motivo": str(exc2)[:300],
                    },
                ) from exc2
        else:
            raise ErrorSTT(
                "Ollama no pudo responder",
                detalles={
                    "proveedor": PROVEEDOR_LLM_OLLAMA,
                    "motivo": f"HTTP {exc.code}: {str(exc)[:200]}",
                },
            ) from exc
    except Exception as exc:  # noqa: BLE001
        raise ErrorSTT(
            "Ollama no pudo responder",
            detalles={"proveedor": PROVEEDOR_LLM_OLLAMA, "motivo": str(exc)[:300]},
        ) from exc

    mensaje = datos.get("message") or {}
    contenido = mensaje.get("content") or ""
    if not contenido and mensaje.get("thinking"):
        contenido = mensaje["thinking"]
    return _json_de_texto(contenido)


def _extraer_con_gemini(prompt):
    if not api_key():
        return None
    try:
        from google import genai
        from google.genai import types

        cliente = genai.Client(api_key=api_key())
        esquema = {
            "type": "object",
            "properties": {
                "tipo": {"type": "string", "enum": ["gasto", "ingreso", "ahorro"]},
                "monto": {"type": "integer", "nullable": True},
                "categoria": {"type": "string", "nullable": True},
                "cuenta": {"type": "string", "nullable": True},
                "meta": {"type": "string", "nullable": True},
                "concepto": {"type": "string"},
            },
            "required": ["tipo", "monto", "categoria", "cuenta", "meta", "concepto"],
        }
        respuesta = cliente.models.generate_content(
            model=modelo or modelo(),
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=esquema,
                temperature=0,
            ),
        )
    except Exception as exc:  # noqa: BLE001
        raise ErrorSTT(
            "Gemini no pudo extraer la estructura",
            detalles={"proveedor": PROVEEDOR_LLM_GEMINI, "motivo": str(exc)[:300]},
        ) from exc
    return _json_de_texto(getattr(respuesta, "text", None))


def _wav_a_float32(audio_bytes):
    """Convierte un WAV 16 bits mono en un arreglo float32 para whisper."""
    import numpy as np

    with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
        frames = wav_file.readframes(wav_file.getnframes())
    return np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0


def transcribe_local(audio_bytes, language=IDIOMA_POR_DEFECTO, initial_prompt=None):
    """Transcribe el audio con faster-whisper corriendo en el PC.

    No necesita clave de API, ni cuota, ni conexion a Internet. El modelo se
    descarga la primera vez y queda en la cache de HuggingFace.
    """
    if not local_disponible():
        raise STTNoConfigurado(
            "faster-whisper no esta instalado. Instalalo con: "
            "py -3 -m pip install faster-whisper",
            detalles={"proveedor": PROVEEDOR_LOCAL},
        )

    started = time.perf_counter()
    try:
        import numpy as np
        from faster_whisper import WhisperModel
    except ImportError as exc:  # pragma: no cover - depende del entorno
        raise STTNoConfigurado(
            "faster-whisper no esta instalado", detalles={"motivo": str(exc)}
        ) from exc

    try:
        muestras = _wav_a_float32(audio_bytes)
    except wave.Error as exc:
        raise ErrorSTT(
            "El audio no se pudo leer para la transcripcion local",
            detalles={"motivo": str(exc)},
        ) from exc

    idioma = IDIOMA_WHISPER.get(language, "es")

    try:
        modelo = _modelo_whisper()
        opciones = {"language": idioma, "beam_size": 1, "vad_filter": True}
        if initial_prompt:
            # Las "hotwords" corrigen marcas y nombres propios: sin esto,
            # whisper escribe "por Nike" en vez de "por Nequi".
            opciones["initial_prompt"] = initial_prompt
        segmentos, _info = modelo.transcribe(muestras, **opciones)
        texto = " ".join(segmento.text for segmento in segmentos)
    except Exception as exc:  # noqa: BLE001
        raise ErrorSTT(
            "El modelo local fallo al transcribir",
            detalles={"modelo": modelo_local(), "motivo": str(exc)[:300]},
        ) from exc

    latencia_ms = int((time.perf_counter() - started) * 1000)
    limpio = _limpiar_texto(texto)
    if not limpio:
        raise STTSinTexto(
            "El modelo local no devolvio texto para este audio",
            detalles={"modelo": modelo_local(), "latencia_ms": latencia_ms},
        )
    return {
        "texto": limpio,
        "modelo": f"whisper-{modelo_local()}",
        "proveedor": PROVEEDOR_LOCAL,
        "latencia_ms": latencia_ms,
        "tokens_entrada": None,
        "tokens_salida": None,
        "idioma": idioma,
    }


_MODELO_WHISPER = None


def _modelo_whisper():
    """Carga el modelo una sola vez y lo reutiliza entre peticiones."""
    global _MODELO_WHISPER
    if _MODELO_WHISPER is None:
        from faster_whisper import WhisperModel

        tamano = modelo_local()
        _MODELO_WHISPER = WhisperModel(tamano, device="cpu", compute_type="int8")
    return _MODELO_WHISPER


def transcribe_gemini(
    audio_bytes,
    mime_type="audio/wav",
    language=IDIOMA_POR_DEFECTO,
    model=None,
    initial_prompt=None,
):
    """Transcribe el audio con Gemini Flash."""
    if not api_key():
        raise STTNoConfigurado(
            "Falta configurar GEMINI_API_KEY en el backend",
            detalles={"archivo": str(ARCHIVO_EXTERNO)},
        )

    cliente = _cliente()
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
                    cliente, audio_bytes, mime_type, language, candidato, initial_prompt
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
        "proveedor": PROVEEDOR_GEMINI,
        "latencia_ms": latencia_ms,
        "tokens_entrada": tokens_entrada,
        "tokens_salida": tokens_salida,
        "idioma": language,
    }


def _esperar(intento):
    espera = ESPERA_INICIAL_S * (2 ** (intento - 1))
    time.sleep(min(espera, 8))


def _convertir_error(exc, modelo_usado):
    codigo = getattr(exc, "code", None)
    texto = str(exc).upper()
    motivo = getattr(exc, "message", None) or str(exc)[:300]

    if codigo == 401 or "UNAUTHENTICATED" in texto:
        prefijo = api_key()[:4]
        raise STTKeyInvalida(
            "Google rechazo la API key (401). Las claves AQ.Ab que crea AI Studio "
            "desde mayo de 2026 estan fallando con ACCESS_TOKEN_TYPE_UNSUPPORTED. "
            "Opciones: usar una clave Standard (AIza) de otro proyecto, pedir "
            "revision de la cuenta a Google, o activar el proveedor local.",
            detalles={
                "modelo": modelo_usado,
                "motivo": str(motivo)[:300],
                "prefijo_clave": prefijo,
                "formato_clave": "AQ" if prefijo.startswith("AQ") else "AIza",
            },
        ) from exc
    if codigo == 403 or "PERMISSION_DENIED" in texto:
        raise STTSinPermisos(
            "La API key no tiene permiso para usar el modelo. Revisa que la "
            "Generative Language API este habilitada en el proyecto de Google.",
            detalles={"modelo": modelo_usado, "motivo": str(motivo)[:300]},
        ) from exc
    if codigo == 429 or "RESOURCE_EXHAUSTED" in texto:
        raise STTCuota(
            "El proveedor alcanzo su limite de peticiones",
            detalles={"modelo": modelo_usado},
        ) from exc
    if codigo in (500, 502, 503, 504) or "UNAVAILABLE" in texto:
        raise STTNoDisponible(
            "El proveedor de transcripcion no esta disponible",
            detalles={"modelo": modelo_usado},
        ) from exc
    raise ErrorSTT(
        "El proveedor de transcripcion fallo",
        detalles={"modelo": modelo_usado, "motivo": str(motivo)[:300]},
    ) from exc
