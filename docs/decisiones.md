# Decisiones técnicas — DaCer

Registro de las principales decisiones de arquitectura y tecnología tomadas durante el desarrollo.

---

## 1. Motor de inferencia en QThread independiente

**Decisión:** El hilo de captura y el de inferencia YOLOv8 corren en QThreads separados del hilo principal de la UI.

**Alternativa descartada:** Correr la inferencia en el hilo principal de PyQt6.

**Razón:** PyQt6 bloquea la interfaz completa mientras el hilo principal está ocupado. Con inferencia a ~60 fps, la UI se congelaría entre cada frame. El patrón QThread permite actualizar el video anotado mediante señales (pyqtSignal) sin bloquear controles ni el log de eventos.

---

## 2. YOLOv8n como modelo base (sin fine-tuning)

**Decisión:** Usar los pesos preentrenados `yolov8n.pt` sobre COCO 2017 sin fine-tuning adicional.

**Alternativa descartada:** Fine-tuning con dataset propio de objetos específicos.

**Razón:** Las clases objetivo (persona, cuchillo, tijeras, celular, botella) están presentes en COCO con suficiente representación. El fine-tuning requeriría recolectar y etiquetar un dataset propio, lo que está fuera del alcance del concurso. YOLOv8n fue elegido sobre YOLOv8s/m por su menor latencia en GPU de gama media (RTX 3060), priorizando tiempo real sobre precisión máxima.

---

## 3. SQLite como base de datos local

**Decisión:** Almacenar incidentes en SQLite embebido, sin servidor de base de datos (aunque puede usarse para un ambiente de monitoreo remoto o de flujo masivo de datos de millones de incidentes).

**Alternativa descartada:** PostgreSQL o MySQL local.

**Razón:** El volumen de incidentes esperado (decenas a cientos por día) no justifica un servidor de BD. SQLite es suficiente, no requiere configuración adicional, y simplifica el despliegue: el sistema arranca con `python main.py` sin servicios externos.

---

## 4. Cifrado Fernet (AES-128) para imágenes en DB

**Decisión:** Las imágenes de evidencia se cifran con Fernet antes de almacenarse en SQLite.

**Alternativa descartada:** Almacenar imágenes como archivos en disco sin cifrar.

**Razón:** Las imágenes de incidentes pueden contener información sensible (personas identificables). Fernet provee cifrado simétrico autenticado; la clave se genera una vez y se almacena localmente en `data/.key`. Si la base de datos es extraída del equipo, las imágenes no son legibles sin la clave.

---

## 5. PyQt6 como framework de interfaz

**Decisión:** Interfaz de escritorio nativa con PyQt6.

**Alternativa descartada:** Interfaz web (Flask + React) o Tkinter.

**Razón:** PyQt6 permite mostrar video a 30 fps con QLabel/QPixmap sin overhead de navegador. Tkinter carece de widgets suficientes para un dashboard operativo. Una interfaz web añadiría complejidad de despliegue innecesaria para un sistema de escritorio on-premise.

---

## 6. ReportLab para generación de PDF

**Decisión:** Generar reportes PDF con ReportLab desde Python.

**Alternativa descartada:** Exportar a HTML y convertir con wkhtmltopdf o similar.

**Razón:** ReportLab genera PDF de forma programática sin dependencias externas de sistema. La conversión HTML→PDF requiere instalar wkhtmltopdf, que varía en comportamiento entre Windows y Linux y añade complejidad al despliegue.
