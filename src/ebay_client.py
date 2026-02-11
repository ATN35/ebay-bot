import os
import base64
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Any, Dict, List, Tuple

OAUTH_PROD = "https://api.ebay.com/identity/v1/oauth2/token"
OAUTH_SANDBOX = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"

BROWSE_PROD = "https://api.ebay.com/buy/browse/v1/item_summary/search"
BROWSE_SANDBOX = "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search"

SCOPE = "https://api.ebay.com/oauth/api_scope"

DEFAULT_TIMEOUT = float(os.getenv("EBAY_TIMEOUT_SECONDS", "20"))

def _build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "POST"),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

_SESSION = _build_session()

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

    r = _SESSION.post(_oauth_url(), headers=headers, data=data, timeout=DEFAULT_TIMEOUT)
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

    try:
        limit = int(os.getenv("EBAY_LIMIT", "50"))
    except Exception:
        limit = 50
    min_price = os.getenv("EBAY_MIN_PRICE", "").strip()
    max_price = os.getenv("EBAY_MAX_PRICE", "").strip()
    condition = os.getenv("EBAY_CONDITION", "NEW_OR_USED").strip()
    sort = os.getenv("EBAY_SORT", "").strip().upper()
    category_ids = os.getenv("EBAY_CATEGORY_IDS", "").strip()

    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": marketplace_id,
    }

    params: Dict[str, Any] = {
        "q": q,
        "limit": max(1, min(limit, 200)),
    }

    allowed_sorts = {
        "BEST_MATCH",
        "ENDING_SOONEST",
        "NEWLY_LISTED",
        "PRICE_PLUS_SHIPPING_LOWEST",
        "PRICE_PLUS_SHIPPING_HIGHEST",
        "DISTANCE_NEAREST",
        "BEST_SELLING",
    }
    if sort and sort in allowed_sorts:
        params["sort"] = sort

    if category_ids:
        cleaned = ",".join([c.strip() for c in category_ids.split(",") if c.strip()])
        if cleaned:
            params["category_ids"] = cleaned

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

    r = _SESSION.get(_browse_url(), headers=headers, params=params, timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    j = r.json()
    return j.get("itemSummaries", []) or []
