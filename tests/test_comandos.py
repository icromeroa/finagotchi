"""Prueba de humo de los comandos documentados.

Levanta el backend en un puerto libre, ejecuta el simulador exactamente como
lo documenta la guia y comprueba que todo arranca. Esta prueba existia para
evitar el fallo clasico de prometer un comando que despues no corre.
"""

import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
TIEMPO_MAXIMO = 60


def puerto_libre():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def esperar_salud(url, proceso, timeout=TIEMPO_MAXIMO):
    """Espera a que el backend responda en /api/v1/health.

    ``url`` es la base completa, ya terminada en /api/v1.
    """
    limite = time.time() + timeout
    while time.time() < limite:
        if proceso.poll() is not None:
            return False
        try:
            with urllib.request.urlopen(f"{url}/health", timeout=2) as respuesta:
                if respuesta.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            time.sleep(0.4)
    return False


class ComandosDocumentadosTests(unittest.TestCase):
    """Comprueba que los comandos de la guia funcionan de verdad."""

    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.puerto = puerto_libre()
        cls.base = f"http://127.0.0.1:{cls.puerto}/api/v1"
        entorno = dict(os.environ)
        entorno["FINAGOTCHI_DB"] = str(Path(cls.temp.name) / "humo.db")
        entorno["PORT"] = str(cls.puerto)
        entorno["FINAGOTCHI_BASE_URL"] = cls.base
        cls.entorno = entorno
        cls.proceso = subprocess.Popen(
            [sys.executable, "backend/server.py"],
            cwd=str(RAIZ),
            env=entorno,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        cls.salud = esperar_salud(cls.base, cls.proceso)

    @classmethod
    def tearDownClass(cls):
        if cls.proceso.poll() is None:
            cls.proceso.terminate()
            try:
                cls.proceso.wait(timeout=10)
            except subprocess.TimeoutExpired:
                cls.proceso.kill()
        cls.temp.cleanup()

    def test_el_backend_arranca_en_el_comando_documentado(self):
        self.assertTrue(
            self.salud,
            "El comando 'py -3 backend/server.py' no levanta el backend.",
        )

    def test_el_simulador_arranca_en_el_comando_documentado(self):
        """Ejecuta 'py -3 simulator/main.py' y sale del menu con 'S'."""
        self._comprobar_comando("simulator/main.py")

    def test_el_comando_antiguo_del_simulador_tambien_funciona(self):
        """El atajo 'py -3 simulator/simulator.py' debe seguir sirviendo."""
        self._comprobar_comando("simulator/simulator.py")

    def _comprobar_comando(self, ruta):
        resultado = subprocess.run(
            [sys.executable, ruta],
            cwd=str(RAIZ),
            env=self.entorno,
            input="s\n",
            capture_output=True,
            text=True,
            timeout=TIEMPO_MAXIMO,
        )
        salida = resultado.stdout + resultado.stderr
        self.assertEqual(
            resultado.returncode,
            0,
            f"Falló 'py -3 {ruta}':\n{salida[-3000:]}",
        )
        self.assertNotIn("ImportError", salida)
        self.assertNotIn("Traceback", salida)
        self.assertIn("Dispositivo vinculado", salida)
        self.assertIn("[H] Hablar", salida)

    def test_el_simulador_explica_cuando_el_backend_no_responde(self):
        """Sin backend debe decir que levantarlo, no soltar una excepcion."""
        entorno = dict(self.entorno)
        entorno["FINAGOTCHI_BASE_URL"] = "http://127.0.0.1:5999/api/v1"
        resultado = subprocess.run(
            [sys.executable, "simulator/main.py"],
            cwd=str(RAIZ),
            env=entorno,
            input="s\n",
            capture_output=True,
            text=True,
            timeout=TIEMPO_MAXIMO,
        )
        salida = resultado.stdout + resultado.stderr
        self.assertNotIn("Traceback", salida)
        self.assertIn("No se pudo conectar con el backend", salida)
        self.assertIn("py -3 backend/server.py", salida)

    def test_el_paquete_simulador_se_importa_desde_la_raiz(self):
        resultado = subprocess.run(
            [sys.executable, "-c", "from simulator import pantallas; print('ok')"],
            cwd=str(RAIZ),
            env=self.entorno,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn("ok", resultado.stdout)


if __name__ == "__main__":
    unittest.main()
