"""
tests/test_database.py
Pruebas para el módulo src/database.py
Usa una base de datos temporal que se elimina al finalizar.
"""

import os
import pytest
import sqlite3
import tempfile
import numpy as np
import cv2

# Redirigir DB_PATH a un archivo temporal antes de importar el módulo
import src.database as db_module

@pytest.fixture(autouse=True)
def db_temporal(tmp_path, monkeypatch):
    """Usa una DB temporal por cada test."""
    db_path = str(tmp_path / "test_incidentes.db")
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    db_module.init_db()
    yield db_path


def _frame_de_prueba() -> bytes:
    """Genera un frame negro de 64x64 y lo codifica como JPEG."""
    frame = np.zeros((64, 64, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", frame)
    return buf.tobytes()


class TestInitDb:
    def test_crea_tabla_incidentes(self, db_temporal):
        conn = sqlite3.connect(db_temporal)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='incidentes'")
        assert cursor.fetchone() is not None
        conn.close()


class TestGuardarIncidente:
    def test_guarda_correctamente(self, db_temporal):
        frame_bytes = _frame_de_prueba()
        result = db_module.guardar_incidente("Cuchillo", frame_bytes)
        assert result is True

    def test_incrementa_contador(self, db_temporal):
        frame_bytes = _frame_de_prueba()
        db_module.guardar_incidente("Tijeras", frame_bytes)
        db_module.guardar_incidente("Cuchillo", frame_bytes)
        assert db_module.contar_incidentes() == 2


class TestObtenerIncidentes:
    def test_devuelve_lista(self, db_temporal):
        frame_bytes = _frame_de_prueba()
        db_module.guardar_incidente("Persona", frame_bytes)
        rows = db_module.obtener_incidentes()
        assert len(rows) == 1
        assert rows[0][2] == "Persona"

    def test_filtra_por_objeto(self, db_temporal):
        frame_bytes = _frame_de_prueba()
        db_module.guardar_incidente("Cuchillo", frame_bytes)
        db_module.guardar_incidente("Celular", frame_bytes)
        rows = db_module.obtener_incidentes("Cuchillo")
        assert len(rows) == 1


class TestEliminar:
    def test_elimina_individual(self, db_temporal):
        frame_bytes = _frame_de_prueba()
        db_module.guardar_incidente("Botella", frame_bytes)
        rows = db_module.obtener_incidentes()
        db_module.eliminar_incidente(rows[0][0])
        assert db_module.contar_incidentes() == 0

    def test_vaciar_base_de_datos(self, db_temporal):
        frame_bytes = _frame_de_prueba()
        db_module.guardar_incidente("Cuchillo", frame_bytes)
        db_module.guardar_incidente("Tijeras", frame_bytes)
        db_module.vaciar_base_de_datos()
        assert db_module.contar_incidentes() == 0
