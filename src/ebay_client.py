import os
import base64
import requests
from typing import Any, Dict, List, Optional, Tuple

OAUTH_PROD = "https://api.ebay.com/identity/v1/oauth2/token"
OAUTH_SANDBOX = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"

BROWSE_PROD = "https://api.ebay.com/buy/browse/v1/item_summary/search"
BROWSE_SANDBOX = "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search"

SCOPE = "https://api.ebay.com/oauth/api_scope"

def _env() -> str:
    return os.getenv("EBAY_ENV", "production").strip().lower()

def _oauth_url() -> str:
    return OAUTH_SANDBOX if _env() == "sandbox" else OAUTH_PROD

def _browse_url() -> str:
    return BROWSE_SANDBOX if _env() == "sandbox" else BROWSE_PROD

def get_app_access_token() -> Tuple[str, int]:
    client_id = os.getenv("EBAY_CLIENT_ID", "").strip()
    client_secret = os.getenv("EBAY_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        raise RuntimeError("EBAY_CLIENT_ID / EBAY_CLIENT_SECRET manquant")

    auth = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("utf-8")
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "client_credentials",
        "scope": SCOPE,
    }

    r = requests.post(_oauth_url(), headers=headers, data=data, timeout=20)
    r.raise_for_status()
    j = r.json()
    token = j["access_token"]
    expires_in = int(j.get("expires_in", 7200))
    return token, expires_in

def search_items(token: str) -> List[Dict[str, Any]]:
    marketplace_id = os.getenv("EBAY_MARKETPLACE_ID", "EBAY_FR").strip()
    q = os.getenv("EBAY_SEARCH_QUERY", "").strip()
    if not q:
        raise RuntimeError("EBAY_SEARCH_QUERY manquant")

    limit = int(os.getenv("EBAY_LIMIT", "50"))
    min_price = os.getenv("EBAY_MIN_PRICE", "").strip()
    max_price = os.getenv("EBAY_MAX_PRICE", "").strip()
    condition = os.getenv("EBAY_CONDITION", "NEW_OR_USED").strip()

    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": marketplace_id,
    }

    params: Dict[str, Any] = {
        "q": q,
        "limit": max(1, min(limit, 200)),
    }

    filters = []
    if min_price or max_price:
        if not min_price:
            min_price = "0"
        if not max_price:
            max_price = "999999"
        filters.append(f"price:[{min_price}..{max_price}]")
    if condition and condition != "NEW_OR_USED":
        filters.append(f"conditionIds:{condition}")

    if filters:
        params["filter"] = ",".join(filters)

    r = requests.get(_browse_url(), headers=headers, params=params, timeout=20)
    r.raise_for_status()
    j = r.json()
    return j.get("itemSummaries", []) or []
