import os
import uuid
from datetime import datetime

from flask import Blueprint, current_app, flash, redirect, render_template, request, send_file, send_from_directory, session, url_for
from werkzeug.utils import secure_filename

from config import Config
from services.common import allowed_file, login_required
from services.pdf_service import build_pdf_report
from services.prediction_service import (
    create_report_id,
    get_model_status,
    get_prediction_report,
    get_result_texts,
    get_user_prediction_history,
    predict_tumor,
    save_prediction,
)

prediction_bp = Blueprint("prediction", __name__)


@prediction_bp.route("/predict", methods=["GET", "POST"])
@login_required
def predict_page():
    user_id = session.get("user_id")
    fullname = session.get("fullname", "User")
    result_data = None
    model_ready, model_error = get_model_status()

    if request.method == "POST":
        if not model_ready:
            flash(f"Model is not available: {model_error}", "danger")
            return redirect(url_for("prediction.predict_page"))

        if "file" not in request.files:
            flash("No file part found.", "danger")
            return redirect(url_for("prediction.predict_page"))

        file = request.files["file"]
        if file.filename == "":
            flash("Please choose an image file.", "warning")
            return redirect(url_for("prediction.predict_page"))

        if not allowed_file(file.filename):
            flash("Only PNG, JPG, and JPEG files are allowed.", "danger")
            return redirect(url_for("prediction.predict_page"))

        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_filename)
        file.save(filepath)

        predicted_result, confidence, probability_rows = predict_tumor(filepath)
        report_id = create_report_id(user_id)
        prediction_id = save_prediction(user_id, report_id, unique_filename, predicted_result, confidence, probability_rows)
        scan_time = datetime.now().strftime("%d-%m-%Y %I:%M %p")
        texts = get_result_texts(predicted_result)

        result_data = {
            "report_id": report_id,
            "prediction_id": prediction_id,
            "scan_time": scan_time,
            "uploaded_filename": filename,
            "unique_filename": unique_filename,
            "predicted_result": predicted_result,
            "confidence": confidence,
            "probability_rows": probability_rows,
            **texts,
        }

    history_rows = get_user_prediction_history(user_id, limit=10)
    return render_template(
        "predict.html",
        config=Config,
        fullname=fullname,
        result_data=result_data,
        history_rows=history_rows,
        model_ready=model_ready,
        model_error=model_error,
    )


@prediction_bp.route("/report/<int:prediction_id>/pdf")
@login_required
def download_report_pdf(prediction_id):
    user_id = session.get("user_id")
    fullname = session.get("fullname", "User")

    report_data = get_prediction_report(prediction_id, user_id)
    if not report_data:
        flash("Report not found.", "danger")
        return redirect(url_for("prediction.predict_page"))

    pdf_buffer = build_pdf_report(report_data, fullname)
    report_id = report_data[1] or f"report_{prediction_id}"
    return send_file(pdf_buffer, as_attachment=True, download_name=f"{report_id}.pdf", mimetype="application/pdf")


@prediction_bp.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)
