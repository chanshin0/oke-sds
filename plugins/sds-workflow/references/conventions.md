# sds-workflow Conventions

플러그인 전반의 공통 계약. enum·포맷·표준 문구를 한 곳에 모아 커맨드·템플릿 간 일관성을 보장한다.

`/sds-tune` 과 각 커맨드는 이 파일을 **SSOT** 로 참조한다. 여기 정의된 값과 모순되는 커맨드 본문은 튠 대상.

---

## 1. 튠 카테고리 enum

`/sds-tune` Phase 1 피드백 분류에 사용.

| 카테고리 | 범위 | 소유자 | 대상 경로 |
|---|---|---|---|
| `command-behavior` | 특정 `sds-*` 커맨드 동작 | 플러그인 | `plugin/sds-workflow/commands/{name}.md` |
| `template` | plan/mr/recap/draft/work-context 템플릿 | 플러그인 | `plugin/sds-workflow/workflow/templates/*.md` |
| `config` | 공통 기본값 | 플러그인 | `plugin/sds-workflow/workflow/config.defaults.yml` |
| `config-local` | 저장소별 override | 저장소 | `.team-workflow/workflow.yml` |
| `design-principle` | 철학·확정 사항 | 플러그인 | `plugin/sds-workflow/SPEC.md` |
| `convention` | 이 파일의 enum/포맷/표준 | 플러그인 | `plugin/sds-workflow/references/conventions.md` |
| `registry` | artifact 타입 레지스트리 | 플러그인 | `plugin/sds-workflow/references/artifact-types.md` |

**sync-points**: 이 enum 변경 시
- `commands/tune.md` Phase 1 카테고리 리스트
- `workflow/seeds/tune-log.md` format 줄
- `.team-workflow/tune-log.md` format 줄 (저장소별)
- `CHANGELOG.md`

---

## 2. 튠 상태 enum

tune-log 엔트리 `상태:` 필드 값.

- `applied` — 수정 즉시 반영
- `deferred` — 대기 (나중에 `--review` 로 재검토)
- `needs-e2e` — E2E 영향 가능, 확인 후 적용 여부 결정
- `rejected` — 폐기 (이력만 남김)

---

## 3. tune-log 엔트리 포맷

```
## {YYYY-MM-DD} — {short-desc-kebab}

- 제출: {user}
- 피드백 원문: "{원문}"
- 카테고리: {카테고리 enum 값}
- 적용 대상: {file-path#section or 리스트}
- 상태: {상태 enum 값}
- 커밋: {sha-short | pending | -}
- 메모: {1-2줄}
```

---

## 4. Handoff 블록 포맷

모든 커맨드는 마지막 Phase 결과를 아래 박스 포맷으로 출력.

```
┌──────────────────────────────────────────────┐
│ {커맨드 요약}: {핵심 식별자}                    │
│   {키1}: {값1}                                │
│   {키2}: {값2}                                │
│                                               │
│ 다음 액션: {커맨드 제안 또는 -}                 │
└──────────────────────────────────────────────┘
```

- 박스 폭은 고정 안 함 (터미널 자동 래핑 의존).
- 내부 키-값은 공백 3칸 들여쓰기.
- "다음 액션" 줄은 빈 줄 1개 위에 배치.

---

## 5. acli 사전 점검 표준

acli 의존 Phase 를 가진 커맨드(pick/ship/land/recap/draft)는 공통 감지 절차 사용.

**감지**:
```bash
command -v acli            # 설치 확인
acli jira auth status      # 인증 확인 (설치됐을 때만)
```

**fallback 분기** (커맨드별로 다름):

| 커맨드 | 미설치/미인증 시 |
|---|---|
| `pick` | **중단** + 설치·인증 안내 (Jira 조회 불가로 Phase 1 불가) |
| `ship` | Phase 0 통과, Phase 5 Jira 코멘트 단계에서 스킵 + Handoff 에 "수동 필요" 표기 |
| `land` | Phase 2 Jira 전환 스킵, git 정리만 수행 + Handoff 에 "Jira RESOLVE: 수동 필요" 표기 |
| `recap` | 경고만 + Phase 4 에서 `.work/{issue_key}-recap-comment.md` 로 초안 저장 |
| `draft` | 경고만 + Phase 2 중복 탐지 스킵 + Phase 5 `.work/drafts/{timestamp}.md` 로 초안 저장 |

Preamble 완료 후 Phase 0 초반에 감지하고, 결과를 세션 변수로 보관해 뒤 Phase 들이 참조한다.

---

## 6. 브랜치 prefix 규약

`config.defaults.yml` `branch.prefix_map` 에서 Jira 이슈 타입 → 커밋/브랜치 prefix 매핑. 팀 `commitlint` type-enum 과 일치해야 하며, 저장소별로 다르면 `.team-workflow/workflow.yml` 에서 override.

기본 매핑은 `config.defaults.yml` 을 SSOT 로 보고, 이 문서에서는 **존재 자체** 만 규약화.

---

## 7. 커맨드 파일 구조 표준

모든 `commands/*.md` 는 다음 구조를 따른다:

```markdown
---
description: {/help 에 노출되는 1줄 요약 — 체언 종결}
argument-hint: "{인자 패턴}"
---

## Preamble

> 본문 실행 전 `${CLAUDE_PLUGIN_ROOT}/workflow/preamble.md` 를 Read 하여 공통 설정 로드 절차를 수행한다.

# /{command-name}

**은유**: {한 줄 메타포}

**목적**: {1-2문장}

인자 `$ARGUMENTS`: {파싱 규칙}

---

## Phase 0: {...}
## Phase 1: {...}
...
## Phase N: Handoff

(Handoff 블록 포맷은 §4 참조)
```

**예외**:
- `init.md` — Preamble 없음 (이 커맨드가 workflow.yml 을 생성하므로)

---

## 8. 파일 명명 규약

- **커맨드 파일**: `commands/{name}.md` (kebab-case, `.md`)
- **템플릿 파일**: `workflow/templates/{name}-template.md` 또는 `{name}.md` (일관성 우선 — 현재 혼재)
- **reference 파일**: `references/{name}.md`
- **seed 파일**: `workflow/seeds/{name}.{md,yml}` (원본 파일명과 동일)

---

## 9. 참조 표기 규약

- 플러그인 내부 절대 경로: `${CLAUDE_PLUGIN_ROOT}/...`
- 저장소 내부 절대 경로: `.team-workflow/...` 또는 `.work/...`
- 외부 `@path` 참조는 사용하지 않음 (Claude Code SlashCommand 는 `@` 문법 미지원 — 명시적 "Read" 지시만 사용)
