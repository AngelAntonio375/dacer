"""
smoke_test.py
Verifica que el entorno está correctamente configurado para correr DaCer.
Uso: python scripts/smoke_test.py
No arranca la interfaz gráfica — solo valida dependencias y hardware.
"""

import sys

PASS = "[OK]"
FAIL = "[FALLA]"
WARN = "[AVISO]"

errors = []

def check(label, fn):
    try:
        result = fn()
        print(f"{PASS} {label}{': ' + result if result else ''}")
    except Exception as e:
        print(f"{FAIL} {label}: {e}")
        errors.append(label)


print("=" * 52)
print("  DaCer — Smoke Test")
print("=" * 52)

# Python
check("Python >= 3.10", lambda: (
    None if sys.version_info >= (3, 10)
    else (_ for _ in ()).throw(RuntimeError(f"Versión actual: {sys.version}"))
))

# Dependencias principales
check("PyQt6",        lambda: __import__("PyQt6") and None)
check("OpenCV",       lambda: __import__("cv2").getVersionString())
check("NumPy",        lambda: __import__("numpy").__version__)
check("Ultralytics",  lambda: __import__("ultralytics").__version__)
check("PyTorch",      lambda: __import__("torch").__version__)
check("cryptography", lambda: __import__("cryptography").__version__)
check("ReportLab",    lambda: __import__("reportlab").__version__)
check("Pillow",       lambda: __import__("PIL").__version__)

# CUDA
def check_cuda():
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA no disponible — revisar drivers NVIDIA y versión de PyTorch")
    return torch.cuda.get_device_name(0)
check("CUDA + GPU", check_cuda)

# Modelo
def check_model():
    from pathlib import Path
    model_path = Path(__file__).parent.parent / "models" / "yolov8n.pt"
    if not model_path.exists():
        raise RuntimeError("Modelo no encontrado — ejecutar: python scripts/download_model.py")
    return str(model_path)
check("Modelo yolov8n.pt", check_model)

# Cámara
def check_camera():
    import cv2, sys
    sys.path.insert(1, str(__import__("pathlib").Path(__file__).parent.parent))
    try:
        import config
        idx = config.CAMERA_INDEX
    except Exception:
        idx = 1
    cap = cv2.VideoCapture(idx)
    if not cap.isOpened():
        raise RuntimeError(f"No se pudo abrir la cámara (índice {idx}) — verificar conexión y config.py")
    cap.release()
    return f"índice {idx}"
check("Cámara", check_camera)

print("=" * 52)
if errors:
    print(f"  {len(errors)} problema(s) encontrado(s): {', '.join(errors)}")
    print("  Resolver los errores antes de ejecutar main.py")
    sys.exit(1)
else:
    print("  Todo listo. Ejecutar: python main.py")
print("=" * 52)
