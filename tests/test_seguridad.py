"""Pruebas de seguridad del repositorio.

Impiden que secretos reales terminen versionados por descuido.
Ya no hay proveedor externo de transcripcion: el STT es local.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAIZ = Path(__file__).resolve().parent

PATRON_KEY_EXTERNA = re.compile(r"^\s*FINAGOTCHI_SECRET\s*=\s*(\S+)\s*$", re.MULTILINE)

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
    def test_env_example_no_tiene_valores_reales(self):
        ejemplo = ROOT / "backend" / ".env.example"
        self.assertTrue(ejemplo.exists(), "Falta backend/.env.example")
        contenido = ejemplo.read_text(encoding="utf-8")
        for variable in ("FINAGOTCHI_SECRET", "OLLAMA_URL", "OLLAMA_MODEL"):
            for linea in contenido.splitlines():
                if linea.strip().startswith(variable + "="):
                    valor = linea.split("=", 1)[1].strip()
                    self.assertIn(
                        valor,
                        ("", "cambia-esto-en-produccion", "http://127.0.0.1:11434", "qwen3:4b"),
                        f"{variable} en .env.example no debe traer un valor real",
                    )

    def test_gitignore_cubre_los_env(self):
        gitignore = ROOT / ".gitignore"
        self.assertTrue(gitignore.exists(), "Falta el .gitignore de la raiz")
        contenido = gitignore.read_text(encoding="utf-8")
        self.assertIn(".env", contenido)
        self.assertIn("backend/.env", contenido)


if __name__ == "__main__":
    unittest.main()
