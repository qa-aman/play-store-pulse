"""Save a rendered leadership email as a Gmail draft. Never sends.

Reads data/report/<label>/email/{subject.txt,email.html} and config/email.json:
  {"gmail_account": "...", "gmail_connection": "...", "to": [...], "cc": [...]}
Checks that Composio is on aman_workspace and that the connection's mailbox is gmail_account,
then calls GMAIL_CREATE_EMAIL_DRAFT through the composio CLI and prints the draft id.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ORG = "aman_workspace"
EMAIL = re.compile(r"^[^@\s<>]+@[^@\s<>]+\.[^@\s<>]+$")


def run(args: list[str]) -> dict:
    out = subprocess.run(["composio", *args], capture_output=True, text=True, timeout=120)
    text = out.stdout.strip()
    start = text.find("{")
    if out.returncode != 0 or start < 0:
        sys.exit(f"composio {' '.join(args[:2])} failed:\n{out.stderr or out.stdout}")
    return json.loads(text[start:])


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--label", required=True)
    args = p.parse_args()

    cfg = json.loads(Path("config/email.json").read_text(encoding="utf-8"))
    account, conn = cfg.get("gmail_account"), cfg.get("gmail_connection")
    if not account or not conn:
        sys.exit("config/email.json needs gmail_account and gmail_connection.")
    to, cc = cfg.get("to", []), cfg.get("cc", [])
    bad = [a for a in [*to, *cc] if not EMAIL.match(a)]
    if bad:
        sys.exit(f"Not valid email addresses in config/email.json: {bad}")

    out = Path("data/report") / args.label / "email"
    subject = (out / "subject.txt").read_text(encoding="utf-8").strip()
    body = (out / "email.html").read_text(encoding="utf-8")

    who = run(["whoami"])
    if who.get("current_org_name") != ORG:
        sys.exit(f"Composio is on {who.get('current_org_name')!r}, not {ORG}. Switch with: composio orgs switch")
    profile = run(["execute", "GMAIL_GET_PROFILE", "--account", conn, "-d", "{}"])
    mailbox = json.dumps(profile)
    if f'"{account}"' not in mailbox:
        sys.exit(f"Connection {conn} is not {account}. Update gmail_connection in config/email.json "
                 f"(composio connections list, then GMAIL_GET_PROFILE on each gmail connection).")

    payload = {"subject": subject, "body": body, "is_html": True, "cc": cc}
    if to:
        payload["recipient_email"] = to[0]
        if to[1:]:
            payload["extra_recipients"] = to[1:]
    data_file = out / "gmail_payload.json"
    data_file.write_text(json.dumps(payload), encoding="utf-8")
    res = run(["execute", "GMAIL_CREATE_EMAIL_DRAFT", "--account", conn, "-d", f"@{data_file}"])
    data = res.get("data", res)
    draft_id = data.get("id") or (data.get("response_data") or {}).get("id")
    if not draft_id:
        sys.exit(f"No draft id in the response:\n{json.dumps(res)[:800]}")
    (out / "gmail_draft.json").write_text(json.dumps({"account": account, "draft_id": draft_id}), encoding="utf-8")
    print(f"Gmail draft created in {account}: id {draft_id}")
    print(f"To: {', '.join(to) or '(none yet, add before sending)'}  Cc: {', '.join(cc) or '(none)'}")


if __name__ == "__main__":
    main()
