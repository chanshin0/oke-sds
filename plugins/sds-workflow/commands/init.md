---
description: 저장소 부팅 — `.team-workflow/` 스캐폴드 생성 + project_key 등 초기값 기록
argument-hint: "[--force]"
entry-mode: interactive
required-permission: accept-edits
---

# /init

**은유**: 새 저장소에 **비행 계획 템플릿**을 펼친다.

**목적**: `sds-workflow` 플러그인을 새 저장소에서 처음 쓸 때 1회 실행. 저장소에 `.team-workflow/` 스캐폴드(workflow.yml, CONVENTIONS, tune-log) 를 생성하고 project_key·base_url 등 저장소별 값을 기록한다.

인자: `--force` 플래그가 있으면 기존 `.team-workflow/workflow.yml` 도 덮어쓴다.

---

## Phase 0.5: Entry Switch (권한 모드 분기)

`/init` 은 `.team-workflow/` 가 없는 상태에서 실행되므로 공통 preamble 을 호출하지 않는다. 대신 preamble 의 Phase 0.5 (Entry Switch) **만** 인라인으로 수행한다.

- `${CLAUDE_PLUGIN_ROOT}/workflow/preamble.md` 의 **Phase 0.5** 섹션을 Read.
- 거기 정의된 절차 (CLI 감지 → 모드 probe → 3-way 분기) 를 본 커맨드의 frontmatter `entry-mode: interactive` 기준으로 적용.
- 결과:
  - `auto` (bypass / accept-edits) → 진행
  - `default` → N회 prompt 안내 후 진행
  - `plan` → **즉시 중단** (init 은 Edit/Write 가 핵심이라 plan 모드에선 불가)

분기 통과 후 Phase 1 으로.

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

## Phase 2.0: origin URL 자동 감지 (defaults 추출)

기존 clone 인 경우 `origin` URL 에서 GitLab base_url + project_path 를 미리 추출해 Phase 2 AskUserQuestion 의 기본값 후보로 사용한다. **추출 성공해도 질문은 항상 하고**, 사용자에게 추출값을 default 로 보여주기만 한다 (silent skip 금지 — `/init` 은 첫 단추라 모든 값이 명시적 confirm 을 받아야 함).

```bash
ORIGIN_URL=$(git remote get-url origin 2>/dev/null || true)
```

Parse 규칙 (모두 `<base_url>` + `<project_path>` 두 변수로 분해):

| ORIGIN_URL 형태 | base_url | project_path |
|---|---|---|
| `https://gitlab.example.com/group/sub/repo.git` | `https://gitlab.example.com` | `group/sub/repo` |
| `https://gitlab.example.com/group/repo` | `https://gitlab.example.com` | `group/repo` |
| `git@gitlab.example.com:group/repo.git` | `git@gitlab.example.com:` | `group/repo` |

`origin` 이 없거나 GitLab 패턴 미일치 → 두 변수 모두 빈 값 (사용자가 수동 입력).

이 추출값들을 `DEFAULT_GITLAB_BASE_URL`, `DEFAULT_GITLAB_PROJECT_PATH` 로 보관해 Phase 2 default 로 사용.

## Phase 2: 대화형 초기값 수집 (AskUserQuestion)

총 4문항. 각 질문은 **AskUserQuestion 다지선다 + Other(직접 입력)** 형태로 띄운다. 첫 옵션이 default(◉) 로 선택되어 있어 Enter 만 치면 통과.

> 참고: Confluence 관련 값(`confluence.base_url`, `confluence.space_key`) 은 `weekly-report` 플러그인 전용이라 여기서 안 묻는다. `/sds-workflow:weekly-report-init` 가 자체적으로 수집한다.

자동 감지 성공 시 정보성 한 줄 출력 (Q3/Q4 위):
> "✓ origin 에서 감지: base=`${DEFAULT_GITLAB_BASE_URL}`, path=`${DEFAULT_GITLAB_PROJECT_PATH}` (Q3/Q4 첫 옵션으로 추가)"

**Q1. `project_keys`** — 이 저장소가 다룰 Jira 프로젝트 키 목록
- ◉ 팀 기본 (CDS, CEPH)
- CDS 만
- CEPH 만
- 모두 허용 (`*`)
- Other (직접 입력 — 콤마 구분)

**Q2. `jira.base_url`** — Atlassian site URL
- ◉ `https://okestro.atlassian.net` (팀 기본)
- Other (직접 입력)

**Q3. `gitlab.base_url`** — GitLab base URL
- *(origin 감지 성공 시 맨 위에 추가)* ◉ `${DEFAULT_GITLAB_BASE_URL}` (origin 자동 감지)
- ◉ `http://gitlab.prd.console.trombone.okestro.cloud` (팀 기본) ※ origin 감지 실패 시 default
- Other (직접 입력)

**Q4. `gitlab.project_path`** — GitLab project path (`<group>/<project>`)
- *(origin 감지 성공 시 맨 위에 추가)* ◉ `${DEFAULT_GITLAB_PROJECT_PATH}` (origin 자동 감지)
- ◉ `SDS306/remote-ceph-admin` (팀 기본) ※ origin 감지 실패 시 default
- Other (직접 입력)

**검증**:
- `project_keys`: 콤마 split 후 각 토큰이 정규식 `^[A-Z][A-Z0-9]+$` 통과. `*` 또는 빈 값은 통과 (느슨 모드).
- `gitlab.base_url`: `^(https?://[^/]+|git@[^:]+:?)$` 패턴 권장 (위반 시 경고만)
- `gitlab.project_path`: 슬래시 1개 이상 포함 + 선두 슬래시·`.git` 접미 금지 (위반 시 재질문)

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

- `{{PROJECT_KEYS_JSON}}` → 수집값 array 의 JSON 표현
  - 콤마 split 결과 array 화: `"PROJ, FOO"` → `["PROJ", "FOO"]`
  - `*` 또는 빈 값 → `["*"]`
- `{{JIRA_BASE_URL}}` → 수집값
- `{{GITLAB_BASE_URL}}` → 수집값 또는 자동 감지값 (둘 다 빈 값이면 빈 문자열)
- `{{GITLAB_PROJECT_PATH}}` → 동일

## Phase 4.5: `remote-sds` git remote 자동 등록 (스크립트 위임)

`/ship`·`/where` 가 팀 공용 고정 remote 이름 `remote-sds` 에 의존한다. 사용자마다 `origin` 이 다른 프로젝트를 가리키는 문제를 피하기 위함. 등록 로직은 `${CLAUDE_PLUGIN_ROOT}/scripts/ensure-remote-sds.sh` 에 캡슐화.

**선결 조건**: `gitlab.base_url` + `gitlab.project_path` 둘 다 채워져 있어야 함. 둘 중 하나라도 비어있으면 Phase 4.5 스킵 + 경고:
> "gitlab 값 미설정 — `remote-sds` 자동 등록 스킵. ship 시 자동 감지 불가, 수동 등록 필요."

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/ensure-remote-sds.sh" \
  "${GITLAB_BASE_URL}" "${GITLAB_PROJECT_PATH}"
```

**Exit code 분기**:

- **0 — 등록 완료** (신규 등록 또는 기존 URL 일치). 통과.

- **10 — URL 불일치**: stderr 에 `existing=...` `expected=...` 출력됨. 즉시 **AskUserQuestion** 실행:

  > 질문: "`remote-sds` 가 다른 URL 을 가리킵니다.
  > - existing: {existing}
  > - expected: {expected}
  > 어떻게 처리할까요?"
  >
  > 옵션:
  > - **(a) 교체** — `git remote set-url remote-sds "$EXPECTED_URL"` 실행 + fetch
  > - **(b) 기존 유지** — ship 단계에서 의도와 다른 프로젝트로 push 위험 경고 (반복적으로 발생)
  > - **(c) 중단** — Phase 6 Handoff 도 건너뛰고 사용자가 수동 정리

  사용자 선택 → 즉시 실행. (a) 의 경우:
  ```bash
  git remote set-url remote-sds "${EXPECTED_URL}"
  git fetch remote-sds --quiet
  ```

- **20 — 치명적 실패** (`GITLAB_BASE_URL`/`GITLAB_PROJECT_PATH` 형식 위반 또는 git add 실패). stderr 메시지를 사용자에게 그대로 보여주고 Phase 4.5 스킵.

## Phase 5: .gitignore 패치

`.gitignore` 에 `.work/` 라인이 없으면 append. 이미 있으면 스킵.

```bash
grep -q '^\.work/' .gitignore 2>/dev/null || printf '\n# sds-workflow\n.work/\n' >> .gitignore
```

## Phase 6: Handoff

```
┌─────────────────────────────────────────────────┐
│ /init 완료                                       │
│ 저장소: {repo}                                    │
│ project_key: {PROJECT_KEY}                       │
│ remote-sds: {EXPECTED_URL or "미등록"}            │
│                                                  │
│ 다음 단계 (팀이 1회):                              │
│  1) .team-workflow/CONVENTIONS.md 의 비타협        │
│     규칙을 저장소 현황에 맞게 정리                  │
│  2) git remote -v 로 remote-sds 등록 확인          │
│                                                  │
│ 이후:                                              │
│  /pick {PROJECT_KEY}-XXXX 로 첫 이슈 착수          │
└─────────────────────────────────────────────────┘
```

---

## 설계 메모

- `/init` 자체는 Claude Code 플러그인 `${CLAUDE_PLUGIN_ROOT}` 환경변수에 의존한다. 플러그인 미설치 상태에서 복사해 쓰면 동작하지 않는다.
- seed 파일은 항상 플러그인 버전에서 가져온다. 저장소 구조가 달라도 seed 는 최신을 반영.
- `workflow.yml` 의 `federation.contract_surface` 는 저장소별로 다르므로 seed 는 빈 배열. 팀이 필요 시 수기로 채움.
- Phase 2.0 의 origin URL 파싱이 실패하면 Phase 2 가 빈 default 로 진행 → 사용자 수동 입력. 실패해도 init 은 계속 진행.
- Phase 4.5 의 exit 10 분기는 **AskUserQuestion 으로 즉시 결정** — 미해결 상태로 init 종료 금지 (이후 ship 에서 사고 위험).
