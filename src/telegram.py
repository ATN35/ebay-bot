import os
import requests
from typing import Optional

API_BASE = "https://api.telegram.org"

def send_telegram(message: str) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not token or not chat_id:
        print("[TELEGRAM] token/chat_id manquant (notifications désactivées)", flush=True)
        return False

    url = f"{API_BASE}/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "disable_web_page_preview": True,
    }

    try:
        r = requests.post(url, json=payload, timeout=15)
        r.raise_for_status()
        print("[TELEGRAM] message envoyé", flush=True)
        return True
    except Exception as e:
        print(f"[TELEGRAM] erreur: {e}", flush=True)
        return False
