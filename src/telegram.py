import os
import requests

def send_telegram(text: str) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not token or not chat_id:
        print("[TELEGRAM] token/chat_id manquant (notifications désactivées)", flush=True)
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}

    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        print("[TELEGRAM] message envoyé", flush=True)
    except Exception as e:
        print(f"[TELEGRAM] erreur: {e}", flush=True)
