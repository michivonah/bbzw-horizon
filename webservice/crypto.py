# crypto.py
import hashlib
import secrets

def hash_password(password: str) -> str:
    """Generiert einen SHA-256 Hash des gegebenen Passworts."""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_new_token(length: int = 32) -> str:
    """Generiert einen neuen sicheren Token."""
    return secrets.token_hex(length)  # Erzeugt einen sicheren Token