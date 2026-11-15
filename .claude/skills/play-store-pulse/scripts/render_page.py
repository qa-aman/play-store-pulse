"""Fill the Play Store Pulse dashboard template for one period and write the store documents for the artifact.

Inputs (all under data/report/<label>/ by default):
  *.json         the 8 summary files from build_report_data.py
  narrative.json the words Claude writes for this period (see references/narrative.md)
  blobs.json     the /_blob/ urls the Artifact upload returned, keyed by file stem

Output: data/report/<label>/artifact/ with one JSON file per store document, plus writes.json,
the exact `writes` list for one ArtifactData batch call.
"""

import argparse
import calendar
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL / "assets" / "dashboard.html"
DATASETS = {
    "kpis": ("Headline numbers", "Review count, ratings, text share, reply figures and the Play Store rating snapshot"),
    "stars": ("Reviews by star rating", "Count and share of reviews at each star rating, and how many of each have text"),
    "complaints": ("Complaint themes", "Keyword-matched themes in written 1 and 2-star reviews, with a suggested owner and one masked quote each"),
    "praise": ("Praise themes", "Keyword-matched themes in written 4 and 5-star reviews"),
    "hours": ("Rating by hour", "Reviews, average rating and 1-star share for each hour of the day, IST"),
    "daily": ("Rating by day", "Reviews, average rating and 1-star share for each day"),
    "versions": ("Rating by app version", "The 8 app versions with the most reviews"),
    "loudest": ("Most agreed-with reviews", "The 5 written reviews with the most thumbs-up, masked for personal details"),
}
FONTS = {"okra-regular": 400, "okra-medium": 500, "okra-semibold": 600}
CALCS = {  # calcs declared in the page: their fields and key values
    "windows": ({"window", "label", "reviews", "avg_rating"}, {"window": {"early", "morning", "afternoon", "night"}}),
    "worst_days": ({"rank", "date", "one_star_share", "reviews"}, {}),
}
FORMATS = {"int", "pct", "dec2", "min"}
TOKEN = re.compile(r"\[\[([a-z_]+)\.([a-z_0-9]+)(?:@([a-z_]+)=([^|\]]+)|#(\d+))?\|([a-z0-9]+)\]\]")


def period(label: str) -> tuple[str, str]:
    """Return (short label, phrase used after 'told us')."""
    month = lambda s: datetime.strptime(s, "%m-%Y")
    if re.fullmatch(r"\d{2}-\d{4}", label):
        m = month(label)
        name = f"{calendar.month_name[m.month]} {m.year}"
        return name, f"in {name}"
    if re.fullmatch(r"\d{2}-\d{4}_to_\d{2}-\d{4}", label):
        a, b = (month(x) for x in label.split("_to_"))
        name = (f"{calendar.month_name[a.month]} to {calendar.month_name[b.month]} {b.year}" if a.year == b.year
                else f"{calendar.month_name[a.month]} {a.year} to {calendar.month_name[b.month]} {b.year}")
        return name, f"from {name}"
    if re.fullmatch(r"\d{2}-\d{2}-\d{4}_to_\d{2}-\d{2}-\d{4}", label):
        a, b = label.split("_to_")
        return f"{a} to {b}", f"from {a} to {b}"
    sys.exit(f"Unrecognised label {label!r}. Use MM-YYYY, MM-YYYY_to_MM-YYYY or DD-MM-YYYY_to_DD-MM-YYYY.")


def expand(text: str, data: dict) -> str:
    """Escape text, then turn [[source.field@key=value|fmt]] or [[source.field#row|fmt]] into marked numbers."""
    out, last = [], 0
    for m in TOKEN.finditer(text):
        src, field, wk, wv, row, fmt = m.groups()
        if fmt not in FORMATS:
            sys.exit(f"Unknown format {fmt!r} in {m.group(0)}")
        if src in CALCS:
            fields, keys = CALCS[src]
            if field not in fields or (wk and wv not in keys.get(wk, {wv})):
                sys.exit(f"{m.group(0)} does not match the {src} calc")
        elif src in data:
            rows = data[src]
            if not rows or field not in rows[0]:
                sys.exit(f"{m.group(0)}: {src} has no field {field!r}")
            if wk and not any(str(r.get(wk)) == wv for r in rows):
                sys.exit(f"{m.group(0)}: no {src} row where {wk}={wv}")
            if row and int(row) >= len(rows):
                sys.exit(f"{m.group(0)}: {src} has no row {row}")
        else:
            sys.exit(f"{m.group(0)}: unknown source {src!r}")
        where = f' data-where="{wk}={html.escape(wv)}"' if wk else f' data-row="{row or 0}"'
        out.append(html.escape(text[last:m.start()]))
        out.append(f'<b data-draw="num" data-source="{src}" data-field="{field}"{where} data-fmt="{fmt}">—</b>')
        last = m.end()
    out.append(html.escape(text[last:]))
    result = "".join(out)
    if "[[" in result:
        sys.exit(f"Malformed number token in: {text}")
    return result


def check_words(text: str, where: str) -> None:
    if "—" in TOKEN.sub("", text):
        sys.exit(f"Em dash in {where}. Use a comma or a full stop.")
    if re.search(r"\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}", text):
        sys.exit(f"Date not in DD-MM-YYYY in {where}.")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--label", required=True)
    p.add_argument("--report-dir", type=Path)
    args = p.parse_args()

    rdir = args.report_dir or Path("data/report") / args.label
    narrative = json.loads((rdir / "narrative.json").read_text(encoding="utf-8"))
    blobs = json.loads((rdir / "blobs.json").read_text(encoding="utf-8"))
    data = {k: json.loads((rdir / f"{k}.json").read_text(encoding="utf-8"))["rows"] for k in DATASETS}
    missing = [k for k in [*DATASETS, *FONTS] if not str(blobs.get(k, "")).startswith("/_blob/")]
    if missing:
        sys.exit(f"blobs.json is missing upload urls for: {', '.join(missing)}")

    for key in ("headline", "comparison_note", "release_note", "asks_heading", "actions"):
        if not narrative.get(key):
            sys.exit(f"narrative.json needs {key!r}")
    if len(narrative["actions"]) != 3:
        sys.exit("narrative.json needs exactly 3 actions")
    for k in ("headline", "comparison_note", "release_note", "asks_heading"):
        check_words(narrative[k], k)

    cards = []
    for i, a in enumerate(narrative["actions"], 1):
        for f in ("owner", "title", "text", "measure"):
            if not a.get(f):
                sys.exit(f"action {i} needs {f!r}")
            check_words(a[f], f"action {i} {f}")
        cards.append(
            '      <div class="pp-card">\n'
            f'        <span class="pp-chip">{html.escape(a["owner"])}</span>\n'
            f'        <h3>{html.escape(a["title"])}</h3>\n'
            f'        <p data-read lang="en">{expand(a["text"], data)}</p>\n'
            f'        <span class="pp-muted">Measure: {html.escape(a["measure"])}</span>\n'
            "      </div>")

    k = data["kpis"][0]
    short, phrase = period(args.label)
    fills = {
        "PERIOD_LABEL": html.escape(short), "PERIOD_PHRASE": html.escape(phrase),
        "RANGE": f'{k["first_day"]} to {k["last_day"]}', "FIRST_DAY": k["first_day"], "LAST_DAY": k["last_day"],
        "HEADLINE": expand(narrative["headline"], data), "COMPARISON_NOTE": expand(narrative["comparison_note"], data),
        "RELEASE_NOTE": expand(narrative["release_note"], data), "ASKS_HEADING": html.escape(narrative["asks_heading"]),
        "ACTIONS": "\n".join(cards),
        "STORE_ASOF": (f'on {k["store_snapshot_at"].split()[0]}' if k.get("store_snapshot_at") else "not captured"),
    }
    page = TEMPLATE.read_text(encoding="utf-8")
    for key, val in fills.items():
        page = page.replace("{{" + key + "}}", val)
    left = re.findall(r"\{\{[A-Z_]+\}\}", page)
    if left:
        sys.exit(f"Template placeholders left unfilled: {left}")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    edit = {"via": "claude", "at": now}
    out = rdir / "artifact"
    out.mkdir(exist_ok=True)
    docs = [("dash", "meta", {"title": f"Zomato Play Store Pulse {short}", "lang": "en"})]
    for name, (title, desc) in DATASETS.items():
        docs.append(("datasets", name, {
            "title": title, "description": f"{desc}, {k['first_day']} to {k['last_day']}.",
            "source": {"kind": "file", "url": blobs[name], "name": f"{name}.json", "format": "json"},
            "updated": {"at": now, "by": f"Claude, from data/raw/reviews_{args.label}.csv"}, "fixed": True,
            "schedule": "Rebuilt for each period by the play-store-pulse skill", "edit": edit}))
    css = "".join(
        f"@font-face{{font-family:'Okra';font-style:normal;font-weight:{w};font-display:swap;"
        f"src:url({blobs[f]}) format('woff2');}}\n" for f, w in FONTS.items())
    docs.append(("files", "okra.css", {"text": css, "edit": edit}))
    docs.append(("files", "index.html", {"text": page, "edit": edit}))

    writes = []
    for coll, doc_id, body in docs:
        path = (out / f"{coll}__{doc_id}.json").resolve()
        path.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
        writes.append({"op": "set", "collection": coll, "doc_id": doc_id, "file_path": str(path)})
    (out / "writes.json").write_text(json.dumps(writes, indent=1), encoding="utf-8")
    (out / "index.html").write_text(page, encoding="utf-8")
    print(f"Title: Zomato Play Store Pulse {short}")
    print(f"Wrote {len(writes)} documents to {out}. Pass the list in {out / 'writes.json'} as `writes`.")


if __name__ == "__main__":
    main()
