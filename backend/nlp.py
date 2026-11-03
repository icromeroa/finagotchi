import re
import unicodedata
from decimal import Decimal, InvalidOperation


NUMBERS = {
    "cero": 0,
    "un": 1,
    "uno": 1,
    "dos": 2,
    "tres": 3,
    "cuatro": 4,
    "cinco": 5,
    "seis": 6,
    "siete": 7,
    "ocho": 8,
    "nueve": 9,
    "diez": 10,
    "once": 11,
    "doce": 12,
    "trece": 13,
    "catorce": 14,
    "quince": 15,
    "dieciseis": 16,
    "diecisiete": 17,
    "dieciocho": 18,
    "diecinueve": 19,
    "veinte": 20,
    "treinta": 30,
    "cuarenta": 40,
    "cincuenta": 50,
    "sesenta": 60,
    "setenta": 70,
    "ochenta": 80,
    "noventa": 90,
    "cien": 100,
    "ciento": 100,
    "doscientos": 200,
    "trescientos": 300,
    "cuatrocientos": 400,
    "quinientos": 500,
    "seiscientos": 600,
    "setecientos": 700,
    "ochocientos": 800,
    "novecientos": 900,
    "veintiuno": 21,
    "veintiun": 21,
    "veintidos": 22,
    "veintitres": 23,
    "veinticuatro": 24,
    "veinticinco": 25,
    "veintiseis": 26,
    "veintisiete": 27,
    "veintiocho": 28,
    "veintinueve": 29,
}

NUMBERS_CENTENAS = {
    "ciento": 100,
    "doscientos": 200,
    "trescientos": 300,
    "cuatrocientos": 400,
    "quinientos": 500,
    "seiscientos": 600,
    "setecientos": 700,
    "ochocientos": 800,
    "novecientos": 900,
}

NUMBERS_DECENAS = {
    "veinte": 20,
    "treinta": 30,
    "cuarenta": 40,
    "cincuenta": 50,
    "sesenta": 60,
    "setenta": 70,
    "ochenta": 80,
    "noventa": 90,
}

ESCALAS = {"mil", "millon", "millones"}

INCOME_WORDS = (
    "ingreso",
    "ingrese",
    "recibi",
    "recibe",
    "me pagaron",
    "pagaron",
    "cobre",
    "sueldo",
    "salario",
    "quincena",
    "gane",
    "ganancia",
    "deposito",
    "transferencia recibida",
)

SAVING_WORDS = (
    "ahorre",
    "ahorro",
    "guarde",
    "guardar",
    "separe",
    "meta",
)

STATUS_WORDS = (
    "como voy",
    "como me fue",
    "como va",
    "resumen",
    "balance",
    "estado",
    "cuanto llevo",
)

CLOSE_WORDS = (
    "cerrar dia",
    "cierra el dia",
    "cerrar el dia",
    "terminar dia",
    "termina el dia",
    "finalizar dia",
    "finaliza el dia",
    "cierre del dia",
)


def normalize(text):
    text = unicodedata.normalize("NFKD", str(text or "").lower())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", text).strip()


def word_in_text(word, text):
    normalized_word = normalize(word)
    if not normalized_word:
        return False
    return re.search(rf"(?<!\w){re.escape(normalized_word)}(?!\w)", text) is not None


def amount_from_words(text):
    """Interpreta un monto escrito en palabras.

    Ejemplos: "catorce mil" -> 14000, "treinta y cinco mil" -> 35000,
    "ciento veinte mil" -> 120000, "un millon" -> 1000000.
    """
    tokens = [token for token in re.split(r"[^a-z]+", str(text or "").lower()) if token]
    if not tokens:
        return None

    mejor = None
    indice = 0
    while indice < len(tokens):
        if tokens[indice] not in NUMBERS and tokens[indice] not in ESCALAS:
            indice += 1
            continue
        valor, consumidos, escala = _parse_number_tokens(tokens, indice)
        inicio_word = tokens[indice]
        aceptable = (
            escala
            or inicio_word in NUMBERS_DECENAS
            or inicio_word in NUMBERS_CENTENAS
        )
        if valor and aceptable:
            if mejor is None or valor > mejor:
                mejor = valor
        indice += max(consumidos, 1)
    return mejor


def _parse_number_tokens(tokens, inicio):
    """Lee un numero en palabras desde tokens[inicio].

    Devuelve (valor, tokens_consumidos, uso_escala).
    """
    actual = 0
    total = 0
    escala = False
    i = inicio
    while i < len(tokens):
        token = tokens[i]
        if token in NUMBERS_CENTENAS:
            actual += NUMBERS_CENTENAS[token]
            i += 1
            continue
        if token in NUMBERS_DECENAS:
            actual += NUMBERS_DECENAS[token]
            i += 1
            if (
                i + 1 < len(tokens)
                and tokens[i] == "y"
                and tokens[i + 1] in NUMBERS
                and tokens[i + 1] not in ("cien", "ciento")
            ):
                actual += NUMBERS[tokens[i + 1]]
                i += 2
            continue
        if token in NUMBERS:
            actual += NUMBERS[token]
            i += 1
            continue
        if token == "mil":
            total += (actual or 1) * 1000
            actual = 0
            escala = True
            i += 1
            continue
        if token in ("millon", "millones"):
            total += (actual or 1) * 1000000
            actual = 0
            escala = True
            i += 1
            continue
        break
    return total + actual, i - inicio, escala


def _parse_amount_digits(text):
    match = re.search(
        r"(\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?)\s*(millones|millon|mil|k)?",
        text,
    )
    if not match:
        return None

    raw = match.group(1)
    suffix = match.group(2)
    try:
        if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", raw):
            value = Decimal(raw.replace(".", "").replace(",", ""))
        else:
            value = Decimal(raw.replace(",", "."))
    except InvalidOperation:
        return None

    if suffix in ("millones", "millon"):
        value *= 1000000
    elif suffix in ("mil", "k"):
        value *= 1000
    elif value < 1000 and re.search(r"\bmil\b", text):
        value *= 1000

    value = int(value)
    return value if value > 0 else None


def parse_amount(text):
    """Obtiene el monto de un texto en cifras o en palabras."""
    digits = _parse_amount_digits(text)
    if digits is not None:
        return digits
    return amount_from_words(text)


def detect_intent(text):
    normalized = normalize(text)
    if any(word_in_text(word, normalized) for word in CLOSE_WORDS):
        return "cerrar_dia"
    if any(word_in_text(word, normalized) for word in STATUS_WORDS):
        return "consulta_estado"
    return "registrar"


def detect_type(text):
    normalized = normalize(text)
    if any(word_in_text(word, normalized) for word in SAVING_WORDS):
        return "ahorro"
    if any(word_in_text(word, normalized) for word in INCOME_WORDS):
        return "ingreso"
    return "gasto"


def keyword_match(conn, table, user_id):
    query = {
        "categoria": """
            SELECT p.palabra, c.id, c.nombre, c.tipo
            FROM categoria_palabras p
            JOIN categorias c
              ON c.usuario_id = p.usuario_id AND c.id = p.categoria_id
            WHERE p.usuario_id = ? AND c.activa = 1
        """,
        "cuenta": """
            SELECT p.palabra, c.id, c.nombre
            FROM cuenta_palabras p
            JOIN cuentas c
              ON c.usuario_id = p.usuario_id AND c.id = p.cuenta_id
            WHERE p.usuario_id = ?
        """,
    }[table]
    return conn.execute(query, (user_id,)).fetchall()


def detect_category(conn, user_id, text, transaction_type):
    normalized = normalize(text)
    if transaction_type == "ahorro":
        return None
    for row in keyword_match(conn, "categoria", user_id):
        if row["tipo"] != transaction_type:
            continue
        if word_in_text(row["palabra"], normalized):
            return dict(row)
    fallback = "Otros ingresos" if transaction_type == "ingreso" else "Otros"
    row = conn.execute(
        """
        SELECT id, nombre, tipo FROM categorias
        WHERE usuario_id = ? AND tipo = ? AND nombre = ? AND activa = 1
        """,
        (user_id, transaction_type, fallback),
    ).fetchone()
    if row:
        return dict(row)
    row = conn.execute(
        """
        SELECT id, nombre, tipo FROM categorias
        WHERE usuario_id = ? AND tipo = ? AND activa = 1
        ORDER BY id LIMIT 1
        """,
        (user_id, transaction_type),
    ).fetchone()
    return dict(row) if row else None


def detect_account(conn, user_id, text):
    normalized = normalize(text)
    for row in keyword_match(conn, "cuenta", user_id):
        if word_in_text(row["palabra"], normalized):
            return dict(row)
    row = conn.execute(
        """
        SELECT id, nombre FROM cuentas
        WHERE usuario_id = ? AND es_por_defecto = 1
        ORDER BY id LIMIT 1
        """,
        (user_id,),
    ).fetchone()
    return dict(row) if row else None


def interpret(conn, user_id, text):
    normalized = normalize(text)
    intent = detect_intent(normalized)
    if intent != "registrar":
        return {"intent": intent, "texto": text, "transacciones": []}

    transaction_type = detect_type(normalized)
    amount = parse_amount(normalized)
    category = detect_category(conn, user_id, normalized, transaction_type)
    account = detect_account(conn, user_id, normalized)
    if amount is None:
        return {
            "intent": "requiere_aclaracion",
            "texto": text,
            "error": "No se identificÃ³ un monto",
            "transacciones": [],
        }
    if account is None:
        return {
            "intent": "requiere_aclaracion",
            "texto": text,
            "error": "No hay una cuenta disponible",
            "transacciones": [],
        }
    if transaction_type != "ahorro" and category is None:
        return {
            "intent": "requiere_aclaracion",
            "texto": text,
            "error": "No hay una categorÃ­a disponible",
            "transacciones": [],
        }

    return {
        "intent": "registrar",
        "texto": text,
        "transacciones": [
            {
                "tipo": transaction_type,
                "monto": amount,
                "categoria_id": category["id"] if category else None,
                "categoria": category["nombre"] if category else None,
                "cuenta_id": account["id"],
                "cuenta": account["nombre"],
                "concepto": text[:255],
                "confianza": 0.9 if category else 0.7,
            }
        ],
    }
