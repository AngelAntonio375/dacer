# Esquema de base de datos — DaCer

Base de datos SQLite local. Archivo: `data/incidents.db`

---

## Tabla: `incidents`

Almacena cada incidente confirmado por el sistema.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | Identificador único del incidente |
| `timestamp` | TEXT NOT NULL | Fecha y hora del incidente (ISO 8601, hora local) |
| `object_class` | TEXT NOT NULL | Clase del objeto detectado (ej: `knife`, `person`) |
| `confidence` | REAL NOT NULL | Confianza de la detección en el frame de confirmación (0.0–1.0) |
| `image_blob` | BLOB NOT NULL | Imagen del frame cifrada con Fernet (AES-128) |
| `roi_active` | INTEGER NOT NULL | 1 si había ROI activa al momento del incidente, 0 si no |

---

## Sentencia de creación

```sql
CREATE TABLE IF NOT EXISTS incidents (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp    TEXT    NOT NULL,
    object_class TEXT    NOT NULL,
    confidence   REAL    NOT NULL,
    image_blob   BLOB    NOT NULL,
    roi_active   INTEGER NOT NULL DEFAULT 0
);
```

---

## Notas

- La clave Fernet se almacena en `data/.key` (excluido del repo con `.gitignore`).
- `image_blob` contiene el frame completo anotado (bounding box visible), no solo el recorte del objeto.
- `timestamp` usa el formato `YYYY-MM-DD HH:MM:SS` para facilitar filtros de búsqueda con `LIKE` y `BETWEEN`.
- No hay tabla de usuarios: el sistema no implementa autenticación en esta versión (limitación conocida documentada en la ficha técnica).
