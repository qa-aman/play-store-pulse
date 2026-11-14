---
name: draft-email
description: Draft the leadership email for a Play Store Pulse period, written to Smart Brevity, BLUF and Pyramid Principle structure with the Writing for Busy Readers checklist. Builds a paste-ready HTML and plain-text email from the same data as the dashboard, with the three asks, a reply-by date, one masked user quote and the dashboard link. Saves it as a Gmail draft in the account set in config/email.json, never sends. Use when the user says "/draft-email", "draft the email for the report", "email this to leadership", "write the leadership update for <period>", or wants to share a Play Store Pulse dashboard by email.
argument-hint: "[period label, e.g. 10-2026 or 01-11-2026_to_07-11-2026] [reply-by DD-MM-YYYY]"
---

# Draft email

Turns a finished Play Store Pulse period into a short leadership email. It needs that period's dashboard first; if `data/report/<label>/narrative.json` or its row in `data/report/run-log.md` is missing, run `/play-store-pulse` for it first. Run every command from the project root.

## 1. Pick the period

`$ARGUMENTS` may name a label (`10-2026`, `01-11-2026_to_07-11-2026`) or a range in words; turn words into the label the same way `/play-store-pulse` does. With no argument, use the last row of `data/report/run-log.md`. A second argument in DD-MM-YYYY is the reply-by date; otherwise the script uses 5 working days from today.

## 2. Read the period

Read `data/report/<label>/kpis.json`, `complaints.json`, `versions.json` and `narrative.json`. Find the earlier comparable period in `run-log.md` (the previous month for a month, the previous run otherwise) so the numbers can carry a comparison token like `[[10-2026:kpis.avg_rating#0|dec2]]`.

## 3. Write email.json

Write `data/report/<label>/email.json` following `references/email-content.md`. Read that file every run: it holds the frameworks, the shape and the token syntax. The bottom line must agree with the dashboard's headline in `narrative.json`.

## 4. Render

```bash
.venv/bin/python .claude/skills/draft-email/scripts/render_email.py --label <label> [--reply-by DD-MM-YYYY]
```

It writes `data/report/<label>/email/{subject.txt,email.txt,email.html}` and fails on a bad token, an em dash, an ISO date, a subject over 70 characters or a body over 200 words: fix `email.json` and rerun. If it lists typed numbers, check each one against the data, or replace it with a token.

## 5. Show the draft

Show the user the subject and the plain-text body in full, and the path to `email.html`. Paste `email.html` into the mail client to keep the formatting (open it in a browser, select all, copy).

Before they send, remind them:
- the dashboard is private until they share it from its Share menu with the recipients, or the "Go deeper" link opens to nothing;
- the asks name suggested owner teams, so they may want to check them.

## 6. Save it as a Gmail draft

Every run saves the email as a draft in the Gmail account named in `config/email.json` (`gmail_account`; copy `config/email.example.json` to create it):

```bash
.venv/bin/python .claude/skills/draft-email/scripts/gmail_draft.py --label <label>
```

It reads `config/email.json` (`gmail_account`, `gmail_connection`, `to`, `cc`), checks that Composio is on `aman_workspace` and that the connection's mailbox really is `gmail_account`, then calls `GMAIL_CREATE_EMAIL_DRAFT` with the HTML body. Recipients come only from `to` and `cc` in that file. When they are empty, the draft has no recipients and the user adds them in Gmail. Never guess or add a recipient, and change `to`/`cc` only when the user names the exact address. If the script says the connection is a different mailbox, find the right one (`composio connections list`, then `GMAIL_GET_PROFILE --account <word_id>` on each Gmail connection), update `gmail_connection` and rerun. If a draft for this label already exists (`email/gmail_draft.json`), ask before making a second one.

**Without the Composio CLI** (a cloud or scheduled run, where `command -v composio` finds nothing, and settings come from the `PULSE_GMAIL_ACCOUNT`, `PULSE_GMAIL_CONNECTION`, `PULSE_TO`, `PULSE_CC` environment variables because `config/email.json` is not in git):

1. Run `gmail_draft.py --label <label> --payload-only`. It prints the account, the connection and the path of the payload file.
2. Call the claude.ai Composio connector's `COMPOSIO_MANAGE_CONNECTIONS` with `gmail`, action `list`, and check that the account whose `id` is the connection has `user_info.email` equal to the account. If not, stop and report it: never draft in another mailbox, and never rely on the default account.
3. Call `COMPOSIO_MULTI_EXECUTE_TOOL` with one tool, `GMAIL_CREATE_EMAIL_DRAFT`, `account` set to the connection, and `arguments` set to the JSON in the payload file.
4. Write `email/gmail_draft.json` as `{"account": <account>, "draft_id": <data.id from the response>}`.

Never call `GMAIL_SEND_DRAFT` or `GMAIL_SEND_EMAIL`. The user reviews and sends it themselves.

## 7. Log

Append `| <DD-MM-YYYY today> | <label> | <subject> | Gmail draft <id> |` to `data/report/email-log.md` (create it with the header `| Date | Period | Subject | Status |` if missing).
