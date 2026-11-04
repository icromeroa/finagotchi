"""Prueba que detecta texto doblemente codificado en el repositorio.

Cuando un archivo UTF-8 se lee como Windows-1252 (cp1252) y se vuelve a
guardar como UTF-8, los acentos quedan con la forma "A-circumflex +
copyright" en vez de "e con acento". Es un fallo silencioso: el codigo compila
y las pruebas pasan, pero la pantalla muestra basura.

La deteccion: un fragmento con caracteres no ASCII que, codificado en cp1252 y
decodificado en UTF-8, produce un texto distinto, esta doblemente codificado.
"""

import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
EXTENSIONES = {".dart", ".md", ".py", ".json", ".yaml", ".csv", ".txt"}
EXCLUIDOS = {".git", "node_modules", "build", "__pycache__", ".dart_tool", "backups"}
TAMANO_MAXIMO = 400000


def corregir_fragmento(fragmento):
    try:
        arreglado = fragmento.encode("cp1252").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return fragmento
    return arreglado if arreglado != fragmento else fragmento


def fragmento_mojibake(texto):
    """True si el texto tiene fragmentos doblemente codificados."""
    buffer = ""
    es_no_ascii = False
    for caracter in texto:
        actual = ord(caracter) > 127
        if actual != es_no_ascii:
            if es_no_ascii and buffer:
                if corregir_fragmento(buffer) != buffer:
                    return True
            buffer = ""
            es_no_ascii = actual
        buffer += caracter
    if es_no_ascii and buffer and corregir_fragmento(buffer) != buffer:
        return True
    return False


def archivos_de_texto():
    for ruta in RAIZ.rglob("*"):
        if not ruta.is_file():
            continue
        if any(parte in EXCLUIDOS for parte in ruta.parts):
            continue
        if ruta.suffix.lower() not in EXTENSIONES:
            continue
        try:
            if ruta.stat().st_size > TAMANO_MAXIMO:
                continue
        except OSError:
            continue
        yield ruta


class CodificacionTests(unittest.TestCase):
    def test_ningun_archivo_tiene_texto_doblemente_codificado(self):
        ofenders = []
        for ruta in archivos_de_texto():
            if ruta.name == Path(__file__).name:
                continue
            try:
                contenido = ruta.read_bytes().decode("utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for numero, linea in enumerate(contenido.splitlines(), 1):
                if fragmento_mojibake(linea):
                    ofenders.append(f"{ruta.relative_to(RAIZ)}:{numero}")
                    break
        self.assertEqual(
            ofenders,
            [],
            "Texto doblemente codificado (acentos rotos) en: "
            + ", ".join(ofenders)
            + ". Se corrige re-codificando de cp1252 a UTF-8.",
        )

    def test_los_textos_publicados_se_ven_bien(self):
        """Muestra representativa de los mensajes que devuelve la API."""
        casos = {
            "backend/nlp.py": [
                "No se identificó un monto",
                "No hay una categoría disponible",
            ],
        }
        for relativo, textos in casos.items():
            ruta = RAIZ / relativo
            self.assertTrue(ruta.exists(), f"Falta {relativo}")
            contenido = ruta.read_bytes().decode("utf-8")
            for texto in textos:
                self.assertIn(
                    texto,
                    contenido,
                    f"El texto {texto!r} no aparece bien en {relativo}",
                )
                self.assertNotIn(
                    texto.encode("utf-8").decode("latin-1"),
                    contenido,
                    f"El texto {texto!r} esta doblemente codificado en {relativo}",
                )


if __name__ == "__main__":
    unittest.main()
