import requests


def send_message(token: str, chat_id: str, text: str) -> None:
    token = (token or "").strip()
    chat_id = (chat_id or "").strip()

    if not token or not chat_id:
        print("[TELEGRAM] token/chat_id manquant (notifications désactivées)", flush=True)
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}

    r = requests.post(url, json=payload, timeout=20)
    r.raise_for_status()
    print("[TELEGRAM] message envoyé", flush=True)
