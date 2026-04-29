# Changelog

이 플러그인의 contract 변경 이력. 외부 저장소가 플러그인을 업데이트할 때 참조한다.

포맷: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) 간소화 버전. Breaking change 는 `⚠️` 로 표시.

모든 `/sds-tune` 엔트리는 Unreleased 섹션에 요약 1줄로 반영한다.

---

## [0.3.0] — 2026-04-23

tune-seed-2026-04-23 일괄 반영 릴리즈. 초기 안전 항목(Week 1) 3건 applied + `--review` 사이클로 Week 2 모두 적용 완료. marketplace.json / plugin.json 0.3.0 정렬.

### Added
- `workflow/templates/jira-comment-ship.md` — /ship Phase 3-3 Jira 코멘트 본문 템플릿 (MR URL·브랜치→타겟·요약·UI_NOTE). tune #7a.
- `workflow/templates/commit-message.md` — /ship Phase 2 커밋 메시지 draft 템플릿 (`{TYPE}: {ISSUE_KEY} {KOREAN_SUBJECT}` + Jira URL). tune #7c.
- `commands/autopilot.md` §A-2a 컨텍스트 스코핑 규칙 — 이슈 경로 추출 우선·헤딩 인덱스 Read·경로 단서 없을 시 AskUserQuestion 1회 게이트. 입력 토큰 절감. tune #2.
- `commands/autopilot.md` §B-4 병렬 Edit 판정 규칙 — 독립 단계 토폴로지 정렬 + 단일 메시지 병렬 Edit + 판정 불가 시 순차 디폴트. tune #5.

### Changed
- ⚠️ `workflow/templates/plan-template.md` — "영향 범위", "테스트 전략" (신규 하위 "신규/재사용 테스트" 추가), 신규 "위험 / 그레이존" 3섹션 "— 필수" 마커 + "빈 섹션 금지, 없어도 '없음' 한 줄 명시". tune #1.
- `commands/pick.md` Phase 3-1 테이블 — "신규/재사용 테스트", "위험/그레이존" 행 + "필수 섹션 규칙" 블록. tune #1.
- `commands/pick.md` Phase 3-1 CONVENTIONS 체크 로직 — CLAUDE.md 헤딩명 앵커 + CONVENTIONS 고유 §A/§B/§C 기반으로 수정. tune #6.
- `commands/ship.md` Phase 3-3 exit 0 — Jira 코멘트 본문을 `.work/{issue_key}-ship-comment.md` 로 저장 후 `jira-comment.sh ... @파일` 경로 호출. tune #7a.
- `commands/ship.md` Phase 1 — 정적 검증 명령을 `VALIDATION_STATIC` 변수(workflow.yml override) 기준으로 일반화 + `vitest related --run` 주의사항 명시. tune #3.
- `commands/ship.md` Phase 2 — 커밋 메시지 draft 를 `commit-message.md` 템플릿 Read+치환 방식으로 전환. tune #7c.
- ⚠️ `workflow/templates/work-context.md` — 섹션 재편성 (메타·Jira·기능개요·영향파일·플랜(by/pick)·실행로그(by/autopilot)·결정메모·검증결과(by/ship)·머지(by/land)·회고(by/recap)). 각 커맨드는 자기 섹션만 채우도록 협업 규약 명시. tune #7b. **기존 `.work/*.md` 와 헤딩 불일치 — gitignore 라 팀 간 영향 없음**. 신규 생성분부터 적용.
- `commands/ship.md` Phase 1.8 / `commands/recap.md` Phase 1·2 — work-context 신규 헤딩명(`## 검증 결과 > ### Deviation / Goal-backward`, `## 머지 (by /land)`, `## 플랜 (by /pick)`) 참조로 동기화.
- ⚠️ `SPEC.md` 확정 사항 표 — `CONVENTIONS SSOT: CLAUDE.md` 신규 행 추가. CONVENTIONS.md 는 앵커 인덱스 + §A/§B/§C 고유 항목으로 축소. tune #6 (철학 게이트 통과).
- `references/artifact-types.md` `workflow.yml` 엔트리 — `validation.static` 배열 원소의 쉘 표현식 허용 규약 추가. tune #3.

### Repo-level (this pilot repo only)
- `CLAUDE.md` 상단 — "안정 앵커 정책" 주석 추가. 헤딩명이 CONVENTIONS 앵커 계약면임을 명시. tune #6.
- `.team-workflow/CONVENTIONS.md` — 62줄 → 앵커 인덱스 + 고유 §A/§B/§C 고유 항목으로 축소. 6개 중복 섹션(계층/책임/타입/Vue/i18n/Federation) 은 CLAUDE.md SSOT 링크로 대체. tune #6.
- `.team-workflow/workflow.yml` `validation.static` — test 명령을 `pnpm exec vitest related --run $(...)` 로 override. tune #3.

## Unreleased

<!-- 다음 버전에 들어갈 엔트리. 머지 시 해당 MR 에서 이 섹션을 `[X.Y.Z] — YYYY-MM-DD` 로 승격 + plugin.json / marketplace.json version bump. -->

### Fixed
- `commands/draft.md` Phase 5 — Jira description 등록 경로를 `--description-file <md>` → `--from-json <adf.json>` 으로 전환. Jira Cloud 의 description 필드는 ADF (Atlassian Document Format) JSON 만 렌더링하므로 마크다운/wiki markup 은 plain text 로 노출되어 헤더·리스트·굵게가 모두 사라지던 문제 수정. ADF 변환 매핑 표 (heading/paragraph/strong/code/orderedList/bulletList) 신설. tune 2026-04-28 (draft-adf-rendering).
- `commands/draft.md` Phase 5 — `type` 값은 프로젝트 허용 enum 의 원어 (예: `작업`) 사용 명시. acli `--from-json` 이 영문 type 미인식 시 한글 enum 으로 재시도하는 폴백 절차 추가.
- `commands/draft.md` Phase 5 — `assignee` 는 `@me` 가 프로젝트 권한에 따라 거절될 수 있어 이메일 폴백 절차 추가.
- `commands/draft.md` Phase 5 — 우선순위는 acli `--from-json` 스키마에 priority 필드 없음을 명시하고 생성 후 `acli jira workitem update --priority` 또는 UI 조정으로 분리 안내.
- `workflow/templates/draft-issue.md` — 헤더 주석에 "마크다운은 사용자 미리보기 + 논리적 구조 정의용, 실제 제출은 ADF 변환" 명시.

## [0.3.3] — 2026-04-24

SessionStart hook 인프라 전면 철회 릴리즈. 0.3.1~0.3.2 의 "자동 업데이트 알림" 시도 재검토 결과 Claude Code 설계와 맞지 않아 폐기. **순 user-facing 기능은 `/sds-workflow:update` 커맨드 하나로 단순화**.

### Removed
- `.claude/settings.json` SessionStart hook 엔트리 — 제거.
- `plugin/sds-workflow/scripts/check-plugin-version.sh` — 삭제.
- `plugin/sds-workflow/scripts/changelog-excerpt.py` — 삭제.

### Rationale
- Claude Code SessionStart hook 의 실제 동작: exit 0 시 stdout 만 Claude context 에 주입, stderr 는 사용자 터미널에 표시되지 **않음** (요약 "hook success: OK" 만 노출). 즉 "사용자 터미널 직접 알림" 경로가 설계상 존재하지 않음.
- 0.3.0 stderr-only → 0.3.1 stdout-only → 0.3.2 `tee /dev/stderr` 의 3연속 실패는 전제(`stderr = 사용자 터미널`) 자체가 틀렸다는 신호. 0.3.2 의 tee 접근도 같은 오인식 위에 있었음.
- 남은 경로는 "stdout → Claude context → Claude 가 사용자에게 전달" 간접 체인뿐. Claude 재량 의존이라 불안정하고, 버전 drift 감지 시마다 CHANGELOG 요약까지 수백~수천 토큰을 컨텍스트에 주입해 비용 대비 효익 낮음.
- 대체 수단: 팀 규약으로 "플러그인 변경 MR 머지 후 `git pull` + `/sds-workflow:update` 실행". 버전 bump 규약(0.3.1 신설) 과 짝을 이루어 자동 반영 보장.

### Kept
- `commands/update.md` (`/sds-workflow:update`) — 유일한 user-facing surface.
- 플러그인 버전 bump 규약 (SPEC.md 확정 사항).

### Changed
- `README.md` §"업데이트 (/git pull + /sds-workflow:update)" — hook 안내 문장 제거, 3줄 시퀀스 직접 안내.
- `commands/update.md` §참조 — SessionStart hook 항목 제거, 호출 계기를 "팀원 수동 실행" 으로 명시.

## [0.3.2] — 2026-04-24 (superseded by 0.3.3)

**⚠️ Superseded**: 이 릴리즈의 `tee /dev/stderr` 접근은 "SessionStart hook stderr = 사용자 터미널" 이라는 잘못된 전제에 기반했음. 실제로는 exit 0 시 stderr 가 무시됨. 0.3.3 에서 hook 인프라 전체 철회.

SessionStart hook 알림 dual-stream 전환 릴리즈 (철회됨). 0.3.0(stderr-only → Claude 미수신) · 0.3.1(stdout-only → 사용자 터미널 미표출) 의 one-sided 문제를 `tee /dev/stderr` 로 동시 해소하려 했으나 전제 오류.

### Fixed (철회됨)
- `scripts/check-plugin-version.sh` — 업데이트 안내 메시지를 `tee /dev/stderr` 로 stdout + stderr 동시 출력. Claude context 주입(stdout) 과 사용자 터미널 표출(stderr) 을 한 번에 커버 시도. heredoc 과 changelog 요약 printf 양쪽에 적용. tune 2026-04-24 (session-start-hook-dual-stream). **0.3.3 에서 스크립트 자체 삭제**.

## [0.3.1] — 2026-04-24

원격 결정성·보안 튜닝 세트 릴리즈. **plugin.json / marketplace.json 0.3.1 정렬 = version bump 규약의 첫 적용**.

### Added
- `.claude/settings.json` SessionStart hook + `plugin/sds-workflow/scripts/check-plugin-version.sh` + `plugin/sds-workflow/scripts/changelog-excerpt.py` — 세션 시작 시 plugin source version (`plugin.json`) vs 설치 version (`installed_plugins.json`) 비교. diff 감지 시 stderr 로 업데이트 안내 + CHANGELOG 해당 버전 섹션 요약 출력 (Claude 가 context 로 수신 → 사용자 알림). 완전 자동화는 Claude Code 공식 제약으로 불가 — detect + notify 까지가 최대치. tune 2026-04-24 (plugin-auto-update-hook).
- `commands/update.md` — `/sds-workflow:update` 커맨드 신설. 팀원에게 3줄 슬래시 커맨드 시퀀스 (`/plugin marketplace update` / `install` / `/reload-plugins`) 를 한 번에 출력. tune 2026-04-24 (plugin-auto-update-hook).
- ⚠️ **플러그인 버전 bump 규약** — dev 머지마다 patch version 1단계 bump 확정. `SPEC.md` 확정 사항에 신규 행 추가. Claude Code `/plugin install` 이 same-version 을 "already installed" 로 스킵해 팀원 업데이트 시 `uninstall` 수동 단계 필수화되던 UX 저하 해소. `plugin.json` + `.claude-plugin/marketplace.json` 동시 bump. tune 2026-04-24 (plugin-version-bump-convention).
- `references/artifact-types.md` — `scripts/*.sh` 엔트리 신설. 기존 `create-mr.sh`·`jira-comment.sh` + 신규 `ensure-remote-sds.sh` 를 공식 등록. 공통 exit code 계약 (0=성공, 10=폴백/경고, 20+=치명) 명문화. pre-existing 레지스트리 갭 보강. tune 2026-04-24 (remote-sds-doc-consistency).

### Fixed
- `scripts/ensure-remote-sds.sh` — 신규 remote 등록 직후 `git fetch remote-sds --quiet` 추가. 기존엔 `git remote add` 만 수행해 `remote-sds/<target>` 로컬 tracking ref 가 없었고, 이어지는 ship Phase 1 vitest diff base 또는 where Step 1 의 `git diff/log remote-sds/<target>...HEAD` 가 `unknown revision` 으로 실패할 수 있었음. **fresh 저장소 회귀 위험** 해소. 기존 등록된 경우 (`already-registered`) 는 fetch 생략해 사용자 fetch 타이밍 존중. tune 2026-04-24 (ensure-remote-sds-fetch-on-register).

### Changed
- ⚠️ `scripts/create-mr.sh` — MR 생성 경로를 **3-layer 폴백 체인** 으로 재설계. 1차 GitLab REST API (curl + PRIVATE-TOKEN, URL path 에 project_path 명시 박아 다중 remote 혼동 면역), 2차 `glab mr create` (REST 미가용 시 안전망), 3차 프리필 URL (둘 다 실패 시 브라우저 클릭). 토큰 탐색: `$GITLAB_TOKEN` env → `glab config get token --host` 순. 409 / "Another open MR" 응답 시 기존 IID 추출해 URL 조립 후 exit 0. Exit code 계약 (0/10/20) 불변 — 호출측 변경 불필요. **배경**: glab 이 다중 remote 환경에서 source project 를 잘못 자동감지 (e.g., `gitlab` remote=SDS305 vs `origin`/`remote-sds`=SDS306 혼재 시 알파벳 순 `gitlab` 을 source 로 선택 → "Source is not a fork of target" 422 에러). REST API 는 URL path 에 project_path 가 명시 박혀 있어 이 종류 오인식 불가능. tune 2026-04-24 (create-mr-rest-fallback).
- `workflow/preamble.md` / `workflow/config.defaults.yml` / `workflow/seeds/workflow.yml` / `commands/init.md` Phase 2 테이블 / `references/artifact-types.md` — `origin` 이 아닌 `remote-sds` 에서 파싱한다는 사실과 일관되도록 주석·예시 일괄 치환. 문서-동작 불일치로 인한 사용자 오해 방지. tune 2026-04-24 (remote-sds-doc-consistency).

### Added (기존 엔트리)
- ⚠️ `remote-sds` — 팀 공용 고정 git remote 이름 도입. `commands/ship.md` Phase 2 push, `commands/ship.md` Phase 1 / `commands/recap.md` Phase 3 / `commands/where.md` Step 1 diff base, `scripts/create-mr.sh` 폴백 URL 파싱의 `origin` 하드코딩을 일괄 `remote-sds` 로 치환. `scripts/ensure-remote-sds.sh` 신규 — 등록 보장 스크립트 (exit 0=OK, 10=URL 불일치, 20=치명). `commands/init.md` Phase 4.5 + `commands/ship.md` Phase 0-1 이 이 스크립트를 공통 호출해 **기존 저장소 사용자도 수동 명령 없이 자동 등록**. 배경: 사용자별 `origin` 이 서로 다른 프로젝트(SDS305/SDS306/fork 등)를 가리킬 때 엉뚱한 곳에 push 되는 리스크. `origin` 명명 강제 대신 별도 전용 remote 추가로 기존 설정 비침습. **needs-e2e** — push·MR 생성·log diff 세 지점 + auto-register 스크립트 동시 변경이라 실제 pick→ship→land 회차 필요. tune 2026-04-24 (remote-sds-fixed-name).
- 모든 출력물(MR body · Jira 코멘트 · Recap 코멘트 · Confluence 페이지)에 authorship footer 1줄 추가. 포맷: `Generated via /sds-workflow:{COMMAND} — agent {AGENT} · plugin sds-workflow v{PLUGIN_VERSION} · user {USER}`. tune 2026-04-23 (authorship-footer-in-outputs). `ship.md` 3-1·3-3, `recap.md` 2·3 에 placeholder 치환 지시 동기화.

## [0.2.0] — 2026-04-22

다중 모드 autopilot + 공통 설정 로드 + 결정성 보장 스크립트 묶음 릴리즈. marketplace.json 과 plugin.json 을 0.2.0 으로 정렬.

### Added
- `docs/onboarding.html` "권장 퍼미션" 슬라이드 + `README.md` "권장 퍼미션 사전 허용" 섹션 — acli/glab/git/pnpm 등 역추적 표 + `~/.claude/settings.json` vs 프로젝트 `.claude/settings.json` 예시. 야간·다중 모드 자율 운행 중 권한 프롬프트로 흐름이 끊기지 않도록 사전 허용 안내.
- `docs/onboarding.html` 시작하기 슬라이드 "4. 플러그인 reload" 단계 — `/plugin` 목록 새로고침 또는 Claude Code 재시작. 설치 직후 구버전 커맨드 인덱스 문제 예방.
- `docs/onboarding.html` 밤사이 비행 예시 — 다중 이슈 한 줄 호출(`/sds-workflow:autopilot CDS-2150 CDS-2151 CDS-2152`) 패턴 명시.
- `commands/autopilot.md` 다중 이슈 모드 — `/autopilot CDS-1 CDS-2 ...` 처럼 N≥2 이슈 키 전달 시 자동 다중 모드 분기. `--ralph` 자동 강제, 각 이슈마다 Task agent (`isolation: "worktree"`) spawn, 단일 메시지 병렬 실행. 신규 Phase 0 (모드 결정) + Phase M (병렬 실행). working tree clean 강제, 워크트리 자동 정리 안 함 (사용자 머지 책임).
- `workflow/preamble.md` — 커맨드 공통 설정 로드 절차 SSOT. 8개 커맨드에서 136줄 중복 제거.
- `references/artifact-types.md` — 모든 문서·설정·산출물의 레지스트리 (위치·owner·Lifecycle·Consumed by·Sync with).
- `references/conventions.md` — 카테고리·상태 enum, Handoff 포맷, acli fallback, 파일 구조 표준.
- `CHANGELOG.md` — 본 파일.
- `workflow/preamble.md` 추출 변수 3개 추가: `MR_TARGET_BRANCH`, `GITLAB_BASE_URL`, `GITLAB_PROJECT_PATH` (ship.md 의 target branch config 화 + glab 폴백 URL 생성에 사용).
- `workflow/config.defaults.yml` `gitlab:` 섹션 — 빈 값 기본, `git remote get-url origin` 파싱 폴백 규약 명시.
- `commands/ship.md#Phase 3-2` 프리필 URL 폴백 경로 — glab 실패·미설치 시 Python urllib.parse 로 GitLab MR create URL 생성 후 사용자에게 제시. MR 확정은 사용자 클릭에 위임.
- `scripts/create-mr.sh` — /ship Phase 3-2 MR 생성 스크립트 (glab 1차 → 프리필 URL 폴백). 결정성 보장 목적. Exit code 계약: 0=확정, 10=폴백, 20+=치명적 실패.
- `scripts/jira-comment.sh` — /ship Phase 3-3 acli 코멘트 wrapper. Exit code 계약: 0=성공, 10=acli 미가용, 20=호출 실패.

### Changed
- `docs/onboarding.html` + `README.md` — 커맨드 참조를 `/sds-workflow:<command>` 풀 네임으로 정규화 (플러그인 기본 호출 규약). 치트시트 표에 autopilot 다중 이슈 예시 · `--stop-at` · `--ralph` 반영 + `/init` 행 추가.
- `commands/autopilot.md` Phase M-2 prompt 골자 + 안전 장치 보강 (다중 모드 첫 실전에서 얻은 학습 #4·#5·#6 반영): 그레이존 자율 결정 + `.work/` 결정 메모 기록 / 환경 정체 90초 fail-fast / pnpm-lock.yaml 등 lockfile 보호 (의존성 명시 변경 없으면 commit 금지). 안전 장치 섹션에 "subagent self-contained 종료" + "lockfile 회귀 차단" 2건 추가. 동작 변경은 subagent prompt 강화 한정 — Phase A-E·M-1·M-3·M-4 동작 무변화.
- ⚠️ `commands/{pick,ship,land,recap,where,draft,autopilot,tune}.md` — Preamble 블록(17줄) 제거, `${CLAUDE_PLUGIN_ROOT}/workflow/preamble.md` Read 지시로 대체. 런타임 동작 동일하되 파일 구조 변경.
- `commands/tune.md` Phase 1~2 개정 — artifact-types 레지스트리 + conventions 필수 Read, 영향 범위 자동 확장 규칙 적용.
- `SPEC.md` — 파일 레이아웃에 `references/`, `CHANGELOG.md`, `workflow/preamble.md` 반영.
- `README.md` — 디렉토리 구조 업데이트.
- ⚠️ `commands/ship.md#Phase 3-2` — `glab mr create --target-branch main` 하드코딩 제거, `${MR_TARGET_BRANCH}` 변수 사용. 기존에 저장소별 target override 가 무시되던 버그 수정.
- `commands/ship.md#Phase 3-3 / Phase 4` — MR 확정(1차)·미확정(폴백) 2경로 분기. 폴백 시 `.work/{issue_key}.md` 상태 블록은 `MR-pending` 으로 기록.
- ⚠️ `commands/ship.md#Phase 3-2 / 3-3` — inline glab 명령·Python urlencode·remote 파싱·8KB 안전장치 로직을 `scripts/create-mr.sh` / `scripts/jira-comment.sh` 로 추출. 커맨드 본문은 exit code 분기만 기술. 결정성·테스트 용이성 향상 (GSD·spec-kit 선례 참조).
- ⚠️ `commands/land.md#Phase 2` — 로컬 git 정리 (`git checkout main && git pull`, `git branch -d`) 완전 제거. Jira RESOLVE 전환만 수행. **동기**: 머지된 로컬 브랜치를 자동 삭제하면 재참조·cherry-pick·히스토리 추적 여지가 사라짐. 작업 내역 보존 우선. 청소는 사용자가 수동으로.
- `commands/land.md` frontmatter description, 은유, 목적, Handoff, 실패 처리, 원칙 섹션 — 위 동작 변경 반영.

### Removed
- 커맨드 파일 8개의 Preamble 블록 중복 (~136줄 감축).

---

## 이전 이력 (sds-tune entries)

이전 변경은 `.team-workflow/tune-log.md` 의 튠 엔트리에 기록. 플러그인 승격 이후(`b-stage-plugin-promotion`) 주요 이벤트:

- `command-prefix-dedup` — 커맨드명 `sds-*` → `{name}` (플러그인 네임스페이스 prefix 중복 제거)
- `command-description-wording` — `/help` 노출 description 체언 종결 통일
- `intel-sunset` — `intel/*.md` 폐지, `/pick` Phase 0 런타임 추론 전환
- `design-to-spec-rename` — `.team-workflow/DESIGN.md` → `plugin/sds-workflow/SPEC.md`
