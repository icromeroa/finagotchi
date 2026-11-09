import io
import os
import secrets
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from flask import Flask, g, request, send_file

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import ai, audio, conversation, nlp, services, tts  # noqa: E402
from backend import finance_engine  # noqa: E402
from backend.api_utils import body, datos_entrantes, error, ok, require_fields  # noqa: E402
from backend.auth import (  # noqa: E402
    auth_required,
    create_access_token,
    device_required,
    hash_password,
    issue_tokens,
    verify_password,
)
from backend.db import (  # noqa: E402
    BOGOTA,
    dict_rows,
    get_db,
    init_app as init_db_app,
    iso_utc,
    local_date,
    local_date_from_timestamp,
    new_token,
    now_utc,
    token_hash,
)
from database import init_db  # noqa: E402


def public_user(row):
    user = dict(row)
    user.pop("password_hash", None)
    return user


MIME_AUDIO_ACEPTADOS = {
    "audio/wav",
    "audio/x-wav",
    "audio/wave",
    "audio/vnd.wave",
    "application/octet-stream",
}


def _voz_endpoint():
    """Anuncia al cliente que puede sintetizar la respuesta con Piper."""
    if not tts.disponible():
        return None
    return {
        "modo": "online",
        "endpoint": "/api/v1/device/voice/synthesize",
        "idioma": "es_MX",
        "max_caracteres": tts.MAX_CARACTERES,
    }


def _sintetizar_voz(data):
    texto = data.get("texto")
    if not texto or not str(texto).strip():
        return error("CAMPOS_REQUERIDOS", "El campo texto es obligatorio", 422)
    if len(str(texto)) > tts.MAX_CARACTERES:
        return error(
            "TTS_TEXTO_LARGO",
            "El texto es demasiado largo para sintetizarlo",
            422,
            {"maximo_caracteres": tts.MAX_CARACTERES},
        )
    audio_bytes = tts.sintetizar_wav(texto)
    if audio_bytes is None:
        return error("TTS_NO_DISPONIBLE", "El sintetizador no esta configurado", 503)
    return send_file(
        io.BytesIO(audio_bytes),
        mimetype="audio/wav",
        as_attachment=False,
        download_name="nancy.wav",
    )


class ErrorSolicitud(Exception):
    """Error de negocio que se traduce a una respuesta de la API."""

    def __init__(self, codigo, mensaje, estado=400, detalles=None):
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje
        self.estado = estado
        self.detalles = detalles or {}


def _mime_audio(archivo):
    mime = (getattr(archivo, "content_type", "") or "").split(";")[0].strip().lower()
    if mime in MIME_AUDIO_ACEPTADOS:
        return mime
    nombre = (getattr(archivo, "filename", "") or "").lower()
    if nombre.endswith(".wav"):
        return audio.MIME_TYPE
    return mime or "application/octet-stream"


def _plan_int(value, nombre, minimo, maximo):
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ErrorSolicitud(
            "PARAMETRO_INVALIDO",
            "El parametro {0} debe ser un entero".format(nombre),
            422,
            {"campo": nombre},
        ) from exc
    if number < minimo or number > maximo:
        raise ErrorSolicitud(
            "PARAMETRO_INVALIDO",
            "El parametro {0} debe estar entre {1} y {2}".format(nombre, minimo, maximo),
            422,
            {"campo": nombre},
        )
    return number


def _plan_pct(value):
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ErrorSolicitud(
            "PARAMETRO_INVALIDO",
            "El parametro colchon_pct debe ser numerico",
            422,
            {"campo": "colchon_pct"},
        ) from exc
    if number < 0 or number > 50:
        raise ErrorSolicitud(
            "PARAMETRO_INVALIDO",
            "El parametro colchon_pct debe estar entre 0 y 50",
            422,
            {"campo": "colchon_pct"},
        )
    return number


def _plan_options(source):
    """Opciones comunes de plan: meses, fecha y colchon."""
    fecha = source.get("fecha") or local_date()
    if finance_engine.parse_date(fecha) is None:
        raise ErrorSolicitud(
            "PARAMETRO_INVALIDO",
            "La fecha no es valida",
            422,
            {"campo": "fecha"},
        )
    return {
        "as_of": str(fecha)[:10],
        "meses": _plan_int(source.get("meses", 12), "meses", 1, 24),
        "colchon_pct": _plan_pct(source.get("colchon_pct", 10)),
    }


def _plan_overrides(data):
    """Opciones adicionales de simulacion y los overrides aplicados."""
    overrides = {}
    result = {}
    for nombre, clave in (
        ("ingreso_mensual", "income_override"),
        ("gasto_mensual", "expense_override"),
        ("capacidad_mensual", "capacity_override"),
    ):
        value = data.get(nombre)
        if value is not None:
            number = _plan_int(value, nombre, 0, 10**15)
            result[clave] = number
            overrides[nombre] = number

    prioridades = data.get("prioridades")
    if prioridades is not None:
        if not isinstance(prioridades, dict):
            raise ErrorSolicitud(
                "PARAMETRO_INVALIDO",
                "prioridades debe ser un objeto meta_id -> prioridad",
                422,
                {"campo": "prioridades"},
            )
        normalizadas = {}
        for key, value in prioridades.items():
            try:
                meta_id = int(key)
            except (TypeError, ValueError) as exc:
                raise ErrorSolicitud(
                    "PARAMETRO_INVALIDO",
                    "Las claves de prioridades deben ser meta_id",
                    422,
                    {"campo": "prioridades"},
                ) from exc
            prioridad = services.parse_priority(value)
            if prioridad is None:
                raise ErrorSolicitud(
                    "PARAMETRO_INVALIDO",
                    "La prioridad debe estar entre 1 y 5",
                    422,
                    {"campo": "prioridades"},
                )
            normalizadas[meta_id] = prioridad
        result["prioridades"] = normalizadas
        overrides["prioridades"] = normalizadas

    incluir = data.get("incluir_metas")
    if incluir is not None:
        if not isinstance(incluir, list):
            raise ErrorSolicitud(
                "PARAMETRO_INVALIDO",
                "incluir_metas debe ser un arreglo de meta_id",
                422,
                {"campo": "incluir_metas"},
            )
        ids = []
        for value in incluir:
            try:
                ids.append(int(value))
            except (TypeError, ValueError) as exc:
                raise ErrorSolicitud(
                    "PARAMETRO_INVALIDO",
                    "incluir_metas debe contener meta_id enteros",
                    422,
                    {"campo": "incluir_metas"},
                ) from exc
        result["incluir_metas"] = ids
        overrides["incluir_metas"] = ids

    return result, overrides


def _verificar_metas(conn, user_id, meta_ids):
    ids = sorted({int(value) for value in meta_ids})
    if not ids:
        return []
    placeholders = ",".join("?" for _ in ids)
    rows = conn.execute(
        "SELECT id FROM metas WHERE usuario_id = ? AND is_deleted = 0 AND id IN ({0})".format(
            placeholders
        ),
        (user_id, *ids),
    ).fetchall()
    existentes = {int(row["id"]) for row in rows}
    return [meta_id for meta_id in ids if meta_id not in existentes]


def procesar_mensaje_voz(
    conn,
    user_id,
    texto=None,
    archivo=None,
    message_id=None,
    device_id=None,
    device_uid=None,
    origen="app_voz",
    idioma=None,
):
    """Procesa un mensaje enviado como audio o como texto.

    El audio se transcribe con el proveedor de STT configurado. El archivo no
    se guarda en disco ni en la base: solo se conserva el texto, la duracion y
    los metadatos de la llamada en ``interacciones_ia``.
    """
    if archivo is not None:
        if not message_id:
            raise ErrorSolicitud(
                "CAMPOS_REQUERIDOS",
                "El campo message_id es obligatorio cuando se envia audio",
                422,
                {"campos": ["message_id"]},
            )

        # Idempotencia antes de gastar una llamada al proveedor.
        existente = services.message_por_message_id(conn, user_id, message_id)
        if existente is not None:
            existente["duplicado"] = True
            existente.setdefault("puntos_otorgados", 0)
            return existente, 200

        audio_bytes = archivo.read()
        try:
            info = audio.validar_wav(audio_bytes)
        except audio.AudioMuyGrande as exc:
            raise ErrorSolicitud(exc.codigo, exc.mensaje, 413, exc.detalles) from exc
        except audio.AudioInvalido as exc:
            raise ErrorSolicitud(exc.codigo, exc.mensaje, 422, exc.detalles) from exc

        mime = _mime_audio(archivo)
        idioma = (idioma or ai.IDIOMA_POR_DEFECTO).strip()
        hotwords = nlp.palabras_clave_usuario(conn, user_id)
        try:
            resultado = ai.transcribe_audio(
                audio_bytes, mime_type=mime, language=idioma, initial_prompt=hotwords
            )
        except ai.ErrorSTT as exc:
            services.log_ai_interaction(
                conn,
                user_id,
                proveedor=ai.proveedor_preferido(),
                modelo=ai.modelo(),
                version_prompt=ai.PROMPT_TRANSCRIPCION,
                entrada={"mime_type": mime, "duracion_s": info.duracion_s, "idioma": idioma},
                salida={
                    "error": exc.codigo,
                    "mensaje": exc.mensaje,
                    "detalles": exc.detalles,
                },
                mensaje_id=None,
            )
            raise ErrorSolicitud(exc.codigo, exc.mensaje, exc.estado_http, exc.detalles) from exc

        payload = conversation.procesar_turno(
            conn,
            user_id,
            resultado["texto"],
            message_id=message_id,
            device_id=device_id,
            dispositivo_uid=device_uid,
            origen=origen,
            audio_duration_s=info.duracion_s,
        )
        salida_ia = {"texto": resultado["texto"]}
        if resultado.get("motivo_fallback"):
            salida_ia["caida_de_proveedor"] = resultado.get("error_proveedor")
            salida_ia["motivo"] = resultado["motivo_fallback"]
        services.log_ai_interaction(
            conn,
            user_id,
            proveedor=resultado.get("proveedor") or "gemini",
            modelo=resultado.get("modelo"),
            version_prompt=ai.PROMPT_TRANSCRIPCION,
            entrada={"mime_type": mime, "duracion_s": info.duracion_s, "idioma": idioma},
            salida=salida_ia,
            latencia_ms=resultado.get("latencia_ms"),
            tokens_entrada=resultado.get("tokens_entrada"),
            tokens_salida=resultado.get("tokens_salida"),
            mensaje_id=payload.get("id"),
        )
        payload.setdefault("duplicado", False)
        payload.setdefault("puntos_otorgados", 0)
        payload["proveedor_stt"] = resultado.get("proveedor")
        payload["modelo_stt"] = resultado.get("modelo")
        voz = _voz_endpoint()
        if voz:
            payload["voz"] = voz
        if resultado.get("motivo_fallback"):
            payload["stt_caida"] = resultado["motivo_fallback"]
        return payload, 201

    texto = (texto or "").strip()
    if not texto:
        raise ErrorSolicitud(
            "CAMPOS_REQUERIDOS",
            "Envia el campo audio o el campo texto",
            422,
            {"campos": ["audio", "texto"]},
        )

    payload = conversation.procesar_turno(
        conn,
        user_id,
        texto,
        message_id=message_id,
        device_id=device_id,
        dispositivo_uid=device_uid,
        origen=origen,
    )
    payload.setdefault("duplicado", False)
    payload.setdefault("puntos_otorgados", 0)
    voz = _voz_endpoint()
    if voz:
        payload["voz"] = voz
    return payload, 200 if payload.get("duplicado") else 201


def create_app(database=None):
    app = Flask(__name__)
    database = database or os.environ.get("FINAGOTCHI_DB") or str(ROOT / "finagotchi.db")
    app.config.update(
        SECRET_KEY=os.environ.get("FINAGOTCHI_SECRET", "finagotchi-dev-secret-v2"),
        DATABASE=database,
        CORS_ORIGIN=os.environ.get("FINAGOTCHI_CORS_ORIGIN", "*"),
        JSON_SORT_KEYS=False,
        MAX_CONTENT_LENGTH=audio.MAX_BYTES,
    )

    path = Path(app.config["DATABASE"])
    if str(path) != ":memory:" and not path.exists():
        init_db.init_sqlite(path)
    init_db_app(app)

    @app.after_request
    def cors(response):
        allowed = app.config["CORS_ORIGIN"]
        origin = request.headers.get("Origin")
        if allowed == "*":
            response.headers["Access-Control-Allow-Origin"] = "*"
        elif origin == allowed:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type, Authorization, X-Device-Token"
        )
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, DELETE, OPTIONS"
        # Chrome (desde la version 115) exige este permiso cuando la app web
        # le pide al backend que esta en la red local. Sin esta linea el
        # navegador bloquea la peticion y ni siquiera llega al servidor.
        if request.headers.get("Access-Control-Request-Private-Network") == "true":
            response.headers["Access-Control-Allow-Private-Network"] = "true"
        return response

    @app.errorhandler(ValueError)
    def value_error(exc):
        return error("DATOS_INVALIDOS", str(exc), 400)

    @app.errorhandler(413)
    def payload_too_large(exc):
        return error(
            "AUDIO_MUY_GRANDE",
            "El archivo enviado supera el tamano maximo permitido",
            413,
            {"max_bytes": audio.MAX_BYTES},
        )

    @app.errorhandler(Exception)
    def error_inesperado(exc):
        """La API siempre responde JSON, nunca la pagina de depuracion de Flask."""
        app.logger.exception("Error no controlado: %s", exc)
        return error(
            "ERROR_INTERNO",
            "Ocurrio un error inesperado al procesar la peticion",
            500,
            {"tipo": type(exc).__name__},
        )

    @app.get("/api/v1/health")
    def health():
        conn = get_db()
        version = conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0]
        return ok({"estado": "ok", "schema_version": version})

    @app.get("/api/v1/ready")
    def ready():
        conn = get_db()
        version = conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0]
        return ok({"listo": True, "schema_version": version})

    @app.post("/api/v1/auth/register")
    def register():
        data = body()
        missing = require_fields(data, ("nombre", "correo", "password"))
        if missing:
            return error("CAMPOS_REQUERIDOS", "Faltan campos obligatorios", 422, {"campos": missing})
        if len(str(data["password"])) < 8:
            return error("PASSWORD_CORTA", "La contraseña debe tener al menos 8 caracteres", 422)
        conn = get_db()
        if conn.execute(
            "SELECT id FROM usuarios WHERE lower(correo) = lower(?)", (data["correo"],)
        ).fetchone():
            return error("CORREO_REGISTRADO", "El correo ya está registrado", 409)

        cursor = conn.execute(
            """
            INSERT INTO usuarios
                (nombre, nombre_completo, correo, password_hash, presupuesto_diario,
                 zona_horaria)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(data["nombre"])[:50],
                data.get("nombre_completo"),
                str(data["correo"]).strip().lower(),
                hash_password(str(data["password"])),
                int(data.get("presupuesto_diario", 30000)),
                data.get("zona_horaria") or "America/Bogota",
            ),
        )
        user_id = cursor.lastrowid
        conn.execute(
            """
            UPDATE progreso_etapa
            SET fecha_inicio_diagnostico = ?, actualizado_en = ?
            WHERE usuario_id = ?
            """,
            (local_date(), iso_utc(), user_id),
        )
        if data.get("acepta_terminos"):
            conn.execute(
                """
                INSERT OR IGNORE INTO consentimientos
                    (usuario_id, tipo, version, aceptado)
                VALUES (?, 'terminos', ?, 1)
                """,
                (user_id, data.get("version_terminos") or "1.0"),
            )
        conn.commit()
        user = conn.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,)).fetchone()
        tokens = issue_tokens(conn, user_id)
        conn.commit()
        return ok({"usuario": public_user(user), "tokens": tokens}, 201)

    @app.post("/api/v1/auth/login")
    def login():
        data = body()
        missing = require_fields(data, ("correo", "password"))
        if missing:
            return error("CAMPOS_REQUERIDOS", "Faltan campos obligatorios", 422, {"campos": missing})
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM usuarios WHERE lower(correo) = lower(?)", (data["correo"],)
        ).fetchone()
        if user is None or not verify_password(user["password_hash"], str(data["password"])):
            return error("CREDENCIALES_INVALIDAS", "Correo o contraseña incorrectos", 401)
        if user["estado"] != "activo":
            return error("CUENTA_INACTIVA", "La cuenta no está activa", 403)
        conn.execute(
            "UPDATE usuarios SET ultimo_acceso = ?, actualizado_en = ? WHERE id = ?",
            (iso_utc(), iso_utc(), user["id"]),
        )
        conn.commit()
        tokens = issue_tokens(conn, user["id"])
        conn.commit()
        return ok({"usuario": public_user(user), "tokens": tokens})

    @app.post("/api/v1/auth/refresh")
    def refresh():
        data = body()
        raw = data.get("refresh_token")
        if not raw:
            return error("CAMPOS_REQUERIDOS", "Falta refresh_token", 422)
        conn = get_db()
        session = conn.execute(
            """
            SELECT * FROM sesiones_refresco
            WHERE token_hash = ? AND revocado_en IS NULL AND expira_en > ?
            """,
            (token_hash(raw), iso_utc()),
        ).fetchone()
        if session is None:
            return error("REFRESH_INVALIDO", "La sesión no es válida o expiró", 401)
        conn.execute(
            "UPDATE sesiones_refresco SET revocado_en = ? WHERE id = ?",
            (iso_utc(), session["id"]),
        )
        conn.commit()
        tokens = issue_tokens(conn, session["usuario_id"])
        conn.commit()
        return ok({"access_token": tokens["access_token"], "refresh_token": tokens["refresh_token"]})

    @app.post("/api/v1/auth/logout")
    @auth_required
    def logout():
        data = body()
        conn = get_db()
        if data.get("refresh_token"):
            conn.execute(
                "UPDATE sesiones_refresco SET revocado_en = ? WHERE usuario_id = ? AND token_hash = ?",
                (iso_utc(), g.user_id, token_hash(data["refresh_token"])),
            )
        else:
            conn.execute(
                "UPDATE sesiones_refresco SET revocado_en = ? WHERE usuario_id = ? AND revocado_en IS NULL",
                (iso_utc(), g.user_id),
            )
        conn.commit()
        return ok({"cerrada": True})

    @app.get("/api/v1/me")
    @auth_required
    def me():
        conn = get_db()
        profile = conn.execute(
            "SELECT * FROM perfil_financiero WHERE usuario_id = ?", (g.user_id,)
        ).fetchone()
        mascot = conn.execute(
            "SELECT * FROM v_estado_mascota WHERE usuario_id = ?", (g.user_id,)
        ).fetchone()
        progress = conn.execute(
            "SELECT * FROM v_progreso_etapa WHERE usuario_id = ?", (g.user_id,)
        ).fetchone()
        points = conn.execute(
            "SELECT COALESCE(SUM(puntos), 0) FROM puntos_log WHERE usuario_id = ?",
            (g.user_id,),
        ).fetchone()[0]
        return ok(
            {
                "usuario": public_user(conn.execute("SELECT * FROM usuarios WHERE id = ?", (g.user_id,)).fetchone()),
                "perfil": dict(profile) if profile else {},
                "mascota": dict(mascot) if mascot else {},
                "progreso": dict(progress) if progress else {},
                "puntos": points,
            }
        )

    @app.patch("/api/v1/me")
    @auth_required
    def update_me():
        data = body()
        allowed = {}
        for field in ("nombre", "nombre_completo", "telefono", "zona_horaria"):
            if field in data:
                allowed[field] = data[field]
        if "presupuesto_diario" in data:
            try:
                budget = int(data["presupuesto_diario"])
            except (TypeError, ValueError):
                raise ValueError("El presupuesto diario debe ser un entero")
            if budget < 0:
                raise ValueError("El presupuesto diario no puede ser negativo")
            allowed["presupuesto_diario"] = budget
        if not allowed:
            return ok({"actualizado": False})
        assignments = ", ".join(f"{column} = ?" for column in allowed)
        conn = get_db()
        conn.execute(
            f"UPDATE usuarios SET {assignments}, actualizado_en = ? WHERE id = ?",
            (*allowed.values(), iso_utc(), g.user_id),
        )
        conn.commit()
        return ok(public_user(conn.execute("SELECT * FROM usuarios WHERE id = ?", (g.user_id,)).fetchone()))

    @app.get("/api/v1/me/profile")
    @auth_required
    def get_profile():
        conn = get_db()
        profile = conn.execute(
            "SELECT * FROM perfil_financiero WHERE usuario_id = ?", (g.user_id,)
        ).fetchone()
        sections = conn.execute(
            "SELECT * FROM v_perfil_completitud WHERE usuario_id = ?", (g.user_id,)
        ).fetchone()
        return ok({"perfil": dict(profile) if profile else {}, "completitud": dict(sections) if sections else {}})

    @app.patch("/api/v1/me/profile")
    @auth_required
    def update_profile():
        data = body()
        conn = get_db()
        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(perfil_financiero)").fetchall()
        }
        allowed = {
            key: value
            for key, value in data.items()
            if key in columns and key not in ("usuario_id", "ingreso_total_mensual")
        }
        if not allowed:
            return ok({"actualizado": False})
        assignments = ", ".join(f"{column} = ?" for column in allowed)
        conn.execute(
            f"UPDATE perfil_financiero SET {assignments} WHERE usuario_id = ?",
            (*allowed.values(), g.user_id),
        )
        conn.commit()
        profile = conn.execute(
            "SELECT * FROM perfil_financiero WHERE usuario_id = ?", (g.user_id,)
        ).fetchone()
        return ok(dict(profile))

    @app.get("/api/v1/me/consents")
    @auth_required
    def get_consents():
        conn = get_db()
        rows = conn.execute(
            "SELECT * FROM consentimientos WHERE usuario_id = ? ORDER BY aceptado_en DESC",
            (g.user_id,),
        ).fetchall()
        return ok(dict_rows(rows))

    @app.post("/api/v1/me/consents")
    @auth_required
    def create_consent():
        data = body()
        missing = require_fields(data, ("tipo", "version"))
        if missing:
            return error("CAMPOS_REQUERIDOS", "Faltan campos obligatorios", 422, {"campos": missing})
        conn = get_db()
        conn.execute(
            """
            INSERT INTO consentimientos (usuario_id, tipo, version, aceptado)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (usuario_id, tipo, version)
            DO UPDATE SET aceptado = excluded.aceptado, aceptado_en = ?
            """,
            (g.user_id, data["tipo"], data["version"], 1 if data.get("aceptado", True) else 0, iso_utc()),
        )
        conn.commit()
        return ok({"registrado": True}, 201)

    @app.get("/api/v1/me/wellbeing")
    @auth_required
    def get_wellbeing():
        conn = get_db()
        row = conn.execute(
            "SELECT * FROM v_bienestar_financiero WHERE usuario_id = ?", (g.user_id,)
        ).fetchone()
        return ok(dict(row) if row else {"puntaje": None, "cobertura": 0})

    @app.get("/api/v1/home")
    @auth_required
    def home():
        incluir_plan = (request.args.get("incluir_plan") or "").strip().lower() in (
            "1",
            "true",
            "si",
            "sí",
        )
        return ok(
            services.home_payload(get_db(), g.user_id, incluir_plan=incluir_plan)
        )

    @app.get("/api/v1/accounts")
    @auth_required
    def list_accounts():
        return ok(services.accounts_summary(get_db(), g.user_id))

    @app.post("/api/v1/accounts")
    @auth_required
    def create_account():
        data = body()
        missing = require_fields(data, ("nombre", "tipo_cuenta"))
        if missing:
            return error("CAMPOS_REQUERIDOS", "Faltan campos obligatorios", 422, {"campos": missing})
        account_type = data["tipo_cuenta"]
        if account_type not in ("efectivo", "billetera_digital", "tarjeta", "cuenta_ahorros", "inversion"):
            return error("TIPO_CUENTA_INVALIDO", "Tipo de cuenta inválido", 422)
        initial = int(data.get("saldo_inicial", 0))
        if account_type == "tarjeta" and initial != 0:
            return error("SALDO_TARJETA_INVALIDO", "Una tarjeta no puede tener saldo inicial", 422)
        conn = get_db()
        order = conn.execute(
            "SELECT COALESCE(MAX(orden), 0) + 1 FROM cuentas WHERE usuario_id = ?", (g.user_id,)
        ).fetchone()[0]
        cursor = conn.execute(
            """
            INSERT INTO cuentas
                (usuario_id, nombre, tipo_cuenta, icono, ultimos_4, saldo_inicial,
                 es_sistema, es_por_defecto, oculta, orden)
            VALUES (?, ?, ?, ?, ?, ?, 0, 0, 0, ?)
            """,
            (
                g.user_id,
                str(data["nombre"])[:24],
                account_type,
                data.get("icono"),
                data.get("ultimos_4"),
                initial,
                order,
            ),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM v_cuentas_resumen WHERE usuario_id = ? AND cuenta_id = ?",
            (g.user_id, cursor.lastrowid),
        ).fetchone()
        return ok(dict(row), 201)

    @app.patch("/api/v1/accounts/<int:account_id>")
    @auth_required
    def update_account(account_id):
        data = body()
        conn = get_db()
        account = conn.execute(
            "SELECT * FROM cuentas WHERE usuario_id = ? AND id = ?", (g.user_id, account_id)
        ).fetchone()
        if account is None:
            return error("CUENTA_NO_ENCONTRADA", "La cuenta no existe", 404)

        fields = {}
        for field in ("nombre", "icono", "ultimos_4", "saldo_inicial", "oculta", "orden"):
            if field in data:
                fields[field] = data[field]
        if "tipo_cuenta" in data:
            if data["tipo_cuenta"] not in ("efectivo", "billetera_digital", "tarjeta", "cuenta_ahorros", "inversion"):
                return error("TIPO_CUENTA_INVALIDO", "Tipo de cuenta inválido", 422)
            fields["tipo_cuenta"] = data["tipo_cuenta"]
        if data.get("es_por_defecto"):
            conn.execute(
                "UPDATE cuentas SET es_por_defecto = 0 WHERE usuario_id = ? AND id <> ?",
                (g.user_id, account_id),
            )
            fields["es_por_defecto"] = 1
            fields["oculta"] = 0
        if fields.get("oculta") == 1 and (account["es_por_defecto"] or fields.get("es_por_defecto")):
            return error("CUENTA_POR_DEFECTO_OCULTA", "La cuenta por defecto no puede ocultarse", 422)
        if fields.get("tipo_cuenta") == "tarjeta" and fields.get("saldo_inicial", account["saldo_inicial"]) != 0:
            return error("SALDO_TARJETA_INVALIDO", "Una tarjeta no puede tener saldo inicial", 422)
        if not fields:
            return ok(dict(account))
        assignments = ", ".join(f"{column} = ?" for column in fields)
        conn.execute(
            f"UPDATE cuentas SET {assignments}, actualizado_en = ? WHERE usuario_id = ? AND id = ?",
            (*fields.values(), iso_utc(), g.user_id, account_id),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM v_cuentas_resumen WHERE usuario_id = ? AND cuenta_id = ?",
            (g.user_id, account_id),
        ).fetchone()
        return ok(dict(row))

    @app.delete("/api/v1/accounts/<int:account_id>")
    @auth_required
    def delete_account(account_id):
        data = body()
        conn = get_db()
        account = conn.execute(
            "SELECT * FROM cuentas WHERE usuario_id = ? AND id = ?", (g.user_id, account_id)
        ).fetchone()
        if account is None:
            return error("CUENTA_NO_ENCONTRADA", "La cuenta no existe", 404)
        if account["es_por_defecto"]:
            return error("CUENTA_POR_DEFECTO", "No se puede eliminar la cuenta por defecto", 422)
        target_id = data.get("cuenta_destino_id")
        target = conn.execute(
            "SELECT id FROM cuentas WHERE usuario_id = ? AND id = ? AND id <> ?",
            (g.user_id, target_id, account_id),
        ).fetchone() if target_id else None
        if target is None:
            target = conn.execute(
                "SELECT id FROM cuentas WHERE usuario_id = ? AND es_por_defecto = 1 AND id <> ?",
                (g.user_id, account_id),
            ).fetchone()
        if target is None:
            return error("CUENTA_DESTINO_REQUERIDA", "Indica una cuenta destino", 422)
        conn.execute(
            "UPDATE transacciones SET cuenta_id = ? WHERE usuario_id = ? AND cuenta_id = ?",
            (target["id"], g.user_id, account_id),
        )
        conn.execute(
            "DELETE FROM cuentas WHERE usuario_id = ? AND id = ?", (g.user_id, account_id)
        )
        conn.commit()
        return ok({"eliminada": True, "cuenta_destino_id": target["id"]})

    @app.get("/api/v1/categories")
    @auth_required
    def list_categories():
        conn = get_db()
        category_type = request.args.get("tipo")
        query = "SELECT * FROM categorias WHERE usuario_id = ? AND activa = 1"
        params = [g.user_id]
        if category_type:
            query += " AND tipo = ?"
            params.append(category_type)
        query += " ORDER BY tipo, orden, nombre"
        return ok(dict_rows(conn.execute(query, params).fetchall()))

    @app.post("/api/v1/categories")
    @auth_required
    def create_category():
        data = body()
        missing = require_fields(data, ("nombre", "tipo", "icono"))
        if missing:
            return error("CAMPOS_REQUERIDOS", "Faltan campos obligatorios", 422, {"campos": missing})
        if data["tipo"] not in ("gasto", "ingreso"):
            return error("TIPO_CATEGORIA_INVALIDO", "Tipo de categoría inválido", 422)
        conn = get_db()
        order = conn.execute(
            "SELECT COALESCE(MAX(orden), 0) + 1 FROM categorias WHERE usuario_id = ? AND tipo = ?",
            (g.user_id, data["tipo"]),
        ).fetchone()[0]
        cursor = conn.execute(
            """
            INSERT INTO categorias
                (usuario_id, nombre, tipo, icono, es_sistema, es_fija, activa, orden)
            VALUES (?, ?, ?, ?, 0, ?, 1, ?)
            """,
            (
                g.user_id,
                str(data["nombre"])[:24],
                data["tipo"],
                data["icono"],
                1 if data.get("es_fija") else 0,
                order,
            ),
        )
        words = data.get("palabras") or []
        for word in words:
            conn.execute(
                "INSERT OR IGNORE INTO categoria_palabras (usuario_id, categoria_id, palabra) VALUES (?, ?, ?)",
                (g.user_id, cursor.lastrowid, nlp.normalize(word)[:40]),
            )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM categorias WHERE usuario_id = ? AND id = ?", (g.user_id, cursor.lastrowid)
        ).fetchone()
        return ok(dict(row), 201)

    @app.patch("/api/v1/categories/<int:category_id>")
    @auth_required
    def update_category(category_id):
        data = body()
        conn = get_db()
        category = conn.execute(
            "SELECT * FROM categorias WHERE usuario_id = ? AND id = ?", (g.user_id, category_id)
        ).fetchone()
        if category is None:
            return error("CATEGORIA_NO_ENCONTRADA", "La categoría no existe", 404)
        allowed = {}
        if "nombre" in data and not category["es_sistema"]:
            allowed["nombre"] = str(data["nombre"])[:24]
        for field in ("icono", "orden", "activa", "es_fija"):
            if field in data:
                allowed[field] = data[field]
        if not allowed:
            return ok(dict(category))
        assignments = ", ".join(f"{column} = ?" for column in allowed)
        conn.execute(
            f"UPDATE categorias SET {assignments} WHERE usuario_id = ? AND id = ?",
            (*allowed.values(), g.user_id, category_id),
        )
        conn.commit()
        return ok(dict(conn.execute(
            "SELECT * FROM categorias WHERE usuario_id = ? AND id = ?", (g.user_id, category_id)
        ).fetchone()))

    @app.post("/api/v1/categories/<int:category_id>/deactivate")
    @auth_required
    def deactivate_category(category_id):
        conn = get_db()
        result = conn.execute(
            "UPDATE categorias SET activa = 0 WHERE usuario_id = ? AND id = ? AND es_sistema = 0",
            (g.user_id, category_id),
        )
        conn.commit()
        if result.rowcount == 0:
            return error("CATEGORIA_NO_ELIMINABLE", "La categoría no existe o es del sistema", 422)
        return ok({"desactivada": True})

    @app.get("/api/v1/transactions")
    @auth_required
    def list_transactions():
        conn = get_db()
        clauses = ["t.usuario_id = ?"]
        params = [g.user_id]
        include_deleted = request.args.get("incluir_anuladas") == "1"
        if not include_deleted:
            clauses.append("t.is_deleted = 0")
        if request.args.get("tipo"):
            clauses.append("t.tipo = ?")
            params.append(request.args["tipo"])
        if request.args.get("categoria_id"):
            clauses.append("t.categoria_id = ?")
            params.append(request.args["categoria_id"])
        if request.args.get("cuenta_id"):
            clauses.append("t.cuenta_id = ?")
            params.append(request.args["cuenta_id"])
        state_filter = request.args.get("estado")
        if state_filter == "anulado":
            clauses.append("t.is_deleted = 1")
        elif state_filter:
            clauses.append("t.estado = ?")
            params.append(state_filter)
        if request.args.get("desde"):
            clauses.append("t.fecha_local >= ?")
            params.append(request.args["desde"])
        if request.args.get("hasta"):
            clauses.append("t.fecha_local <= ?")
            params.append(request.args["hasta"])
        if request.args.get("monto_min"):
            clauses.append("t.monto >= ?")
            params.append(int(request.args["monto_min"]))
        if request.args.get("monto_max"):
            clauses.append("t.monto <= ?")
            params.append(int(request.args["monto_max"]))
        limit = min(int(request.args.get("limit", 100)), 500)
        offset = max(int(request.args.get("offset", 0)), 0)
        query = f"""
            SELECT t.*, c.nombre AS categoria, cu.nombre AS cuenta, m.nombre AS meta
            FROM transacciones t
            LEFT JOIN categorias c ON c.usuario_id = t.usuario_id AND c.id = t.categoria_id
            LEFT JOIN cuentas cu ON cu.usuario_id = t.usuario_id AND cu.id = t.cuenta_id
            LEFT JOIN metas m ON m.usuario_id = t.usuario_id AND m.id = t.meta_id
            WHERE {' AND '.join(clauses)}
            ORDER BY t.fecha_hora DESC, t.id DESC
            LIMIT ? OFFSET ?
        """
        rows = conn.execute(query, (*params, limit, offset)).fetchall()
        total = conn.execute(
            f"SELECT COUNT(*) FROM transacciones t WHERE {' AND '.join(clauses)}", params
        ).fetchone()[0]
        return ok({"items": dict_rows(rows), "total": total, "limit": limit, "offset": offset})

    @app.post("/api/v1/transactions")
    @auth_required
    def post_transaction():
        transaction = services.create_transaction(get_db(), g.user_id, body())
        return ok(transaction, 201)

    @app.get("/api/v1/transactions/<int:transaction_id>")
    @auth_required
    def get_transaction(transaction_id):
        row = services.transaction_row(get_db(), g.user_id, transaction_id)
        if row is None:
            return error("MOVIMIENTO_NO_ENCONTRADO", "El movimiento no existe", 404)
        return ok(dict(row))

    @app.patch("/api/v1/transactions/<int:transaction_id>")
    @auth_required
    def patch_transaction(transaction_id):
        row = services.update_transaction(get_db(), g.user_id, transaction_id, body())
        if row is None:
            return error("MOVIMIENTO_NO_ENCONTRADO", "El movimiento no existe", 404)
        return ok(row)

    @app.delete("/api/v1/transactions/<int:transaction_id>")
    @auth_required
    def delete_transaction(transaction_id):
        data = body()
        action = data.get("via") or request.args.get("via") or "app"
        if action not in ("app", "voz", "deshacer", "sistema"):
            action = "app"
        row = services.delete_transaction(get_db(), g.user_id, transaction_id, action)
        if row is None:
            return error("MOVIMIENTO_NO_ENCONTRADO", "El movimiento no existe", 404)
        return ok(row)

    @app.post("/api/v1/transactions/<int:transaction_id>/restore")
    @auth_required
    def restore_transaction(transaction_id):
        row = services.restore_transaction(get_db(), g.user_id, transaction_id)
        if row is None:
            return error("MOVIMIENTO_NO_ENCONTRADO", "El movimiento no existe", 404)
        return ok(row)

    @app.post("/api/v1/messages")
    @auth_required
    def post_message():
        data = datos_entrantes()
        try:
            payload, status = procesar_mensaje_voz(
                get_db(),
                g.user_id,
                texto=data.get("texto"),
                archivo=request.files.get("audio"),
                message_id=data.get("message_id"),
                device_id=data.get("device_id"),
                origen=data.get("origen") or "app_voz",
                idioma=data.get("idioma"),
            )
        except ErrorSolicitud as exc:
            return error(exc.codigo, exc.mensaje, exc.estado, exc.detalles)
        return ok(payload, status)

    @app.get("/api/v1/messages/<int:message_id>")
    @auth_required
    def get_message(message_id):
        payload = services.message_payload(get_db(), g.user_id, message_id)
        if payload is None:
            return error("MENSAJE_NO_ENCONTRADO", "El mensaje no existe", 404)
        return ok(payload)

    @app.post("/api/v1/messages/<int:message_id>/confirm")
    @auth_required
    def confirm_message(message_id):
        payload = services.confirm_message(get_db(), g.user_id, message_id)
        if payload is None:
            return error("MENSAJE_NO_ENCONTRADO", "El mensaje no existe", 404)
        conversation.invalidar_accion_pendiente(g.user_id, message_id)
        return ok(payload)

    @app.post("/api/v1/messages/<int:message_id>/discard")
    @auth_required
    def discard_message(message_id):
        conn = get_db()
        message = conn.execute(
            "SELECT * FROM mensajes_dispositivo WHERE usuario_id = ? AND id = ?",
            (g.user_id, message_id),
        ).fetchone()
        if message is None:
            return error("MENSAJE_NO_ENCONTRADO", "El mensaje no existe", 404)
        conn.execute(
            """
            UPDATE transacciones
            SET is_deleted = 1, deleted_at = ?, eliminado_via = 'voz', actualizado_en = ?
            WHERE usuario_id = ? AND mensaje_id = ? AND estado = 'pendiente' AND is_deleted = 0
            """,
            (iso_utc(), iso_utc(), g.user_id, message_id),
        )
        conn.execute(
            "UPDATE mensajes_dispositivo SET estado = 'descartado' WHERE usuario_id = ? AND id = ?",
            (g.user_id, message_id),
        )
        conn.commit()
        conversation.invalidar_accion_pendiente(g.user_id, message_id)
        return ok({"descartado": True})

    @app.get("/api/v1/days/<date_value>")
    @auth_required
    def get_day(date_value):
        if services.parse_date(date_value) is None:
            return error("FECHA_INVALIDA", "La fecha debe tener formato YYYY-MM-DD", 422)
        conn = get_db()
        closure = conn.execute(
            "SELECT * FROM cierres_dia WHERE usuario_id = ? AND fecha_local = ?",
            (g.user_id, date_value),
        ).fetchone()
        if closure:
            payload = dict(closure)
            payload["cerrado"] = True
        else:
            payload = {
                "fecha_local": date_value,
                "cerrado": False,
                "totales": services.day_totals(conn, g.user_id, date_value),
                "presupuesto_diario": services.budget_for_day(conn, g.user_id, date_value),
                "proyeccion": services.health_projection(conn, g.user_id, date_value),
            }
        payload["categorias"] = services.categories_breakdown(conn, g.user_id, date_value)
        return ok(payload)

    @app.post("/api/v1/days/<date_value>/close")
    @auth_required
    def close_day(date_value):
        if services.parse_date(date_value) is None:
            return error("FECHA_INVALIDA", "La fecha debe tener formato YYYY-MM-DD", 422)
        return ok(services.close_day(get_db(), g.user_id, date_value))

    @app.get("/api/v1/metrics/daily")
    @auth_required
    def metrics_daily():
        date_value = request.args.get("fecha") or local_date()
        if services.parse_date(date_value) is None:
            return error("FECHA_INVALIDA", "La fecha debe tener formato YYYY-MM-DD", 422)
        conn = get_db()
        return ok(
            {
                "resumen": services.metrics_daily(conn, g.user_id, date_value),
                "categorias": services.categories_breakdown(conn, g.user_id, date_value),
            }
        )

    @app.get("/api/v1/metrics/weekly")
    @auth_required
    def metrics_weekly():
        end = services.parse_date(request.args.get("fecha") or local_date())
        if end is None:
            return error("FECHA_INVALIDA", "La fecha debe tener formato YYYY-MM-DD", 422)
        start = end - timedelta(days=6)
        conn = get_db()
        totals = conn.execute(
            """
            SELECT
              COALESCE(SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END), 0) AS ingresos,
              COALESCE(SUM(CASE WHEN tipo = 'gasto' THEN monto ELSE 0 END), 0) AS gastos,
              COALESCE(SUM(CASE WHEN tipo = 'ahorro' THEN monto ELSE 0 END), 0) AS ahorro,
              COUNT(*) AS num_registros
            FROM transacciones
            WHERE usuario_id = ? AND fecha_local BETWEEN ? AND ?
              AND estado = 'confirmado' AND is_deleted = 0
            """,
            (g.user_id, start.isoformat(), end.isoformat()),
        ).fetchone()
        totals = dict(totals)
        totals["balance_neto"] = totals["ingresos"] - totals["gastos"]
        totals["capacidad_libre_ahorro"] = totals["ingresos"] - totals["gastos"] - totals["ahorro"]
        days = conn.execute(
            """
            SELECT fecha_local, SUM(CASE WHEN tipo = 'gasto' THEN monto ELSE 0 END) AS gastos
            FROM transacciones
            WHERE usuario_id = ? AND fecha_local BETWEEN ? AND ?
              AND estado = 'confirmado' AND is_deleted = 0
            GROUP BY fecha_local ORDER BY fecha_local
            """,
            (g.user_id, start.isoformat(), end.isoformat()),
        ).fetchall()
        return ok({"desde": start.isoformat(), "hasta": end.isoformat(), "resumen": totals, "dias": dict_rows(days)})

    @app.get("/api/v1/metrics/monthly")
    @auth_required
    def metrics_monthly():
        end = services.parse_date(request.args.get("fecha") or local_date())
        if end is None:
            return error("FECHA_INVALIDA", "La fecha debe tener formato YYYY-MM-DD", 422)
        start = end.replace(day=1)
        conn = get_db()
        totals = conn.execute(
            """
            SELECT
              COALESCE(SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END), 0) AS ingresos,
              COALESCE(SUM(CASE WHEN tipo = 'gasto' THEN monto ELSE 0 END), 0) AS gastos,
              COALESCE(SUM(CASE WHEN tipo = 'ahorro' THEN monto ELSE 0 END), 0) AS ahorro,
              COUNT(*) AS num_registros
            FROM transacciones
            WHERE usuario_id = ? AND fecha_local BETWEEN ? AND ?
              AND estado = 'confirmado' AND is_deleted = 0
            """,
            (g.user_id, start.isoformat(), end.isoformat()),
        ).fetchone()
        totals = dict(totals)
        totals["balance_neto"] = totals["ingresos"] - totals["gastos"]
        categories = conn.execute(
            """
            SELECT COALESCE(c.nombre, 'Sin categoría') AS categoria, c.icono,
                   SUM(t.monto) AS total, COUNT(*) AS num_registros
            FROM transacciones t
            LEFT JOIN categorias c ON c.usuario_id = t.usuario_id AND c.id = t.categoria_id
            WHERE t.usuario_id = ? AND t.fecha_local BETWEEN ? AND ?
              AND t.tipo = 'gasto' AND t.estado = 'confirmado' AND t.is_deleted = 0
            GROUP BY t.categoria_id, c.nombre, c.icono
            ORDER BY total DESC
            """,
            (g.user_id, start.isoformat(), end.isoformat()),
        ).fetchall()
        return ok({"desde": start.isoformat(), "hasta": end.isoformat(), "resumen": totals, "categorias": dict_rows(categories)})

    @app.get("/api/v1/metrics/health")
    @auth_required
    def metrics_health():
        date_value = request.args.get("fecha") or local_date()
        if services.parse_date(date_value) is None:
            return error("FECHA_INVALIDA", "La fecha debe tener formato YYYY-MM-DD", 422)
        conn = get_db()
        closure = conn.execute(
            "SELECT * FROM cierres_dia WHERE usuario_id = ? AND fecha_local = ?",
            (g.user_id, date_value),
        ).fetchone()
        return ok(
            {
                "persistida": dict(closure) if closure else None,
                "proyeccion": services.health_projection(conn, g.user_id, date_value),
            }
        )

    @app.get("/api/v1/metrics/diagnostics")
    @auth_required
    def metrics_diagnostics():
        conn = get_db()
        progress = conn.execute(
            "SELECT * FROM v_progreso_etapa WHERE usuario_id = ?", (g.user_id,)
        ).fetchone()
        points = conn.execute(
            "SELECT * FROM v_puntos_usuario WHERE usuario_id = ?", (g.user_id,)
        ).fetchone() if conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='view' AND name='v_puntos_usuario'"
        ).fetchone() else None
        closures = conn.execute(
            "SELECT * FROM cierres_dia WHERE usuario_id = ? ORDER BY fecha_local DESC LIMIT 30",
            (g.user_id,),
        ).fetchall()
        return ok(
            {
                "progreso": dict(progress) if progress else {},
                "puntos": dict(points) if points else {},
                "cierres": dict_rows(closures),
            }
        )

    @app.get("/api/v1/goals")
    @auth_required
    def list_goals():
        conn = get_db()
        rows = conn.execute(
            "SELECT * FROM v_metas_estado WHERE usuario_id = ? ORDER BY fecha_limite, meta_id",
            (g.user_id,),
        ).fetchall()
        return ok(dict_rows(rows))

    @app.get("/api/v1/goals/plan")
    @auth_required
    def get_goal_plan():
        try:
            options = _plan_options(request.args)
        except ErrorSolicitud as exc:
            return error(exc.codigo, exc.mensaje, exc.estado, exc.detalles)
        return ok(services.goal_plan(get_db(), g.user_id, **options))

    @app.post("/api/v1/goals/plan/simulate")
    @auth_required
    def simulate_goal_plan():
        data = body()
        try:
            options = _plan_options(data)
            extra, overrides = _plan_overrides(data)
        except ErrorSolicitud as exc:
            return error(exc.codigo, exc.mensaje, exc.estado, exc.detalles)

        conn = get_db()
        solicitadas = set(extra.get("incluir_metas") or [])
        solicitadas.update(extra.get("prioridades") or {})
        faltantes = _verificar_metas(conn, g.user_id, solicitadas)
        if faltantes:
            return error(
                "META_INEXISTENTE",
                "Alguna meta no existe o no pertenece al usuario",
                404,
                {"metas": faltantes},
            )

        plan = services.goal_plan(
            conn,
            g.user_id,
            simulacion=True,
            overrides=overrides,
            **options,
            **extra,
        )
        return ok(plan)

    @app.post("/api/v1/goals")
    @auth_required
    def create_goal():
        try:
            goal = services.create_goal(get_db(), g.user_id, body())
        except services.ErrorMeta as exc:
            return error(exc.codigo, exc.mensaje, exc.estado, exc.detalles)
        return ok(goal, 201)

    @app.get("/api/v1/goals/<int:goal_id>")
    @auth_required
    def get_goal(goal_id):
        payload = services.serialize_goal(get_db(), g.user_id, goal_id)
        if payload is None:
            return error("META_NO_ENCONTRADA", "La meta no existe", 404)
        return ok(payload)

    @app.patch("/api/v1/goals/<int:goal_id>")
    @auth_required
    def update_goal(goal_id):
        data = body()
        conn = get_db()
        goal = conn.execute(
            "SELECT * FROM metas WHERE usuario_id = ? AND id = ? AND is_deleted = 0",
            (g.user_id, goal_id),
        ).fetchone()
        if goal is None:
            return error("META_NO_ENCONTRADA", "La meta no existe", 404)
        allowed = {}
        for field in (
            "nombre",
            "icono",
            "monto_meta",
            "fecha_limite",
            "frecuencia_ahorro",
            "aporte_periodico",
            "dia_aporte",
            "hora_recordatorio",
            "prioridad",
            "estado",
        ):
            if field in data:
                allowed[field] = data[field]
        if "prioridad" in allowed:
            prioridad = services.parse_priority(allowed["prioridad"])
            if prioridad is None:
                return error(
                    "PRIORIDAD_INVALIDA",
                    "La prioridad debe estar entre 1 y 5",
                    422,
                    {"campo": "prioridad"},
                )
            allowed["prioridad"] = prioridad
        if not allowed:
            return ok(services.serialize_goal(conn, g.user_id, goal_id))
        assignments = ", ".join(f"{column} = ?" for column in allowed)
        conn.execute(
            f"UPDATE metas SET {assignments}, actualizado_en = ? WHERE usuario_id = ? AND id = ?",
            (*allowed.values(), iso_utc(), g.user_id, goal_id),
        )
        conn.commit()
        return ok(services.serialize_goal(conn, g.user_id, goal_id))

    @app.delete("/api/v1/goals/<int:goal_id>")
    @auth_required
    def delete_goal(goal_id):
        conn = get_db()
        result = conn.execute(
            "UPDATE metas SET is_deleted = 1, deleted_at = ?, actualizado_en = ? WHERE usuario_id = ? AND id = ? AND is_deleted = 0",
            (iso_utc(), iso_utc(), g.user_id, goal_id),
        )
        conn.commit()
        if result.rowcount == 0:
            return error("META_NO_ENCONTRADA", "La meta no existe", 404)
        return ok({"eliminada": True})

    @app.get("/api/v1/budget")
    @auth_required
    def get_budget():
        today = local_date()
        conn = get_db()
        budget = conn.execute(
            """
            SELECT * FROM presupuestos
            WHERE usuario_id = ? AND aprobado = 1 AND ? BETWEEN fecha_inicio AND fecha_fin
            ORDER BY fecha_inicio DESC LIMIT 1
            """,
            (g.user_id, today),
        ).fetchone()
        if budget is None:
            user = conn.execute("SELECT presupuesto_diario FROM usuarios WHERE id = ?", (g.user_id,)).fetchone()
            return ok({"presupuesto": None, "presupuesto_diario": user["presupuesto_diario"]})
        categories = conn.execute(
            """
            SELECT pc.*, c.nombre, c.tipo FROM presupuesto_categoria pc
            JOIN categorias c ON c.usuario_id = pc.usuario_id AND c.id = pc.categoria_id
            WHERE pc.usuario_id = ? AND pc.presupuesto_id = ?
            ORDER BY c.nombre
            """,
            (g.user_id, budget["id"]),
        ).fetchall()
        return ok({"presupuesto": dict(budget), "categorias": dict_rows(categories)})

    @app.post("/api/v1/budgets")
    @auth_required
    def create_budget():
        data = body()
        start = data.get("fecha_inicio") or local_date()
        start_date = services.parse_date(start)
        if start_date is None:
            return error("FECHA_INVALIDA", "La fecha de inicio no es válida", 422)
        months = int(data.get("meses", 2))
        if months not in (2, 3):
            return error("MESES_INVALIDOS", "El presupuesto debe durar 2 o 3 meses", 422)
        end_date = start_date.replace(year=start_date.year + (start_date.month - 1 + months) // 12,
                                      month=(start_date.month - 1 + months) % 12 + 1) - timedelta(days=1)
        conn = get_db()
        cursor = conn.execute(
            """
            INSERT INTO presupuestos (usuario_id, fecha_inicio, fecha_fin, meses)
            VALUES (?, ?, ?, ?)
            """,
            (g.user_id, start_date.isoformat(), end_date.isoformat(), months),
        )
        budget_id = cursor.lastrowid
        for item in data.get("categorias", []):
            conn.execute(
                """
                INSERT INTO presupuesto_categoria
                    (usuario_id, presupuesto_id, categoria_id, tipo, monto_limite_mensual)
                VALUES (?, ?, ?, 'gasto', ?)
                """,
                (g.user_id, budget_id, item["categoria_id"], int(item.get("monto_limite_mensual", 0))),
            )
        conn.commit()
        budget = conn.execute("SELECT * FROM presupuestos WHERE id = ?", (budget_id,)).fetchone()
        return ok(dict(budget), 201)

    @app.post("/api/v1/budgets/<int:budget_id>/approve")
    @auth_required
    def approve_budget(budget_id):
        conn = get_db()
        result = conn.execute(
            "UPDATE presupuestos SET aprobado = 1, aprobado_en = ? WHERE usuario_id = ? AND id = ? AND aprobado = 0",
            (iso_utc(), g.user_id, budget_id),
        )
        conn.commit()
        if result.rowcount == 0:
            return error("PRESUPUESTO_NO_ENCONTRADO", "El presupuesto no existe o ya está aprobado", 404)
        return ok(dict(conn.execute("SELECT * FROM presupuestos WHERE id = ?", (budget_id,)).fetchone()))

    @app.get("/api/v1/notifications/settings")
    @auth_required
    def get_notification_settings():
        conn = get_db()
        row = conn.execute(
            "SELECT * FROM preferencias_notificacion WHERE usuario_id = ?", (g.user_id,)
        ).fetchone()
        return ok(dict(row))

    @app.patch("/api/v1/notifications/settings")
    @auth_required
    def update_notification_settings():
        data = body()
        conn = get_db()
        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(preferencias_notificacion)").fetchall()
        }
        allowed = {key: value for key, value in data.items() if key in columns and key != "usuario_id"}
        if not allowed:
            return ok(dict(conn.execute(
                "SELECT * FROM preferencias_notificacion WHERE usuario_id = ?", (g.user_id,)
            ).fetchone()))
        assignments = ", ".join(f"{column} = ?" for column in allowed)
        conn.execute(
            f"UPDATE preferencias_notificacion SET {assignments} WHERE usuario_id = ?",
            (*allowed.values(), g.user_id),
        )
        conn.commit()
        return ok(dict(conn.execute(
            "SELECT * FROM preferencias_notificacion WHERE usuario_id = ?", (g.user_id,)
        ).fetchone()))

    @app.post("/api/v1/device/register")
    def register_device():
        data = body()
        missing = require_fields(data, ("device_uid",))
        if missing:
            return error("CAMPOS_REQUERIDOS", "Falta device_uid", 422, {"campos": missing})
        conn = get_db()
        device = conn.execute(
            "SELECT * FROM dispositivos WHERE device_uid = ?", (data["device_uid"],)
        ).fetchone()
        if device and device["usuario_id"]:
            return error("DISPOSITIVO_VINCULADO", "El dispositivo ya está vinculado", 409)
        if device is None:
            cursor = conn.execute(
                """
                INSERT INTO dispositivos (device_uid, modelo, firmware, mac_address)
                VALUES (?, ?, ?, ?)
                """,
                (data["device_uid"], data.get("modelo"), data.get("firmware"), data.get("mac_address")),
            )
            device_id = cursor.lastrowid
        else:
            device_id = device["id"]
            conn.execute(
                """
                UPDATE dispositivos SET modelo = COALESCE(?, modelo),
                       firmware = COALESCE(?, firmware), actualizado_en = ?
                WHERE id = ?
                """,
                (data.get("modelo"), data.get("firmware"), iso_utc(), device_id),
            )
        pin = str(secrets.randbelow(1000000)).zfill(6)
        expires = iso_utc(now_utc() + timedelta(minutes=10))
        conn.execute(
            """
            INSERT INTO vinculacion_codigos
                (dispositivo_id, metodo, codigo_hash, expira_en)
            VALUES (?, 'pin', ?, ?)
            """,
            (device_id, token_hash(pin), expires),
        )
        conn.commit()
        return ok({"device_uid": data["device_uid"], "pin": pin, "expira_en": expires}, 201)

    @app.post("/api/v1/device/pair")
    @auth_required
    def pair_device():
        data = body()
        missing = require_fields(data, ("device_uid", "pin"))
        if missing:
            return error("CAMPOS_REQUERIDOS", "Faltan campos obligatorios", 422, {"campos": missing})
        conn = get_db()
        device = conn.execute(
            "SELECT * FROM dispositivos WHERE device_uid = ?", (data["device_uid"],)
        ).fetchone()
        if device is None:
            return error("DISPOSITIVO_NO_ENCONTRADO", "El dispositivo no existe", 404)
        code = conn.execute(
            """
            SELECT * FROM vinculacion_codigos
            WHERE dispositivo_id = ? AND usado_en IS NULL AND expira_en > ?
            ORDER BY id DESC LIMIT 1
            """,
            (device["id"], iso_utc()),
        ).fetchone()
        if code is None:
            return error("PIN_EXPIRADO", "El PIN no existe o expiró", 422)
        if code["intentos"] >= code["max_intentos"]:
            return error("PIN_BLOQUEADO", "El PIN superó el número de intentos", 429)
        if code["codigo_hash"] != token_hash(str(data["pin"])):
            conn.execute(
                "UPDATE vinculacion_codigos SET intentos = intentos + 1 WHERE id = ?", (code["id"],)
            )
            conn.commit()
            return error("PIN_INVALIDO", "El PIN es incorrecto", 401)
        raw_token = new_token()
        conn.execute(
            """
            UPDATE dispositivos
            SET usuario_id = ?, token_hash = ?, token_actualizado_en = ?,
                metodo_vinculacion = 'pin', vinculado_en = ?, estado_conexion = 'conectado',
                actualizado_en = ?
            WHERE id = ?
            """,
            (g.user_id, token_hash(raw_token), iso_utc(), iso_utc(), iso_utc(), device["id"]),
        )
        conn.execute(
            """
            UPDATE vinculacion_codigos
            SET usado_en = ?, usado_por_usuario_id = ?
            WHERE id = ?
            """,
            (iso_utc(), g.user_id, code["id"]),
        )
        conn.commit()
        return ok({"device_uid": data["device_uid"], "device_token": raw_token})

    @app.post("/api/v1/device/telemetry")
    @device_required
    def device_telemetry():
        data = body()
        conn = get_db()
        device = g.device
        battery = data.get("bateria")
        if battery is not None:
            battery = max(0, min(100, int(battery)))
        state = data.get("estado_dispositivo") or data.get("estado")
        if state not in (None, "reposo", "grabando", "procesando", "transmitiendo", "bloqueado"):
            state = None
        conn.execute(
            """
            UPDATE dispositivos
            SET ultima_conexion = ?, ultima_telemetria = ?,
                nivel_bateria = COALESCE(?, nivel_bateria),
                estado_dispositivo = COALESCE(?, estado_dispositivo),
                estado_conexion = 'conectado',
                firmware = COALESCE(?, firmware),
                registros_pendientes = COALESCE(?, registros_pendientes),
                actualizado_en = ?
            WHERE id = ?
            """,
            (
                iso_utc(),
                iso_utc(),
                battery,
                state,
                data.get("firmware"),
                data.get("registros_pendientes"),
                iso_utc(),
                device["id"],
            ),
        )
        conn.execute(
            """
            INSERT INTO dispositivos_telemetria
                (dispositivo_id, usuario_id, message_id, tipo, bateria, estado,
                 boton, audio_duracion_s, payload_json, fecha_local)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                device["id"],
                device["usuario_id"],
                data.get("message_id"),
                data.get("tipo") or "latido",
                battery,
                state,
                data.get("boton"),
                data.get("audio_duracion_s"),
                None,
                local_date(),
            ),
        )
        conn.commit()
        if not device["usuario_id"]:
            return error("DISPOSITIVO_NO_VINCULADO", "El dispositivo no está vinculado", 403)
        home = services.home_payload(conn, device["usuario_id"])
        return ok(
            {
                "vinculado": True,
                "salud": home["mascota"].get("salud"),
                "animo": home["mascota"].get("animo"),
                "cupo_restante": home["hoy"]["cupo_restante"],
                "hoy": home["hoy"],
            }
        )

    @app.get("/api/v1/device/notifications")
    @device_required
    def device_notification_list():
        if not g.device["usuario_id"]:
            return error("DISPOSITIVO_NO_VINCULADO", "El dispositivo no esta vinculado", 403)
        estado = request.args.get("estado")
        after_id = request.args.get("after_id", 0, type=int)
        limit = request.args.get("limit", 20, type=int)
        rows = services.device_notifications(
            get_db(),
            g.device["usuario_id"],
            g.device["id"],
            estado=estado,
            after_id=after_id,
            limit=limit,
        )
        return ok(
            {
                "notificaciones": rows,
                "ultima_id": rows[-1]["id"] if rows else after_id,
            }
        )

    @app.post("/api/v1/device/notifications/<int:notification_id>/ack")
    @device_required
    def device_notification_ack(notification_id):
        if not g.device["usuario_id"]:
            return error("DISPOSITIVO_NO_VINCULADO", "El dispositivo no esta vinculado", 403)
        data = body()
        row = services.ack_device_notification(
            get_db(),
            g.device["usuario_id"],
            g.device["id"],
            notification_id,
            estado=data.get("estado") or "leida",
        )
        if row is None:
            return error("NOTIFICACION_NO_ENCONTRADA", "La notificacion no existe", 404)
        return ok(row)

    @app.post("/api/v1/device/notifications/ack")
    @device_required
    def device_notification_bulk_ack():
        if not g.device["usuario_id"]:
            return error("DISPOSITIVO_NO_VINCULADO", "El dispositivo no esta vinculado", 403)
        data = body()
        ids = data.get("ids")
        if not isinstance(ids, list) or not ids:
            return error("CAMPOS_REQUERIDOS", "Envia una lista de ids", 422)
        updated = services.ack_device_notifications(
            get_db(),
            g.device["usuario_id"],
            g.device["id"],
            ids,
            estado=data.get("estado") or "leida",
        )
        return ok({"actualizadas": updated})

    @app.post("/api/v1/device/messages")
    @device_required
    def device_message():
        if not g.device["usuario_id"]:
            return error("DISPOSITIVO_NO_VINCULADO", "El dispositivo no está vinculado", 403)
        data = datos_entrantes()
        try:
            payload, status = procesar_mensaje_voz(
                get_db(),
                g.device["usuario_id"],
                texto=data.get("texto"),
                archivo=request.files.get("audio"),
                message_id=data.get("message_id"),
                device_id=g.device["id"],
                device_uid=g.device["device_uid"],
                origen="dispositivo",
                idioma=data.get("idioma"),
            )
        except ErrorSolicitud as exc:
            return error(exc.codigo, exc.mensaje, exc.estado, exc.detalles)
        return ok(payload, status)

    @app.post("/api/v1/voice/synthesize")
    @auth_required
    def app_synthesize_voice():
        return _sintetizar_voz(body())

    @app.post("/api/v1/device/voice/synthesize")
    @device_required
    def device_synthesize_voice():
        if not g.device["usuario_id"]:
            return error("DISPOSITIVO_NO_VINCULADO", "El dispositivo no está vinculado", 403)
        return _sintetizar_voz(body())

    @app.post("/api/v1/device/messages/<int:message_id>/confirm")
    @device_required
    def device_confirm_message(message_id):
        if not g.device["usuario_id"]:
            return error("DISPOSITIVO_NO_VINCULADO", "El dispositivo no está vinculado", 403)
        payload = services.confirm_message(get_db(), g.device["usuario_id"], message_id)
        if payload is None:
            return error("MENSAJE_NO_ENCONTRADO", "El mensaje no existe", 404)
        conversation.invalidar_accion_pendiente(g.device["usuario_id"], message_id)
        return ok(payload)

    @app.post("/api/v1/device/close-day")
    @device_required
    def device_close_day():
        if not g.device["usuario_id"]:
            return error("DISPOSITIVO_NO_VINCULADO", "El dispositivo no está vinculado", 403)
        return ok(services.close_day(get_db(), g.device["usuario_id"], local_date()))

    @app.get("/api/v1/device")
    @auth_required
    def list_devices():
        conn = get_db()
        rows = conn.execute(
            """
            SELECT id, device_uid, modelo, firmware, estado_conexion, estado_dispositivo,
                   nivel_bateria, ultima_conexion, vinculado_en
            FROM dispositivos WHERE usuario_id = ? ORDER BY id
            """,
            (g.user_id,),
        ).fetchall()
        return ok(dict_rows(rows))

    @app.post("/api/v1/device/unlink")
    @auth_required
    def unlink_device():
        data = body()
        if not data.get("device_uid"):
            return error("CAMPOS_REQUERIDOS", "Falta device_uid", 422)
        conn = get_db()
        result = conn.execute(
            """
            UPDATE dispositivos
            SET usuario_id = NULL, estado_conexion = 'desconectado', actualizado_en = ?
            WHERE usuario_id = ? AND device_uid = ?
            """,
            (iso_utc(), g.user_id, data["device_uid"]),
        )
        conn.commit()
        if result.rowcount == 0:
            return error("DISPOSITIVO_NO_ENCONTRADO", "El dispositivo no está vinculado", 404)
        return ok({"desvinculado": True})

    @app.post("/api/v1/finagotchi/telemetry")
    @device_required
    def legacy_telemetry():
        return device_telemetry()

    return app


app = create_app()


if __name__ == "__main__":
    # El reinicio automatico de Flask (debug) corta las peticiones en vuelo
    # cuando se cambia un archivo: durante una demo eso parte el audio a
    # medio enviar. Se deja desactivado por defecto y se puede activar con
    # FLASK_DEBUG=1.
    depurar = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", 5001)),
        debug=depurar,
        use_reloader=depurar,
    )