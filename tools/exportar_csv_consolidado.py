"""Exporta todo el dataset a un unico CSV en formato largo.

Cada fila del CSV representa un campo de un registro:

    tabla;id_registro;usuario_id;fecha;columna_fecha;campo;valor

Incluye las 40 tablas de ``finagotchi.db`` y, por defecto, tambien las
celdas ``NULL`` (con ``valor`` vacio). El archivo usa UTF-8 con BOM y
separador ``;`` para que Excel lo abra bien en configuracion regional
en espanol.
"""

import argparse
import csv
import hashlib
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "finagotchi.db"
SALIDA = ROOT / "datasets" / "dataset_bd" / "consolidado"
ARCHIVO = "dataset_completo.csv"
COLUMNAS = (
    "tabla",
    "id_registro",
    "usuario_id",
    "fecha",
    "columna_fecha",
    "campo",
    "valor",
)

# Orden de preferencia para elegir la fecha representativa de cada fila.
# La columna elegida se publica en ``columna_fecha`` para que sea trazable.
PRIORIDAD_FECHAS = (
    "fecha_local",
    "fecha_hora",
    "solicitada_en",
    "respondido_en",
    "aplicado_en",
    "aceptado_en",
    "recibido_en",
    "creado_en",
    "cambiado_en",
    "otorgado_en",
    "cerrado_en",
    "vinculado_en",
    "ultima_actualizacion",
    "actualizado_en",
    "ultima_conexion",
)

# Claves naturales para tablas que no tienen columna ``id``.
CLAVES_NATURALES = {
    "estado_mascota": ("usuario_id",),
    "perfil_financiero": ("usuario_id",),
    "preferencias_notificacion": ("usuario_id",),
    "progreso_etapa": ("usuario_id",),
    "perfil_secciones": ("usuario_id", "seccion"),
    "schema_migrations": ("version",),
    "plantilla_categoria_palabras": ("tipo", "categoria_nombre", "palabra"),
    "plantilla_cuenta_palabras": ("cuenta_nombre", "palabra"),
}


def _tablas(conn) -> list[str]:
    return [
        fila[0]
        for fila in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]


def _columnas(conn, tabla: str) -> list[str]:
    return [
        fila[1]
        for fila in conn.execute(f"PRAGMA table_xinfo('{tabla}')")
        if fila[6] != 1  # descarta columnas ocultas de tablas virtuales
    ]


def _clave(tabla: str, columnas: list[str], fila) -> str:
    if "id" in columnas:
        return str(fila["id"])
    partes = CLAVES_NATURALES.get(tabla)
    if partes and all(parte in columnas for parte in partes):
        return ":".join(str(fila[parte]) for parte in partes)
    return str(fila["__rowid"])


def _usuario(tabla: str, columnas: list[str], fila) -> str:
    if tabla == "usuarios":
        return str(fila["id"])
    if "usuario_id" in columnas and fila["usuario_id"] is not None:
        return str(fila["usuario_id"])
    if tabla == "vinculacion_codigos" and fila["usado_por_usuario_id"] is not None:
        return str(fila["usado_por_usuario_id"])
    return ""


def _columna_fecha(columnas: list[str]) -> str:
    for candidata in PRIORIDAD_FECHAS:
        if candidata in columnas:
            return candidata
    return ""


def _texto(valor) -> str:
    if valor is None:
        return ""
    if isinstance(valor, bytes):
        return valor.hex()
    return str(valor)


def exportar_consolidado(
    db_path=DB_PATH,
    *,
    salida=None,
    separador=";",
    bom=True,
    incluir_vacios=True,
) -> dict:
    """Escribe ``dataset_completo.csv`` y su manifest. Devuelve el manifest."""
    if not separador:
        raise ValueError("El separador no puede estar vacio")

    db_path = Path(db_path)
    salida = Path(salida) if salida else SALIDA
    salida.mkdir(parents=True, exist_ok=True)
    ruta = salida / ARCHIVO

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    tablas = _tablas(conn)
    if not tablas:
        conn.close()
        raise RuntimeError(f"La base {db_path} no tiene tablas")

    detalle = {}
    total_filas = 0
    codificacion = "utf-8-sig" if bom else "utf-8"
    try:
        with ruta.open("w", encoding=codificacion, newline="") as archivo:
            escritor = csv.writer(
                archivo, delimiter=separador, lineterminator="\r\n"
            )
            escritor.writerow(COLUMNAS)

            for tabla in tablas:
                columnas = _columnas(conn, tabla)
                columna_fecha = _columna_fecha(columnas)
                clave_usada = "id" if "id" in columnas else (
                    CLAVES_NATURALES.get(tabla, ("rowid",))
                )
                filas = 0
                cursor = conn.execute(f'SELECT rowid AS __rowid, * FROM "{tabla}"')
                for fila in cursor:
                    id_registro = _clave(tabla, columnas, fila)
                    usuario_id = _usuario(tabla, columnas, fila)
                    fecha = _texto(fila[columna_fecha]) if columna_fecha else ""
                    for campo in columnas:
                        valor = fila[campo]
                        if valor is None and not incluir_vacios:
                            continue
                        escritor.writerow(
                            (
                                tabla,
                                id_registro,
                                usuario_id,
                                fecha,
                                columna_fecha,
                                campo,
                                _texto(valor),
                            )
                        )
                        total_filas += 1
                    filas += 1
                detalle[tabla] = {
                    "filas": filas,
                    "columnas": len(columnas),
                    "clave": list(clave_usada)
                    if isinstance(clave_usada, tuple) else [clave_usada],
                    "columna_fecha": columna_fecha or None,
                }
    finally:
        conn.close()

    contenido = ruta.read_bytes()
    manifest = {
        "generado_en": datetime.now().isoformat(timespec="seconds"),
        "fuente": db_path.name,
        "archivo": ARCHIVO,
        "separador": separador,
        "codificacion": "UTF-8 con BOM" if bom else "UTF-8 sin BOM",
        "incluye_vacios": bool(incluir_vacios),
        "columnas": list(COLUMNAS),
        "total_tablas": len(tablas),
        "total_filas": total_filas,
        "bytes": len(contenido),
        "sha256": hashlib.sha256(contenido).hexdigest(),
        "tablas": detalle,
    }
    (salida / "manifest_consolidado.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Exporta todas las tablas de finagotchi.db a un unico CSV "
            "en formato largo"
        ),
    )
    parser.add_argument("--db", default=str(DB_PATH), help="Base de datos de origen")
    parser.add_argument(
        "--salida", default=None,
        help="Carpeta de salida (por defecto datasets/dataset_bd/consolidado)",
    )
    parser.add_argument(
        "--separador", default=";",
        help="Separador de campos (por defecto ';' para Excel en espanol)",
    )
    parser.add_argument(
        "--sin-bom", action="store_true",
        help="Escribe UTF-8 sin BOM en lugar de UTF-8 con BOM",
    )
    parser.add_argument(
        "--omitir-vacios", action="store_true",
        help="No escribe filas para celdas NULL",
    )
    args = parser.parse_args(argv)

    try:
        manifest = exportar_consolidado(
            args.db,
            salida=args.salida,
            separador=args.separador,
            bom=not args.sin_bom,
            incluir_vacios=not args.omitir_vacios,
        )
    except Exception as exc:  # noqa: BLE001 - se muestra el error al usuario
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    carpeta = Path(args.salida) if args.salida else SALIDA
    print(f"Base:         {Path(args.db).resolve()}")
    print(f"Archivo:      {(carpeta / ARCHIVO).resolve()}")
    print(
        "Contenido:    {total_filas} filas de {total_tablas} tablas "
        "({bytes} bytes)".format(**manifest)
    )
    print(
        "Formato:      separador '{separador}', {codificacion}, "
        "vacios {vacios}".format(
            vacios="incluidos" if manifest["incluye_vacios"] else "omitidos",
            **manifest,
        )
    )
    print(f"SHA-256:      {manifest['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
