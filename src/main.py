import os
import time
from datetime import datetime
from dotenv import load_dotenv

from telegram import send_telegram
from ebay_client import get_app_access_token, search_items
from scoring import compute_market_median_price, score_item
from storage import log, load_seen, save_seen, save_snapshot

def _env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() == "true"

def main() -> None:
    load_dotenv()

    env = os.getenv("EBAY_ENV", "production").strip().lower()
    dry_run = _env_bool("DRY_RUN", "true")

    interval = int(os.getenv("SCAN_INTERVAL_SECONDS", "120"))
    min_score = int(os.getenv("TELEGRAM_MIN_SCORE", "70"))

    min_discount = float(os.getenv("EBAY_MIN_DISCOUNT_PERCENT", "0"))
    seller_min_positive = float(os.getenv("SELLER_MIN_POSITIVE", "0"))
    seller_min_feedback = float(os.getenv("SELLER_MIN_FEEDBACK", "0"))

    log(f"[BOT] start | EBAY_ENV={env} | DRY_RUN={dry_run} | interval={interval}s | min_score={min_score}")

    seen = load_seen()
    token = ""
    token_exp_at = 0.0

    while True:
        try:
            now = time.time()
            if not token or now >= token_exp_at - 60:
                t, expires_in = get_app_access_token()
                token = t
                token_exp_at = now + float(expires_in)
                log(f"[EBAY] OAuth OK | expires_in={expires_in}s | token_prefix={token[:14]}...")
                send_telegram(f"✅ eBay OAuth OK ({env})")

            items = search_items(token)
            if not items:
                log("[SCAN] 0 item")
                time.sleep(interval)
                continue

            median_price = compute_market_median_price(items)

            alerts = []
            enriched = []

            for item in items:
                item_id = str(item.get("itemId", "")).strip()
                title = str(item.get("title", "")).strip()
                url = str(item.get("itemWebUrl", "")).strip()

                score, breakdown = score_item(item, median_price)

                seller_feedback = float(breakdown.get("seller_feedback", 0))
                seller_positive = float(breakdown.get("seller_positive", 0))
                discount = float(breakdown.get("discount_percent", 0))

                enriched.append({
                    "itemId": item_id,
                    "title": title,
                    "url": url,
                    "score": score,
                    "breakdown": breakdown,
                    "raw": item,
                })

                if not item_id:
                    continue
                if item_id in seen:
                    continue

                if discount < min_discount:
                    continue
                if seller_positive < seller_min_positive:
                    continue
                if seller_feedback < seller_min_feedback:
                    continue

                if score >= min_score:
                    alerts.append((item_id, title, url, score, breakdown))

            snapshot_path = save_snapshot(enriched)
            log(f"[SCAN] items={len(items)} | median={median_price:.2f} | alerts={len(alerts)} | snapshot={snapshot_path}")

            if alerts:
                alerts.sort(key=lambda x: x[3], reverse=True)
                for (item_id, title, url, score, breakdown) in alerts[:10]:
                    msg = (
                        f"🔥 Opportunité détectée (score {score})\n"
                        f"{title}\n"
                        f"{url}\n"
                        f"Remise: {breakdown.get('discount_percent', 0):.1f}% | "
                        f"Prix: {breakdown.get('price', 0)} | "
                        f"Vendeur: {breakdown.get('seller_positive', 0)}% / {int(breakdown.get('seller_feedback', 0))}"
                    )

                    if dry_run:
                        log(f"[ALERT][DRY_RUN] {title} | score={score} | {url}")
                    else:
                        send_telegram(msg)

                    seen.add(item_id)

                save_seen(seen)

            log("[BOT] heartbeat")
        except Exception as e:
            log(f"[ERROR] {e}")

        time.sleep(interval)

if __name__ == "__main__":
    main()
