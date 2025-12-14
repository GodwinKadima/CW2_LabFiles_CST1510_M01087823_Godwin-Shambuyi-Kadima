import bcrypt
import re

class AuthManager:
    def __init__(self, db_manager):
        self.db = db_manager

    def hash_password(self, password):
        """Hashes the password using bcrypt."""
        # bcrypt requires the password to be bytes
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        return hashed.decode('utf-8')

    def check_password(self, password, password_hash):
        """Checks if the provided password matches the hash."""
        # bcrypt requires both password and hash to be bytes
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

    def validate_username(self, username):
        """Validates username format and length."""
        if not (3 <= len(username) <= 20):
            return False, "Username must be between 3 and 20 characters."
        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            return False, "Username must contain only letters, numbers, and underscores."
        return True, "Username is valid."
        
    def validate_password(self, password):
        """Validates password strength."""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long."
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter."
        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter."
        if not re.search(r"\d", password):
            return False, "Password must contain at least one digit."
        return True, "Password is valid."

    def register_user(self, username, password):
        """Registers a new user."""
        hashed_password = self.hash_password(password)
        # db.insert_user returns False if the username already exists
        return self.db.insert_user(username, hashed_password)

    def login(self, username, password):
        """Authenticates a user."""
        user = self.db.get_user(username)
        
        if user is None:
            # User not found
            return False
            
        # Check the provided password against the stored hash
        if self.check_password(password, user['password_hash']):
            return True
        else:
            # Incorrect password
            return False