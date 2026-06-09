"""
tests/test_crypto.py
Pruebas para el módulo src/crypto.py
Verifica que el cifrado y descifrado sean correctos y que la clave persiste.
"""

import pytest
from pathlib import Path
from cryptography.fernet import Fernet


class TestCifradoFernet:
    def test_cifrado_descifrado_roundtrip(self):
        """El mensaje descifrado debe ser idéntico al original."""
        from src.crypto import cipher_suite
        mensaje = b"imagen_de_prueba_12345"
        cifrado = cipher_suite.encrypt(mensaje)
        assert cipher_suite.decrypt(cifrado) == mensaje

    def test_cifrado_no_es_texto_plano(self):
        """El mensaje cifrado no debe contener el texto original en claro."""
        from src.crypto import cipher_suite
        mensaje = b"secreto_visible"
        cifrado = cipher_suite.encrypt(mensaje)
        assert b"secreto_visible" not in cifrado

    def test_key_file_se_crea(self, tmp_path, monkeypatch):
        """Si no existe secret.key, debe crearse automáticamente."""
        import src.crypto as crypto_module
        key_path = tmp_path / "test.key"
        monkeypatch.setattr(crypto_module, "DATA_DIR", tmp_path)
        monkeypatch.setattr(crypto_module, "KEY_FILE", key_path)
        key = crypto_module._load_or_create_key()
        assert key_path.exists()
        assert len(key) > 0

    def test_key_file_se_reutiliza(self, tmp_path, monkeypatch):
        """La misma clave debe usarse si el archivo ya existe."""
        import src.crypto as crypto_module
        key_path = tmp_path / "test2.key"
        monkeypatch.setattr(crypto_module, "DATA_DIR", tmp_path)
        monkeypatch.setattr(crypto_module, "KEY_FILE", key_path)
        key1 = crypto_module._load_or_create_key()
        key2 = crypto_module._load_or_create_key()
        assert key1 == key2