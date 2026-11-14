"""Render the leadership email for one Play Store Pulse period.

Reads data/report/<label>/: kpis.json, complaints.json, loudest.json, narrative.json (the dashboard's asks)
and email.json (written by Claude, see references/email-content.md). Numbers go in as tokens and are
filled from the data, so the email always matches the dashboard.

Writes data/report/<label>/email/: subject.txt, email.txt (plain text) and email.html (paste-ready).
"""

import argparse
import html
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

TOKEN = re.compile(r"\[\[(?:([0-9_to-]+):)?([a-z_]+)\.([a-z_0-9]+)(?:@([a-z_]+)=([^|\]]+)|#(\d+))?\|([a-z0-9]+)\]\]")
FORMATS = {
    "int": lambda v: f"{int(v):,}",
    "pct": lambda v: f"{float(v):.1f}%",
    "dec2": lambda v: f"{float(v):.2f}",
    "min": lambda v: f"{v} min",
    "text": str,
}
MAX_SUBJECT = 70
MAX_WORDS = 200
WINDOWS = {"early": (0, 8), "morning": (8, 12), "afternoon": (12, 20), "night": (20, 24)}


def load(label: str) -> dict:
    base = Path("data/report") / label
    if not base.exists():
        sys.exit(f"{base} not found. Run /play-store-pulse for {label} first.")
    data = {}
    for f in base.glob("*.json"):
        if f.stem in ("narrative", "email", "blobs"):
            continue
        data[f.stem] = json.loads(f.read_text(encoding="utf-8"))["rows"]
    hours = data.get("hours", [])
    data["windows"] = []
    for name, (a, b) in WINDOWS.items():
        hs = [h for h in hours if a <= h["hour"] < b]
        n = sum(h["reviews"] for h in hs)
        data["windows"].append({"window": name, "reviews": n,
                                "avg_rating": round(sum(h["avg_rating"] * h["reviews"] for h in hs) / n, 2) if n else None})
    return data


def expand(text: str, label: str, cache: dict) -> str:
    def one(m):
        lab, src, field, wk, wv, row, fmt = m.groups()
        lab = lab or label
        if lab not in cache:
            cache[lab] = load(lab)
        rows = cache[lab].get(src)
        if rows is None:
            sys.exit(f"{m.group(0)}: no {src} data for {lab}")
        if fmt not in FORMATS:
            sys.exit(f"{m.group(0)}: unknown format {fmt!r}")
        if wk:
            hit = [r for r in rows if str(r.get(wk)) == wv]
            if len(hit) != 1:
                sys.exit(f"{m.group(0)}: {len(hit)} {src} rows where {wk}={wv} in {lab}")
            r = hit[0]
        else:
            i = int(row or 0)
            if i >= len(rows):
                sys.exit(f"{m.group(0)}: {src} has no row {i} in {lab}")
            r = rows[i]
        if field not in r or r[field] is None:
            sys.exit(f"{m.group(0)}: {src} has no value for {field!r} in {lab}")
        return FORMATS[fmt](r[field])

    out = TOKEN.sub(one, text)
    if "[[" in out:
        sys.exit(f"Malformed token in: {text}")
    return out


def check_words(text: str, where: str) -> None:
    if "—" in text:
        sys.exit(f"Em dash in {where}. Use a comma or a full stop.")
    if re.search(r"\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}", text):
        sys.exit(f"Date not in DD-MM-YYYY in {where}.")


def raw_numbers(text: str) -> list[str]:
    """Numbers typed by hand (outside tokens), left for a human check. Versions, dates and '1-star' are fine."""
    t = TOKEN.sub("", text)
    t = re.sub(r"\b\d+\.\d+\.\d+\b|\b\d{2}-\d{2}(-\d{4})?\b|\b\d-star\b", "", t)
    return re.findall(r"\d(?:[\d,.]*\d)?%?", t)


def working_days_from(start: date, n: int) -> date:
    d = start
    while n:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def dashboard_url(label: str) -> str | None:
    log = Path("data/report/run-log.md")
    if not log.exists():
        return None
    url = None
    for line in log.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 5 and cells[1] == label and cells[4].startswith("https://claude.ai/"):
            url = cells[4]
    return url


def trim(text: str, limit: int = 160) -> str:
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(",.;: ")
    return cut + "..."


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--label", required=True)
    p.add_argument("--reply-by", help="DD-MM-YYYY (default: 5 working days from today)")
    p.add_argument("--dashboard", help="dashboard url (default: from data/report/run-log.md)")
    args = p.parse_args()

    base = Path("data/report") / args.label
    cache = {args.label: load(args.label)}
    narrative = json.loads((base / "narrative.json").read_text(encoding="utf-8"))
    email_path = base / "email.json"
    if not email_path.exists():
        sys.exit(f"{email_path} not found. Write it first (see references/email-content.md).")
    email = json.loads(email_path.read_text(encoding="utf-8"))

    for key in ("subject", "bottom_line", "why_it_matters", "numbers", "quote"):
        if not email.get(key):
            sys.exit(f"email.json needs {key!r}")
    if not 2 <= len(email["numbers"]) <= 4:
        sys.exit("email.json needs 2 to 4 numbers")

    reply_by = (datetime.strptime(args.reply_by, "%d-%m-%Y").date() if args.reply_by
                else working_days_from(date.today(), 5))
    url = args.dashboard or dashboard_url(args.label)
    if not url:
        sys.exit("No dashboard url. Pass --dashboard or log the run in data/report/run-log.md.")

    ex = lambda t: expand(t, args.label, cache)
    subject = ex(email["subject"])
    bottom = ex(email["bottom_line"])
    why = ex(email["why_it_matters"])
    numbers = [ex(n) for n in email["numbers"]]
    asks = [(a["owner"], a["title"]) for a in narrative.get("actions", [])]
    if len(asks) != 3:
        sys.exit("narrative.json must hold the dashboard's 3 actions")

    q = email["quote"]
    src, _, key = q.partition(":")
    rows = cache[args.label][src] if src in ("complaints", "loudest") else sys.exit("quote must be complaints:<code> or loudest:<rank>")
    if src == "complaints":
        hit = [r for r in rows if r["code"] == key]
        quote = hit[0]["quote_1"] if hit else ""
    else:
        hit = [r for r in rows if str(r["rank"]) == key]
        quote = hit[0]["text"] if hit else ""
    if not quote:
        sys.exit(f"No quote found for {q}")
    quote = trim(quote)

    for name, text in [("subject", subject), ("bottom_line", bottom), ("why_it_matters", why), *[(f"number {i}", n) for i, n in enumerate(numbers, 1)]]:
        check_words(text, name)
    if len(subject) > MAX_SUBJECT:
        sys.exit(f"Subject is {len(subject)} characters; keep it under {MAX_SUBJECT}: {subject}")

    rb = reply_by.strftime("%d-%m-%Y")
    lines = [
        f"Bottom line: {bottom}", "",
        f"Why it matters: {why}", "",
        "The numbers", *[f"- {n}" for n in numbers], "",
        f"Three asks (reply by {rb})", *[f"{i}. {o}: {t}" for i, (o, t) in enumerate(asks, 1)], "",
        f'In their words: "{quote}"', "",
        f"Go deeper: {url}", "",
        "Reply with a different owner if one of these sits with another team.",
    ]
    text = "\n".join(lines)
    words = len(re.findall(r"\S+", text.replace(url, "")))
    if words > MAX_WORDS:
        sys.exit(f"Email body is {words} words; keep it under {MAX_WORDS}. Shorten bottom_line, why_it_matters or numbers.")

    e = html.escape
    label = lambda t: f'<p style="margin:16px 0 4px;font-weight:600;color:#1C1C1C">{e(t)}</p>'
    body = f"""<div style="font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;font-size:14px;line-height:1.5;color:#1C1C1C;max-width:600px">
<p style="margin:0 0 4px;font-size:12px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:#CF4A57">Play Store Pulse</p>
<p style="margin:0 0 12px"><strong>Bottom line:</strong> {e(bottom)}</p>
<p style="margin:0 0 12px"><strong>Why it matters:</strong> {e(why)}</p>
{label("The numbers")}<ul style="margin:0;padding-left:20px">{''.join(f'<li>{e(n)}</li>' for n in numbers)}</ul>
{label(f"Three asks (reply by {rb})")}<ol style="margin:0;padding-left:20px">{''.join(f'<li><strong>{e(o)}:</strong> {e(t)}</li>' for o, t in asks)}</ol>
{label("In their words")}<p style="margin:0;padding:8px 12px;border-left:3px solid #EF4F5F;background:#FFF6F7;color:#414A5D">"{e(quote)}"</p>
<p style="margin:16px 0 4px"><strong>Go deeper:</strong> <a href="{e(url)}" style="color:#CF4A57">open the dashboard</a></p>
<p style="margin:16px 0 0;color:#596378">Reply with a different owner if one of these sits with another team.</p>
</div>"""

    out = base / "email"
    out.mkdir(exist_ok=True)
    (out / "subject.txt").write_text(subject + "\n", encoding="utf-8")
    (out / "email.txt").write_text(text + "\n", encoding="utf-8")
    (out / "email.html").write_text(body + "\n", encoding="utf-8")
    print(f"Subject ({len(subject)} chars): {subject}")
    print(f"Body: {words} words, reply by {rb}, dashboard {url}")
    typed = sorted(set(n for t in (email["subject"], email["bottom_line"], email["why_it_matters"], *email["numbers"]) for n in raw_numbers(t)))
    if typed:
        print(f"Typed numbers to check by hand (not from tokens): {', '.join(typed)}")
    print(f"Wrote {out}/subject.txt, email.txt, email.html")


if __name__ == "__main__":
    main()
