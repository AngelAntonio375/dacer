# Tests — DaCer

## Ejecutar todas las pruebas

```bash
# Desde la raíz del repositorio, con el entorno virtual activo
python -m pytest tests/ -v
```

## Suites disponibles

| Archivo            | Qué prueba                                              | Requiere GPU | Requiere cámara |
|--------------------|---------------------------------------------------------|:---:|:---:|
| `test_database.py` | Inicialización de DB, escritura, lectura, filtros, borrado | No | No |
| `test_crypto.py`   | Cifrado/descifrado Fernet, persistencia de clave        | No | No |
| `test_roi.py`      | Lógica de inclusión/exclusión de detecciones por zona   | No | No |

Todas las pruebas son unitarias y corren sin cámara ni GPU. No modifican datos de producción: usan bases de datos y archivos temporales aislados por `pytest` fixtures.

## Correr una suite individual

```bash
python -m pytest tests/test_database.py -v
python -m pytest tests/test_crypto.py -v
python -m pytest tests/test_roi.py -v
```

## Datos de muestra

No se requieren datos externos. Los tests generan internamente frames sintéticos (arrays NumPy de ceros) para probar el pipeline de cifrado y almacenamiento.
