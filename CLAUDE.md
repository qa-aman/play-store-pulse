# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

Automating a Zomato PM's monthly Google Play Store review summary for the leadership team (Android only). Today the PM exports reviews, works through them in Excel, writes the report by hand and shares it. The aim is to get the reviews, theme and score them with AI, build a report in a fixed format and send it on a schedule, with the PM only reviewing and approving.

`problem-statement.md` is the source of truth for scope, report contents, success criteria, data sources and open questions. Read it before proposing a design, and update it when scope changes.

## Commands

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # setup
.venv/bin/python scripts/fetch_reviews.py --month 10-2026            # one calendar month -> data/raw/reviews_10-2026.csv
.venv/bin/python scripts/fetch_reviews.py --from-month 01-2026 --to-month 06-2026   # month range
.venv/bin/python scripts/fetch_reviews.py --from-date 01-10-2026 --to-date 15-10-2026  # date range
```

`--month` takes MM-YYYY and defaults to last month. Each range writes `data/raw/reviews_<label>.csv`, where the label is `10-2026`, `01-2026_to_06-2026` or `01-10-2026_to_15-10-2026`. The scraper reads newest first, so a fetch takes about 2 s per day between today and the range start. The scraper is `google-play-scraper` (open source, reads the public Play Store page, no login). It returns only the `--lang` given (default `en`, country `in`). One month in English is about 19,600 reviews and takes about 85 s. Dates in the CSV are DD-MM-YYYY HH:MM. There are no tests or linter yet.

```bash
.venv/bin/python scripts/build_report_data.py --label 10-2026        # -> data/report/<label>/*.json
```

`fetch_reviews.py` also saves `data/raw/store_<label>.json`, the Play Store rating shown in India on the fetch day (`--store-only` takes just that). This builds 8 summary files (`kpis, stars, complaints, praise, hours, daily, versions, loudest`), each shaped `{rows, meta}`, with the script's own code in `meta`. Themes are keyword regexes in `COMPLAINTS` and `PRAISE` on reviews with more than 20 characters of text. Quotes are masked and never reused across themes.

## Leadership dashboard

Run it with the `play-store-pulse` skill (`/play-store-pulse <range>`, in `.claude/skills/play-store-pulse/`). Its `SKILL.md` holds the full procedure: fetch, build, check quotes, write `narrative.json`, create a new Data artifact, upload, render with `render_page.py` and batch-write. It creates one artifact per period, and each run is logged in `data/report/run-log.md`. Its last step runs `draft-email` for the same period, so one command gives the dashboard and the Gmail draft. The page template is `assets/dashboard.html`, styled with Zomato's Sushi tokens.

## Leadership email

Run it with the `draft-email` skill (`/draft-email [label] [reply-by]`, in `.claude/skills/draft-email/`), after `/play-store-pulse` has built that period. Claude writes `data/report/<label>/email.json` (subject, bottom line, why it matters, 2 to 4 numbers as tokens, quote choice). `render_email.py` fills it from the same data as the dashboard, takes the three asks from `narrative.json` and the link from `run-log.md`, and writes `email/{subject.txt,email.txt,email.html}`. The structure is Smart Brevity, BLUF and Pyramid Principle, checked against Writing for Busy Readers: subject under 70 characters, body under 200 words. It then saves the email as a Gmail draft in the account set in `config/email.json` (`gmail_account`; not committed, copy `config/email.example.json`) with `gmail_draft.py` (Composio `aman_workspace`, connection set in `config/email.json`, which also holds `to`/`cc`, empty until the user names addresses). It never sends. Drafts are logged in `data/report/email-log.md`.

The first dashboard, built by hand before the skill existed:

The Dashboard artifact "Zomato Play Store Pulse October 2026" is at https://claude.ai/artifact/RpvNsCSkum5vSw8xjtLSjD. The 8 JSON files are uploaded as assets and attached as `fixed` file datasets. The page is `files/index.html` in the artifact's store and follows the one-writer rule. Two calcs live in the page: `windows` (rating by part of the day) and `worst_days`. Later periods get their own artifact through the skill, not by refreshing this one.

## Report audit

The `report-auditor` subagent (`.claude/agents/report-auditor.md`, Sonnet) checks one period: it recomputes every number on the dashboard and in the email from `data/raw/reviews_<label>.csv` and lists each mismatch with where it appears and the correct value. Run it after `/play-store-pulse` or `/draft-email`, before the email goes to leadership. It is read-only: the hook `.claude/hooks/report-auditor-guard.py` lets it write only to its memory folder (`.claude/agent-memory/report-auditor/`, committed), and allows Bash only an allowlist of read-only commands plus inline project Python whose imports and `open()` calls are checked.

## Monthly run (pm-agent)

`pm-agent` (`.claude/agents/pm-agent.md`, Sonnet, project memory in `.claude/agent-memory/pm-agent/`) runs the whole pack for one period: `play-store-pulse` without its email step, `draft-email` up to rendering, then `report-auditor`, and saves the Gmail draft only after a clean audit. On a mismatch it stops and tells the PM. Start it as the main session, `claude --agent pm-agent`, then give the period. Run as a background subagent it would lose `ArtifactData` (needed to write the dashboard) and the ability to ask questions (https://code.claude.com/docs/en/sub-agents). Email is never sent: the project hook `.claude/hooks/no-send-guard.py` (in `.claude/settings.json`) blocks any Gmail send, reply or forward call in every session here.

## Constraints to design around

- **Most reviews are star-only:** in October 2026, only about 4,900 of 19,600 reviews had more than 20 characters of text. Ratings use every review. Themes can only use reviews with text.
- **Monthly data source (production):** Play Console writes a monthly reviews CSV for each app to a Google Cloud Storage bucket (`reviews_[package_name]_YYYYMM.csv`). It covers the full month and is the primary source. Docs: https://support.google.com/googleplay/android-developer/answer/6135870
- **The Developer API covers only 7 days:** the Reply to Reviews API returns only reviews created or changed in the last 7 days. It can cover a month only if it is pulled weekly and stored. Docs: https://developers.google.com/android-publisher/reply-to-reviews
- **Stable theme list:** month-on-month comparison depends on the same themes. Propose theme changes to the PM. Never apply them silently.
- **Approval gate:** nothing goes to leadership without the PM's approval.
- **Privacy:** mask names, phone numbers and order details in quoted reviews.
- **Out of scope for now:** iOS, replying to reviews, competitor apps, real-time alerts.

## Related work

`../../zomato-pm/` is an earlier weekly version of the same workflow. It has fetch, batch, AI labelling, a dashboard, Jira tickets and a scheduled email. Its `CLAUDE.md` is worth reading for patterns that carry over. Its scraper (`google-play-scraper`) is unofficial and returns only the language you ask for.
