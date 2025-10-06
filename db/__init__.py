# db/__init__.py

import sqlite3
from pathlib import Path

# Path to the database file, located in the same directory as this script.
DB_PATH: Path = Path(__file__).parent / "fichajes.db"

def connect_db() -> sqlite3.Connection:
    """Returns a connection object to the SQLite database."""
    return sqlite3.connect(DB_PATH)