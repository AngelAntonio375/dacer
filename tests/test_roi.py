"""
tests/test_roi.py
Pruebas para el módulo src/roi_utils.py
Verifica la lógica de inclusión/exclusión de detecciones dentro del ROI.
"""

import pytest
from src.roi_utils import box_en_roi, roi_como_pixeles


class TestBoxEnRoi:
    def test_sin_roi_siempre_true(self):
        """Sin ROI definido, cualquier box debe pasar."""
        assert box_en_roi([0, 0, 100, 100], 1920, 1080, None) is True

    def test_centro_dentro_del_roi(self):
        """Box cuyo centro está dentro del ROI debe retornar True."""
        # ROI: cuadrante superior izquierdo (0-50% en x, 0-50% en y)
        roi = (0.0, 0.0, 0.5, 0.5)
        # Box con centro en (25%, 25%) del frame 1920x1080
        box = [0, 0, 480, 270]  # centro: (240, 135) → (12.5%, 12.5%)
        assert box_en_roi(box, 1920, 1080, roi) is True

    def test_centro_fuera_del_roi(self):
        """Box cuyo centro está fuera del ROI debe retornar False."""
        roi = (0.0, 0.0, 0.5, 0.5)
        # Box en la esquina inferior derecha
        box = [1440, 810, 1920, 1080]  # centro: (1680, 945) → (87.5%, 87.5%)
        assert box_en_roi(box, 1920, 1080, roi) is False

    def test_centro_en_borde_roi(self):
        """Centro exactamente en el borde del ROI debe ser True (bordes inclusivos)."""
        roi = (0.0, 0.0, 0.5, 0.5)
        # Box con centro exactamente en (50%, 50%)
        box = [480, 270, 1440, 810]  # centro: (960, 540) → (50%, 50%)
        assert box_en_roi(box, 1920, 1080, roi) is True

    def test_roi_frame_completo(self):
        """ROI que cubre el 100% del frame debe aceptar cualquier box."""
        roi = (0.0, 0.0, 1.0, 1.0)
        box = [0, 0, 1920, 1080]
        assert box_en_roi(box, 1920, 1080, roi) is True


class TestRoiComoPixeles:
    def test_conversion_correcta(self):
        """La conversión de normalizadas a píxeles debe ser exacta."""
        roi = (0.25, 0.25, 0.75, 0.75)
        x1, y1, x2, y2 = roi_como_pixeles(roi, 1920, 1080)
        assert x1 == 480
        assert y1 == 270
        assert x2 == 1440
        assert y2 == 810

    def test_roi_completo_a_pixeles(self):
        roi = (0.0, 0.0, 1.0, 1.0)
        x1, y1, x2, y2 = roi_como_pixeles(roi, 1920, 1080)
        assert x1 == 0
        assert y1 == 0
        assert x2 == 1920
        assert y2 == 1080
