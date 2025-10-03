# db/__init__.py

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "fichajes.db"

def conectar():
    """Devuelve una conexión a la base de datos SQLite."""
    return sqlite3.connect(DB_PATH)
