import os
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

CONFIRMAR_WORDS = (
    "si",
    "sí",
    "ok",
    "okay",
    "correcto",
    "esta bien",
    "está bien",
    "confirmo",
    "confirmar",
    "dale",
    "claro",
    "acepto",
    "adelante",
    "de acuerdo",
    "perfecto",
)

CANCELAR_WORDS = (
    "no",
    "cancela",
    "cancelar",
    "cancelo",
    "descarta",
    "descartar",
    "olvidalo",
    "olvídalo",
    "dejalo",
    "déjalo",
)

AYUDA_WORDS = (
    "ayuda",
    "que puedo decir",
    "qué puedo decir",
    "que puedo hacer",
    "cómo funciona",
    "como funciona",
)

CLOSE_WORDS = (
    "cerrar dia",
    "cierra el dia",
    "cerra el dia",
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


def detect_type_explicit(text):
    """Tipo solo si la frase lo dice; None si no hay marca explícita.

    Sirve para corregir un pendiente sin que la falta de palabra de tipo
    convierta todo en «gasto» por defecto.
    """
    normalized = normalize(text)
    if any(word_in_text(word, normalized) for word in SAVING_WORDS):
        return "ahorro"
    if any(word_in_text(word, normalized) for word in INCOME_WORDS):
        return "ingreso"
    if any(
        word_in_text(word, normalized)
        for word in ("gaste", "gasto", "gasto", "compré", "compre", "pague", "pago")
    ):
        return "gasto"
    return None


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


def detect_account_explicit(conn, user_id, text):
    """Cuenta solo si se menciona de forma explícita; None si no se menciona.

    A diferencia de ``detect_account`` no cae a la cuenta por defecto: para
    corregir un pendiente, una frase como «es de hoy» no debe mover el
    movimiento a Efectivo.
    """
    normalized = normalize(text)
    if not normalized:
        return None
    for row in keyword_match(conn, "cuenta", user_id):
        if word_in_text(row["palabra"], normalized):
            return dict(row)
    for row in conn.execute(
        "SELECT id, nombre FROM cuentas WHERE usuario_id = ? ORDER BY id",
        (user_id,),
    ):
        if word_in_text(row["nombre"], normalized):
            return dict(row)
    return None


def detect_category_explicit(conn, user_id, text, transaction_type):
    """Categoría solo si la frase la menciona; None si no hay mención."""
    normalized = normalize(text)
    if transaction_type == "ahorro" or not normalized:
        return None
    for row in keyword_match(conn, "categoria", user_id):
        if row["tipo"] != transaction_type:
            continue
        if word_in_text(row["palabra"], normalized):
            return dict(row)
    for row in conn.execute(
        """
        SELECT id, nombre, tipo FROM categorias
        WHERE usuario_id = ? AND tipo = ? AND activa = 1 ORDER BY id
        """,
        (user_id, transaction_type),
    ):
        if word_in_text(row["nombre"], normalized):
            return dict(row)
    return None


def _distancia(a, b):
    """Distancia de Levenshtein entre dos textos."""
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    anterior = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        actual = [i]
        for j, cb in enumerate(b, start=1):
            actual.append(
                min(
                    anterior[j] + 1,
                    actual[j - 1] + 1,
                    anterior[j - 1] + (ca != cb),
                )
            )
        anterior = actual
    return anterior[-1]


def coincide_en_catalogo(valor, catalogo):
    """Busca el nombre del catalogo que corresponde a lo que dijo el modelo.

    Primero intenta coincidencia exacta sin tildes ni mayusculas. Si no hay,
    acepta un solo caracter de diferencia cuando el nombre es largo, para no
    perder "Nequi" por una transcripcion como "Neqi".
    """
    if not valor:
        return None
    objetivo = normalize(valor)
    for item in catalogo:
        if normalize(item["nombre"]) == objetivo:
            return item
    for item in catalogo:
        nombre = normalize(item["nombre"])
        if len(nombre) >= 5 and _distancia(nombre, objetivo) <= 1:
            return item
    return None


def metas_usuario(conn, user_id):
    """Metas activas del usuario, con el nombre que usa la voz."""
    return [
        {"id": row["id"], "nombre": row["nombre"]}
        for row in conn.execute(
            """
            SELECT id, nombre FROM metas
            WHERE usuario_id = ? AND is_deleted = 0 AND estado = 'activa'
            ORDER BY prioridad, fecha_limite, id
            """,
            (user_id,),
        )
    ]


def palabras_clave_usuario(conn, user_id):
    """Nombres de cuentas, categorias y metas del usuario, para las hotwords."""
    cuentas = [
        row["nombre"]
        for row in conn.execute(
            "SELECT nombre FROM cuentas WHERE usuario_id = ? ORDER BY id", (user_id,)
        )
    ]
    categorias = [
        row["nombre"]
        for row in conn.execute(
            "SELECT nombre FROM categorias WHERE usuario_id = ? AND activa = 1 ORDER BY id",
            (user_id,),
        )
    ]
    metas = [meta["nombre"] for meta in metas_usuario(conn, user_id)]
    return ", ".join(sorted(set(cuentas + categorias + metas)))


EXPRESIONES_META = (
    "para mi meta de",
    "para la meta de",
    "para mi meta",
    "para la meta",
    "meta de",
    "meta para",
    "ahorrar para",
    "ahorro para",
)


def menciona_meta(text):
    normalized = normalize(text)
    return any(word_in_text(expresion, normalized) for expresion in EXPRESIONES_META)


def detect_goal(conn, user_id, text):
    """Asocia un texto con una meta activa del usuario.

    Acepta el nombre exacto con o sin tildes y frases como "para mi meta de mi
    nuevo celular". Si no hay coincidencia segura devuelve None: nunca adivina
    una meta distinta.
    """
    metas = metas_usuario(conn, user_id)
    if not metas:
        return None
    normalized = normalize(text)
    for meta in metas:
        nombre = normalize(meta["nombre"])
        if nombre and word_in_text(nombre, normalized):
            return meta
    # Quita las palabras de enlace para comparar el resto de la frase.
    recortado = normalized
    for expresion in EXPRESIONES_META:
        recortado = recortado.replace(normalize(expresion), " ")
    recortado = re.sub(r"\b(mi|mis|la|las|el|los|de|del|para|por)\b", " ", recortado)
    recortado = re.sub(r"\s+", " ", recortado).strip()
    if recortado:
        return coincide_en_catalogo(recortado, metas)
    return None


def _entero(valor):
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return None
    return numero if numero > 0 else None


_PALABRAS_NO_CUENTA = {
    "la", "el", "los", "las", "mi", "mis", "un", "una", "unos", "unas",
    "hoy", "ayer", "anteayer", "antier", "mes", "semana", "ano",
    "manana", "noche", "tarde", "trabajo", "almuerzo", "comida",
}


def pista_cuenta_no_reconocida(conn, user_id, texto, tipo_final):
    """Palabra tras «por/con» que parece una cuenta pero no se reconoce.

    Devuelve la palabra desconocida o None. Las palabras de categoría
    («por trabajo») y los artículos no cuentan como pista de cuenta.
    """
    normalized = normalize(texto)
    for match in re.finditer(r"\b(?:por|con)\s+([a-z]+)\b", normalized):
        palabra = match.group(1)
        if palabra in _PALABRAS_NO_CUENTA:
            continue
        if detect_category_explicit(conn, user_id, palabra, tipo_final) is not None:
            continue
        if detect_account_explicit(conn, user_id, palabra) is not None:
            continue
        return palabra
    return None


def construir_movimiento(
    conn,
    user_id,
    texto,
    tipo=None,
    monto=None,
    categoria=None,
    cuenta=None,
    meta=None,
    concepto=None,
    origen="reglas",
    proveedor=None,
    latencia_ms=None,
):
    """Arma una propuesta de movimiento validada contra el catalogo.

    Es la misma ruta para las reglas y para el agente conversacional. No
    escribe en la base: solo devuelve la propuesta pendiente de confirmacion.
    """
    normalized = normalize(texto)
    tipo_final = str(tipo or "").strip().lower()
    if tipo_final not in ("gasto", "ingreso", "ahorro"):
        tipo_final = detect_type(normalized)

    monto_final = _entero(monto)
    if monto_final is None:
        monto_final = parse_amount(normalized)

    metas = metas_usuario(conn, user_id)
    categorias = [
        {"id": row["id"], "nombre": row["nombre"], "tipo": row["tipo"]}
        for row in conn.execute(
            "SELECT id, nombre, tipo FROM categorias "
            "WHERE usuario_id = ? AND activa = 1 ORDER BY id",
            (user_id,),
        )
    ]
    cuentas = [
        {"id": row["id"], "nombre": row["nombre"]}
        for row in conn.execute(
            "SELECT id, nombre FROM cuentas WHERE usuario_id = ? ORDER BY id", (user_id,)
        )
    ]

    meta_final = coincide_en_catalogo(meta, metas)
    if meta_final is None and tipo_final == "ahorro":
        meta_final = detect_goal(conn, user_id, texto)

    if monto_final is None:
        return {
            "intent": "requiere_aclaracion",
            "texto": texto,
            "error": "No se identificó un monto",
            "transacciones": [],
        }
    if not cuentas:
        return {
            "intent": "requiere_aclaracion",
            "texto": texto,
            "error": "No hay una cuenta disponible",
            "transacciones": [],
        }

    if tipo_final == "ahorro":
        categoria_final = None
        if meta_final is None and menciona_meta(texto):
            return {
                "intent": "requiere_aclaracion",
                "texto": texto,
                "error": "No encontré esa meta",
                "meta_sugerida": meta or nombre_meta_probable(texto),
                "transacciones": [],
            }
    else:
        meta_final = None
        categoria_final = coincide_en_catalogo(categoria, categorias)
        if categoria_final is None:
            categoria_final = detect_category(conn, user_id, normalized, tipo_final)
        if categoria_final is None:
            return {
                "intent": "requiere_aclaracion",
                "texto": texto,
                "error": "No hay una categoría disponible",
                "transacciones": [],
            }
        if categoria_final["tipo"] != tipo_final:
            categoria_final = _categoria_fallback(conn, user_id, tipo_final)

    # La cuenta del LLM solo vale si se dijo en el texto; «Nuwank» no es «Nu».
    cuenta_entidad = None
    if cuenta and word_in_text(normalize(cuenta), normalized):
        cuenta_entidad = coincide_en_catalogo(cuenta, cuentas)
    cuenta_final = cuenta_entidad or detect_account_explicit(
        conn, user_id, normalized
    )
    if cuenta_final is None:
        pista = pista_cuenta_no_reconocida(conn, user_id, normalized, tipo_final)
        if pista:
            return {
                "intent": "requiere_aclaracion",
                "texto": texto,
                "error": (
                    f"No reconocí la cuenta \"{pista}\". "
                    "Dime el nombre exacto de la cuenta o dime que use Efectivo."
                ),
                "cuenta_sugerida": pista,
                "transacciones": [],
            }
        cuenta_final = detect_account(conn, user_id, normalized)
    if cuenta_final is None:
        return {
            "intent": "requiere_aclaracion",
            "texto": texto,
            "error": "No hay una cuenta disponible",
            "transacciones": [],
        }

    resumen = (concepto or "").strip()[:255] or texto[:255]
    return {
        "intent": "registrar",
        "texto": texto,
        "error": None,
        "origen": "ia" if proveedor else origen,
        "proveedor": proveedor,
        "latencia_ia_ms": latencia_ms,
        "transacciones": [
            {
                "tipo": tipo_final,
                "monto": monto_final,
                "categoria_id": categoria_final["id"] if categoria_final else None,
                "categoria": categoria_final["nombre"] if categoria_final else None,
                "cuenta_id": cuenta_final["id"],
                "cuenta": cuenta_final["nombre"],
                "meta_id": meta_final["id"] if meta_final else None,
                "meta": meta_final["nombre"] if meta_final else None,
                "meta_mencionada": meta or (texto if menciona_meta(texto) else None),
                "concepto": resumen,
                "confianza": 0.85 if (categoria_final or meta_final) else 0.7,
            }
        ],
    }


def parse_frecuencia(text):
    normalized = normalize(text)
    for frecuencia, palabras in (
        ("diaria", ("diario", "diaria", "cada dia", "todos los dias")),
        ("semanal", ("semanal", "semana", "cada semana")),
        ("quincenal", ("quincenal", "quincena", "cada quincena")),
        ("mensual", ("mensual", "mes", "cada mes", "al mes")),
    ):
        if any(word_in_text(palabra, normalized) for palabra in palabras):
            return frecuencia
    return None


def parse_plazo(text, base_date=None):
    """Interpreta un plazo dicho en voz y calcula la fecha limite en Python.

    Devuelve ``{"meses", "dias", "fecha_limite"}`` o None si no hay plazo.
    """
    normalized = normalize(text)
    plural = re.search(
        r"\b(\d{1,3}|un|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce)"
        r"\s*(dias?|semanas?|meses?|mes|anos?|año)\b",
        normalized,
    )
    if not plural:
        if word_in_text("un ano", normalized) or word_in_text("un año", normalized):
            return _plazo_resultado(12, 0, base_date)
        return None
    texto_cantidad = plural.group(1)
    if texto_cantidad.isdigit():
        cantidad = int(texto_cantidad)
    else:
        cantidad = amount_from_words(texto_cantidad)
        if cantidad is None:
            cantidad = NUMBERS.get(texto_cantidad) or {"un": 1, "una": 1}.get(
                texto_cantidad, 1
            )
    unidad = plural.group(2)
    if unidad.startswith("dia"):
        return _plazo_resultado(0, cantidad, base_date)
    if unidad.startswith("semana"):
        return _plazo_resultado(0, cantidad * 7, base_date)
    if unidad.startswith("mes"):
        return _plazo_resultado(cantidad, 0, base_date)
    if unidad.startswith("ano") or unidad.startswith("año"):
        return _plazo_resultado(cantidad * 12, 0, base_date)
    return None


def _plazo_resultado(meses, dias, base_date=None):
    from datetime import date as date_cls
    from datetime import timedelta

    base = base_date or date_cls.today()
    total_meses = max(0, int(meses))
    year = base.year + (base.month - 1 + total_meses) // 12
    month = (base.month - 1 + total_meses) % 12 + 1
    day = min(base.day, _dias_del_mes(year, month))
    limite = date_cls(year, month, day) + timedelta(days=max(0, int(dias)))
    return {
        "meses": total_meses,
        "dias": max(0, int(dias)),
        "fecha_limite": limite.isoformat(),
    }


def _dias_del_mes(year, month):
    import calendar

    return calendar.monthrange(year, month)[1]


def detect_priority(text):
    normalized = normalize(text)
    if any(word_in_text(palabra, normalized) for palabra in ("alta", "urgente", "primero")):
        return 1
    if any(word_in_text(palabra, normalized) for palabra in ("media", "normal")):
        return 3
    if any(word_in_text(palabra, normalized) for palabra in ("baja", "despues")):
        return 5
    match = re.search(r"prioridad\s*(?:numero\s*)?(\d)", normalized)
    if match:
        numero = int(match.group(1))
        if 1 <= numero <= 5:
            return numero
    return None


def nombre_meta_probable(text):
    """Extrae el nombre de una meta nueva de una frase natural."""
    normalized = normalize(text)
    patrones = (
        r"(?:meta|objetivo)\s+(?:de|para)\s+(.+)",
        r"(?:quiero|quisiera|necesito|me gustaria)\s+(?:comprar|comprarme|ahorrar para|ahorrar por)\s+(.+)",
        r"(?:estoy ahorrando|ahorrar)\s+para\s+(.+)",
    )
    for patron in patrones:
        match = re.search(patron, normalized)
        if match:
            nombre = re.sub(
                r"\b(una|un|unos|unas|mi|mis|comprarme|comprar|para|de|del|la|el|los|las)\b",
                " ",
                match.group(1),
            )
            nombre = re.sub(r"\s+", " ", nombre).strip(" .,;")
            if nombre:
                return nombre[:30]
    return None


MESES_RANGO = {
    "enero": 1,
    "ene": 1,
    "febrero": 2,
    "feb": 2,
    "marzo": 3,
    "mar": 3,
    "abril": 4,
    "abr": 4,
    "mayo": 5,
    "may": 5,
    "junio": 6,
    "jun": 6,
    "julio": 7,
    "jul": 7,
    "agosto": 8,
    "ago": 8,
    "septiembre": 9,
    "setiembre": 9,
    "sep": 9,
    "octubre": 10,
    "oct": 10,
    "noviembre": 11,
    "nov": 11,
    "diciembre": 12,
    "dic": 12,
}

MESES_NOMBRES = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


def _fecha_valida(anio, mes, dia):
    from datetime import date as date_cls

    try:
        return date_cls(int(anio), int(mes), int(dia))
    except (TypeError, ValueError):
        return None


def _fecha_desde_expresion(texto, base):
    """Interpreta una fecha suelta (no un rango) y devuelve ``date`` o None."""
    normalized = normalize(texto)

    match = re.search(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", normalized)
    if match:
        return _fecha_valida(match.group(1), match.group(2), match.group(3))

    match = re.search(
        r"(?<!\d)(\d{1,2})[/\-.](\d{1,2})(?:[/\-.](\d{2,4}))?(?!\d)", normalized
    )
    if match:
        anio = int(match.group(3)) if match.group(3) else base.year
        if anio < 100:
            anio += 2000
        return _fecha_valida(anio, match.group(2), match.group(1))

    match = re.search(
        r"\b(\d{1,2})\s+de\s+([a-z]+)(?:\s+de\s+(\d{4}))?\b", normalized
    )
    if match and match.group(2) in MESES_RANGO:
        return _fecha_valida(
            match.group(3) or base.year, MESES_RANGO[match.group(2)], match.group(1)
        )

    match = re.search(
        r"\b(\d{1,2})\s+([a-z]+)(?:\s+de\s+(\d{4}))?\b", normalized
    )
    if match and match.group(2) in MESES_RANGO:
        return _fecha_valida(
            match.group(3) or base.year, MESES_RANGO[match.group(2)], match.group(1)
        )
    return None


def _etiqueta_dia(fecha):
    return f"{fecha.day} de {MESES_NOMBRES[fecha.month - 1]} de {fecha.year}"


def _etiqueta_rango(inicio, fin):
    if inicio == fin:
        return _etiqueta_dia(inicio)
    if inicio.year == fin.year and inicio.month == fin.month:
        return (
            f"del {inicio.day} al {fin.day} de "
            f"{MESES_NOMBRES[inicio.month - 1]}"
        )
    if inicio.year == fin.year:
        return (
            f"del {inicio.day} de {MESES_NOMBRES[inicio.month - 1]} "
            f"al {fin.day} de {MESES_NOMBRES[fin.month - 1]}"
        )
    return (
        f"del {inicio.day} de {MESES_NOMBRES[inicio.month - 1]} de {inicio.year} "
        f"al {fin.day} de {MESES_NOMBRES[fin.month - 1]} de {fin.year}"
    )


def _resultado_rango(inicio, fin, etiqueta, alcance, expresion):
    if inicio > fin:
        inicio, fin = fin, inicio
    return {
        "desde": inicio.isoformat(),
        "hasta": fin.isoformat(),
        "etiqueta": etiqueta,
        "alcance": alcance,
        "expresion": expresion,
    }


def resolver_rango(texto, hoy=None):
    """Resuelve una expresión temporal en un rango ISO determinista.

    El LLM puede copiar la expresión, pero nunca calcula la fecha: esta
    función lo hace con Python para que «esta semana» sea siempre lunes a hoy.
    """
    from datetime import date as date_cls
    from datetime import timedelta

    base = hoy or date_cls.today()
    if isinstance(base, str):
        base = date_cls.fromisoformat(base)
    normalized = normalize(texto)
    # «No es de ayer, es de hoy»: la fecha negada no puede ganar por aparecer
    # primero. Se retira la mención negada antes de buscar cualquier día.
    normalized = re.sub(
        r"\bno\s+(?:es|fue|era|son)\s*(?:de\s*)?(?:ayer|hoy|anteayer|antier)\b",
        " ",
        normalized,
    )

    match = re.search(
        r"\b(?:del|desde el|desde|entre el|entre|de)\s+"
        r"(\d{1,2})(?:\s+de\s+([a-z]+))?(?:\s+de\s+(\d{4}))?"
        r"\s+(?:al|a|hasta el|hasta|y)\s+"
        r"(\d{1,2})(?:\s+de\s+([a-z]+))?(?:\s+de\s+(\d{4}))?",
        normalized,
    )
    if match:
        dia1, dia2 = int(match.group(1)), int(match.group(4))
        mes1 = MESES_RANGO.get(match.group(2)) if match.group(2) else None
        mes2 = MESES_RANGO.get(match.group(5)) if match.group(5) else None
        anio1 = int(match.group(3)) if match.group(3) else None
        anio2 = int(match.group(6)) if match.group(6) else None
        if mes1 is None and mes2 is not None:
            mes1 = mes2
        if mes2 is None and mes1 is not None:
            mes2 = mes1
        mes1 = mes1 or base.month
        mes2 = mes2 or base.month
        anio_base = anio1 or anio2 or base.year
        inicio = _fecha_valida(anio1 or anio_base, mes1, dia1)
        fin = _fecha_valida(anio2 or anio_base, mes2, dia2)
        if (
            inicio
            and fin
            and inicio > fin
            and mes1 > mes2
            and not (anio1 and anio2)
        ):
            inicio = _fecha_valida(anio_base - 1, mes1, dia1)
        if inicio and fin:
            return _resultado_rango(
                inicio,
                fin,
                _etiqueta_rango(inicio, fin),
                "rango",
                match.group(0),
            )

    if any(
        word_in_text(palabra, normalized)
        for palabra in ("anteayer", "antes de ayer", "antier")
    ):
        dia = base - timedelta(days=2)
        return _resultado_rango(dia, dia, "anteayer", "dia", "anteayer")
    if word_in_text("ayer", normalized):
        dia = base - timedelta(days=1)
        return _resultado_rango(dia, dia, "ayer", "dia", "ayer")
    if word_in_text("hoy", normalized):
        return _resultado_rango(base, base, "hoy", "dia", "hoy")

    if any(
        word_in_text(palabra, normalized)
        for palabra in ("semana pasada", "la semana pasada", "ultima semana")
    ):
        inicio_semana = base - timedelta(days=base.weekday())
        fin = inicio_semana - timedelta(days=1)
        inicio = fin - timedelta(days=6)
        return _resultado_rango(
            inicio, fin, "la semana pasada", "semana", "semana pasada"
        )
    if word_in_text("esta semana", normalized) or word_in_text("semana", normalized):
        inicio = base - timedelta(days=base.weekday())
        return _resultado_rango(
            inicio, base, "esta semana (lunes a hoy)", "semana", "esta semana"
        )

    if any(
        word_in_text(palabra, normalized)
        for palabra in ("mes pasado", "el mes pasado", "ultimo mes")
    ):
        inicio_mes = base.replace(day=1)
        fin = inicio_mes - timedelta(days=1)
        inicio = fin.replace(day=1)
        return _resultado_rango(
            inicio, fin, "el mes pasado", "mes", "mes pasado"
        )
    if word_in_text("este mes", normalized) or word_in_text("mes", normalized):
        inicio = base.replace(day=1)
        return _resultado_rango(inicio, base, "este mes", "mes", "este mes")

    fecha = _fecha_desde_expresion(normalized, base)
    if fecha:
        return _resultado_rango(
            fecha, fecha, _etiqueta_dia(fecha), "dia", normalized
        )

    return _resultado_rango(base, base, "hoy", "dia", "")


INTENCIONES_CONSULTA = {
    "como me fue": "hoy",
    "como va mi dia": "hoy",
    "como voy": "hoy",
    "balance de hoy": "hoy",
    "balance del dia": "hoy",
    "como me fue hoy": "hoy",
    "balance de esta semana": "semana",
    "balance semanal": "semana",
    "esta semana": "semana",
    "balance del mes": "mes",
    "este mes": "mes",
    "cuanto he gastado": "mes",
    "cuanto llevo": "hoy",
}


def detectar_intencion_conversacional(text):
    """Respaldo determinista cuando no hay LLM disponible.

    Devuelve la misma forma que ``ai.interpretar_conversacion``.
    """
    normalized = normalize(text)
    if not normalized:
        return {"intent": "desconocido", "entidades": {}, "confianza": 0.0}

    # Va antes de confirmar/cancelar: «qué me falta por confirmar» es una
    # consulta, no una aceptación.
    if any(
        word_in_text(palabra, normalized)
        for palabra in (
            "pendiente",
            "pendientes",
            "por confirmar",
            "sin confirmar",
            "me falta",
            "que tengo pendiente",
            "que hay pendiente",
            "tengo pendiente",
        )
    ):
        return {"intent": "consultar_pendientes", "entidades": {}, "confianza": 0.85}
    if any(word_in_text(palabra, normalized) for palabra in CONFIRMAR_WORDS):
        if len(normalized.split()) <= 6:
            return {"intent": "confirmar", "entidades": {}, "confianza": 0.9}
    if any(word_in_text(palabra, normalized) for palabra in CANCELAR_WORDS):
        if len(normalized.split()) <= 6:
            return {"intent": "cancelar", "entidades": {}, "confianza": 0.9}
    if any(word_in_text(palabra, normalized) for palabra in CLOSE_WORDS):
        return {"intent": "cerrar_dia", "entidades": {}, "confianza": 0.9}
    if any(word_in_text(palabra, normalized) for palabra in AYUDA_WORDS):
        return {"intent": "ayuda", "entidades": {}, "confianza": 0.9}

    if any(word_in_text(palabra, normalized) for palabra in ("mis metas", "las metas", "metas van", "progreso de")):
        return {"intent": "consultar_metas", "entidades": {}, "confianza": 0.85}
    if any(word_in_text(palabra, normalized) for palabra in ("plan de ahorro", "cuanto debo ahorrar", "plan recomienda", "plan de metas")):
        return {"intent": "consultar_plan", "entidades": {}, "confianza": 0.85}
    if any(word_in_text(palabra, normalized) for palabra in ("mis cuentas", "cuentas tengo", "saldo de mis cuentas")):
        return {"intent": "consultar_cuentas", "entidades": {}, "confianza": 0.85}
    if any(word_in_text(palabra, normalized) for palabra in ("mis categorias", "categorias tengo")):
        return {"intent": "consultar_categorias", "entidades": {}, "confianza": 0.85}

    # Una expresion temporal con verbo o sustantivo de movimiento es una
    # consulta por ese dia/rango, no un registro. Va antes de las frases
    # genericas («mis movimientos») para que «movimientos de ayer» filtre.
    # Un rango («del 3 al 5») nunca se lee como monto.
    rango = resolver_rango(text)
    if rango["expresion"]:
        pide_balance = any(
            word_in_text(palabra, normalized)
            for palabra in ("cuanto", "balance", "resumen", "total")
        )
        menciona_movimiento = any(
            word_in_text(palabra, normalized)
            for palabra in (
                "gaste",
                "gastado",
                "gasto",
                "gastos",
                "ingrese",
                "ingresado",
                "ingreso",
                "ingresos",
                "ahorre",
                "ahorrado",
                "ahorro",
                "movimiento",
                "movimientos",
                "registro",
                "registros",
            )
        )
        consulta_temporal = (pide_balance or menciona_movimiento) and (
            parse_amount(normalized) is None or rango["alcance"] == "rango"
        )
        if consulta_temporal:
            return {
                "intent": (
                    "consultar_balance" if pide_balance else "consultar_movimientos"
                ),
                "entidades": {"fecha_texto": text},
                "confianza": 0.85,
            }

    if any(word_in_text(palabra, normalized) for palabra in ("mis movimientos", "ultimos movimientos", "movimientos de")):
        return {"intent": "consultar_movimientos", "entidades": {}, "confianza": 0.85}
    if any(word_in_text(palabra, normalized) for palabra in ("presupuesto", "cupo")):
        if parse_amount(normalized) is None:
            return {"intent": "consultar_presupuesto", "entidades": {}, "confianza": 0.85}
    if any(word_in_text(palabra, normalized) for palabra in ("mi perfil", "mi ingreso", "mis ingresos")):
        if parse_amount(normalized) is None:
            return {"intent": "consultar_perfil", "entidades": {}, "confianza": 0.8}

    for frase, periodo in INTENCIONES_CONSULTA.items():
        if word_in_text(frase, normalized):
            return {
                "intent": "consultar_balance",
                "entidades": {"periodo": periodo},
                "confianza": 0.85,
            }

    if any(word_in_text(palabra, normalized) for palabra in STATUS_WORDS):
        periodo = "semana" if "semana" in normalized else "mes" if "mes" in normalized else "hoy"
        return {
            "intent": "consultar_balance",
            "entidades": {"periodo": periodo},
            "confianza": 0.8,
        }

    if any(word_in_text(palabra, normalized) for palabra in ("elimina", "borra", "anula", "quita")):
        if any(word_in_text(palabra, normalized) for palabra in ("meta", "objetivo")):
            return {"intent": "eliminar_meta", "entidades": {}, "confianza": 0.85}
        if any(word_in_text(palabra, normalized) for palabra in ("movimiento", "gasto", "ingreso", "registro")):
            return {"intent": "eliminar_movimiento", "entidades": {}, "confianza": 0.85}
    if any(word_in_text(palabra, normalized) for palabra in ("edita", "editar", "cambia", "cambiar", "corrige")):
        if any(word_in_text(palabra, normalized) for palabra in ("movimiento", "gasto", "ingreso", "registro")):
            return {"intent": "editar_movimiento", "entidades": {}, "confianza": 0.8}
    if any(word_in_text(palabra, normalized) for palabra in ("crea", "crear", "nueva", "nuevo", "agrega")):
        if any(word_in_text(palabra, normalized) for palabra in ("cuenta",)):
            return {"intent": "crear_cuenta", "entidades": {}, "confianza": 0.85}
        if any(word_in_text(palabra, normalized) for palabra in ("categoria", "categoría")):
            return {"intent": "crear_categoria", "entidades": {}, "confianza": 0.85}
    if any(word_in_text(palabra, normalized) for palabra in ("presupuesto diario", "presupuesto", "cupo diario")):
        if parse_amount(normalized) is not None:
            return {
                "intent": "actualizar_presupuesto",
                "entidades": {"monto": parse_amount(normalized)},
                "confianza": 0.85,
            }
    if any(word_in_text(palabra, normalized) for palabra in ("mi ingreso", "ingreso mensual", "gano al mes", "sueldo mensual")):
        if parse_amount(normalized) is not None:
            return {
                "intent": "actualizar_perfil",
                "entidades": {"monto": parse_amount(normalized)},
                "confianza": 0.85,
            }

    ahorro_pasado = any(
        word_in_text(palabra, normalized)
        for palabra in ("ahorre", "ahorré", "guarde", "separe")
    )
    creacion = (
        not ahorro_pasado
        and any(
            word_in_text(palabra, normalized)
            for palabra in ("crear", "crea", "plantear", "plantea", "nueva", "quiero", "necesito")
        )
        and any(
            word_in_text(palabra, normalized)
            for palabra in ("meta", "objetivo", "ahorrar para", "comprar", "comprarme")
        )
    )
    if creacion:
        return {
            "intent": "crear_meta",
            "entidades": {
                "nombre": nombre_meta_probable(text),
                "monto": parse_amount(normalized),
            },
            "confianza": 0.75,
        }

    if parse_amount(normalized) is not None:
        entidades = {
            "tipo": detect_type(normalized),
            "monto": parse_amount(normalized),
        }
        # Solo una fecha de dia («ayer», «el 3 de mayo») fecha el movimiento.
        # «este mes» o «esta semana» no convierten un gasto en un dia suelto.
        if rango["expresion"] and rango["alcance"] == "dia":
            entidades["fecha_texto"] = text
        return {
            "intent": "registrar_movimiento",
            "entidades": entidades,
            "confianza": 0.8,
        }

    return {"intent": "desconocido", "entidades": {}, "confianza": 0.3}


def _cuenta_por_defecto(conn, user_id):
    row = conn.execute(
        """
        SELECT id, nombre FROM cuentas
        WHERE usuario_id = ? AND es_por_defecto = 1
        ORDER BY id LIMIT 1
        """,
        (user_id,),
    ).fetchone()
    return dict(row) if row else None


def _categoria_fallback(conn, user_id, tipo):
    """Categoria de ultimo recurso: el esquema exige categoria en todo gasto.

    Prioriza "Otros" y "Otros ingresos" y, si no existen, la primera categoria
    activa del tipo.
    """
    nombre = "Otros ingresos" if tipo == "ingreso" else "Otros"
    row = conn.execute(
        """
        SELECT id, nombre, tipo FROM categorias
        WHERE usuario_id = ? AND tipo = ? AND nombre = ? AND activa = 1
        """,
        (user_id, tipo, nombre),
    ).fetchone()
    if row:
        return dict(row)
    row = conn.execute(
        """
        SELECT id, nombre, tipo FROM categorias
        WHERE usuario_id = ? AND tipo = ? AND activa = 1
        ORDER BY id LIMIT 1
        """,
        (user_id, tipo),
    ).fetchone()
    return dict(row) if row else None


def interpretar_con_ia(conn, user_id, text):
    """Le pide a un LLM que extraiga tipo, monto, categoria y cuenta.

    Devuelve la propuesta validada contra el catalogo del usuario, o None si
    no hay LLM disponible o la respuesta no sirve.
    """
    from . import ai

    categorias = [
        {"id": row["id"], "nombre": row["nombre"], "tipo": row["tipo"]}
        for row in conn.execute(
            "SELECT id, nombre, tipo FROM categorias "
            "WHERE usuario_id = ? AND activa = 1 ORDER BY id",
            (user_id,),
        )
    ]
    cuentas = [
        {"id": row["id"], "nombre": row["nombre"]}
        for row in conn.execute(
            "SELECT id, nombre FROM cuentas WHERE usuario_id = ? ORDER BY id", (user_id,)
        )
    ]
    metas = metas_usuario(conn, user_id)
    if not categorias or not cuentas:
        return None

    try:
        crudo = ai.extraer_estructura(text, categorias, cuentas, metas)
    except ai.ErrorSTT:
        return None
    if not crudo:
        return None

    tipo = str(crudo.get("tipo") or "").strip().lower()
    if tipo not in ("gasto", "ingreso", "ahorro"):
        tipo = None

    monto = crudo.get("monto")
    try:
        monto = int(monto)
    except (TypeError, ValueError):
        monto = None
    if monto is not None and monto <= 0:
        monto = None
    if monto is None:
        monto = parse_amount(normalize(text))

    monto_texto = parse_amount(normalize(text))
    if monto_texto is not None:
        monto = monto_texto

    categoria = coincide_en_catalogo(crudo.get("categoria"), categorias)
    cuenta_cruda = crudo.get("cuenta")
    cuenta = None
    if cuenta_cruda and word_in_text(normalize(cuenta_cruda), normalize(text)):
        cuenta = coincide_en_catalogo(cuenta_cruda, cuentas)
    meta = coincide_en_catalogo(crudo.get("meta"), metas)
    if meta is None and (tipo == "ahorro" or detect_type(normalize(text)) == "ahorro"):
        meta = detect_goal(conn, user_id, text)

    if categoria is not None and tipo in ("gasto", "ingreso"):
        if categoria["tipo"] != tipo:
            categoria = None
    if tipo == "ahorro":
        categoria = None

    tipo_final = tipo or detect_type(normalize(text))
    if tipo_final != "ahorro" and categoria is None:
        # El esquema exige categoria en todo gasto o ingreso.
        categoria = _categoria_fallback(conn, user_id, tipo_final)

    if cuenta is None:
        cuenta = _cuenta_por_defecto(conn, user_id)
    if cuenta is None:
        return None

    concepto = str(crudo.get("concepto") or "").strip()[:255] or text[:255]

    return {
        "intent": "registrar",
        "texto": text,
        "error": None,
        "origen": "ia",
        "proveedor": crudo.get("proveedor"),
        "modelo": crudo.get("modelo"),
        "latencia_ia_ms": crudo.get("latencia_ms"),
        "transacciones": [
            {
                "tipo": tipo_final,
                "monto": monto,
                "categoria_id": categoria["id"] if categoria else None,
                "categoria": categoria["nombre"] if categoria else None,
                "cuenta_id": cuenta["id"],
                "cuenta": cuenta["nombre"],
                "meta_id": meta["id"] if meta else None,
                "meta": meta["nombre"] if meta else None,
                "meta_mencionada": text if menciona_meta(text) else None,
                "concepto": concepto,
                "confianza": 0.85 if (categoria or meta) else 0.7,
            }
        ],
    }


def interpret(conn, user_id, text):
    normalized = normalize(text)
    intent = detect_intent(normalized)
    if intent != "registrar":
        return {"intent": intent, "texto": text, "transacciones": []}

    if (os.environ.get("NLP_USAR_IA") or "auto").strip().lower() != "off":
        propuesta = interpretar_con_ia(conn, user_id, text)
        if propuesta and propuesta.get("transacciones"):
            return propuesta

    transaction_type = detect_type(normalized)
    amount = parse_amount(normalized)
    category = detect_category(conn, user_id, normalized, transaction_type)
    account = detect_account(conn, user_id, normalized)
    if amount is None:
        return {
            "intent": "requiere_aclaracion",
            "texto": text,
            "error": "No se identificó un monto",
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
            "error": "No hay una categoría disponible",
            "transacciones": [],
        }

    goal = detect_goal(conn, user_id, normalized) if transaction_type == "ahorro" else None

    return {
        "intent": "registrar",
        "texto": text,
        "origen": "reglas",
        "transacciones": [
            {
                "tipo": transaction_type,
                "monto": amount,
                "categoria_id": category["id"] if category else None,
                "categoria": category["nombre"] if category else None,
                "cuenta_id": account["id"],
                "cuenta": account["nombre"],
                "meta_id": goal["id"] if goal else None,
                "meta": goal["nombre"] if goal else None,
                "meta_mencionada": text if menciona_meta(text) else None,
                "concepto": text[:255],
                "confianza": 0.9 if (category or goal) else 0.7,
            }
        ],
    }
