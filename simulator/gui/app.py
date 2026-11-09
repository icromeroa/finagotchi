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
        self.cabecera = ctk.CTkFrame(self, fg_color=tema.PRIMARY, corner_radius=0)
        self.cabecera.pack(fill="x", side="top", padx=8, pady=(8, 0))
        ctk.CTkLabel(
            self.cabecera, text="FINAGOTCHI", font=tema.headline(22),
            text_color="white",
        ).pack(side="left", padx=12, pady=8)
        self.etiqueta_fecha = ctk.CTkLabel(
            self.cabecera, text="", font=tema.cuerpo(13), text_color="white"
        )
        self.etiqueta_fecha.pack(side="right", padx=12)

        self.sprite = ctk.CTkLabel(self, text="", fg_color=tema.SECONDARY,
                                   corner_radius=18, width=180, height=180)
        self.sprite.pack(pady=(10, 0), padx=10, anchor="center")
        self.etiqueta_animo = ctk.CTkLabel(
            self, text="NANCY", font=tema.headline(18), text_color=tema.PRIMARY
        )
        self.etiqueta_animo.pack()

        self.contenido = ctk.CTkScrollableFrame(
            self, fg_color=tema.NEUTRAL, corner_radius=0
        )
        self.contenido.pack(fill="both", expand=True, padx=12, pady=8)

        self.entrada = ctk.CTkEntry(
            self, placeholder_text="Escribe lo que quieres decir…",
            font=tema.cuerpo(14), fg_color="white", border_color=tema.BORDE,
        )
        self.entrada.pack(fill="x", padx=12, pady=(0, 6))
        self.entrada.bind("<Return>", lambda _e: self.enviar_entrada())

        botones = ctk.CTkFrame(self, fg_color=tema.NEUTRAL)
        botones.pack(fill="x", padx=12, pady=(0, 12))
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
                botones, text=texto, command=accion, font=tema.cuerpo(13),
                fg_color=color, text_color=tema.TEXTO if color != tema.PRIMARY else "white",
                corner_radius=12, width=130,
            ).grid(row=indice // 3, column=indice % 3, padx=4, pady=4)

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
            self.contenido, fg_color=color or tema.SECONDARY, corner_radius=16
        )
        ctk.CTkLabel(
            tarjeta, text=str(titulo), font=tema.headline(15),
            text_color=tema.PRIMARY, wraplength=380, justify="left",
        ).pack(anchor="w", padx=12, pady=(10, 0))
        ctk.CTkLabel(
            tarjeta, text=str(cuerpo), font=tema.cuerpo(14),
            text_color=tema.TEXTO, wraplength=380, justify="left",
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
        self.etiqueta_animo.configure(text=f"NANCY · {animo}")
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
                str(transaccion.get("tipo", "")).upper(),
                f"{pantallas._dinero(transaccion.get('monto', 0))} "
                f"· {transaccion.get('categoria') or ''} "
                f"· {transaccion.get('cuenta') or ''}".strip(),
                tema.TERTIARY,
            )
        self._tarjeta(
            "NANCY dice", respuesta.get("mensaje_nancy") or "No obtuve respuesta."
        )
        for clave in ("cuentas", "categorias", "pendientes", "movimientos"):
            lista = datos.get(clave)
            if lista:
                lineas = "\n".join(str(item) for item in lista[:5])
                self._tarjeta(clave.capitalize(), lineas, tema.NEUTRAL)
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
        self.mostrar_texto("Te escucho", "Mantén presionada la tecla ESPACIO y habla. Suelta para enviar.")

        def trabajo():
            wav_bytes, duracion, _stats = capture_voice()
            self._grabando = False
            if not wav_bytes:
                self.cola.put(("texto", ("Sin audio", "No se pudo capturar la frase.")))
                return
            self.cola.put(("texto", ("Procesando", "Entendiendo tu mensaje…")))
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
