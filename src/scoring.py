from typing import Any, Dict, List, Tuple
import statistics

def _to_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0

def extract_price(item: Dict[str, Any]) -> float:
    price = item.get("price", {})
    return _to_float(price.get("value"))

def extract_currency(item: Dict[str, Any]) -> str:
    price = item.get("price", {})
    return str(price.get("currency", ""))

def extract_discount_percent(item: Dict[str, Any]) -> float:
    mp = item.get("marketingPrice", {})
    dp = mp.get("discountPercentage")
    if dp is not None:
        return _to_float(dp)
    original = mp.get("originalPrice", {})
    op = _to_float(original.get("value"))
    p = extract_price(item)
    if op > 0 and p > 0 and op >= p:
        return ((op - p) / op) * 100.0
    return 0.0

def extract_seller(item: Dict[str, Any]) -> Tuple[float, float]:
    seller = item.get("seller", {}) or {}
    feedback = _to_float(seller.get("feedbackScore"))
    positive = _to_float(seller.get("positiveFeedbackPercent"))
    return feedback, positive

def compute_market_median_price(items: List[Dict[str, Any]]) -> float:
    prices = [extract_price(x) for x in items if extract_price(x) > 0]
    if not prices:
        return 0.0
    return float(statistics.median(prices))

def score_item(item: Dict[str, Any], median_price: float) -> Tuple[int, Dict[str, Any]]:
    price = extract_price(item)
    discount = extract_discount_percent(item)
    feedback, positive = extract_seller(item)

    score = 0

    discount_score = 0
    if discount >= 10:
        discount_score = min(40, int(discount * 1.5))
    score += discount_score

    price_vs_med_score = 0
    if median_price > 0 and price > 0:
        ratio = price / median_price
        if ratio <= 0.70:
            price_vs_med_score = 30
        elif ratio <= 0.85:
            price_vs_med_score = 20
        elif ratio <= 1.00:
            price_vs_med_score = 10
        else:
            price_vs_med_score = 0
    score += price_vs_med_score

    seller_score = 0
    if positive >= 99:
        seller_score += 20
    elif positive >= 98:
        seller_score += 16
    elif positive >= 97:
        seller_score += 12
    elif positive >= 95:
        seller_score += 6

    if feedback >= 5000:
        seller_score += 10
    elif feedback >= 1000:
        seller_score += 8
    elif feedback >= 200:
        seller_score += 6
    elif feedback >= 50:
        seller_score += 3

    score += min(30, seller_score)

    buying_options = item.get("buyingOptions", []) or []
    format_score = 0
    if "FIXED_PRICE" in buying_options:
        format_score = 5
    score += format_score

    breakdown = {
        "price": price,
        "discount_percent": discount,
        "median_price": median_price,
        "seller_feedback": feedback,
        "seller_positive": positive,
        "discount_score": discount_score,
        "price_vs_median_score": price_vs_med_score,
        "seller_score": min(30, seller_score),
        "format_score": format_score,
        "total": score,
    }

    return int(score), breakdown
