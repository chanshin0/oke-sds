---
description: 다음 주차 주간보고 페이지를 가장 최근 페이지 템플릿으로 자동 생성
argument-hint: "[--source-id <ID>] [--apply]"
---

## Preamble

> 본문 실행 전 `${CLAUDE_PLUGIN_ROOT}/workflow/preamble.md` 를 Read.

# /weekly-report:create

**은유**: 다음 비행을 위한 **빈 좌석표 템플릿** 펼치기.

**목적**: 가장 최근 주간보고 페이지를 템플릿 삼아 다음 주차 페이지를 부모 위치에 생성. 모든 담당자 행은 비어 있는 상태로 만들어 각자 `/weekly-report:update-mine` 으로 채우거나 `/weekly-report:update-all` 일괄 갱신을 받도록 한다.

신규 페이지 제목 규칙: 소스 페이지 제목의 날짜에 +7 일, 월/주차 재계산.
예: `4월 5주차 주간 보고 (26-04-27)` → `5월 2주차 주간 보고 (26-05-04)`.

인자:
- `--source-id <ID>` — 명시 시 해당 페이지를 템플릿으로. 생략 시 `confluence.weekly_report.template_source_id` 또는 부모 자식 중 최신.
- `--apply` — 실제 POST. 기본은 dry-run.

---

## Phase 0: 사전 점검 + 필수 설정 검증

- 토큰·이메일 — 동일.
- **`.team-workflow/workflow.yml` 의 `confluence.weekly_report.root_id` 검증**:
  - 미설정 또는 빈 값이면 즉시 중단 + 안내:
    > "`confluence.weekly_report.root_id` 가 설정되지 않았습니다. 다음 중 하나로 설정 후 재실행:
    > - `/weekly-report:init` 호출 (대화형 안내)
    > - `.team-workflow/workflow.yml` 의 `confluence.weekly_report.root_id` 에 직접 입력 (Confluence 주간보고 루트 페이지 ID)"
- **Atlassian API 토큰 keychain 등록 확인**:
  - `security find-generic-password -s atlassian-api-token -a "<EMAIL>" -w` 호출
  - 실패 시 중단 + 안내: "`/weekly-report:init` 의 Phase 2 절차로 토큰 keychain 등록 필요."

## Phase 1: 소스 페이지 결정

1. `--source-id` 있으면 그것 사용.
2. 없고 `template_source_id` 있으면 그것.
3. 둘 다 없으면 `root_id` 의 자식 중 제목 날짜 기준 최신 페이지 자동 선택.

## Phase 2: dry-run

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/weekly_report_create.py" \
  --site "<HOST>" --source-id "<SOURCE_ID>"
```

출력의 새 제목과 비어진 body 크기 변화를 사용자에게 보여준다.

## Phase 3: 적용 결정

`--apply` 없으면 `AskUserQuestion` 으로 확인. Yes 이면 `--apply` 추가하여 재실행.

## Phase 4: 사후 처리

POST 성공 후:
- 새 페이지 ID 와 URL 출력
- (선택) `template_source_id` 를 새 페이지 ID 로 갱신할지 물어봄 → 다음 주에 자동으로 더 최신 페이지에서 시작됨
- (선택) 곧바로 `/weekly-report:update-all` 을 실행하여 새 페이지를 미리 채울지 안내
