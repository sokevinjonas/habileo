import cloudinary
import cloudinary.uploader
from app.config import Config


def _configure():
    if Config.CLOUDINARY_URL:
        # cloudinary lit CLOUDINARY_URL automatiquement via env
        return
    if Config.CLOUDINARY_CLOUD_NAME:
        cloudinary.config(
            cloud_name=Config.CLOUDINARY_CLOUD_NAME,
            api_key=Config.CLOUDINARY_API_KEY,
            api_secret=Config.CLOUDINARY_API_SECRET,
            secure=True,
        )


_configure()


def upload_image(file) -> str:
    result = cloudinary.uploader.upload(file, folder="habileo")
    return result["secure_url"]
