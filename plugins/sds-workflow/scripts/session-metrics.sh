#!/usr/bin/env bash
# session-metrics.sh — Phase 1 메트릭 (소요 시간만).
#
# 사용처: autopilot/ship 의 Jira 코멘트 footer 에 누적 시간 라인을 합성할 때.
# autopilot Phase 0 에서 `date +%s` 출력을 `.work/{issue_key}.md` "## 메트릭" 섹션
# `start_epoch:` 라인에 기록하고, 각 페이즈 코멘트 직전에 이 스크립트를 호출해
# `{ELAPSED_HUMAN}` 플레이스홀더 값을 얻는다.
#
# 인자:
#   $1 — 시작 timestamp (epoch seconds, `date +%s` 출력)
#
# 출력 (stdout, 1줄):
#   elapsed=<sec> human=<H h M m | M m S s | S s>
#
# Exit code:
#   0  성공
#   1  인자 누락
#   2  시작 시각이 미래 (시계 어긋남 / 잘못된 입력)
#
# 의존: 표준 POSIX `date` / `printf` 만 사용. macOS · Linux 둘 다 동작.

set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "usage: session-metrics.sh <start_epoch>" >&2
  exit 1
fi

START="$1"
NOW=$(date +%s)

# 입력이 숫자가 아니면 셸 산술이 실패하므로 명시적으로 검증
if ! [[ "$START" =~ ^[0-9]+$ ]]; then
  echo "error: start_epoch must be a positive integer (got '$START')" >&2
  exit 1
fi

ELAPSED=$((NOW - START))

if [ "$ELAPSED" -lt 0 ]; then
  echo "error: start_epoch is in the future (clock skew?)" >&2
  exit 2
fi

H=$((ELAPSED / 3600))
M=$(( (ELAPSED % 3600) / 60 ))
S=$((ELAPSED % 60))

if [ "$H" -gt 0 ]; then
  HUMAN="${H}h ${M}m"
elif [ "$M" -gt 0 ]; then
  HUMAN="${M}m ${S}s"
else
  HUMAN="${S}s"
fi

printf 'elapsed=%d human=%s\n' "$ELAPSED" "$HUMAN"
