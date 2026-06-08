"""
src/crypto.py
Inicialización y exposición del objeto Fernet para cifrado AES-128.
La clave se persiste en secret.key en el directorio de trabajo.
IMPORTANTE: secret.key está excluido del repositorio en .gitignore.
"""

import os
from cryptography.fernet import Fernet

KEY_FILE = "secret.key"


def _load_or_create_key() -> bytes:
    """Carga la clave existente o genera una nueva si no existe."""
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    else:
        with open(KEY_FILE, "rb") as f:
            key = f.read()
    return key


# Instancia global reutilizada en todo el sistema
cipher_suite = Fernet(_load_or_create_key())
