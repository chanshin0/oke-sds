# sds-workflow 공통 Preamble

모든 `sds-*` 커맨드(`init` 제외)는 본문 Phase 실행 **전에** 다음 절차를 1회 수행한다. 이미 같은 세션 내에서 수행했다면 재사용 가능.

## 절차

1. **플러그인 기본값 로드**: Read `${CLAUDE_PLUGIN_ROOT}/workflow/config.defaults.yml`
2. **저장소 override 로드**: Read `.team-workflow/workflow.yml`
   - 파일 없음 → 중단: "이 저장소에서 sds 를 쓰려면 `/sds-workflow:init` 먼저 실행."
3. **deep-merge → 변수 추출**:
   - `PROJECT_KEY` ← `jira.project_key` (예: `CDS`)
   - `JIRA_BASE_URL` ← `jira.base_url`
   - `TRANSITIONS` ← `jira.transitions`
   - `PREFIX_MAP` ← `branch.prefix_map`
   - `VALIDATION_STATIC` ← `validation.static`
   - `UI_CHANGE_GLOBS` ← `validation.ui_change_globs`
   - `MR_TARGET_BRANCH` ← `mr.target_branch` (기본 `main`, 저장소별로 `dev` 등 override 가능)
   - `GITLAB_BASE_URL` ← `gitlab.base_url` (폴백 URL 생성에 사용, 미설정 시 `git remote get-url remote-sds` 에서 파싱)
   - `GITLAB_PROJECT_PATH` ← `gitlab.project_path` (예: `<your-group>/<your-project>`, 미설정 시 `remote-sds` URL 파싱)
   - `TEMPLATE_ROOT` = `${CLAUDE_PLUGIN_ROOT}/workflow/templates`
4. **이슈키 정규식**: `^${PROJECT_KEY}-\d+$`
5. 본문의 `CDS-XXXX` 표기는 `${PROJECT_KEY}-XXXX` 의 **예시**다. 실제 런타임에는 위에서 로드한 `PROJECT_KEY` 를 사용한다.

## 참조

- 이 파일 변경 시 → `CHANGELOG.md` 에 기록 (모든 커맨드 공통 영향)
- 변수 스키마 변경 시 → `references/artifact-types.md` 의 `workflow.yml` 엔트리도 함께 갱신
