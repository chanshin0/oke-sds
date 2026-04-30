---
description: 자율 운행 — pick → 구현 → ship 원샷 (다중 이슈 시 worktree 병렬)
argument-hint: "CDS-XXXX [CDS-YYYY ...] | \"자유 설명\" [--stop-at <phase>] [--dry-run]"
entry-mode: autopilot
required-permission: bypass
---


## Preamble

> 본문 실행 전 `${CLAUDE_PLUGIN_ROOT}/workflow/preamble.md` 를 Read 하여 공통 설정 로드 절차를 수행한다. 이 절차에서 추출한 `PROJECT_KEY` 등 변수를 이하 Phase 에서 사용한다. autopilot 은 내부에서 `pick`/`ship` 을 호출하므로 Preamble 을 1회만 수행한다.

# /autopilot

**은유**: 비행기 **자동조종**. 조종사(사람)는 이륙(목표 확정)·착륙(머지 판단) 게이트만 담당, 항로(구현·검증)는 오토파일럿이 수행.

**목적**: 사용자 워크플로우 1~5단계(`등록 → 계획 → 구현 → 검증 → MR`)를 한 호출로 **끝까지 자율 실행**. 머지는 여전히 리뷰어 판단, 그 이후 `/land` 는 별도.

**자율 디폴트** (2026-04-29 폐기 정리): 플랜 승인·커밋 메시지 승인 게이트는 더 이상 사람 개입을 요구하지 않는다. autopilot 은 항상 끝까지 진행하며, 사용자 개입은 안전장치 트리거(Deviation·UI 검증 실패·Goal-backward 의문·연속 실패) 시에만 발생한다. 검토를 원하는 흐름은 `/pick` → 수동 구현 → `/ship` 분리 사용을 권장.

인자 `$ARGUMENTS`:
- `CDS-XXXX` (단일 이슈) 또는 `"자유 설명"` (필수, 후자는 `/draft` 선행)
- `CDS-XXXX CDS-YYYY [CDS-ZZZZ ...]` (다중 이슈, 공백 구분) — Phase 0 가 자동으로 다중 모드로 분기. 자유 프롬프트와 혼용 불가.
- `--stop-at <phase>` — 지정 단계까지만 실행. 값: `pick` / `implement` / `ship-preflight` / `mr` (다중 모드 시 각 subagent 에 그대로 전달)
- `--dry-run` — 경로만 출력, 실행 안 함

---

## Phase 0: 인자 파싱 + 모드 결정 + 시작 시각 기록

1. `$ARGUMENTS` 토큰화 (공백 분리). 옵션 플래그(`--stop-at <v>`, `--dry-run`) 분리.
2. 남은 토큰 중 이슈키 정규식 `^(${PROJECT_KEYS.join('|')})-\d+$` 매칭 카운트 → `N`.
3. 분기:
   - **N == 0 + 자유 프롬프트 토큰** → 단일 모드. Phase A-1 에서 `/draft` 선행으로 이슈 생성 후 진입.
   - **N == 1** → 단일 모드. Phase A 진입.
   - **N >= 2** → **다중 모드**. Phase M 진입.
4. 다중 모드 사전 점검:
   - 자유 프롬프트 토큰 동시 존재 → 중단: "다중 이슈 모드는 자유 프롬프트와 혼용 불가."
   - `--stop-at <phase>` 는 각 subagent 에 그대로 전달.
   - `--dry-run` 시 spawn 하지 않고 각 이슈에 대한 예상 워크트리 경로·브랜치명만 요약 후 종료.
5. **시작 시각 기록 (1차 메트릭)** — `--dry-run` 이 아니면 `date +%s` 와 `date -Iseconds` (또는 `date '+%Y-%m-%dT%H:%M:%S%z'`) 출력을 캡처해 `START_EPOCH` 변수에 보관. Phase A-2 에서 `.work/{issue_key}.md` 가 생성되면 "## 메트릭" 섹션의 `start_epoch:` / `start_iso:` 라인에 기록 (work-context.md 템플릿 구조 참조). 다중 모드는 각 subagent 가 자기 워크트리에서 같은 절차로 자기 시작 시각을 기록.

## Phase A: 이륙 (pick)

### A-1. 이슈 확보

- 인자가 `CDS-XXXX` 패턴 → 그대로 사용
- 인자가 자유 프롬프트 → `/draft` 를 내부적으로 **순차 선행**. 생성된 이슈 키 확보 후 계속.
  - `/draft` 의 그레이존 질문(타입·우선순위·assignee)은 그대로 사용자에게 표시 (이슈 생성은 의도적 사람 결정)

### A-2. `/pick` 실행

`/pick CDS-XXXX` 의 Phase 0~3 전부 실행:
- 저장소 맥락 런타임 추론 (package.json·tsconfig·CLAUDE.md·CONVENTIONS) — 아래 **A-2a 스코핑 규칙** 준수
- Phase 1 병렬 컨텍스트 수집 — A-2a 준수
- 브랜치 생성 + Jira 전환
- `.work/{issue_key}.md` 생성
- 플랜 자동 초안 → `.work/{issue_key}.md` "## 플랜" 섹션에 기록 (`EnterPlanMode` 호출 안 함)

### A-2a. 컨텍스트 스코핑 규칙 (입력 토큰 절감 — needs-e2e)

전 repo·전 문서 Read 는 입력 토큰 30~60K 를 소모한다. 아래 규칙으로 **이슈 범위에만** 국한한다:

1. **이슈 본문 경로 추출 우선** — Jira description·제목·코멘트에서 정규식 `src/[\w./\-]+`, `pkg/[\w./\-]+`, `plugin/[\w./\-]+` 매칭. 추출된 경로의 **상위 디렉토리 1단계** 까지만 Read/Glob 대상.
2. **CLAUDE.md / CONVENTIONS.md 헤딩 인덱스만 먼저 Read** — `grep -n '^##' <file>` 로 목차 확보. 본문은 이슈 범위 키워드와 매칭되는 섹션만 재Read.
3. **package.json 블록 한정** — `scripts` / `dependencies` 헤더 블록만 파싱. `devDependencies` / `engines` 등은 필요 시에만.
4. **tsconfig·vite/webpack** — `paths` alias 와 `include`/`exclude` 필드만. 전체 설정 Read 금지.
5. **경로 추출 실패 시 보수적 자율 결정** — 이슈 본문에 경로 단서가 전혀 없으면 `CONVENTIONS.md` / `CLAUDE.md` 의 도메인 매핑 규칙으로 추론하고 결정 근거를 `.work/{issue_key}.md` "## 결정 메모" 에 기록 후 진행. 추론 근거가 약하면 `failed` 로 즉시 종료 (전 repo 스캔 금지).
6. **Phase B 에서 추가 Read 허용** — 구현 단계에서 스코핑 실패가 드러나면 그때 추가 Read. 사전 과적재보다 사후 보강이 저렴하다는 가정.

이 규칙은 `/pick` 단독 호출에도 동일 적용된다 (A-2 가 /pick Phase 0-1 을 그대로 실행하므로).

### A-3. 페이즈 코멘트 (단일 모드만)

`/pick` 완료 후 `${CLAUDE_PLUGIN_ROOT}/workflow/templates/jira-comment-pick.md` 로드 → 플레이스홀더 치환 → `.work/{issue_key}-pick-comment.md` 저장 → `${CLAUDE_PLUGIN_ROOT}/scripts/jira-comment.sh {issue_key} @.work/{issue_key}-pick-comment.md` 호출.

플레이스홀더:
- `{ISSUE_KEY}`, `{BRANCH}` — 확정값
- `{FILE_CANDIDATES}` — Phase 1 영향 파일 후보 (상위 5개, 콤마 구분)
- `{PLAN_SUMMARY}` — `.work/{issue_key}.md` "## 플랜 > 구현 접근" 첫 3-5줄
- `{ELAPSED_HUMAN}` — Phase 0 의 `START_EPOCH` 를 인자로 `${CLAUDE_PLUGIN_ROOT}/scripts/session-metrics.sh ${START_EPOCH}` 호출 결과에서 `human=` 부분 추출 (예: `2m 14s`). 스크립트 실패 시 `—` 로 폴백 후 본 흐름 계속.
- `{COMMAND}` = `autopilot`, `{AGENT}` = 세션 모델명, `{PLUGIN_VERSION}` = plugin.json version, `{USER}` = `git config user.name`

스크립트 exit code 분기는 ship Phase 3.3 와 동일 (acli 미가용 → 코멘트 스킵 + `.work` 초안 유지, 본 흐름은 계속). **다중 모드 subagent 는 이 단계 스킵** (Phase M 참조).

`--stop-at pick` 시 여기서 종료.

## Phase B: 구현 (단계별 + 편차 감지)

1. `.work/{issue_key}.md` "## 플랜 > 구현 접근" 섹션을 단계로 파싱.
2. 각 단계 순차 실행:
   - Edit / Write 툴로 파일 수정
   - 단계 완료 시 1줄 진행 보고 ("[{n}/{N}] {단계명} 완료")
   - 진행 결과를 `.work/{issue_key}.md` "## 실행 로그" 에 누적 기록 (1줄/단계)
3. **편차/그레이존 — 보수적 자율 결정**: 아래 상황 발생 시 사용자에게 묻지 않고 `CONVENTIONS.md` / `CLAUDE.md` 기준으로 결정 + 근거를 `.work/{issue_key}.md` "## 결정 메모" 에 `{timestamp} — {상황} → {결정} (근거: ...)` 형식으로 기록 후 진행:
   - 플랜에 명시되지 않은 파일 수정 필요 → 영향 범위 자동 보강
   - 구현 중 새로운 트레이드오프 발견 → 컨벤션 기반 선택
   - 테스트 작성 필요 여부 판단 불가 → 컨벤션 기반 결정
4. **자율 결정 불가 시 종료**: 컨벤션·규약으로도 판단 불가능한 진정 모호 케이스는 결정 메모에 사유 기록 후 `failed` 로 즉시 종료. 부분 진행 상태는 그대로 둠 (사용자가 `.work` 노트 보고 재개 판단).
5. **에러 / 빌드 실패**: 한 단계에서 3회 이상 연속 실패 시 중단 + 결정 메모에 실패 로그 기록 + `failed` 종료.

### B-2. 페이즈 코멘트 (단일 모드만)

Phase B 완료 후 `${CLAUDE_PLUGIN_ROOT}/workflow/templates/jira-comment-implement.md` 로드 → 플레이스홀더 치환 → `.work/{issue_key}-implement-comment.md` 저장 → `jira-comment.sh` 호출.

플레이스홀더:
- `{ISSUE_KEY}`, `{BRANCH}` — 확정값
- `{FILE_COUNT}` — `git diff --stat HEAD` 의 변경 파일 수
- `{DIFF_STAT}` — `git diff --stat HEAD` 출력 (상위 10줄, 그 이상은 "... 외 N건" 으로 압축)
- `{STEP_LOG}` — `.work/{issue_key}.md` "## 실행 로그" 에서 단계 1줄씩 (최대 10줄)
- `{ELAPSED_HUMAN}` — Phase A-3 와 동일 절차 (`session-metrics.sh ${START_EPOCH}` → `human=` 추출). 누적값이므로 pick 코멘트보다 큰 값.
- footer 자동 필드는 Phase A-3 와 동일

acli 미가용·실패 시 본 흐름 계속. **다중 모드 subagent 는 스킵**.

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

**실패 시 중단** — 자동 재시도 금지. 결정 메모에 사유 기록 후 사용자에게 결과 보고.

검증 결과는 `.work/{issue_key}.md` "## 검증 결과" 에 기록되며, Phase D 의 ship 코멘트에서 한 줄 요약(`{VERIFY_SUMMARY}`)으로 흡수된다 (별도 페이즈 코멘트 없음).

`--stop-at ship-preflight` 시 여기서 종료 (커밋·푸시·MR 없음).

## Phase D: 출하 (커밋 + 푸시 + MR)

`/ship` 의 Phase 2-3 실행:

### D-1. 커밋 메시지 자동 확정

`/ship` Phase 2 의 commit-message.md 템플릿 치환 결과를 그대로 최종 메시지로 사용. 사용자 승인 루프 없음.

### D-2. 커밋 + 푸시 + MR 생성 + Jira ship 코멘트

`/ship` Phase 2-3 의 나머지를 그대로 실행. ship 코멘트는 `{VERIFY_SUMMARY}` 가 채워진 형태로 post 된다.

`--stop-at mr` 와 이 단계 완료는 동일 (기본 종료 지점).

## Phase E: Handoff

```
┌──────────────────────────────────────────────┐
│ 자율 순항 완료: {issue_key}                    │
│   MR: {url}                                    │
│   Jira: IN PROGRESS (머지 대기)                │
│                                               │
│ Jira 코멘트: pick / implement / ship 3건       │
│ 사람 개입: {n} 회 (안전장치 트리거 시만)        │
│                                               │
│ 다음: 머지 후 → /land {issue_key}            │
└──────────────────────────────────────────────┘
```

## Phase M: 다중 이슈 병렬 실행 (Phase 0 가 다중 모드 판정 시)

**전제**: Phase 0 가 N >= 2 로 판정 + 자유 프롬프트 미혼용.

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
  - 임무: "이 워크트리 안에서 `/sds-workflow:autopilot {issue_key} [--stop-at <phase>] --skip-phase-comments` 를 실행하고, 결과를 한 줄 표 형태(`{issue_key} | {결과} | {MR URL or 사유} | {워크트리 경로} | {브랜치명}`)로 반환하라."
  - **페이즈 코멘트 스킵**: 다중 모드 subagent 는 Phase A-3 / B-2 의 pick·implement 코멘트를 post 하지 않는다 (이슈 N개 × 코멘트 3개 = Jira watcher 메일 폭증 방지). ship 코멘트만 1회 post.
  - **그레이존 처리**: 부모와 자식 모두 동일 정책. `CONVENTIONS.md` / `CLAUDE.md` 기준 보수적 자율 결정 → 결정 근거를 `.work/{issue_key}.md` "## 결정 메모" 에 기록 → 진행. 진정으로 모호하면 `failed` 로 즉시 반환.
  - **환경 정체 fail-fast**: 어떤 외부 프로세스(lint·build·network) 든 진행 없이 90초 이상 대기하면 즉시 중단하고 `failed | <단계> stalled` 로 반환. 부모가 resume 할 수단 없음 (SendMessage 미배포 환경).
  - **lockfile 보호**: `pnpm-lock.yaml` / `package-lock.json` / `yarn.lock` 은 의존성을 명시적으로 추가/제거한 경우가 아니면 절대 commit 하지 말 것. 환경(패키지 매니저 버전) 차이로 인한 lockfile diff 는 `git checkout HEAD -- <lockfile>` 로 되돌릴 것.
  - 종료 조건: Phase D 완료 또는 `--stop-at` 지점 도달 또는 안전장치 트리거 시 즉시 보고

각 subagent 내부에서는 단일 모드 Phase A-E 가 실행된다 (페이즈 코멘트만 스킵).

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
│   페이즈 코멘트: 스킵 (ship 코멘트만 N건)         │
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
│  각 워크트리에서 머지 검토 → /land {key}         │
│  워크트리 정리: git worktree remove <path>       │
└─────────────────────────────────────────────────┘
```

---

## 사람 개입 지점 (안전장치 트리거 시만)

| # | 트리거 | 시점 | 단일 모드 | 다중 모드 (Phase M) |
|---|-------|------|---------|------------------|
| 1 | Deviation (플랜 밖 변경) | Phase C `/ship` Phase 0 | 자동 중단 → 사용자 결정 | 발생 subagent 만 `failed` 로 종료 |
| 2 | UI 검증 실패 | Phase C `/ship` Phase 1.5 | 자동 중단 → 사용자 결정 | 발생 subagent 만 `failed` 로 종료 |
| 3 | Goal-backward 의문 | Phase C `/ship` Phase 1.8 | 자동 중단 → 사용자 결정 | 발생 subagent 만 `failed` 로 종료 |
| 4 | 연속 실패 3회 | Phase B 어느 단계든 | 중단 → 결정 메모 기록 후 `failed` | 동일 |

**더 이상 사람 개입 게이트가 아닌 항목** (자율 진행):
- 플랜 승인 — `.work` 노트에 자동 기록
- 커밋 메시지 승인 — 템플릿 치환 결과 자동 사용
- 그레이존 답변 — 보수적 자율 결정 + `.work` 결정 메모 기록

## 사람 미개입 (자동 실행)

- 컨텍스트 수집·브랜치 생성·Jira 전이
- 플랜 초안·구현 단계 전환·커밋 메시지
- 정적 검증 실행 판단
- MR 본문 작성·Jira 코멘트 (pick / implement / ship 3건)
- 그레이존 보수적 자율 결정 + 결정 메모 기록

## 안전 장치

- **Deviation 자동 중단** — `/ship` Phase 0 편차 감지 시 자동 중단 + 사용자 결정 요청 (ship 책임)
- **`--stop-at <phase>`** — 의도적 중단 지점. 값: `pick` / `implement` / `ship-preflight` / `mr`
- **`--dry-run`** — 경로만 출력, 실제 실행 없음. Phase 별 예상 입출력 요약
- **연속 실패 차단** — 한 단계 3회 연속 실패 시 중단 + 결정 메모 기록 + `failed` 종료
- **다중 모드 working tree clean 강제** — Phase M-1 에서 `git status --porcelain` 비어있지 않으면 중단. 부모 세션의 미커밋 변경이 subagent 워크트리에 새어들어가는 것 방지.
- **다중 모드 워크트리 격리** — Phase M-2 의 `isolation: "worktree"` 가 각 subagent 에 임시 워크트리를 부여. 같은 파일을 여러 이슈가 동시에 건드려도 부모 working tree 와 분리됨. 다만 같은 원격 브랜치명 충돌은 `/pick` 의 brand 생성 단계에서 검출 → 해당 subagent 만 실패로 보고.
- **다중 모드 subagent self-contained 종료** — Phase M-2 spec 상 subagent 는 부모와 비동기. SendMessage resume 은 Claude Code 환경별로 미배포(2026-04 ceph-web-ui 검증). 환경 정체·중단 시 subagent 가 즉시 fail-fast 종료하도록 prompt 에 90초 stall 규칙 강제. 부모는 살아있는 agent 를 재개할 수단이 없으므로, 정체 = 손실로 간주.
- **다중 모드 lockfile 회귀 차단** — subagent 환경의 패키지 매니저 버전 차이가 `pnpm-lock.yaml` 등을 downgrade 시키는 사례 관측(2026-04 다중 모드 첫 실전). spawn prompt 에 lockfile 보호 규칙(의존성 명시 추가/제거가 아니면 commit 금지) 강제.
- **다중 모드 페이즈 코멘트 스킵** — subagent 는 ship 코멘트만 post. pick/implement 코멘트는 스킵하여 N개 이슈 × 3개 코멘트 = Jira watcher 메일 폭증 방지.

## 원칙

- 자율 실행이되 **머지는 여전히 사람**. `/autopilot` 은 MR 출하까지만.
- **승인 게이트는 폐기**: 플랜·커밋 메시지를 사람이 검토해야 한다면 `/pick` → 수동 구현 → `/ship` 분리 사용. autopilot 은 자율 흐름 전용.
- `--skip-ui-check` 는 autopilot 에서 비활성 — UI 검증 생략은 사람의 명시적 선택이어야 함.
- 복잡도가 높은 이슈 (여러 도메인 교차, 외부 API 계약 변경 등) 는 `/pick` 개별 호출 권장. autopilot 은 **Trivial ~ Medium** 복잡도에 최적.
- 자율 디폴트는 사람의 검토 없이 MR 까지 가므로 리뷰어 부담이 커진다. 반복 패턴·저위험 이슈에 한정 권장.
- **다중 모드는 의도된 batch 작업** — 비슷한 패턴의 trivial 이슈 여러 건을 한 번에 처리할 때만 사용. 도메인이 교차하거나 서로 의존하는 이슈는 단일 모드에서 순차 처리해야 충돌·재작업이 줄어든다.
- **다중 모드는 워크트리 정리 책임이 사용자에게 있음** — `/autopilot` 은 워크트리를 자동 삭제하지 않는다. 머지 후 `git worktree remove <path>` 수동 실행.
