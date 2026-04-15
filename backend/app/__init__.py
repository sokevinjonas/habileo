from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)

    from app.routes.tryon import tryon_bp
    app.register_blueprint(tryon_bp, url_prefix="/api")

    return app