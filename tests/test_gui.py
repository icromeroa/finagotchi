"""Pruebas de la GUI del simulador (Fase 24), sin red ni micrófono.

Las pruebas de ventana se omiten si no hay pantalla disponible; las de
tema y sprites corren siempre.
"""

import os
import tempfile
import unittest
from pathlib import Path

from simulator.gui import sprites, tema


class TemaTests(unittest.TestCase):
    def test_paleta_del_mockup(self):
        self.assertEqual(tema.PRIMARY, "#832D52")
        self.assertEqual(tema.SECONDARY, "#F0AFC5")
        self.assertEqual(tema.TERTIARY, "#B2CE45")
        self.assertEqual(tema.NEUTRAL, "#F6E5D1")

    def test_fuentes_con_fallback(self):
        self.assertTrue(tema.headline(20))
        self.assertTrue(tema.cuerpo(14))


class SpritesTests(unittest.TestCase):
    def _con_carpetas(self, carpeta):
        original = sprites.SPRITES
        gifs_original = sprites.GIFS
        sprites.SPRITES = Path(carpeta)
        sprites.GIFS = Path(carpeta) / "vacio"
        sprites.GIFS.mkdir(exist_ok=True)
        return original, gifs_original

    def test_sin_archivo_hay_placeholder(self):
        with tempfile.TemporaryDirectory() as carpeta:
            original, gifs_original = self._con_carpetas(carpeta)
            try:
                frames, _duracion = sprites.cargar_frames("feliz")
            finally:
                sprites.SPRITES = original
                sprites.GIFS = gifs_original
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0].size, (sprites.ANCHO_SPRITE,) * 2)

    def test_png_se_anima_como_un_frame(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as carpeta:
            original, gifs_original = self._con_carpetas(carpeta)
            ruta = sprites.SPRITES / "nancy_feliz.png"
            Image.new("RGB", (40, 40), (240, 175, 197)).save(ruta)
            try:
                frames, _duracion = sprites.cargar_frames("feliz")
            finally:
                sprites.SPRITES = original
                sprites.GIFS = gifs_original
        self.assertEqual(len(frames), 1)

    def test_alias_preocupada_equivale_a_preocupado(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as carpeta:
            original = sprites.SPRITES
            gifs_original = sprites.GIFS
            sprites.SPRITES = Path(carpeta)
            sprites.GIFS = Path(carpeta) / "vacio"
            (sprites.SPRITES / "nancy_preocupada.png").parent.mkdir(exist_ok=True)
            Image.new("RGB", (40, 40), (240, 175, 197)).save(
                sprites.SPRITES / "nancy_preocupada.png"
            )
            try:
                frames, _duracion = sprites.cargar_frames("preocupado", tamano=40)
            finally:
                sprites.SPRITES = original
                sprites.GIFS = gifs_original
        self.assertEqual(len(frames), 1)

    def test_fondo_negro_se_vuelve_transparente(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as carpeta:
            original, gifs_original = self._con_carpetas(carpeta)
            ruta = sprites.SPRITES / "nancy_feliz.png"
            imagen = Image.new("RGB", (40, 40), (0, 0, 0))
            for x in range(10, 30):
                for y in range(10, 30):
                    imagen.putpixel((x, y), (240, 175, 197))
            imagen.save(ruta)
            try:
                frames, _duracion = sprites.cargar_frames("feliz", tamano=40)
            finally:
                sprites.SPRITES = original
                sprites.GIFS = gifs_original
        # La esquina era fondo negro: ahora es la tarjeta rosa.
        self.assertEqual(frames[0].getpixel((0, 0)), (240, 175, 197))

    def test_diptico_vertical_deja_una_sola_cerdita(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as carpeta:
            original, gifs_original = self._con_carpetas(carpeta)
            ruta = sprites.SPRITES / "nancy_escuchando.gif"
            arriba = Image.new("RGB", (60, 60), (0, 0, 0))
            abajo = Image.new("RGB", (60, 60), (255, 255, 255))
            abajo = Image.new("RGB", (60, 60), (255, 255, 255))
            lienzo = Image.new("RGB", (60, 120), (255, 255, 255))
            lienzo.paste(arriba, (0, 0))
            lienzo.paste(abajo, (0, 60))
            lienzo.save(ruta, save_all=True, append_images=[lienzo.copy()], duration=100, loop=0)
            try:
                frames, _duracion = sprites.cargar_frames("escuchando", tamano=60)
            finally:
                sprites.SPRITES = original
                sprites.GIFS = gifs_original
        # Solo queda la mitad clara (ya sin negro) como una sola imagen.
        self.assertEqual(frames[0].getpixel((0, 0)), (240, 175, 197))

    def test_ventana_es_compacta(self):
        self.assertLessEqual(tema.TAMANO_VENTANA[0], 400)
        self.assertLessEqual(tema.TAMANO_VENTANA[1], 650)

    def test_gif_se_descompone_en_frames(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as carpeta:
            original, gifs_original = self._con_carpetas(carpeta)
            ruta = sprites.SPRITES / "nancy_escuchando.gif"
            imagen = Image.new("RGB", (40, 40), (240, 175, 197))
            imagen.save(ruta, save_all=True, append_images=[imagen.copy()], duration=100, loop=0)
            try:
                frames, duracion = sprites.cargar_frames("escuchando")
            finally:
                sprites.SPRITES = original
                sprites.GIFS = gifs_original
        self.assertGreaterEqual(len(frames), 1)
        self.assertGreater(duracion, 0)


@unittest.skipIf(os.environ.get("CI"), "Sin pantalla en CI")
class NavegacionTests(unittest.TestCase):
    def test_la_ventana_se_construye_y_pinta_reposo(self):
        from simulator.gui.app import App

        try:
            app = App(arranque=False)
        except Exception as exc:  # noqa: BLE001 - sin display no se puede
            self.skipTest(f"Sin pantalla: {exc}")
        try:
            app.mostrar_reposo(
                {
                    "hoy": {"gastos": 20000, "ingresos": 800000,
                            "cupo_restante": 10000, "presupuesto_diario": 30000},
                    "mascota": {"animo": "FELIZ", "salud": 92},
                    "puntos": 3,
                }
            )
            self.assertTrue(app.contenido.winfo_children())
            self.assertEqual(app.etiqueta_animo.cget("text"), "Nancy · Feliz")
            app.update()
            self.assertEqual(app.geometry().split("+")[0], "380x620")
        finally:
            app.destroy()


if __name__ == "__main__":
    unittest.main()
