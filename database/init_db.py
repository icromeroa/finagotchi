import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "finagotchi.db"
SQL_DIR = Path(__file__).resolve().parent / "sql"
SCHEMA_VERSION = 3
SCHEMA_FILES = ("001_schema.sql", "002_views.sql", "003_seed.sql")


def connect(db_path=DB_PATH):
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def table_names(conn):
    return {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }


def view_names(conn):
    return [
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'view' ORDER BY name"
        )
    ]


def is_legacy_database(conn):
    tables = table_names(conn)
    return (
        "transacciones" in tables
        and "usuarios" not in tables
        and "schema_migrations" not in tables
    )


def schema_version(conn):
    if "schema_migrations" not in table_names(conn):
        return None
    row = conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()
    return row[0] if row else None


def apply_sql_file(conn, filename):
    path = SQL_DIR / filename
    conn.executescript(path.read_text(encoding="utf-8"))


def apply_schema(conn):
    for filename in SCHEMA_FILES:
        apply_sql_file(conn, filename)


def drop_views(conn):
    for name in view_names(conn):
        escaped = name.replace('"', '""')
        conn.execute(f'DROP VIEW IF EXISTS "{escaped}"')


def refresh_views(db_path=DB_PATH):
    conn = connect(db_path)
    try:
        drop_views(conn)
        apply_sql_file(conn, "002_views.sql")
        conn.commit()
    finally:
        conn.close()
    return db_path


def init_sqlite(db_path=DB_PATH):
    db_path = Path(db_path) if str(db_path) != ":memory:" else db_path
    version = None
    exists = isinstance(db_path, Path) and db_path.exists() and db_path.stat().st_size > 0

    if exists:
        check = connect(db_path)
        try:
            if is_legacy_database(check):
                raise RuntimeError(
                    "La base de datos es legacy y no se migra en esta version. "
                    "Elimina finagotchi.db y ejecuta: py -3 database/init_db.py"
                )
            version = schema_version(check)
        finally:
            check.close()

    if isinstance(db_path, Path):
        db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = connect(db_path)
    try:
        if version is None:
            apply_schema(conn)
        elif version < SCHEMA_VERSION:
            apply_schema(conn)
        elif version > SCHEMA_VERSION:
            raise RuntimeError(
                f"La base de datos usa el esquema {version}, "
                f"pero este codigo solo soporta {SCHEMA_VERSION}"
            )
        conn.commit()
    finally:
        conn.close()

    return db_path


if __name__ == "__main__":
    print(init_sqlite())
