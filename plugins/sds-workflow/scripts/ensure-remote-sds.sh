#!/usr/bin/env bash
# ensure-remote-sds.sh — 팀 공용 고정 remote `remote-sds` 등록 보장
#
# 사용법:
#   ensure-remote-sds.sh <gitlab_base_url> <gitlab_project_path>
#
# 동작:
#   1. `git remote get-url remote-sds` 시도
#   2a. 존재 + URL 일치 → stdout "ok: already-registered"; exit 0 (fetch 생략 — 사용자 타이밍 존중)
#   2b. 존재 + URL 불일치 → stderr warn + stdout "warn: url-mismatch"; exit 10
#        (호출측이 AskUserQuestion 으로 교체/유지 결정)
#   3. 존재 안 함 → `git remote add remote-sds <URL>` + `git fetch remote-sds --quiet`
#        → stdout "ok: registered"; exit 0
#        (fetch 가 필요한 이유: ship Phase 1 / where Step 1 이 `remote-sds/<target>` 로컬
#         tracking ref 를 참조. fetch 없이는 `unknown revision` 으로 실패)
#
# 치명적 실패:
#   - 입력 부족 → exit 20
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

# 빈 문자열 방어 (Preamble 이 기본값 안 주면 조용히 실패하므로 명시적 체크)
if [[ -z "$GITLAB_BASE_URL" || -z "$GITLAB_PROJECT_PATH" ]]; then
  echo "error: gitlab_base_url 또는 gitlab_project_path 가 비어있다. .team-workflow/workflow.yml 의 gitlab 섹션 확인 필요" >&2
  exit 20
fi

EXPECTED_URL="${GITLAB_BASE_URL%/}/${GITLAB_PROJECT_PATH}.git"

if EXISTING="$(git remote get-url remote-sds 2>/dev/null)"; then
  # 마지막 .git 은 optional (사용자가 .git 없이 add 했을 수도). 비교는 normalize.
  normalize() { printf '%s' "${1%.git}"; }
  if [[ "$(normalize "$EXISTING")" == "$(normalize "$EXPECTED_URL")" ]]; then
    echo "ok: already-registered ($EXISTING)"
    exit 0
  fi
  echo "warn: url-mismatch existing=$EXISTING expected=$EXPECTED_URL" >&2
  echo "warn: url-mismatch"
  exit 10
fi

if git remote add remote-sds "$EXPECTED_URL" 2>/dev/null; then
  # 신규 등록 직후 fetch — ship Phase 1 의 vitest diff base (`remote-sds/<target>...HEAD`)
  # 와 where Step 1 의 로컬 커밋 감지가 로컬 tracking ref 를 필요로 하기 때문.
  # `--quiet` 로 진행 출력 억제 (호출측 stdout 오염 방지).
  # `|| true` — fetch 실패해도 등록 자체는 성공으로 간주 (다음 push/fetch 시 재시도 기회).
  git fetch remote-sds --quiet 2>&1 || true
  echo "ok: registered ($EXPECTED_URL)"
  exit 0
fi

echo "error: git remote add remote-sds 실패 ($EXPECTED_URL)" >&2
exit 20
