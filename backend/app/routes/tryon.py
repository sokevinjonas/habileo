from flask import Blueprint, request, jsonify
from app.services.replicate_service import generate_tryon
from app.services.storage_service import upload_image
from app.utils.helpers import validate_user_photo, validate_garment_photo

tryon_bp = Blueprint("tryon", __name__)


@tryon_bp.route("/try-on", methods=["POST"])
def try_on():
    user_file = request.files.get("user")
    cloth_file = request.files.get("cloth")

    # Validate user photo
    ok, err = validate_user_photo(user_file)
    if not ok:
        return jsonify({"error": err, "field": "user"}), 400

    # Validate garment photo
    ok, err = validate_garment_photo(cloth_file)
    if not ok:
        return jsonify({"error": err, "field": "cloth"}), 400

    # Zone
    zone_raw = request.form.get("zone", "")
    if zone_raw not in ("haut", "bas", "tout"):
        return jsonify({"error": "Zone d'habillage invalide. Choisissez : haut, bas ou tout.", "field": "zone"}), 400

    zone_map = {"haut": "upper_body", "bas": "lower_body", "tout": "dresses"}
    zone = zone_map[zone_raw]

    # Upload to Cloudinary
    try:
        user_url = upload_image(user_file)
        cloth_url = upload_image(cloth_file)
    except Exception as e:
        return jsonify({"error": f"Erreur lors de l'upload des images: {e}"}), 502

    # Generate
    desc_map = {
        "upper_body": "Short Sleeve Round Neck T-shirt",
        "lower_body": "Trousers",
        "dresses": "Full body dress",
    }
    garment_desc = request.form.get("garment_desc", desc_map.get(zone, "garment"))

    result = generate_tryon(user_url, cloth_url, zone, garment_desc)
    status = 200 if "image" in result else 502
    return jsonify(result), status


@tryon_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})
