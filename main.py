import sys
import cv2
import numpy as np
import sqlite3
import os
import time
from datetime import datetime
from cryptography.fernet import Fernet

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QTextEdit,
                             QFrame, QCheckBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QLineEdit, QMessageBox, QSlider,
                             QDoubleSpinBox, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QRect, QPoint
from PyQt6.QtGui import QImage, QPixmap, QFont, QPainter, QPen, QColor

# reportlab para PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import tempfile
import io

from ultralytics import YOLO
os.makedirs("models", exist_ok=True)
os.makedirs("data", exist_ok=True)

# ==========================================
# CONFIGURACIÓN GLOBAL Y CIFRADO
# ==========================================
MODELO_YOLO = "models/yolov8n.pt"
CAMARA_INDEX = 1
ANCHO_CAM = 1920
ALTO_CAM = 1080
UMBRAL_CONFIANZA = 0.90
FRAMES_PERSISTENCIA_ALERTA = 5
COOLDOWN_SEGUNDOS = 30          # segundos mínimos entre registros del mismo objeto

OBJETOS_ALERTAS = {
    "Persona": 0,
    "Bicicleta": 1,
    "Automóvil": 2,
    "Motocicleta": 3,
    #"Avión": 4,
    "Autobús": 5,
    #"Tren": 6,
    "Camión": 7,
    #"Barco": 8,
    #"Semáforo": 9,
    #"Hidrante de incendios": 10,
    #"Señal de stop": 11,
    #"Parquímetro": 12,
    #"Banco": 13,
    #"Pájaro": 14,
    "Gato": 15,
    "Perro": 16,
    #"Caballo": 17,
    #"Oveja": 18,
    #"Vaca": 19,
    #"Elefante": 20,
    #"Oso": 21,
    #"Cebra": 22,
    #"Jirafa": 23,
    "Mochila": 24,
    #"Paraguas": 25,
    "Bolso de mano": 26,
    #"Corbata": 27,
    "Maleta": 28,
    #"Frisbee": 29,
    #"Esquís": 30,
    #"Tabla de snowboard": 31,
    #"Pelota deportiva": 32,
    #"Cometa": 33,
    "Bate de béisbol": 34,
    #"Guante de béisbol": 35,
    #"Patineta": 36,
    #"Tabla de surf": 37,
    #"Raqueta de tenis": 38,
    "Botella": 39,
    #"Copa de vino": 40,
    #"Taza": 41,
    #"Tenedor": 42,
    "Cuchillo": 43,
    #"Cuchara": 44,
    #"Tazón": 45,
    #"Plátano": 46,
    #"Manzana": 47,
    #"Sándwich": 48,
    #"Naranja": 49,
    #"Brócoli": 50,
    #"Zanahoria": 51,
    #"Perrito caliente": 52,
    #"Pizza": 53,
    #"Dona": 54,
    #"Pastel": 55,
    #"Silla": 56,
    #"Sofá": 57,
    #"Planta en maceta": 58,
    #"Cama": 59,
    #"Mesa de comedor": 60,
    #"Inodoro": 61,
    #"Televisor": 62,
    #"Computadora portátil": 63,
    #"Ratón": 64,
    #"Control remoto": 65,
    #"Teclado": 66,
    "Celular": 67,
    #"Microondas": 68,
    #"Horno": 69,
    #"Tostadora": 70,
    #"Fregadero": 71,
    #"Refrigerador": 72,
    #"Libro": 73,
    #"Reloj": 74,
    #"Florero": 75,
    "Tijeras": 76,
    #"Oso de peluche": 77,
    #"Secador de pelo": 78,
    #"Cepillo de dientes": 79
}

KEY_FILE = "data/secret.key"
if not os.path.exists(KEY_FILE):
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)
else:
    with open(KEY_FILE, "rb") as f:
        key = f.read()
cipher_suite = Fernet(key)


# ==========================================
# GESTIÓN DE BASE DE DATOS
# ==========================================
def init_db():
    conn = sqlite3.connect("data/incidentes.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS incidentes 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       fecha TEXT, objeto TEXT, imagen_cifrada BLOB)''')
    conn.commit()
    conn.close()


def guardar_incidente_db(objeto, frame):
    try:
        _, buffer = cv2.imencode('.jpg', frame)
        img_encriptada = cipher_suite.encrypt(buffer.tobytes())
        conn = sqlite3.connect("data/incidentes.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO incidentes (fecha, objeto, imagen_cifrada) VALUES (?, ?, ?)",
                       (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), objeto, img_encriptada))
        conn.commit()
        conn.close()
    except Exception:
        pass


# ==========================================
# WIDGET DE VIDEO CON SOPORTE ROI
# ==========================================
class VideoLabel(QLabel):
    """QLabel extendido que permite dibujar un ROI con el mouse."""
    roi_changed = pyqtSignal(object)  # emite QRect o None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.roi_rect = None          # QRect en coords del widget
        self._drawing = False
        self._start_point = None
        self._end_point = None
        self.roi_enabled = False

    def set_roi_mode(self, enabled: bool):
        self.roi_enabled = enabled
        if not enabled:
            self.roi_rect = None
            self.roi_changed.emit(None)
            self.update()

    def mousePressEvent(self, event):
        if self.roi_enabled and event.button() == Qt.MouseButton.LeftButton:
            self._drawing = True
            self._start_point = event.pos()
            self._end_point = event.pos()

    def mouseMoveEvent(self, event):
        if self._drawing:
            self._end_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if self._drawing and event.button() == Qt.MouseButton.LeftButton:
            self._drawing = False
            self._end_point = event.pos()
            self.roi_rect = QRect(self._start_point, self._end_point).normalized()
            self.roi_changed.emit(self.roi_rect)
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)

        # Dibuja el ROI guardado
        if self.roi_rect and not self._drawing:
            pen = QPen(QColor(0, 255, 100), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawRect(self.roi_rect)
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            painter.setPen(QColor(0, 255, 100))
            painter.drawText(self.roi_rect.topLeft() + QPoint(4, -6), "ZONA ACTIVA")

        # Dibuja mientras arrastra
        if self._drawing and self._start_point and self._end_point:
            pen = QPen(QColor(255, 200, 0), 2, Qt.PenStyle.DotLine)
            painter.setPen(pen)
            painter.drawRect(QRect(self._start_point, self._end_point).normalized())

        painter.end()


# ==========================================
# HILO DE IA
# ==========================================
class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)
    alert_signal = pyqtSignal(bool, str, bool)   # activa, mensaje, guardar_en_db
    detection_log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.clases_activas = []
        self.umbral_confianza = UMBRAL_CONFIANZA

        # ROI en coordenadas normalizadas [x1, y1, x2, y2] (0.0 – 1.0)
        # None = sin restricción de zona
        self.roi_norm = None

        # Cooldown: guarda el timestamp del último registro por objeto
        self._ultimo_guardado: dict[str, float] = {}

    def actualizar_clases(self, lista_ids):
        self.clases_activas = lista_ids

    def actualizar_umbral(self, valor: float):
        self.umbral_confianza = valor

    def actualizar_roi(self, roi_norm):
        """roi_norm: (x1_n, y1_n, x2_n, y2_n) o None."""
        self.roi_norm = roi_norm

    def _puede_guardar(self, label: str) -> bool:
        """Devuelve True solo si pasaron COOLDOWN_SEGUNDOS desde el último
        registro del mismo tipo de objeto. Actualiza el timestamp si procede."""
        ahora = time.time()
        if ahora - self._ultimo_guardado.get(label, 0) >= COOLDOWN_SEGUNDOS:
            self._ultimo_guardado[label] = ahora
            return True
        return False

    def _box_en_roi(self, box_xyxy, frame_w, frame_h):
        """Devuelve True si el centro del bounding box está dentro del ROI."""
        if self.roi_norm is None:
            return True
        x1r, y1r, x2r, y2r = self.roi_norm
        bx1, by1, bx2, by2 = box_xyxy
        cx = ((bx1 + bx2) / 2) / frame_w
        cy = ((by1 + by2) / 2) / frame_h
        return x1r <= cx <= x2r and y1r <= cy <= y2r

    def run(self):
        try:
            self.model = YOLO(MODELO_YOLO)
            self.model.to('cuda')
            self.cap = cv2.VideoCapture(CAMARA_INDEX, cv2.CAP_DSHOW)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, ANCHO_CAM)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, ALTO_CAM)

            contador_alerta = 0
            alerta_activa = False

            while self._run_flag:
                ret, frame = self.cap.read()
                if not ret:
                    break

                fh, fw = frame.shape[:2]
                results = self.model(frame, stream=True, device=0,
                                     conf=self.umbral_confianza, verbose=False)
                hay_amenaza = False
                label_obj = ""
                annotated_frame = frame.copy()

                for r in results:
                    for box in r.boxes:
                        cls = int(box.cls[0])
                        xyxy = box.xyxy[0].tolist()
                        if cls in self.clases_activas and self._box_en_roi(xyxy, fw, fh):
                            hay_amenaza = True
                            label_obj = self.model.names[cls]
                    annotated_frame = r.plot()

                # Dibuja el ROI sobre el frame anotado
                if self.roi_norm is not None:
                    x1r, y1r, x2r, y2r = self.roi_norm
                    rx1, ry1 = int(x1r * fw), int(y1r * fh)
                    rx2, ry2 = int(x2r * fw), int(y2r * fh)
                    cv2.rectangle(annotated_frame, (rx1, ry1), (rx2, ry2),
                                  (0, 255, 100), 2)
                    cv2.putText(annotated_frame, "ZONA ACTIVA",
                                (rx1 + 4, ry1 - 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                                (0, 255, 100), 2)

                if hay_amenaza:
                    contador_alerta += 1
                    if contador_alerta >= FRAMES_PERSISTENCIA_ALERTA and not alerta_activa:
                        alerta_activa = True
                        debe_guardar = self._puede_guardar(label_obj)
                        self.alert_signal.emit(
                            True,
                            f"¡ALERTA! Objeto Detectado ({label_obj.upper()})",
                            debe_guardar)
                        if debe_guardar:
                            self.detection_log_signal.emit(f"Detección confirmada: {label_obj}")
                        else:
                            self.detection_log_signal.emit(
                                f"Detección ({label_obj}) — cooldown activo, no se vuelve a registrar")
                else:
                    contador_alerta = 0
                    if alerta_activa:
                        alerta_activa = False
                        self.alert_signal.emit(False, "", False)

                self.change_pixmap_signal.emit(annotated_frame)

            self.cap.release()
        except Exception as e:
            print(f"Error en hilo de video: {e}")

    def stop(self):
        self._run_flag = False
        self.wait()


# ==========================================
# GUI PRINCIPAL
# ==========================================
class SurveillanceDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        init_db()
        self.setWindowTitle("DaCer")
        self.resize(1800, 1100)
        self.last_frame = None
        self._roi_mode_active = False

        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QLabel { color: #f0f0f0; font-family: 'Segoe UI'; }
            QCheckBox { color: #f0f0f0; font-family: 'Segoe UI'; font-size: 14px; }
            QTextEdit { background-color: #2d2d2d; color: #a0f0a0; border: 1px solid #3d3d3d; font-family: 'Consolas'; font-size: 12px; }
            QFrame#VideoFrame { border: 2px solid #3d3d3d; background-color: #000; }
            QFrame#LogFrame { border: 1px solid #3d3d3d; background-color: #252525; }
            QPushButton#BtnStop { background-color: #d32f2f; color: white; font-weight: bold; border-radius: 5px; padding: 10px; }
            QPushButton#BtnHistory { background-color: #0078d7; color: white; font-weight: bold; border-radius: 5px; padding: 10px; }
            QPushButton#BtnRoi { background-color: #2e7d32; color: white; font-weight: bold; border-radius: 5px; padding: 10px; }
            QPushButton#BtnRoiActive { background-color: #f9a825; color: #1e1e1e; font-weight: bold; border-radius: 5px; padding: 10px; }
            QPushButton#BtnClearRoi { background-color: #4a4a4a; color: white; font-weight: bold; border-radius: 5px; padding: 8px; }
            QLabel#AlertStatus { background-color: #2d2d2d; color: #4caf50; font-weight: bold; font-size: 18px; border-radius: 5px; padding: 10px; border: 1px solid #3d3d3d;}
            QDoubleSpinBox { background-color: #2d2d2d; color: white; border: 1px solid #3d3d3d; padding: 4px; border-radius: 4px; }
        """)

        self.check_widgets = {}
        self.init_ui()

        self.alert_timer = QTimer()
        self.alert_timer.timeout.connect(self.toggle_alert_style)
        self.alert_state = False

        self.thread = VideoThread()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.alert_signal.connect(self.handle_alert)
        self.thread.detection_log_signal.connect(self.update_log_event)
        self.actualizar_configuracion_alertas()
        self.thread.start()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # --- HEADER ---
        header_layout = QHBoxLayout()
        title_label = QLabel("PANEL DE CONTROL DE VIGILANCIA")
        title_label.setFont(QFont('Segoe UI', 20, QFont.Weight.Bold))
        header_layout.addWidget(title_label, stretch=3)

        self.lbl_alert_status = QLabel("ESTADO: SEGURO")
        self.lbl_alert_status.setObjectName("AlertStatus")
        self.lbl_alert_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.lbl_alert_status, stretch=2)

        btn_history = QPushButton("VER REGISTRO DB")
        btn_history.setObjectName("BtnHistory")
        btn_history.clicked.connect(self.mostrar_historial)
        header_layout.addWidget(btn_history, stretch=1)

        btn_stop = QPushButton("DETENER SISTEMA")
        btn_stop.setObjectName("BtnStop")
        btn_stop.clicked.connect(self.close_application)
        header_layout.addWidget(btn_stop, stretch=1)
        main_layout.addLayout(header_layout, stretch=1)

        # --- CONTENIDO CENTRAL ---
        central_content_layout = QHBoxLayout()
        central_content_layout.setSpacing(15)

        # Frame de video
        self.video_frame = QFrame()
        self.video_frame.setObjectName("VideoFrame")
        video_layout = QVBoxLayout(self.video_frame)
        video_layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_video = VideoLabel("Esperando señal de cámara...")
        self.lbl_video.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_video.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.lbl_video.roi_changed.connect(self.on_roi_drawn)
        video_layout.addWidget(self.lbl_video)
        central_content_layout.addWidget(self.video_frame, stretch=4)

        # Sidebar
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("LogFrame")
        sidebar_layout = QVBoxLayout(sidebar_frame)

        lbl_info = QLabel("INFO SISTEMA")
        lbl_info.setFont(QFont('Segoe UI', 12, QFont.Weight.Bold))
        lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(lbl_info)

        self.lbl_gpu_info = QLabel("GPU: NVIDIA RTX 3060 Activa")
        self.lbl_gpu_info.setStyleSheet("color: #4caf50;")
        sidebar_layout.addWidget(self.lbl_gpu_info)

        self.lbl_cam_info = QLabel(f"Res: {ANCHO_CAM}x{ALTO_CAM} @ 60fps")
        sidebar_layout.addWidget(self.lbl_cam_info)

        self._add_separator(sidebar_layout)

        # --- CONTROL DE CONFIANZA ---
        lbl_conf = QLabel("UMBRAL DE CONFIANZA:")
        lbl_conf.setFont(QFont('Segoe UI', 10, QFont.Weight.Bold))
        sidebar_layout.addWidget(lbl_conf)

        conf_row = QHBoxLayout()
        self.spin_conf = QDoubleSpinBox()
        self.spin_conf.setRange(0.05, 0.95)
        self.spin_conf.setSingleStep(0.05)
        self.spin_conf.setValue(UMBRAL_CONFIANZA)
        self.spin_conf.setDecimals(2)
        self.spin_conf.valueChanged.connect(self.actualizar_umbral)
        conf_row.addWidget(self.spin_conf)
        self.lbl_conf_val = QLabel(f"{UMBRAL_CONFIANZA:.0%}")
        self.lbl_conf_val.setStyleSheet("color: #f9a825; font-weight: bold;")
        conf_row.addWidget(self.lbl_conf_val)
        sidebar_layout.addLayout(conf_row)

        self._add_separator(sidebar_layout)

        # --- CONTROL DE ROI ---
        lbl_roi_sec = QLabel("ZONA DE INTERÉS (ROI):")
        lbl_roi_sec.setFont(QFont('Segoe UI', 10, QFont.Weight.Bold))
        sidebar_layout.addWidget(lbl_roi_sec)

        self.btn_roi = QPushButton("✏  DIBUJAR ZONA")
        self.btn_roi.setObjectName("BtnRoi")
        self.btn_roi.clicked.connect(self.toggle_roi_mode)
        sidebar_layout.addWidget(self.btn_roi)

        self.btn_clear_roi = QPushButton("✕  QUITAR ZONA")
        self.btn_clear_roi.setObjectName("BtnClearRoi")
        self.btn_clear_roi.clicked.connect(self.clear_roi)
        sidebar_layout.addWidget(self.btn_clear_roi)

        self.lbl_roi_estado = QLabel("Sin zona activa")
        self.lbl_roi_estado.setStyleSheet("color: #888; font-size: 11px;")
        sidebar_layout.addWidget(self.lbl_roi_estado)

        self._add_separator(sidebar_layout)

        # --- ALERTAS ---
        lbl_alert_config = QLabel("ACTIVAR ALERTAS:")
        lbl_alert_config.setFont(QFont('Segoe UI', 10, QFont.Weight.Bold))
        sidebar_layout.addWidget(lbl_alert_config)

        for nombre, coco_id in OBJETOS_ALERTAS.items():
            cb = QCheckBox(nombre)
            #if nombre in ["Tijeras", "Cuchillo"]:
            #    cb.setChecked(True)
            cb.stateChanged.connect(self.actualizar_configuracion_alertas)
            self.check_widgets[coco_id] = cb
            sidebar_layout.addWidget(cb)

        sidebar_layout.addStretch()
        central_content_layout.addWidget(sidebar_frame, stretch=1)
        main_layout.addLayout(central_content_layout, stretch=6)

        # --- LOG ---
        log_frame = QFrame()
        log_frame.setObjectName("LogFrame")
        log_layout = QVBoxLayout(log_frame)
        lbl_log = QLabel("LOG DE DETECCIONES Y EVENTOS")
        lbl_log.setFont(QFont('Segoe UI', 11, QFont.Weight.Bold))
        log_layout.addWidget(lbl_log)
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        log_layout.addWidget(self.txt_log)
        main_layout.addWidget(log_frame, stretch=2)

    def _add_separator(self, layout):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #3d3d3d;")
        layout.addWidget(line)

    # ---- ROI ----
    def toggle_roi_mode(self):
        self._roi_mode_active = not self._roi_mode_active
        self.lbl_video.set_roi_mode(self._roi_mode_active)
        if self._roi_mode_active:
            self.btn_roi.setObjectName("BtnRoiActive")
            self.btn_roi.setText("✏  DIBUJANDO... (clic en video)")
            self.lbl_roi_estado.setText("Arrastra en el video para definir la zona")
            self.lbl_roi_estado.setStyleSheet("color: #f9a825; font-size: 11px;")
        else:
            self.btn_roi.setObjectName("BtnRoi")
            self.btn_roi.setText("✏  DIBUJAR ZONA")
        self.btn_roi.setStyle(self.btn_roi.style())  # fuerza refresco del estilo

    def on_roi_drawn(self, q_rect):
        """Convierte el QRect del widget a coordenadas normalizadas del frame."""
        self._roi_mode_active = False
        self.btn_roi.setObjectName("BtnRoi")
        self.btn_roi.setText("✏  DIBUJAR ZONA")
        self.btn_roi.setStyle(self.btn_roi.style())

        if q_rect is None or not self.lbl_video.pixmap():
            self.thread.actualizar_roi(None)
            return

        # El pixmap está centrado con KeepAspectRatio; hay que mapear correctamente
        pm = self.lbl_video.pixmap()
        lw, lh = self.lbl_video.width(), self.lbl_video.height()
        pw, ph = pm.width(), pm.height()
        off_x = (lw - pw) // 2
        off_y = (lh - ph) // 2

        # Coordenadas relativas al pixmap
        rx1 = max(0, q_rect.left() - off_x) / pw
        ry1 = max(0, q_rect.top() - off_y) / ph
        rx2 = min(pw, q_rect.right() - off_x) / pw
        ry2 = min(ph, q_rect.bottom() - off_y) / ph

        if rx2 <= rx1 or ry2 <= ry1:
            return

        self.thread.actualizar_roi((rx1, ry1, rx2, ry2))
        self.lbl_roi_estado.setText(
            f"Zona: ({rx1:.2f},{ry1:.2f}) → ({rx2:.2f},{ry2:.2f})")
        self.lbl_roi_estado.setStyleSheet("color: #4caf50; font-size: 11px;")
        self.update_log_event("ROI actualizado")

    def clear_roi(self):
        self.lbl_video.set_roi_mode(False)
        self._roi_mode_active = False
        self.thread.actualizar_roi(None)
        self.lbl_roi_estado.setText("Sin zona activa")
        self.lbl_roi_estado.setStyleSheet("color: #888; font-size: 11px;")
        self.update_log_event("ROI eliminado — vigilancia en frame completo")

    # ---- UMBRAL ----
    def actualizar_umbral(self, valor):
        self.lbl_conf_val.setText(f"{valor:.0%}")
        if hasattr(self, 'thread'):
            self.thread.actualizar_umbral(valor)

    # ---- ALERTAS / CLASES ----
    def actualizar_configuracion_alertas(self):
        ids = [cid for cid, cb in self.check_widgets.items() if cb.isChecked()]
        if hasattr(self, 'thread'):
            self.thread.actualizar_clases(ids)

    def update_image(self, cv_img):
        try:
            self.last_frame = cv_img.copy()
            rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888).copy()
            pixmap = QPixmap.fromImage(qimg)
            self.lbl_video.setPixmap(
                pixmap.scaled(self.lbl_video.width(), self.lbl_video.height(),
                              Qt.AspectRatioMode.KeepAspectRatio))
        except Exception:
            pass

    def handle_alert(self, active, message, guardar):
        if active:
            self.lbl_alert_status.setText(message)
            if guardar and self.last_frame is not None:
                guardar_incidente_db(message, self.last_frame)
            self.alert_timer.start(500)
        else:
            self.lbl_alert_status.setText("ESTADO: SEGURO")
            self.lbl_alert_status.setStyleSheet(
                "background-color: #2d2d2d; color: #4caf50;")
            self.alert_timer.stop()

    def toggle_alert_style(self):
        color = "#d32f2f" if self.alert_state else "#2d2d2d"
        self.lbl_alert_status.setStyleSheet(
            f"background-color: {color}; color: white;")
        self.alert_state = not self.alert_state

    def update_log_event(self, text):
        self.txt_log.append(
            f"[{datetime.now().strftime('%H:%M:%S')}] - {text}")

    def mostrar_historial(self):
        self.win_history = HistoryWindow()
        self.win_history.show()

    def close_application(self):
        if hasattr(self, 'thread'):
            self.thread.stop()
        QApplication.quit()

    def closeEvent(self, event):
        if hasattr(self, 'thread'):
            self.thread.stop()
        event.accept()


# ==========================================
# EXPORTACIÓN PDF
# ==========================================
def exportar_reporte_pdf(filtro: str = "") -> str:
    """Genera un PDF con los incidentes de la DB y devuelve la ruta del archivo."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta = f"data/reporte_incidentes_{timestamp}.pdf"

    doc = SimpleDocTemplate(ruta, pagesize=letter,
                            leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                            topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    story = []

    # Estilos personalizados
    titulo_style = ParagraphStyle('titulo', parent=styles['Title'],
                                  fontSize=20, spaceAfter=6,
                                  textColor=colors.HexColor('#1a237e'))
    sub_style = ParagraphStyle('sub', parent=styles['Normal'],
                               fontSize=10, textColor=colors.grey, spaceAfter=20)
    info_style = ParagraphStyle('info', parent=styles['Normal'],
                                fontSize=9, textColor=colors.HexColor('#333333'))

    # Encabezado
    story.append(Paragraph("REPORTE DE INCIDENTES DE VIGILANCIA", titulo_style))
    story.append(Paragraph(
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}  |  Sistema: DaCer",
        sub_style))

    # Línea separadora (tabla 1-celda con fondo)
    sep = Table([['']], colWidths=[6.5 * inch], rowHeights=[4])
    sep.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1),
                              colors.HexColor('#1a237e'))]))
    story.append(sep)
    story.append(Spacer(1, 14))

    # Resumen
    conn = sqlite3.connect("data/incidentes.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM incidentes")
    total = cursor.fetchone()[0]

    cursor.execute(
        "SELECT objeto, COUNT(*) as n FROM incidentes GROUP BY objeto ORDER BY n DESC")
    conteos = cursor.fetchall()

    story.append(Paragraph(f"<b>Total de incidentes registrados:</b> {total}", info_style))
    story.append(Spacer(1, 6))

    if conteos:
        resumen_data = [["Objeto Detectado", "Cantidad"]]
        for obj, cnt in conteos:
            resumen_data.append([obj, str(cnt)])
        t_resumen = Table(resumen_data, colWidths=[3 * inch, 1.5 * inch])
        t_resumen.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.HexColor('#f5f5f5'), colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t_resumen)

    story.append(Spacer(1, 20))

    # Tabla de incidentes con imágenes
    query = """SELECT id, fecha, objeto, imagen_cifrada FROM incidentes
               WHERE objeto LIKE ? OR fecha LIKE ?
               ORDER BY id DESC"""
    cursor.execute(query, (f'%{filtro}%', f'%{filtro}%'))
    rows = cursor.fetchall()
    conn.close()

    story.append(Paragraph("<b>DETALLE DE INCIDENTES</b>", info_style))
    story.append(Spacer(1, 8))

    for rec_id, fecha, objeto, img_cifrada in rows:
        # Fila de datos
        data = [["ID", "Fecha y Hora", "Objeto Detectado"],
                [str(rec_id), fecha, objeto]]
        t_inc = Table(data, colWidths=[0.6 * inch, 2.2 * inch, 3.7 * inch])
        t_inc.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#37474f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#eceff1')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#b0bec5')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t_inc)

        # Imagen del incidente
        if img_cifrada:
            try:
                decrypted = cipher_suite.decrypt(img_cifrada)
                nparr = np.frombuffer(decrypted, np.uint8)
                img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
                from PIL import Image as PILImage
                pil_img = PILImage.fromarray(img_rgb)
                buf = io.BytesIO()
                pil_img.save(buf, format='JPEG', quality=70)
                buf.seek(0)
                rl_img = RLImage(buf, width=5 * inch, height=2.8 * inch)
                story.append(rl_img)
            except Exception:
                story.append(Paragraph("[Imagen no disponible]",
                                       styles['Italic']))

        story.append(Spacer(1, 14))

    doc.build(story)
    return ruta


# ==========================================
# VENTANA DE REGISTRO
# ==========================================
class HistoryWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Incidentes")
        self.resize(1000, 800)
        self.setStyleSheet("""
            QWidget { background-color: #1e1e1e; color: white; }
            QLineEdit { background-color: #2d2d2d; color: white; border: 1px solid #3d3d3d; padding: 8px; border-radius: 5px; }
            QPushButton#BtnDelOne { background-color: #e67e22; color: white; border-radius: 5px; padding: 8px; font-weight: bold; }
            QPushButton#BtnDelAll { background-color: #c0392b; color: white; border-radius: 5px; padding: 8px; font-weight: bold; }
            QPushButton#BtnExport { background-color: #1565c0; color: white; border-radius: 5px; padding: 8px; font-weight: bold; }
            QTableWidget { gridline-color: #3d3d3d; border: 1px solid #3d3d3d; selection-background-color: #3498db; }
            QHeaderView::section { background-color: #2d2d2d; color: white; border: 1px solid #3d3d3d; }
        """)

        layout = QVBoxLayout(self)

        # Barra de herramientas
        tool_bar = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Filtrar...")
        self.search_bar.textChanged.connect(self.cargar_datos)

        btn_del_selected = QPushButton("ELIMINAR SELECCIONADO")
        btn_del_selected.setObjectName("BtnDelOne")
        btn_del_selected.clicked.connect(self.eliminar_registro_individual)

        btn_del_all = QPushButton("VACIAR TODO")
        btn_del_all.setObjectName("BtnDelAll")
        btn_del_all.clicked.connect(self.eliminar_todo)

        btn_export = QPushButton("📄 EXPORTAR PDF")
        btn_export.setObjectName("BtnExport")
        btn_export.clicked.connect(self.exportar_pdf)

        tool_bar.addWidget(self.search_bar, stretch=4)
        tool_bar.addWidget(btn_del_selected, stretch=1)
        tool_bar.addWidget(btn_del_all, stretch=1)
        tool_bar.addWidget(btn_export, stretch=1)
        layout.addLayout(tool_bar)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["ID", "Fecha", "Objeto"])
        self.tabla.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.itemDoubleClicked.connect(self.ver_imagen)
        layout.addWidget(self.tabla)

        self.lbl_img = QLabel("Doble clic para ver captura")
        self.lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_img.setStyleSheet(
            "background: #000; border: 2px solid #3d3d3d; min-height: 400px; border-radius: 10px;")
        layout.addWidget(self.lbl_img)

        self.cargar_datos()

    def cargar_datos(self):
        try:
            filtro = self.search_bar.text()
            self.tabla.setRowCount(0)
            conn = sqlite3.connect("data/incidentes.db")
            cursor = conn.cursor()
            query = ("SELECT id, fecha, objeto FROM incidentes "
                     "WHERE objeto LIKE ? OR fecha LIKE ? ORDER BY id DESC")
            cursor.execute(query, (f'%{filtro}%', f'%{filtro}%'))
            for i, row in enumerate(cursor.fetchall()):
                self.tabla.insertRow(i)
                for j, val in enumerate(row):
                    item = QTableWidgetItem(str(val))
                    item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                    self.tabla.setItem(i, j, item)
            conn.close()
        except Exception:
            pass

    def eliminar_registro_individual(self):
        row = self.tabla.currentRow()
        if row < 0:
            return
        id_db = self.tabla.item(row, 0).text()
        confirm = QMessageBox.question(
            self, 'Confirmar', f'¿Eliminar registro {id_db}?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            conn = sqlite3.connect("data/incidentes.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM incidentes WHERE id = ?", (id_db,))
            conn.commit()
            conn.close()
            self.cargar_datos()
            self.lbl_img.setText("Eliminado.")

    def eliminar_todo(self):
        reply = QMessageBox.question(
            self, 'Confirmar', '¿Vaciar base de datos?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            conn = sqlite3.connect("data/incidentes.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM incidentes")
            conn.commit()
            conn.close()
            self.cargar_datos()
            self.lbl_img.setText("DB Vaciada.")

    def exportar_pdf(self):
        try:
            filtro = self.search_bar.text()
            ruta = exportar_reporte_pdf(filtro)
            QMessageBox.information(
                self, "PDF Exportado",
                f"Reporte guardado exitosamente:\n{os.path.abspath(ruta)}")
        except Exception as e:
            QMessageBox.critical(self, "Error al exportar",
                                 f"No se pudo generar el PDF:\n{str(e)}")

    def ver_imagen(self, item):
        try:
            id_db = self.tabla.item(item.row(), 0).text()
            conn = sqlite3.connect("data/incidentes.db")
            cursor = conn.cursor()
            cursor.execute(
                "SELECT imagen_cifrada FROM incidentes WHERE id = ?", (id_db,))
            res = cursor.fetchone()
            conn.close()
            if res:
                decrypted = cipher_suite.decrypt(res[0])
                nparr = np.frombuffer(decrypted, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                qimg = QImage(rgb.data, w, h, w * ch,
                              QImage.Format.Format_RGB888).copy()
                self.lbl_img.setPixmap(
                    QPixmap.fromImage(qimg).scaled(
                        self.lbl_img.width(), self.lbl_img.height(),
                        Qt.AspectRatioMode.KeepAspectRatio))
        except Exception:
            self.lbl_img.setText("Error al cargar imagen.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    dashboard = SurveillanceDashboard()
    dashboard.show()
    sys.exit(app.exec())