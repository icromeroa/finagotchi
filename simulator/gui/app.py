"""Ventana gráfica del simulador FinaGotchi (Fase 24).

Replica el mockup del dispositivo (D01-D17) con CustomTkinter y la paleta
de ``tema.py``: conserva el flujo real del backend (hablar, escribir,
consultar, confirmar, cerrar) sin tocarlo. La consola de
``simulator/main.py`` sigue disponible.

Ejecución:

    py -3 -m simulator.gui.app
"""

import queue
import threading
import uuid
from datetime import datetime

import customtkinter as ctk

from simulator import pantallas, voice
from simulator.main import (
    CONFIG,
    ApiError,
    FinaGotchiClient,
    capture_voice,
    load_config,
    verificar_backend,
)

from . import sprites
from . import tema

ESTADO_ANIMO = {
    "FELIZ": "feliz",
    "PREOCUPADO": "preocupado",
    "TRISTE": "triste",
    "CRITICO": "critico",
}

# Iconos por nombre normalizado (sin tildes). Fallback genérico si no hay match.
ICONOS_CATEGORIA = {
    "alimentacion": "🍲",
    "transporte": "🚌",
    "cafe": "☕",
    "cafe y mecato": "☕",
    "salud": "💊",
    "casa": "🏠",
    "vivienda": "🏠",
    "educacion": "📚",
    "entretenimiento": "🎮",
    "ocio": "🎮",
    "ropa": "👕",
    "tecnologia": "💻",
    "servicios": "🧾",
    "trabajo": "💼",
    "nomina": "💼",
    "ingreso": "💵",
    "ingresos": "💵",
    "beca": "🎓",
    "apoyo": "🤝",
    "apoyo familiar": "🤝",
    "ahorro": "🐷",
    "emprendimiento": "🏪",
    "imprevistos": "🚨",
    "mantenimientos": "🔧",
    "abono": "💳",
    "otros": "💸",
}

ICONOS_CUENTA = {
    "efectivo": "💵",
    "nequi": "📱",
    "daviplata": "📲",
    "nu": "🏦",
    "billetera": "👛",
    "tarjeta": "💳",
    "banco": "🏦",
    "cuenta": "🏦",
}

def _normalizar_nombre(texto):
    import unicodedata

    limpio = unicodedata.normalize("NFKD", str(texto or "").lower())
    return "".join(c for c in limpio if not unicodedata.combining(c)).strip()


def _icono_para(nombre, tipo=None):
    clave = _normalizar_nombre(nombre)
    for pista, icono in ICONOS_CATEGORIA.items():
        if pista in clave or clave in pista:
            return icono
    if tipo == "gasto":
        return "💸"
    if tipo == "ingreso":
        return "💵"
    return "◎"


def _icono_cuenta(nombre):
    clave = _normalizar_nombre(nombre)
    for pista, icono in ICONOS_CUENTA.items():
        if pista in clave or clave in pista:
            return icono
    return "◉"


def _coach_tip(resumen, movimientos=None):
    """Tip corto de Nancy Coach calculado solo con los movimientos reales."""
    resumen = resumen or {}
    gastos = int(resumen.get("total_gastos") or resumen.get("gastos") or 0)
    ingresos = int(resumen.get("total_ingresos") or resumen.get("ingresos") or 0)
    presupuesto = int(resumen.get("presupuesto_diario") or 0)
    if gastos <= 0 and ingresos <= 0:
        return "Sin movimientos netos hoy. Registra al menos un gasto o ingreso para poder ayudarte con un consejo útil."
    por_cat = {}
    for mov in movimientos or []:
        if str(mov.get("tipo") or "gasto").lower() == "gasto":
            cat = str(mov.get("categoria") or "Otros")
            por_cat[cat] = por_cat.get(cat, 0) + int(mov.get("monto") or 0)
    if por_cat:
        top, total_top = max(por_cat.items(), key=lambda kv: kv[1])
        pct = int(round(total_top * 100 / gastos)) if gastos else 0
        if pct >= 60:
            return f"{top} concentra el {pct}% de tus gastos de hoy. Reducirlo un poco ya mejora tu saldo."
        if pct >= 35:
            return f"Vas bien, pero {top} pesa el {pct}% del gasto. Mantén ese control mañana."
    if presupuesto and gastos > presupuesto:
        return "Hoy pasaste el presupuesto. Mirar los gastos más frecuentes te puede devolver al rango seguro."
    if gastos < presupuesto * 0.7 if presupuesto else ingresos > 0:
        return "Vas en rango seguro. Mantén ese ritmo y registra cada gasto al momento."
    return "Anota tus movimientos al momento para que el consejo de mañana sea más preciso."


class App(ctk.CTk):
    def __init__(self, client=None, config=None, arranque=True):
        tema.registrar_fuentes()
        ctk.set_appearance_mode("light")
        super().__init__()
        self.title("FinaGotchi · Simulador")
        self.geometry(f"{tema.TAMANO_VENTANA[0]}x{tema.TAMANO_VENTANA[1]}")
        self.resizable(False, False)
        self.configure(fg_color=tema.NEUTRAL)

        self.config = config or load_config()
        self.client = client
        self.ultima_respuesta = None
        self.cola = queue.Queue()
        self._grabando = False
        self._sprite_fotos = []
        self._sprite_animacion = None
        self._construir_ui()
        self._actualizar_fecha()
        if arranque and client is None:
            threading.Thread(target=self._arranque_hilo, daemon=True).start()
        self.after(150, self._procesar_cola)

    # --- Construcción ---------------------------------------------------
    def _construir_ui(self):
        self.marco = ctk.CTkFrame(
            self, fg_color=tema.BORDE, corner_radius=28,
            border_width=6, border_color=tema.BORDE,
        )
        self.marco.pack(fill="both", expand=True, padx=6, pady=6)
        interior = ctk.CTkFrame(self.marco, fg_color=tema.NEUTRAL, corner_radius=20)
        interior.pack(fill="both", expand=True, padx=2, pady=2)
        self.cabecera = ctk.CTkFrame(interior, fg_color=tema.PRIMARY, corner_radius=14)
        self.cabecera.pack(fill="x", side="top", padx=8, pady=(8, 0))
        ctk.CTkLabel(
            self.cabecera, text="FinaGotchi", font=tema.headline(20),
            text_color="white",
        ).pack(side="left", padx=12, pady=6)
        self.etiqueta_fecha = ctk.CTkLabel(
            self.cabecera, text="", font=tema.cuerpo(12), text_color="white"
        )
        self.etiqueta_fecha.pack(side="right", padx=12)

        self.sprite = ctk.CTkLabel(interior, text="", fg_color=tema.SECONDARY,
                                   corner_radius=18, width=160, height=160)
        self.sprite.pack(pady=(8, 0), padx=10, anchor="center")
        self.etiqueta_animo = ctk.CTkLabel(
            interior, text="Nancy · Feliz", font=tema.headline(16), text_color=tema.PRIMARY
        )
        self.etiqueta_animo.pack()

        self.contenido = ctk.CTkScrollableFrame(
            interior, fg_color=tema.NEUTRAL, corner_radius=10
        )
        self.contenido.pack(fill="both", expand=True, padx=10, pady=6)

        self.entrada = ctk.CTkEntry(
            interior, placeholder_text="Escribe lo que quieres decir…",
            font=tema.cuerpo(13), fg_color="white", border_color=tema.BORDE,
            corner_radius=12, height=32,
        )
        self.entrada.pack(fill="x", padx=10, pady=(0, 6))
        self.entrada.bind("<Return>", lambda _e: self.enviar_entrada())

        botones = ctk.CTkFrame(interior, fg_color=tema.NEUTRAL)
        botones.pack(fill="x", padx=10, pady=(0, 10))
        definiciones = [
            ("🎙 Hablar", self.hablar, tema.TERTIARY),
            ("Enviar", self.enviar_entrada, tema.SECONDARY),
            ("Estado", self.estado_del_dia, tema.NEUTRAL),
            ("Plan", self.ver_plan, tema.NEUTRAL),
            ("Cerrar", self.cerrar_dia, tema.NEUTRAL),
            ("Avisos", self.ver_notificaciones, tema.NEUTRAL),
            ("Repetir", self.repetir, tema.NEUTRAL),
            ("Voz", self.alternar_voz, tema.NEUTRAL),
            ("Salir", self.destroy, tema.PRIMARY),
        ]
        for indice, (texto, accion, color) in enumerate(definiciones):
            ctk.CTkButton(
                botones, text=texto, command=accion, font=tema.cuerpo(12),
                fg_color=color, text_color=tema.TEXTO if color != tema.PRIMARY else "white",
                corner_radius=12, width=100, height=30,
            ).grid(row=indice // 3, column=indice % 3, padx=3, pady=3)

    # --- Utilidades ------------------------------------------------------
    def _actualizar_fecha(self):
        momento = datetime.now()
        self.etiqueta_fecha.configure(
            text=(
                f"{pantallas._DIAS_CORTO[momento.weekday()]} {momento.day} "
                f"{pantallas._MESES_CORTO[momento.month - 1]} · "
                f"{momento.hour:02d}:{momento.minute:02d}"
            )
        )
        self.after(30000, self._actualizar_fecha)

    def _poner_sprite(self, estado):
        if self._sprite_animacion:
            self.after_cancel(self._sprite_animacion)
            self._sprite_animacion = None
        frames, duracion = sprites.cargar_frames(estado)
        self._sprite_fotos = [sprites.foto(frame) for frame in frames]
        self.sprite.configure(image=self._sprite_fotos[0])
        if len(self._sprite_fotos) > 1:
            indice = [0]

            def avanzar():
                indice[0] = (indice[0] + 1) % len(self._sprite_fotos)
                self.sprite.configure(image=self._sprite_fotos[indice[0]])
                self._sprite_animacion = self.after(duracion, avanzar)

            self._sprite_animacion = self.after(duracion, avanzar)

    def _limpiar(self):
        for hijo in self.contenido.winfo_children():
            hijo.destroy()

    def _tarjeta(self, titulo, cuerpo, color=None):
        tarjeta = ctk.CTkFrame(
            self.contenido, fg_color=color or tema.SECONDARY, corner_radius=16,
            border_width=2, border_color=tema.BORDE,
        )
        ctk.CTkLabel(
            tarjeta, text=str(titulo), font=tema.headline(15),
            text_color=tema.PRIMARY, wraplength=300, justify="left",
        ).pack(anchor="w", padx=12, pady=(10, 0))
        ctk.CTkLabel(
            tarjeta, text=str(cuerpo), font=tema.cuerpo(13),
            text_color=tema.TEXTO, wraplength=300, justify="left",
        ).pack(anchor="w", padx=12, pady=(0, 10))
        tarjeta.pack(fill="x", pady=4, padx=4)

    def _procesar_cola(self):
        try:
            while True:
                accion, payload = self.cola.get_nowait()
                if accion == "balance":
                    hoy = (payload or {}).get("hoy", {})
                    mascota = (payload or {}).get("mascota", {})
                    movimientos = (payload or {}).get("movimientos") or []
                    resumen = {
                        "total_ingresos": hoy.get("ingresos", 0),
                        "total_gastos": hoy.get("gastos", 0),
                        "total_ahorrado": hoy.get("ahorro", 0),
                        "presupuesto_diario": hoy.get("presupuesto_diario", 0),
                        "num_registros": hoy.get("num_registros", len(movimientos)),
                        "balance_neto": hoy.get("balance_neto", 0),
                    }
                    salud = mascota.get("salud")
                    self.etiqueta_animo.configure(text=f"Nancy · {str(mascota.get('animo') or 'FELIZ').capitalize()}")
                    self._poner_sprite(ESTADO_ANIMO.get(str(mascota.get("animo") or "FELIZ"), "feliz"))
                    self._limpiar()
                    self._vista_balance_v11(
                        hoy, resumen, movimientos, salud=salud,
                        etiqueta_fecha=str((payload or {}).get("fecha_local") or "hoy"),
                    )
                elif accion == "vinculacion":
                    self.mostrar_vinculacion(payload)
                elif accion == "reposo":
                    self.mostrar_reposo(payload)
                elif accion == "respuesta":
                    self._procesar_respuesta(payload)
                elif accion == "texto":
                    titulo, mensaje, *extra = payload
                    if extra:
                        self.mostrar_texto(titulo, mensaje, estado_sprite=extra[0], etiqueta_animo=extra[1] if len(extra) > 1 else None)
                    else:
                        self.mostrar_texto(titulo, mensaje)
                elif accion == "sprite":
                    self._poner_sprite(payload)
                    etiqueta = {
                        "escuchando": "Nancy · Escuchando",
                        "puntos": "Nancy · Pensando",
                        "ola": "Nancy · Escuchando",
                        "dormida": "Nancy · Dormida",
                    }.get(str(payload).lower())
                    if etiqueta:
                        self.etiqueta_animo.configure(text=etiqueta)
        except queue.Empty:
            pass
        self.after(150, self._procesar_cola)

    # --- Arranque ---------------------------------------------------------
    def _arranque_hilo(self):
        if not verificar_backend():
            self.cola.put(("texto", ("Sin conexión", "No se pudo conectar con el backend.")))
            return
        client = FinaGotchiClient(self.config)
        try:
            client.login_or_register()
            # Flujo sync: simulador genera PIN, Flutter lo ingresa, simulador reclama.
            try:
                registration = client.generar_pin()
                pin = registration["pin"]
            except RuntimeError:
                # Ya vinculado a otra cuenta: cae al flujo auto para demo.
                client.ensure_device()
                pin = None
            if pin is not None:
                self.cola.put(("vinculacion", {
                    "device_uid": client.device_uid,
                    "pin": pin,
                }))
                # Polling de claim cada 3s por hasta 10 minutos (expiry del PIN)
                import time as _time
                inicio = _time.monotonic()
                while _time.monotonic() - inicio < 600:
                    try:
                        client.claim_token(pin)
                        break
                    except ApiError as exc:
                        if exc.status not in (409, 401):
                            raise
                        self.cola.put(("vinculacion", {
                            "device_uid": client.device_uid,
                            "pin": pin,
                            "esperando": True,
                        }))
                        _time.sleep(3)
                else:
                    self.cola.put(("texto", ("Sin vinculación", "El PIN expiró (10 min). Reinicia el simulador para generar uno nuevo.")))
                    return
            client.telemetry()
        except ApiError as exc:
            self.cola.put(("texto", ("Error al vincular", str(exc))))
            return
        self.client = client
        self.cola.put(("reposo", self._home_seguro()))

    def _home_seguro(self):
        try:
            return self.client.home()
        except Exception:  # noqa: BLE001 - sin home, el reposo muestra ceros
            return {}

    # --- Pantallas ---------------------------------------------------------

    def mostrar_vinculacion(self, vinculacion):
        """D02 Sin vincular: muestra PIN grande esperando el ingreso en Flutter."""
        self._limpiar()
        self.etiqueta_animo.configure(text="Nancy · Esperando")
        self._poner_sprite("puntos")
        pin = str((vinculacion or {}).get("pin") or "------")
        device_uid = str((vinculacion or {}).get("device_uid") or "")
        tarjeta = ctk.CTkFrame(
            self.contenido, fg_color=tema.SECONDARY, corner_radius=16,
            border_width=2, border_color=tema.BORDE,
        )
        ctk.CTkLabel(
            tarjeta, text="Enlaza tu finagotchi",
            font=tema.headline(18), text_color=tema.PRIMARY,
        ).pack(pady=(12, 0))
        ctk.CTkLabel(
            tarjeta,
            text="Escribe este PIN en la app Flutter (Conectar → PIN manual).",
            font=tema.cuerpo(12), text_color=tema.TEXTO, wraplength=280, justify="center",
        ).pack(padx=12)
        ctk.CTkLabel(
            tarjeta, text=pin, font=("Outfit", 42, "bold"), text_color=tema.TEXTO,
        ).pack(pady=8)
        ctk.CTkLabel(
            tarjeta,
            text=f"Dispositivo: {device_uid}\nVálido 10 minutos. Esperando que lo ingreses en Flutter…",
            font=tema.cuerpo(11), text_color=tema.TEXTO, wraplength=280, justify="center",
        ).pack(padx=12, pady=(0, 12))
        tarjeta.pack(fill="x", pady=4, padx=4)

    def mostrar_reposo(self, home):
        self._limpiar()
        hoy = (home or {}).get("hoy", {})
        mascota = (home or {}).get("mascota", {})
        animo = str(mascota.get("animo") or "FELIZ")
        self.etiqueta_animo.configure(text=f"Nancy · {animo.capitalize()}")
        self._poner_sprite(ESTADO_ANIMO.get(animo, "feliz"))
        self._tarjeta(
            "Cupo del día",
            f"Te quedan {pantallas._dinero(hoy.get('cupo_restante', 0))} de "
            f"{pantallas._dinero(hoy.get('presupuesto_diario', 0))}\n"
            f"Gastos {pantallas._dinero(hoy.get('gastos', 0))} · "
            f"Ingresos {pantallas._dinero(hoy.get('ingresos', 0))}",
        )
        self._tarjeta(
            "Estado",
            f"Salud {mascota.get('salud', 100)}% · Puntos {(home or {}).get('puntos', 0)}"
            "\nMantén [ESPACIO] y habla, o escribe tu frase abajo.",
            tema.NEUTRAL,
        )

    def mostrar_texto(self, titulo, mensaje, estado_sprite=None, etiqueta_animo=None):
        self._limpiar()
        if estado_sprite:
            self._poner_sprite(estado_sprite)
        if etiqueta_animo:
            self.etiqueta_animo.configure(text=etiqueta_animo)
        self._tarjeta(titulo, mensaje)

    # --- Vistas estructuradas (sin volcar diccionarios crudos) ------------
    def _mini(self, padre, fila, columna, icono, nombre, linea, distintivo, color_distintivo):
        tarjeta = ctk.CTkFrame(
            padre, fg_color=tema.NEUTRAL, corner_radius=16,
            border_width=2, border_color=tema.BORDE,
        )
        ctk.CTkLabel(
            tarjeta, text=icono, font=tema.headline(18),
            text_color=tema.PRIMARY, fg_color=tema.SECONDARY,
            corner_radius=20, width=40, height=40,
        ).grid(row=0, column=0, padx=8, pady=8)
        ctk.CTkLabel(
            tarjeta, text=distintivo, font=tema.cuerpo(10),
            text_color=tema.TEXTO, fg_color=color_distintivo, corner_radius=8,
        ).grid(row=0, column=1, padx=4, pady=8, sticky="e")
        ctk.CTkLabel(
            tarjeta, text=str(nombre), font=tema.headline(14),
            text_color=tema.PRIMARY, wraplength=130, justify="left",
        ).grid(row=1, column=0, columnspan=2, padx=8, sticky="w")
        ctk.CTkLabel(
            tarjeta, text=str(linea), font=tema.cuerpo(12),
            text_color=tema.TEXTO, wraplength=130, justify="left",
        ).grid(row=2, column=0, columnspan=2, padx=8, pady=(0, 8), sticky="w")
        tarjeta.grid(row=fila, column=columna, padx=4, pady=4, sticky="nsew")
        return tarjeta

    def _vista_cuentas(self, cuentas):
        self._tarjeta("Cuentas", f"{len(cuentas)} cuentas visibles", tema.SECONDARY)
        rejilla = ctk.CTkFrame(self.contenido, fg_color=tema.NEUTRAL)
        rejilla.pack(fill="x")
        rejilla.columnconfigure(0, weight=1)
        rejilla.columnconfigure(1, weight=1)
        for indice, cuenta in enumerate(cuentas[:8]):
            distintivo = "PREDET." if cuenta.get("es_sistema") else "TUYA"
            color = tema.SECONDARY if cuenta.get("es_sistema") else tema.TERTIARY
            self._mini(
                rejilla, indice // 2, indice % 2, _icono_cuenta(cuenta.get("nombre")),
                cuenta.get("nombre") or "?",
                f"{cuenta.get('num_movs') or 0} movs · "
                f"{pantallas._dinero(cuenta.get('saldo_actual'))}",
                distintivo, color,
            )

    def _vista_categorias(self, categorias):
        self._categorias = categorias
        self._tarjeta(
            "Categorías",
            "Nancy aprende de estas categorías para ordenar tus audios y mensajes al instante.",
            tema.SECONDARY,
        )
        botones = ctk.CTkFrame(self.contenido, fg_color=tema.NEUTRAL)
        botones.pack(fill="x", pady=4)
        self._boton_gastos = ctk.CTkButton(
            botones, text="Gastos", width=150, fg_color=tema.PRIMARY,
            text_color="white", font=tema.headline(14), corner_radius=12,
            command=lambda: self._pintar_categorias("gasto"),
        )
        self._boton_gastos.pack(side="left", padx=4)
        self._boton_ingresos = ctk.CTkButton(
            botones, text="Ingresos", width=150, fg_color=tema.SECONDARY,
            text_color=tema.TEXTO, font=tema.headline(14), corner_radius=12,
            command=lambda: self._pintar_categorias("ingreso"),
        )
        self._boton_ingresos.pack(side="left", padx=4)
        self._rejilla_categorias = ctk.CTkFrame(self.contenido, fg_color=tema.NEUTRAL)
        self._rejilla_categorias.pack(fill="x")
        self._rejilla_categorias.columnconfigure(0, weight=1)
        self._rejilla_categorias.columnconfigure(1, weight=1)
        self._pintar_categorias("gasto")

    def _pintar_categorias(self, tipo):
        self._tipo_categorias_activa = tipo
        # Estado visual de las pestañas (bug: no se quedaba seleccionado)
        self._boton_gastos.configure(
            fg_color=tema.PRIMARY if tipo == "gasto" else tema.SECONDARY,
            text_color="white" if tipo == "gasto" else tema.TEXTO,
        )
        self._boton_ingresos.configure(
            fg_color=tema.PRIMARY if tipo == "ingreso" else tema.SECONDARY,
            text_color="white" if tipo == "ingreso" else tema.TEXTO,
        )
        for hijo in self._rejilla_categorias.winfo_children():
            hijo.destroy()
        lista = [c for c in self._categorias if c.get("tipo") == tipo]
        lista = sorted(lista, key=lambda c: int(c.get("num_registros") or 0), reverse=True)
        for indice, categoria in enumerate(lista[:8]):
            distintivo = "PREDET." if categoria.get("es_sistema") else "TUYA"
            color = tema.SECONDARY if categoria.get("es_sistema") else tema.TERTIARY
            nombre = categoria.get("nombre") or "?"
            self._mini(
                self._rejilla_categorias, indice // 2, indice % 2,
                _icono_para(nombre, tipo),
                nombre,
                f"{categoria.get('num_registros') or 0} movs",
                distintivo, color,
            )

    def _vista_metas(self, metas):
        activas = [m for m in metas if m.get("estado") == "activa"] or metas
        total_ahorrado = sum(int(m.get("ahorrado") or 0) for m in activas)
        total_meta = sum(int(m.get("monto_meta") or 0) for m in activas) or 1
        self._tarjeta(
            "Metas de ahorro",
            f"Has ahorrado {pantallas._dinero(total_ahorrado)} · "
            f"{len(activas)} metas activas",
            tema.SECONDARY,
        )
        barra = ctk.CTkProgressBar(
            self.contenido, fg_color=tema.SECONDARY, progress_color=tema.TERTIARY,
            height=14, corner_radius=8,
        )
        barra.pack(fill="x", padx=8, pady=4)
        barra.set(max(0.0, min(1.0, total_ahorrado / total_meta)))
        for meta in activas[:5]:
            ahorrado = int(meta.get("ahorrado") or 0)
            monto = int(meta.get("monto_meta") or 0)
            porcentaje = int(round((ahorrado / monto * 100) if monto else 0))
            estado = str(meta.get("estado_plan") or meta.get("estado") or "En curso")
            fecha = str(meta.get("fecha_limite") or "")[:10]
            linea = (
                f"{pantallas._dinero(ahorrado)} de {pantallas._dinero(monto)} · {porcentaje}%\n"
                f"Meta: {fecha} · Ahorra {pantallas._dinero(meta.get('aporte_periodico'))}"
            )
            tarjeta = ctk.CTkFrame(
                self.contenido, fg_color=tema.NEUTRAL, corner_radius=16,
                border_width=2, border_color=tema.BORDE,
            )
            ctk.CTkLabel(
                tarjeta, text=str(meta.get("nombre") or "Meta"),
                font=tema.headline(14), text_color=tema.PRIMARY, wraplength=300,
            ).pack(anchor="w", padx=12, pady=(10, 0))
            ctk.CTkLabel(
                tarjeta, text=str(estado), font=tema.cuerpo(11),
                text_color=tema.TEXTO, fg_color=tema.TERTIARY, corner_radius=8,
            ).pack(anchor="e", padx=12)
            ctk.CTkLabel(
                tarjeta, text=linea, font=tema.cuerpo(12), text_color=tema.TEXTO,
                wraplength=300, justify="left",
            ).pack(anchor="w", padx=12, pady=(0, 6))
            progreso = ctk.CTkProgressBar(
                tarjeta, fg_color=tema.SECONDARY, progress_color=tema.TERTIARY,
                height=10, corner_radius=6,
            )
            progreso.pack(fill="x", padx=12, pady=(0, 10))
            progreso.set(max(0.0, min(1.0, porcentaje / 100)))
            tarjeta.pack(fill="x", pady=4, padx=4)

    def _vista_pendientes(self, pendientes):
        self._tarjeta(
            "Pendientes", f"{len(pendientes)} sin confirmar", tema.SECONDARY
        )
        for pendiente in pendientes[:5]:
            self._tarjeta(
                str(pendiente.get("tipo") or "").capitalize(),
                f"{pantallas._dinero(pendiente.get('monto', 0))} · "
                f"{pendiente.get('categoria') or pendiente.get('meta') or ''} · "
                f"{pendiente.get('cuenta') or ''}",
                tema.NEUTRAL,
            )

    def _vista_balance_v11(self, hoy, resumen=None, movimientos=None, salud=None, etiqueta_fecha="hoy"):
        resumen = resumen or {}
        movimientos = movimientos or []
        total_ingresos = int(resumen.get("total_ingresos") or hoy.get("ingresos") or 0)
        total_gastos = int(resumen.get("total_gastos") or hoy.get("gastos") or 0)
        total_ahorro = int(resumen.get("total_ahorrado") or hoy.get("ahorro") or 0)
        balance = int(resumen.get("balance_neto") or hoy.get("balance_neto") or (total_ingresos - total_gastos))
        presupuesto = int(resumen.get("presupuesto_diario") or hoy.get("presupuesto_diario") or 0)
        num_mov = int(resumen.get("num_registros") or hoy.get("num_registros") or len(movimientos) or 0)
        cupo = presupuesto - total_gastos if presupuesto else int(hoy.get("cupo_restante") or 0)
        if salud is None:
            pet = int(hoy.get("salud") or 0) if isinstance(hoy, dict) else 0
            salud = pet or (100 - int(round(total_gastos * 100 / presupuesto)) if presupuesto and total_gastos else 84)
        salud = max(0, min(100, int(salud)))
        # Encabezado V11.1
        self._tarjeta(
            "Balance del día",
            str(etiqueta_fecha or "hoy"),
            tema.SECONDARY,
        )
        # Arco circular + saldo
        cont = ctk.CTkFrame(self.contenido, fg_color=tema.NEUTRAL)
        cont.pack(fill="x", padx=4, pady=2)
        ctk.CTkLabel(
            cont, text=f"{salud}%", font=("Outfit", 36, "bold"),
            text_color=tema.TERTIARY if salud >= 50 else "#C0392B",
        ).pack(pady=(6, 0))
        ctk.CTkLabel(
            cont, text="EN RANGO SEGURO" if salud >= 60 else "REVISAR",
            font=tema.cuerpo(11), text_color=tema.TEXTO,
        ).pack()
        ctk.CTkLabel(
            cont, text="SALDO NETO DEL DÍA", font=tema.cuerpo(11), text_color=tema.TEXTO,
        ).pack(pady=(6, 0))
        signo = "+" if balance >= 0 else ""
        ctk.CTkLabel(
            cont,
            text=f"{signo}{pantallas._dinero(balance)} COP",
            font=tema.headline(20),
            text_color=tema.TERTIARY if balance >= 0 else "#C0392B",
        ).pack()
        ctk.CTkLabel(
            cont,
            text="✓ Superávit" if balance >= 0 else "Revisar ritmo",
            font=tema.cuerpo(11), text_color=tema.TEXTO, fg_color=tema.TERTIARY, corner_radius=8,
        ).pack(pady=2)
        # Ingresos / Gastos totales
        fila = ctk.CTkFrame(self.contenido, fg_color=tema.NEUTRAL)
        fila.pack(fill="x", padx=4, pady=2)
        for titulo, valor, sub in (
            ("Ingresos Totales", f"{pantallas._dinero(total_ingresos)} COP", f"{num_mov} registros"),
            ("Gastos Totales", f"-{pantallas._dinero(total_gastos)} COP", f"{num_mov} registros"),
        ):
            caja = ctk.CTkFrame(fila, fg_color=tema.NEUTRAL, border_width=2, border_color=tema.BORDE, corner_radius=14)
            ctk.CTkLabel(caja, text=titulo, font=tema.cuerpo(11), text_color=tema.TEXTO).pack(anchor="w", padx=10, pady=(8, 0))
            ctk.CTkLabel(caja, text=valor, font=tema.headline(15), text_color=tema.PRIMARY).pack(anchor="w", padx=10)
            ctk.CTkLabel(caja, text=sub, font=tema.cuerpo(11), text_color=tema.TEXTO).pack(anchor="w", padx=10, pady=(0, 8))
            caja.pack(side="left", fill="x", expand=True, padx=3)
        # Presupuesto
        caja = ctk.CTkFrame(self.contenido, fg_color=tema.NEUTRAL, border_width=2, border_color=tema.BORDE, corner_radius=14)
        ctk.CTkLabel(
            caja, text=f"Presupuesto diario  {pantallas._dinero(total_gastos)} / {pantallas._dinero(presupuesto)} COP",
            font=tema.cuerpo(12), text_color=tema.TEXTO,
        ).pack(anchor="w", padx=10, pady=(8, 2))
        barra = ctk.CTkProgressBar(caja, fg_color=tema.SECONDARY, progress_color=tema.TERTIARY, height=12, corner_radius=8)
        barra.pack(fill="x", padx=10)
        barra.set(max(0.0, min(1.0, total_gastos / presupuesto)) if presupuesto else 0.0)
        ctk.CTkLabel(caja, text=f"Margen libre: {pantallas._dinero(max(0, cupo))} COP", font=tema.cuerpo(11), text_color=tema.TEXTO).pack(anchor="w", padx=10, pady=(2, 8))
        caja.pack(fill="x", padx=4, pady=4)
        # Análisis Nancy Coach (tip IA local deterministic)
        tip = _coach_tip(resumen, movimientos)
        if total_gastos and presupuesto:
            tip += f" Tu cupo restante es {pantallas._dinero(max(0, cupo))} COP."
        self._tarjeta("💡 Análisis de Nancy Coach", tip, tema.SECONDARY)
        # Gastos por categoría
        por_cat = {}
        for mov in movimientos:
            if str(mov.get("tipo") or "gasto").lower() == "gasto":
                cat = str(mov.get("categoria") or "Otros")
                por_cat[cat] = por_cat.get(cat, 0) + int(mov.get("monto") or 0)
        if por_cat:
            ctk.CTkLabel(
                self.contenido, text=f"🏷️ Gastos por Categoría  ·  {sum(1 for v in por_cat.values() if v)} activas hoy",
                font=tema.headline(13), text_color=tema.PRIMARY,
            ).pack(anchor="w", padx=8, pady=(6, 2))
            top = max(por_cat.values()) or 1
            for cat, total in sorted(por_cat.items(), key=lambda kv: kv[1], reverse=True)[:5]:
                pct = int(round(total * 100 / total_gastos)) if total_gastos else 0
                estado = "Rango seguro" if pct < 50 else "En presupuesto" if pct < 70 else "Revisar"
                tarjeta = ctk.CTkFrame(
                    self.contenido, fg_color=tema.NEUTRAL, corner_radius=14,
                    border_width=2, border_color=tema.BORDE,
                )
                ctk.CTkLabel(
                    tarjeta, text=f"{_icono_para(cat, 'gasto')} {cat}", font=tema.headline(13), text_color=tema.PRIMARY,
                ).pack(anchor="w", padx=10, pady=(8, 0))
                ctk.CTkLabel(
                    tarjeta, text=f"{pantallas._dinero(total)} COP · {pct}% del gasto · {estado}",
                    font=tema.cuerpo(12), text_color=tema.TEXTO,
                ).pack(anchor="w", padx=10)
                barra = ctk.CTkProgressBar(tarjeta, fg_color=tema.SECONDARY, progress_color=tema.TERTIARY, height=8, corner_radius=6)
                barra.pack(fill="x", padx=10, pady=(2, 8))
                barra.set(max(0.0, min(1.0, total / top)))
                tarjeta.pack(fill="x", pady=3, padx=4)
        if movimientos:
            ctk.CTkLabel(
                self.contenido, text=f"• {num_mov} movimientos registrados",
                font=tema.cuerpo(11), text_color=tema.TEXTO,
            ).pack(padx=8)

    def _vista_resumen(self, datos):
        resumen = datos.get("resumen") or {}
        movimientos = datos.get("movimientos") or []
        # Balance V11.1 cuando es consulta (¿cómo me fue hoy? / esta semana / rango)
        if resumen:
            # Extraer salud si viene en datos (mascota o proyección)
            salud = None
            if datos.get("mascota"):
                salud = datos["mascota"].get("salud")
            elif datos.get("proyeccion_hoy"):
                salud = datos["proyeccion_hoy"].get("salud_proyectada") or datos["proyeccion_hoy"].get("salud")
            etiqueta = str(resumen.get("desde") or datos.get("periodo") or "hoy")
            self._vista_balance_v11({}, resumen, movimientos, salud=salud, etiqueta_fecha=f"Resumen — {etiqueta}")
            return
        for movimiento in (datos.get("movimientos") or [])[:5]:
            self._tarjeta(
                str(movimiento.get("tipo") or "").capitalize(),
                f"{pantallas._dinero(movimiento.get('monto', 0))} · "
                f"{movimiento.get('categoria') or movimiento.get('cuenta') or ''} · "
                f"{movimiento.get('fecha_local') or ''}",
                tema.NEUTRAL,
            )

    def _procesar_respuesta(self, respuesta):
        if not isinstance(respuesta, dict):
            return
        self.ultima_respuesta = respuesta
        self._limpiar()
        self._poner_sprite(
            ESTADO_ANIMO.get(
                str((respuesta.get("datos") or {}).get("animo") or "FELIZ"), "feliz"
            )
            if not respuesta.get("requiere_confirmacion")
            else "escuchando"
        )
        escuchado = respuesta.get("texto_transcrito")
        if escuchado:
            self._tarjeta("Escuché", f'"{escuchado}"', tema.NEUTRAL)
        datos = respuesta.get("datos") or {}
        transaccion = datos.get("transaccion")
        if transaccion:
            self._tarjeta(
                str(transaccion.get("tipo", "")).capitalize(),
                f"{pantallas._dinero(transaccion.get('monto', 0))} "
                f"· {transaccion.get('categoria') or ''} "
                f"· {transaccion.get('cuenta') or ''}".strip(),
                tema.TERTIARY,
            )
        # Nancy lo dice en voz; en pantalla solo se muestra información
        # estructurada. Los avisos (aclaración/error/ayuda) sí se muestran:
        # sin ellos el usuario no sabe por qué se pidió aclaración.
        if respuesta.get("tipo_respuesta") in ("aclaracion", "error", "ayuda"):
            self._tarjeta(
                "Aviso", respuesta.get("mensaje_nancy") or "No obtuve respuesta."
            )
        if datos.get("cuentas"):
            self._vista_cuentas(datos["cuentas"])
        elif datos.get("categorias"):
            self._vista_categorias(datos["categorias"])
        elif datos.get("metas"):
            self._vista_metas(datos["metas"])
        elif datos.get("pendientes"):
            self._vista_pendientes(datos["pendientes"])
        elif datos.get("resumen") or datos.get("movimientos"):
            self._vista_resumen(datos)
        if respuesta.get("requiere_confirmacion"):
            fila = ctk.CTkFrame(self.contenido, fg_color=tema.NEUTRAL)
            ctk.CTkButton(
                fila, text="✓ Sí", width=160, fg_color=tema.TERTIARY,
                text_color=tema.TEXTO, font=tema.headline(16),
                command=lambda: self.enviar_texto("sí"),
            ).pack(side="left", padx=4)
            ctk.CTkButton(
                fila, text="✗ No", width=160, fg_color=tema.SECONDARY,
                text_color=tema.TEXTO, font=tema.headline(16),
                command=lambda: self.enviar_texto("no"),
            ).pack(side="left", padx=4)
            fila.pack(pady=6)

    # --- Acciones (hilos: la red y el micrófono bloquean) ----------------
    def _hilo(self, funcion):
        threading.Thread(target=funcion, daemon=True).start()

    def hablar(self):
        if self._grabando or self.client is None:
            return
        self._grabando = True
        self._poner_sprite("ola")
        self.etiqueta_animo.configure(text="Nancy · Escuchando")
        self.mostrar_texto("Te escucho", "Mantén presionada la tecla ESPACIO y habla. Suelta para enviar.")

        def trabajo():
            wav_bytes, duracion, _stats = capture_voice()
            self._grabando = False
            if not wav_bytes:
                self.cola.put(("texto", ("Sin audio", "No se pudo capturar la frase.")))
                return
            self.cola.put(("texto", ("Procesando", "Entendiendo tu mensaje…", "puntos", "Nancy · Pensando")))
            self.cola.put(("sprite", "puntos"))
            try:
                respuesta = self.client.send_audio(
                    wav_bytes, duracion, str(uuid.uuid4())
                )
            except ApiError as exc:
                self.cola.put(("texto", ("Error al procesar", str(exc))))
                return
            self._hablar_respuesta(respuesta)
            self.cola.put(("respuesta", respuesta))

        self._hilo(trabajo)

    def enviar_entrada(self):
        texto = self.entrada.get().strip()
        if texto:
            self.entrada.delete(0, "end")
            self.enviar_texto(texto)

    def enviar_texto(self, texto):
        if self.client is None:
            return
        self.mostrar_texto(
            "Procesando", "Entendiendo tu mensaje…",
            estado_sprite="puntos", etiqueta_animo="Nancy · Pensando",
        )

        def trabajo():
            try:
                respuesta = self.client.send_text(texto, str(uuid.uuid4()))
            except ApiError as exc:
                self.cola.put(("texto", ("Error al procesar", str(exc))))
                return
            self._hablar_respuesta(respuesta)
            self.cola.put(("respuesta", respuesta))

        self._hilo(trabajo)

    def _hablar_respuesta(self, respuesta):
        def trabajo():
            try:
                voice.hablar(self.client, respuesta, self.config)
            except Exception:  # noqa: BLE001 - el audio no bloquea la GUI
                pass

        threading.Thread(target=trabajo, daemon=True).start()

    def estado_del_dia(self):
        if self.client is None:
            return

        def trabajo():
            home = self._home_seguro()
            hoy = (home or {}).get("hoy", {})
            fecha = (home or {}).get("fecha_local") or ""
            movimientos = []
            try:
                payload = self.client.request(
                    "GET",
                    "/transactions",
                    params={"desde": fecha, "hasta": fecha, "tipo": "gasto", "limit": 50, "offset": 0},
                    headers=self.client.user_headers(),
                )
                if isinstance(payload, dict):
                    movimientos = payload.get("items") or []
                elif isinstance(payload, list):
                    movimientos = payload
            except Exception:  # noqa: BLE001 - el balance se pinta sin desglose
                movimientos = []
            home = dict(home or {})
            home["movimientos"] = movimientos
            self.cola.put(("balance", home))

        self._hilo(trabajo)

    def ver_plan(self):
        if self.client is None:
            return
        def trabajo():
            try:
                plan = self.client.goal_plan(12)
                resumen = plan.get("resumen") or {}
                linea = (
                    f"Capacidad mes 1: {pantallas._dinero(plan.get('capacidad_mes_actual', 0))}\n"
                    f"Metas: {resumen.get('metas_totales', 0)} · "
                    f"Cumplimiento: {int(round((resumen.get('cumplimiento_ponderado') or 0) * 100))}%"
                )
                self.cola.put(("texto", ("Plan de ahorro", linea)))
            except ApiError as exc:
                self.cola.put(("texto", ("Sin plan", str(exc))))

        self._hilo(trabajo)

    def cerrar_dia(self):
        if self.client is None:
            return
        def trabajo():
            try:
                cierre = self.client.close_day()
                self.cola.put(("texto", ("Cierre del día", str(cierre))))
                self.cola.put(("sprite", "dormida"))
            except ApiError as exc:
                self.cola.put(("texto", ("No se pudo cerrar", str(exc))))

        self._hilo(trabajo)

    def ver_notificaciones(self):
        if self.client is None:
            return
        def trabajo():
            try:
                payload = self.client.notifications(0)
                filas = payload.get("notificaciones") or []
                if not filas:
                    self.cola.put(("texto", ("Avisos", "Sin avisos.")))
                else:
                    lineas = "\n".join(
                        f"{f.get('titulo') or 'Aviso'}: {f.get('mensaje') or ''}"
                        for f in filas[:5]
                    )
                    self.cola.put(("texto", ("Avisos", lineas)))
            except ApiError as exc:
                self.cola.put(("texto", ("Sin avisos", str(exc))))

        self._hilo(trabajo)

    def repetir(self):
        if self.ultima_respuesta:
            self._procesar_respuesta(self.ultima_respuesta)

    def alternar_voz(self):
        activado = voice.alternar()
        self.mostrar_texto("Voz de Nancy", "Activada" if activado else "Silenciada")

    def salir(self):
        self.destroy()


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
