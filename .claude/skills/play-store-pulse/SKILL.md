---
name: play-store-pulse
description: Build the Zomato Play Store Pulse leadership dashboard for any period. Fetches Zomato Android Google Play reviews for a month, a month range or a date range, builds the summary data, writes the takeaway and three asks, publishes a new Zomato-styled (Sushi design system) Dashboard artifact, then drafts the leadership email in Gmail through the draft-email skill. Use when the user says "/play-store-pulse", "run the play store report for <month>", "monthly review report", "leadership review dashboard for <range>", "Play Store Pulse for October", "reviews from 01-10 to 15-10", or asks for the monthly Play Store review summary.
argument-hint: "<MM-YYYY> | <MM-YYYY> to <MM-YYYY> | <DD-MM-YYYY> to <DD-MM-YYYY>"
---

# Play Store Pulse

Produces one new dashboard per period, for Zomato leadership. Run every command from the project root (the folder holding `scripts/` and `.venv/`). Read `problem-statement.md` once if scope is unclear.

## 1. Read the range

The input is `$ARGUMENTS`. Turn it into fetch arguments and a label:

| Input | Fetch arguments | Label |
|---|---|---|
| `10-2026` or "October 2026" | `--month 10-2026` | `10-2026` |
| `01-2026 to 06-2026` | `--from-month 01-2026 --to-month 06-2026` | `01-2026_to_06-2026` |
| `01-10-2026 to 15-10-2026` | `--from-date 01-10-2026 --to-date 15-10-2026` | `01-10-2026_to_15-10-2026` |

No input means last month (`fetch_reviews.py` defaults to it). If the range is ambiguous, ask once. A range that ends in the future, or today, gives a partial period: say so before fetching.

## 2. Fetch

```bash
.venv/bin/python scripts/fetch_reviews.py <fetch arguments>     # -> data/raw/reviews_<label>.csv
```

If `data/raw/reviews_<label>.csv` already exists, ask before fetching it again. The scraper reads newest first, so time depends on how far back the range starts: about 2 seconds per day between today and the start date (October from mid-November took 85 s). Run it with `run_in_background` when the start is more than about 60 days back, and wait for the notification.

The scraper is google-play-scraper: public Play Store page, English reviews from India only (`--lang en --country in`).

## 3. Build the data

```bash
.venv/bin/python scripts/build_report_data.py --label <label>     # -> data/report/<label>/*.json
```

Then read `data/report/<label>/kpis.json`. Check `days` against the calendar days in the range. If days are missing, tell the user which, and carry on only if they agree.

## 4. Check the quotes

Read `complaints.json` (`quote_1`) and `loudest.json` (`text`). Each complaint quote must be about its theme. If one isn't, replace it with a better review from `data/raw/reviews_<label>.csv` (1 or 2 stars, 60 to 260 characters, matching the theme), passed through `mask()` from `scripts/build_report_data.py`, or set it to `""`. Never show a phone number, email or order id.

## 5. Write the words

Write `data/report/<label>/narrative.json` following `references/narrative.md`. Read that file every run. Numbers go in as tokens, never typed.

## 6. Create the dashboard

Create a new artifact from the Data type, one per period:

- Artifact publish with `type_url` `https://claude.ai/artifact/GZLZthZ2sQjn7T16skfdeF`, `title` `Zomato Play Store Pulse <period>` (for example "October 2026"), `auto_open` `"after_first_write"`, no files.

Then upload, with the new artifact's `url` and `asset: true`:
- each of the 8 files `data/report/<label>/{kpis,stars,complaints,praise,hours,daily,versions,loudest}.json`, **one call each** (JSON files can't share a call; send the 8 calls in one message);
- the 3 fonts in one call with `file_paths`: `.claude/skills/play-store-pulse/assets/fonts/okra-{regular,medium,semibold}.woff2`.

Write `data/report/<label>/blobs.json` mapping each file stem to the `/_blob/...` url it got:
`{"kpis": "/_blob/...", ..., "loudest": "/_blob/...", "okra-regular": "/_blob/...", "okra-medium": "/_blob/...", "okra-semibold": "/_blob/..."}`

## 7. Render and write

```bash
.venv/bin/python .claude/skills/play-store-pulse/scripts/render_page.py --label <label>
```

It fills `assets/dashboard.html` and fails loudly on a bad token, an em dash, an ISO date or a missing upload. Fix the input and rerun; never edit the template to get past it. Then call `ArtifactData` `batch` on the artifact's url with `writes` set to the list in `data/report/<label>/artifact/writes.json` (11 documents, all `set`, no `if_version` on a new artifact).

## 8. Check

Read `ArtifactData` `list` of `data/users/me` on the artifact. `check` with `status: "passed"` is good. `failed` lists what threw: fix it in the template or data, re-render, and write `files/index.html` again with `if_version`. `not_shown` or nothing at all means no tab has the page open: say the page hasn't run yet, and don't loop.

## 9. Log

Append one row to `data/report/run-log.md` (create it with a header if missing): `| <DD-MM-YYYY today> | <label> | <reviews> | <avg rating> | <artifact url> |`. The email step reads the dashboard link from this row, so log before step 10.

## 10. Draft the leadership email (last step)

Invoke the `draft-email` skill with the same label (Skill tool, `skill: "draft-email"`, `args: "<label>"`) and follow it to the end: it writes the email from this period's data, saves it as a Gmail draft in the account set in `config/email.json` and logs it. It never sends. If the user said not to draft an email this run, skip this step and say so.

Then give one combined hand-over, in a few lines:
- the dashboard link, and the 3 to 4 findings that matter (from the data, not adjectives);
- the email subject and that the Gmail draft is ready, with or without recipients;
- what is assumed: English-only, keyword themes, suggested owners, any replaced quotes, any missing days;
- share the dashboard from its Share menu with the recipients before sending, since the page is private and the email links to it; anyone who can open it can read the attached summary files;
- for production, the Play Console monthly reviews export could replace the scraper.

## Changing the design

The look follows Zomato's Sushi design system (github.com/Zomato/compose-sushi): brand red `#EF4F5F`, deep red `#CF4A57`, greens `#009A51` and `#108145`, warn `#A5820A`, error orange `#CC511C`, 8px corners, Okra type, and green/yellow/orange rating badges. Text, cards and background use the dashboard's theme tokens so light and dark both read. Change `assets/dashboard.html` only when the user asks for a design change, and keep its `{{PLACEHOLDERS}}`, its `<meta name="dash-one-writer">` line and its `data-source`/`data-field` marks. Every new number on the page is a `data-draw="num"` mark, never text.
