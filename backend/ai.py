"""Proveedor de transcripcion de audio e interpretacion con LLM.

Reglas del proyecto:
- No se usa ningun servicio externo para transcribir: el STT es
  ``faster-whisper`` local en el PC del backend. No necesita clave,
  cuota ni conexion a Internet.
- El audio se procesa en memoria y nunca se guarda en disco ni en la base.
- El proveedor solo transcribe. La interpretacion de montos, categorias y
  cuentas la hace un modelo de lenguaje via Ollama (si esta corriendo)
  con respaldo en las reglas de ``backend/nlp.py``.
"""

import io
import os
import time
import wave

IDIOMA_POR_DEFECTO = "es-CO"
MAX_TEXTO = 2000

PROVEEDOR_LOCAL = "local"
MODELOS_LOCALES = ("tiny", "base", "small", "medium", "large-v3")
IDIOMA_WHISPER = {"es-CO": "es", "es": "es"}

PROVEEDOR_LLM_OLLAMA = "ollama"
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
    """Falta el paquete requerido o no hay modelo disponible."""

    codigo = "STT_NO_CONFIGURADO"
    estado_http = 503


class STTNoDisponible(ErrorSTT):
    codigo = "STT_NO_DISPONIBLE"
    estado_http = 502


class STTSinTexto(ErrorSTT):
    """El audio se proceso pero no se obtuvo texto utilizable."""

    codigo = "STT_SIN_TEXTO"
    estado_http = 422


def proveedor_preferido():
    """Proveedor de transcripcion (siempre local)."""
    return PROVEEDOR_LOCAL


def modelo():
    """Modelo de transcripcion en uso (para auditoria)."""
    return f"whisper-{modelo_local()}"


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
    """Devuelve 'ollama' si Ollama responde con el modelo, o None."""
    if ollama_disponible():
        return PROVEEDOR_LLM_OLLAMA
    return None


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


def transcribe_audio(
    audio_bytes,
    mime_type="audio/wav",
    language=IDIOMA_POR_DEFECTO,
    model=None,
    initial_prompt=None,
):
    """Transcribe el audio con faster-whisper local y devuelve trazabilidad.

    ``initial_prompt`` son las "hotwords" del usuario (cuentas y categorias):
    hacen que el modelo escriba bien las marcas y los nombres propios.
    """
    if not audio_bytes:
        raise STTNoConfigurado("No se recibio audio para transcribir")
    idioma = (language or IDIOMA_POR_DEFECTO).strip()
    return transcribe_local(audio_bytes, idioma, initial_prompt)


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
    """Pide a Ollama que extraiga tipo, monto, categoria, cuenta y meta.

    Devuelve un diccionario con los datos crudos del modelo, o None si no
    hay Ollama disponible o si la respuesta no es utilizable.
    """
    proveedor = proveedor_llm()
    if proveedor is None:
        return None

    prompt = _armar_prompt_extraccion(texto, categorias, cuentas, metas)
    started = time.perf_counter()

    respuesta = _extraer_con_ollama(prompt, modelo)

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
- consultar_pendientes: que tengo pendiente o por confirmar.
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

    Ollama solo interpreta. La validacion, el calculo de fechas y la ejecucion
    quedan a cargo de ``backend/conversation.py``.

    Devuelve ``None`` si no hay Ollama disponible o si la respuesta no es
    un objeto JSON utilizable.
    """
    proveedor = proveedor_llm()
    if proveedor is None:
        return None

    prompt = _armar_prompt_conversacion(texto, contexto)
    started = time.perf_counter()
    try:
        respuesta = _extraer_con_ollama(prompt, modelo)
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
        "modelo": modelo or modelo_ollama(),
        "latencia_ms": int((time.perf_counter() - started) * 1000),
    }


def _extraer_con_ollama(prompt, modelo=None):
    import json
    import urllib.error
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
