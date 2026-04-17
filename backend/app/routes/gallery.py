import logging
from flask import Blueprint, request, jsonify
from app.services.storage_service import list_user_gallery, delete_gallery_item

log = logging.getLogger(__name__)

gallery_bp = Blueprint("gallery", __name__)


@gallery_bp.route("/gallery", methods=["GET"])
def get_gallery():
    """Return all images saved for a given device_id."""
    device_id = request.args.get("device_id", "").strip()
    if not device_id:
        return jsonify({"error": "device_id requis"}), 400

    try:
        items = list_user_gallery(device_id)
    except Exception as e:
        log.exception("Failed to list gallery")
        return jsonify({"error": f"Erreur Cloudinary: {e}"}), 502

    return jsonify({"items": items, "count": len(items)})


@gallery_bp.route("/gallery/<path:public_id>", methods=["DELETE"])
def delete_gallery(public_id):
    """Delete a specific image from user's gallery."""
    device_id = request.args.get("device_id", "").strip()
    if not device_id:
        return jsonify({"error": "device_id requis"}), 400

    try:
        ok = delete_gallery_item(device_id, public_id)
    except Exception as e:
        log.exception("Failed to delete gallery item")
        return jsonify({"error": f"Erreur Cloudinary: {e}"}), 502

    if not ok:
        return jsonify({"error": "Image introuvable ou accès refusé"}), 404

    return jsonify({"ok": True})
