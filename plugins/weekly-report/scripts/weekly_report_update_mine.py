#!/usr/bin/env python3
"""Update the calling user's row in a weekly-report Confluence page from their Jira sprint issues.

Reads token from macOS keychain. Auto-discovers calling user's accountId via /myself.
The user's row is found by that accountId in the page table.

Usage:
  python3 weekly_report_update_mine.py --site SITE --page-id ID
  python3 weekly_report_update_mine.py --site SITE --page-id ID --apply
  python3 weekly_report_update_mine.py --site SITE --page-id ID --apply --email me@example.com
"""
from __future__ import annotations
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from weekly_report_lib.clients import (  # noqa
    cf_get_page, cf_update_page, default_email,
    jira_myself, jira_done_recent, jira_active_or_todo,
)
from weekly_report_lib.page_ops import (  # noqa
    replace_user_cells, render_grouped_list, categorize,
)

BACKUP_DIR = os.environ.get("WEEKLY_REPORT_BACKUP_DIR", os.path.expanduser("~/.weekly-report-backups"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True, help="Atlassian host, e.g. <your-team>.atlassian.net")
    ap.add_argument("--page-id", required=True)
    ap.add_argument("--email", default=None)
    ap.add_argument("--apply", action="store_true", help="Actually PUT the update (default: dry-run)")
    args = ap.parse_args()

    email = args.email or default_email()
    if not email:
        sys.exit("❌ no email — pass --email or set ATLASSIAN_EMAIL or `git config user.email`")

    print(f"[1/5] caller={email} site={args.site}")
    me = jira_myself(args.site, email)
    account_id = me["accountId"]
    display = me.get("displayName", account_id)
    print(f"      accountId={account_id} display={display!r}")

    print(f"[2/5] fetching page {args.page_id}...")
    page = cf_get_page(args.site, args.page_id, email)
    body = page["body"]["storage"]["value"]
    cur_ver = page["version"]["number"]
    title = page["title"]
    print(f"      title={title!r} v{cur_ver} body_len={len(body)}")

    print(f"[3/5] fetching jira issues...")
    done = jira_done_recent(args.site, email)
    active = jira_active_or_todo(args.site, email)
    tw, nw = categorize(done, active)
    print(f"      금주 {sum(len(v) for v in tw.values())} / 차주 {sum(len(v) for v in nw.values())}")

    new_body = replace_user_cells(body, account_id, render_grouped_list(tw), render_grouped_list(nw))
    print(f"[4/5] body delta {len(new_body) - len(body):+d}")

    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    with open(os.path.join(BACKUP_DIR, f"{args.page_id}-v{cur_ver}-{ts}.html"), "w") as f:
        f.write(body)
    proposed = os.path.join(BACKUP_DIR, f"{args.page_id}-v{cur_ver}-{ts}.proposed.html")
    with open(proposed, "w") as f:
        f.write(new_body)
    print(f"      backup + proposed → {BACKUP_DIR}")

    if not args.apply:
        print(f"[5/5] DRY-RUN — diff: {proposed}")
        return 0

    print(f"[5/5] PUT v{cur_ver + 1}...")
    res = cf_update_page(args.site, args.page_id, title, new_body, cur_ver + 1, email)
    print(f"      OK v{res['version']['number']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
