import time
import requests
from app.config import Config

REPLICATE_API_URL = "https://api.replicate.com/v1/predictions"


def generate_tryon(user_url: str, cloth_url: str, zone: str = "upper_body") -> dict:
    if not Config.REPLICATE_API_TOKEN:
        return {"error": "REPLICATE_API_TOKEN manquant"}
    if not Config.REPLICATE_MODEL_VERSION:
        return {"error": "REPLICATE_MODEL_VERSION manquant"}

    try:
        response = requests.post(
            REPLICATE_API_URL,
            headers={
                "Authorization": f"Token {Config.REPLICATE_API_TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "version": Config.REPLICATE_MODEL_VERSION,
                "input": {
                    "human_img": user_url,
                    "garm_img": cloth_url,
                    "garment_des": "clothing item",
                    "category": zone,
                    "crop": True,
                },
            },
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        return {"error": f"Appel Replicate échoué: {e}"}

    data = response.json()
    prediction_url = data.get("urls", {}).get("get")
    if not prediction_url:
        return {"error": "Réponse Replicate invalide", "raw": data}

    return wait_for_result(prediction_url)


def wait_for_result(url: str) -> dict:
    deadline = time.time() + Config.REPLICATE_TIMEOUT
    headers = {"Authorization": f"Token {Config.REPLICATE_API_TOKEN}"}

    while time.time() < deadline:
        try:
            res = requests.get(url, headers=headers, timeout=15).json()
        except requests.RequestException as e:
            return {"error": f"Polling Replicate échoué: {e}"}

        status = res.get("status")
        if status == "succeeded":
            output = res.get("output")
            image = output[0] if isinstance(output, list) and output else output
            return {"image": image}
        if status in ("failed", "canceled"):
            return {"error": res.get("error") or f"Génération {status}"}

        time.sleep(Config.REPLICATE_POLL_INTERVAL)

    return {"error": "Timeout dépassé en attendant Replicate"}
