import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"

    # Replicate
    REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
    REPLICATE_MODEL_VERSION = os.getenv("REPLICATE_MODEL_VERSION")
    REPLICATE_POLL_INTERVAL = float(os.getenv("REPLICATE_POLL_INTERVAL", "2"))
    REPLICATE_TIMEOUT = int(os.getenv("REPLICATE_TIMEOUT", "120"))

    # Cloudinary
    CLOUDINARY_URL = os.getenv("CLOUDINARY_URL")
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

    # Uploads
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
