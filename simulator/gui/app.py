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
    MICROFONO_DISPONIBLE,
    NIVEL_SILENCIO,
    ApiError,
    FinaGotchiClient,
    Grabacion,
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
        self._grabadora = None
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
            boton = ctk.CTkButton(
                botones, text=texto, command=accion, font=tema.cuerpo(12),
                fg_color=color, text_color=tema.TEXTO if color != tema.PRIMARY else "white",
                corner_radius=12, width=100, height=30,
            )
            boton.grid(row=indice // 3, column=indice % 3, padx=3, pady=3)
            if texto.endswith("Hablar"):
                self.boton_hablar = boton

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
                if accion == "reposo":
                    self.mostrar_reposo(payload)
                elif accion == "respuesta":
                    self._procesar_respuesta(payload)
                elif accion == "texto":
                    titulo, mensaje = payload
                    self.mostrar_texto(titulo, mensaje)
                elif accion == "sprite":
                    self._poner_sprite(payload)
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
            client.ensure_device()
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

    def mostrar_texto(self, titulo, mensaje):
        self._limpiar()
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
                rejilla, indice // 2, indice % 2, "◉",
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
        for hijo in self._rejilla_categorias.winfo_children():
            hijo.destroy()
        lista = [c for c in self._categorias if c.get("tipo") == tipo]
        activos = [c for c in lista if c.get("num_registros")]
        self._tarjeta(
            f"Catálogo activo — {tipo}",
            f"{len(activos)} movimientos registrados",
            tema.NEUTRAL,
        )
        for indice, categoria in enumerate(lista[:8]):
            distintivo = "PREDET." if categoria.get("es_sistema") else "TUYA"
            color = tema.SECONDARY if categoria.get("es_sistema") else tema.TERTIARY
            self._mini(
                self._rejilla_categorias, indice // 2, indice % 2,
                str(categoria.get("nombre") or "?")[:1].upper(),
                categoria.get("nombre") or "?",
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

    def _vista_resumen(self, datos):
        resumen = datos.get("resumen") or {}
        if resumen:
            self._tarjeta(
                "Resumen",
                f"Ingresos {pantallas._dinero(resumen.get('total_ingresos', 0))} · "
                f"Gastos {pantallas._dinero(resumen.get('total_gastos', 0))} · "
                f"Ahorro {pantallas._dinero(resumen.get('total_ahorrado', 0))}",
                tema.SECONDARY,
            )
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
        if self.client is None:
            return

        if not self._grabando:
            if not MICROFONO_DISPONIBLE:
                self.mostrar_texto(
                    "Sin micrófono",
                    "No se pudo cargar sounddevice/PortAudio. "
                    "Instala requirements-simulator.txt.",
                )
                return
            self._grabadora = Grabacion()
            try:
                nombre = self._grabadora.iniciar()
            except Exception as exc:  # noqa: BLE001 - el micrófono no debe tumbar la GUI
                self.mostrar_texto("Sin micrófono", str(exc))
                self._grabadora = None
                return
            self._grabando = True
            self._poner_sprite("ola")
            self.mostrar_texto(
                "Te escucho",
                f"Habla ahora ({nombre}) y pulsa [Detener] al terminar.",
            )
            self.boton_hablar.configure(text="■ Detener")
            return

        self._grabando = False
        self.boton_hablar.configure(text="🎙 Hablar")
        try:
            wav_bytes, duracion, stats = self._grabadora.detener()
        except Exception as exc:  # noqa: BLE001
            self.mostrar_texto("Error de audio", str(exc))
            return
        finally:
            self._grabadora = None

        if not wav_bytes:
            if stats.get("pico", 0) < NIVEL_SILENCIO:
                self.mostrar_texto(
                    "No escuché tu voz",
                    "Revisa el micrófono o escribe la frase en el campo de texto.",
                )
            else:
                self.mostrar_texto("Audio vacío", "No se pudo capturar la frase.")
            return

        self.mostrar_texto("Procesando", "Entendiendo tu mensaje…")
        self._poner_sprite("puntos")

        def trabajo():
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

    def destroy(self):
        if getattr(self, "_grabando", False) and getattr(self, "_grabadora", None):
            try:
                self._grabadora.detener()
            except Exception:  # noqa: BLE001
                pass
        super().destroy()

    def enviar_entrada(self):
        texto = self.entrada.get().strip()
        if texto:
            self.entrada.delete(0, "end")
            self.enviar_texto(texto)

    def enviar_texto(self, texto):
        if self.client is None:
            return
        self.mostrar_texto("Procesando", "Entendiendo tu mensaje…")

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
        self.cola.put(("reposo", self._home_seguro()))

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
