import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import List

API_BASE = "https://api.telegram.org"

DEFAULT_TIMEOUT = float(os.getenv("TELEGRAM_TIMEOUT_SECONDS", "15"))
MAX_MESSAGE_LENGTH = 4096

def _build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("POST",),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

_SESSION = _build_session()

def _chunk_message(message: str) -> List[str]:
    if len(message) <= MAX_MESSAGE_LENGTH:
        return [message]
    chunks = []
    start = 0
    while start < len(message):
        end = min(start + MAX_MESSAGE_LENGTH, len(message))
        chunks.append(message[start:end])
        start = end
    return chunks

def send_telegram(message: str) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not token or not chat_id:
        print("[TELEGRAM] token/chat_id manquant (notifications désactivées)", flush=True)
        return False

    url = f"{API_BASE}/bot{token}/sendMessage"

    try:
        for chunk in _chunk_message(message):
            payload = {
                "chat_id": chat_id,
                "text": chunk,
                "disable_web_page_preview": True,
            }
            r = _SESSION.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
            if r.status_code == 429:
                retry_after = r.headers.get("Retry-After", "")
                print(f"[TELEGRAM] rate limit (Retry-After={retry_after})", flush=True)
                r.raise_for_status()
            r.raise_for_status()
        print("[TELEGRAM] message envoyé", flush=True)
        return True
    except Exception as e:
        detail = getattr(e, "response", None)
        if detail is not None:
            try:
                print(f"[TELEGRAM] erreur: {e} | body={detail.text}", flush=True)
            except Exception:
                print(f"[TELEGRAM] erreur: {e}", flush=True)
        else:
            print(f"[TELEGRAM] erreur: {e}", flush=True)
        return False
