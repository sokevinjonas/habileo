from flask import Flask
from flask_cors import CORS
from app.config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)

    from app.routes.tryon import tryon_bp
    app.register_blueprint(tryon_bp, url_prefix="/api")

    return app
