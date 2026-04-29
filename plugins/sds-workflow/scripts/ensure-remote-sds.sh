#!/usr/bin/env bash
# ensure-remote-sds.sh — 팀 공용 고정 remote `remote-sds` 등록 보장
#
# 사용법:
#   ensure-remote-sds.sh <gitlab_base_url> <gitlab_project_path>
#
# 동작:
#   0. 입력 URL 형식 검증 (scheme + host + path 형태)
#   1. `git remote get-url remote-sds` 시도
#   2a. 존재 + URL 일치 → stdout "ok: already-registered"; exit 0
#   2b. 존재 + URL 불일치 → stderr 에 existing/expected 비교 출력; exit 10
#        (호출측이 AskUserQuestion 으로 set-url/유지/중단 결정)
#   3. 존재 안 함 → `git remote add remote-sds <URL>` + `git fetch remote-sds --quiet`
#        → stdout "ok: registered"; exit 0
#
# 치명적 실패:
#   - 입력 부족/형식 위반 → exit 20
#   - `git remote add` 실패 → exit 20
#
# 호출 예 (shell):
#   if out=$(bash ensure-remote-sds.sh "$GITLAB_BASE_URL" "$GITLAB_PROJECT_PATH"); then
#     echo "remote-sds ready: $out"
#   else
#     code=$?
#     # 10: url-mismatch, 20: fatal
#   fi

set -euo pipefail

GITLAB_BASE_URL="${1:?gitlab_base_url required}"
GITLAB_PROJECT_PATH="${2:?gitlab_project_path required}"

# 빈 문자열 방어
if [[ -z "$GITLAB_BASE_URL" || -z "$GITLAB_PROJECT_PATH" ]]; then
  echo "error: gitlab_base_url 또는 gitlab_project_path 가 비어있다. .team-workflow/workflow.yml 의 gitlab 섹션 확인 필요" >&2
  exit 20
fi

# URL 형식 검증 — scheme://host (https://, http://) 또는 SSH (git@host:)
if ! [[ "$GITLAB_BASE_URL" =~ ^(https?://[^/]+|git@[^:]+:)/?$ || "$GITLAB_BASE_URL" =~ ^(https?://[^/]+|git@[^:]+:)$ ]]; then
  if ! [[ "$GITLAB_BASE_URL" =~ ^https?:// || "$GITLAB_BASE_URL" =~ ^git@ ]]; then
    echo "error: gitlab_base_url 형식 위반: '$GITLAB_BASE_URL' (예: https://gitlab.example.com 또는 git@gitlab.example.com)" >&2
    exit 20
  fi
fi

# project_path 형식 검증 — at least one slash, no leading slash, no trailing .git
if [[ "$GITLAB_PROJECT_PATH" =~ ^/ || "$GITLAB_PROJECT_PATH" =~ \.git$ || ! "$GITLAB_PROJECT_PATH" =~ / ]]; then
  echo "error: gitlab_project_path 형식 위반: '$GITLAB_PROJECT_PATH' (예: my-group/my-project, 슬래시 1개 이상, 선두 슬래시·.git 접미 금지)" >&2
  exit 20
fi

EXPECTED_URL="${GITLAB_BASE_URL%/}/${GITLAB_PROJECT_PATH}.git"

# .git 접미 normalize 비교 (사용자가 .git 없이 add 했을 수 있음)
normalize() { printf '%s' "${1%.git}"; }

if EXISTING="$(git remote get-url remote-sds 2>/dev/null)"; then
  if [[ "$(normalize "$EXISTING")" == "$(normalize "$EXPECTED_URL")" ]]; then
    echo "ok: already-registered ($EXISTING)"
    exit 0
  fi
  # URL 불일치 — 호출측이 결정
  echo "warn: url-mismatch" >&2
  echo "  existing: $EXISTING" >&2
  echo "  expected: $EXPECTED_URL" >&2
  echo "warn: url-mismatch"
  exit 10
fi

# 신규 등록
if git remote add remote-sds "$EXPECTED_URL" 2>/dev/null; then
  # ship Phase 1 / where Step 1 이 `remote-sds/<target>` 로컬 tracking ref 참조
  git fetch remote-sds --quiet 2>&1 || {
    echo "warn: 등록은 성공했으나 fetch 실패. 인증/네트워크 확인 후 'git fetch remote-sds' 수동 실행 필요" >&2
  }
  echo "ok: registered ($EXPECTED_URL)"
  exit 0
fi

echo "error: 'git remote add remote-sds $EXPECTED_URL' 실패" >&2
exit 20
