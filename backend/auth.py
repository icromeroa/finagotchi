from datetime import timedelta
from functools import wraps

from flask import current_app, g, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from .api_utils import error
from .db import (
    ACCESS_TOKEN_MAX_AGE,
    REFRESH_TOKEN_DAYS,
    get_db,
    iso_utc,
    new_token,
    now_utc,
    token_hash,
)


def serializer():
    return URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"], salt="finagotchi-access"
    )


def create_access_token(user_id):
    return serializer().dumps({"uid": user_id, "tipo": "access"})


def read_access_token(raw):
    return serializer().loads(raw, max_age=ACCESS_TOKEN_MAX_AGE)


def create_refresh_token(conn, user_id, user_agent=None, ip=None):
    raw = new_token()
    expires = now_utc() + timedelta(days=REFRESH_TOKEN_DAYS)
    conn.execute(
        """
        INSERT INTO sesiones_refresco
            (usuario_id, token_hash, expira_en, user_agent, ip)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, token_hash(raw), iso_utc(expires), user_agent, ip),
    )
    return raw, expires


def issue_tokens(conn, user_id):
    return {
        "access_token": create_access_token(user_id),
        "refresh_token": create_refresh_token(
            conn,
            user_id,
            request.headers.get("User-Agent"),
            request.remote_addr,
        )[0],
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_MAX_AGE,
    }


def hash_password(password):
    return generate_password_hash(password)


def verify_password(password_hash, password):
    return bool(password_hash) and check_password_hash(password_hash, password)


def auth_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return error("NO_AUTENTICADO", "Falta el token de acceso", 401)
        raw = header.split(" ", 1)[1].strip()
        try:
            payload = read_access_token(raw)
        except SignatureExpired:
            return error("TOKEN_EXPIRADO", "El token de acceso expiró", 401)
        except BadSignature:
            return error("TOKEN_INVALIDO", "El token de acceso no es válido", 401)

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM usuarios WHERE id = ? AND estado = 'activo'",
            (payload.get("uid"),),
        ).fetchone()
        if user is None:
            return error("USUARIO_NO_ENCONTRADO", "El usuario no existe", 401)
        g.user = dict(user)
        g.user_id = user["id"]
        return view(*args, **kwargs)

    return wrapped


def device_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        raw = request.headers.get("X-Device-Token", "").strip()
        if not raw:
            return error("DISPOSITIVO_NO_AUTENTICADO", "Falta el token del dispositivo", 401)
        conn = get_db()
        device = conn.execute(
            "SELECT * FROM dispositivos WHERE token_hash = ?",
            (token_hash(raw),),
        ).fetchone()
        if device is None:
            return error("DISPOSITIVO_NO_AUTENTICADO", "Token de dispositivo inválido", 401)
        g.device = dict(device)
        return view(*args, **kwargs)

    return wrapped
