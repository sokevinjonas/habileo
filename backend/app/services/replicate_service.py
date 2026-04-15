import os
import requests

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

def generate_tryon(user_url, cloth_url):
    response = requests.post(
        "https://api.replicate.com/v1/predictions",
        headers={
            "Authorization": f"Token {REPLICATE_API_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "version": "MODEL_VERSION_ID",
            "input": {
                "person_image": user_url,
                "garment_image": cloth_url
            }
        }
    )

    data = response.json()

    # ⚠️ Replicate fonctionne async → faut récupérer le résultat
    prediction_url = data.get("urls", {}).get("get")

    return wait_for_result(prediction_url)


def wait_for_result(url):
    import time

    while True:
        res = requests.get(url).json()

        if res["status"] == "succeeded":
            return {"image": res["output"][0]}

        if res["status"] == "failed":
            return {"error": "Generation failed"}

        time.sleep(2)