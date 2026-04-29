#!/usr/bin/env bash
# create-mr.sh — /ship Phase 3-2
#
# 사용법:
#   create-mr.sh <source_branch> <target_branch> <title> <body_file> [gitlab_base_url] [gitlab_project_path]
#
# 3-layer 폴백 체인 (결정성 순):
#   1차: GitLab REST API (curl + PRIVATE-TOKEN).
#        project_path 를 URL 에 명시 박음 → 다중 remote 혼동 면역. 성공 → stdout=MR URL, exit 0.
#   2차: glab mr create (REST 미가용 시 — 토큰 추출 실패·네트워크 이슈 등).
#        정상 환경에서는 성공. 다중 remote (origin=fork 등) 환경에서는 source 오인식 가능.
#        성공 → stdout=MR URL, exit 0.
#   3차: 프리필 URL (브라우저 클릭용). 두 자동 경로 실패 시.
#        stdout=프리필 URL, exit 10 (폴백 신호 — 호출측은 MR 미확정으로 처리).
#   치명적 실패 (필수 입력 누락 / remote 파싱 불가 등): stderr 메시지, exit 20.
#
# 토큰 탐색 순 (1차 REST 용):
#   1) $GITLAB_TOKEN 환경변수
#   2) `glab config get token --host <host>` (glab 인증돼 있으면 자동)
#   없으면 1차 스킵하고 2차 진행.
#
# gitlab_base_url / gitlab_project_path 가 빈 문자열이면 `git remote get-url remote-sds` 에서 파싱.
# `remote-sds` 는 팀 공용 고정 remote 이름. `/sds-workflow:init` Phase 4.5 가 자동 등록한다.
# 본문 8KB 초과 시 프리필 URL 의 description 은 "원본 파일 참조" 로 대체 (URL 길이 안전장치).

set -euo pipefail

SOURCE_BRANCH="${1:?source_branch required}"
TARGET_BRANCH="${2:?target_branch required}"
TITLE="${3:?title required}"
BODY_FILE="${4:?body_file required}"
GITLAB_BASE_URL="${5:-}"
GITLAB_PROJECT_PATH="${6:-}"

[[ -f "$BODY_FILE" ]] || { echo "body_file not found: $BODY_FILE" >&2; exit 20; }

# --- 공통: base_url / project_path 확정 (REST API 와 프리필 URL 둘 다 필요) ---
if [[ -z "$GITLAB_BASE_URL" || -z "$GITLAB_PROJECT_PATH" ]]; then
  REMOTE="$(git remote get-url remote-sds 2>/dev/null || true)"
  if [[ -z "$REMOTE" ]]; then
    echo "no git remote 'remote-sds' — /sds-workflow:init 재실행 또는 'git remote add remote-sds <URL>' 필요" >&2
    exit 20
  fi
  if ! PARSED="$(python3 - "$REMOTE" <<'PY'
import re, sys
r = sys.argv[1].strip()
m = re.match(r'^git@([^:]+):(.+?)(?:\.git)?$', r)
if m:
    print(f"https://{m.group(1)}\t{m.group(2)}")
    sys.exit(0)
m = re.match(r'^(https?://[^/]+)/(.+?)(?:\.git)?$', r)
if m:
    print(f"{m.group(1)}\t{m.group(2)}")
    sys.exit(0)
sys.exit(1)
PY
  )"; then
    echo "failed to parse git remote: $REMOTE" >&2
    exit 20
  fi
  [[ -z "$GITLAB_BASE_URL" ]] && GITLAB_BASE_URL="$(printf '%s' "$PARSED" | cut -f1)"
  [[ -z "$GITLAB_PROJECT_PATH" ]] && GITLAB_PROJECT_PATH="$(printf '%s' "$PARSED" | cut -f2)"
fi

# --- 1차: GitLab REST API ---
# Host 는 GITLAB_BASE_URL 에서 scheme 제거 (glab config get token --host 용).
GITLAB_HOST="$(printf '%s' "$GITLAB_BASE_URL" | sed -E 's|^https?://||; s|/.*$||')"

# 토큰 탐색
TOKEN="${GITLAB_TOKEN:-}"
if [[ -z "$TOKEN" ]] && command -v glab >/dev/null 2>&1; then
  TOKEN="$(glab config get token --host "$GITLAB_HOST" 2>/dev/null || true)"
fi

if [[ -n "$TOKEN" ]] && command -v curl >/dev/null 2>&1; then
  REST_URL="${GITLAB_BASE_URL%/}/api/v4/projects/$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote_plus(sys.argv[1]))" "$GITLAB_PROJECT_PATH")/merge_requests"

  PAYLOAD="$(python3 - "$SOURCE_BRANCH" "$TARGET_BRANCH" "$TITLE" "$BODY_FILE" <<'PY'
import json, sys
src, tgt, title, body_file = sys.argv[1:5]
with open(body_file) as f:
    desc = f.read()
print(json.dumps({
    "source_branch": src,
    "target_branch": tgt,
    "title": title,
    "description": desc,
    "remove_source_branch": True,  # 원격 브랜치만 삭제. 로컬 working copy 무관.
}))
PY
  )"

  # mktemp + trap — 하드코딩 /tmp 경로 제거 (race·멀티유저 노출 방지, 권한 600).
  RESP_FILE="$(mktemp -t create-mr-rest.XXXXXX)"
  CURL_ERR_FILE="$(mktemp -t create-mr-curl-err.XXXXXX)"
  # shellcheck disable=SC2064 — 변수 값을 즉시 고정 (trap 발동 시점 변수 덮이기 방지)
  trap "rm -f '$RESP_FILE' '$CURL_ERR_FILE'" EXIT INT TERM

  # Token 을 argv 에 실으면 ps/proc/cmdline 에 노출됨. `-K -` (config from stdin)
  # 로 header 를 stdin 파이프로 전달 → argv 밖으로 분리.
  HTTP_CODE="$(curl -sS -o "$RESP_FILE" -w '%{http_code}' \
    -X POST \
    --data-binary "$PAYLOAD" \
    -K - \
    "$REST_URL" 2>"$CURL_ERR_FILE" <<CONFIG || echo "000"
header = "PRIVATE-TOKEN: $TOKEN"
header = "Content-Type: application/json"
CONFIG
  )"

  if [[ "$HTTP_CODE" == "201" ]]; then
    MR_URL="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['web_url'])" "$RESP_FILE" 2>/dev/null || true)"
    if [[ -n "$MR_URL" ]]; then
      printf '%s\n' "$MR_URL"
      exit 0
    fi
  elif [[ "$HTTP_CODE" == "409" ]] || grep -q 'Another open merge request already exists' "$RESP_FILE" 2>/dev/null; then
    # 이미 열린 MR 있음 — IID 추출해서 URL 조립
    EXISTING_IID="$(python3 -c "
import json, re, sys
try:
    d = json.load(open(sys.argv[1]))
    msg = d.get('message', [])
    if isinstance(msg, list):
        msg = ' '.join(str(x) for x in msg)
    m = re.search(r'!(\d+)', str(msg))
    if m:
        print(m.group(1))
except Exception:
    pass
" "$RESP_FILE" 2>/dev/null || true)"
    if [[ -n "$EXISTING_IID" ]]; then
      MR_URL="${GITLAB_BASE_URL%/}/${GITLAB_PROJECT_PATH}/-/merge_requests/${EXISTING_IID}"
      printf '%s\n' "$MR_URL"
      exit 0
    fi
  fi

  # 실패 진단 — curl stderr 와 HTTP status 를 보존해 상위로 전달.
  CURL_DIAG=""
  if [[ -s "$CURL_ERR_FILE" ]]; then
    CURL_DIAG=" curl-stderr: $(tr '\n' ' ' <"$CURL_ERR_FILE")"
  fi
  echo "REST API failed (HTTP $HTTP_CODE)${CURL_DIAG} — falling back to glab" >&2
fi

# --- 2차: glab mr create ---
# REST API 가 가용 안 한 환경 (토큰 없음·curl 없음·네트워크 이슈) 안전망.
# 정상 환경에서는 동작. 다중 remote 환경에서는 source 오인식 가능 (알려진 제약).
if command -v glab >/dev/null 2>&1; then
  GLAB_ARGS=(
    --source-branch "$SOURCE_BRANCH"
    --target-branch "$TARGET_BRANCH"
    --title "$TITLE"
    --description-file "$BODY_FILE"
    --yes
  )
  if [[ -n "$GITLAB_PROJECT_PATH" ]]; then
    GLAB_ARGS=(--repo "$GITLAB_PROJECT_PATH" "${GLAB_ARGS[@]}")
  fi
  if GLAB_OUT="$(glab mr create "${GLAB_ARGS[@]}" 2>&1)"; then
    MR_URL="$(printf '%s\n' "$GLAB_OUT" | grep -oE 'https?://[^[:space:]]+/merge_requests/[0-9]+' | tail -1 || true)"
    if [[ -n "$MR_URL" ]]; then
      printf '%s\n' "$MR_URL"
      exit 0
    fi
    echo "glab succeeded but no MR URL in output — falling back" >&2
  else
    echo "glab failed — falling back to prefill URL" >&2
  fi
fi

# --- 3차: 프리필 URL 폴백 ---
BODY_SIZE=$(wc -c <"$BODY_FILE")
if (( BODY_SIZE > 8000 )); then
  DESC_BODY="본문이 URL 길이 한계를 초과하여 포함 불가. \`${BODY_FILE}\` 내용을 복사해 description 에 붙여넣으세요."
else
  DESC_BODY="$(cat "$BODY_FILE")"
fi

python3 - "$SOURCE_BRANCH" "$TARGET_BRANCH" "$TITLE" "$GITLAB_BASE_URL" "$GITLAB_PROJECT_PATH" "$DESC_BODY" <<'PY'
import sys, urllib.parse
src, tgt, title, base, proj, body = sys.argv[1:7]
params = {
    "merge_request[source_branch]": src,
    "merge_request[target_branch]": tgt,
    "merge_request[title]": title,
    "merge_request[description]": body,
}
print(f"{base.rstrip('/')}/{proj.strip('/')}/-/merge_requests/new?" + urllib.parse.urlencode(params))
PY
exit 10
