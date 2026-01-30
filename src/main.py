import os
import time
from dotenv import load_dotenv

load_dotenv()

def main():
    env = os.getenv("EBAY_ENV", "sandbox")
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    print(f"[BOT] Démarré | EBAY_ENV={env} | DRY_RUN={dry_run}")
    print("[BOT] Pour l’instant, je tourne juste pour valider Docker + déploiement.\n")

    while True:
        print("[BOT] heartbeat...")
        time.sleep(30)

if __name__ == "__main__":
    main()

