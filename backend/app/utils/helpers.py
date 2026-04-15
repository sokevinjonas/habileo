from app.config import Config


def allowed_file(filename: str) -> bool:
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in Config.ALLOWED_EXTENSIONS


def validate_image(file_storage):
    if file_storage is None:
        return False, "Fichier manquant"
    if not allowed_file(file_storage.filename):
        return False, f"Extension non supportée (autorisées: {', '.join(Config.ALLOWED_EXTENSIONS)})"
    return True, None
