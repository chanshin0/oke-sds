# sds-workflow 공통 Preamble

모든 `sds-*` 커맨드(`init` 제외)는 본문 Phase 실행 **전에** 다음 절차를 1회 수행한다. 이미 같은 세션 내에서 수행했다면 재사용 가능.

## 절차

1. **플러그인 기본값 로드**: Read `${CLAUDE_PLUGIN_ROOT}/workflow/config.defaults.yml`
2. **저장소 override 로드**: Read `.team-workflow/workflow.yml`
   - 파일 없음 → 중단: "이 저장소에서 sds 를 쓰려면 `/sds-workflow:init` 먼저 실행."
3. **deep-merge → 변수 추출**:
   - `PROJECT_KEYS` ← `jira.project_keys` (array, 예: `["CDS", "PROJ"]` 또는 `["*"]`)
     - 옛 schema (`jira.project_key`, 단수 string) 도 1회 호환: `[project_key]` 로 변환
   - `JIRA_BASE_URL` ← `jira.base_url`
   - `TRANSITIONS` ← `jira.transitions`
   - `PREFIX_MAP` ← `branch.prefix_map`
   - `VALIDATION_STATIC` ← `validation.static`
   - `UI_CHANGE_GLOBS` ← `validation.ui_change_globs`
   - `MR_TARGET_BRANCH` ← `mr.target_branch` (기본 `main`, 저장소별로 `dev` 등 override 가능)
   - `GITLAB_BASE_URL` ← `gitlab.base_url` (폴백 URL 생성에 사용, 미설정 시 `git remote get-url remote-sds` 에서 파싱)
   - `GITLAB_PROJECT_PATH` ← `gitlab.project_path` (예: `<your-group>/<your-project>`, 미설정 시 `remote-sds` URL 파싱)
   - `TEMPLATE_ROOT` = `${CLAUDE_PLUGIN_ROOT}/workflow/templates`

4. **이슈키 정규식 생성**:
   - `PROJECT_KEYS` 가 비어있거나 `["*"]` → 느슨 검증: `^[A-Z][A-Z0-9]+-\d+$` (모든 uppercase prefix 허용)
   - 그 외 array → 엄격 검증: `^(KEY1|KEY2|...)-\d+$`

5. **세션 PROJECT_KEY 결정 + 자동 등록 분기**:

   - 커맨드가 issue_key 인자 (예: `PROJ-123`) 를 받음:
     1. prefix 추출 → 후보 `SESSION_PROJECT_KEY = "PROJ"`
     2. PROJECT_KEYS 검증:
        - `PROJECT_KEYS == ["*"]` 또는 비어있음 → 통과 (느슨 모드, silent)
        - `prefix in PROJECT_KEYS` → 통과
        - **prefix 미포함 시 분기**:

          | 호출 컨텍스트 | 동작 |
          |---|---|
          | **autopilot** (`/sds-workflow:autopilot`) | **즉시 중단** — `AskUserQuestion` 없이 명시적 fail. 메시지: "프로젝트 키 `{prefix}` 가 project_keys 에 없습니다. 자율 운행 안전 차원에서 중단. workflow.yml 수동 갱신 후 재실행." |
          | **그 외** (pick / ship / land / recap / draft) | **AskUserQuestion** 으로 사용자 결정: |

          AskUserQuestion (autopilot 외):
          > "프로젝트 키 `{prefix}` 가 `.team-workflow/workflow.yml` 의 `jira.project_keys` 에 없습니다. 어떻게 처리할까요?"
          >
          > 옵션:
          > - **(a) workflow.yml 에 추가** — Edit 툴로 `project_keys` array 에 `{prefix}` 추가 (다른 항목 보존) + 진행
          > - **(b) 이 세션만 일회성 허용** — workflow.yml 수정 안 하고 SESSION_PROJECT_KEY 만 적용
          > - **(c) 중단** — 커맨드 종료

          (a) 선택 시 Edit 절차:
          ```
          Edit .team-workflow/workflow.yml:
            old: project_keys: ["CDS"]
            new: project_keys: ["CDS", "FOO"]
          ```
          wildcard 인 경우 변경 없음 (이미 모두 허용).

   - 인자 없는 커맨드 (예: `/where`) 는 PROJECT_KEYS[0] 을 default 로 사용 (와일드카드면 미정).
   - 모든 후속 변수 치환 (`${PROJECT_KEY}`) 은 SESSION_PROJECT_KEY 로 해석.

   **autopilot 분기 이유**: 자율 운행 중 silent 로 workflow.yml 변경하면 사용자 의도와 다를 수 있고, 다중 모드에서 race condition. 명시적 fail 이 안전.

6. 본문의 `PROJ-XXXX` 표기는 `${PROJECT_KEY}-XXXX` 의 **예시**. 실제 런타임에는 위에서 결정된 SESSION_PROJECT_KEY 를 사용한다.

## 코드 상수 (workflow.yml override 불가)

다음 값들은 plugin 코드에 박혀있어 저장소별 override 불가:

| 상수 | 값 |
|---|---|
| commit message format | `{type}: {issue_key} {subject}` |
| MR title format | `{type}: {issue_key} {subject}` |
| branch slug max words | `5` |
| branch slug separator | `-` |
| plan escape hatch label | `Trivial fix — no plan needed` |

## 참조

- 이 파일 변경 시 → 모든 커맨드 공통 영향이라 신중하게.
- 변수 스키마 변경 시 → `references/artifact-types.md` 의 `workflow.yml` 엔트리도 함께 갱신
