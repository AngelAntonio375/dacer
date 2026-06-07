# Pruebas automatizadas — DaCer

## Cómo correr las pruebas

### Todas las pruebas
```bash
python -m pytest tests/ -v
```

### Por módulo
```bash
# Motor de detección
python -m pytest tests/test_detection.py -v

# Base de datos y cifrado
python -m pytest tests/test_database.py -v

# Lógica de alertas y cooldown
python -m pytest tests/test_alerts.py -v
```

### Con reporte de cobertura
```bash
pip install pytest-cov
python -m pytest tests/ --cov=src --cov-report=term-missing
```

---

## Qué prueba cada archivo

### test_detection.py
- El motor de inferencia carga el modelo YOLOv8n correctamente.
- La detección devuelve resultados para un frame de prueba conocido.
- El filtro por ROI descarta detecciones fuera del área definida.
- El umbral de confianza filtra detecciones por debajo del límite configurado.
- Solo las clases activas en config producen detecciones.

### test_database.py
- Un incidente se escribe correctamente en SQLite.
- La imagen se almacena cifrada (el blob en DB no es legible como imagen directa).
- La imagen se descifra correctamente al leerla.
- La consulta de historial devuelve los registros en orden cronológico.
- Los filtros de búsqueda por fecha y tipo de objeto funcionan.

### test_alerts.py
- Una detección en N fotogramas consecutivos genera exactamente una alerta.
- Una detección de menos de N fotogramas no genera alerta.
- El cooldown impide registrar una segunda alerta del mismo objeto antes de 30 segundos.
- Al cambiar las clases activas, el estado de confirmación se reinicia.

---

## Datos de muestra

Los archivos de prueba usan imágenes sintéticas generadas en memoria (numpy arrays).
No se requiere descargar datasets externos para correr las pruebas.

El modelo `yolov8n.pt` debe estar descargado antes de correr `test_detection.py`.
Descargarlo con:
```bash
python scripts/download_model.py
```
