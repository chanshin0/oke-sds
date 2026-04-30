---
description: 현재 주차 주간보고 페이지에서 **내 행만** Jira 이슈로 최신화
argument-hint: "[<page-id>] [--apply]"
---

## Preamble

> 본문 실행 전 `${CLAUDE_PLUGIN_ROOT}/workflow/preamble.md` 를 Read 하여 공통 설정 로드. 변수 `JIRA_BASE_URL`, `confluence.weekly_report.root_id` 추출.

# /weekly-report:update-mine

**은유**: 자기 좌석 보고서만 **본인이 적어 넣기**.

**목적**: 활성 스프린트 본인 이슈를 긁어 주간보고 페이지의 **본인 행** 금주/차주 셀만 교체. 다른 사람 영역은 절대 건드리지 않는다.

인자:
- `<page-id>` (선택) — 대상 페이지 ID. 생략 시 `confluence.weekly_report.root_id` 의 자식 중 최신 페이지 자동 선택.
- `--apply` — 실제 PUT. 기본은 dry-run.

---

## Phase 0: 사전 점검 + 필수 설정 검증

- `python3 --version` 성공.
- **`confluence.weekly_report.root_id` 검증**: 미설정/빈 값이면 즉시 중단:
  > "`confluence.weekly_report.root_id` 미설정. `/weekly-report:init` 또는 `.team-workflow/workflow.yml` 직접 편집으로 채운 뒤 재실행."
- `security find-generic-password -a "<EMAIL>" -s atlassian-api-token -w` 로 토큰 존재 확인. 없으면 중단: "`/weekly-report:init` 의 Phase 2 절차로 토큰 keychain 등록 필요."
  - `<EMAIL>` = `git config sds.atlassian.email` 우선, 없으면 `git config user.email`.
- **`WEEKLY_REPORT_GROUP_LABEL` env var 확인** (선택): 미설정 시 "TEAM" 기본 사용. stderr 로 1회 알림: "WEEKLY_REPORT_GROUP_LABEL 미설정 → 기본 'TEAM' 사용. 너의 팀 그룹 라벨이 다르면 export 필요."

## Phase 1: 대상 페이지 ID 결정

1. `$ARGUMENTS` 첫 토큰이 숫자면 그것을 page-id 로 사용.
2. 아니면 `confluence.weekly_report.root_id` 의 자식 페이지 목록에서 제목에 `(YY-MM-DD)` 형식 날짜가 가장 최근인 것을 선택. (REST: `GET /wiki/rest/api/content/<parent>/child/page?expand=version&limit=50` → 제목 정규식 `\((\d{2})-(\d{2})-(\d{2})\)$` 매치 후 정렬)
3. 결정된 page-id 를 사용자에게 1회 확인.

## Phase 2: dry-run 실행

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/weekly_report_update_mine.py" \
  --site "<HOST>" --page-id "<PAGE_ID>"
```

`<HOST>` = `JIRA_BASE_URL` 의 host 부분 (예: `<your-team>.atlassian.net`).

출력의 "금주 N / 차주 M" 항목 수와 dry-run diff 경로를 사용자에게 보여준다.

## Phase 3: 적용 결정

`$ARGUMENTS` 에 `--apply` 있으면 즉시 적용. 없으면 `AskUserQuestion`:
- "이 항목들로 본인 행을 갱신할까요?" → Yes / No

Yes 이면 동일 명령에 `--apply` 추가하여 재실행. No 면 종료.

## Phase 4: 완료 보고

PUT 성공 시 새 버전 번호와 페이지 URL 출력:
- `https://<HOST>/wiki/spaces/<SPACE>/pages/<PAGE_ID>`
