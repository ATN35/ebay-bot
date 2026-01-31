import os
import time
from datetime import datetime
from dotenv import load_dotenv

from telegram import send_message
from ebay_oauth import get_oauth_token

load_dotenv()

DATA_DIR = os.path.join(os.getcwd(), "data")
LOG_PATH = os.path.join(DATA_DIR, "bot.log")


def log(msg: str) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    line = f"{datetime.now().isoformat()} | {msg}\n"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)
    print(msg, flush=True)


def main() -> None:
    env = os.getenv("EBAY_ENV", "sandbox").strip().lower()
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    tg_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    log(f"[BOT] start | EBAY_ENV={env} | DRY_RUN={dry_run}")

    # 1) Test Telegram
    try:
        send_message(tg_token, tg_chat_id, "✅ Bot démarré (test Telegram OK)")
    except Exception as e:
        log(f"[TELEGRAM] erreur: {e}")

    # 2) Test OAuth eBay
    try:
        token, expires_in = get_oauth_token(env)
        log(f"[EBAY] OAuth OK | expires_in={expires_in}s | token_prefix={token[:12]}...")
        try:
            send_message(tg_token, tg_chat_id, f"✅ eBay OAuth OK (env={env}, expires_in={expires_in}s)")
        except Exception as e:
            log(f"[TELEGRAM] erreur notif eBay: {e}")
    except Exception as e:
        log(f"[EBAY] OAuth ERROR: {e}")
        try:
            send_message(tg_token, tg_chat_id, f"❌ eBay OAuth ERROR (env={env}): {e}")
        except Exception as ee:
            log(f"[TELEGRAM] erreur notif eBay: {ee}")

    # Heartbeat
    while True:
        log("[BOT] heartbeat")
        time.sleep(10)


if __name__ == "__main__":
    main()
