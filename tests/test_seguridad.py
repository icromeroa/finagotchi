"""Pruebas de seguridad del repositorio.

Impiden que una API key real termine versionada por descuido.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAIZ = Path(__file__).resolve().parent

PATRON_KEY_GOOGLE = re.compile(r"(?:AIza|AQ\.Ab)[0-9A-Za-z\-_]{20,}")
PATRON_KEY_ENTORNO = re.compile(
    r"^\s*(GEMINI_API_KEY|FINAGOTCHI_SECRET)\s*=\s*(\S+)\s*$", re.MULTILINE
)

CARPETAS_EXCLUIDAS = {
    ".git",
    "node_modules",
    "__pycache__",
    "audio",
    "backups",
    ".dart_tool",
    "build",
}


def archivos_textuales():
    for ruta in ROOT.rglob("*"):
        if not ruta.is_file():
            continue
        if any(parte in CARPETAS_EXCLUIDAS for parte in ruta.parts):
            continue
        if ruta.suffix.lower() in {".wav", ".mp3", ".png", ".jpg", ".ico", ".zip", ".db"}:
            continue
        if "finagotchi.db" in ruta.name:
            continue
        yield ruta


class SeguridadRepoTests(unittest.TestCase):
    def test_no_hay_api_keys_de_google_en_el_repo(self):
        ofensores = []
        for ruta in archivos_textuales():
            try:
                contenido = ruta.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if PATRON_KEY_GOOGLE.search(contenido):
                ofensores.append(str(ruta.relative_to(ROOT)))
        self.assertEqual(
            ofensores,
            [],
            "Hay una API key de Google en: "
            + ", ".join(ofensores)
            + ". Quitala de inmediato y rota la clave en Google AI Studio.",
        )

    def test_la_clave_externa_no_esta_en_el_repo(self):
        """La clave real debe vivir en %USERPROFILE%/.finagotchi/gemini.env."""
        from backend import ai

        externo = ai.ARCHIVO_EXTERNO
        if not externo.exists():
            self.skipTest("Todavia no se ha configurado la clave externa")

        clave = ""
        for linea in externo.read_text(encoding="utf-8-sig").splitlines():
            if linea.strip().startswith("GEMINI_API_KEY="):
                clave = linea.split("=", 1)[1].strip()
        if not clave:
            self.skipTest("El archivo externo no tiene clave")
        self.assertGreater(len(clave), 20, "La clave externa parece incompleta")

        for ruta in archivos_textuales():
            try:
                contenido = ruta.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            self.assertNotIn(
                clave,
                contenido,
                f"La clave de {externo} tambien aparece en {ruta}",
            )

    def test_env_example_no_tiene_valores_reales(self):
        ejemplo = ROOT / "backend" / ".env.example"
        self.assertTrue(ejemplo.exists(), "Falta backend/.env.example")
        contenido = ejemplo.read_text(encoding="utf-8")
        for variable in ("GEMINI_API_KEY", "FINAGOTCHI_SECRET"):
            for linea in contenido.splitlines():
                if linea.strip().startswith(variable + "="):
                    valor = linea.split("=", 1)[1].strip()
                    self.assertIn(
                        valor,
                        ("", "cambia-esto-en-produccion"),
                        f"{variable} en .env.example no debe traer un valor real",
                    )

    def test_gitignore_cubre_los_env(self):
        gitignore = ROOT / ".gitignore"
        self.assertTrue(gitignore.exists(), "Falta el .gitignore de la raiz")
        contenido = gitignore.read_text(encoding="utf-8")
        self.assertIn(".env", contenido)
        self.assertIn("backend/.env", contenido)

    def test_el_archivo_externo_esta_fuera_del_repo(self):
        from backend import ai

        self.assertFalse(
            str(ai.ARCHIVO_EXTERNO).lower().startswith(str(ROOT).lower()),
            "El archivo externo de la API key debe vivir fuera del repositorio",
        )
        self.assertEqual(ai.ARCHIVO_EXTERNO.name, "gemini.env")

    def test_rutas_de_configuracion_en_orden(self):
        from backend import ai

        rutas = ai.rutas_env()
        self.assertEqual(len(rutas), 3)
        self.assertEqual(rutas[0], ROOT / "backend" / ".env")
        self.assertEqual(rutas[1], ROOT / ".env")
        self.assertEqual(rutas[-1], ai.ARCHIVO_EXTERNO)


if __name__ == "__main__":
    unittest.main()
