#!/usr/bin/env python3
"""Create next week's weekly-report Confluence page under {year}/{half}/{month} folders.

Source = latest dated page in prev_monday's month folder under root.
Destination = new_monday's month folder (auto-created with half-year folder if missing).
Carries 차주 계획 → 금주 진행 (manual siblings preserved), blanks 차주, recomputes
header date ranges from new title's Monday.

Inputs:
  --site         Atlassian site (e.g. <your-team>.atlassian.net)
  --root-id      ROOT page ID under which {year}/{half}/{month} folders live
                 (e.g. "02. 주간 보고" page). Folders auto-created.
  --source-id    Optional override: explicit source/template page ID.
                 If omitted, picks latest dated page in prev_monday's month folder.
"""
from __future__ import annotations
import argparse
import os
import re
import sys
import time
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(__file__))
from weekly_report_lib.clients import (  # noqa
    cf_get_page, cf_create_page, cf_children, default_email,
)
from weekly_report_lib.page_ops import (  # noqa
    carry_template, compute_next_title, append_footer, update_header_dates,
    half_title, month_title, kst_today_monday, find_child_by_title,
)

BACKUP_DIR = os.environ.get("WEEKLY_REPORT_BACKUP_DIR", os.path.expanduser("~/.weekly-report-backups"))
PLUGIN_VERSION = "0.4.1"


def _now_kst() -> str:
    from datetime import datetime, timezone, timedelta as _td
    from datetime import datetime as _dt
    return _dt.now(timezone(_td(hours=9))).strftime("%Y-%m-%d %H:%M KST")


def find_or_create_folder(site: str, parent_id: str, title: str, space_key: str, email: str, apply: bool) -> str:
    cid = find_child_by_title(cf_children(site, parent_id, email), title)
    if cid:
        return cid
    if not apply:
        print(f"      (dry-run) would create folder: {title!r} under {parent_id}")
        return f"<DRY-FOLDER:{title}>"
    print(f"      creating folder: {title!r} under {parent_id}")
    res = cf_create_page(site, space_key, title, "<p />", parent_id, email)
    return res["id"]


def pick_source_for(site: str, root_id: str, prev_monday: date, email: str) -> str:
    h_id = find_child_by_title(cf_children(site, root_id, email), half_title(prev_monday))
    if not h_id:
        sys.exit(f"❌ no half folder under root: {half_title(prev_monday)}")
    m_id = find_child_by_title(cf_children(site, h_id, email), month_title(prev_monday))
    if not m_id:
        sys.exit(f"❌ no month folder under half: {month_title(prev_monday)}")
    rx = re.compile(r"\((\d{2})-(\d{2})-(\d{2})\)")
    dated: list[tuple[date, str]] = []
    for c in cf_children(site, m_id, email):
        m = rx.search(c.get("title", ""))
        if m:
            yy, mm, dd = (int(x) for x in m.groups())
            dated.append((date(2000 + yy, mm, dd), c["id"]))
    if not dated:
        sys.exit(f"❌ no dated weekly page in {month_title(prev_monday)}")
    dated.sort()
    return dated[-1][1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--root-id", required=True, help="Root page ID under which year/half/month folders live")
    ap.add_argument("--source-id", default=None, help="Optional explicit source page ID (else auto-pick from prev month folder)")
    ap.add_argument("--email", default=None)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    email = args.email or default_email()
    if not email:
        sys.exit("❌ no email — pass --email or set ATLASSIAN_EMAIL or `git config user.email`")

    new_monday = kst_today_monday()
    prev_monday = new_monday - timedelta(days=7)
    print(f"[1/4] new_monday={new_monday} prev_monday={prev_monday}")

    root = cf_get_page(args.site, args.root_id, email)
    space_key = root["space"]["key"]
    print(f"      root={root['title']!r} space={space_key}")

    source_id = args.source_id or pick_source_for(args.site, args.root_id, prev_monday, email)
    print(f"[2/4] source page: {source_id}")
    src = cf_get_page(args.site, source_id, email)
    body = src["body"]["storage"]["value"]
    src_title = src["title"]

    new_title = compute_next_title(src_title)
    new_body = carry_template(body)
    new_body = update_header_dates(new_body, new_title)
    new_body = append_footer(
        new_body,
        source="/weekly-report:create",
        generator="Claude (interactive)",
        version=PLUGIN_VERSION,
        generated_at_kst=_now_kst(),
    )
    print(f"[3/4] new title={new_title!r}")
    print(f"      body: {len(body)} → {len(new_body)} ({len(new_body) - len(body):+d})")

    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    proposed = os.path.join(BACKUP_DIR, f"new-page-{ts}.proposed.html")
    with open(proposed, "w") as f:
        f.write(new_body)

    half_id = find_or_create_folder(args.site, args.root_id, half_title(new_monday), space_key, email, args.apply)
    if args.apply:
        month_id = find_or_create_folder(args.site, half_id, month_title(new_monday), space_key, email, args.apply)
    else:
        # In dry-run, only attempt month lookup if half exists
        existing_half = find_child_by_title(cf_children(args.site, args.root_id, email), half_title(new_monday))
        month_id = (
            find_child_by_title(cf_children(args.site, existing_half, email), month_title(new_monday))
            if existing_half else f"<DRY-MONTH:{month_title(new_monday)}>"
        )

    if not args.apply:
        print(f"[4/4] DRY-RUN — proposed body: {proposed}")
        print(f"      dest parent (would be): {month_id} ({month_title(new_monday)})")
        return 0

    print(f"[4/4] POST under {month_id} ({month_title(new_monday)})...")
    res = cf_create_page(args.site, space_key, new_title, new_body, month_id, email)
    print(f"      OK id={res['id']}")
    print(f"      url: https://{args.site}/wiki/spaces/{space_key}/pages/{res['id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
