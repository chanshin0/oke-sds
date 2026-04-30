# Team Workflow Layer 설계 (ceph-web-ui 파일럿)

이 문서는 팀의 Jira→Claude Code→GitLab MR→배포 플로우에 얹는 얇은 워크플로우 레이어의 단일 출처(single source of truth)다. 커맨드·템플릿 수정 시 본 문서도 함께 갱신한다.

## Context

현재 팀의 작업 플로우는 **Jira(Atlassian) → Claude Code → GitLab MR → 트롬본 배포** 구조로 단계 수 자체는 적절하나 다음 문제가 있다.

- **플랜의 비일관성** — 같은 성격의 이슈인데 매번 다른 구조의 플랜이 생성됨
- **테스트 전략의 묵시성** — 플랜에 테스트가 포함되지만 형식이 제각각, 수동 항목 누락 가능
- **Jira 상태 수기 전환** — TO DO → IN PROGRESS → RESOLVE 전환이 사람 손에 의존, 보드 신뢰도 저하
- **추적성 단절** — 지라 ↔ 브랜치 ↔ 커밋 ↔ MR 연결이 컨벤션만 있고 강제 안 됨
- **컨텍스트 전환 비용** — 터미널 ↔ GitLab ↔ 트롬본 3회 전환

Spec Kit(7단계)·GSD(69 커맨드)는 현재 팀 규모에 과하다. 대신 Claude Code 하네스 위에 얇은 워크플로우 레이어를 얹어 기존 단계 수를 늘리지 않고, 각 단계의 출력을 표준화하며, 자동화 가능한 것만 에이전트로 끌어온다. 배포는 **의도적 수동 게이트**로 남긴다.

**목표**: 팀원 누가 작업해도 같은 형식의 계획·MR·상태 흐름이 나오도록 하고, 수동 조작 횟수를 AS-IS 대비 약 1/3로 줄인다.

**범위**: 본 계획은 이 저장소(ceph-web-ui) 단독 파일럿까지. 팀 전체 롤아웃은 1~2주 검증 후 별도 결정.

## 확정 사항

| 항목 | 결정 |
|------|------|
| VCS | **GitLab (MR)**. 기존 `bitbucket-*` 파일은 레거시로 취급 |
| CLI | `glab` (GitLab), `acli` (Jira). Jira 는 acli 단일 (Atlassian MCP 대체 완료, 2026-04-20 /tune). Confluence 는 MCP/REST 유지 |
| 커밋 컨벤션 | `{type}: CDS-XXXX {한국어 요약}` — 기존 `commitlint.config.cjs` 유지 |
| 브랜치 컨벤션 | `{commit-type}/CDS-XXXX-{slug}` — 커밋 type과 동일 접두사 |
| Jira 상태 흐름 | `/pick` 시 TO DO→IN PROGRESS / MR 생성 시 **유지** / **머지 후** `/land`에서만 RESOLVE |
| 커맨드 브랜딩 | 팀 솔루션 **SDS** 접두사 + 물류/비행 은유 (pick→ship→land→recap, where/draft/autopilot/tune) |
| MR 템플릿 | 7섹션 (자동 4 + 수동 3) |
| 배포 | 트롬본 수동 유지 |
| CONVENTIONS SSOT | **`CLAUDE.md`** (tune 2026-04-23 #6). `.team-workflow/CONVENTIONS.md` 는 앵커 인덱스 + 고유 항목(§A 커밋/브랜치 · §B 응답 말투 · §C 검증 경계) 만 담는다. 중복 본문 금지. |
| 플러그인 버전 bump 규약 | **dev 브랜치에 플러그인(`plugin/sds-workflow/**`) 변경이 포함된 MR 머지 시 patch version 1단계 bump** (`plugin.json` + `.claude-plugin/marketplace.json` 동시). 이유: Claude Code `/plugin install` 이 same-version 을 "already installed" 로 스킵 → 팀원 update 시 `/plugin uninstall` 수동 단계 필수화되는 UX 저하. Bump 하면 신규 버전 디렉토리에 자동 설치 → uninstall 불필요. 머지 직전 MR 커밋 또는 머지 후 post-merge 커밋 중 팀 자율 (현재는 머지 MR 에 포함 권장). tune 2026-04-24 (plugin-version-bump-convention). |

## 파일 레이아웃

```
ceph-web-ui/
├── .claude/
│   └── commands/
│       ├── pick.md             ← 티켓을 집는다 (구 start-issue)
│       ├── ship.md             ← 출하한다 (구 finish-issue)
│       ├── land.md             ← 착륙한다 (구 sync-issue)
│       ├── recap.md            ← 비행 보고서 (Stage 2)
│       ├── where.md            ← 지금 어디? — 상태 기반 라우터 (구 next-issue)
│       ├── draft.md            ← 설계도 초안 (Stage 3, 선택)
│       ├── autopilot.md       ← 자동 순항 — 1~5단계 자율 (Stage 4)
│       └── tune.md             ← 기체 튜닝 — 피드백 통합 (Stage 5)
├── plugin/sds-workflow/
│   ├── SPEC.md                     ← 이 문서 (설계·철학·확정 사항)
├── .team-workflow/
│   ├── CONVENTIONS.md             ← 비타협 규칙
│   ├── tune-log.md                ← /tune 피드백 적용 이력
│   ├── templates/
│   │   ├── plan-template.md
│   │   ├── mr-template.md
│   │   ├── work-context.md
│   │   ├── draft-issue.md         ← /draft 용
│   │   ├── recap-comment.md       ← /recap Jira 코멘트
│   │   └── recap-page.md          ← /recap --confluence 페이지
│   └── config.yml
├── .work/                         ← gitignore
│   └── CDS-XXXX.md
└── .gitignore
```

**변경하지 않을 파일**: `commitlint.config.cjs`, `.husky/commit-msg`, `package.json`.

## 커맨드 네이밍 — SDS 브랜딩 + 물류/비행 은유

모든 팀 커맨드는 `sds-` 접두사로 팀 솔루션(SDS) 정체성을 담고, 각 커맨드는 물리적 행위를 떠올리게 하는 단어를 사용해 단계 전이를 직관화한다.

| 커맨드 | 은유 | 단계 역할 |
|-------|------|---------|
| `/pick` | 백로그에서 **집어든다** | 티켓 확보 + 플랜이라는 계약 체결 (EnterPlanMode) |
| `/ship` | 검증 후 컨테이너(MR)에 **출하한다** | lint·type·test·UI 통과 → commit → push → MR |
| `/land` | 활주로(머지)에 **착륙시킨다** | Jira RESOLVE·main pull·브랜치 삭제 |
| `/recap` | 비행 **보고서** | Jira 결과 코멘트 + 선택적 Confluence 페이지 |
| `/where` | 궤도상 **지금 어디?** | 상태 기반 라우터 (읽기 전용) |
| `/draft` | 설계도 **초안** | 신규 Jira 이슈 초안 (선택 사용) |
| `/autopilot` | **자동 순항** | 1~5단계 끝까지 자율 실행 (승인 게이트 없음). 사람 개입은 안전장치 트리거(Deviation·UI 실패·Goal-backward·연속 실패)에 한정. 다중 이슈 시 worktree 격리 + subagent 병렬 |
| `/tune` | 기체 **튜닝** | 피드백을 커맨드·템플릿·설정에 구조화 반영 |

**네이밍 효과**:
- `sds-` 접두사로 외부 스킬과 구분
- 단계 전이가 물리적 이미지(pick→ship→land→recap)로 떠오름
- `ship` / `land` 는 오픈소스 컨벤션(`bors`, GitHub "ship it")과 일치
- `autopilot` 은 자율 실행이지만 조종사(사람)가 있다는 메타포 유지

## 커맨드

### `/pick CDS-XXXX`

**목적**: Jira 이슈 착수 시 필요한 세팅 원샷.

```
Phase 0: 저장소 맥락 런타임 추론 + 규칙 로드
  - package.json, tsconfig.json, vite/webpack config 읽기 → 스택·버전
  - 루트 디렉터리 구조 파악 (src/ 계층)
  - CLAUDE.md + .team-workflow/CONVENTIONS.md 읽기 → 명시적 규칙
  - Phase 1 탐색의 기준선. 추론 가능한 정보는 문서화하지 않고 매번 파생.

Phase 1: 병렬 컨텍스트 수집 (단일 메시지 병렬)
  ├─ acli jira workitem view {issue_key} --json
  ├─ git status
  ├─ git log --oneline -20
  ├─ git log --grep "CDS-" --oneline -20
  └─ Grep/Glob (이슈 키워드 → 영향 파일, Phase 0 결과 기준 delta만 탐색)
  ※ Phase 0 에서 `command -v acli` / `acli jira auth status` 점검.
    미설치·미인증 → 중단 + 설치/인증 안내.

Phase 2: 파생 (순차)
  1) 이슈 타입 → 커밋 type 매핑 (.team-workflow/config.yml)
  2) 이슈 제목에서 kebab-case 영문 slug 3~5단어
  3) git checkout -b {type}/CDS-XXXX-{slug}
  4) Jira 전환: TO DO → IN PROGRESS
  5) .work/CDS-XXXX.md 생성

Phase 2.5: 기능 개요 브리핑 (사용자에게 먼저 설명)
  - 영향 파일 후보 중 진입점 성격 1-2개 Read
  - 3-5문단 브리핑 작성: 기능 이름 / 화면 경로 / 사용자 관점 동작 /
    코드 구조(axios·query·composable 경계) / 현재 증상·변경 요청 포인트
  - 사용자에게 먼저 출력 후 .work/CDS-XXXX.md "## 기능 개요" 섹션 기록
  - 담당자가 기능에 익숙하지 않을 수 있으므로 플랜 검증의 배경을 선제공
  - 추정은 "추정" 으로 명시

Phase 3: 플랜 자동 생성 + 플랜 모드 진입 (강제)
  1) 플랜 전 섹션 자동 초안 작성 (사람 fill-in 금지)
     - 배경 / 목표 / 범위 / 영향 범위 / 구현 접근
     - 테스트 전략 > 정적 / 브라우저 체크리스트
     - 검증 방법 / 보류·가정
     - CONVENTIONS 위반 자동 플래그
  2) 그레이존 질문 수면화 (AskUserQuestion) — 판단 불가 지점만
  3) .work/CDS-XXXX.md "## 플랜" 섹션에 최종 초안
  4) EnterPlanMode 호출 → 플랜 모드 ON (비-readonly 툴 구조적 차단)
  5) 사용자 검토 → 수정 지시 루프 → 승인 시 사용자 ExitPlanMode

사람의 역할: (1) 초안 검증 (2) 수정 지시 (3) 그레이존 질문 답변. 빈칸 채우기 금지.

Handoff 노출:
  ① 플랜 모드 진입 직후: "플랜 초안이다. 검토/수정 후 승인해줘."
  ② ExitPlanMode 직후 1회:
     ┌─────────────────────────────────────────┐
     │ 플랜 승인 완료                            │
     │ 브랜치: {type}/CDS-XXXX-{slug}           │
     │ Jira: IN PROGRESS                       │
     │ 다음: 구현 진행 후 → /ship        │
     └─────────────────────────────────────────┘
```

### `/ship`

**목적**: 검증 → 커밋 → 푸시 → MR 생성 → Jira 코멘트 원샷.

```
Phase 0: 전제 + Deviation 감지 (순차)
  - 현재 브랜치명에서 CDS-XXXX 추출, 형식 불일치 시 중단
  - .work/CDS-XXXX.md "## 플랜" 섹션 비어있는지 확인 (비어있으면 중단)
    · escape hatch: "Trivial fix — no plan needed" 한 줄 기입 시 통과
  - Deviation 체크: 플랜의 "영향 범위" ↔ 실제 `git diff --stat` 비교
    · 불일치 시 AskUserQuestion: (a) 플랜 갱신 (b) 변경 되돌리기 (c) 무시 진행

Phase 1: 정적 검증 병렬 (단일 메시지 병렬)
  ├─ pnpm run lint
  ├─ pnpm run type-check
  └─ pnpm run test
  하나라도 FAIL → 중단 보고

Phase 1.5: 브라우저 검증 (UI 변경 시 자동 실행)
  - UI 변경 감지: git diff --stat 에 src/views/ | src/components/ | src/assets/ | src/locales/
  - 변경 없음 → 스킵
  - 변경 있음:
      1) dev server 응답 확인 (미기동 시 중단, 자동 기동 지양)
      2) .work/CDS-XXXX.md "브라우저 체크리스트" 로드
      3) Claude in Chrome 실행:
         ├─ tabs_context_mcp / tabs_create_mcp
         ├─ gif_creator 시작
         ├─ 체크리스트 단계별 실행 (form_input/computer/find)
         ├─ read_console_messages (에러 패턴 필터)
         └─ gif_creator 종료 → .work/CDS-XXXX-verify-ui.gif
      4) 결과 기록, 실패 시 중단
  - escape hatch: /ship --skip-ui-check (사유 자동 기록)

Phase 1.8: Goal-backward 검증 (순차, 짧음)
  - 플랜의 "목표" + "구현 접근" 다시 로드
  - 현재 diff 가 목표를 달성했는지 에이전트 자문
  - 미달성/의문 시 AskUserQuestion 확인
  - 단순 수정은 "달성 판단 근거 1줄" 기록 후 통과

Phase 2: 커밋 + 푸시 (순차)
  1) git diff --stat, git status
  2) 커밋 메시지 draft: "{type}: CDS-XXXX {요약}"
  3) 사용자 승인
  4) git add + git commit
  5) git push -u remote-sds HEAD

Phase 3: MR 생성 + 병렬 후처리
  1) MR 템플릿 채움:
     - 📸 스크린샷: .work/CDS-XXXX-verify-ui.gif 있으면 첨부, UI 변경 없으면 섹션 제거
  2) glab mr create
  3) 병렬:
     ├─ acli jira workitem comment {issue_key} --body "MR: {url}"
     │    (acli 미가용 시 이 항목 스킵 → Handoff 에 수동 안내)
     └─ .work/CDS-XXXX.md 에 변경파일·검증결과·MR URL 기록

Phase 4: 보고 (Handoff)
  ┌─────────────────────────────────────────────┐
  │ 완료: {type}: CDS-XXXX {요약}                │
  │ MR: {url}                                    │
  │ Jira: IN PROGRESS (머지 대기)                │
  │ 다음: 리뷰어 머지 후 → /land CDS-XXXX  │
  └─────────────────────────────────────────────┘
```

### `/land CDS-XXXX`

**목적**: 머지 후 Jira RESOLVE 전환 + 로컬 정리.

```
Phase 1: MR 상태 확인 (순차)
  - glab mr view {mr-id} --output json
  - 머지 상태 미확인 시 중단

Phase 2: 병렬 정리 (단일 메시지 병렬)
  ├─ acli jira workitem transition {issue_key} --status "RESOLVE"
  │    (acli 미가용 시 스킵 → Handoff 에 "Jira RESOLVE: 수동 필요")
  ├─ git checkout main && git pull
  └─ git branch -d {merged-branch}

Phase 3: Handoff
  "CDS-XXXX RESOLVE 전환 완료. 다음 이슈 → /pick CDS-YYYY 또는 /where"
```

### `/recap CDS-XXXX [--confluence]`

**목적**: 착륙 후 완료 보고. `/land` 에서 결과 보고를 분리해 "착륙" 과 "보고" 를 각자 전담.

```
Phase 1: 컨텍스트 로드
  - .work/{issue_key}.md 에서 플랜 목표·검증 결과·MR URL·머지 상태
  - 상태 != Merged → 중단 ("/land 선행 필요")

Phase 2: Jira 결과 보고 코멘트 초안 (필수)
  .team-workflow/templates/recap-comment.md 로드
  플레이스홀더 치환:
    - 목적 (플랜 목표 1줄)
    - 변경 (diff 요약)
    - 검증 결과 (정적/UI/Goal-backward)
    - 배포 후 확인 포인트
    - MR URL
  불확실 지점 → AskUserQuestion

Phase 3: Confluence 페이지 초안 (--confluence 시만)
  .team-workflow/templates/recap-page.md 로드
  플레이스홀더 치환 (Phase 2 대비 풍부한 서술)
  자동 publish 금지 — 초안만

Phase 4: 사람 승인 → 게시
  - Jira 코멘트 post
  - (옵션) Confluence publish — MCP 미지원 시 수동 안내

Phase 5: 상태 갱신 + Handoff
  - .work/{issue_key}.md 상태: Merged → Recapped
```

**원칙**: 자동 publish 금지. `--confluence` 없으면 Confluence 동작 전혀 없음.

### `/where` — 상태 기반 자동 라우터

**목적**: 현재 저장소·브랜치·이슈 상태를 읽어 **다음으로 실행해야 할 커맨드를 자동으로 결정·실행**. GSD `/gsd-next` 에서 차용하되 우리 3-커맨드 체계에 맞춰 축소.

디자인 철학: "지금 어느 단계에 있었지?" 를 사람이 기억하지 않아도 되도록 한다. 이슈 전환·세션 복귀 시 가장 먼저 입력하는 커맨드.

```
Step 1: 상태 감지 (단일 메시지 병렬)
  ├─ git branch --show-current / git status --short / git log --oneline -5
  ├─ git log remote-sds/main..HEAD --oneline    (로컬 커밋 존재 여부)
  ├─ Glob .work/CDS-*.md                        (최근 작업 컨텍스트)
  └─ 이슈키 추출 시 추가 병렬:
       - .work/{issue_key}.md Read
       - acli jira workitem view {issue_key} --json
         (acli 미가용 시 Jira 축 unknown 처리, 해당 축 의존 경고 스킵)

Step 2: 상태 결정 — 5 축으로 분류
  | 축        | 값                                                  |
  |-----------|----------------------------------------------------|
  | 브랜치     | main / issue_branch                                |
  | 플랜       | 없음 / 있음 / escape_hatch                          |
  | 로컬 커밋  | 없음 / 있음(미푸시) / 푸시됨                         |
  | MR         | 없음 / opened / merged / closed                    |
  | Jira       | TO DO / IN PROGRESS / RESOLVE                      |

Step 3: 라우팅 (9 routes — 매칭 다중 시 진행도 우선: I > G > F > E > D > C > B > A)
  Route A: main + 작업 컨텍스트 없음                → "/pick CDS-XXXX"
  Route B: main + 미해결 이슈 컨텍스트 (MR merged 아님) → git checkout 제안 또는 /land
  Route C: 이슈 브랜치 + 플랜 없음                    → "/pick {issue_key}" (복구)
  Route D: 이슈 브랜치 + 플랜 있음 + 로컬 변경 없음    → "구현 시작" 안내
  Route E: 이슈 브랜치 + 플랜 있음 + 로컬 커밋 + 미푸시 → "/ship"
  Route F: 이슈 브랜치 + MR opened                    → "리뷰 대기. 머지 후 /land"
  Route G: 이슈 브랜치 + MR merged + Jira IN PROGRESS → "/land {issue_key}"
  Route H: 이슈 브랜치 + MR merged + Jira RESOLVE + main 미 체크아웃 → "git checkout main && pull"
  Route I: .work/{issue_key}.md 상태 Merged + Recapped 아님 → "/recap {issue_key}"

Step 4: 안전 게이트 (실행 전 검사)
  - 미커밋 변경 + 제안이 브랜치 스위치/삭제면 경고
  - Route E 제안 시 플랜 "영향 범위" ↔ diff 일치 여부 미리 경고
  - 브랜치는 이슈 중인데 Jira TO DO → Phase 2 전환 누락 경고
  - merged MR 에 신규 커밋 → 새 브랜치 권장 경고
  --force 플래그 시 게이트 우회

Step 5: 제안 출력 + 실행 (읽기 전용)
  - dry-run 또는 게이트 트리거 시: 현재 위치·제안·경고 박스만 출력
  - 기본: 제안 출력 후 "다음 커맨드 입력" 유도
  - 본 커맨드는 /pick·/ship·/land·/recap 을 내부에서 직접 실행하지 않음
    (슬래시 커맨드 호출은 사용자가 한다 — 의도된 최소 부작용)
```

**/where 의 가치 포인트**:
- 복귀 시 0-friction: 어느 단계인지 기억할 필요 없음
- 멀티 이슈 병행 시 컨텍스트 전환 쉬움
- Dry-run 모드로 "지금 뭐가 다음이지?" 확인만 가능

### `/autopilot CDS-XXXX [CDS-YYYY ...] [--stop-at <phase>] [--dry-run]` — 자율 순항

**목적**: 사용자 1~5단계(등록 → 계획 → 구현 → 검증 → MR)를 **한 호출로 끝까지 자율 실행**. 머지 이후는 `/land` → `/recap` 별도. 이슈 키 N≥2 전달 시 다중 모드로 분기 (worktree 격리 + subagent 병렬).

승인 게이트는 폐기되었다 (2026-04-29). 검토를 원하는 흐름은 `/pick` → 수동 구현 → `/ship` 분리 사용을 권장.

```
Phase 0: 인자 파싱 — 이슈 키 N개 카운트 → 단일/다중 모드 결정

[단일 모드] N==1 또는 자유 프롬프트
Phase A: 이륙 — /pick 실행 (플랜 자동 초안만, EnterPlanMode 호출 없음)
  (인자가 자유 프롬프트면 /draft 선행해 이슈부터 생성)
  → Phase A-3: pick 코멘트 1건 post

Phase B: 구현 — 플랜의 "구현 접근" 단계별 자동 실행
  - 편차/그레이존: 보수적 자율 결정 + .work "## 결정 메모" 기록
  - 한 단계 3회 연속 실패 시 failed 종료
  → Phase B-2: implement 코멘트 1건 post

Phase C: 검증 — /ship Phase 0~1.8 (정적·브라우저·Goal-backward)
  - 실패 시 자동 재시도 금지, 사용자 개입
  - 검증 결과는 Phase D ship 코멘트에 한 줄로 흡수

Phase D: 출하 — /ship Phase 2~3
  - 커밋 메시지 자동 확정
  - 커밋 · 푸시 · MR · ship 코멘트 1건 post

Phase E: Handoff — "머지 후 /land → /recap"

[다중 모드] N>=2
Phase M: 다중 이슈 병렬 실행
  - working tree clean 강제, 워크트리 충돌 사전 검사
  - 각 이슈마다 Task agent (isolation: "worktree") spawn — 단일 메시지 병렬
  - 각 subagent 가 자기 워크트리에서 단일 모드 Phase A-E 실행
  - 페이즈 코멘트 스킵 (ship 코멘트만 1건씩, Jira watcher 메일 폭증 방지)
  - 결과 aggregate → 다중 모드 전용 Handoff (성공/부분/실패 분리)
  - 워크트리는 자동 정리하지 않음 (사용자 머지 판단 후 git worktree remove)
```

**사람 개입 — 안전장치 트리거 시만**:

| # | 트리거 | 시점 | 단일 모드 | 다중 모드 |
|---|-------|------|---------|---------|
| 1 | Deviation (플랜 밖 변경) | Phase C `/ship` Phase 0 | 자동 중단 → 사용자 결정 | 발생 subagent 만 `failed` 종료 |
| 2 | UI 검증 실패 | Phase C `/ship` Phase 1.5 | 자동 중단 → 사용자 결정 | 발생 subagent 만 `failed` 종료 |
| 3 | Goal-backward 의문 | Phase C `/ship` Phase 1.8 | 자동 중단 → 사용자 결정 | 발생 subagent 만 `failed` 종료 |
| 4 | 연속 실패 3회 | Phase B 어느 단계든 | 결정 메모 기록 후 `failed` | 동일 |

**안전 장치**:
- `/ship` Phase 0 Deviation 체크 유지
- `--stop-at <phase>` — pick / implement / ship-preflight / mr
- `--dry-run` — 경로만 출력
- `--skip-ui-check` 는 autopilot 에서 비활성 (UI 검증 생략은 사람의 명시적 선택이어야 함)
- 다중 모드 working tree clean 강제 + 워크트리 격리 (`isolation: "worktree"`)
- 다중 모드 페이즈 코멘트 스킵 (ship 만 post)

**적용 권장**: Trivial ~ Medium 복잡도. 여러 도메인 교차·외부 API 계약 변경 이슈는 `/pick` 개별 호출 권장. 다중 모드는 비슷한 패턴의 trivial batch 작업에 한정 — 도메인 교차·상호 의존 이슈는 단일 모드 순차 처리.

### `/draft "자유 프롬프트"` — 신규 이슈 초안 (선택)

**목적**: 개발자 본인이 관찰한 버그·개선을 Jira 에 등록. PM 기획 이슈는 기존대로 수기.

```
Phase 1: 입력 수신 + 키워드 파싱
Phase 2: 병렬 컨텍스트 수집
  ├─ acli jira workitem search --jql '...' --json  (중복/유사 이슈 탐지, acli 미가용 시 스킵)
  ├─ Grep / Glob                   (영향 파일 후보)
  └─ git log --grep                (관련 과거 커밋)
Phase 3: description 초안 (draft-issue.md 5섹션)
  - 3-1: 중복 탐지 경고 (유사도 70% 이상 시 대안 제시)
Phase 4: 🚦 그레이존 질문 (타입·우선순위·assignee·재현 세부)
Phase 5: 최종 미리보기 + 🚦 등록 승인
Phase 6: Handoff — "다음: /pick {new_issue_key}"
```

**원칙**: 중복 탐지를 우선, 그레이존은 무조건 사람에게. description 5섹션 구조 고정.

### `/tune "자유 형식 피드백" [--review]` — 피드백 → 시스템 통합 창구

**목적**: 운용 중 피드백을 구조화된 수정 제안 + 적용 로그로 변환. 커맨드·템플릿·설정을 팀이 함께 튜닝하는 공식 창구.

```
모드 A: 피드백 접수 (기본)
  Phase 1: 카테고리 판정 (command-behavior/template/config/config-local/design-principle)
  Phase 2: Diff 초안 + 영향 범위 + 리스크 + 상태 초기값
  Phase 3: 🚦 그레이존 확인 (즉시 적용/대기/폐기, 브랜치 전략)
  Phase 4: 적용 + tune-log.md 엔트리 추가 + 🚦 커밋 메시지 승인
  Phase 5: Handoff

모드 B: 대기 엔트리 리뷰 (--review)
  tune-log.md 의 deferred 엔트리 일괄 리뷰
```

**안전 장치**:
- E2E 영향 자동 판정 → `needs-e2e` 로 적용 보류
- SPEC.md "확정 사항" 표 변경 시 추가 확인 (철학 변경)
- Amend 금지 (CLAUDE 규약 준수)

**대상**: 워크플로우 시스템만. 제품 코드(`src/**`) 수정은 대상 아님 — `/pick` 또는 `/draft` 사용.

## 피드백 루프

워크플로우 자체도 **워크플로우** 로 개선한다.

| 단계 | 역할 |
|------|------|
| 관찰 | 팀원이 `/sds-*` 사용 중 비효율·버그 발견 |
| 접수 | `/tune "피드백 원문"` 호출 |
| 분류 | 에이전트가 카테고리·대상 파일 판정 |
| 초안 | 수정 Diff + 영향 범위 + 리스크 |
| 결정 | 사람이 즉시 적용 / 대기 / 폐기 |
| 기록 | `tune-log.md` 엔트리 (모든 결정 이력) |
| 적용 | 승인 시 Edit + 커밋 |
| 되돌아보기 | `--review` 로 `deferred` 일괄 재검토 |

**원칙**:
- 피드백이 시스템에 녹지 않으면 같은 피드백이 반복된다 — `tune-log.md` 로 이력 축적
- 파일럿 철학(SPEC.md "확정 사항") 변경은 별도 확인 게이트
- 빠른 적용 (applied) 이 기본, 확신 없으면 deferred, 폐기(rejected) 이력도 남긴다

## 병렬 처리 포인트

| 위치 | 병렬 항목 | 기대 효과 |
|------|---------|---------|
| `/pick` Phase 1 | Jira + git 상태/로그 + 영향 파일 탐색 + 유사 커밋 | 컨텍스트 수집 40~60% 단축 |
| `/ship` Phase 1 | lint + type-check + test | 순차 대비 2~3배 |
| `/ship` Phase 3 | Jira 코멘트 + work-context 기록 | 네트워크 I/O 겹침 |
| `/land` Phase 2 | Jira 전환 + main pull + 브랜치 삭제 | 네트워크 지연 흡수 |

**주의**: Bash 병렬은 Claude Code가 단일 메시지에 여러 Bash 툴 호출을 넣을 때만 병렬 실행. 커맨드 프롬프트에 "이 단계는 반드시 단일 메시지 병렬 호출"로 명시한다.

## 템플릿

### mr-template.md

```markdown
## 🔗 Jira
[CDS-XXXX](https://<your-team>.atlassian.net/browse/CDS-XXXX) — {이슈 제목}

## 📝 변경 요약
{자동 초안 → 사람이 1-3줄로 보정}

## 📂 변경 파일
{git diff --stat 기반}

## ✅ 자동 검증
- lint: PASS/FAIL
- type-check: PASS/FAIL
- test: PASS/FAIL (coverage: N%)

## 🧪 테스트 방법
{재현/확인 절차}

## ⚠️ 리뷰 포인트 (선택)
{필요 시만, 없으면 섹션 제거}

## 📸 스크린샷 (UI 변경 시)
{Before/After, UI 변경 없으면 섹션 제거}
```

### plan-template.md

모든 섹션은 에이전트가 자동 채움. 각 섹션 헤더 아래 `<!-- auto: ... -->` 주석으로 생성 소스 명시.

```markdown
# CDS-XXXX: {title}  <!-- auto: Jira summary -->

## 배경
<!-- auto: Jira description 3-5줄 요약 -->

## 목표
<!-- auto: Jira acceptance criteria / description 목표 문장 -->

## 범위 (포함 / 제외)
<!-- auto: 제목 + 영향 파일 후보 파생 -->

## 영향 범위 (파일 / 컴포넌트 / API)
<!-- auto: Phase 1 Grep/Glob + git log --grep -->

## 구현 접근 (단계별)
<!-- auto: 영향 파일 읽고 단계별 제안 -->

## 테스트 전략
### 정적 (pnpm scripts)
<!-- auto: lint / type-check / test + 추가 vitest 케이스 제안 -->

### 브라우저 체크리스트 (/ship Phase 1.5에서 자동 실행)
<!-- auto: 변경된 view/route 감지 후 체크리스트. UI 변경 없으면 "해당 없음" -->
- [ ] {URL 경로} 접속 → {액션} → {기대 결과}
- [ ] console 에러/경고 없음

## 검증 방법
<!-- auto: 테스트 전략에서 파생 -->

## 보류 / 가정 사항
<!-- auto: 불확실 지점 수집. 없으면 "없음" -->
```

**사람의 역할**: (1) 검증 (2) 수정 지시 (3) 그레이존 답변. **빈칸 채우기 금지**.

### work-context.md

```markdown
# CDS-XXXX

## 상태 (auto, 각 커맨드가 갱신)
단계: Planning | Implementing | Verifying | MR-ed | Merged
브랜치: {type}/CDS-XXXX-{slug}
검증: lint — / type-check — / test — / ui —
다음 액션: {command}

## Jira (auto)
Link / Type / Priority / Reporter / Assignee
요약:

## 영향 파일 후보 (auto)

## 플랜
[plan-template 구조 전체 초안]

## 구현 로그
[플랜 단계별 커밋 해시·메모]

## 검증 결과
- 정적: lint / type-check / test
- 브라우저: verify-ui.gif 경로 + 체크리스트 결과

## Deviation / Goal-backward 기록
[/ship 에서 감지된 편차·목표 달성 판단 근거]

## MR
URL / 리뷰 상태
```

### .team-workflow/config.yml

```yaml
jira:
  transitions:
    start: {from: "TO DO", to: "IN PROGRESS"}
    resolve: {from: "IN PROGRESS", to: "RESOLVE"}

branch:
  prefix_map:
    Bug: fix
    Task: feat
    Story: feat
    Improvement: refactor
    Documentation: docs
  slug: {max_words: 5, separator: "-"}

commit:
  format: "{type}: {issue_key} {subject}"

mr:
  title_format: "{type}: {issue_key} {subject}"
  template_path: .team-workflow/templates/mr-template.md
```

## 플랜 모드 강제 메커니즘

`/pick` ↔ `/ship` 사이 구간을 "실수로 바로 코딩" 하지 못하도록 다층 방어.

| 레이어 | 수단 | 효과 |
|-------|------|------|
| 1. 구조적 차단 | `/pick` 말미에 내장 `EnterPlanMode` 호출 | 플랜 모드가 비-readonly 툴을 런타임 차단 |
| 2. 프롬프트 규약 | 커맨드 본문에 "플랜 승인 전 코드 수정 금지" 명시 | 에이전트 자발적 유지 |
| 3. 선행 조건 | `/ship` Phase 0에서 플랜 섹션 존재 확인 | 플랜 없이 finish 방지 |
| 4. (선택) 훅 | `.claude/hooks/pre-edit-guard.js` | 커맨드 우회 편집에도 경고 |

**Escape hatch**: `Trivial fix — no plan needed` 한 줄 기입 시 통과. 남용 금지는 팀 규칙으로 관리.

## 배포 전략 (A → B 단계 승격)

| 단계 | 형태 | 사용처 | 전환 트리거 |
|------|------|--------|------------|
| A (Phase 1~3) | ceph-web-ui 에 `.claude/commands/*`, `.team-workflow/*` 직접 커밋 | 파일럿 1개 저장소 | — |
| B (Phase 4) | 별도 git repo → `/plugin install <git-url>` | 팀 전체 저장소 | 파일럿 2주 안정 + 팀 합의 |
| C (미채택) | `npx @<your-org>/team-workflow init` 스타일 | — | 플러그인으로 해결 안 될 때만 재검토 |

**B 승격 체크리스트**:
- `/pick` → `/ship` → `/land` E2E 5건 이상 성공
- 템플릿 수정이 1주 이상 없음 (안정화 신호)
- 팀 2인 이상 동일 플로우 재현 성공

## 구현 Phase

### Phase 1 — MVP (반나절~하루)
1. `plugin/sds-workflow/SPEC.md` ✓ (이 파일)
2. `.team-workflow/CONVENTIONS.md` — CLAUDE.md "솔루션 규칙" 에서 비타협 항목 추출
3. `.team-workflow/workflow.yml`, `plan-template.md`, `work-context.md`
4. `.claude/commands/pick.md`
5. `.gitignore`에 `.work/` 추가
6. 실제 Jira 이슈 1건으로 `/pick` E2E

### Phase 2 — 완성 (하루)
8. `.team-workflow/templates/mr-template.md`
9. `.claude/commands/ship.md`
10. `glab` 인증 확인
11. 실제 이슈 1건으로 MR 생성까지 E2E

### Phase 3 — 보정 (2~3시간)
12. `.claude/commands/land.md`
13. 엣지 케이스 분기
14. 에러/롤백 안내

### Phase 3.5 — 라우터 (Phase 1~3 안정 후 1시간)
15. `.claude/commands/where.md` — 상태 탐지·라우팅 (읽기 전용 제안)

### Phase 4 — 결과 보고 분리 + 신규 이슈 등록
16. `.claude/commands/recap.md` — `/land` 에서 결과 보고 책임 분리 (Jira 코멘트 + `--confluence` 옵션)
17. `.team-workflow/templates/recap-comment.md`, `recap-page.md`
18. `.claude/commands/draft.md` — 개발자 관찰 기반 신규 Jira 이슈 초안
19. `.team-workflow/templates/draft-issue.md`

### Phase 5 — 자율 실행 + 피드백 루프
20. `.claude/commands/autopilot.md` — pick→ship 을 한 호출로 자율 실행 (사람 개입 게이트 4개 유지)
21. `.claude/commands/tune.md` — 피드백을 커맨드·템플릿·설정에 구조화 반영
22. `.team-workflow/tune-log.md` — 피드백 적용 이력

### Phase 6 — 팀 공유 및 플러그인 승격 (별도)
23. `CLAUDE.md` 하단 안내 섹션
24. 팀 1인 시범 운영 → 피드백
25. Claude Code 플러그인으로 분리

## 검증 방법

**Phase 1 E2E**: 테스트용 Jira 이슈 1건 → `/pick CDS-XXXX` →
- 브랜치 `{type}/CDS-XXXX-{slug}` 생성
- Jira IN PROGRESS 전환
- `.work/CDS-XXXX.md` 생성, 이슈 요약 자동 채워짐
- Phase 1 병렬 수집이 단일 메시지 내 툴 호출로 확인 가능

**Phase 2 E2E**: 소규모 코드 변경 → `/ship` →
- 정적 검증 3개가 단일 메시지 병렬
- UI 변경 포함 시 Phase 1.5 자동 실행, GIF 생성
- UI 변경 없을 시 Phase 1.5 스킵
- 커밋 메시지 형식, MR 생성, 7섹션 채움, Jira 코멘트
- 이 시점 Jira IN PROGRESS (RESOLVE 금지)

**Phase 3 E2E**: MR 머지 → `/land CDS-XXXX` →
- Jira RESOLVE, main 최신화, 머지 브랜치 삭제

**Phase 3.5 E2E**: `/where` →
- 브랜치·상태별로 라우트 A~H 중 정확한 결정 출력
- 커맨드형 라우트는 자동 실행, 안내형은 메시지만

## 참조 기존 파일

| 파일 | 역할 |
|------|------|
| `commitlint.config.cjs` | 커밋 type 허용 목록 (브랜치 prefix_map 이와 일치) |
| `.husky/commit-msg` | 커밋 메시지 검증 (유지) |
| `package.json` | `lint / type-check / test / build:dev` 스크립트 |
| `CLAUDE.md` | 프로젝트 규칙 |

## 2026-04-21 — B 단계 승격 (플러그인화)

파일럿 저장소(ceph-web-ui) 내부에서 Claude Code 플러그인 구조로 재조직했다. 배포 전략 표의 B 단계가 이 날짜로 적용됨.

### 달라진 것

- **`.claude/commands/sds-*.md` 8개 → `plugin/sds-workflow/commands/` 9개 이전** (신규 `/init` 포함).
- **`.team-workflow/templates/*` 6개 → `plugin/sds-workflow/workflow/templates/`** 로 이동.
- **`.team-workflow/config.yml` 분할**:
  - 저장소 비의존 필드(transitions·prefix_map·slug·commit.types·validation 등) → `plugin/sds-workflow/workflow/config.defaults.yml`
  - 저장소 의존 필드(jira.project_key·jira.base_url·confluence·federation.contract_surface) → `.team-workflow/workflow.yml`
- **repo 루트 `.claude-plugin/marketplace.json` 추가** — ceph-web-ui 자체가 self-hosted marketplace.
- **`/init` 신규** — 새 저장소에서 `.team-workflow/` 스캐폴드 1회 생성.
- **모든 `sds-*` 커맨드 상단에 Preamble 블록 주입** — 커맨드는 `.team-workflow/workflow.yml` 에서 `PROJECT_KEY` 등을 런타임 로드. `CDS-` 하드코딩 제거.

### 설치·배포 (다른 저장소용)

```
# git URL 방식 — prd 에 marketplace.json 머지 전까지 #dev 핀 필요
/plugin marketplace add <your-gitlab-host>/<your-group>/<your-project>.git#dev
# 또는 로컬 clone 경로 방식
/plugin marketplace add /path/to/<your-marketplace>

/plugin install sds-workflow@<your-marketplace>
/init   # 각 저장소에서 1회
```

### 파일 레이아웃 (갱신)

```
ceph-web-ui/
├── .claude-plugin/marketplace.json            ← marketplace manifest
├── plugin/sds-workflow/                       ← 플러그인 본체
│   ├── .claude-plugin/plugin.json
│   ├── SPEC.md                                ← 설계·철학·확정 사항 (이 문서)
│   ├── README.md
│   ├── CHANGELOG.md                           ← 플러그인 contract 변경 이력
│   ├── commands/*.md                          ← 9개 (init 포함)
│   ├── workflow/
│   │   ├── preamble.md                        ← 공통 설정 로드 절차 SSOT
│   │   ├── config.defaults.yml                ← 공통 기본값
│   │   ├── templates/                         ← 6개 템플릿
│   │   └── seeds/                             ← /init 씨앗
│   ├── scripts/                               ← 결정성 보장용 외부화 로직
│   │   ├── create-mr.sh                       ← /ship Phase 3-2 (glab → prefill URL 폴백)
│   │   └── jira-comment.sh                    ← /ship Phase 3-3 (acli wrapper)
│   └── references/
│       ├── artifact-types.md                  ← artifact 레지스트리 (sync-points)
│       └── conventions.md                     ← enum·포맷·표준 계약 SSOT
└── .team-workflow/                            ← 저장소 소유
    ├── workflow.yml                           ← project_key 등 override
    ├── CONVENTIONS.md
    └── tune-log.md
```

### `/tune` 카테고리 재분류

카테고리 enum 의 SSOT 는 `plugin/sds-workflow/references/conventions.md §1`. 아래는 SPEC 차원의 요약.

| 카테고리 | 적용 경로 | 소유자 |
|---|---|---|
| `command-behavior` | `plugin/sds-workflow/commands/*` | 플러그인 repo |
| `template` | `plugin/sds-workflow/workflow/templates/*` | 플러그인 repo |
| `config` (공통 기본값) | `plugin/sds-workflow/workflow/config.defaults.yml` | 플러그인 repo |
| `config-local` (저장소별) | `.team-workflow/workflow.yml` | 현재 저장소 |
| `design-principle` | `plugin/sds-workflow/SPEC.md` | 플러그인 repo |
| `convention` | `plugin/sds-workflow/references/conventions.md` | 플러그인 repo |
| `registry` | `plugin/sds-workflow/references/artifact-types.md` | 플러그인 repo |

외부 저장소에서 플러그인 소유 파일 수정이 필요하면 `/tune` 이 "플러그인 repo 에 PR 필요" 로 안내하고 `deferred` 기록.

`/tune` Phase 2 는 `references/artifact-types.md` 를 Read 해 `Sync with` 목록·"영향 범위 자동 확장 규칙" 으로 2차 영향 파일을 후보에 자동 포함한다 — 한 피드백의 일관성 전파를 강제하는 메커니즘.

### 배포 전략 표 (현재 상태)

| 단계 | 형태 | 사용처 | 상태 |
|---|---|---|---|
| A | ceph-web-ui 에 `.claude/commands/*`, `.team-workflow/*` 직접 커밋 | 파일럿 1 저장소 | 종료 (2026-04-20) |
| **B** | self-hosted marketplace (`.claude-plugin/marketplace.json` + `plugin/sds-workflow/`) | 팀 전체 저장소 | **진행 (2026-04-21~)** |
| C | 외부 marketplace 제출 | 오픈소스 | 미채택 |

---

## 주의사항 / 비범위

- 배포(트롬본) 자동화 없음 — 안전 게이트
- `/ship` 는 Jira RESOLVE 하지 않음 — 머지 후 `/land`
- `.work/` 는 gitignore
- 기존 수동 플로우 병행 가능 — 강제 아님
- 서브에이전트·스펙 파일 현 단계 미도입 — 과잉
- `.bitbucket/pull_request_template.md` 는 레거시로 방치
- 플러그인 자체 CI(lint/test) 세팅은 범위 외. 초기 배포 버전 `0.1.0`.
- 다른 팀 저장소 마이그레이션은 파일럿 E2E 성공 후 별도 결정.
