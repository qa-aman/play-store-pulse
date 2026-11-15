"""Build a standalone copy of a Play Store Pulse dashboard for GitHub Pages.

The live dashboard runs inside the claude.ai Dashboard runtime (dash.data, dash.calc, dash.draw and its theme
tokens). This wraps the page that render_page.py produced in a plain HTML document with a tiny stand-in for that
runtime and the period's data inlined, so it opens anywhere. The Okra font is Zomato's licensed typeface, so it is
not published; the page falls back to the system font.

Output: docs/<label>/index.html (served by GitHub Pages from the docs/ folder on main).
"""

import argparse
import json
import re
import sys
from pathlib import Path

DATASETS = ["kpis", "stars", "complaints", "praise", "hours", "daily", "versions", "loudest"]
D3 = "https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="robots" content="noindex">
<style>
:root {{
  --color-bg: #ffffff; --color-panel: #f7f7f8; --color-fg: #1c1c1c; --color-fg-muted: #696969;
  --color-border-line: #e8e8e8; --font-anthropic-sans: system-ui;
  --cds-border: #e8e8e8; --cds-chart-axis: #9c9c9c; --cds-chart-grid: #efefef; --cds-chart-reference: #696969;
  --cds-surface-popover: #ffffff; --cds-shadow-popover: 0 4px 16px rgba(0,0,0,.12); --cds-text-secondary: #696969;
  color-scheme: light;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --color-bg: #141414; --color-panel: #1e1e1e; --color-fg: #f0f0f0; --color-fg-muted: #a8a8a8;
    --color-border-line: #333333; --cds-border: #333333; --cds-chart-axis: #8a8a8a; --cds-chart-grid: #2a2a2a;
    --cds-chart-reference: #a8a8a8; --cds-surface-popover: #232323; --cds-shadow-popover: 0 4px 16px rgba(0,0,0,.5);
    --cds-text-secondary: #a8a8a8; color-scheme: dark;
  }}
}}
html, body {{ margin: 0; background: var(--color-bg); color: var(--color-fg); }}
body {{ font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif; }}
main {{ max-width: 1080px; margin: 0 auto; padding: 24px 16px 48px; }}
.pp-foot {{ margin-top: 40px; font-size: 13px; color: var(--color-fg-muted); }}
.pp-foot a {{ color: #cf4a57; }}
</style>
<script src="{d3}"></script>
<script>
(function () {{
  const DATA = {data};
  const calcs = {{}}, draws = {{}};
  window.dash = {{
    data(name) {{
      if (name in DATA) return {{ status: 'ok', data: DATA[name] }};
      if (name in calcs) {{
        const c = calcs[name];
        if (!('value' in c)) c.value = c.fn(...c.inputs.map((i) => DATA[i]));
        return {{ status: 'ok', data: c.value }};
      }}
      return {{ status: 'error', data: [] }};
    }},
    calc(name, spec) {{ calcs[name] = {{ fn: spec.fn, inputs: spec.inputs }}; }},
    draw(name, fn) {{ draws[name] = fn; }},
  }};
  document.addEventListener('DOMContentLoaded', () => {{
    document.querySelectorAll('[data-draw]').forEach((el) => {{
      const fn = draws[el.dataset.draw];
      if (fn) try {{ fn(el); }} catch (e) {{ console.error(el.dataset.draw, e); }}
    }});
  }});
}})();
</script>
</head>
<body>
<main>
"""

FOOT = """
<p class="pp-foot">About this data: English reviews from India on the public Google Play page for {period}, read with an
open-source scraper, not Zomato's Play Console. Quotes are masked for personal details. Complaint themes are keyword
matches, a first cut rather than a final count. <a href="../">All reports</a></p>
</main>
</body>
</html>
"""


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--label", required=True)
    args = p.parse_args()
    rdir = Path("data/report") / args.label
    page_path = rdir / "artifact" / "index.html"
    if not page_path.exists():
        sys.exit(f"{page_path} not found. Run render_page.py --label {args.label} first.")
    page = page_path.read_text(encoding="utf-8")
    page = re.sub(r'<meta name="dash-one-writer">\s*', "", page)
    page = re.sub(r'<link rel="stylesheet" href="okra.css">\s*', "", page)
    data = {k: json.loads((rdir / f"{k}.json").read_text(encoding="utf-8"))["rows"] for k in DATASETS}
    title = json.loads((rdir / "artifact" / "dash__meta.json").read_text(encoding="utf-8"))["title"]
    period = title.replace("Zomato Play Store Pulse ", "")
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = HEAD.format(title=title, d3=D3, data=blob) + page + FOOT.format(period=period, label=args.label)
    out = Path("docs") / args.label / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"Wrote {out} ({len(html) // 1024} KB)")


if __name__ == "__main__":
    main()
