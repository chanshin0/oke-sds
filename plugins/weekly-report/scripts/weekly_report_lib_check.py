#!/usr/bin/env python3
"""Quick Atlassian credential check — used by /weekly-report:init Phase 3."""
from __future__ import annotations
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from weekly_report_lib.clients import jira_myself, default_email  # noqa


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--email", default=None)
    args = ap.parse_args()

    email = args.email or default_email()
    if not email:
        sys.exit("❌ no email")

    try:
        me = jira_myself(args.site, email)
    except Exception as e:
        sys.exit(f"❌ jira /myself failed: {e}")

    print(f"OK accountId={me['accountId']} display={me.get('displayName', '?')!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
