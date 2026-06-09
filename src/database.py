"""
src/database.py
Gestión de la base de datos SQLite de incidentes.
Todas las imágenes se almacenan cifradas con Fernet.
"""
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from src.crypto import cipher_suite

# Raíz del proyecto = carpeta padre de /src
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "incidentes.db"

DATA_DIR.mkdir(exist_ok=True)


def init_db() -> None:
    """Crea la tabla de incidentes si no existe."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS incidentes
           (id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            objeto TEXT,
            imagen_cifrada BLOB)"""
    )
    conn.commit()
    conn.close()


def guardar_incidente(objeto: str, frame_jpg_bytes: bytes) -> bool:
    try:
        img_cifrada = cipher_suite.encrypt(frame_jpg_bytes)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO incidentes (fecha, objeto, imagen_cifrada) VALUES (?, ?, ?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), objeto, img_cifrada),
        )
        conn.commit()
        conn.close()
        return True
    except Exception as exc:
        print(f"[database] Error al guardar incidente: {exc}")
        return False


def obtener_incidentes(filtro: str = "") -> list[tuple]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, fecha, objeto FROM incidentes "
        "WHERE objeto LIKE ? OR fecha LIKE ? ORDER BY id DESC",
        (f"%{filtro}%", f"%{filtro}%"),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def obtener_imagen_incidente(incidente_id: int) -> bytes | None:
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT imagen_cifrada FROM incidentes WHERE id = ?", (incidente_id,)
        )
        res = cursor.fetchone()
        conn.close()
        if res:
            return cipher_suite.decrypt(res[0])
        return None
    except Exception as exc:
        print(f"[database] Error al obtener imagen: {exc}")
        return None


def eliminar_incidente(incidente_id: int) -> bool:
    """Elimina un incidente por ID."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM incidentes WHERE id = ?", (incidente_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as exc:
        print(f"[database] Error al eliminar incidente: {exc}")
        return False


def vaciar_base_de_datos() -> bool:
    """Elimina todos los incidentes de la base de datos."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM incidentes")
        conn.commit()
        conn.close()
        return True
    except Exception as exc:
        print(f"[database] Error al vaciar la base de datos: {exc}")
        return False


def contar_incidentes() -> int:
    """Devuelve el total de incidentes registrados."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM incidentes")
    total = cursor.fetchone()[0]
    conn.close()
    return total


def conteo_por_objeto() -> list[tuple]:
    """Devuelve lista de (objeto, cantidad) ordenada por cantidad descendente."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT objeto, COUNT(*) as n FROM incidentes GROUP BY objeto ORDER BY n DESC"
    )
    rows = cursor.fetchall()
    conn.close()
    return rows