"""
download_model.py
Descarga el modelo YOLOv8n desde los servidores de Ultralytics.
Uso: python scripts/download_model.py
"""

import sys
from pathlib import Path

MODELS_DIR = Path(__file__).parent.parent / "models"
MODEL_PATH = MODELS_DIR / "yolov8n.pt"


def download_model():
    MODELS_DIR.mkdir(exist_ok=True)

    if MODEL_PATH.exists():
        print(f"[OK] El modelo ya existe en: {MODEL_PATH}")
        return

    print("Descargando yolov8n.pt desde Ultralytics (~6 MB)...")

    try:
        from ultralytics import YOLO
        model = YOLO("yolov8n.pt")
        import shutil
        yolo_cache = Path.home() / ".cache" / "ultralytics" / "assets" / "yolov8n.pt"
        if yolo_cache.exists():
            shutil.copy(yolo_cache, MODEL_PATH)
            print(f"[OK] Modelo guardado en: {MODEL_PATH}")
        else:
            model_path = Path("yolov8n.pt")
            if model_path.exists():
                shutil.move(str(model_path), MODEL_PATH)
                print(f"[OK] Modelo guardado en: {MODEL_PATH}")
            else:
                print(f"[INFO] Modelo descargado por Ultralytics. Mover manualmente a: {MODEL_PATH}")
    except ImportError:
        print("[ERROR] Ultralytics no está instalado. Ejecutar: pip install ultralytics")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] No se pudo descargar el modelo: {e}")
        sys.exit(1)


if __name__ == "__main__":
    download_model()
