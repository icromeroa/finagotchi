"""Atajo de arranque del simulador.

Permite que el comando antigo 'py -3 simulator/simulator.py' siga funcionando.
La entrada real esta en simulator/main.py: si este archivo se llamara igual
que el paquete, al ejecutarlo directamente Python lo cargaria como 'simulator'
y el import del paquete fallaria con ImportError.
"""

import sys
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
RAIZ = CARPETA.parent

# Se quita la carpeta del script del camino de busqueda para que el nombre
# 'simulator' resuelva al paquete y no a este archivo.
sys.path = [ruta for ruta in sys.path if Path(ruta or ".").resolve() != CARPETA]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from simulator.main import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
