---
description: 저장소 부팅 — `.team-workflow/` 스캐폴드 생성 + project_key 등 초기값 기록
argument-hint: "[--force]"
---

# /init

**은유**: 새 저장소에 **비행 계획 템플릿**을 펼친다.

**목적**: `sds-workflow` 플러그인을 새 저장소에서 처음 쓸 때 1회 실행. 저장소에 `.team-workflow/` 스캐폴드(workflow.yml, CONVENTIONS, tune-log) 를 생성하고 project_key·base_url 등 저장소별 값을 기록한다.

인자: `--force` 플래그가 있으면 기존 `.team-workflow/workflow.yml` 도 덮어쓴다.

---

## Phase 1: 선행 확인 (순차)

1. **git repo 루트 검증**
   ```bash
   git rev-parse --show-toplevel
   ```
   실패 시 중단: "git 저장소 루트에서 실행해야 한다."

2. **중복 실행 방지**
   - `.team-workflow/workflow.yml` 존재 여부 확인.
   - 존재하고 `--force` 없으면 중단: "이미 /init 이 완료된 저장소다. 재실행하려면 `/init --force`."

3. **플러그인 root 확인**
   - 환경변수 `CLAUDE_PLUGIN_ROOT` 가 비어있으면 중단: "플러그인이 설치되지 않았다. `/plugin install sds-workflow` 먼저 실행."

## Phase 2: 대화형 초기값 수집 (AskUserQuestion)

다음 항목을 한 번에 물어본다. (기본값은 Okestro 환경 가정)

| 키 | 질문 | 기본값 |
|---|---|---|
| project_key | 이 저장소가 다루는 Jira 프로젝트 키 (예: CDS, PROJ) | (없음, 필수) |
| jira.base_url | Atlassian site URL | `https://okestro.atlassian.net` |
| gitlab.base_url | GitLab site URL (MR 생성 대상. 비우면 `remote-sds` URL 에서 파싱; Phase 4.5 가 이 값으로 `remote-sds` 를 등록하므로 가능한 채우기 권장) | 빈 값 |
| gitlab.project_path | GitLab 프로젝트 경로 `OWNER/REPO` (다중 remote 환경 시 필수 — glab 이 엉뚱한 프로젝트 선택 방지) | 빈 값 |
| confluence.base_url | Confluence site URL | `https://okestro.atlassian.net/wiki` |
| confluence.space_key | Confluence space key (선택, 비우면 `--confluence` 미사용) | 빈 값 |

project_key 는 대문자·숫자·하이픈만 허용 (정규식 `^[A-Z][A-Z0-9]+$`). 위반 시 재질문.

## Phase 3: 씨앗 복사 (Bash, 병렬 안전)

```bash
mkdir -p .team-workflow
cp -n "${CLAUDE_PLUGIN_ROOT}/workflow/seeds/workflow.yml"       .team-workflow/workflow.yml
cp -n "${CLAUDE_PLUGIN_ROOT}/workflow/seeds/CONVENTIONS.md"     .team-workflow/CONVENTIONS.md
cp -n "${CLAUDE_PLUGIN_ROOT}/workflow/seeds/tune-log.md"        .team-workflow/tune-log.md
```

`--force` 시 `cp -n` → `cp -f`.

## Phase 4: workflow.yml 치환

Phase 2 에서 수집한 값으로 `.team-workflow/workflow.yml` 의 플레이스홀더를 치환한다 (Edit 툴).

- `{{PROJECT_KEY}}` → 수집값
- `{{JIRA_BASE_URL}}` → 수집값
- `{{GITLAB_BASE_URL}}` → 수집값 (빈 값이면 빈 문자열)
- `{{GITLAB_PROJECT_PATH}}` → 수집값 (빈 값이면 빈 문자열)
- `{{CONFLUENCE_BASE_URL}}` → 수집값
- `{{CONFLUENCE_SPACE_KEY}}` → 수집값 (빈 값이면 빈 문자열)

## Phase 4.5: `remote-sds` git remote 자동 등록 (스크립트 위임)

`/ship`·`/recap`·`/where` 가 팀 공용 고정 remote 이름 `remote-sds` 에 의존한다. 사용자마다 `origin` 이 다른 프로젝트를 가리키는 문제를 피하기 위함. 등록 로직은 `${CLAUDE_PLUGIN_ROOT}/scripts/ensure-remote-sds.sh` 에 캡슐화.

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/ensure-remote-sds.sh" \
  "${GITLAB_BASE_URL}" "${GITLAB_PROJECT_PATH}"
```

**Exit code 분기**:
- **0** — 등록 완료 (신규 등록 또는 기존 URL 일치). 통과.
- **10** — 기존 `remote-sds` 가 다른 URL 을 가리킴. `AskUserQuestion`:
  > "`remote-sds` 가 다른 URL 을 가리킵니다. (stderr 로 `existing=...` `expected=...` 출력됨). (a) `git remote set-url remote-sds "$EXPECTED_URL"` 로 교체 / (b) 기존 유지 (ship 단계에서 의도 다른 프로젝트 push 가능성 경고) / (c) 중단"
- **20** — 치명적 실패 (`GITLAB_BASE_URL`/`GITLAB_PROJECT_PATH` 비어있음 또는 git add 실패). Phase 전체 스킵하고 경고 출력 ("gitlab 값 미설정 — ship 시 자동 감지 불가").

## Phase 5: .gitignore 패치

`.gitignore` 에 `.work/` 라인이 없으면 append. 이미 있으면 스킵.

```bash
grep -q '^\.work/' .gitignore 2>/dev/null || printf '\n# sds-workflow\n.work/\n' >> .gitignore
```

## Phase 6: Handoff

```
┌─────────────────────────────────────────────────┐
│ /init 완료                                  │
│ 저장소: {repo}                                   │
│ project_key: {PROJECT_KEY}                       │
│                                                  │
│ 다음 단계 (팀이 1회):                             │
│  1) .team-workflow/CONVENTIONS.md 의 비타협      │
│     규칙을 저장소 현황에 맞게 정리                │
│  2) git remote -v 로 remote-sds 등록 확인         │
│     (Phase 4.5 에서 자동 등록됐어야 함)            │
│                                                  │
│ 이후:                                            │
│  /pick {PROJECT_KEY}-XXXX 로 첫 이슈 착수   │
└─────────────────────────────────────────────────┘
```

---

## 설계 메모

- `/init` 자체는 Claude Code 플러그인 `${CLAUDE_PLUGIN_ROOT}` 환경변수에 의존한다. 플러그인 미설치 상태에서 복사해 쓰면 동작하지 않는다.
- seed 파일은 항상 플러그인 버전에서 가져온다. 저장소 구조가 달라도 seed 는 최신을 반영.
- `workflow.yml` 의 `federation.contract_surface` 는 저장소별로 다르므로 seed 는 빈 배열. 팀이 필요 시 수기로 채움.
