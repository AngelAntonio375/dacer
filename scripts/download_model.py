"""
download_model.py
Descarga el modelo YOLOv8n desde los servidores de Ultralytics.
Uso: python scripts/download_model.py
"""
import os
import sys
import shutil
from pathlib import Path

# Raíz del proyecto = carpeta padre de /scripts
ROOT_DIR = Path(__file__).parent.parent
MODELS_DIR = ROOT_DIR / "models"
MODEL_PATH = MODELS_DIR / "yolov8n.pt"


def download_model():
    MODELS_DIR.mkdir(exist_ok=True)

    if MODEL_PATH.exists():
        print(f"[OK] El modelo ya existe en: {MODEL_PATH}")
        return

    print("Descargando yolov8n.pt desde Ultralytics (~6 MB)...")

    try:
        from ultralytics import YOLO

        # Ultralytics descarga el modelo al directorio de trabajo actual
        original_cwd = Path.cwd()
        os.chdir(ROOT_DIR)  # Cambiamos al root para controlar dónde cae el archivo

        model = YOLO("yolov8n.pt")  # Si no existe, lo descarga aquí

        os.chdir(original_cwd)  # Restauramos el directorio de trabajo

        # Posibles rutas donde Ultralytics pudo haber dejado el archivo
        candidates = [
            ROOT_DIR / "yolov8n.pt",
            Path.cwd() / "yolov8n.pt",
            Path.home() / ".cache" / "ultralytics" / "assets" / "yolov8n.pt",
        ]

        for candidate in candidates:
            if candidate.exists() and candidate != MODEL_PATH:
                shutil.move(str(candidate), MODEL_PATH)
                print(f"[OK] Modelo guardado en: {MODEL_PATH}")
                return

        if MODEL_PATH.exists():
            print(f"[OK] Modelo ya disponible en: {MODEL_PATH}")
        else:
            print(f"[WARN] No se encontró el archivo descargado. Mover manualmente a: {MODEL_PATH}")

    except ImportError:
        print("[ERROR] Ultralytics no está instalado. Ejecutar: pip install ultralytics")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] No se pudo descargar el modelo: {e}")
        sys.exit(1)


if __name__ == "__main__":
    download_model()