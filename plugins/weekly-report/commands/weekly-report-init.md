---
description: 주간보고 자동화 초기 설정 — Atlassian API 토큰 keychain 등록, 이메일·페이지 ID 기록
argument-hint: ""
---

# /sds-workflow:weekly-report-init

**은유**: 비행 전 **연료 주입과 항법 좌표 입력**.

**목적**: `weekly-report-*` 커맨드를 처음 쓰기 전에 1회 실행. 사용자별 Atlassian API 토큰을 macOS keychain 에 안전 저장하고, 저장소 `workflow.yml` 에 주간보고 페이지 부모/템플릿 ID 를 기록한다.

이 커맨드는 토큰 값을 메시지에 노출하지 않도록 사용자가 **별도 터미널**에서 직접 keychain 등록 명령을 실행하게 안내한다.

---

## Phase 0: 선행 점검

- macOS 환경 확인 (`uname` → `Darwin`). 다른 OS 면 중단: "현재 macOS keychain 기반 토큰 저장만 지원."
- `git rev-parse --show-toplevel` 성공 여부.
- `.team-workflow/workflow.yml` 존재 여부. 없으면 중단: "`/sds-workflow:init` 먼저 실행."

## Phase 0.5: Confluence 좌표 수집 (workflow.yml 에 없으면)

`.team-workflow/workflow.yml` 을 읽어 `confluence.base_url` / `confluence.space_key` 존재 여부 확인.

**케이스 A — 둘 다 채워져 있음**: 스킵, 정보성 한 줄 출력:
> "✓ confluence.base_url=`<existing>`, space_key=`<existing>` (workflow.yml 에서 읽음)"

**케이스 B — `confluence:` 섹션 자체가 없음** (sds-workflow:init 직후 상태): **AskUserQuestion** 으로 묻고, 응답값으로 `confluence:` 블록을 새로 만들어 `workflow.yml` **`federation:` 라인 바로 위에 삽입** (Edit 툴 — `federation:` 을 anchor 로 그 앞에 블록 + 빈 줄 prepend).

**케이스 C — `confluence:` 섹션은 있는데 base_url/space_key 가 빈 값**: 동일하게 묻되 Edit 으로 빈 값 자리만 치환.

질문 (B/C 공통):

**Q. `confluence.base_url`** — Confluence site URL
- ◉ `https://okestro.atlassian.net/wiki` (팀 기본)
- Other (직접 입력)

**Q. `confluence.space_key`** — Confluence space key
- ◉ `PS7` (팀 기본)
- Other (직접 입력)

삽입 결과 (케이스 B):
```yaml
gitlab:
  ...

confluence:
  base_url: "<응답값>"
  space_key: "<응답값>"

federation:
  ...
```

멱등성: 두 번째 실행 시 케이스 A 로 분기되어 no-op.

## Phase 1: Atlassian 이메일 결정

다음 우선순위로 사용자의 Atlassian Cloud 이메일을 결정한다:
1. `git config sds.atlassian.email`
2. `git config user.email` (Atlassian 가입 이메일과 같은지 사용자 확인)

`AskUserQuestion` 으로:
- 위 후보를 보여주고 "이 이메일이 Atlassian 계정과 일치하는가?" 확인
- 다르면 사용자가 직접 입력

확정값을 다음 명령으로 기록 (저장소 로컬 git config):
```bash
git config sds.atlassian.email "<EMAIL>"
```

## Phase 2: API 토큰 keychain 등록 안내

사용자에게 다음 절차를 메시지로 안내하고 완료 신호를 기다린다 — Claude 가 토큰 값을 받지 않는다.

1. https://id.atlassian.com/manage-profile/security/api-tokens 접속 → **Create API token (without scopes)** 또는 scope 선택 시 Confluence/Jira 모두 read+write.
2. **별도 터미널 창**에서 다음 명령 직접 실행 (입력값 화면에 안 찍힘):
   ```bash
   read -s TOKEN && security add-generic-password \
     -a "<EMAIL>" -s "atlassian-api-token" -w "$TOKEN" -U && unset TOKEN
   ```

사용자가 "완료" 신호하면 Phase 3 으로 진행.

## Phase 3: 토큰 검증

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/weekly_report_lib_check.py --site "<JIRA_BASE_URL_HOST>" --email "<EMAIL>"
```
(JIRA_BASE_URL_HOST 는 `confluence.base_url` / `jira.base_url` 에서 host 만 추출 — 둘은 동일 site.)

성공 출력 예: `OK accountId=... display='홍길동'`. 실패 시 사용자에게 토큰 재발급 안내.

## Phase 4: 주간보고 페이지 ID 수집

`AskUserQuestion`:

| 키 | 질문 | 비고 |
|---|---|---|
| `weekly_report.root_id` | 주간보고 페이지들이 속한 **부모 페이지 ID** | 부모 페이지 URL 의 마지막 숫자. 예: `2950693214` |
| `weekly_report.template_source_id` | 신규 주차 페이지 생성 시 **참고할 가장 최근 주차 페이지 ID** | 비우면 `weekly-report-create` 가 매번 묻거나 부모 자식 중 최신 자동 선택 (v2) |

## Phase 5: workflow.yml 갱신

Phase 0.5 에서 만든(또는 보존한) `confluence:` 블록 아래 `weekly_report:` 키 추가/갱신:

```yaml
confluence:
  base_url: "..."        # Phase 0.5
  space_key: "..."       # Phase 0.5
  weekly_report:
    root_id: "<ROOT_ID>"
    template_source_id: "<SOURCE_ID>"  # optional
```

기존 `confluence:` 블록을 보존하면서 `weekly_report:` 만 병합한다 (Edit, 멱등).

## Phase 6: 완료 보고

성공 메시지에 다음 안내 포함:
- 본인 행만 갱신: `/sds-workflow:weekly-report-update-mine`
- 다음 주차 페이지 생성: `/sds-workflow:weekly-report-create`
- (관리자 권한자만) 전체 갱신: `/sds-workflow:weekly-report-update-all`
