from flask import Blueprint, render_template

from config import Config

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    return render_template("home.html", config=Config)
