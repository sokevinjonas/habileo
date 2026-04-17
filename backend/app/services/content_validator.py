"""
Content validation using moondream2 VLM.
Ensures uploaded images match expected content before running expensive try-on.
"""
import time
import logging
import requests
from app.config import Config

log = logging.getLogger(__name__)

REPLICATE_API_URL = "https://api.replicate.com/v1/predictions"
MOONDREAM_VERSION = "72ccb656353c348c1385df54b237eeb7bfa874bf11486cf0b9473e691b662d31"


def _run_vlm(image_url: str, prompt: str) -> str:
    """Run moondream2 and return the text response."""
    headers = {
        "Authorization": f"Token {Config.REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    try:
        r = requests.post(
            REPLICATE_API_URL,
            headers=headers,
            json={"version": MOONDREAM_VERSION, "input": {"image": image_url, "prompt": prompt}},
            timeout=30,
        )
        r.raise_for_status()
    except requests.RequestException as e:
        log.warning("Validator VLM call failed: %s", e)
        return ""

    get_url = r.json().get("urls", {}).get("get")
    if not get_url:
        return ""

    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            res = requests.get(get_url, headers=headers, timeout=10).json()
        except requests.RequestException:
            return ""

        status = res.get("status")
        if status == "succeeded":
            output = res.get("output")
            if isinstance(output, list):
                return " ".join(str(x) for x in output).strip().lower()
            return str(output or "").strip().lower()
        if status in ("failed", "canceled"):
            return ""
        time.sleep(1.5)

    return ""


def validate_user_content(image_url: str) -> tuple[bool, str | None]:
    """
    Check that the image contains a full-body or upper-body photo of a person.
    Returns (is_valid, error_message).
    """
    prompt = (
        "Does this image show a full person (not just face, not an object)? "
        "Answer only with 'yes' or 'no' followed by a brief reason."
    )
    answer = _run_vlm(image_url, prompt)
    log.info("User photo check: %s", answer[:200])

    if not answer:
        # Validator unavailable — don't block, let user proceed
        return True, None

    if answer.startswith("no") or "no," in answer[:10]:
        return False, (
            "L'image ne semble pas contenir une personne visible. "
            "Veuillez uploader une photo en pied d'une personne (pas un objet, un animal ou un paysage)."
        )

    return True, None


def validate_garment_content(image_url: str) -> tuple[bool, str | None]:
    """
    Check that the image contains a piece of clothing/garment.
    Returns (is_valid, error_message).
    """
    prompt = (
        "Is this image showing a piece of clothing or a garment "
        "(shirt, pants, dress, jacket, etc.)? Answer only with 'yes' or 'no' followed by a brief reason."
    )
    answer = _run_vlm(image_url, prompt)
    log.info("Garment photo check: %s", answer[:200])

    if not answer:
        return True, None

    if answer.startswith("no") or "no," in answer[:10]:
        return False, (
            "L'image ne semble pas contenir un vêtement. "
            "Veuillez uploader une photo d'une pièce de vêtement (chemise, pantalon, robe, veste, etc.)."
        )

    return True, None
