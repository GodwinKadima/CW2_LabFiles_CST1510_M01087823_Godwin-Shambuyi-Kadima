from pathlib import Path
import re
import bcrypt

USER_DATA = Path('user.txt')

def hash_password(plain_text_password):
	# Encode the password to bytes, required by bcrypt
    password_bytes = plain_text_password.encode('utf-8')
	# Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
	# Decode the hash back to a string to store in a text file
    return hashed_password