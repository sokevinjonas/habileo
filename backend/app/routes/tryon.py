from flask import Blueprint, request, jsonify
from app.services.replicate_service import generate_tryon
from app.services.storage_service import upload_image
from app.utils.helpers import validate_image

tryon_bp = Blueprint("tryon", __name__)


@tryon_bp.route("/try-on", methods=["POST"])
def try_on():
    user_file = request.files.get("user")
    cloth_file = request.files.get("cloth")

    for label, f in (("user", user_file), ("cloth", cloth_file)):
        ok, err = validate_image(f)
        if not ok:
            return jsonify({"error": f"{label}: {err}"}), 400

    try:
        user_url = upload_image(user_file)
        cloth_url = upload_image(cloth_file)
    except Exception as e:
        return jsonify({"error": f"Upload Cloudinary échoué: {e}"}), 502

    zone_map = {"haut": "upper_body", "bas": "lower_body", "tout": "dresses"}
    zone = zone_map.get(request.form.get("zone", "haut"), "upper_body")

    result = generate_tryon(user_url, cloth_url, zone)
    status = 200 if "image" in result else 502
    return jsonify(result), status


@tryon_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})
