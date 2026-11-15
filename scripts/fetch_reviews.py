"""Fetch one calendar month of Google Play reviews for an app and save them as CSV.

Uses google-play-scraper (open source, MIT, reads the public Play Store page, no login).
For production on our own app, swap this for the Play Console monthly reviews export.
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from google_play_scraper import Sort, app, reviews

FIELDS = ["reviewId", "at", "score", "content", "thumbsUpCount", "appVersion", "replyContent", "repliedAt"]
BATCH = 200


def month_bounds(month: str) -> tuple[datetime, datetime]:
    start = datetime.strptime(month, "%m-%Y")
    end = start.replace(year=start.year + 1, month=1) if start.month == 12 else start.replace(month=start.month + 1)
    return start, end


def previous_month() -> str:
    now = datetime.now()
    return f"12-{now.year - 1}" if now.month == 1 else f"{now.month - 1:02d}-{now.year}"


def fetch(app_id: str, lang: str, country: str, start: datetime, end: datetime) -> list[dict]:
    seen: dict[str, dict] = {}
    token = None
    while True:
        batch, token = reviews(
            app_id, lang=lang, country=country, sort=Sort.NEWEST, count=BATCH, continuation_token=token
        )
        if not batch:
            break
        for r in batch:
            if start <= r["at"] < end:
                seen[r["reviewId"]] = r
        oldest = min(r["at"] for r in batch)
        print(f"  kept {len(seen)} reviews, oldest in batch {oldest:%d-%m-%Y %H:%M}", file=sys.stderr)
        if oldest < start or token is None:
            break
    return sorted(seen.values(), key=lambda r: r["at"], reverse=True)


def save_store(app_id: str, lang: str, country: str, path: Path) -> None:
    """Save the rating the Play Store shows today. It is recency-weighted by Google (formula unpublished) and
    specific to the country, so it is a snapshot at fetch time, not a figure for the period."""
    a = app(app_id, lang=lang, country=country)
    snap = {"store_rating": round(a["score"], 2), "store_ratings_total": a["ratings"],
            "store_histogram": a["histogram"], "store_version": a["version"], "country": country,
            "snapshot_at": datetime.now().strftime("%d-%m-%Y %H:%M")}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, indent=1), encoding="utf-8")
    print(f"Store rating {snap['store_rating']} from {snap['store_ratings_total']:,} ratings, saved to {path}")


def save(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            out = {k: r.get(k) for k in FIELDS}
            for k in ("at", "repliedAt"):
                if out[k]:
                    out[k] = out[k].strftime("%d-%m-%Y %H:%M")
            w.writerow(out)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--app-id", default="com.application.zomato")
    p.add_argument("--month", default=previous_month(), help="MM-YYYY (default: last month)")
    p.add_argument("--from-month", help="MM-YYYY, first month of a range (use with --to-month)")
    p.add_argument("--to-month", help="MM-YYYY, last month of a range, inclusive")
    p.add_argument("--from-date", help="DD-MM-YYYY, first day of a range (use with --to-date)")
    p.add_argument("--to-date", help="DD-MM-YYYY, last day of a range, inclusive")
    p.add_argument("--lang", default="en")
    p.add_argument("--country", default="in")
    p.add_argument("--out", type=Path, help="CSV path (default: data/raw/reviews_<MM-YYYY>.csv)")
    p.add_argument("--store-only", action="store_true",
                   help="only save today's Play Store rating to data/raw/store_<label>.json, skip the reviews")
    args = p.parse_args()

    if bool(args.from_month) != bool(args.to_month) or bool(args.from_date) != bool(args.to_date):
        sys.exit("Pass both ends of a range: --from-month with --to-month, or --from-date with --to-date.")
    if args.from_month and args.from_date:
        sys.exit("Use a month range or a date range, not both.")
    if args.from_date:
        start = datetime.strptime(args.from_date, "%d-%m-%Y")
        end = datetime.strptime(args.to_date, "%d-%m-%Y") + timedelta(days=1)
        if start >= end:
            sys.exit("--from-date must be on or before --to-date.")
        if end > datetime.now() + timedelta(days=1):
            sys.exit("--to-date is in the future.")
        label = f"{args.from_date}_to_{args.to_date}"
    elif args.from_month:
        start, end = month_bounds(args.from_month)[0], month_bounds(args.to_month)[1]
        if start >= end:
            sys.exit("--from-month must be on or before --to-month.")
        label = f"{args.from_month}_to_{args.to_month}"
    else:
        start, end = month_bounds(args.month)
        label = args.month
    out = args.out or Path("data/raw") / f"reviews_{label}.csv"
    default_app = args.app_id == p.get_default("app_id")
    store_path = (Path("data/raw") / f"store_{label}.json" if default_app
                  else out.with_name(f"store_{args.app_id}_{label}.json"))
    save_store(args.app_id, args.lang, args.country, store_path)
    if args.store_only:
        return
    print(f"Fetching {label} {args.lang}-{args.country} reviews for {args.app_id}", file=sys.stderr)
    rows = fetch(args.app_id, args.lang, args.country, start, end)
    if not rows:
        sys.exit("No reviews returned for that month. The scraper may be blocked or the app id is wrong.")
    save(rows, out)

    stars = {s: sum(1 for r in rows if r["score"] == s) for s in range(5, 0, -1)}
    avg = sum(r["score"] for r in rows) / len(rows)
    print(f"Saved {len(rows)} reviews to {out}")
    print(f"Range {rows[-1]['at']:%d-%m-%Y} to {rows[0]['at']:%d-%m-%Y} | Average {avg:.2f} | "
          + " ".join(f"{s}*: {n}" for s, n in stars.items()))


if __name__ == "__main__":
    main()
