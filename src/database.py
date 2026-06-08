"""
src/database.py
Gestión de la base de datos SQLite de incidentes.
Todas las imágenes se almacenan cifradas con Fernet.
"""

import sqlite3
from datetime import datetime
from src.crypto import cipher_suite

DB_PATH = "incidentes.db"


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
    """
    Cifra el frame JPG y lo persiste en la base de datos.

    Args:
        objeto: Nombre del objeto detectado (ej. "Cuchillo").
        frame_jpg_bytes: Bytes del frame codificado como JPEG.

    Returns:
        True si el guardado fue exitoso, False en caso de error.
    """
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
    """
    Devuelve incidentes filtrados por objeto o fecha.

    Args:
        filtro: Cadena de búsqueda (vacía = todos).

    Returns:
        Lista de tuplas (id, fecha, objeto).
    """
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
    """
    Devuelve la imagen descifrada de un incidente, o None si no existe.

    Args:
        incidente_id: ID del incidente en la base de datos.

    Returns:
        Bytes de la imagen JPEG descifrada, o None.
    """
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


def eliminar_incidente(incidente_id: int) -> None:
    """Elimina un incidente por ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM incidentes WHERE id = ?", (incidente_id,))
    conn.commit()
    conn.close()


def vaciar_base_de_datos() -> None:
    """Elimina todos los incidentes de la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM incidentes")
    conn.commit()
    conn.close()


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
