# sds-workflow

오케스트로 SDS 팀 워크플로우 Claude Code 플러그인.

Jira(acli) → Claude Code → GitLab MR(glab) 의 **집기(pick) → 출하(ship) → 착륙(land) → 보고(recap)** 파이프라인을 표준화한다. 상세 설계는 `SPEC.md` 참조.

## 설치

이 플러그인은 **ceph-web-ui 저장소 자체가 self-hosted marketplace** 다. 별도 repo 없이 ceph-web-ui 를 marketplace 로 등록해 설치한다.

```
# 1) marketplace 등록 (사용자 계정당 1회, 이름: remote-ceph-admin)
# A. git URL + dev 브랜치 핀 (운영 트렁크 prd 에는 marketplace.json 미반영)
/plugin marketplace add http://gitlab.prd.console.trombone.okestro.cloud/SDS306/remote-ceph-admin.git#dev
# B. 또는 로컬 clone 경로 (ceph-web-ui 작업자 권장)
/plugin marketplace add /path/to/remote-ceph-admin

# 2) 설치 (사용자 계정당 1회)
/plugin install sds-workflow@remote-ceph-admin

# 3) 플러그인 reload — 현재 세션은 구버전 커맨드 인덱스를 쥐고 있으므로 필수
/reload-plugins
# 반영이 안 되면 Claude Code 를 새 탭/프로세스로 재시작
```

`#dev` 핀은 `prd` 기본 브랜치에 `marketplace.json` 이 머지될 때까지 한시적으로 필요하다. 머지 이후에는 핀 제거 가능. 이후 플러그인 업데이트(`/plugin marketplace update`) 후에도 **3) `/reload-plugins`** 를 반복한다.

## 업데이트 (팀원 공통)

플러그인 새 버전 (v0.3.1+) 이 dev 에 머지됐을 때:

```
# 터미널
git checkout dev && git pull --ff-only
```

→ `git pull` 로 플러그인 source 가 갱신된 경우 Claude Code 캐시는 아직 이전 버전이므로 아래 3줄을 순차 입력해 반영:

```
/plugin marketplace update
/plugin install sds-workflow@remote-ceph-admin
/reload-plugins
```

또는 단축 커맨드:
```
/sds-workflow:update
```
→ 위 3줄 시퀀스를 안내 출력.

### 동작 원리 / 한계

`/plugin install` 은 `plugin.json` version 을 기준:
- **새 버전** → 새 디렉토리에 설치 → 자동 반영
- **같은 버전** → "already installed" 스킵 → `/plugin uninstall` 먼저 필요

**머지마다 patch version 자동 bump 규약** (SPEC.md 확정 사항) 적용 후부터는 uninstall 단계 불필요.

**완전 자동화 불가** (Claude Code 공식 제약): hook 은 slash 커맨드를 직접 invoke 할 수 없고, 설정 수정도 현재 session 에 즉시 반영 안 됨. 따라서 `/plugin install` 등 실제 반영 단계는 사용자 클릭 유지.

첫 `/sds-workflow:ship` 또는 `/sds-workflow:autopilot` 호출 시 `remote-sds` remote 미등록 상태면 자동 등록 + fetch 프롬프트. 수동 등록도 가능:

```bash
git remote add remote-sds http://gitlab.prd.console.trombone.okestro.cloud/SDS306/remote-ceph-admin.git
git fetch remote-sds
```

## 새 저장소에서 첫 사용

```
# 저장소 루트에서
/sds-workflow:init
```

`/sds-workflow:init` 은 다음을 수행한다:
- `.team-workflow/workflow.yml` 생성 (project_key·base_url·space_key 대화형 입력)
- `.team-workflow/CONVENTIONS.md` seed
- `.team-workflow/tune-log.md` 빈 로그
- `.gitignore` 에 `.work/` append
- **`remote-sds` git remote 자동 등록** (Phase 4.5) — 팀 공용 고정 이름. `/ship` 의 push 타겟, `/where`·`/recap` 의 diff base 가 이 이름에 의존한다. 사용자마다 `origin` 이 다른 프로젝트를 가리키는 문제 방지 목적.

그 뒤 `CONVENTIONS.md` 를 저장소 현황에 맞게 1회 정리하면 운영 준비 완료. 기술 스택·아키텍처 맥락은 `/sds-workflow:pick` 이 매번 `package.json`·`tsconfig`·폴더 구조·`CLAUDE.md` 에서 런타임 추론한다.

## 커맨드

커맨드는 Claude Code 플러그인 기본 규약에 따라 `/<plugin-name>:<command>` 형태로 호출한다. 이 문서는 풀 네임 `/sds-workflow:<command>` 를 기본 표기로 쓴다. 다른 플러그인과 이름이 겹치지 않을 때는 Claude Code 가 단축 `/pick` 으로 매칭해 주기도 하지만, 안전하게는 접두사 포함을 권장.

| 커맨드 | 역할 |
|---|---|
| `/sds-workflow:init` | 저장소 부팅 — `.team-workflow/` 스캐폴드 생성 + project_key 등 초기값 기록 |
| `/sds-workflow:pick CDS-XXXX` | Jira 이슈 가져오기 — 컨텍스트 수집 → 브랜치 생성 → Jira 전환 → 플랜 자동 초안 → 플랜 모드 진입 |
| `/sds-workflow:ship` | 검증(테스트) → 커밋 → 푸시 → MR 등록 → Jira 코멘트 원샷 |
| `/sds-workflow:land CDS-XXXX` | MR 수동 머지 후 — Jira RESOLVE 전환 + 로컬 정리 |
| `/sds-workflow:recap CDS-XXXX [--confluence]` | land 완료 후 결과 및 조치 내용 초안 — Jira 결과 코멘트, 선택적 Confluence 페이지 |
| `/sds-workflow:where` | 현재 상태를 감지해 다음 액션 안내 |
| `/sds-workflow:draft "자유 프롬프트"` | 신규 Jira 이슈 초안 — 자유 프롬프트 → 5섹션 구조화 + 중복 탐지 |
| `/sds-workflow:autopilot CDS-XXXX [CDS-YYYY ...] [--stop-at <phase>] [--ralph]` | 자율 운행 — pick → 구현 → ship 원샷. 다중 이슈 시 worktree 격리 + subagent 병렬 (`--ralph` 자동 강제). 예: `/sds-workflow:autopilot CDS-2150 CDS-2151 CDS-2152` |
| `/sds-workflow:tune "피드백"` | 피드백을 sds 워크플로우(커맨드·템플릿·설정)에 구조화해 반영 |
| `/sds-workflow:update` | 플러그인 업데이트 3줄 슬래시 커맨드 시퀀스 안내 (git pull 후 실행) |

`CDS-XXXX` 는 예시다. `.team-workflow/workflow.yml` 에 기록된 `jira.project_key` 로 런타임 치환된다.

## 구조

```
plugin/sds-workflow/
├── .claude-plugin/plugin.json
├── SPEC.md                   # 설계·철학·확정 사항
├── README.md                 # 이 문서
├── CHANGELOG.md              # contract 변경 이력
├── commands/                 # 9개 슬래시 커맨드
├── workflow/
│   ├── preamble.md           # 공통 설정 로드 절차 SSOT (8개 커맨드 참조)
│   ├── config.defaults.yml   # 공통 기본값 (transitions/prefix_map/validation 등)
│   ├── templates/            # plan/mr/work-context/draft-issue/recap-comment/recap-page
│   └── seeds/                # /init 가 새 저장소로 복사하는 씨앗
├── scripts/                  # 결정성 보장용 외부화 로직 (GSD·spec-kit 선례)
│   ├── create-mr.sh          # /ship Phase 3-2 (glab → 프리필 URL 폴백)
│   └── jira-comment.sh       # /ship Phase 3-3 (acli 코멘트 wrapper)
└── references/
    ├── artifact-types.md     # 문서 레지스트리 (sync-points + 영향 범위 자동 확장 규칙)
    └── conventions.md        # enum·포맷·표준 계약 SSOT
```

호스트 저장소 (각 프로젝트) 에는 다음만 남는다:

```
.team-workflow/
├── workflow.yml           # project_key 등 저장소별 override
├── CONVENTIONS.md         # 저장소별 비타협 규칙
└── tune-log.md
```

## 설정 머지

모든 `sds-*` 커맨드(init 제외)는 본문 실행 전 `${CLAUDE_PLUGIN_ROOT}/workflow/preamble.md` 의 공통 로드 절차를 Read 로 수행한다. 절차는 preamble.md 가 SSOT:

1. `${CLAUDE_PLUGIN_ROOT}/workflow/config.defaults.yml` Read
2. `.team-workflow/workflow.yml` Read (없으면 `/sds-workflow:init` 선행 안내)
3. deep-merge → `PROJECT_KEY`, `JIRA_BASE_URL`, `TRANSITIONS`, `PREFIX_MAP`, `VALIDATION_STATIC`, `UI_CHANGE_GLOBS`, `TEMPLATE_ROOT` 추출
4. 이슈키 정규식 `^${PROJECT_KEY}-\d+$` 로 모든 인자 검증

절차를 바꾸려면 preamble.md 한 곳만 수정 — 8개 커맨드 공통 영향이라 `CHANGELOG.md` 기록 필수.

## 권장 퍼미션 사전 허용

`/sds-workflow:*` 커맨드는 외부 CLI(`acli`·`glab`·`git`·`pnpm`)를 Bash 로 호출한다. 처음 만난 명령마다 Claude Code 가 권한 프롬프트를 띄우므로 자주 쓰는 패턴은 미리 허용해 두면 야간·다중 모드 자율 운행 중에 흐름이 끊기지 않는다.

| 허용 패턴 | 왜 필요 | 사용 커맨드 |
|---|---|---|
| `Bash(acli:*)` | Jira 이슈 조회·전환·코멘트·생성 | pick · ship · land · recap · draft · autopilot |
| `Bash(glab:*)` | GitLab MR 생성 | ship |
| `Bash(git:*)` | 브랜치·커밋·push·diff·status·worktree | 모두 |
| `Bash(pnpm:*)` | 정적 검증 (`lint` / `type-check` / `test`) | ship (Phase 1) |
| `Bash(command -v:*)` | 도구 설치 여부 감지 | acli 쓰는 모든 커맨드 Phase 0 |
| `Bash(bash:*)` 또는 `Bash(${CLAUDE_PLUGIN_ROOT}/scripts/*.sh:*)` | 플러그인 스크립트 실행 (`create-mr.sh`·`jira-comment.sh`) | ship |
| `Bash(mkdir:*)`·`Bash(cp:*)`·`Bash(grep:*)`·`Bash(printf:*)` | seed 복사 + `.gitignore` 패치 | init |

**A. 사용자 계정 전체** — `~/.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(acli:*)",
      "Bash(glab:*)",
      "Bash(git:*)",
      "Bash(pnpm:*)",
      "Bash(command -v:*)",
      "Bash(bash:*)",
      "Bash(mkdir:*)",
      "Bash(cp:*)",
      "Bash(grep:*)",
      "Bash(printf:*)"
    ]
  }
}
```

**B. 프로젝트 한정** — 저장소 루트 `.claude/settings.json` 에 같은 블록. 팀 공유 기준치를 한 곳에서 관리하고 싶을 때.

보안 메모: 와일드카드는 해당 CLI 전체를 허용하므로 Jira/GitLab 자격증명이 설치된 PC 에서만 사용. `Bash(rm:*)` 같은 파괴적 패턴은 일괄 허용하지 않는다.

## 피드백

`/sds-workflow:tune "피드백 원문"` 을 호출한다. 카테고리 enum 의 SSOT 는 `references/conventions.md §1`:

| 카테고리 | 경로 | 소유자 |
|---|---|---|
| `command-behavior` | `plugin/sds-workflow/commands/*` | 플러그인 repo |
| `template` | `plugin/sds-workflow/workflow/templates/*` | 플러그인 repo |
| `config` (공통) | `plugin/sds-workflow/workflow/config.defaults.yml` | 플러그인 repo |
| `config-local` | `.team-workflow/workflow.yml` | 현재 저장소 |
| `design-principle` | `plugin/sds-workflow/SPEC.md` | 플러그인 repo |
| `convention` | `plugin/sds-workflow/references/conventions.md` | 플러그인 repo |
| `registry` | `plugin/sds-workflow/references/artifact-types.md` | 플러그인 repo |

`/sds-workflow:tune` Phase 2 는 `references/artifact-types.md` 를 Read 해 `Sync with` 목록과 "영향 범위 자동 확장 규칙" 으로 2차 영향 파일을 자동 포함한다 — 한 번의 피드백이 관련 문서 전반에 일관되게 전파되도록 강제.

외부 저장소에서 플러그인 소유 파일 수정을 시도하면 `/sds-workflow:tune` 은 "플러그인 repo 에 PR 필요" 로 안내하고 tune-log 에 `deferred` 로 기록한다.

## 버전

`0.3.1` — plugin version bump 규약 확정 + remote-sds 고정 이름·3-layer MR 폴백·ensure-remote-sds fetch 등 원격 결정성 튜닝 세트.
`0.3.0` — tune-seed-2026-04-23 일괄 반영 (plan-template 필수 섹션·autopilot 스코핑·commit-message 템플릿 등).
`0.2.0` — autopilot 다중 이슈 모드 + 공통 설정 로드(preamble) + 결정성 보장 스크립트 + 온보딩/퍼미션 가이드.
`0.1.0` — ceph-web-ui self-hosted marketplace 초기 배포.
