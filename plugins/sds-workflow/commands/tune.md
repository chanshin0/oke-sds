---
description: 피드백을 sds 워크플로우(커맨드·템플릿·설정)에 구조화해 반영
argument-hint: "\"자유 형식 피드백\" | --review"
---


## Preamble

> 본문 실행 전 `${CLAUDE_PLUGIN_ROOT}/workflow/preamble.md` 를 Read 하여 공통 설정 로드 절차를 수행한다.

**튠 전용 추가 로드** — Phase 1·2 분류·영향 범위 판정에 필수:

- Read `${CLAUDE_PLUGIN_ROOT}/references/conventions.md` — 카테고리 enum·상태 enum·Handoff 포맷·acli fallback 표준
- Read `${CLAUDE_PLUGIN_ROOT}/references/artifact-types.md` — 문서 타입 레지스트리 (sync-points·영향 범위 자동 확장 규칙 포함)

# /tune

**은유**: 기체 **튜닝**. 비행 중 발견한 비효율·버그를 워크플로우 시스템(커맨드·템플릿·설정) 에 반영한다.

**목적**: 운용 중 발생하는 "이 커맨드가 이렇게 동작했으면 좋겠다" 같은 피드백을 구조화된 수정 제안 + 적용 로그로 변환. 현재는 피드백이 Slack/구두/개인 메모로 흩어지는 문제를 해결.

인자 `$ARGUMENTS`:
- `"자유 형식 피드백"` (기본) — 새 피드백 접수
- `--review` — `tune-log.md` 에서 `deferred` 상태 엔트리를 일괄 리뷰

---

## 모드 A: 피드백 접수 (기본)

### Phase 1: 피드백 분류

1. **카테고리 판정** — `references/conventions.md §1` 의 enum 을 SSOT 로 사용. 인라인 나열 금지. 현재 enum (요약):
   - `command-behavior` / `template` / `config` / `config-local` / `design-principle` / `convention` / `registry`
   - 각 카테고리의 소유자·대상 경로는 conventions 표 참조.
2. **1차 타겟 파일 식별** — Grep/Glob 로 피드백에서 언급된 커맨드명·섹션명·용어를 탐색해 **직접 수정 대상** 후보 1~N 개를 뽑는다.
3. **소유자 경계 확인** — conventions §1 의 `소유자` 열로 플러그인/저장소 구분. 플러그인 소유 파일은 현재 세션이 **플러그인 호스트 저장소** (`plugin/sds-workflow/...` 가 실재하는 repo) 에서 실행 중일 때만 직접 Edit 가능. 외부 저장소에서 실행 중이라면 "플러그인 repo 에 PR 필요" 안내 후 tune-log `deferred`.

### Phase 2: 수정 제안 초안

**Phase 2 시작 전 필수 Read**:
- `${CLAUDE_PLUGIN_ROOT}/references/artifact-types.md` — artifact 엔트리별 `Sync with` 목록 + "영향 범위 자동 확장 규칙" 7건

1. **Diff 초안** (기존 vs 신규) — 1차 타겟 파일 Read 후 구체적 Edit 지점 표기.
2. **영향 범위 자동 확장** — 1차 타겟의 artifact 타입을 레지스트리에서 찾아 `Sync with` 엔트리를 **2차 영향 후보**로 자동 포함. 추가로 "영향 범위 자동 확장 규칙" 에 해당하는 패턴이면 해당 규칙의 파생 파일도 포함.
   - 예: `command description` 변경 → 규칙 1 적용 → `README.md` 커맨드 표 + `SPEC.md` 커맨드 표 자동 포함.
   - 예: 카테고리 enum 변경 → 규칙 2 적용 → `commands/tune.md` Phase 1 리스트 + `seeds/tune-log.md` + `.team-workflow/tune-log.md` format 줄 자동 포함.
   - 누락 시 같은 피드백이 다른 파일에서 재발하므로 **자동 확장 결과는 Phase 3 확인창에 명시 출력**.
3. **리스크** — 기존 파일럿 E2E (`pick → ship → land → recap`) 에 영향 가능성.
4. **상태 초기값 판정** (conventions §2 enum 사용):
   - E2E 에 영향 없음 → `applied` 후보
   - E2E 에 영향 가능 → `needs-e2e` 후보 (사용자 확인 후 적용 여부 결정)
   - `SPEC.md` "확정 사항" 표 변경 또는 `references/{conventions,artifact-types}.md` 변경 → 추가 확인 질문 (철학·계약 변경은 파생 영향 큼)

### Phase 3: 🚦 그레이존 확인 (AskUserQuestion)

사용자에게 확인:

| 질문 | 선택지 |
|-----|-------|
| 이 수정을 지금 적용할까요? | 즉시 적용 / 대기 (deferred) / 폐기 (rejected) |
| 적용 시 브랜치는? | 현재 브랜치 / 새 브랜치 `chore/tune-{short-desc}` |
| (E2E 영향 감지 시) | 적용 강행 / needs-e2e 로 보류 |
| (SPEC.md 확정 사항 변경 시) | 철학 변경 확정 / 수정 사항 변경 철회 |

### Phase 4: 적용 + 기록

사용자 "즉시 적용" 선택 시:

1. **파일 수정** (Edit 툴로 Diff 적용).
2. **`.team-workflow/tune-log.md` 엔트리 추가**:
   ```
   ## {YYYY-MM-DD} — {short-desc-kebab}
   - 제출: {user}
   - 피드백 원문: "{원문}"
   - 카테고리: {category}
   - 적용 대상: {file-path#section}
   - 상태: applied
   - 커밋: {will-be-filled}
   - 메모: {1-2줄}
   ```
3. **커밋** — `git add` 수정 파일 + tune-log → 🚦 **커밋 메시지 승인 게이트**:
   - 기본 메시지: `chore: tune {short-desc}`
4. 커밋 후 `tune-log.md` 엔트리의 `커밋:` 필드에 실제 SHA 주입 → **amend 대신** 추가 커밋으로 로그 SHA 기록 (amend 금지 CLAUDE 규약 준수). 실용적 접근: `tune-log.md` 는 1차 커밋에 포함하고, SHA 는 엔트리에 생략 또는 `pending` 으로 두는 것도 허용.

사용자 "대기 (deferred)" 선택 시:
- 수정 없음. tune-log 엔트리만 추가 (`상태: deferred`).

사용자 "폐기 (rejected)" 선택 시:
- tune-log 엔트리만 추가 (`상태: rejected`). 이력 추적용.

### Phase 5: Handoff

```
┌──────────────────────────────────────────────┐
│ 튜닝 처리: {short-desc}                        │
│   상태: {applied / deferred / rejected}       │
│   커밋: {sha or "-"}                          │
│   tune-log: .team-workflow/tune-log.md        │
│                                               │
│ 대기 엔트리 리뷰 → /tune --review          │
└──────────────────────────────────────────────┘
```

---

## 모드 B: 대기 엔트리 리뷰 (`--review`)

1. `.team-workflow/tune-log.md` 로드 → `상태: deferred` 엔트리 추출
2. 각 엔트리별:
   - 피드백 원문 표시
   - 현재 적용 시 Diff 초안 재계산 (파일이 그동안 변경되었을 수 있음)
   - `AskUserQuestion`: 지금 적용 / 계속 대기 / 폐기
3. 선택에 따라 Phase 4 동일 처리.
4. 1주 이상 `deferred` 엔트리가 있으면 Handoff 에 경고 표시.

---

## 안전 장치

- **E2E 영향 자동 판정** — `needs-e2e` 로 표시 후 적용 보류.
- **SPEC.md 확정 사항 변경 시 추가 확인** — 파일럿 철학은 쉽게 바뀌면 안 됨.
- **Amend 금지** — 커밋 후 추가 커밋으로 SHA 기록.
- **파괴적 작업 금지** — 파일 삭제·브랜치 강제 삭제·force push 없음.

## 사람 개입 지점

- 수정 제안 Diff 검토·승인
- 즉시 적용 / 대기 / 폐기 선택
- 브랜치 전략 선택 (현재 브랜치 / 새 `chore/tune-*` 브랜치)
- 커밋 메시지 최종 승인

## 사람 미개입

- 피드백 카테고리 판정
- 대상 파일 후보 탐색
- Diff 초안 작성
- tune-log 엔트리 작성

## 원칙

- **이 커맨드는 워크플로우 시스템만 수정**. 제품 코드 (`src/**`) 수정은 대상 아님 — 그건 일반 이슈로 `/pick` 또는 `/draft` 사용.
- **모든 피드백은 기록** — 폐기되어도 이력은 남긴다 (같은 피드백이 반복 제기될 때 참조).
- **tune-log 는 gitignore 하지 않음** — 팀 공유 자산.
