import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path=ENV_PATH, override=True)


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev_secret_change_me")
    BASE_DIR = BASE_DIR

    MODEL_PATH = os.path.join(BASE_DIR, "models", "model_fixed.keras")
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    DB_NAME = os.path.join(BASE_DIR, "users.db")

    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
    IMAGE_SIZE = 128

    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    USE_HTTPS = os.getenv("USE_HTTPS", "0") == "1"

    DEBUG_OTP_MODE = str(os.getenv("DEBUG_OTP_MODE", "False")).strip().lower() == "true"

    MODEL_NAME = "Brain Tumor Classification Model"
    MODEL_TYPE = "VGG16 + Transfer Learning"
    MODEL_VERSION = "v3.0 Medical Report PDF"
    DATASET_INFO = "MRI brain scans classified into pituitary, glioma, meningioma, and no tumor"
    MODEL_CLASSES = ["notumor", "glioma", "pituitary", "meningioma"]

    OTP_EXPIRE_MINUTES = 5
    OTP_RESEND_COOLDOWN_SECONDS = 60
    OTP_MAX_VERIFY_ATTEMPTS = 5
    OTP_MAX_RESEND_PER_WINDOW = 3
    OTP_RESEND_WINDOW_MINUTES = 15

    RESET_OTP_EXPIRE_MINUTES = 10
    RESET_MAX_VERIFY_ATTEMPTS = 5

    HERO_IMAGE_URL = "https://images.unsplash.com/photo-1559757175-5700dde675bc?auto=format&fit=crop&w=1600&q=80"