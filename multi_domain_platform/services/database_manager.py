import sqlite3

class DatabaseManager:
    def __init__(self, db_name):
        self.db_name = db_name
        # This method is called when DatabaseManager is instantiated, ensuring all tables exist.
        self._create_table() 

    # --- Core Connection Helper ---
    def _get_connection(self):
        """Returns a new SQLite connection."""
        return sqlite3.connect(self.db_name)

    # --- Read Operations (Used by all dashboards) ---
    def fetch_all(self, query, params=()):
        """Fetches all rows from a query and returns them as a list of dicts."""
        conn = self._get_connection()
        try:
            cursor = conn.execute(query, params)
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        finally:
            conn.close()

    # --- Write/Modify Operations (Used by all CRUD forms) ---
    def execute_query(self, query, params=()):
        """Executes an INSERT, UPDATE, or DELETE query."""
        conn = self._get_connection()
        try:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount, cursor.lastrowid # Return rowcount and last row ID
        except Exception as e:
            print(f"Database error during execution: {e}")
            return 0, None
        finally:
            conn.close()

    # --- Authentication Methods (Required by Home.py) ---
    def insert_user(self, username, password_hash):
        """Inserts a new user into the database."""
        conn = self._get_connection()
        try:
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                (username, password_hash)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_user(self, username):
        """Retrieves a user's data by username."""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT username, password_hash FROM users WHERE username = ?", 
                (username,)
            )
            user_data = cursor.fetchone()
            if user_data:
                return {'username': user_data[0], 'password_hash': user_data[1]}
            return None
        finally:
            conn.close()
            
    # --- Table Creation (FIXED AND CONSOLIDATED) ---
    def _create_table(self):
        """Creates all necessary tables if they do not exist."""
        conn = self._get_connection()
        try:
            # 1. Users table (for Home.py login)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL
                );
            ''')
            # 2. Security Incidents table (for _🛡️ _Cybersecurity.py)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS security_incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    status TEXT NOT NULL,
                    description TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            # 3. IT Tickets table (for _💻 _IT_Operations.py)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS it_tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Open',
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            # 4. ML Experiments table (THE FIX for the current error)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ml_experiments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL,
                    dataset TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Pending',
                    accuracy REAL,
                    run_time_seconds INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            conn.commit()
        finally:
            conn.close()