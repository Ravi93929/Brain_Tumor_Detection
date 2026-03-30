import json
import sqlite3
from datetime import datetime

import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import load_img, img_to_array

from config import Config


MODEL_CLASSES = Config.MODEL_CLASSES
MODEL_ERROR = None
model = None

try:
    model = tf.keras.models.load_model(
        Config.MODEL_PATH,
        compile=False,
        safe_mode=False
    )
except Exception as e:
    MODEL_ERROR = str(e)


def get_db():
    return sqlite3.connect(Config.DB_NAME)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def create_report_id(user_id):
    return f"NSAI-{datetime.now().strftime('%Y%m%d')}-{str(user_id).zfill(4)}"


def get_model_status():
    return model is not None, MODEL_ERROR


def get_result_texts(predicted_result, confidence=None):
    if predicted_result == "No Tumor":
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
        finding_text = f"The uploaded MRI image is most consistent with {predicted_result}."
        impression_text = (
            f"The model assigned the highest probability to {predicted_result}, indicating that the scan "
            f"contains image features most similar to this tumor category."
        )
        recommendation_text = (
            "This AI output should be considered a decision-support result only. "
            "Confirmatory review by a radiologist or medical specialist is strongly recommended."
        )
        status_badge = "Tumor Pattern Detected"

    return {
        "finding_text": finding_text,
        "impression_text": impression_text,
        "recommendation_text": recommendation_text,
        "status_badge": status_badge,
    }


def predict_tumor(image_path):
    if model is None:
        raise RuntimeError(f"Model unavailable: {MODEL_ERROR}")

    img = load_img(image_path, target_size=(Config.IMAGE_SIZE, Config.IMAGE_SIZE))
    img_array = img_to_array(img).astype("float32") / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    predictions = model.predict(img_array, verbose=0)[0]
    predicted_index = int(np.argmax(predictions))
    confidence_score = float(predictions[predicted_index])

    label_map = {
        "pituitary": "Pituitary Tumor",
        "glioma": "Glioma Tumor",
        "meningioma": "Meningioma Tumor",
        "notumor": "No Tumor"
    }

    predicted_label = MODEL_CLASSES[predicted_index]
    readable_result = label_map.get(predicted_label, predicted_label)

    probability_rows = []
    for i, cls in enumerate(MODEL_CLASSES):
        probability_rows.append({
            "class_name": label_map.get(cls, cls),
            "probability": round(float(predictions[i]) * 100, 2)
        })

    probability_rows.sort(key=lambda x: x["probability"], reverse=True)
    return readable_result, confidence_score, probability_rows


def save_prediction_result(user_id, report_id, image_filename, predicted_class, confidence, probability_rows):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO prediction_history (
            user_id, report_id, image_filename, predicted_class,
            confidence, probability_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        report_id,
        image_filename,
        predicted_class,
        confidence,
        json.dumps(probability_rows),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    inserted_id = cursor.lastrowid
    conn.close()
    return inserted_id


def save_prediction(user_id, report_id, image_filename, predicted_class, confidence, probability_rows):
    return save_prediction_result(
        user_id=user_id,
        report_id=report_id,
        image_filename=image_filename,
        predicted_class=predicted_class,
        confidence=confidence,
        probability_rows=probability_rows,
    )


def get_user_prediction_history(user_id, limit=10):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, report_id, image_filename, predicted_class, confidence, created_at
        FROM prediction_history
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_prediction_report(prediction_id, user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, report_id, image_filename, predicted_class, confidence,
               probability_json, created_at
        FROM prediction_history
        WHERE id = ? AND user_id = ?
    """, (prediction_id, user_id))
    row = cursor.fetchone()
    conn.close()
    return row