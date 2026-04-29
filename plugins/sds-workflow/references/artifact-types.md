# Artifact Type Registry

이 플러그인이 다루는 모든 문서·설정·산출물의 **SSOT**. 타입별로 위치·구조·lifecycle·소유자·소비처·동기화 대상을 정의한다.

`/sds-tune` 은 수정 대상 분류 시 이 레지스트리를 **반드시** Read 해 영향 범위를 자동 확장한다. 새 artifact 타입을 도입하거나 기존 타입의 구조를 바꾸면 이 파일을 먼저 갱신한다.

## 용어

- **Owner (플러그인 / 저장소)**: 수정 권한 소재. "플러그인 owned" 는 sds-workflow 플러그인 repo 에서만 수정, "저장소 owned" 는 플러그인을 설치한 각 저장소에서 자율 수정.
- **Consumed by**: 이 artifact 를 Read 또는 Write 하는 커맨드.
- **Sync with**: 이 artifact 변경 시 **반드시** 함께 갱신해야 하는 다른 artifact. 튠 스킬이 이 목록을 보고 수정 후보를 자동 확장.

---

## 플러그인 소유 artifacts

### `SPEC.md`

- **위치**: `plugin/sds-workflow/SPEC.md`
- **소유자**: 플러그인
- **목적**: 설계·철학·확정 사항. 은유 테이블·파일 레이아웃·커맨드 Phase 개괄.
- **Lifecycle**: 철학 변경 시 수정. `/sds-tune design-principle` 카테고리.
- **Consumed by**: 모든 `sds-*` 커맨드 (참조용), `/sds-tune` Phase 2 (영향 판정)
- **Sync with**:
  - `README.md` — 커맨드 표·디렉토리 구조 동기화
  - `commands/*.md` line 27 (은유 문구) — SPEC §파일럿 은유 변경 시
  - `CHANGELOG.md` — breaking change 기록

### `README.md`

- **위치**: `plugin/sds-workflow/README.md`
- **소유자**: 플러그인
- **목적**: 설치·사용법·커맨드 표.
- **Consumed by**: 사용자 (수동), 플러그인 marketplace
- **Sync with**: `SPEC.md` (커맨드 표·은유)

### `CHANGELOG.md`

- **위치**: `plugin/sds-workflow/CHANGELOG.md`
- **소유자**: 플러그인
- **목적**: Contract 변경 이력. 외부 저장소가 플러그인 업데이트 시 참조.
- **Lifecycle**: 매 `/sds-tune` 적용 시 해당 엔트리를 CHANGELOG 의 "Unreleased" 섹션에 요약.
- **Consumed by**: 사용자 (업데이트 판정)

### `commands/*.md`

- **위치**: `plugin/sds-workflow/commands/{pick,ship,land,recap,where,draft,autopilot,tune,init}.md`
- **소유자**: 플러그인
- **구조**:
  - frontmatter: `description`, `argument-hint`
  - Preamble 참조 (init 제외)
  - 은유 블록 (line 27 근처)
  - Phase 0 ~ Phase N 본문
  - Handoff 블록 (box format)
- **Consumed by**: Claude Code 런타임 (`/sds-workflow:{name}` 호출 시)
- **Sync with**:
  - `SPEC.md` — 커맨드 표 `description` 요약, Phase 개괄
  - `README.md` — 커맨드 표 "역할" 열
  - `autopilot.md` — 하위 커맨드 호출 시 해당 참조
  - `where.md` — 라우팅 테이블이 해당 커맨드로 분기할 때

### `workflow/preamble.md`

- **위치**: `plugin/sds-workflow/workflow/preamble.md`
- **소유자**: 플러그인
- **목적**: 모든 커맨드(init 제외)가 본문 Phase 전에 수행하는 config 로드 절차. **SSOT**.
- **Consumed by**: `pick`, `ship`, `land`, `recap`, `where`, `draft`, `autopilot`, `tune` (총 8개)
- **Sync with**:
  - `workflow/config.defaults.yml` — 추출 변수 키 변경 시
  - `CHANGELOG.md` — 변경 전파 영향이 커 기록 필수

### `workflow/config.defaults.yml`

- **위치**: `plugin/sds-workflow/workflow/config.defaults.yml`
- **소유자**: 플러그인
- **목적**: 저장소 비의존 공통 기본값 (jira transitions, branch prefix_map, validation commands 등).
- **Consumed by**: Preamble (모든 커맨드)
- **Sync with**:
  - `workflow/preamble.md` — 변수 추출 규칙
  - `workflow/seeds/workflow.yml` — seed 가 override 예시 제공

### `workflow/templates/*.md`

- **위치**: `plugin/sds-workflow/workflow/templates/{plan,mr,work-context,recap-comment,recap-page,draft-issue}.md`
- **소유자**: 플러그인
- **Consumed by**:
  - `plan-template.md` → `/sds-workflow:pick` (Phase 3 플랜 초안)
  - `mr-template.md` → `/sds-workflow:ship` (MR 본문)
  - `work-context.md` → `/sds-workflow:pick` (.work/{issue_key}.md 생성)
  - `recap-comment.md` / `recap-page.md` → `/sds-workflow:recap`
  - `draft-issue.md` → `/sds-workflow:draft`
- **Sync with**: 해당 소비 커맨드의 Phase 단계 — 템플릿 섹션 추가/변경 시 커맨드가 섹션을 채우는 로직도 수정

### `workflow/seeds/*`

- **위치**: `plugin/sds-workflow/workflow/seeds/{workflow.yml,CONVENTIONS.md,tune-log.md}`
- **소유자**: 플러그인 (배포만), 사용 시 저장소로 복사
- **목적**: `/sds-workflow:init` 이 신규 저장소에 스캐폴드로 복사하는 원본.
- **Consumed by**: `/sds-workflow:init` (Phase 3 seed copy)
- **Sync with**:
  - `seeds/workflow.yml` ↔ `config.defaults.yml` 스키마
  - `seeds/tune-log.md` 포맷 줄 ↔ `references/conventions.md` 카테고리 enum

### `scripts/*.sh`

- **위치**: `plugin/sds-workflow/scripts/{create-mr,jira-comment,ensure-remote-sds}.sh`
- **소유자**: 플러그인
- **목적**: 결정성 보장용 외부화 로직. 에이전트가 복잡 분기·URL 인코딩·remote 파싱을 직접 다루지 않고 스크립트 exit code 계약만 처리 (GSD·spec-kit 선례).
- **Consumed by**:
  - `create-mr.sh` → `/sds-workflow:ship` Phase 3-2 (glab 1차 → 프리필 URL 폴백)
  - `jira-comment.sh` → `/sds-workflow:ship` Phase 3-3 (acli 코멘트 wrapper)
  - `ensure-remote-sds.sh` → `/sds-workflow:init` Phase 4.5 + `/sds-workflow:ship` Phase 0-1 (`remote-sds` 등록 보장)
- **Exit code 계약 (공통)**: `0` = 성공, `10` = 폴백/경고 (호출측이 AskUserQuestion 으로 사용자 개입 요청), `20+` = 치명적 실패. 자세한 의미는 각 스크립트 상단 주석 참조.
- **Sync with**: 해당 소비 커맨드의 Phase 단계 — 스크립트 계약 변경 시 커맨드의 exit code 분기 처리도 수정.

### `references/artifact-types.md` (이 파일)

- **위치**: `plugin/sds-workflow/references/artifact-types.md`
- **소유자**: 플러그인
- **목적**: 본 레지스트리. 새 artifact 추가/기존 수정 시 최우선 갱신.
- **Consumed by**: `/sds-tune` Phase 2 (영향 범위 자동 확장)
- **Sync with**: `references/conventions.md` (포맷·enum 공유)

### `references/conventions.md`

- **위치**: `plugin/sds-workflow/references/conventions.md`
- **소유자**: 플러그인
- **목적**: 카테고리 enum, 상태 enum, Handoff 포맷, acli fallback 표준 등 공통 계약.
- **Consumed by**: 모든 커맨드 (간접), `/sds-tune` Phase 1~4 (분류·검증)
- **Sync with**:
  - `commands/tune.md` Phase 1 카테고리 리스트
  - `seeds/tune-log.md` format 줄
  - `.team-workflow/tune-log.md` format 줄 (저장소별)

---

## 저장소 소유 artifacts

### `.team-workflow/workflow.yml`

- **위치**: 저장소 루트 `.team-workflow/workflow.yml`
- **소유자**: 저장소
- **목적**: 플러그인 기본값을 저장소 값으로 override.
- **Lifecycle**: `/sds-workflow:init` Phase 4 에서 치환 생성. 이후 팀이 필요 시 수기 수정.
- **Consumed by**: Preamble (모든 커맨드)
- **Sync with**: `config.defaults.yml` 스키마 변경 시 override 도 검토
- **규약 (tune 2026-04-23 #3)**: `validation.static` 배열 원소는 순수 명령 외에 **쉘 표현식** (backtick·`$(...)`·pipe) 허용. 예: `pnpm exec vitest related --run $(git diff --name-only "remote-sds/${MR_TARGET_BRANCH}...HEAD")`. 주석을 파일 상단에 달아 의도를 남기고, 관련 감지 누락 사례 수집 후 롤백 가능하도록 유지.

### `.team-workflow/CONVENTIONS.md`

- **위치**: 저장소 루트 `.team-workflow/CONVENTIONS.md`
- **소유자**: 저장소
- **목적**: 이 저장소의 비타협 규칙 (코딩·리뷰·배포 등).
- **Consumed by**: `/sds-workflow:pick` Phase 0
- **Sync with**: 저장소 정책 문서 (각 저장소 자율)

### `.team-workflow/tune-log.md`

- **위치**: 저장소 루트 `.team-workflow/tune-log.md`
- **소유자**: 저장소
- **목적**: 해당 저장소에서 제출된 `/sds-tune` 엔트리 이력.
- **Lifecycle**: `/sds-tune` 매 실행 시 상단에 엔트리 append.
- **Consumed by**: `/sds-tune --review`
- **Sync with**:
  - format 줄은 플러그인 `references/conventions.md` 의 카테고리 enum 을 따름
  - 엔트리 내 `카테고리` 필드는 conventions 의 enum 에 존재해야 함

### `.work/{issue_key}.md`

- **위치**: 저장소 루트 `.work/{issue_key}.md` (gitignore)
- **소유자**: 저장소 (ephemeral)
- **목적**: 이슈별 작업 컨텍스트 (상태 블록·플랜·MR URL·기능 개요).
- **Lifecycle**: `/sds-workflow:pick` 생성, `ship`/`land`/`recap` 에서 상태 블록 갱신. 머지 완료 후 archival 은 저장소 자율.
- **Consumed by**: `pick` (create/update), `ship` (update), `land` (update), `recap` (read), `where` (read)
- **템플릿**: `workflow/templates/work-context.md`
- **Sync with**: `work-context.md` 템플릿 변경 시 이 파일을 갱신하는 커맨드들의 Phase 로직도 검토

---

## 영향 범위 자동 확장 규칙 (튠 스킬용)

`/sds-tune` Phase 2 는 사용자 피드백에서 **1차 타겟 파일**을 식별한 뒤, 아래 규칙에 따라 **2차 영향 파일**을 후보에 자동 포함한다:

1. **커맨드 description 변경** → `README.md` 커맨드 표, `SPEC.md` 커맨드 표 자동 포함
2. **카테고리 enum 변경** → `commands/tune.md`, `seeds/tune-log.md`, `.team-workflow/tune-log.md` format 줄, `references/conventions.md` 자동 포함
3. **은유 문구 변경** → `SPEC.md §파일럿 은유`, 해당 `commands/*.md` line 27, `README.md` 커맨드 표 자동 포함
4. **Preamble 절차 변경** → `workflow/preamble.md` 1곳만 수정 (파생 동기화 불필요, 단 CHANGELOG 기록)
5. **커맨드명 변경** → 파일명 + `SPEC.md` + `README.md` + `autopilot.md` 하위 호출 + `where.md` 라우팅 테이블 자동 포함
6. **config.defaults.yml 스키마 변경** → `preamble.md` 변수 추출, `seeds/workflow.yml` 예시 자동 포함
7. **새 템플릿 추가** → 해당 소비 커맨드의 Phase 로직, `config.defaults.yml` `*_template_path` 추가, 이 레지스트리의 templates 엔트리 자동 포함

---

## 엔트리 추가 절차

새 artifact 타입을 도입할 때:

1. 이 파일에 위 포맷으로 엔트리 추가 (위치·소유자·목적·Lifecycle·Consumed by·Sync with)
2. "영향 범위 자동 확장 규칙" 에 해당되는 규칙이 있으면 추가
3. `CHANGELOG.md` 에 기록
4. `/sds-tune` 실행 시 Phase 2 가 새 규칙을 로드하도록 다음 튠부터 반영
