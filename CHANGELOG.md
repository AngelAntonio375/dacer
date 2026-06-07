# Changelog — DaCer

Todos los cambios significativos del proyecto se documentan en este archivo.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).

---

## [Unreleased]

### Por hacer
- Medición y documentación de métricas de desempeño
- Reporte de pruebas de carga (4 escenarios)
- Soporte multi-cámara (trabajo futuro priorizado)

---

## [0.3.0] - 2026-05-XX

### Agregado
- Exportación de reportes PDF de incidentes con ReportLab
- Filtros de búsqueda en historial de incidentes (fecha, tipo de objeto)
- Script `scripts/smoke_test.py` para verificación rápida del sistema

### Corregido
- Cooldown de alertas no se reiniciaba correctamente al cambiar de clase activa
- Fuga de memoria en hilo de captura al reconectar cámara IP

---

## [0.2.0] - 2026-04-XX

### Agregado
- Módulo de cifrado Fernet para imágenes almacenadas en SQLite
- Selección de ROI (zona de interés) por clic y arrastre en la interfaz
- Log de eventos en tiempo real en la interfaz PyQt6
- Pruebas automatizadas para módulo de base de datos y alertas

### Modificado
- Motor de inferencia migrado a QThread independiente para eliminar bloqueos en la UI
- Umbral de confianza ahora configurable desde la interfaz sin reiniciar el sistema

---

## [0.1.0] - 2026-03-XX

### Agregado
- Captura de video con OpenCV desde cámara USB/IP
- Inferencia YOLOv8n sobre GPU NVIDIA vía CUDA
- Detección de 5 clases: Persona, Cuchillo, Tijeras, Celular, Botella
- Interfaz básica PyQt6 con visualización de video anotado
- Almacenamiento de incidentes en SQLite local
- Configuración centralizada en `config.py`
