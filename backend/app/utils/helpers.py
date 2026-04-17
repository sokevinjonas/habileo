from io import BytesIO
from PIL import Image
from app.config import Config

MIN_WIDTH = 300
MIN_HEIGHT = 400
MAX_WIDTH = 4096
MAX_HEIGHT = 4096


def allowed_file(filename: str) -> bool:
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in Config.ALLOWED_EXTENSIONS


def validate_image(file_storage):
    if file_storage is None:
        return False, "Fichier manquant"
    if not allowed_file(file_storage.filename):
        exts = ", ".join(Config.ALLOWED_EXTENSIONS)
        return False, f"Format non supporté. Formats acceptés : {exts}"
    return True, None


def validate_user_photo(file_storage):
    """Validate the user (person) photo for try-on quality."""
    ok, err = validate_image(file_storage)
    if not ok:
        return False, err

    try:
        file_storage.seek(0)
        img = Image.open(BytesIO(file_storage.read()))
        file_storage.seek(0)
        w, h = img.size
    except Exception:
        return False, "Impossible de lire l'image. Le fichier est peut-être corrompu."

    if w < MIN_WIDTH or h < MIN_HEIGHT:
        return False, (
            f"Image trop petite ({w}x{h}). "
            f"Minimum requis : {MIN_WIDTH}x{MIN_HEIGHT} pixels. "
            "Utilisez une photo de meilleure qualité."
        )

    if w > MAX_WIDTH or h > MAX_HEIGHT:
        return False, (
            f"Image trop grande ({w}x{h}). "
            f"Maximum : {MAX_WIDTH}x{MAX_HEIGHT} pixels."
        )

    ratio = h / w
    if ratio < 1.0:
        return False, (
            "La photo doit être en portrait (verticale). "
            "Votre image est en paysage (horizontale). "
            "Prenez une photo debout, en pied."
        )

    return True, None


def validate_garment_photo(file_storage):
    """Validate the garment (clothing) photo."""
    ok, err = validate_image(file_storage)
    if not ok:
        return False, err

    try:
        file_storage.seek(0)
        img = Image.open(BytesIO(file_storage.read()))
        file_storage.seek(0)
        w, h = img.size
    except Exception:
        return False, "Impossible de lire l'image du vêtement. Fichier corrompu."

    if w < 200 or h < 200:
        return False, (
            f"Image du vêtement trop petite ({w}x{h}). "
            "Minimum requis : 200x200 pixels."
        )

    if w > MAX_WIDTH or h > MAX_HEIGHT:
        return False, (
            f"Image du vêtement trop grande ({w}x{h}). "
            f"Maximum : {MAX_WIDTH}x{MAX_HEIGHT} pixels."
        )

    return True, None
