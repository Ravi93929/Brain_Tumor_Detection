import os

from flask import Flask

from config import Config
from database.db import init_db
from routes.auth_routes import auth_bp
from routes.main_routes import main_bp
from routes.prediction_routes import prediction_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = Config.SECRET_KEY

    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    init_db()


    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(prediction_bp)
    return app


app = create_app()

if __name__ == "__main__":
    if Config.USE_HTTPS:
        app.run(debug=True, use_reloader=False, ssl_context="adhoc")
    else:
        app.run(debug=True, use_reloader=False)
