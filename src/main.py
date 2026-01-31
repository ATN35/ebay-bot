import os
import time
from datetime import datetime
from dotenv import load_dotenv

from telegram import send_telegram

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
    env = os.getenv("EBAY_ENV", "sandbox")
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    log(f"[BOT] start | EBAY_ENV={env} | DRY_RUN={dry_run}")
    send_telegram("🚀 Bot eBay démarré (test Telegram OK)")

    while True:
        log("[BOT] heartbeat")
        time.sleep(10)

if __name__ == "__main__":
    main()
