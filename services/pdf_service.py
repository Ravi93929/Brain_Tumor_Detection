import json
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from config import Config


def wrap_text(text, font_name, font_size, max_width):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        trial = f"{current} {word}".strip()
        if stringWidth(trial, font_name, font_size) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines



def build_pdf_report(report_data, fullname):
    prediction_id, report_id, image_filename, predicted_class, confidence, probability_json, created_at = report_data
    probability_rows = json.loads(probability_json) if probability_json else []

    if predicted_class == "No Tumor":
        finding_text = "No tumor pattern detected in the uploaded MRI image."
        impression_text = (
            "The model classified the scan into the no-tumor category with a relatively high confidence score. "
            "This suggests absence of visible tumor-related features in the uploaded image."
        )
        recommendation_text = (
            "This AI result is supportive only and should not be treated as a final diagnosis. "
            "Clinical correlation and radiologist review are still recommended."
        )
        status_badge = "No Tumor Detected"
    else:
        finding_text = f"The uploaded MRI image is most consistent with {predicted_class}."
        impression_text = (
            f"The model assigned the highest probability to {predicted_class}, indicating that the scan "
            f"contains image features most similar to this tumor category."
        )
        recommendation_text = (
            "This AI output should be considered a decision-support result only. "
            "Confirmatory review by a radiologist or medical specialist is strongly recommended."
        )
        status_badge = "Tumor Pattern Detected"

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 45
    y = height - 45

    def draw_line():
        nonlocal y
        pdf.setStrokeColorRGB(0.82, 0.88, 0.94)
        pdf.line(margin, y, width - margin, y)
        y -= 14

    def draw_title(text, size=20):
        nonlocal y
        pdf.setFont("Helvetica-Bold", size)
        pdf.drawString(margin, y, text)
        y -= size + 8

    def draw_label_value(label, value):
        nonlocal y
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(margin, y, f"{label}:")
        pdf.setFont("Helvetica", 11)
        pdf.drawString(margin + 110, y, str(value))
        y -= 18

    def draw_paragraph(text):
        nonlocal y
        lines = wrap_text(text, "Helvetica", 11, width - 2 * margin)
        pdf.setFont("Helvetica", 11)
        for line in lines:
            if y < 70:
                pdf.showPage()
                y = height - 45
            pdf.drawString(margin, y, line)
            y -= 15
        y -= 4

    def draw_probability_table(rows):
        nonlocal y
        col1 = margin
        col2 = margin + 250
        col3 = margin + 360

        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(col1, y, "Class")
        pdf.drawString(col2, y, "Probability")
        pdf.drawString(col3, y, "Strength")
        y -= 16

        pdf.setFont("Helvetica", 11)
        for row in rows:
            if y < 80:
                pdf.showPage()
                y = height - 45
            pdf.drawString(col1, y, row["class_name"])
            pdf.drawString(col2, y, f'{row["probability"]:.2f}%')
            bar_width = 120
            fill_width = min(bar_width, (row["probability"] / 100.0) * bar_width)
            pdf.rect(col3, y - 6, bar_width, 8, stroke=1, fill=0)
            pdf.setFillColorRGB(0.01, 0.52, 0.78)
            pdf.rect(col3, y - 6, fill_width, 8, stroke=0, fill=1)
            pdf.setFillColorRGB(0, 0, 0)
            y -= 18
        y -= 6

    pdf.setTitle(f"{report_id}.pdf")
    draw_title("NeuroScan AI Medical Prediction Report", 18)
    pdf.setFont("Helvetica", 11)
    pdf.drawString(margin, y, "AI-generated MRI classification summary")
    y -= 10
    draw_line()

    draw_title("Report Summary", 14)
    draw_label_value("Report ID", report_id)
    draw_label_value("Prediction ID", prediction_id)
    draw_label_value("Patient / User", fullname)
    draw_label_value("Scan Date & Time", created_at)
    draw_label_value("Uploaded File", image_filename)
    draw_label_value("Model Name", Config.MODEL_NAME)
    draw_label_value("Model Type", Config.MODEL_TYPE)
    draw_label_value("Model Version", Config.MODEL_VERSION)
    draw_label_value("Input Size", f"{Config.IMAGE_SIZE} x {Config.IMAGE_SIZE}")
    draw_label_value("Status", status_badge)

    draw_line()
    draw_title("Primary Finding", 14)
    draw_label_value("Predicted Class", predicted_class)
    draw_label_value("Confidence Score", f"{confidence * 100:.2f}%")
    draw_paragraph(finding_text)

    draw_line()
    draw_title("Impression", 14)
    draw_paragraph(impression_text)

    draw_line()
    draw_title("Recommendation", 14)
    draw_paragraph(recommendation_text)

    draw_line()
    draw_title("Class Probability Analysis", 14)
    draw_probability_table(probability_rows)

    draw_line()
    draw_title("Important Note", 14)
    draw_paragraph(
        "This report is generated by an AI-based classification model and is intended only for academic, "
        "research, or decision-support use. It is not a substitute for professional radiological or clinical diagnosis."
    )

    pdf.save()
    buffer.seek(0)
    return buffer
