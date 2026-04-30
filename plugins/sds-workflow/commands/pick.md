---
description: Jira 이슈 가져오기 — 컨텍스트 수집 → 브랜치 생성 → Jira 전환 → 플랜 자동 초안 → 플랜 모드 진입
argument-hint: "CDS-XXXX"
entry-mode: interactive
required-permission: accept-edits
---


## Preamble

> 본문 실행 전 `${CLAUDE_PLUGIN_ROOT}/workflow/preamble.md` 를 Read 하여 공통 설정 로드 절차를 수행한다. 이 절차에서 추출한 `PROJECT_KEY`·`TRANSITIONS`·`PREFIX_MAP` 등 변수를 이하 Phase 에서 사용한다.

# /pick

**은유**: 백로그에서 티켓을 **집어든다**. 이륙 전 비행 계획서(플랜)를 체결한다.

**목적**: Jira 이슈 착수 시 필요한 세팅 원샷. 컨텍스트 수집 → 브랜치 생성 → Jira 전환 → 플랜 자동 초안 → 플랜 모드 진입.

인자 `$ARGUMENTS` 에서 이슈 키(`CDS-XXXX`)를 추출한다. 형식 불일치면 중단하고 사용자에게 정정 요청.

---

## Phase 0: 저장소 맥락 추론 + 규칙 로드

이 저장소의 기술 스택·구조를 **런타임 추론** 으로 파악한다. 사전 작성한 intel 문서 없이 아래 소스에서 직접 읽어 Phase 1 탐색의 기준선으로 삼는다.

아래를 병렬 Read / Glob:

1. `package.json` — 런타임·주요 의존성·스크립트
2. `tsconfig.json` (있으면) — 경로 alias·컴파일러 옵션
3. Vite/Webpack 설정 파일 — `vite.config.*`, `webpack.config.*` 등 (glob)
4. 루트 레벨 디렉터리 구조 (`ls src/` 로 계층 파악)
5. `CLAUDE.md` (프로젝트 루트) — 공식 개발 기준 문서
6. `.team-workflow/CONVENTIONS.md` — 비타협 규칙 (없으면 경고 후 계속)

(브랜치·커밋·MR 설정은 Preamble 에서 이미 merged config 로 로드 완료 — 재로드 불필요.)

- 추론으로 확정 불가한 항목(예: 금지된 레거시 패턴) 은 `CONVENTIONS.md` 에만 의존.
- 이 단계의 결과는 Phase 1 탐색 계획에 반영 — 이미 드러난 계층·패턴은 재탐색하지 않는다.

### acli 사전 점검 (Jira CLI)

Phase 1 의 Jira 조회는 `acli` (Atlassian CLI) 를 사용한다. Phase 1 진입 전에 한 번만 점검:

```bash
command -v acli
```

- 미설치 → 중단. 사용자에게 안내:
  - "acli 미설치. 설치 후 재시도 필요."
  - 설치: macOS `brew tap atlassian/homebrew-acli && brew install acli` / 공식 문서 https://developer.atlassian.com/cloud/acli/guides/install-macos/
  - 인증: `acli jira auth login --web` (OAuth) 또는 `acli jira auth login --site "<site>.atlassian.net" --email "<email>" --token` (API 토큰, 최초 1회)
- 설치됨 + 미인증 (`acli jira auth status` 실패) → 중단, `acli jira auth login` 안내.
- 통과 → Phase 1 진입.

## Phase 1: 병렬 컨텍스트 수집 (단일 메시지 병렬)

아래 항목을 **단일 메시지 내 병렬 툴 호출**로 실행:

- `acli jira workitem view {issue_key} --json` (Bash) — 이슈 본문, 타입, 우선순위, reporter, assignee
- `git status` (Bash)
- `git log --oneline -20` (Bash)
- `git log --grep "${PROJECT_KEY}-" --oneline -20` (Bash) — 유사 과거 이슈 참고 (예: `CDS-`)
- Grep/Glob — 이슈 제목 키워드로 영향 파일 후보 스캔

결과를 모두 받은 뒤 Phase 2 진입.

## Phase 2: 파생 (순차)

1. **이슈 타입 → 커밋 type 매핑** — Preamble 에서 로드한 `PREFIX_MAP` 사용.
   - Bug → fix / Task,Story → feat / Improvement → refactor / Documentation → docs
2. **slug 생성** — 이슈 제목에서 영문 kebab-case 3~5 단어. 한글/특수문자 제거.
3. **브랜치 생성** — `git checkout -b {type}/{issue_key}-{slug}`
   - 이미 존재하면 `git checkout {branch}` 로 스위치 후 알림.
4. **Jira 전환** — `acli jira workitem transition {issue_key} --status "IN PROGRESS"` (Bash). TO DO → IN PROGRESS.
   - 이미 IN PROGRESS 면 스킵 (view 결과의 status 필드로 판단).
   - 전이 플래그 이름은 acli 버전에 따라 `--status` / `--transition` 이 혼재할 수 있음. 실패 시 `acli jira workitem transition --help` 로 확인 후 재시도.
5. **`.work/{issue_key}.md` 생성** — `${CLAUDE_PLUGIN_ROOT}/workflow/templates/work-context.md` 구조로, 이슈 요약·파일 후보·상태 블록 자동 채움.

## Phase 2.5: 기능 개요 브리핑 (사용자에게 먼저 설명)

플랜 초안을 쓰기 전에 **이 이슈가 어떤 기능인지**를 사용자에게 먼저 브리핑한다. 이슈 담당자가 해당 기능·화면·코드 경로에 익숙하지 않을 수 있으므로, 플랜을 검증할 수 있는 최소한의 배경을 먼저 제공한다.

### 절차

1. **영향 파일 후보 중 핵심 1-2개 Read** — View/Composable/Modal 등 진입점 성격의 파일을 우선.
2. **브리핑 작성 (3-5문단)** — 아래 4요소를 포함.
   - 기능 이름 / 화면 경로 (예: 관리자 > 인증 사용자 > "불러오기" 모달)
   - 사용자 관점 동작 (무엇을 할 수 있는 기능인지)
   - 코드 관점 구조 (어느 파일에서 시작하여 어디로 흐르는지 — axios/query/composable 경계 포함)
   - 현재 관찰된 증상 또는 변경 요청 포인트 (이슈 description 과 코드의 교집합)
3. **사용자에게 출력** — 플랜 초안 작성 전, 이 브리핑을 사용자 메시지로 먼저 제시한다.
4. **`.work/{issue_key}.md` 에 "## 기능 개요" 섹션으로 기록** — 플랜 검증 시 참조 가능하도록.

### 원칙

- 추측은 "추정" 으로 명시한다 (BE 동작·외부 시스템 규칙 등 코드를 읽지 않은 부분).
- 사용자의 후속 질문(예: "왜 X라고 판단했는지") 에 답할 수 있도록 근거 파일 경로·라인을 함께 적는다.
- 브리핑 단계에서 사용자가 "이 이슈는 내가 맡을 일이 아님" 등을 판단할 수 있으면 Phase 3 진입 전 중단해도 된다.

## Phase 3: 플랜 자동 초안 + 플랜 모드 진입 (핵심 — 강제)

### 3-1. 플랜 초안 자동 작성

`${CLAUDE_PLUGIN_ROOT}/workflow/templates/plan-template.md` 의 모든 섹션을 에이전트가 직접 채운다. 사람은 fill-in 금지. 검증·수정만.

각 섹션 자동 소스:

| 섹션 | 소스 |
|------|------|
| 배경 | Jira description 3-5줄 요약 |
| 목표 | Jira acceptance criteria / description 내 목표 문장 |
| 범위 (포함/제외) | 제목 + 영향 파일 후보에서 파생 |
| 영향 범위 | Phase 1 Grep/Glob + `git log --grep` 결과 |
| 구현 접근 | 영향 파일을 Read 후 단계별 제안 |
| CONVENTIONS 체크 | CONVENTIONS.md 앵커 목록(CLAUDE.md §아키텍처와-계층 / §Query-Data-Store / §타입 / §Vue-TS-lint / §i18n / §Module-Federation) + 고유 항목(§A 커밋/브랜치, §B 응답 말투, §C 검증 경계) 에 대해 자가 점검. 원문 SSOT 는 CLAUDE.md (tune 2026-04-23 #6) |
| 테스트 전략 > 정적 | 항상 `pnpm run lint / type-check / test` |
| 테스트 전략 > 신규/재사용 | 추가할 테스트 파일·재사용 스펙. 없으면 "없음 + 사유" 1줄 |
| 테스트 전략 > 브라우저 | 변경 예상 view/route 감지 → 체크리스트 자동 생성. UI 변경 없으면 "해당 없음" |
| 검증 방법 | 테스트 전략에서 파생 |
| 위험 / 그레이존 | 회귀 가능성 있는 지점. 그레이존 기본 방침: CONVENTIONS 보수 선택. 없으면 "없음" 1줄 |
| 보류 / 가정 | 읽지 못한 외부 API·서버 제약 등 불확실 지점 |

**필수 섹션 규칙**: 영향 범위 / 테스트 전략 / 위험 / 그레이존 세 섹션은 빈 채로 남기지 않는다. 후보가 없어도 "없음" 한 줄로 명시한다 (빈 섹션 = 플랜 미완).

### 3-2. 그레이존 질문 수면화

초안 작성 중 에이전트가 판단 불가한 지점은 **플랜에 박지 않고** `AskUserQuestion` 으로 수면화.

질문 대상:
- 동일 기능 구현 경로가 2개 이상이고 각기 트레이드오프가 있는 경우 (예: 신규 컴포저블 분리 vs 기존 통합)
- 서버/외부 시스템 제약이 불명확한 경우
- 성능/UX 트레이드오프 (즉시 리페치 vs 캐시 유지 등)
- 이슈 설명이 모호해서 "의도된 동작"이 복수 해석되는 경우

사람의 답변을 해당 섹션(주로 구현 접근 / 범위 / 보류·가정)에 반영하고, 플랜의 "그레이존 답변 로그" 에 `Q: ... → A: ...` 형식으로 기록.

질문이 없으면 이 스텝 스킵.

### 3-3. 플랜 반영

`.work/{issue_key}.md` 의 "## 플랜" 섹션에 최종 초안을 기록한다.

### 3-4. 플랜 모드 진입

내장 `EnterPlanMode` 툴 호출. 이후 흐름:

1. 사용자가 플랜 초안 검토
2. 수정 요청 루프 ("{섹션}을 {이유}로 다시")
3. 승인 시 사용자가 `ExitPlanMode`
4. 구현 단계 진입 (Edit/Write 해금)

이 Phase 종료 전까지 **코드 수정 금지**. `EnterPlanMode` 가 비-readonly 툴을 구조적으로 차단.

## Handoff 노출 (이 커맨드는 ① 까지만 책임)

### ① `EnterPlanMode` 직후 (플랜 초안 옆)

```
플랜 초안이다. 검토/수정 후 승인해줘.
- 브랜치: {type}/{issue_key}-{slug}
- Jira: IN PROGRESS
- 작업 노트: .work/{issue_key}.md
```

### ② `ExitPlanMode` 직후 (구현 모드 전환 시점 — 에이전트가 첫 구현 단계 전 1회 출력)

```
┌─────────────────────────────────────────┐
│ 플랜 승인 완료                            │
│ 브랜치: {type}/{issue_key}-{slug}         │
│ Jira: IN PROGRESS                       │
│ 다음: 구현 진행 후 → /ship            │
└─────────────────────────────────────────┘
```

---

## 실패/예외 처리

- 이슈 키 형식 불일치 → 중단, 사용자에게 정정 요청
- acli 미설치/미인증 → Phase 0 에서 중단 + 설치·인증 안내
- Jira 조회 실패 (acli exit ≠ 0) → 사용자에게 stderr 표시 후 중단 (브랜치 생성 전에 판단)
- 브랜치 이미 있음 → 스위치 + 안내 (덮어쓰기 금지)
- Jira 전환 실패 → 브랜치는 유지, 수동 전환 안내 (`acli jira workitem transition --help` 로 플래그 확인)

## 원칙 (재확인)

- 사람은 플랜을 **쓰지 않는다**. 사람의 역할은 세 가지:
  1. 에이전트가 쓴 초안 **검증**
  2. 필요 시 **수정 지시** ("{섹션}을 {이유}로 다시")
  3. 에이전트가 올린 **그레이존 질문에 답변**
- 플랜 승인 전 코드 수정 금지 (EnterPlanMode 구조적 차단 + 프롬프트 규약)
