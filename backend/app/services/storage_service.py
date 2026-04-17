import re
import cloudinary
import cloudinary.uploader
import cloudinary.api
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


# ─── Sanitize device_id pour usage comme nom de dossier ───
_SAFE = re.compile(r"[^a-zA-Z0-9_-]")


def _safe_device_id(device_id: str) -> str:
    """Strip dangerous chars; device_id max 64 chars."""
    clean = _SAFE.sub("", device_id or "")[:64]
    return clean or "anonymous"


# ─── Upload ───

def upload_image(file, folder: str = "habileo/temp") -> str:
    """Upload a file/stream to Cloudinary and return the secure URL."""
    result = cloudinary.uploader.upload(file, folder=folder)
    return result["secure_url"]


def save_tryon_result(image_url: str, device_id: str, label: str = "") -> dict:
    """
    Re-upload the final try-on result into the user's gallery folder.
    Returns the uploaded resource info.
    """
    device = _safe_device_id(device_id)
    folder = f"habileo/users/{device}"

    context = {"label": label} if label else {}

    result = cloudinary.uploader.upload(
        image_url,
        folder=folder,
        context=context,
        resource_type="image",
    )
    return {
        "id": result["public_id"],
        "url": result["secure_url"],
        "created_at": result.get("created_at"),
    }


# ─── Gallery listing ───

def list_user_gallery(device_id: str, max_results: int = 50) -> list[dict]:
    """List all images saved under the user's folder, most recent first."""
    device = _safe_device_id(device_id)
    prefix = f"habileo/users/{device}/"

    res = cloudinary.api.resources(
        type="upload",
        prefix=prefix,
        max_results=max_results,
        context=True,
    )

    resources = res.get("resources", [])
    # Cloudinary returns most-recent-first by default when using the search API,
    # but resources() can vary. Sort by created_at desc to be safe.
    resources.sort(key=lambda r: r.get("created_at", ""), reverse=True)

    return [
        {
            "id": r["public_id"],
            "url": r["secure_url"],
            "date": r.get("created_at"),
            "label": (r.get("context", {}).get("custom", {}) or {}).get("label", ""),
        }
        for r in resources
    ]


def delete_gallery_item(device_id: str, public_id: str) -> bool:
    """Delete an image from the user's gallery. Public_id must start with user's prefix."""
    device = _safe_device_id(device_id)
    prefix = f"habileo/users/{device}/"

    if not public_id.startswith(prefix):
        return False  # ne peut pas supprimer un item d'un autre user

    result = cloudinary.uploader.destroy(public_id)
    return result.get("result") == "ok"
