"""
src/roi_utils.py
Utilidades para la zona de interés (Region of Interest).
Todas las coordenadas normalizadas son floats en [0.0, 1.0].
"""

from typing import Optional


RoiNorm = tuple[float, float, float, float]  # (x1, y1, x2, y2) normalizadas


def box_en_roi(box_xyxy: list[float], frame_w: int, frame_h: int,
               roi: Optional[RoiNorm]) -> bool:
    """
    Devuelve True si el centro del bounding box está dentro del ROI.

    Si roi es None, siempre devuelve True (sin restricción de zona).

    Args:
        box_xyxy: Coordenadas del bounding box [x1, y1, x2, y2] en píxeles.
        frame_w: Ancho del frame en píxeles.
        frame_h: Alto del frame en píxeles.
        roi: Tupla (x1_n, y1_n, x2_n, y2_n) en coordenadas normalizadas, o None.

    Returns:
        True si el centro del box está dentro del ROI (o si roi es None).
    """
    if roi is None:
        return True

    x1r, y1r, x2r, y2r = roi
    bx1, by1, bx2, by2 = box_xyxy

    cx = ((bx1 + bx2) / 2) / frame_w
    cy = ((by1 + by2) / 2) / frame_h

    return x1r <= cx <= x2r and y1r <= cy <= y2r


def qrect_a_roi_norm(q_rect, label_w: int, label_h: int,
                     pixmap_w: int, pixmap_h: int) -> Optional[RoiNorm]:
    """
    Convierte un QRect en coordenadas del widget a coordenadas normalizadas del frame.

    Tiene en cuenta el centrado del pixmap con KeepAspectRatio dentro del QLabel.

    Args:
        q_rect: QRect dibujado por el usuario sobre el QLabel.
        label_w / label_h: Dimensiones del QLabel en píxeles.
        pixmap_w / pixmap_h: Dimensiones del QPixmap escalado en píxeles.

    Returns:
        Tupla (x1_n, y1_n, x2_n, y2_n) normalizadas, o None si el rect es inválido.
    """
    off_x = (label_w - pixmap_w) // 2
    off_y = (label_h - pixmap_h) // 2

    rx1 = max(0.0, (q_rect.left() - off_x) / pixmap_w)
    ry1 = max(0.0, (q_rect.top() - off_y) / pixmap_h)
    rx2 = min(1.0, (q_rect.right() - off_x) / pixmap_w)
    ry2 = min(1.0, (q_rect.bottom() - off_y) / pixmap_h)

    if rx2 <= rx1 or ry2 <= ry1:
        return None

    return (rx1, ry1, rx2, ry2)


def roi_como_pixeles(roi: RoiNorm, frame_w: int, frame_h: int) -> tuple[int, int, int, int]:
    """
    Convierte coordenadas ROI normalizadas a píxeles del frame.

    Args:
        roi: Tupla normalizada (x1_n, y1_n, x2_n, y2_n).
        frame_w / frame_h: Dimensiones del frame en píxeles.

    Returns:
        Tupla (x1_px, y1_px, x2_px, y2_px) en píxeles.
    """
    x1n, y1n, x2n, y2n = roi
    return (
        int(x1n * frame_w),
        int(y1n * frame_h),
        int(x2n * frame_w),
        int(y2n * frame_h),
    )
