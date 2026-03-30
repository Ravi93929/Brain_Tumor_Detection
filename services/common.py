from datetime import datetime
from functools import wraps

from flask import flash, redirect, session, url_for
from config import Config


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def parse_dt(value):
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("auth.login"))
        return func(*args, **kwargs)

    return wrapper
