---
description: 현재 주차 주간보고 페이지의 **모든 담당자 행**을 Jira 이슈로 일괄 최신화
argument-hint: "[<page-id>] [--apply]"
---

## Preamble

> 본문 실행 전 `${CLAUDE_PLUGIN_ROOT}/workflow/preamble.md` 를 Read 하여 공통 설정 로드.

# /sds-workflow:weekly-report-update-all

**은유**: 항공기 전체 좌석을 **승무원이 일괄 점검**.

**목적**: 페이지 표의 모든 user 행 (account-id 가 있는 모든 `<tr>`) 을 각 담당자의 Jira 이슈로 일괄 갱신. **자기 토큰으로 다른 사람 데이터를 읽기/쓰기 가능한 권한**이 있어야 함 (보통 Jira 프로젝트 관리자급).

이 커맨드는 자동 스케줄에서 권장 — 한 명의 토큰으로 모두 채워두면 회의 시점에 표가 미리 차 있다.

인자:
- `<page-id>` (선택) — 생략 시 부모의 최신 자식 페이지 자동 선택.
- `--apply` — 실제 PUT.

---

## Phase 0: 사전 점검

- 토큰·이메일 — `weekly-report-update-mine` Phase 0 와 동일.
- 권한 경고 — 첫 1회는 사용자에게 "다른 담당자 이슈에도 접근 권한이 있는지" 확인.

## Phase 1: 대상 페이지 결정

`weekly-report-update-mine` Phase 1 과 동일.

## Phase 2: dry-run

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/weekly_report_update_all.py" \
  --site "<HOST>" --page-id "<PAGE_ID>"
```

출력의 사용자별 항목 수 표를 사용자에게 보여준다. "no items" 로 스킵된 사용자가 있으면 별도 표시.

## Phase 3: 적용 결정

`--apply` 없으면 `AskUserQuestion` 으로 확인 후 `--apply` 추가하여 재실행.

## Phase 4: 완료 보고

새 버전 번호 + 페이지 URL 출력. 갱신된 행 수와 스킵된 행 수 명시.
