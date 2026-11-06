"""Pantallas del dispositivo simulado.

Cada funcion dibuja una pantalla de 240x320 como un recuadro de texto. Los
titulos, contenidos y botones siguen lo definido en docs/DISPOSITIVO.md
(seccion 7, pantallas D01 a D13).
"""

ANCHO = 38
LINEA = "-" * ANCHO

TONO_FELIZ = [
    "Vas muy bien hoy.",
    "Buen trabajo, sigue asi.",
    "Me encanta how te va.",
    "Hoy vas con todo.",
]
TONO_PREOCUPADO = [
    "Ojo, se te va el cupo.",
    "Casi no te queda nada.",
    "Un poquito de calma, porfa.",
]
TONO_TRISTE = [
    "Hoy fue un dia dificil.",
    "Mañana se arma mejor.",
    "No te preocupes, aqui estoy.",
]
TONO_CRITICO = [
    "Vamos a cuidar el gasto.",
    "Mejor pausemos un poquito.",
]


def _fila(texto="", ancho=ANCHO):
    if len(texto) > ancho:
        texto = texto[: ancho - 1] + "..."
    return f"| {texto.ljust(ancho - 2)} |"


def _caja(lineas):
    partes = [f"+{LINEA}+"]
    for linea in lineas:
        partes.append(_fila(linea))
    partes.append(f"+{LINEA}+")
    return "\n".join(partes)


def _barra(valor, total=100, largo=12):
    valor = max(0, min(100, valor))
    lleno = int(largo * valor / total)
    return "#" * lleno + "." * (largo - lleno)


def _dinero(valor):
    valor = int(valor or 0)
    signo = "-" if valor < 0 else ""
    return f"{signo}${abs(valor):,}".replace(",", ".")


def _animo_normalizado(animo):
    return str(animo or "FELIZ").upper()


def _tono(animo):
    animo = _animo_normalizado(animo)
    if animo == "FELIZ":
        return TONO_FELIZ
    if animo == "PREOCUPADO":
        return TONO_PREOCUPADO
    if animo == "TRISTE":
        return TONO_TRISTE
    return TONO_CRITICO


def d01_arranque():
    return _caja(
        [
            "",
            "        FinaGotchi",
            "",
            "      NANCY esta lista",
            "        para ayudarte",
            "",
            "   [OK] Continuar",
            "",
        ]
    )


def d02_sin_vincular():
    return _caja(
        [
            "",
            "   Dispositivo sin vincular",
            "",
            "   Abre la app y vincula",
            "   este dispositivo para",
            "   empezar a guardar.",
            "",
            "   Codigo: 482913",
            "",
        ]
    )


def d03_reposo(home, conectado=True, bateria=87, pendientes=0):
    hoy = home.get("hoy", {})
    mascota = home.get("mascota", {})
    animo = _animo_normalizado(mascota.get("animo"))
    salud = mascota.get("salud", 100)
    cupo = hoy.get("cupo_restante", 0)
    presupuesto = hoy.get("presupuesto_diario", 0)
    estado_red = "WiFi" if conectado else "Sin senal"
    lineas = [
        "",
        f"  NANCY · {animo}",
        f"  Salud {_barra(salud)} {salud}%",
        "",
        f"  Te quedan {_dinero(cupo)} de {_dinero(presupuesto)}",
        f"  Gastos {_dinero(hoy.get('gastos', 0))} · Ingresos {_dinero(hoy.get('ingresos', 0))}",
        "",
        f"  Puntos {home.get('puntos', 0)}   {estado_red}   Batt {bateria}%",
    ]
    if pendientes:
        lineas.append(f"  {pendientes} mensaje(s) pendiente(s)")
    lineas += ["", "        Mantén para hablar", ""]
    return _caja(lineas)


def d04_grabando(segundos=0):
    minutos, resto = divmod(int(segundos), 60)
    reloj = f"{minutos:02d}:{resto:02d}"
    barras = ".-/-.-/-.-/-.-"
    return _caja(
        [
            "",
            "      Te escucho",
            "",
            f"      {barras}",
            f"        {reloj}",
            "",
            "   Suelta para enviar",
            "   Atrás para cancelar",
            "",
        ]
    )


def d05_procesando():
    return _caja(
        [
            "",
            "     Nancy está pensando",
            "",
            "      . . .",
            "",
            "  Entendiendo tu mensaje",
            "",
            "",
        ]
    )


def d06_confirmar(transacciones, texto=""):
    lineas = [
        "",
        "   ¿Registro esto?",
        f"   1 de {len(transacciones)}",
        "",
    ]
    for transaccion in transacciones[:3]:
        tipo = str(transaccion.get("tipo", "gasto")).upper()
        lineas.append(f"   {tipo}   {_dinero(transaccion.get('monto', 0))}")
        detalles = " · ".join(
            parte
            for parte in [
                transaccion.get("categoria") or "",
                transaccion.get("cuenta") or "",
            ]
            if parte
        )
        if detalles:
            lineas.append(f"          {detalles}")
    if texto:
        lineas += ["", f'   "{texto[:30]}"']
    lineas += ["", "   Di: sí, está bien u ok", ""]
    return _caja(lineas)


def d07_resultado(puntos, home, racha=None):
    hoy = home.get("hoy", {})
    lineas = [
        "",
        "         Listo",
        "",
        f"   +{puntos} punto(s)",
        f"   Te quedan {_dinero(hoy.get('cupo_restante', 0))} de {_dinero(hoy.get('presupuesto_diario', 0))}",
    ]
    if racha:
        lineas.append(f"   Racha: {racha}")
    lineas += ["", "   OK para volver", ""]
    return _caja(lineas)


def d08_consulta(home):
    hoy = home.get("hoy", {})
    mascota = home.get("mascota", {})
    animo = _animo_normalizado(mascota.get("animo"))
    salud = mascota.get("salud", 100)
    balance = hoy.get("balance_neto", 0)
    lineas = [
        "",
        "     Así vas hoy",
        "",
        f"   Ingresos      {_dinero(hoy.get('ingresos', 0)):>12}",
        f"   Gastos        {_dinero(hoy.get('gastos', 0)):>12}",
        f"   Ahorro        {_dinero(hoy.get('ahorro', 0)):>12}",
        "   " + "-" * 20,
        f"   Balance       {_dinero(balance):>12}",
        "",
        f"   Te quedan     {_dinero(hoy.get('cupo_restante', 0)):>12}",
        f"   de un total de {_dinero(hoy.get('presupuesto_diario', 0)):>9}",
        "",
        f"   Cupo {'agotado' if (hoy.get('cupo_restante', 0) or 0) < 0 else 'disponible'}",
        "",
        f"   Nancy: {animo} · salud {salud}%",
        f"   {_tono(animo)[0]}",
        "",
    ]
    return _caja(lineas)


def d09_cierre(cierre):
    if not cierre:
        return d03_reposo({})
    salud = cierre.get("salud_fin", cierre.get("salud", 100))
    animo = _animo_normalizado(cierre.get("animo"))
    lineas = [
        "",
        "     Cierre del día",
        "",
        f"   Ingresos  {_dinero(cierre.get('total_ingresos', 0)):>12}",
        f"   Gastos    {_dinero(cierre.get('total_gastos', 0)):>12}",
        f"   Ahorro    {_dinero(cierre.get('total_ahorrado', 0)):>12}",
        "   " + "-" * 20,
        f"   Balance   {_dinero(cierre.get('balance_neto', 0)):>12}",
        "",
        f"   Salud {salud}% · Animo {animo}",
        "",
    ]
    return _caja(lineas)


def d10_sin_conexion():
    return _caja(
        [
            "",
            "     Sin conexión",
            "",
            "   No pude enviar tu",
            "   mensaje.",
            "",
            "   Voy a intentarlo otra vez",
            "",
            "   [OK] Reintentar",
            "",
        ]
    )


def d11_no_entendio():
    return _caja(
        [
            "",
            "     No entendió",
            "",
            "   Intenta decir el monto",
            "   y el tipo de movimiento.",
            "",
            '   "Gasté 10.000 en almuerzo"',
            "",
            "   [OK] Intentar de nuevo",
            "",
        ]
    )


def d12_bloqueado():
    return _caja(
        [
            "",
            "      Dispositivo",
            "      desvinculado",
            "",
            "   Abre la app y vuelve",
            "   a vincular este",
            "   dispositivo.",
            "",
            "   [OK] Entendido",
            "",
        ]
    )


def d13_aviso(titulo, mensaje):
    return _caja(
        [
            "",
            f"   {titulo}",
            "",
            f"   {mensaje}",
            "",
            "   [OK] Entendido",
            "",
        ]
    )


def d14_plan_ahorro(plan):
    """Resumen del plan de metas calculado con programacion lineal."""
    if not plan:
        return d13_aviso("Sin plan", "No se pudo calcular el plan de ahorro.")
    resumen = plan.get("resumen", {})
    diagnostico = plan.get("diagnostico", {})
    lineas = [
        "",
        "    Plan de ahorro",
        "",
        f"   Capacidad mes 1  {_dinero(plan.get('capacidad_mes_actual', 0)):>11}",
        f"   Metas            {resumen.get('metas_totales', 0):>11}",
        f"   Cumplimiento     {int(round(resumen.get('cumplimiento_ponderado', 0) * 100)):>10}%",
        "",
    ]
    for meta in (plan.get("metas") or [])[:4]:
        nombre = str(meta.get("nombre") or "Meta")[:16]
        porcentaje = int(round((meta.get("cumplimiento") or 0) * 100))
        lineas.append(f"   {nombre:<16} {porcentaje:>3}%")
        lineas.append(
            f"   -> {_dinero(meta.get('asignacion_mes_actual', 0))}/mes"
        )
    if not plan.get("metas"):
        lineas.append("   Aun no tienes metas.")
    lineas += [
        "",
        "   Nancy: " + str(diagnostico.get("mensaje") or "")[:26],
        "",
    ]
    return _caja(lineas)


def _envolver(texto, ancho=ANCHO - 4):
    palabras = str(texto or "").split()
    lineas = []
    actual = ""
    for palabra in palabras:
        if len(actual) + len(palabra) + 1 > ancho:
            if actual:
                lineas.append(actual)
            actual = palabra
        else:
            actual = f"{actual} {palabra}".strip()
    if actual:
        lineas.append(actual)
    return lineas or [""]


def d15_conversacion(respuesta):
    """Respuesta conversacional de Nancy, valida para voz y texto."""
    mensaje = respuesta.get("mensaje_nancy") or "No obtuve una respuesta."
    estado = respuesta.get("estado_conversacion") or "inactiva"
    lineas = ["", "   NANCY dice:", ""]
    for linea in _envolver(mensaje)[:7]:
        lineas.append(f"   {linea}")
    datos = respuesta.get("datos") or {}
    transaccion = datos.get("transaccion")
    borrador = datos.get("borrador")
    meta = datos.get("meta")
    if transaccion:
        lineas += ["", f"   {str(transaccion.get('tipo', '')).upper()} {_dinero(transaccion.get('monto', 0))}"]
        if transaccion.get("meta"):
            lineas.append(f"   Meta: {transaccion['meta'][:22]}")
    if borrador:
        lineas += [
            "",
            f"   Meta: {str(borrador.get('nombre') or '')[:22]}",
            f"   Monto: {_dinero(borrador.get('monto_meta', 0))}",
        ]
    if meta:
        lineas += ["", f"   {str(meta.get('nombre') or '')[:24]}"]
    lineas += ["", f"   Estado: {estado}"]
    if respuesta.get("requiere_confirmacion"):
        lineas.append("   Di sí, está bien, ok o no")
    lineas.append("")
    return _caja(lineas)


def d16_error(titulo, mensaje, detalle=None):
    lineas = ["", f"   {str(titulo)[:30]}", ""]
    for linea in _envolver(mensaje)[:6]:
        lineas.append(f"   {linea}")
    if detalle:
        for linea in _envolver(detalle, ancho=ANCHO - 4)[:3]:
            lineas.append(f"   {linea}")
    lineas += ["", "   [T] Escribir o [H] Hablar", ""]
    return _caja(lineas)


def d17_microfono(dispositivo, pico, rms, correcto=True):
    lineas = [
        "",
        "   Prueba de micrófono",
        "",
        f"   Dispositivo: {str(dispositivo)[:20]}",
        f"   Pico: {pico}",
        f"   RMS: {rms}",
        "",
        "   " + ("Señal detectada." if correcto else "Casi no hay señal."),
        "",
    ]
    if not correcto:
        lineas += [
            "   Revisa el micrófono",
            "   en Windows o elige",
            "   otro dispositivo.",
            "",
        ]
    return _caja(lineas)


def menu():
    """Menu informativo: la entrada principal es la voz."""
    return (
        "\n"
        "  Habla con Nancy o escribe la misma frase natural.\n"
        "  Puedes decir:\n"
        "   - Gasté 20 mil en almuerzo\n"
        "   - Ahorré 50 mil para mi meta\n"
        "   - Quiero crear una meta para comprar audífonos\n"
        "   - ¿Cómo me fue hoy?  /  ¿Cómo van mis metas?\n"
        "   - Sí, está bien  /  No, cancela\n"
        "\n"
        "  [H] Hablar   [T] Escribir   [A] Probar micrófono   [V] Voz"
        "\n"
        "  [E] Estado del día   [C] Cerrar el día\n"
        "  [P] Plan de ahorro   [N] Notificaciones\n"
        "  [R] Repetir la última frase   [S] Salir"
    )
