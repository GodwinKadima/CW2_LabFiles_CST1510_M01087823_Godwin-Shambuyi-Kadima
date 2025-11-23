import sqlite3
from pathlib import Path

# Define paths
DATA_DIR = Path("DATA") / "intelligence_platform.db"
DB_PATH = DATA_DIR / "intelligence_platform.db"

def connect_database(db_path=DB_PATH):
     """Connect to SQlite database."""
     return sqlite3.connect(str(db_path))

