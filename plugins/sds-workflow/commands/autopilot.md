---
description: 자율 운행 — pick → 구현 → ship 원샷 (다중 이슈 시 worktree 병렬)
argument-hint: "CDS-XXXX [CDS-YYYY ...] | \"자유 설명\" [--stop-at <phase>] [--dry-run] [--ralph]"
---


## Preamble

> 본문 실행 전 `${CLAUDE_PLUGIN_ROOT}/workflow/preamble.md` 를 Read 하여 공통 설정 로드 절차를 수행한다. 이 절차에서 추출한 `PROJECT_KEY` 등 변수를 이하 Phase 에서 사용한다. autopilot 은 내부에서 `pick`/`ship` 을 호출하므로 Preamble 을 1회만 수행한다.

# /autopilot

**은유**: 비행기 **자동조종**. 조종사(사람)는 이륙(목표 확정)·착륙(머지 판단) 게이트만 담당, 항로(구현·검증)는 오토파일럿이 수행.

**목적**: 사용자 워크플로우 1~5단계(`등록 → 계획 → 구현 → 검증 → MR`)를 한 호출로 자율 실행. 머지는 여전히 리뷰어 판단, 그 이후 `/land` → `/recap` 은 별도.

인자 `$ARGUMENTS`:
- `CDS-XXXX` (단일 이슈) 또는 `"자유 설명"` (필수, 후자는 `/draft` 선행)
- `CDS-XXXX CDS-YYYY [CDS-ZZZZ ...]` (다중 이슈, 공백 구분) — Phase 0 가 자동으로 다중 모드로 분기. 자유 프롬프트와 혼용 불가.
- `--stop-at <phase>` — 지정 단계까지만 실행. 값: `pick` / `plan-approved` / `implement` / `ship-preflight` / `mr` (다중 모드 시 각 subagent 에 그대로 전달)
- `--dry-run` — 경로만 출력, 실행 안 함
- `--ralph` — **모든 승인 게이트 스킵** (플랜 승인 / 커밋 메시지). 사용자 개입 없이 MR 출하까지 자동 진행. 안전장치(Deviation·UI 검증 실패·연속 실패 3회) 는 유지. 고위험 모드 — 의도된 호출에서만 사용. **다중 모드는 자동 강제** (단일 세션이 N개 게이트를 동시에 처리할 수 없기 때문).

---

## Phase 0: 인자 파싱 + 모드 결정

1. `$ARGUMENTS` 토큰화 (공백 분리). 옵션 플래그(`--stop-at <v>`, `--dry-run`, `--ralph`) 분리.
2. 남은 토큰 중 이슈키 정규식 `^(${PROJECT_KEYS.join('|')})-\d+$` 매칭 카운트 → `N`.
3. 분기:
   - **N == 0 + 자유 프롬프트 토큰** → 단일 모드. Phase A-1 에서 `/draft` 선행으로 이슈 생성 후 진입.
   - **N == 1** → 단일 모드. Phase A 진입.
   - **N >= 2** → **다중 모드**. Phase M 진입.
4. 다중 모드 사전 강제:
   - `--ralph` 자동 활성화 (사용자 미지정이어도). Handoff 에 "자동 강제" 표기.
   - 자유 프롬프트 토큰 동시 존재 → 중단: "다중 이슈 모드는 자유 프롬프트와 혼용 불가."
   - `--stop-at <phase>` 는 각 subagent 에 그대로 전달.
   - `--dry-run` 시 spawn 하지 않고 각 이슈에 대한 예상 워크트리 경로·브랜치명만 요약 후 종료.

## Phase A: 이륙 (pick + 플랜 승인 게이트)

### A-1. 이슈 확보

- 인자가 `CDS-XXXX` 패턴 → 그대로 사용
- 인자가 자유 프롬프트 → `/draft` 를 내부적으로 **순차 선행**. 생성된 이슈 키 확보 후 계속.
  - `/draft` 의 AskUserQuestion (타입·우선순위·assignee) 은 그대로 사용자에게 표시
  - 생성 승인 게이트는 그대로 유지

### A-2. `/pick` 실행

`/pick CDS-XXXX` 의 Phase 0~3 전부 실행:
- 저장소 맥락 런타임 추론 (package.json·tsconfig·CLAUDE.md·CONVENTIONS) — 아래 **A-2a 스코핑 규칙** 준수
- Phase 1 병렬 컨텍스트 수집 — A-2a 준수
- 브랜치 생성 + Jira 전환
- `.work/{issue_key}.md` 생성
- 플랜 자동 초안 + `EnterPlanMode`

### A-2a. 컨텍스트 스코핑 규칙 (입력 토큰 절감 — needs-e2e)

전 repo·전 문서 Read 는 입력 토큰 30~60K 를 소모한다. 아래 규칙으로 **이슈 범위에만** 국한한다:

1. **이슈 본문 경로 추출 우선** — Jira description·제목·코멘트에서 정규식 `src/[\w./\-]+`, `pkg/[\w./\-]+`, `plugin/[\w./\-]+` 매칭. 추출된 경로의 **상위 디렉토리 1단계** 까지만 Read/Glob 대상.
2. **CLAUDE.md / CONVENTIONS.md 헤딩 인덱스만 먼저 Read** — `grep -n '^##' <file>` 로 목차 확보. 본문은 이슈 범위 키워드와 매칭되는 섹션만 재Read.
3. **package.json 블록 한정** — `scripts` / `dependencies` 헤더 블록만 파싱. `devDependencies` / `engines` 등은 필요 시에만.
4. **tsconfig·vite/webpack** — `paths` alias 와 `include`/`exclude` 필드만. 전체 설정 Read 금지.
5. **경로 추출 실패 시 게이트** — 이슈 본문에 경로 단서가 전혀 없으면 `AskUserQuestion` 으로 "관련 모듈/경로 1~2개?" 1회 확인 후 진행. 게이트 없이 전 repo 스캔 금지.
6. **Phase B 에서 추가 Read 허용** — 구현 단계에서 스코핑 실패가 드러나면 그때 추가 Read. 사전 과적재보다 사후 보강이 저렴하다는 가정.

이 규칙은 `/pick` 단독 호출에도 동일 적용된다 (A-2 가 /pick Phase 0-1 을 그대로 실행하므로).

### A-3. 🚦 **플랜 승인 게이트** (사람 개입)

사용자가 플랜을 검토하고 `ExitPlanMode` 로 승인하기 전까지 Phase B 진입 금지. `EnterPlanMode` 가 구조적으로 차단.

`--stop-at pick` 또는 `--stop-at plan-approved` 시 여기서 종료.

**`--ralph` 시**: `EnterPlanMode` 를 호출하지 않고 플랜 초안만 `.work/{issue_key}.md` "## 플랜" 섹션에 기록한 뒤 Phase B 로 즉시 진입. 사용자 검토 없이 자동 승인으로 간주.

## Phase B: 구현 (단계별 + 편차 감지)

`EnterPlanMode` 해제 후:

1. 플랜의 "구현 접근" 섹션을 단계로 파싱.
2. 각 단계 순차 실행:
   - Edit / Write 툴로 파일 수정
   - 단계 완료 시 1줄 진행 보고 ("[{n}/{N}] {단계명} 완료")
3. **편차/그레이존 감지** — 아래 상황에서 `AskUserQuestion` 조종사 호출:
   - 플랜에 명시되지 않은 파일 수정 필요
   - 구현 중 새로운 트레이드오프 발견
   - 에러 / 빌드 실패
   - 테스트 작성 필요 여부 판단 불가
4. **안전 장치** — 한 단계에서 3회 이상 연속 실패 시 중단, 사용자 개입 요청.

### B-4. 병렬 Edit 판정 규칙 (needs-e2e)

플랜 단계가 서로 독립적인 파일을 수정하고 의존 관계가 없으면 병렬 실행 가능:

1. **독립성 판정** — 아래 조건 **모두** 충족 시 병렬 후보:
   - 대상 파일이 서로 다름 (동일 파일 수정 단계 = 병렬 금지)
   - 단계 사이 `import`/`export` 의존이 없음 (한 단계가 추가하는 export 를 다른 단계가 import 하지 않음)
   - 단계 설명이 명시적으로 "이후 단계에서 참조" 를 언급하지 않음
2. **토폴로지 정렬** — 의존 그래프를 세워 독립 단계 집합을 추출. 같은 레벨은 병렬, 다음 레벨로 넘어가기 전에 이전 레벨 완료 대기.
3. **단일 메시지 병렬 Edit** — 같은 집합의 Edit 툴 복수 호출을 한 메시지에 담아 호출.
4. **판정 불가 시 순차 디폴트** — 의존성 판단이 애매하면 보수적으로 순차 실행. "아마 독립" 으로 병렬 돌리지 않는다.
5. **병렬 실패 롤백** — 병렬 집합 중 하나라도 실패하면 집합 전체를 롤백 (Edit 역변환). 실패 단계 원인 로그 + 이후 단계는 순차 재시도.
6. **autopilot 다중 모드와의 관계** — Phase M 에서 이미 이슈 단위 병렬. B-4 는 **단일 이슈 내부** 단계 병렬. 다중 모드 + B-4 동시 적용 가능하지만 subagent 내부 병렬 로그가 복잡해질 수 있음 (debug 시 주의).

`--stop-at implement` 시 여기서 종료.

## Phase C: 검증 (ship Phase 0-1.8)

`/ship` 의 Phase 0 ~ 1.8 자동 실행:
- Phase 0 Deviation 체크 (편차 감지 시 자동 중단 → 사용자 개입)
- Phase 1 정적 검증 (lint / type-check / test 병렬)
- Phase 1.5 브라우저 검증 (UI 변경 시, `--skip-ui-check` 는 autopilot 에서 비활성)
- Phase 1.8 Goal-backward

**실패 시 중단** — 자동 재시도 금지. 사용자에게 결과 보고 후 지시 요청.

`--stop-at ship-preflight` 시 여기서 종료 (커밋·푸시·MR 없음).

## Phase D: 출하 (커밋 + 푸시 + MR)

`/ship` 의 Phase 2-3 실행:

### D-1. 커밋 메시지 draft 작성

### D-2. 🚦 **커밋 메시지 승인 게이트** (사람 개입)

사용자 승인 없이 커밋 금지. 수정 요청 루프.

**`--ralph` 시**: D-1 에서 작성한 draft 를 그대로 최종 메시지로 사용하고 승인 루프 없이 D-3 로 즉시 진행.

### D-3. 커밋 + 푸시 + MR 생성 + Jira 코멘트 (원본 Phase 2-3 그대로)

`--stop-at mr` 와 이 단계 완료는 동일 (기본 종료 지점).

## Phase E: Handoff

```
┌──────────────────────────────────────────────┐
│ 자율 순항 완료: {issue_key}                    │
│   MR: {url}                                    │
│   Jira: IN PROGRESS (머지 대기)                │
│                                               │
│ 사람 개입 횟수: {n}/4 (목표 ≤2)                │
│   - 플랜 승인 (필수)                           │
│   - 그레이존 답변 (발생 시만)                   │
│   - 커밋 메시지 승인 (필수)                    │
│   - (UI 검증 실패 / Goal-backward 의문)         │
│                                               │
│ 다음: 머지 후 → /land {issue_key} →        │
│                  /recap {issue_key}        │
└──────────────────────────────────────────────┘
```

## Phase M: 다중 이슈 병렬 실행 (Phase 0 가 다중 모드 판정 시)

**전제**: Phase 0 가 N >= 2 로 판정 + `--ralph` 강제 활성화 + 자유 프롬프트 미혼용.

### M-1. 사전 점검

1. **이슈 존재·접근 검증**: 각 이슈 키에 대해 `acli jira workitem view {issue_key} --json` 병렬 실행 (단일 메시지 병렬). 실패한 이슈는 Handoff 의 "실패 목록" 으로 분리, 나머지는 진행.
2. **working tree clean 강제**: `git status --porcelain` 결과가 비어있어야 함. dirty 면 중단: "다중 모드는 깨끗한 working tree 가 필요. stash 또는 commit 후 재시도."
3. **워크트리 충돌 방지**: 각 이슈 키마다 워크트리 경로가 이미 존재하는지 사전 검사. 존재 시 사용자에게 안내 ("기존 워크트리 정리 후 재시도").

### M-2. 병렬 subagent spawn (단일 메시지, 병렬)

각 이슈 키마다 Task agent 1개를 **단일 메시지 내 병렬 호출**로 spawn.

- `subagent_type`: `general-purpose`
- `description`: `"autopilot {issue_key}"` (12자 내외)
- `isolation`: `"worktree"` — 자동 임시 git worktree 생성 + 그 안에서 agent 실행. 종료 시 변경 있으면 path/branch 반환, 없으면 자동 정리.
- `prompt`: 다음 골자로 self-contained 작성 —
  - 컨텍스트: 저장소 목적·`CONVENTIONS.md` 위치·`CLAUDE.md` 위치
  - 임무: "이 워크트리 안에서 `/sds-workflow:autopilot {issue_key} --ralph [--stop-at <phase>]` 를 실행하고, 결과를 한 줄 표 형태(`{issue_key} | {결과} | {MR URL or 사유} | {워크트리 경로} | {브랜치명}`)로 반환하라."
  - **그레이존 처리**: `AskUserQuestion` 등 사용자 입력 도구는 부모 세션에서만 동작. 그레이존 발생 시
    (1) `CONVENTIONS.md` / `CLAUDE.md` 기준으로 보수적 자율 결정 → (2) 결정 근거를 `.work/{issue_key}.md` 의
    "## 결정 메모" 섹션에 기록 → (3) 진행. 진정으로 모호하면 `failed` 로 즉시 반환.
  - **환경 정체 fail-fast**: 어떤 외부 프로세스(lint·build·network) 든 진행 없이 90초 이상 대기하면
    즉시 중단하고 `failed | <단계> stalled` 로 반환. 부모가 resume 할 수단 없음 (SendMessage 미배포 환경).
  - **lockfile 보호**: `pnpm-lock.yaml` / `package-lock.json` / `yarn.lock` 은 의존성을 명시적으로
    추가/제거한 경우가 아니면 절대 commit 하지 말 것. 환경(패키지 매니저 버전) 차이로 인한 lockfile
    diff 는 `git checkout HEAD -- <lockfile>` 로 되돌릴 것.
  - 종료 조건: Phase D 완료 또는 `--stop-at` 지점 도달 또는 안전장치 트리거 시 즉시 보고

각 subagent 내부에서는 단일 모드 Phase A-E 가 실행된다 (`--ralph` 라 게이트 없음).

### M-3. 결과 aggregate

각 subagent 가 반환하는 페이로드:
- 이슈 키
- 결과 상태: `success` / `partial` (`--stop-at` 도달) / `failed`
- MR URL (성공 시) 또는 폴백 사유 (`MR-pending`) 또는 실패 단계
- 워크트리 경로 + 브랜치명

부모 세션은 결과를 다음 표로 집계:

| 이슈 | 결과 | MR | 워크트리 | 브랜치 |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

워크트리는 **자동 정리하지 않음** (사용자가 머지·정리 판단).

### M-4. Handoff (다중 모드 전용)

```
┌─────────────────────────────────────────────────┐
│ 다중 자율 순항 완료                              │
│   요청 이슈: {N} 개                              │
│   성공: {S} / 부분(stop-at 도달): {P} / 실패: {F}│
│   --ralph 자동 강제: yes                         │
│                                                 │
│ [성공 / 부분]                                    │
│   {issue_key_1}: {url} (워크트리 {path})        │
│   {issue_key_2}: {url} (워크트리 {path})        │
│   ...                                           │
│                                                 │
│ [실패]                                           │
│   {issue_key_x}: {실패 단계} - {원인}           │
│                                                 │
│ 다음:                                            │
│  각 워크트리에서 머지 검토 → /land {key} →       │
│                              /recap {key}        │
│  워크트리 정리: git worktree remove <path>       │
└─────────────────────────────────────────────────┘
```

---

## 사람 개입 지점 (의도적 게이트, 단일 모드 기준 총 2-4회)

| # | 게이트 | 시점 | 단일 모드 | 다중 모드 (Phase M) |
|---|-------|------|---------|------------------|
| 1 | 플랜 승인 | Phase A-3 | 필수 (`--ralph` 시 스킵) | 자동 스킵 (--ralph 강제) |
| 2 | 그레이존 답변 | Phase B / Phase C | 발생 시만 (`--ralph` 시에도 유지) | subagent 내부에서 발생 시 해당 subagent 만 일시 정지 |
| 3 | 커밋 메시지 승인 | Phase D-2 | 필수 (`--ralph` 시 스킵) | 자동 스킵 (--ralph 강제) |
| 4 | UI/Goal-backward 실패 시 중단 지시 | Phase C | 발생 시만 (`--ralph` 시에도 유지) | 발생 subagent 만 실패 처리, 다른 subagent 는 계속 |

## 사람 미개입 (자동 실행)

- 컨텍스트 수집·브랜치 생성·Jira 전이
- 구현 단계 전환 (플랜의 단계별 진행)
- 정적 검증 실행 판단
- MR 본문 작성·Jira 코멘트

## 안전 장치

- **플랜 미승인 상태에서 구현 진입 불가** — `EnterPlanMode` 구조적 차단 (`--ralph` 예외)
- **Deviation 체크 유지** — `/ship` Phase 0 편차 감지 시 자동 중단 → 사용자 개입 (`--ralph` 시에도 유지)
- **`--stop-at <phase>`** — 의도적 중단 지점. 값: `pick` / `plan-approved` / `implement` / `ship-preflight` / `mr`
- **`--dry-run`** — 경로만 출력, 실제 실행 없음. Phase 별 예상 입출력 요약
- **`--ralph`** — 승인 게이트(플랜·커밋 메시지) 만 스킵. Deviation·UI 실패·Goal-backward 의문·연속 실패 3회 등 나머지 안전장치는 유지.
- **연속 실패 차단** — 한 단계 3회 연속 실패 시 중단
- **다중 모드 working tree clean 강제** — Phase M-1 에서 `git status --porcelain` 비어있지 않으면 중단. 부모 세션의 미커밋 변경이 subagent 워크트리에 새어들어가는 것 방지.
- **다중 모드 워크트리 격리** — Phase M-2 의 `isolation: "worktree"` 가 각 subagent 에 임시 워크트리를 부여. 같은 파일을 여러 이슈가 동시에 건드려도 부모 working tree 와 분리됨. 다만 같은 원격 브랜치명 충돌은 `/pick` 의 brand 생성 단계에서 검출 → 해당 subagent 만 실패로 보고.
- **다중 모드 subagent self-contained 종료** — Phase M-2 spec 상 subagent 는 부모와 비동기. SendMessage resume 은 Claude Code 환경별로 미배포(2026-04 ceph-web-ui 검증). 환경 정체·중단 시 subagent 가 즉시 fail-fast 종료하도록 prompt 에 90초 stall 규칙 강제. 부모는 살아있는 agent 를 재개할 수단이 없으므로, 정체 = 손실로 간주.
- **다중 모드 lockfile 회귀 차단** — subagent 환경의 패키지 매니저 버전 차이가 `pnpm-lock.yaml` 등을 downgrade 시키는 사례 관측(2026-04 다중 모드 첫 실전). spawn prompt 에 lockfile 보호 규칙(의존성 명시 추가/제거가 아니면 commit 금지) 강제.

## 원칙

- 자율 실행이되 **머지는 여전히 사람**. `/autopilot` 은 MR 출하까지만.
- 게이트 1·3 은 기본 **우회 불가**. `--ralph` 는 이 게이트만 명시적으로 스킵하는 옵트인 플래그이며, `--force` 같은 모든 안전장치 우회는 제공하지 않는다.
- `--skip-ui-check` 는 autopilot 에서 비활성 — UI 검증 생략은 사람의 명시적 선택이어야 함.
- 복잡도가 높은 이슈 (여러 도메인 교차, 외부 API 계약 변경 등) 는 `/pick` 개별 호출 권장. autopilot 은 **Trivial ~ Medium** 복잡도에 최적.
- `--ralph` 는 플랜·커밋 메시지 품질을 사람이 검토하지 않으므로 리뷰 단계에서 리뷰어 부담 증가 가능. 반복 패턴·저위험 이슈에 한정 권장.
- **다중 모드는 의도된 batch 작업** — 비슷한 패턴의 trivial 이슈 여러 건을 한 번에 처리할 때만 사용. 도메인이 교차하거나 서로 의존하는 이슈는 단일 모드에서 순차 처리해야 충돌·재작업이 줄어든다.
- **다중 모드는 워크트리 정리 책임이 사용자에게 있음** — `/autopilot` 은 워크트리를 자동 삭제하지 않는다. 머지 후 `git worktree remove <path>` 수동 실행.
