#!/usr/bin/env python3
"""Update every user row in a weekly-report page from each user's Jira issues.

Iterates account-ids found in the page table. For each, queries Jira for that
user's recent done + active items and replaces their 금주/차주 cells.
Skips users with no items.
"""
from __future__ import annotations
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from weekly_report_lib.clients import (  # noqa
    cf_get_page, cf_update_page, default_email,
    jira_done_recent, jira_active_or_todo,
)
from weekly_report_lib.page_ops import (  # noqa
    replace_user_cells, render_grouped_list, categorize, all_user_rows,
)

BACKUP_DIR = os.environ.get("WEEKLY_REPORT_BACKUP_DIR", os.path.expanduser("~/.weekly-report-backups"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--page-id", required=True)
    ap.add_argument("--email", default=None)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--only", help="Comma-separated account-ids to update (others skipped)")
    args = ap.parse_args()

    email = args.email or default_email()
    if not email:
        sys.exit("❌ no email — pass --email or set ATLASSIAN_EMAIL or `git config user.email`")

    only = set(args.only.split(",")) if args.only else None

    print(f"[1/4] page {args.page_id} site={args.site}")
    page = cf_get_page(args.site, args.page_id, email)
    body = page["body"]["storage"]["value"]
    cur_ver = page["version"]["number"]
    title = page["title"]
    rows = all_user_rows(body)
    print(f"      title={title!r} v{cur_ver} users_in_page={len(rows)}")

    print(f"[2/4] fetching jira data per user...")
    new_body = body
    updated = 0
    for account_id, _span in rows:
        if only and account_id not in only:
            continue
        try:
            done = jira_done_recent(args.site, email, account_id=account_id)
            active = jira_active_or_todo(args.site, email, account_id=account_id)
        except Exception as e:
            print(f"      ! {account_id[:30]}: jira fetch failed ({e})")
            continue
        if not done and not active:
            print(f"      · {account_id[:30]}: no items")
            continue
        tw, nw = categorize(done, active)
        try:
            new_body = replace_user_cells(new_body, account_id, render_grouped_list(tw), render_grouped_list(nw))
            print(f"      ✓ {account_id[:30]}: 금주 {sum(len(v) for v in tw.values())} / 차주 {sum(len(v) for v in nw.values())}")
            updated += 1
        except Exception as e:
            print(f"      ! {account_id[:30]}: cell replace failed ({e})")

    print(f"[3/4] {updated} rows updated. body delta: {len(new_body) - len(body):+d}")

    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    with open(os.path.join(BACKUP_DIR, f"{args.page_id}-v{cur_ver}-{ts}.html"), "w") as f:
        f.write(body)
    proposed = os.path.join(BACKUP_DIR, f"{args.page_id}-v{cur_ver}-{ts}.proposed.html")
    with open(proposed, "w") as f:
        f.write(new_body)

    if not args.apply:
        print(f"[4/4] DRY-RUN — diff: {proposed}")
        return 0

    print(f"[4/4] PUT v{cur_ver + 1}...")
    res = cf_update_page(args.site, args.page_id, title, new_body, cur_ver + 1, email)
    print(f"      OK v{res['version']['number']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
