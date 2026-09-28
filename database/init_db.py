import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "finagotchi.db")


def init_sqlite(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Tabla de transacciones
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS transacciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE,
            device_id TEXT,
            timestamp TEXT,
            transaction_type TEXT,
            amount REAL,
            category TEXT,
            raw_text TEXT,
            cerrado INTEGER DEFAULT 0
        )
    """
    )

    # Migración: Verificar si la columna 'cerrado' existe
    cursor.execute("PRAGMA table_info(transacciones)")
    columnas = [columna[1] for columna in cursor.fetchall()]
    if "cerrado" not in columnas:
        cursor.execute(
            "ALTER TABLE transacciones ADD COLUMN cerrado INTEGER DEFAULT 0"
        )

    # Tabla del Estado de la Mascota
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS estado_mascota (
            id INTEGER PRIMARY KEY,
            salud INTEGER,
            animo TEXT
        )
    """
    )
    cursor.execute("SELECT COUNT(*) FROM estado_mascota")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO estado_mascota (id, salud, animo) VALUES (1, 100, 'FELIZ')"
        )

    # NUEVA TABLA: Presupuestos por Categoría
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS presupuestos_categoria (
            categoria TEXT PRIMARY KEY,
            monto_limite REAL
        )
    """
    )

    # Asignación de Presupuestos Iniciales por Defecto (COP)
    presupuestos_iniciales = [
        ("food", 25000.0),  # Alimentos / Comida
        ("transport", 15000.0),  # Transporte / Bus / Pasajes
        ("entertainment", 20000.0),  # Entretenimiento / Salidas
        ("health", 15000.0),  # Salud / Droguería
        ("housing", 30000.0),  # Vivienda / Servicios
        ("other", 10000.0),  # Otros gastos
    ]

    for cat, limite in presupuestos_iniciales:
        cursor.execute(
            "INSERT OR IGNORE INTO presupuestos_categoria (categoria, monto_limite) VALUES (?, ?)",
            (cat, limite),
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_sqlite()