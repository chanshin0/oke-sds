# sds-workflow

Generic Jira → Claude Code → GitLab MR 워크플로우 플러그인.

`acli` (Atlassian CLI) → Claude Code → `glab` (GitLab CLI) 의 **집기(pick) → 출하(ship) → 착륙(land) → 보고(recap)** 파이프라인을 표준화. 상세 설계는 `SPEC.md` 참조.

## 사전 요구사항

| CLI | 용도 |
|---|---|
| `acli` | Jira 이슈 조회·전환·코멘트·생성 |
| `glab` | GitLab MR 생성 (REST API 폴백 가능) |
| `git` | 브랜치·커밋·push·diff |

각 CLI 는 본인 PC 에서 인증 완료된 상태여야 한다. plugin 자체는 자격증명을 보유하지 않는다.

## 설치

이 plugin 은 marketplace 를 통해 설치한다. 너의 marketplace 카탈로그에 이 plugin 을 등록한 뒤:

```
/plugin marketplace add <your-org>/<your-marketplace-repo>
/plugin install sds-workflow@<your-marketplace>
/reload-plugins
```

## 새 저장소에서 첫 사용

```
/sds-workflow:init
```

대화형으로 다음을 묻고 `.team-workflow/workflow.yml` 에 기록:

- `jira.project_key` (예: `PROJ`)
- `jira.base_url` (예: `https://<your-team>.atlassian.net`)
- `gitlab.base_url` (예: `https://<your-gitlab-host>`)
- `gitlab.project_path` (예: `<your-group>/<your-project>`)
- `confluence.base_url`, `confluence.space_key` (선택)

추가로 자동 수행:
- `.team-workflow/CONVENTIONS.md` seed 생성
- `.team-workflow/tune-log.md` 빈 로그 생성
- `.gitignore` 에 `.work/` append
- **`remote-sds` git remote 자동 등록** (Phase 4.5)

### remote-sds 정책

`remote-sds` 는 팀 공용 고정 remote 이름. plugin 의 push 타겟·diff base 가 이 이름에 의존한다. 이유:

- 사용자마다 `origin` 이 fork 등 다른 프로젝트를 가리킬 수 있음 → push 사고 방지
- `remote-sds` 는 항상 워크플로우 대상 GitLab repo 를 가리킴 (init 가 강제 등록)

`/init` Phase 4.5 가 `scripts/ensure-remote-sds.sh` 를 호출해 다음을 수행:
1. `remote-sds` 미등록 → 등록 + fetch
2. 등록됐지만 URL 불일치 → 사용자에게 alert + AskUserQuestion 으로 (a) 교체 / (b) 유지 / (c) 중단
3. 등록됐고 URL 일치 → no-op

이미 운영중인 저장소에서도 `/sds-workflow:ship` 첫 호출 시 같은 보장 절차가 자동 실행됨 (Phase 0-1).

## 커맨드

| 커맨드 | 역할 |
|---|---|
| `/sds-workflow:init` | 저장소 부팅 — `.team-workflow/` 스캐폴드 생성 + remote-sds 등록 |
| `/sds-workflow:pick PROJ-XXXX` | Jira 이슈 가져오기 — 컨텍스트 수집 → 브랜치 생성 → Jira 전환 → 플랜 자동 초안 → 플랜 모드 진입 |
| `/sds-workflow:ship` | 검증(테스트) → 커밋 → 푸시 → MR 등록 → Jira 코멘트 원샷 |
| `/sds-workflow:land PROJ-XXXX` | MR 수동 머지 후 — Jira RESOLVE 전환 + 로컬 정리 |
| `/sds-workflow:recap PROJ-XXXX [--confluence]` | land 완료 후 결과 및 조치 내용 초안 — Jira 결과 코멘트, 선택적 Confluence 페이지 |
| `/sds-workflow:where` | 현재 상태를 감지해 다음 액션 안내 |
| `/sds-workflow:draft "자유 프롬프트"` | 신규 Jira 이슈 초안 — 자유 프롬프트 → 5섹션 구조화 + 중복 탐지. authorship footer 자동 첨부 |
| `/sds-workflow:autopilot PROJ-XXXX [PROJ-YYYY ...] [--stop-at <phase>]` | 자율 운행 — pick → 구현 → ship 원샷. 끝까지 자율 (승인 게이트 없음). 다중 이슈 시 worktree 격리 + subagent 병렬. Phase A-3 / B-2 페이지 코멘트 자동 post |
| `/sds-workflow:tune "피드백"` | 피드백을 sds 워크플로우에 구조화해 반영 |
| `/sds-workflow:update` | 플러그인 업데이트 안내 |

`PROJ-XXXX` 는 예시. `.team-workflow/workflow.yml` 의 `jira.project_key` 로 런타임 치환된다.

## 메트릭 (누적 소요 시간)

`autopilot` Phase 0 가 `start_epoch` 를 `.work/{issue_key}.md` "## 메트릭" 에 기록. 이후 ship/autopilot 페이지 코멘트가 누적 elapsed 를 합성해 `⏱ 누적 {ELAPSED_HUMAN}` 형식으로 footer 에 자동 표기. 다중 모드 subagent 도 자기 워크트리에서 동일 절차.

`scripts/session-metrics.sh ${start_epoch}` 가 elapsed 계산 (POSIX `date` / `printf` 만 의존, macOS · Linux 동작).

## 구조

```
sds-workflow/
├── .claude-plugin/plugin.json
├── SPEC.md                   # 설계·철학·확정 사항
├── README.md                 # 이 문서
├── commands/                 # 슬래시 커맨드
├── workflow/
│   ├── preamble.md           # 공통 설정 로드 절차 SSOT
│   ├── config.defaults.yml   # 공통 기본값 (transitions/prefix_map/validation 등)
│   ├── templates/            # plan/mr/work-context/draft-issue/recap/jira-comment-pick/implement/ship
│   └── seeds/                # /init 가 새 저장소로 복사하는 씨앗
├── scripts/                  # 결정성 보장용 외부화 로직
│   ├── create-mr.sh          # /ship MR 생성 (REST API → glab → 프리필 URL 3-layer 폴백)
│   ├── ensure-remote-sds.sh  # remote-sds 등록 보장
│   ├── jira-comment.sh       # /ship Jira 코멘트
│   └── session-metrics.sh    # autopilot 누적 elapsed 계산
└── references/
    ├── artifact-types.md     # 문서 레지스트리
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

모든 `sds-*` 커맨드(init 제외)는 본문 실행 전 `${CLAUDE_PLUGIN_ROOT}/workflow/preamble.md` 의 공통 로드 절차를 Read 로 수행한다:

1. `${CLAUDE_PLUGIN_ROOT}/workflow/config.defaults.yml` Read
2. `.team-workflow/workflow.yml` Read (없으면 `/sds-workflow:init` 선행 안내)
3. deep-merge → `PROJECT_KEY`, `JIRA_BASE_URL`, `TRANSITIONS`, `PREFIX_MAP`, `VALIDATION_STATIC`, `UI_CHANGE_GLOBS`, `TEMPLATE_ROOT`, `GITLAB_BASE_URL`, `GITLAB_PROJECT_PATH` 추출
4. 이슈키 정규식 `^${PROJECT_KEY}-\d+$` 로 모든 인자 검증

## 권장 퍼미션 사전 허용

`/sds-workflow:*` 커맨드는 외부 CLI 를 Bash 로 호출한다. 자주 쓰는 패턴은 미리 허용해 두면 자율 운행 중 흐름이 끊기지 않는다.

| 허용 패턴 | 사용 커맨드 |
|---|---|
| `Bash(acli:*)` | pick · ship · land · recap · draft · autopilot |
| `Bash(glab:*)` | ship |
| `Bash(git:*)` | 모두 |
| `Bash(pnpm:*)` 또는 `Bash(npm:*)` 등 | ship (Phase 1 정적 검증) |
| `Bash(command -v:*)` | acli 쓰는 모든 커맨드 Phase 0 |
| `Bash(bash:*)` 또는 `Bash(${CLAUDE_PLUGIN_ROOT}/scripts/*.sh:*)` | ship · autopilot |
| `Bash(mkdir:*)`·`Bash(cp:*)`·`Bash(grep:*)`·`Bash(printf:*)` | init |

`~/.claude/settings.json` 또는 프로젝트 `.claude/settings.json`:

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

보안 메모: 와일드카드는 해당 CLI 전체를 허용하므로 자격증명이 설치된 PC 에서만 사용. `Bash(rm:*)` 같은 파괴적 패턴은 일괄 허용하지 않는다.

## 피드백

`/sds-workflow:tune "피드백 원문"` 호출. 카테고리 enum 의 SSOT 는 `references/conventions.md §1`.

## 라이선스

MIT
