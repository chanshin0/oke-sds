---
description: 검증(테스트) → 커밋 → 푸시 → MR 등록 → Jira 코멘트 원샷
argument-hint: "[--skip-ui-check <사유>]"
---


## Preamble

> 본문 실행 전 `${CLAUDE_PLUGIN_ROOT}/workflow/preamble.md` 를 Read 하여 공통 설정 로드 절차를 수행한다. 이 절차에서 추출한 `PROJECT_KEY`·`VALIDATION_STATIC`·`UI_CHANGE_GLOBS`·`TEMPLATE_ROOT`·`MR_TARGET_BRANCH`·`GITLAB_BASE_URL`·`GITLAB_PROJECT_PATH` 등 변수를 이하 Phase 에서 사용한다.

# /ship

**은유**: 조립(구현)이 끝난 변경을 **품질 검사(lint·type·test·UI)** 통과 후 컨테이너(MR)에 **출하**한다.

**목적**: 구현 완료 후 정적·브라우저 검증 → 커밋 → 푸시 → GitLab MR 생성 → Jira 코멘트 원샷.

Jira 상태는 **IN PROGRESS 유지** (의도됨 — 머지 후 `/land` 에서만 RESOLVE).

인자 `$ARGUMENTS` 파싱:
- `--skip-ui-check <사유>` — Phase 1.5 브라우저 검증 스킵 (사유 필수)

---

## Phase 0: 전제 + Deviation 감지 (순차)

0. **acli 사전 점검** — `command -v acli` 로 설치 확인. Phase 3.3 Jira 코멘트에 사용.
   - 미설치 → 경고만 (커밋·MR 은 계속 진행). Phase 3.3 에서 코멘트를 건너뛰고 수동 안내.
   - 설치됨 + 미인증 (`acli jira auth status` 실패) → 동일하게 경고 후 진행.
0-1. **`remote-sds` remote 자동 등록 (스크립트 위임)** — `ensure-remote-sds.sh` 호출로 미등록 시 자동 등록. 사용자 수동 명령 불필요.
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/ensure-remote-sds.sh" \
     "${GITLAB_BASE_URL}" "${GITLAB_PROJECT_PATH}"
   ```
   - **exit 0** → 통과 (신규 등록 또는 기존 URL 일치).
   - **exit 10** → URL 불일치. `AskUserQuestion`: "`remote-sds` 가 다른 URL 을 가리킵니다 (stderr 참조). (a) 교체 / (b) 기존 유지하고 ship 진행 (리스크 사용자 책임) / (c) 중단".
   - **exit 20** → 치명적 실패 (`GITLAB_BASE_URL`/`GITLAB_PROJECT_PATH` 미설정 등). 중단하고 `/sds-workflow:init --force` 재실행 안내.

   이 remote 는 팀 공용 고정 이름이며 Phase 2 push · Phase 1 diff base 가 의존한다.
1. **브랜치명에서 이슈 키 추출** — `git branch --show-current` → `{type}/CDS-XXXX-{slug}` 패턴에서 `CDS-XXXX` 추출.
   - 형식 불일치 → 중단.
2. **플랜 존재 확인** — `.work/{issue_key}.md` 의 "## 플랜" 섹션이 비어있지 않은지.
   - 비어있음 → 중단. "`/pick {issue_key}` 재실행 또는 플랜 수기 기입 후 재시도" 안내.
   - `Trivial fix — no plan needed` 한 줄만 있어도 통과 (escape hatch).
3. **Deviation 체크** — 플랜의 "영향 범위" 섹션과 `git diff --stat` 비교.
   - 플랜 밖 파일 변경 감지 시 `AskUserQuestion`:
     > "플랜 범위를 벗어난 변경 감지: {files}. (a) 스코프 추가로 플랜 갱신 / (b) 실수 — 해당 변경 되돌리기 / (c) 무시하고 진행"
   - (a) 선택 시 플랜의 "영향 범위" 섹션 자동 보강 + "Deviation 기록" 에 로그.

## Phase 1: 정적 검증 (단일 메시지 병렬 호출)

**반드시 단일 메시지 내 Bash 툴 병렬 실행** — 명령 목록은 Preamble `VALIDATION_STATIC` (저장소별 override, deep-merge 결과) 에서 가져옴. `.team-workflow/workflow.yml` 의 `validation.static` 배열을 그대로 사용.

기본 예시 (저장소 override 기준):

- `pnpm run lint:changed`
- `pnpm run type-check`
- `pnpm exec vitest related --run $(git diff --name-only "remote-sds/${MR_TARGET_BRANCH}...HEAD")`

**주의 (tune 2026-04-23 #3 적용)**: test 는 변경 파일 의존 스펙만 실행 (`vitest related`). 글로벌 회귀는 CI 전체 스위트가 커버한다는 가정. related 감지 누락 사례가 관측되면 `workflow.yml` 에서 `pnpm run test` 로 롤백.

결과 모두 수집 후:
- 하나라도 FAIL → 중단하고 원인 보고. `.work/{issue_key}.md` 검증 결과 섹션 갱신.
- 모두 PASS → Phase 1.5 진행.

## Phase 1.5: 브라우저 검증 (UI 변경 시 자동)

### UI 변경 감지

`git diff --stat` 출력에서 아래 경로가 포함되면 UI 변경:
- `src/views/**`
- `src/components/**`
- `src/assets/**`
- `src/locales/**`

변경 없음 → Phase 1.5 스킵.

### 변경 있음 + `--skip-ui-check` 아님

1. **dev server 상태 확인** — `http://localhost:*` 응답 (일반 포트 5173/5174/8080 등).
   - 미기동 → 중단. "`pnpm run serve` 또는 `pnpm run mockup` 실행 후 재시도" 안내.
   - **자동 기동 금지**: 모드(local/localbe/mockup) 결정이 비결정적.
2. **체크리스트 로드** — `.work/{issue_key}.md` 의 "브라우저 체크리스트" 섹션.
   - 비어있음 → 경고. `--skip-ui-check <사유>` 로만 계속 가능.
3. **Claude in Chrome 단일 세션 실행** (MCP 툴은 `ToolSearch` 로 사전 로드):
   - `mcp__claude-in-chrome__tabs_context_mcp` — 기존 탭 확인
   - `mcp__claude-in-chrome__tabs_create_mcp` — 대상 페이지 네비게이트
   - `mcp__claude-in-chrome__gif_creator` 시작 (파일명: `{issue_key}-verify-ui.gif`)
   - 체크리스트 단계별 `form_input` / `computer` / `find` 실행
   - `read_console_messages` (패턴 `/Error|Warning|Failed/`) 로 콘솔 확인
   - `gif_creator` 종료 → `.work/{issue_key}-verify-ui.gif` 저장
4. **결과 기록** — `.work/{issue_key}.md` "## 검증 결과 > 브라우저":
   - 체크리스트별 PASS/FAIL
   - 콘솔 에러 요약
   - GIF 경로
5. **실패 시 중단** (자동 커밋 금지).

### `--skip-ui-check <사유>` 사용 시

- Phase 1.5 전체 스킵.
- `.work/{issue_key}.md` 에 `UI 검증 스킵: {사유}` 기록.
- MR 본문에도 자동 주입.

## Phase 1.8: Goal-backward 검증 (순차, 짧음)

1. `.work/{issue_key}.md` 에서 "목표" + "구현 접근" 섹션 재로드.
2. 현재 `git diff` 가 그 목표를 실제로 달성했는지 에이전트가 자문.
3. 미달성/의문 지점이 있으면 `AskUserQuestion`:
   > "목표 '{X}' 가 diff 에서 {이유} 로 달성 미확인. (a) 보강 구현 / (b) 플랜 목표 재정의 / (c) 달성했다고 판단 — 진행"
4. 단순 수정은 "달성 판단 근거 1줄"만 기록하고 자동 통과.
5. 결과를 `.work/{issue_key}.md` "## 검증 결과 > ### Deviation / Goal-backward" 에 추가.

## Phase 2: 커밋 + 푸시 (순차)

1. `git status`, `git diff --stat` 출력 확인.
2. **커밋 메시지 draft** — `${CLAUDE_PLUGIN_ROOT}/workflow/templates/commit-message.md` 로드 후 플레이스홀더 치환.
   - `{TYPE}` — 브랜치 prefix (`PREFIX_MAP` 파생)
   - `{ISSUE_KEY}` — Phase 0 에서 추출
   - `{KOREAN_SUBJECT}` — 플랜 "목표" 에서 1줄 파생
   - `{OPTIONAL_BODY}` — 추가 설명 없으면 줄 자체 제거
   - `{JIRA_BASE_URL}` — Preamble 변수
3. **사용자 승인** — draft 를 보여주고 확인 요청. 수정 요청 시 반영 루프.
4. `git add -A` (주의: 플랜 범위 내 파일만 — Phase 0 Deviation 체크 통과 상태여야 함).
5. `git commit -m "..."`.
   - `husky` `commit-msg` 훅 통과 확인.
6. `git push -u remote-sds HEAD`.

## Phase 3: MR 생성 + 병렬 후처리

### 3-1. MR 템플릿 채움 (순차)

`${CLAUDE_PLUGIN_ROOT}/workflow/templates/mr-template.md` 의 자동 필드 주입:
- `{issue_key}`, `{issue_title}` — Jira 에서
- 📝 변경 요약 — 플랜 "목표" + diff 요약
- 📂 변경 파일 — `git diff --stat`
- ✅ 자동 검증 — Phase 1 결과
- 🧪 테스트 방법 — 플랜 "검증 방법" 참조
- 📸 스크린샷:
  - `.work/{issue_key}-verify-ui.gif` 존재 시 첨부 링크 자동 삽입
  - 없고 UI 변경 X → 섹션 자체 제거
  - 없고 `--skip-ui-check` → "UI 검증 스킵: {사유}" 표기
- **Authorship footer** (마지막 1줄):
  - `{COMMAND}` → `ship` (autopilot 이 호출한 경우 `autopilot`)
  - `{AGENT}` → 현재 세션의 Claude 모델명 (예: `Claude Opus 4.7`, `Claude Sonnet 4.6`). 런타임에 에이전트가 자기 모델명을 그대로 삽입. 알 수 없으면 `Claude`.
  - `{PLUGIN_VERSION}` → `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` 의 `version` 필드
  - `{USER}` → `git config user.name`

### 3-2. MR 생성 (스크립트 위임)

`${CLAUDE_PLUGIN_ROOT}/scripts/create-mr.sh` 호출 — glab 1차·프리필 URL 폴백 로직이 스크립트 내부에 캡슐화됨 (에이전트가 glab 명령·URL 인코딩·remote 파싱·8KB 안전장치를 직접 다루지 않는다 — 결정성 보장):

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/create-mr.sh \
  "$(git branch --show-current)" \
  "${MR_TARGET_BRANCH}" \
  "{type}: {issue_key} {subject}" \
  ".work/{issue_key}-mr-body.md" \
  "${GITLAB_BASE_URL}" \
  "${GITLAB_PROJECT_PATH}"
```

**호출 전 준비**: 3-1 에서 채운 MR 템플릿을 `.work/{issue_key}-mr-body.md` 로 저장 (스크립트 4번째 인자 = body 파일 경로).

**Exit code 분기**:
- **0** — stdout 은 확정된 MR URL. 3-3 의 "MR 확정" 경로.
- **10** — stdout 은 브라우저 프리필 URL (MR 미확정). 3-3 의 "MR 미확정" 경로. 사용자에게 "링크 클릭 → Create 눌러 확정" 안내.
- **20+** — 치명적 실패 (remote 파싱 불가 등). 사용자 개입 요청, 3-3 스킵.

**스크립트 계약**: `plugin/sds-workflow/scripts/create-mr.sh` 상단 주석 참조.

### 3-3. 병렬 후처리 (단일 메시지 병렬)

3-2 exit code 에 따라 분기.

**exit 0 — MR URL 확정**:
- **Jira 코멘트 본문 준비** — `${CLAUDE_PLUGIN_ROOT}/workflow/templates/jira-comment-ship.md` 로드 후 아래 플레이스홀더 치환 → `.work/{issue_key}-ship-comment.md` 로 저장.
  - `{ISSUE_KEY}`, `{MR_URL}`, `{BRANCH}`, `{TARGET_BRANCH}` — 확정값
  - `{SUBJECT}` — 커밋 메시지 요약 부분
  - `{UI_NOTE}` — GIF 첨부 시 "• UI GIF: 첨부" / `--skip-ui-check` 시 "• UI 검증 스킵: {사유}" / UI 변경 없음이면 줄 제거
  - **Authorship footer** — `{COMMAND}` = `ship`, `{AGENT}` = 세션 모델명, `{PLUGIN_VERSION}` = plugin.json version, `{USER}` = `git config user.name`
- `${CLAUDE_PLUGIN_ROOT}/scripts/jira-comment.sh {issue_key} @.work/{issue_key}-ship-comment.md` (Bash) — `@파일` 경로 폼 사용.
  - exit 0 → 코멘트 post 성공.
  - exit 10 → acli 미가용. Handoff 에 "Jira 코멘트: 수동 필요 ({mr_url})" 표기 + 초안 파일 경로 안내.
  - exit 20 → acli 호출 실패. Handoff 에 "Jira 코멘트 실패 ({mr_url}) — 재시도 또는 수동 post" 표기 + 초안 파일 경로 안내.
- `.work/{issue_key}.md` 갱신 — 변경 파일, 검증 결과, MR URL 기록, 상태 블록 `MR-ed` 로 전환.

**exit 10 — MR 미확정 (프리필 URL 폴백)**:
- Jira 코멘트 자동 post 불가 (URL 확정 전) → Handoff 에 "Jira 코멘트: MR 생성 후 수동 post" + 프리필 URL 표기.
- `.work/{issue_key}.md` 상태 블록은 `MR-pending` 으로 전환 (`MR-ed` 금지 — 아직 MR 없음).

## Phase 4: 보고 (Handoff)

**1차 성공 (glab)**:
```
┌─────────────────────────────────────────────┐
│ 출하 완료: {type}: {issue_key} {subject}      │
│ MR: {url}                                    │
│ Jira: IN PROGRESS (머지 대기)                 │
│ 다음: 리뷰어 머지 후 → /land {issue_key}   │
└─────────────────────────────────────────────┘
```

**폴백 (프리필 URL)**:
```
┌──────────────────────────────────────────────┐
│ 출하 준비 완료 (MR 미확정): {subject}          │
│ glab 사용 불가 → 프리필 링크로 대체            │
│ 링크: {prefill_url}                          │
│ 본문이 길면: .work/{issue_key}-mr-body.md    │
│ Jira: IN PROGRESS (MR 생성 후 수동 코멘트)    │
│ 다음: 링크 → Create → /land {issue_key}  │
└──────────────────────────────────────────────┘
```

---

## 실패/예외 처리

- 정적 검증 FAIL → Phase 1 에서 중단. 원인 리포트 후 수정 안내.
- 브라우저 검증 FAIL → Phase 1.5 에서 중단. GIF/콘솔 로그 경로 안내.
- 커밋 훅 실패 → 원인 고치고 새 커밋 (amend 금지 — CLAUDE 규약).
- **MR 생성 실패 (glab 인증 등) → Phase 3-2 폴백 경로 (프리필 URL) 자동 진입**. 푸시는 유지.
- Jira 코멘트 실패 → MR URL 은 출력, 수동 코멘트 안내.

## 원칙

- 이 커맨드는 **RESOLVE 전환 금지**. 머지 후 `/land` 에서만.
- 병렬 지정된 단계는 반드시 단일 메시지 병렬 호출 (순차 전환 금지).
