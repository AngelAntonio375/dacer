"""
src/crypto.py
Inicialización y exposición del objeto Fernet para cifrado AES-128.
La clave se persiste en data/secret.key en la raíz del proyecto.
IMPORTANTE: secret.key está excluido del repositorio en .gitignore.
"""

from pathlib import Path
from cryptography.fernet import Fernet

# Raíz del proyecto = carpeta padre de /src
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
KEY_FILE = DATA_DIR / "secret.key"


def _load_or_create_key() -> bytes:
    """Carga la clave existente o genera una nueva si no existe."""
    DATA_DIR.mkdir(exist_ok=True)

    if not KEY_FILE.exists():
        key = Fernet.generate_key()
        KEY_FILE.write_bytes(key)
    else:
        key = KEY_FILE.read_bytes()
    return key


# Instancia global reutilizada en todo el sistema
cipher_suite = Fernet(_load_or_create_key())