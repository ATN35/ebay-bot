import base64
import os
import requests


def get_oauth_token(env: str) -> tuple[str, int]:
    """
    Retourne (access_token, expires_in).
    Utilise le Client Credentials Grant (app token).
    """
    client_id = os.getenv("EBAY_CLIENT_ID", "").strip()
    client_secret = os.getenv("EBAY_CLIENT_SECRET", "").strip()

    if not client_id or not client_secret:
        raise RuntimeError("EBAY_CLIENT_ID/EBAY_CLIENT_SECRET manquants")

    base_url = "https://api.sandbox.ebay.com" if env == "sandbox" else "https://api.ebay.com"
    url = f"{base_url}/identity/v1/oauth2/token"

    # Scope “général” (suffisant pour Browse / recherche / lecture)
    scope = "https://api.ebay.com/oauth/api_scope"

    basic = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("utf-8")

    headers = {
        "Authorization": f"Basic {basic}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "grant_type": "client_credentials",
        "scope": scope,
    }

    r = requests.post(url, headers=headers, data=data, timeout=20)
    r.raise_for_status()
    payload = r.json()

    token = payload.get("access_token")
    expires_in = int(payload.get("expires_in", 0))

    if not token:
        raise RuntimeError(f"Réponse OAuth invalide: {payload}")

    return token, expires_in
