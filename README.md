# DaCer — Sistema de Analítica de Video en Tiempo Real

Sistema de vigilancia inteligente que detecta objetos de interés en flujos de video mediante YOLOv8, genera alertas automáticas y registra incidentes de forma cifrada, todo on-premise sin dependencia de APIs comerciales.

**Concurso Hola Mundo 2026 · Categoría C — Analítica de Video**
**Equipo TENAXES · ITESI**

---

## Tabla de contenidos

1. [Descripción general](#descripción-general)
2. [Requisitos del sistema](#requisitos-del-sistema)
3. [Instalación](#instalación)
4. [Configuración](#configuración)
5. [Descarga del modelo](#descarga-del-modelo)
6. [Cómo ejecutar el sistema](#cómo-ejecutar-el-sistema)
7. [Cómo usar el sistema](#cómo-usar-el-sistema)
8. [Cómo correr las pruebas](#cómo-correr-las-pruebas)
9. [Estructura del proyecto](#estructura-del-proyecto)
10. [Tecnologías utilizadas](#tecnologías-utilizadas)
11. [Métricas principales](#métricas-principales)
12. [Limitaciones conocidas](#limitaciones-conocidas)
13. [Equipo](#equipo)
14. [Licencia](#licencia)

---

## Descripción general

DaCer procesa el flujo de una cámara IP o USB (1920×1080 @ 30 fps) mediante el modelo YOLOv8n ejecutado sobre GPU NVIDIA. El operador configura desde una interfaz de escritorio (PyQt6) qué clases de objetos vigilar, delimita una zona de interés (ROI) dentro del encuadre y ajusta el umbral de confianza.

Cuando una detección persiste durante N fotogramas consecutivos, el sistema:
- Emite una alerta visual en pantalla.
- Registra el incidente en una base de datos SQLite local con la imagen de evidencia cifrada (Fernet/AES-128).
- Permite consultar el historial de incidentes y exportar reportes en PDF.

Todo el procesamiento ocurre on-premise. No se requiere conexión a internet en operación.

**Objetos detectables por defecto:** Persona · Cuchillo · Tijeras · Celular · Botella (clases COCO). Configurables desde la interfaz sin modificar código.

---

## Requisitos del sistema

### Hardware mínimo

| Componente | Mínimo recomendado                                     |
|---|--------------------------------------------------------|
| CPU | AMD Ryzen 5-2600 o equivalente (6 cores)               |
| RAM | 16 GB DDR4                                             |
| GPU | NVIDIA GeForce RTX 3060 · 12 GB VRAM (CUDA compatible) |
| Almacenamiento | SSD 256 GB                                             |
| Cámara | USB (índice 0 o 1) o cámara IP accesible por red local |

> **Nota:** El sistema requiere GPU NVIDIA compatible con CUDA. No existe fallback eficiente a CPU para el motor de inferencia en tiempo real.

### Software base

| Componente | Versión |
|---|---|
| Sistema operativo | Windows 10/11 64-bit (probado) · Ubuntu 22.04 LTS (compatible) |
| Python | 3.10 o 3.11 |
| Driver NVIDIA | 525 o superior |
| CUDA Toolkit | 12.x |
| cuDNN | 8.x |

**Windows:** Asegurarse de tener instalado [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe).  
**Linux:** Instalar `libGL`: `sudo apt install libgl1-mesa-glx`.

---

## Instalación

Seguir los pasos en orden desde una máquina limpia:

### 1. Clonar el repositorio

```bash
git clone https://github.com/AngelAntonio375/dacer.git
cd dacer
```

### 2. Crear entorno virtual (recomendado)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

> La instalación incluye PyTorch con soporte CUDA. Si `pip` descarga la versión CPU de PyTorch, instalar manualmente:
> ```bash
> pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
> ```

### 4. Verificar CUDA disponible

```bash
python -c "import torch; print('CUDA disponible:', torch.cuda.is_available(), '·', torch.cuda.get_device_name(0))"
```

La salida debe mostrar `CUDA disponible: True` y el nombre de su GPU.

---

## Configuración

Editar el archivo `config.py` en la raíz del proyecto:

```python
# Índice de la cámara (0 = primera USB, 1 = segunda, o URL rtsp://... para cámara IP)
CAMERA_INDEX = 1

# Umbral de confianza de detección (0.0 – 1.0)
CONFIDENCE_THRESHOLD = 0.5

# Número mínimo de fotogramas consecutivos para confirmar una alerta
MIN_FRAMES_TO_ALERT = 3

# Cooldown entre alertas del mismo tipo de objeto (segundos)
ALERT_COOLDOWN_SECONDS = 30

# Ruta donde se almacena la base de datos de incidentes
DB_PATH = "data/incidents.db"

# Ruta del modelo (se descarga automáticamente si no existe)
MODEL_PATH = "models/yolov8n.pt"
```

La clave de cifrado Fernet se genera automáticamente en el primer arranque y se guarda en `data/.key`. **No compartir ni subir este archivo.**

---

## Descarga del modelo

El modelo `yolov8n.pt` se descarga automáticamente desde los servidores de Ultralytics al ejecutar el sistema por primera vez (requiere internet solo en esa ocasión, ~6 MB).

Para descargarlo manualmente antes:

```bash
python scripts/download_model.py
```

---

## Cómo ejecutar el sistema

```bash
python main.py
```

La interfaz de escritorio abre automáticamente. Si la cámara no se detecta, verificar el valor de `CAMERA_INDEX` en `config.py`.

---

## Cómo usar el sistema

Una vez abierta la interfaz:

1. **Seleccionar clases activas** — marcar los objetos que se desean vigilar en el panel lateral.
2. **Definir ROI (zona de interés)** — hacer clic y arrastrar sobre el video para delimitar el área de vigilancia. Dejar vacío para vigilar el encuadre completo.
3. **Ajustar umbral de confianza** — deslizar el control para modificar la sensibilidad.
4. **Iniciar vigilancia** — presionar "Iniciar". Las detecciones aparecen anotadas en el video y el log inferior registra los eventos.
5. **Consultar historial** — pestaña "Incidentes" para ver, filtrar y buscar registros anteriores.
6. **Exportar reporte PDF** — botón "Exportar PDF" en la pestaña de incidentes; genera un archivo en la carpeta `exports/`.

---

## Cómo correr las pruebas

```bash
# Todas las pruebas
python -m pytest tests/ -v

# Solo pruebas del motor de detección
python -m pytest tests/test_detection.py -v

# Solo pruebas de la base de datos
python -m pytest tests/test_database.py -v
```

Ver `tests/README.md` para descripción de cada caso de prueba y datos de muestra necesarios.

---

## Estructura del proyecto

```
dacer/
│
├── main.py                  # Punto de entrada de la aplicación
├── config.py                # Configuración editable por el operador
├── requirements.txt         # Dependencias Python con versiones fijadas
├── LICENSE                  # Licencia MIT
├── README.md                # Este archivo
├── CHANGELOG.md             # Registro de cambios por versión
│
├── src/                     # Código fuente principal
│   ├── detection/           # Motor de inferencia YOLOv8 (QThread)
│   ├── alerts/              # Lógica de confirmación de alertas y cooldown
│   ├── database/            # Acceso a SQLite: escritura, consulta, cifrado
│   ├── ui/                  # Componentes de la interfaz PyQt6
│   └── reports/             # Generación de reportes PDF con ReportLab
│
├── tests/                   # Pruebas automatizadas
│   ├── test_detection.py    # Pruebas del motor de detección
│   ├── test_database.py     # Pruebas de escritura/lectura/cifrado
│   ├── test_alerts.py       # Pruebas de lógica de alertas y cooldown
│   └── README.md            # Instrucciones y datos de muestra para pruebas
│
├── scripts/                 # Scripts auxiliares
│   ├── download_model.py    # Descarga yolov8n.pt desde Ultralytics
│   └── smoke_test.py        # Verifica que el sistema arranca correctamente
│
├── docs/                    # Documentación complementaria
│   ├── arquitectura.png     # Diagrama de arquitectura del sistema
│   ├── decisiones.md        # Registro de decisiones técnicas (ADR)
│   └── esquema_db.md        # Esquema de la base de datos SQLite
│
├── models/                  # Pesos del modelo (descargados, no en el repo)
│   └── .gitkeep
│
└── data/                    # Datos en tiempo de ejecución (no en el repo)
    └── .gitkeep
```

> Las carpetas `models/` y `data/` están en `.gitignore`. Solo se incluye `.gitkeep` para preservar la estructura al clonar.

---

## Tecnologías utilizadas

| Componente | Versión | Función |
|---|---|---|
| Python | 3.11 | Lenguaje principal |
| PyQt6 | 6.7 | Interfaz gráfica de escritorio |
| OpenCV (cv2) | 4.10 | Captura y procesamiento de frames |
| Ultralytics YOLOv8 | 8.2 | Motor de detección de objetos |
| PyTorch | 2.3 (CUDA 12.x) | Backend de inferencia |
| SQLite3 | 3.45 (stdlib) | Base de datos local de incidentes |
| cryptography (Fernet) | 42.0 | Cifrado AES-128 de imágenes |
| ReportLab | 4.2 | Generación de reportes PDF |
| NumPy | 1.26 | Manipulación de arrays de imagen |
| Pillow (PIL) | 10.3 | Conversión de imágenes para PDF |

**Modelo preentrenado:** YOLOv8n (`yolov8n.pt`) · Origen: Ultralytics / COCO 2017 · Licencia: AGPL-3.0 · Sin fine-tuning.

---

## Métricas principales

> Métricas medidas sobre hardware: Intel Core i5-12400F · 16 GB DDR4 · NVIDIA RTX 3060 12 GB · SSD NVMe · Windows 11.

| Métrica | Valor |
|---|---|
| Inferencia YOLOv8n por frame (p50) | — ms *(pendiente de medición)* |
| Inferencia YOLOv8n por frame (p95) | — ms |
| Escritura de incidente en DB | — ms |
| Generación de reporte PDF | — ms |

Ver documento técnico (`docs/`) para métricas detalladas, condiciones de medición y reporte de pruebas de carga.

---

## Limitaciones conocidas

- **Iluminación baja:** Precisión degradada por debajo de 50 lux sin iluminación infrarroja.
- **Clases COCO únicamente:** El sistema detecta objetos de las 80 clases COCO. Objetos fuera de ese conjunto requieren fine-tuning del modelo.
- **Un stream simultáneo:** Una instancia del sistema gestiona una cámara. Instalaciones con múltiples cámaras requieren múltiples instancias.
- **GPU NVIDIA obligatoria:** No existe fallback eficiente a CPU para operación en tiempo real.
- **Sin autenticación de usuario:** Cualquier operador con acceso al equipo puede ver y eliminar incidentes.

---

## Equipo

**TENAXES · Instituto Tecnológico Superior de Irapuato (ITESI) · Irapuato, Guanajuato**

| Nombre | Rol técnico | Correo |
|---|---|---|
| Ángel Antonio Ramírez Gutiérrez | *(por confirmar)* | *(por confirmar)* |
| Nataly Daphne Cervantes Martínez | *(por confirmar)* | *(por confirmar)* |
| *(Tercer integrante)* | *(por confirmar)* | *(por confirmar)* |

**Contacto principal:** *(correo del líder)*
**Repositorio:** https://github.com/AngelAntonio375/dacer
**Video de demostración:** *(link por confirmar)*

---

## Licencia

Este proyecto se distribuye bajo la licencia MIT. Ver archivo [LICENSE](LICENSE) para el texto completo.

El modelo YOLOv8n (`yolov8n.pt`) se distribuye bajo licencia AGPL-3.0 por Ultralytics. Su uso en este proyecto es conforme a dicha licencia.
