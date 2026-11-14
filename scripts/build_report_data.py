"""Turn one month of raw Play Store reviews into the small JSON files the leadership dashboard reads.

Themes are keyword matches on reviews with real text (a review can match more than one theme).
Quotes are masked for phone numbers, emails and long ids.
"""

import argparse
import csv
import json
import re
import statistics as st
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

MIN_TEXT = 20  # characters; shorter reviews count as star-only

COMPLAINTS = [
    ("support", "Customer support", "Customer Experience", r"support|customer care|customer service|\bchat\b|\bagent\b|helpline"),
    ("price", "Prices and fees", "Pricing and Monetisation", r"price|expensive|costly|overcharg|platform fee|delivery fee|charges?\b|\bfees?\b"),
    ("late", "Late delivery", "Delivery Operations", r"\blate\b|delay|on time|took \d+|hours?\b|\d+ ?min"),
    ("refund", "Refunds", "Customer Experience and Payments", r"refund"),
    ("missing", "Wrong or missing items", "Restaurant Operations", r"wrong (item|order|food)|missing|not received|didn.?t receive|never (arrived|received|delivered)|not delivered"),
    ("cancel", "Cancellations", "Delivery Operations", r"cancel"),
    ("quality", "Food quality", "Restaurant Partnerships", r"\bcold\b|stale|quality|taste|spoil|hair|insect|cockroach|raw\b|undercooked|rotten"),
    ("rider", "Delivery partner behaviour", "Delivery Fleet", r"rider|delivery (boy|guy|partner|person|executive)|valet|rude"),
    ("offers", "Coupons and offers", "Growth and Marketing", r"coupon|offer|discount|promo|cashback"),
    ("payment", "Payment failures", "Payments", r"payment|upi|money (was )?deducted|debited|wallet"),
]
PRAISE = [
    ("fast", "Fast delivery", r"fast|quick|on time|speedy|in time"),
    ("offers", "Offers and discounts", r"offer|discount|coupon|deal|cashback"),
    ("easy", "Easy to use", r"easy|smooth|user friendly|convenient|simple"),
    ("variety", "Choice of restaurants", r"variety|options|restaurants|choices"),
    ("food", "Tasty food", r"tasty|delicious|taste|fresh|\bhot\b"),
]
MASKS = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "[email]"),
    (re.compile(r"(\+?91[\s-]?)?\b\d{10}\b"), "[phone]"),
    (re.compile(r"\b\d{6,}\b"), "[id]"),
]


def mask(text: str) -> str:
    for pattern, repl in MASKS:
        text = pattern.sub(repl, text)
    return " ".join(text.split())


def load(path: Path) -> list[dict]:
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    if not rows:
        raise SystemExit(f"{path} has no reviews.")
    for r in rows:
        r["dt"] = datetime.strptime(r["at"], "%d-%m-%Y %H:%M")
        r["stars"] = int(r["score"])
        r["text"] = (r["content"] or "").strip()
        r["has_text"] = len(r["text"]) > MIN_TEXT
        r["thumbs"] = int(r["thumbsUpCount"] or 0)
        r["low"] = r["text"].lower()
    return rows


def share(n: int, d: int) -> float:
    return round(n / d * 100, 1) if d else 0.0


NEGATIVE = re.compile(r"worst|bad|never|pathetic|terrible|poor|fraud|disappoint|not good")


def pick_quotes(pool: list[dict], themes: list[str], used: set, k: int = 2, positive: bool = False) -> list[str]:
    """Prefer reviews that fit only this theme, then the most thumbs-up; never reuse a review."""
    def fits(r):
        return sum(1 for pat in themes if re.search(pat, r["low"]))
    fit = [r for r in pool if 60 <= len(r["text"]) <= 260 and r["reviewId"] not in used
           and not (positive and NEGATIVE.search(r["low"]))]
    fit.sort(key=lambda r: (fits(r), -r["thumbs"], -len(r["text"])))
    chosen = fit[:k]
    used.update(r["reviewId"] for r in chosen)
    return [mask(r["text"]) for r in chosen]


def build(rows: list[dict]) -> dict[str, list[dict]]:
    n = len(rows)
    text = [r for r in rows if r["has_text"]]
    star_only = [r for r in rows if not r["has_text"]]
    neg = [r for r in text if r["stars"] <= 2]
    pos = [r for r in text if r["stars"] >= 4]
    one = [r for r in rows if r["stars"] == 1]
    replied = [r for r in rows if r["replyContent"]]
    openings = Counter(r["replyContent"][:50] for r in replied)
    lag = [
        (datetime.strptime(r["repliedAt"], "%d-%m-%Y %H:%M") - r["dt"]).total_seconds() / 60
        for r in replied if r["repliedAt"]
    ]

    kpis = [{
        "first_day": min(r["dt"] for r in rows).strftime("%d-%m-%Y"),
        "last_day": max(r["dt"] for r in rows).strftime("%d-%m-%Y"),
        "days": len({r["dt"].date() for r in rows}),
        "reviews": n,
        "reviews_per_day": round(n / len({r["dt"].date() for r in rows})),
        "avg_rating": round(st.mean(r["stars"] for r in rows), 2),
        "one_star_share": share(len(one), n),
        "text_reviews": len(text),
        "text_share": share(len(text), n),
        "text_avg": round(st.mean(r["stars"] for r in text), 2),
        "star_only_avg": round(st.mean(r["stars"] for r in star_only), 2),
        "negative_text_reviews": len(neg),
        "positive_text_reviews": len(pos),
        "reply_rate": share(len(replied), n),
        "one_star_reply_rate": share(sum(1 for r in one if r["replyContent"]), len(one)),
        "one_star_unreplied": sum(1 for r in one if not r["replyContent"]),
        "top_template_share": share(openings.most_common(1)[0][1], len(replied)) if replied else 0.0,
        "top3_template_share": share(sum(c for _, c in openings.most_common(3)), len(replied)) if replied else 0.0,
        "median_reply_minutes": round(st.median(lag)) if lag else None,
    }]

    stars = [{"stars": s, "reviews": sum(1 for r in rows if r["stars"] == s),
              "share": share(sum(1 for r in rows if r["stars"] == s), n),
              "text_share": share(sum(1 for r in rows if r["stars"] == s and r["has_text"]),
                                  sum(1 for r in rows if r["stars"] == s))} for s in range(5, 0, -1)]

    used: set = set()
    complaint_pats = [c[3] for c in COMPLAINTS]
    praise_pats = [p[2] for p in PRAISE]
    loud = sorted(text, key=lambda r: -r["thumbs"])[:5]
    used.update(r["reviewId"] for r in loud)

    complaints = []
    for code, name, owner, pat in COMPLAINTS:
        hit = [r for r in neg if re.search(pat, r["low"])]
        q = pick_quotes(hit, complaint_pats, used)
        complaints.append({"code": code, "theme": name, "reviews": len(hit), "share": share(len(hit), len(neg)),
                           "owner": owner, "quote_1": q[0] if q else "", "quote_2": q[1] if len(q) > 1 else ""})
    complaints.sort(key=lambda c: -c["reviews"])

    praise = []
    for code, name, pat in PRAISE:
        hit = [r for r in pos if re.search(pat, r["low"])]
        q = pick_quotes(hit, praise_pats, used, 1, positive=True)
        praise.append({"code": code, "theme": name, "reviews": len(hit), "share": share(len(hit), len(pos)),
                       "quote": q[0] if q else ""})
    praise.sort(key=lambda p: -p["reviews"])

    by_hour = defaultdict(list)
    for r in rows:
        by_hour[r["dt"].hour].append(r["stars"])
    hours = [{"hour": h, "label": f"{h:02d}:00", "reviews": len(v), "avg_rating": round(st.mean(v), 2),
              "one_star_share": share(sum(1 for s in v if s == 1), len(v))} for h, v in sorted(by_hour.items())]

    by_day = defaultdict(list)
    for r in rows:
        by_day[r["dt"].strftime("%d-%m-%Y")].append(r["stars"])
    daily = [{"date": d, "reviews": len(v), "avg_rating": round(st.mean(v), 2),
              "one_star_share": share(sum(1 for s in v if s == 1), len(v))}
             for d, v in sorted(by_day.items(), key=lambda kv: datetime.strptime(kv[0], "%d-%m-%Y"))]

    by_ver = defaultdict(list)
    for r in rows:
        by_ver[r["appVersion"] or "Not given"].append(r["stars"])
    top_ver = sorted(by_ver.items(), key=lambda kv: -len(kv[1]))[:8]
    versions = [{"version": v, "reviews": len(s), "avg_rating": round(st.mean(s), 2),
                 "one_star_share": share(sum(1 for x in s if x == 1), len(s))} for v, s in top_ver]

    loudest = [{"rank": i + 1, "thumbs_up": r["thumbs"], "stars": r["stars"], "date": r["dt"].strftime("%d-%m-%Y"),
                "text": mask(r["text"])[:320]} for i, r in enumerate(loud)]

    return {"kpis": kpis, "stars": stars, "complaints": complaints, "praise": praise,
            "hours": hours, "daily": daily, "versions": versions, "loudest": loudest}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--label", "--month", dest="label", required=True,
                   help="the fetch label, e.g. 10-2026 or 01-10-2026_to_15-10-2026; reads data/raw/reviews_<label>.csv")
    args = p.parse_args()
    src = Path("data/raw") / f"reviews_{args.label}.csv"
    if not src.exists():
        raise SystemExit(f"{src} not found. Run fetch_reviews.py for this range first.")
    out = Path("data/report") / args.label
    out.mkdir(parents=True, exist_ok=True)
    code = Path(__file__).read_text(encoding="utf-8")
    for name, rows in build(load(src)).items():
        meta = [{"label": "build_report_data.py", "value": code, "type": "code", "lang": "python"},
                {"label": "Input", "value": src.name}]
        (out / f"{name}.json").write_text(json.dumps({"rows": rows, "meta": meta}, ensure_ascii=False, indent=1),
                                          encoding="utf-8")
        print(f"{name}: {len(rows)} rows")


if __name__ == "__main__":
    main()
