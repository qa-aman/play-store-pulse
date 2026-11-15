"""PreToolUse guard for this project: email is drafted, never sent.

Blocks any Bash command or MCP tool call whose input names a Gmail tool that sends, replies or forwards
(for example GMAIL_SEND_EMAIL, GMAIL_SEND_DRAFT, GMAIL_REPLY_TO_THREAD). Creating drafts is allowed.
Exit 2 blocks the call.
"""

import json
import re
import sys

SENDS = re.compile(r"GMAIL_(SEND|REPLY|FORWARD)\w*|SEND_DRAFT|SEND_EMAIL|messages/send|drafts/send", re.I)
MAIL_TOOL = re.compile(r"(gmail|mail|outlook).*(send|reply|forward)|(send|reply|forward).*(gmail|mail|outlook)", re.I)


def main() -> None:
    event = json.load(sys.stdin)
    name = event.get("tool_name", "")
    if MAIL_TOOL.search(name) or SENDS.search(name + " " + json.dumps(event.get("tool_input", {}))):
        print("Blocked: this project only creates Gmail drafts. The PM reviews and sends them.", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
