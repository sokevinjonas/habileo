import time
import logging
import requests
from app.config import Config

log = logging.getLogger(__name__)

REPLICATE_API_URL = "https://api.replicate.com/v1/predictions"

# Model version for background removal
REMOVE_BG_VERSION = "95fcc2a26d3899cd6c2691c900465aaeff466285a65c14638cc5f36f34befaf1"


def _headers():
    return {
        "Authorization": f"Token {Config.REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }


def _run_model(version: str, model_input: dict, label: str, max_retries: int = 3) -> dict:
    """Run a Replicate model and wait for the result, with retry on 429."""
    for attempt in range(max_retries):
        try:
            response = requests.post(
                REPLICATE_API_URL,
                headers=_headers(),
                json={"version": version, "input": model_input},
                timeout=30,
            )
            if response.status_code == 429 and attempt < max_retries - 1:
                wait = (attempt + 1) * 5
                log.warning("%s: rate limit (429), retry dans %ds...", label, wait)
                time.sleep(wait)
                continue
            response.raise_for_status()
            break
        except requests.RequestException as e:
            if attempt < max_retries - 1 and "429" in str(e):
                time.sleep((attempt + 1) * 5)
                continue
            return {"error": f"{label}: appel échoué — {e}"}

    data = response.json()
    prediction_url = data.get("urls", {}).get("get")
    if not prediction_url:
        return {"error": f"{label}: réponse invalide", "raw": data}

    return _wait_for_result(prediction_url, label)


def _wait_for_result(url: str, label: str) -> dict:
    """Poll a prediction until completion."""
    deadline = time.time() + Config.REPLICATE_TIMEOUT
    headers = {"Authorization": f"Token {Config.REPLICATE_API_TOKEN}"}

    while time.time() < deadline:
        try:
            res = requests.get(url, headers=headers, timeout=15).json()
        except requests.RequestException as e:
            return {"error": f"{label}: polling échoué — {e}"}

        status = res.get("status")
        if status == "succeeded":
            output = res.get("output")
            image = output[0] if isinstance(output, list) and output else output
            return {"image": image}
        if status in ("failed", "canceled"):
            return {"error": res.get("error") or f"{label}: génération {status}"}

        time.sleep(Config.REPLICATE_POLL_INTERVAL)

    return {"error": f"{label}: timeout dépassé"}


# ─── STEP 1: Remove background from garment ───────────────────────

def remove_background(image_url: str) -> dict:
    """Remove background from garment image for cleaner try-on."""
    log.info("Pipeline étape 1/2 — Nettoyage du vêtement")
    return _run_model(
        version=REMOVE_BG_VERSION,
        model_input={"image": image_url},
        label="Nettoyage vêtement",
    )


# ─── STEP 2: IDM-VTON try-on ──────────────────────────────────────

def idm_vton(user_url: str, garment_url: str, zone: str, garment_desc: str) -> dict:
    """Run IDM-VTON virtual try-on."""
    log.info("Pipeline étape 2/2 — Essayage virtuel IDM-VTON")
    return _run_model(
        version=Config.REPLICATE_MODEL_VERSION,
        model_input={
            "human_img": user_url,
            "garm_img": garment_url,
            "garment_des": garment_desc,
            "category": zone,
            "crop": True,
            "steps": 40,
            "seed": 0,
        },
        label="Essayage virtuel",
    )


# ─── MAIN PIPELINE ────────────────────────────────────────────────

def generate_tryon(user_url: str, cloth_url: str, zone: str = "upper_body", garment_desc: str = "garment") -> dict:
    """
    2-step try-on pipeline:
    1. Remove background from garment image (isolate garment)
    2. Run IDM-VTON with cleaned garment

    Step 1 is resilient — if it fails, we proceed with the original image.
    """
    if not Config.REPLICATE_API_TOKEN:
        return {"error": "REPLICATE_API_TOKEN manquant"}
    if not Config.REPLICATE_MODEL_VERSION:
        return {"error": "REPLICATE_MODEL_VERSION manquant"}

    # ── Step 1: Clean garment image ──
    bg_result = remove_background(cloth_url)
    if "error" in bg_result:
        log.warning("Step 1 échoué, on continue avec l'image originale: %s", bg_result["error"])
        clean_garment_url = cloth_url
    else:
        clean_garment_url = bg_result["image"]
        log.info("Step 1 OK — vêtement nettoyé: %s", clean_garment_url)

    # ── Step 2: IDM-VTON try-on ──
    tryon_result = idm_vton(user_url, clean_garment_url, zone, garment_desc)
    if "error" in tryon_result:
        return tryon_result

    log.info("Step 2 OK — essayage généré")
    return tryon_result
