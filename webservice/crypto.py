# crypto.py
import hashlib
import secrets

def hash_password(password: str) -> str:
    """Generiert einen SHA-256 Hash des gegebenen Passworts."""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_new_token(length: int = 32) -> str:
    """Generiert einen neuen sicheren Token."""
    return secrets.token_hex(length)  # Erzeugt einen sicheren Token

def substitute_string_reverse(s: str, alphabet: str, key: str) -> str:
    reverse_map = {k: a for a, k in zip(alphabet, key)}
    return "".join(reverse_map.get(ch.upper(), ch) for ch in s)