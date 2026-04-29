#!/usr/bin/env bash
# jira-comment.sh — /ship Phase 3-3 Jira 코멘트 wrapper
#
# 사용법:
#   jira-comment.sh <issue_key> <body>
#   jira-comment.sh <issue_key> @<body_file>    # @-prefix 면 파일 내용을 body 로 사용
#
# Exit:
#   0  : 코멘트 post 성공
#   10 : acli 미가용 (미설치 OR 미인증) — 호출측은 "수동 post" 로 처리
#   20 : acli 호출 실패 (네트워크·권한 등) — 호출측은 사용자에게 재시도 또는 수동 post 안내

set -euo pipefail

ISSUE_KEY="${1:?issue_key required}"
BODY_ARG="${2:?body required}"

if [[ "$BODY_ARG" == @* ]]; then
  BODY_FILE="${BODY_ARG:1}"
  [[ -f "$BODY_FILE" ]] || { echo "body file not found: $BODY_FILE" >&2; exit 20; }
  BODY="$(cat "$BODY_FILE")"
else
  BODY="$BODY_ARG"
fi

command -v acli >/dev/null 2>&1 || exit 10
acli jira auth status >/dev/null 2>&1 || exit 10

acli jira workitem comment "$ISSUE_KEY" --body "$BODY" || exit 20
