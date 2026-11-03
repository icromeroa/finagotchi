"""Genera y valida el manifiesto del dataset de evaluacion de audio.

Uso:
    py -3 tools/generar_dataset.py              # completa el manifiesto a 500 casos
    py -3 tools/generar_dataset.py --total 800  # otra cantidad de casos
    py -3 tools/generar_dataset.py --validar    # solo valida el manifiesto actual

Las filas que ya estan en el manifiesto se conservan: el generador solo agrega
las que faltan y renumera los identificadores. Cada fila candidata se valida
contra ``backend/nlp.py`` antes de escribirse, de modo que el monto esperado y
la intencion siempre correspondan con lo que el motor puede resolver.

Criterios de validacion por fila:
    1. La intencion base de ``nlp.detect_intent`` coincide con la declarada.
    2. Una fila con monto declara exactamente el valor de ``nlp.parse_amount``.
    3. Una fila sin monto no tiene ningun monto parseable.
    4. La categoria pertenece al catalogo del usuario para su tipo.
    5. La cuenta pertenece al catalogo de cuentas.
"""

import argparse
import csv
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend import nlp  # noqa: E402

DATASET = ROOT / "datasets" / "eval_audio"
MANIFEST = DATASET / "manifest.csv"

TOTAL_POR_DEFECTO = 500
SEMILLA = 20261103

CAMPOS = [
    "id",
    "archivo",
    "transcripcion",
    "intent",
    "monto_esperado",
    "categoria_esperada",
    "cuenta_esperada",
    "duracion_s",
    "ruido",
    "notas",
]

CATALOGO_GASTO = (
    "Alimentación",
    "Transporte",
    "Familia y detalles",
    "Ocio y gustos",
    "Vivienda y fijos",
    "Suscripciones",
    "Salud y aseo",
    "Deudas",
    "Finanzas",
    "Préstamos",
    "Ahorro e inversión",
    "Otros",
)
CATALOGO_INGRESO = ("Trabajo", "Apoyo familiar", "Beca", "Otros ingresos")
CUENTAS = ("Efectivo", "Nequi", "Daviplata", "Nu", "Bancolombia")

SUFIJO_CUENTA = {
    "Efectivo": " en efectivo",
    "Nequi": " con nequi",
    "Daviplata": " con daviplata",
    "Nu": " con nu",
    "Bancolombia": " con bancolombia",
}

# Categorias que estaban en el manifiesto pero no existen en el catalogo del
# usuario. Se corrigen al nombre real de la plantilla.
ALIAS_CATEGORIA = {
    "Vivienda": "Vivienda y fijos",
    "Ropa": "Familia y detalles",
}

# Casos puntuales del manifiesto original que estaban incompletos o usaban
# una categoria que el propio catalogo descarta.
CORRECCIONES = {
    # "mesada" es palabra clave de "Apoyo familiar", no de "Trabajo".
    "006": {"categoria_esperada": "Apoyo familiar"},
    # "parqueadero" es palabra clave de "Transporte" y la fila no lo decia.
    "023": {"categoria_esperada": "Transporte"},
}

# Cuantos casos de cada tipo debe tener el manifiesto final.
OBJETIVO_POR_TIPO = {
    "gasto": 260,
    "ingreso": 80,
    "ahorro": 45,
    "consulta": 50,
    "cierre": 30,
    "aclaracion": 35,
}

# Reparto del ruido de fondo entre los clips nuevos.
RUIDO = ("bajo", "bajo", "bajo", "bajo", "bajo", "bajo", "medio", "medio", "medio", "alto")


# ---------------------------------------------------------------------------
# Montos escritos en palabras
# ---------------------------------------------------------------------------

UNIDADES = (
    "",
    "uno",
    "dos",
    "tres",
    "cuatro",
    "cinco",
    "seis",
    "siete",
    "ocho",
    "nueve",
    "diez",
    "once",
    "doce",
    "trece",
    "catorce",
    "quince",
    "dieciséis",
    "diecisiete",
    "dieciocho",
    "diecinueve",
)
DECENAS = {
    10: "diez",
    20: "veinte",
    30: "treinta",
    40: "cuarenta",
    50: "cincuenta",
    60: "sesenta",
    70: "setenta",
    80: "ochenta",
    90: "noventa",
}
CENTENAS = {
    200: "doscientos",
    300: "trescientos",
    400: "cuatrocientos",
    500: "quinientos",
    600: "seiscientos",
    700: "setecientos",
    800: "ochocientos",
    900: "novecientos",
}


def _tres_digitos(numero):
    """Escribe en palabras un numero entre 1 y 999."""
    if numero < 100:
        if numero < 10:
            return UNIDADES[numero]
        decena = (numero // 10) * 10
        resto = numero - decena
        if decena == 20 and resto:
            return "veinti" + UNIDADES[resto]
        if resto:
            return f"{DECENAS[decena]} y {UNIDADES[resto]}"
        return DECENAS[decena]
    centena = (numero // 100) * 100
    resto = numero - centena
    if centena == 100:
        if not resto:
            return "cien"
        return "ciento " + _tres_digitos(resto)
    if not resto:
        return CENTENAS[centena]
    return f"{CENTENAS[centena]} " + _tres_digitos(resto)


def numero_a_palabras(numero):
    """Escribe en palabras un monto entero. Ej: 2500000 -> 'dos millones
    quinientos mil'."""
    if numero < 1000:
        return _tres_digitos(numero)
    if numero < 1000000:
        miles, resto = divmod(numero, 1000)
        texto = "mil" if miles == 1 else f"{_tres_digitos(miles)} mil"
        if resto:
            texto = f"{texto} {_tres_digitos(resto)}"
        return texto
    millones, resto = divmod(numero, 1000000)
    texto = "un millón" if millones == 1 else f"{_tres_digitos(millones)} millones"
    if resto >= 1000:
        miles, unidad = divmod(resto, 1000)
        texto = f"{texto} " + ("mil" if miles == 1 else f"{_tres_digitos(miles)} mil")
        if unidad:
            texto = f"{texto} {_tres_digitos(unidad)}"
    elif resto:
        texto = f"{texto} {_tres_digitos(resto)}"
    return texto


# ---------------------------------------------------------------------------
# Formas de escribir un mismo monto
# ---------------------------------------------------------------------------


def formatos_monto(monto):
    """Formas en que se puede dictar un monto. Devuelve (texto, etiqueta)."""
    formatos = []
    if monto >= 1000:
        formatos.append((f"{monto:,}".replace(",", "."), "monto con puntos de miles"))
        formatos.append((f"{monto:,}", "monto con comas de miles"))
        formatos.append((str(monto), "monto sin separador"))
        if monto % 1000 == 0:
            formatos.append((f"{monto // 1000} mil", "mil abreviado"))
            formatos.append((f"{monto // 1000}k", "k abreviado"))
        formatos.append((numero_a_palabras(monto), "monto en palabras"))
    else:
        formatos.append((str(monto), "monto sin separador"))
    return formatos


def formatos_monto_grande(monto):
    """Formas de dictar un monto grande, con millones."""
    formatos = []
    if monto % 1000000 == 0:
        formatos.append((f"{monto // 1000000} millones", "millones"))
    if monto % 100000 == 0 and monto >= 1000000:
        millones, resto = divmod(monto, 1000000)
        decimal = resto // 100000
        if decimal:
            formatos.append((f"{millones}.{decimal} millones", "millones con decimal"))
    formatos.append((f"{monto:,}".replace(",", "."), "monto con puntos de miles"))
    if monto >= 1000000:
        etiqueta = "millones y miles" if monto % 1000000 else "millones en palabras"
    else:
        etiqueta = "monto en palabras"
    formatos.append((numero_a_palabras(monto), etiqueta))
    formatos.append((str(monto), "monto sin separador"))
    return formatos


# ---------------------------------------------------------------------------
# Escenarios
#
# Cada escenario tiene tipo, categoria y grupos. Un grupo es una lista de
# montos plausibles con las frases que los usan, para que un cafe no termine
# costando lo mismo que un arriendo.
# ---------------------------------------------------------------------------

ESCENARIOS = (
    # --- gastos -----------------------------------------------------------
    {
        "tipo": "gasto",
        "categoria": "Alimentación",
        "grupos": (
            ((2000, 2500, 3000, 3500, 4000), ("gasté {m} en una empanada",)),
            ((3000, 4000, 4500, 5000, 6500), ("compré café por {m}",)),
            (
                (9000, 12000, 14000, 15000, 18000, 22000),
                (
                    "gasté {m} en el almuerzo",
                    "pagué {m} del desayuno",
                    "me gasté {m} en la cena",
                    "pagué {m} en una comida",
                    "compré un corrientazo de {m}",
                    "desayuné en un restaurante por {m}",
                ),
            ),
            (
                (35000, 45000, 60000, 80000, 120000),
                ("gasté {m} en el mercado", "la comida del mes costó {m}"),
            ),
        ),
    },
    {
        "tipo": "gasto",
        "categoria": "Transporte",
        "grupos": (
            ((2000, 2500, 3000, 3500, 4000), ("pagué {m} de pasaje", "gasté {m} en bus")),
            (
                (5000, 6000, 8000),
                ("pagué {m} en transmilenio",),
            ),
            (
                (9000, 12000, 15000, 20000, 25000),
                ("tomé un uber por {m}", "tomé un taxi por {m}"),
            ),
            (
                (40000, 55000, 70000, 90000),
                ("pagué {m} de gasolina",),
            ),
            ((3000, 4000, 5000, 6000), ("dejé {m} de parqueadero",)),
            (
                (120000, 180000, 250000),
                ("gasté {m} en transporte", "el viaje me costó {m}"),
            ),
        ),
    },
    {
        "tipo": "gasto",
        "categoria": "Familia y detalles",
        "grupos": (
            (
                (25000, 35000, 50000, 70000, 90000),
                (
                    "compré un regalo para mi mamá por {m}",
                    "gasté {m} en un regalo de cumpleaños",
                    "pagué {m} por el regalo de mi hijo",
                    "gasté {m} en un detalle para mi papá",
                ),
            ),
        ),
    },
    {
        "tipo": "gasto",
        "categoria": "Ocio y gustos",
        "grupos": (
            ((3000, 4000, 5000, 6000), ("me pedí un helado por {m}",)),
            (
                (6000, 8000, 10000, 12000),
                ("compré cerveza por {m}", "tomé una cerveza en un bar por {m}"),
            ),
            ((8000, 12000, 15000, 20000), ("gasté {m} en un juego",)),
            (
                (18000, 25000, 30000, 35000),
                ("fui al cine y pagué {m}",),
            ),
            (
                (25000, 35000, 45000, 60000),
                ("la salida con amigos me costó {m}",),
            ),
            ((40000, 60000, 80000), ("fui a una fiesta y gasté {m}",)),
            ((90000, 120000, 150000), ("gasté {m} en un concierto",)),
        ),
    },
    {
        "tipo": "gasto",
        "categoria": "Vivienda y fijos",
        "grupos": (
            (
                (120000, 150000, 180000, 200000, 250000, 300000),
                ("pagué {m} de arriendo", "pagué {m} de alquiler"),
            ),
            ((35000, 45000, 60000, 80000), ("came la factura de luz por {m}",)),
            ((45000, 60000, 70000, 90000), ("gasté {m} en internet",)),
            ((25000, 35000, 45000), ("pagué {m} del agua",)),
            ((30000, 45000, 60000), ("pagué {m} del gas",)),
            ((70000, 90000, 110000, 130000), ("pagué {m} de los servicios",)),
        ),
    },
    {
        "tipo": "gasto",
        "categoria": "Suscripciones",
        "grupos": (
            ((25000, 30000, 35000, 45000), ("pagué {m} de netflix",)),
            (
                (15000, 18000, 20000, 25000),
                ("renové spotify por {m}", "pagué {m} de la suscripción de spotify"),
            ),
        ),
    },
    {
        "tipo": "gasto",
        "categoria": "Salud y aseo",
        "grupos": (
            ((15000, 25000, 35000, 50000), ("gasté {m} en la farmacia",)),
            ((8000, 12000, 18000, 25000), ("pagué {m} en la droguería",)),
            ((20000, 30000, 45000), ("compré medicina por {m}",)),
            ((35000, 45000, 60000), ("pagué {m} del gimnasio",)),
            (
                (80000, 120000, 150000),
                ("gasté {m} en la consulta con el médico",),
            ),
            ((20000, 35000, 50000), ("pagué {m} por la salud",)),
        ),
    },
    {
        "tipo": "gasto",
        "categoria": "Deudas",
        "grupos": (
            (
                (60000, 90000, 120000, 150000, 200000, 250000),
                (
                    "pagué {m} de la tarjeta de crédito",
                    "abonné {m} a la deuda del banco",
                    "pagué {m} de la cuota de la tarjeta",
                    "cancelé {m} de una deuda pendiente",
                ),
            ),
        ),
    },
    {
        "tipo": "gasto",
        "categoria": "Finanzas",
        "grupos": (
            ((8000, 12000, 25000, 40000), ("pagué {m} de comisión de la cuenta",)),
            ((30000, 45000, 70000), ("gasté {m} en el impuesto",)),
        ),
    },
    {
        "tipo": "gasto",
        "categoria": "Préstamos",
        "grupos": (
            (
                (80000, 120000, 200000, 300000),
                ("pagué {m} de la cuota del préstamo", "gasté {m} en el préstamo"),
            ),
        ),
    },
    {
        "tipo": "gasto",
        "categoria": "Ahorro e inversión",
        "grupos": (
            ((200000, 350000, 500000, 800000), ("gasté {m} en un CDT",)),
            ((150000, 250000, 400000), ("pagué {m} de una acción",)),
        ),
    },
    {
        "tipo": "gasto",
        "categoria": "Otros",
        "grupos": (
            (
                (4000, 9000, 17000, 22000, 55000),
                (
                    "gasté {m} en unas cosas",
                    "pagué {m} por un tema que no recuerdo",
                    "gasté {m} en varios gastos",
                    "compré {m} en una tienda",
                ),
            ),
        ),
    },
    # --- ingresos ---------------------------------------------------------
    {
        "tipo": "ingreso",
        "categoria": "Trabajo",
        "grande": True,
        "grupos": (
            (
                (800000, 1200000, 1500000, 2000000, 2500000),
                (
                    "me pagaron {m} por un trabajo",
                    "recibí el sueldo de {m}",
                    "cobré {m} de honorarios",
                    "me llegó la quincena de {m}",
                    "recibí mi salario de {m}",
                    "me pagaron {m} del trabajo",
                    "gané {m} por un proyecto de trabajo",
                ),
            ),
        ),
    },
    {
        "tipo": "ingreso",
        "categoria": "Apoyo familiar",
        "grupos": (
            (
                (250000, 300000, 450000, 600000),
                (
                    "recibí la mesada de {m}",
                    "recibí el apoyo económico de {m}",
                    "recibí la mesada que me mandaron de {m}",
                ),
            ),
        ),
    },
    {
        "tipo": "ingreso",
        "categoria": "Beca",
        "grande": True,
        "grupos": (
            (
                (800000, 1200000, 1500000),
                ("recibí la beca de {m}", "recibí el pago de la beca de {m}"),
            ),
        ),
    },
    {
        "tipo": "ingreso",
        "categoria": "Otros ingresos",
        "grupos": (
            (
                (30000, 60000, 90000, 150000),
                (
                    "recibí {m} por la venta de una consola",
                    "recibí {m} por la venta de un mueble",
                    "recibí {m} por una regalía",
                ),
            ),
        ),
    },
    # --- ahorro -----------------------------------------------------------
    {
        "tipo": "ahorro",
        "categoria": "",
        "grupos": (
            (
                (20000, 50000, 80000, 150000, 300000, 500000),
                (
                    "ahorré {m} para el portátil",
                    "guardé {m} para el viaje",
                    "separé {m} para la meta",
                    "puse {m} en ahorro",
                    "aparté {m} para la meta del portátil",
                ),
            ),
        ),
    },
    # --- consultas --------------------------------------------------------
    {
        "tipo": "consulta",
        "categoria": "",
        "frases": (
            "¿cómo voy hoy?",
            "¿cómo voy?",
            "cómo voy hoy",
            "dame mi balance",
            "muéstrame el balance",
            "revises el balance",
            "dame el balance de hoy",
            "dame el balance de la semana",
            "quiero ver el balance del mes",
            "necesito el balance",
            "hazme un resumen",
            "hazme un resumen del mes",
            "hazme un resumen de la semana",
            "hazme un resumen de mis gastos",
            "muéstrame el resumen del mes",
            "necesito un resumen",
            "dame el estado de hoy",
            "dame el estado de la semana",
            "dame el estado de mis finanzas",
            "muéstrame mi estado",
            "necesito el estado de mis cuentas",
            "¿cómo va mi mes?",
            "cómo va mi semana",
            "cómo va el mes",
            "¿cómo me fue esta semana?",
            "cómo me fue hoy",
            "cuánto llevo gastado",
            "cuánto llevo gastado hoy",
            "cuánto llevo en gastos",
            "cuánto llevo ahorrado",
            "cuánto llevo de ahorro",
            "cuánto llevo en total",
            "quiero saber cómo voy",
            "necesito saber cómo voy",
            "revisemos cómo voy",
            "por favor dame mi balance",
            "por favor hazme un resumen",
            "por favor dime cómo voy",
            "dime cómo voy hoy",
            "dime el estado de mis finanzas",
            "muéstrame cómo va el mes",
            "quiero ver el resumen del mes",
            "cómo va mi presupuesto",
            "cómo va mi ahorro",
            "cómo va mi mes hasta ahora",
            "cuánto llevo del mes",
            "quiero un balance de hoy",
            "muéstrame el estado de hoy",
            "cómo voy financieramente",
            "necesito saber el balance",
        ),
    },
    # --- cierre del día ---------------------------------------------------
    {
        "tipo": "cierre",
        "categoria": "",
        "frases": (
            "cierra el día",
            "cierra el día por favor",
            "cerrar el día",
            "cerrar el día por favor",
            "termina el día",
            "termina el día por favor",
            "finaliza el día",
            "finaliza el día ya",
            "cierre del día",
            "por favor termina el día",
            "por favor cierra el día",
            "quiero cerrar el día",
            "por favor cerrar el día",
            "ya cerra el día",
            "listo cierra el día",
            "bueno termina el día",
            "cerrá el día",
            "podés cerrar el día",
            "hora de cerrar el día",
            "vamos a cerrar el día",
            "termina el día de una vez",
            "por favor finaliza el día",
            "haz el cierre del día",
            "ya es hora de cerrar el día",
            "cierra el día de una vez",
            "por favor cerra el día",
            "necesito cerrar el día",
            "es hora de cerrar el día",
            "cerrar el día porfa",
            "termina el día porfa",
        ),
    },
    # --- frases sin monto -------------------------------------------------
    {
        "tipo": "aclaracion",
        "categoria": "",
        "frases": (
            "gasté en el mercado pero no sé cuánto",
            "la verdad no me acuerdo de cuánto gasté",
            "me salió un gasto raro",
            "pagué la cuota de la biking",
            "compré gasolina pero no me acuerdo del valor",
            "no tengo idea de cuánto gasté hoy",
            "se me olvidó la cantidad del gasto",
            "hice una compra pero no sé el monto",
            "no me acuerdo del valor de lo que compré",
            "pagué por el parqueadero pero se me olvidó el monto",
            "gasté en una empanada pero no recuerdo la cantidad",
            "compré algo en la tienda y no sé cuánto fue",
            "me gasté una platita pero no sé cuánto",
            "no sé cuánto pagué en el almuerzo",
            "no sé cuánto gasté en el bus",
            "pagué el arriendo pero se me olvidó el valor",
            "no sé cuánto costó la cena",
            "no recuerdo cuánto gasté en el mercado",
            "perdí la cuenta de lo que gasté",
            "no sé el valor de la compra",
            "compré gasolina y no me acuerdo del monto",
            "gasté en un regalo pero no sé el valor",
            "no tengo el dato de cuánto gasté",
            "se me fue la cifra de lo que gasté",
            "no sé cuánto pagué por el desayuno",
            "quedó sin saber el monto de la compra",
            "no sé cuánto fue la factura",
            "no me acuerdo cuánto pagué en la cena",
            "hice un gasto pero no sé la cantidad",
            "se me olvidó cuánto pagué",
            "no sé el precio de lo que compré",
            "pagué por el servicio pero no sé el monto",
            "gasté en el cine pero no me acuerdo cuánto",
            "no me acuerdo de cuánto pagué en la farmacia",
            "invertí una cantidad pero no sé cuál",
        ),
    },
)

# Casos con dos transacciones en la misma frase: el motor toma el primer monto.
ESCENARIOS_DOBLES = (
    {
        "tipo": "gasto",
        "categoria": "Alimentación",
        "montos": ((12000, 3000), (15000, 4500), (20000, 6000), (8000, 2500)),
        "frases": (
            "gasté {m} en almuerzo y {m2} en bus",
            "gasté {m} en el mercado y {m2} en pasaje",
        ),
    },
)


# ---------------------------------------------------------------------------
# Validacion
# ---------------------------------------------------------------------------


def tipo_de_fila(fila):
    """Clasifica una fila por su tipo de contenido."""
    intent = fila["intent"]
    if intent == "consulta_estado":
        return "consulta"
    if intent == "cerrar_dia":
        return "cierre"
    if intent == "requiere_aclaracion":
        return "aclaracion"
    if fila["categoria_esperada"] in CATALOGO_INGRESO:
        return "ingreso"
    if fila["categoria_esperada"]:
        return "gasto"
    # Sin categoria puede ser ahorro o un gasto sin categoria (un retiro, por
    # ejemplo): el texto es el que decide.
    tipo = nlp.detect_type(nlp.normalize(fila["transcripcion"]))
    return "ahorro" if tipo == "ahorro" else "gasto"


def validar_fila(fila):
    """Devuelve la lista de problemas de una fila del manifiesto."""
    problemas = []
    texto = fila["transcripcion"]
    normalizado = nlp.normalize(texto)
    intent = fila["intent"]
    monto_esperado = (fila["monto_esperado"] or "").strip()
    monto_obtenido = nlp.parse_amount(normalizado)
    intent_base = nlp.detect_intent(normalizado)

    if intent in ("consulta_estado", "cerrar_dia", "registrar"):
        if intent_base != intent:
            problemas.append(f"detect_intent devolvio {intent_base}")
    elif intent == "requiere_aclaracion":
        if intent_base != "registrar":
            problemas.append(f"la frase no es un registro, detect_intent dio {intent_base}")
        if monto_obtenido is not None:
            problemas.append(f"la frase si tiene monto ({monto_obtenido})")
    else:
        problemas.append(f"intent desconocido: {intent}")

    if monto_esperado:
        if monto_obtenido is None:
            problemas.append("no se pudo parsear el monto")
        elif str(monto_obtenido) != str(monto_esperado):
            problemas.append(f"monto parseado {monto_obtenido} != {monto_esperado}")
    elif monto_obtenido is not None:
        problemas.append(f"la fila no declara monto pero se parsea {monto_obtenido}")

    categoria = (fila["categoria_esperada"] or "").strip()
    if categoria:
        if categoria not in CATALOGO_GASTO and categoria not in CATALOGO_INGRESO:
            problemas.append(f"categoria fuera del catalogo: {categoria}")
        elif tipo_de_fila(fila) == "ingreso" and categoria not in CATALOGO_INGRESO:
            problemas.append(f"categoria de gasto en un ingreso: {categoria}")
        elif tipo_de_fila(fila) == "gasto" and categoria not in CATALOGO_GASTO:
            problemas.append(f"categoria de ingreso en un gasto: {categoria}")

    cuenta = (fila["cuenta_esperada"] or "").strip()
    if cuenta and cuenta not in CUENTAS:
        problemas.append(f"cuenta fuera del catalogo: {cuenta}")

    return problemas


# ---------------------------------------------------------------------------
# Construccion de las filas nuevas
# ---------------------------------------------------------------------------


def _candidato(texto, intent, monto, categoria, cuenta, ruido, notas):
    return {
        "transcripcion": texto,
        "intent": intent,
        "monto_esperado": "" if monto is None else str(monto),
        "categoria_esperada": categoria,
        "cuenta_esperada": cuenta,
        "duracion_s": "",
        "ruido": ruido,
        "notas": "; ".join(notas),
    }


def _generar_candidatos():
    """Arma la lista de filas candidatas, ya validadas."""
    candidatos = []
    rotacion_ruido = 0
    rotacion_cuenta = 0

    def tomar_ruido():
        nonlocal rotacion_ruido
        ruido = RUIDO[rotacion_ruido % len(RUIDO)]
        rotacion_ruido += 1
        return ruido

    def tomar_cuenta():
        nonlocal rotacion_cuenta
        cuenta = CUENTAS[rotacion_cuenta % len(CUENTAS)]
        rotacion_cuenta += 1
        return cuenta

    for escenario in ESCENARIOS:
        tipo = escenario["tipo"]
        categoria = escenario.get("categoria", "")

        if tipo in ("consulta", "cierre", "aclaracion"):
            intent = {
                "consulta": "consulta_estado",
                "cierre": "cerrar_dia",
                "aclaracion": "requiere_aclaracion",
            }[tipo]
            # Una consulta, un cierre o una frase sin monto no mueven dinero:
            # no llevan cuenta, igual que las filas que ya traia el manifiesto.
            for frase in escenario["frases"]:
                fila = _candidato(
                    frase,
                    intent,
                    None,
                    "",
                    "",
                    tomar_ruido(),
                    [
                        {
                            "consulta": "consulta",
                            "cierre": "cierre",
                            "aclaracion": "sin monto",
                        }[tipo]
                    ],
                )
                if not validar_fila(fila):
                    candidatos.append(fila)
            continue

        for montos, frases in escenario["grupos"]:
            for monto in montos:
                formatos = (
                    formatos_monto_grande(monto)
                    if escenario.get("grande")
                    else formatos_monto(monto)
                )
                for texto_monto, etiqueta in formatos:
                    for frase in frases:
                        cuenta = tomar_cuenta()
                        texto = frase.format(m=texto_monto) + SUFIJO_CUENTA[cuenta]
                        notas = [etiqueta]
                        if tipo == "ingreso":
                            notas.append("ingreso")
                        elif tipo == "ahorro":
                            notas.append("ahorro")
                        if cuenta != "Efectivo":
                            notas.append("cuenta digital")
                        fila = _candidato(
                            texto,
                            "registrar",
                            monto,
                            categoria,
                            cuenta,
                            tomar_ruido(),
                            notas,
                        )
                        if not validar_fila(fila):
                            candidatos.append(fila)

    for escenario in ESCENARIOS_DOBLES:
        for primero, segundo in escenario["montos"]:
            texto_primero = f"{primero:,}".replace(",", ".")
            texto_segundo = f"{segundo:,}".replace(",", ".")
            for frase in escenario["frases"]:
                cuenta = tomar_cuenta()
                texto = frase.format(m=texto_primero, m2=texto_segundo)
                texto = f"{texto}{SUFIJO_CUENTA[cuenta]}"
                fila = _candidato(
                    texto,
                    "registrar",
                    primero,
                    escenario["categoria"],
                    cuenta,
                    tomar_ruido(),
                    ["dos transacciones", "monto con puntos de miles"],
                )
                if not validar_fila(fila):
                    candidatos.append(fila)

    return candidatos


def _repartir(candidatos, cuantos, semilla):
    """Toma `cuantos` candidatos repartiendolos entre las formas de dictar
    el monto, para que el conjunto tenga de todo y no solo de un formato.

    No se repite ninguna frase: si dos candidatos dicen lo mismo, se queda
    solo el primero."""
    por_forma = {}
    vistas = set()
    for fila in candidatos:
        texto = fila["transcripcion"]
        if texto in vistas:
            continue
        vistas.add(texto)
        etiqueta = fila["notas"].split(";")[0].strip()
        por_forma.setdefault(etiqueta, []).append(fila)

    generador = random.Random(semilla)
    for filas in por_forma.values():
        generador.shuffle(filas)

    orden = sorted(por_forma)
    elegidas = []
    posicion = 0
    while len(elegidas) < cuantos and any(por_forma[clave] for clave in orden):
        clave = orden[posicion % len(orden)]
        if por_forma[clave]:
            elegidas.append(por_forma[clave].pop())
        posicion += 1
    return elegidas


# ---------------------------------------------------------------------------
# Manifiesto
# ---------------------------------------------------------------------------


def normalizar_fila(fila):
    """Deja la fila con la misma forma que el resto del manifiesto.

    - Corrige las categorias que no existen en el catalogo del usuario.
    - Una frase de registro sin monto recuperable no puede crear una
      transaccion: queda pendiente de aclaracion, sin categoria ni cuenta.
    """
    categoria = (fila.get("categoria_esperada") or "").strip()
    if categoria in ALIAS_CATEGORIA:
        fila["categoria_esperada"] = ALIAS_CATEGORIA[categoria]
    fila.update(CORRECCIONES.get(fila.get("id"), {}))

    sin_monto = not (fila.get("monto_esperado") or "").strip()
    if fila.get("intent") == "registrar" and sin_monto:
        fila["intent"] = "requiere_aclaracion"
        fila["categoria_esperada"] = ""
        fila["cuenta_esperada"] = ""
    return fila


def leer_manifesto():
    if not MANIFEST.exists():
        return []
    with MANIFEST.open(encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.DictReader(archivo))
    return [normalizar_fila(fila) for fila in filas]


def escribir_manifesto(filas):
    with MANIFEST.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=CAMPOS, lineterminator="\n")
        escritor.writeheader()
        for indice, fila in enumerate(filas, start=1):
            fila = dict(fila)
            fila["id"] = f"{indice:03d}"
            fila["archivo"] = f"audio/{indice:04d}.wav"
            fila.setdefault("duracion_s", "")
            escritor.writerow({campo: fila.get(campo, "") for campo in CAMPOS})


def construir(total):
    existentes = leer_manifesto()
    if len(existentes) >= total:
        return existentes[:total], 0

    por_tipo = {}
    for fila in existentes:
        por_tipo.setdefault(tipo_de_fila(fila), []).append(fila)

    candidatos = _generar_candidatos()
    ya_dichas = {fila["transcripcion"] for fila in existentes}
    candidatos = [c for c in candidatos if c["transcripcion"] not in ya_dichas]

    faltantes = []
    for tipo, objetivo in OBJETIVO_POR_TIPO.items():
        ya_hay = len(por_tipo.get(tipo, []))
        faltan = max(0, objetivo - ya_hay)
        if faltan:
            disponibles = [c for c in candidatos if tipo_de_fila(c) == tipo]
            elegidas = _repartir(disponibles, faltan, SEMILLA + len(tipo))
            if len(elegidas) < faltan:
                print(
                    f"AVISO: solo hay {len(elegidas)} candidatos validos de tipo "
                    f"'{tipo}' y se necesitan {faltan}"
                )
            faltantes.extend(elegidas)

    # Orden estable: primero por tipo y categoria, dentro de cada grupo se
    # conserva el orden mixto que salio del reparto.
    orden_tipos = list(OBJETIVO_POR_TIPO)
    faltantes.sort(
        key=lambda f: (orden_tipos.index(tipo_de_fila(f)), f["categoria_esperada"])
    )

    return existentes + faltantes, len(faltantes)


def main():
    parser = argparse.ArgumentParser(description="Generar el dataset de evaluacion de audio")
    parser.add_argument("--total", type=int, default=TOTAL_POR_DEFECTO)
    parser.add_argument("--validar", action="store_true", help="Solo valida el manifiesto")
    args = parser.parse_args()

    if args.validar:
        filas = leer_manifesto()
        problemas = 0
        for fila in filas:
            fallos = validar_fila(fila)
            if fallos:
                problemas += 1
                print(f"!! [{fila['id']}] {fila['transcripcion']}")
                for fallo in fallos:
                    print(f"     - {fallo}")
        print(f"\n{len(filas)} filas, {problemas} con problemas")
        return 1 if problemas else 0

    filas, agregadas = construir(args.total)
    escribir_manifesto(filas)

    problemas = 0
    for fila in filas:
        fallos = validar_fila(fila)
        if fallos:
            problemas += 1
            print(f"!! [{fila['id']}] {fila['transcripcion']}")
            for fallo in fallos:
                print(f"     - {fallo}")

    conteo = {}
    for fila in filas:
        clave = tipo_de_fila(fila)
        conteo[clave] = conteo.get(clave, 0) + 1

    print(f"Manifiesto escrito: {MANIFEST}")
    print(f"Filas: {len(filas)} (agregadas {agregadas}, objetivo {args.total})")
    for clave in ("gasto", "ingreso", "ahorro", "consulta", "cierre", "aclaracion"):
        print(f"  {clave:12} {conteo.get(clave, 0)}")
    print(f"Filas con problemas: {problemas}")
    return 1 if problemas else 0


if __name__ == "__main__":
    raise SystemExit(main())
