"""
src/pdf_export.py
Generación de reportes PDF de incidentes con ReportLab.
Las imágenes se descifran en memoria antes de incluirlas en el reporte.
"""

import io
import cv2
import numpy as np
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

from src.database import obtener_incidentes, conteo_por_objeto, contar_incidentes, obtener_imagen_incidente


def exportar_reporte_pdf(filtro: str = "") -> str:
    """
    Genera un PDF con los incidentes registrados en la base de datos.

    Args:
        filtro: Cadena de búsqueda para filtrar por objeto o fecha (vacío = todos).

    Returns:
        Ruta absoluta del archivo PDF generado.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta = f"reporte_incidentes_{timestamp}.pdf"

    doc = SimpleDocTemplate(
        ruta, pagesize=letter,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()

    titulo_style = ParagraphStyle(
        "titulo", parent=styles["Title"],
        fontSize=20, spaceAfter=6,
        textColor=colors.HexColor("#1a237e"),
    )
    sub_style = ParagraphStyle(
        "sub", parent=styles["Normal"],
        fontSize=10, textColor=colors.grey, spaceAfter=20,
    )
    info_style = ParagraphStyle(
        "info", parent=styles["Normal"],
        fontSize=9, textColor=colors.HexColor("#333333"),
    )

    story = []

    # Encabezado
    story.append(Paragraph("REPORTE DE INCIDENTES DE VIGILANCIA", titulo_style))
    story.append(Paragraph(
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}  |  Sistema: DaCer",
        sub_style,
    ))

    sep = Table([[""]], colWidths=[6.5 * inch], rowHeights=[4])
    sep.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1a237e"))]))
    story.append(sep)
    story.append(Spacer(1, 14))

    # Resumen
    total = contar_incidentes()
    conteos = conteo_por_objeto()

    story.append(Paragraph(f"<b>Total de incidentes registrados:</b> {total}", info_style))
    story.append(Spacer(1, 6))

    if conteos:
        resumen_data = [["Objeto Detectado", "Cantidad"]]
        for obj, cnt in conteos:
            resumen_data.append([obj, str(cnt)])
        t_resumen = Table(resumen_data, colWidths=[3 * inch, 1.5 * inch])
        t_resumen.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f5f5f5"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(t_resumen)

    story.append(Spacer(1, 20))

    # Detalle de incidentes con imagen
    story.append(Paragraph("<b>DETALLE DE INCIDENTES</b>", info_style))
    story.append(Spacer(1, 8))

    incidentes = _obtener_incidentes_con_imagen(filtro)
    for rec_id, fecha, objeto, img_cifrada in incidentes:
        data = [
            ["ID", "Fecha y Hora", "Objeto Detectado"],
            [str(rec_id), fecha, objeto],
        ]
        t_inc = Table(data, colWidths=[0.6 * inch, 2.2 * inch, 3.7 * inch])
        t_inc.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#37474f")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#eceff1")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#b0bec5")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(t_inc)

        if img_cifrada:
            try:
                from PIL import Image as PILImage
                nparr = np.frombuffer(img_cifrada, np.uint8)
                img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
                pil_img = PILImage.fromarray(img_rgb)
                buf = io.BytesIO()
                pil_img.save(buf, format="JPEG", quality=70)
                buf.seek(0)
                story.append(RLImage(buf, width=5 * inch, height=2.8 * inch))
            except Exception:
                story.append(Paragraph("[Imagen no disponible]", styles["Italic"]))

        story.append(Spacer(1, 14))

    doc.build(story)
    return ruta


def _obtener_incidentes_con_imagen(filtro: str) -> list[tuple]:
    """Consulta incidentes con su imagen cifrada para el reporte."""
    import sqlite3
    from src.database import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, fecha, objeto, imagen_cifrada FROM incidentes "
        "WHERE objeto LIKE ? OR fecha LIKE ? ORDER BY id DESC",
        (f"%{filtro}%", f"%{filtro}%"),
    )
    rows = cursor.fetchall()
    conn.close()
    # Descifrar imágenes
    result = []
    from src.crypto import cipher_suite
    for rec_id, fecha, objeto, img_cifrada in rows:
        img_bytes = None
        if img_cifrada:
            try:
                img_bytes = cipher_suite.decrypt(img_cifrada)
            except Exception:
                pass
        result.append((rec_id, fecha, objeto, img_bytes))
    return result
