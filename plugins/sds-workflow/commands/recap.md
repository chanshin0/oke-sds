---
description: land 완료 후 결과 및 조치 내용 초안 — Jira 결과 코멘트, 선택적 Confluence 페이지
argument-hint: "CDS-XXXX [--confluence]"
---


## Preamble

> 본문 실행 전 `${CLAUDE_PLUGIN_ROOT}/workflow/preamble.md` 를 Read 하여 공통 설정 로드 절차를 수행한다. 이 절차에서 추출한 `PROJECT_KEY`·`JIRA_BASE_URL`·`TEMPLATE_ROOT` 등 변수를 이하 Phase 에서 사용한다.

# /recap

**은유**: 착륙 후의 **비행 보고서**. 이번 비행에서 무엇을 해냈는지, 다음 편에서 관찰할 것은 무엇인지 정리한다.

**목적**: `/land` 가 착륙(RESOLVE·git 정리)만 수행하고, 결과 보고는 이 커맨드가 전담. 기본은 Jira 결과 코멘트 초안. `--confluence` 플래그 시 Confluence 페이지 초안까지.

인자 `$ARGUMENTS`:
- `CDS-XXXX` (필수) — 이슈 키
- `--confluence` — Confluence 페이지 초안까지 작성 (선택)

---

## Phase 0: 사전 점검

- `command -v acli` — acli 설치 확인. Phase 4 Jira 코멘트 post 에 사용.
  - 미설치 → 경고만 (초안 작성은 진행). Phase 4 에서 코멘트를 `.work/{issue_key}-recap-comment.md` 로 저장하고 수동 post 안내.
  - 미인증 (`acli jira auth status` 실패) → 동일 취급.

## Phase 1: 컨텍스트 로드 (순차)

1. **이슈 키 파싱** — `$ARGUMENTS` 에서 `CDS-XXXX` 추출. 형식 불일치 시 중단.
2. **`.work/{issue_key}.md` 읽기** — 아래 섹션 추출:
   - `## Jira` — 제목, 담당자
   - `## 플랜 (by /pick)` — 목표, 구현 접근, 검증 방법
   - `## 검증 결과 (by /ship)` — 정적/브라우저
   - `## 검증 결과 > ### Deviation / Goal-backward` — 판단 근거
   - `## 머지 (by /land)` — MR URL
3. **머지 상태 확인** — 상태 블록이 `Merged` 인지. 아님 → 중단, "`/land {issue_key}` 선행 필요" 안내.
4. **Confluence 설정 로드** — `--confluence` 시만: Preamble 에서 로드한 merged config 의 `confluence.space_key` / `confluence.parent_id` 사용. 비어있으면 사용자에게 1회 입력 요청.

## Phase 2: Jira 결과 보고 코멘트 초안 (필수)

`${CLAUDE_PLUGIN_ROOT}/workflow/templates/recap-comment.md` 로드 후 플레이스홀더 치환:

| 플레이스홀더 | 소스 |
|------------|------|
| `{goal_one_liner}` | 플랜 "목표" 섹션 1줄 요약 |
| `{diff_summary_one_liner}` | 구현 접근 1줄 요약 |
| `{key_files}` | `.work/` 변경 파일 상위 3-5개 |
| `{static_result}` | 검증 결과 > 정적 |
| `{ui_gif_or_skip_reason}` | GIF 존재하면 "GIF 첨부", 스킵 시 사유 |
| `{ui_result}` | 브라우저 체크리스트 결과 |
| `{goal_backward_note}` | 검증 결과 > Deviation/Goal-backward |
| `{post_deploy_checks}` | 플랜 "검증 방법" + UI 체크리스트에서 2-3개 추출 |
| `{mr_url}` | MR URL |
| `{COMMAND}` | `recap` |
| `{AGENT}` | 현재 세션의 Claude 모델명 (예: `Claude Opus 4.7`). 알 수 없으면 `Claude` |
| `{PLUGIN_VERSION}` | `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` `version` |
| `{USER}` | `git config user.name` |

**불확실 지점 수면화** — 아래 경우 `AskUserQuestion`:
- 플랜 "목표" 가 비어있거나 추출 불가
- 배포 후 확인 포인트가 기계적으로 정할 수 없는 경우 (예: 특정 테넌트만 영향)

초안 완성 후 사용자에게 제시. 수정 요청 루프.

## Phase 3: Confluence 페이지 초안 (`--confluence` 시만)

`${CLAUDE_PLUGIN_ROOT}/workflow/templates/recap-page.md` 로드 후 플레이스홀더 치환:

| 플레이스홀더 | 소스 |
|------------|------|
| `{issue_key}`, `{issue_title}`, `{jira_url}`, `{assignee}`, `{resolved_date}` | Jira 메타 |
| `{background}` | Jira description 3-5줄 요약 |
| `{change_narrative}` | 플랜 목표 + 구현 접근 → 3-5문단 서술문 (사용자 관점) |
| `{changed_files_table}` | `git log remote-sds/${MR_TARGET_BRANCH}..merged_commit --stat` |
| `{gif_embed_or_skip}` | GIF 파일이 있으면 attachment 링크, 없으면 "UI 변경 없음" |
| `{goal_backward_note}` | `.work/{issue_key}.md` |
| `{post_deploy_checks}` | 플랜 검증 방법 |
| `{related_issues_or_comments}` | `git log --grep "CDS-"` 에서 동일 파일 범위 연관 이슈 |
| `{COMMAND}` | `recap --confluence` |
| `{AGENT}` | 현재 세션의 Claude 모델명 |
| `{PLUGIN_VERSION}` | plugin.json version |
| `{USER}` | `git config user.name` |

초안은 Phase 2 코멘트보다 훨씬 풍부한 서술. **에이전트가 자동 publish 하지 않음** — 초안만 작성 후 사람 리뷰 게이트.

## Phase 4: 사람 승인 → 게시 (단일 메시지 병렬)

### Phase 2 만 (기본)

사용자 승인 후:
- `acli jira workitem comment {issue_key} --body "<초안 본문>"` (Bash) 로 Jira 코멘트 post
  - acli 미가용 (Phase 0 판정) → 초안을 `.work/{issue_key}-recap-comment.md` 로 저장 + 수동 post 안내

### Phase 3 포함 (`--confluence`)

사용자 승인 후 병렬:
- `acli jira workitem comment {issue_key} --body "<초안 본문>"` (Bash)
  - acli 미가용 → 초안 파일 저장 + 수동 안내
- Confluence 페이지 publish — Atlassian MCP `confluence_create_page` 계열 가용 여부 확인. 없으면 Confluence REST API 직접 호출 또는 사용자에게 초안 파일 경로 안내 (`.work/{issue_key}-recap-page.md`) 후 수동 복사 요청. (Confluence 는 acli 대체 범위 밖 — Jira 만 acli 전면 대체, Confluence 는 MCP/REST 경로 유지)

**중요**: Confluence 자동 publish 가 지원되지 않는 환경이면 초안을 `.work/{issue_key}-recap-page.md` 로 저장하고 사용자에게 수동 publish 안내. 거짓 성공 금지.

## Phase 5: 상태 갱신 + Handoff

1. `.work/{issue_key}.md` 갱신:
   - 상태 블록 단계: `Merged` → `Recapped`
   - "완료 보고 (Recap)" 섹션에 Jira 코멘트 ID, (옵션) Confluence URL 기록
2. Handoff:

```
┌──────────────────────────────────────────────┐
│ 보고 완료: {issue_key}                         │
│   Jira 코멘트: posted                          │
│   Confluence: {published / skipped}           │
│                                               │
│ 다음 이슈 → /pick CDS-YYYY                 │
│ 또는 상태 확인 → /where                    │
└──────────────────────────────────────────────┘
```

---

## 실패/예외 처리

- `.work/{issue_key}.md` 미존재 → 중단, "`/pick` 선행 필요" 안내
- 상태가 `Merged` 아님 → 중단, `/land` 선행 안내
- acli 미설치/미인증 → Phase 0 에서 감지, Phase 4 자동 폴백 (초안 파일 저장 + 수동 안내)
- Jira 코멘트 post 실패 (acli exit ≠ 0) → 초안은 `.work/{issue_key}-recap-comment.md` 로 저장하고 수동 post 안내
- Confluence API 미지원 → Phase 3 초안만 파일로 저장, 수동 publish 안내 (거짓 성공 금지)
- `{goal_one_liner}` 등 필수 플레이스홀더 추출 실패 → `AskUserQuestion` 으로 수면화

## 원칙

- **자동 publish 금지** — Jira 는 사람 승인 후 post, Confluence 는 기본적으로 초안까지만.
- 템플릿 외 섹션 자의적 추가 금지 — 팀이 `recap-page.md` 를 고치는 것이 유일한 확장 경로.
- `--confluence` 플래그가 없으면 Confluence 관련 동작 전혀 하지 않음 (의도적 최소 부작용).
