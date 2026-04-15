from flask import Blueprint, request, jsonify
from app.services.replicate_service import generate_tryon
from app.services.storage_service import upload_image

tryon_bp = Blueprint("tryon", __name__)

@tryon_bp.route("/try-on", methods=["POST"])
def try_on():
    user_file = request.files.get("user")
    cloth_file = request.files.get("cloth")

    if not user_file or not cloth_file:
        return jsonify({"error": "Missing images"}), 400

    # Upload images
    user_url = upload_image(user_file)
    cloth_url = upload_image(cloth_file)

    # Call AI
    result = generate_tryon(user_url, cloth_url)

    return jsonify(result)