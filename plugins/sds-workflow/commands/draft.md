---
description: 신규 Jira 이슈 초안 — 자유 프롬프트 → 5섹션 구조화 + 중복 탐지
argument-hint: "\"자유 프롬프트\""
entry-mode: interactive
required-permission: default
---


## Preamble

> 본문 실행 전 `${CLAUDE_PLUGIN_ROOT}/workflow/preamble.md` 를 Read 하여 공통 설정 로드 절차를 수행한다. 이 절차에서 추출한 `PROJECT_KEY`·`JIRA_BASE_URL`·`TEMPLATE_ROOT` 등 변수를 이하 Phase 에서 사용한다.

# /draft

**은유**: 관찰 사항을 **설계도 초안**으로 변환. 본인이 발견한 버그·개선을 Jira 에 등록할 때만 사용 (선택). PM 기획 이슈는 기존대로 수기 등록.

**목적**: 개발자 본인이 관찰한 이슈를 `draft-issue.md` 5섹션 구조로 description 초안화하고, 타입·우선순위·assignee 그레이존을 수면화해 `acli jira workitem create` 로 등록.

인자 `$ARGUMENTS`:
- 자유 형식 설명 (필수). 예: `/draft "이미지 레이어링 유효성 검사가 조건별로 다르게 동작함"`

---

## Phase 0: 사전 점검

- `command -v acli` — acli 설치 확인. 등록(Phase 5) 과 중복 탐지(Phase 2) 에 사용.
  - 미설치 → 경고만 (초안 작성·그레이존 질문은 진행). Phase 2 `acli jira workitem search` 는 스킵 → 중복 탐지 결과 없음 표기. Phase 5 `acli jira workitem create` 는 초안을 `.work/drafts/{timestamp}.md` 로 저장하고 수동 등록 안내.
  - 미인증 (`acli jira auth status` 실패) → 동일 취급.

## Phase 1: 입력 수신 + 키워드 파싱 (순차)

1. `$ARGUMENTS` 전체를 자유 프롬프트로 수신. 빈 값 → 중단, "설명 필수" 안내.
2. 프롬프트에서 기술적 키워드 추출 (명사구 위주). 예: "이미지 레이어링", "유효성 검사".
3. 키워드 2-3개를 Phase 2 병렬 수집 입력으로 사용.

## Phase 2: 병렬 컨텍스트 수집 (단일 메시지 병렬 호출)

**반드시 단일 메시지 내 병렬 실행**:

- `acli jira workitem search --jql 'project = CDS AND text ~ "{keyword1} OR {keyword2}" ORDER BY created DESC' --json` (Bash) — 최근 20건. **중복/유사 이슈 탐지**. acli 미가용 시 이 단계 스킵.
- Grep — 프로젝트 소스에서 키워드 매칭 파일 후보
- Glob — 관련 경로 패턴 (`src/views/**`, `src/composables/**`)
- `git log --grep "{keyword}" --oneline -15` (Bash) — 관련 과거 커밋

결과 수집 후 Phase 3 진입.

## Phase 3: description 초안 작성 (순차)

`${CLAUDE_PLUGIN_ROOT}/workflow/templates/draft-issue.md` 로드 후 치환:

| 플레이스홀더 | 소스 |
|------------|------|
| `{background}` | 자유 프롬프트 + 관련 과거 커밋에서 맥락 추론 |
| `{reproduction}` | 자유 프롬프트에서 재현 단계 추출. 불명확하면 "재현 불가 — 관찰 사례만" |
| `{observed}`, `{expected}` | 자유 프롬프트에서 추출 |
| `{impact}` | Grep/Glob 결과에서 영향 파일 후보 |
| `{file_candidates}` | 상위 5-10개 |
| `{related_past_issues}` | Jira 검색 결과 중 유사 이슈 2-3개 (key + 제목) |
| `{uncertainties}` | 에이전트가 판단 불가한 지점 |
| `{suggested_priority}` | 키워드 + 영향 범위 크기에서 휴리스틱 (Critical/High/Medium/Low) |
| `{suggested_type}` | 프롬프트 톤에서 추론 (Bug / Improvement / Task) |
| `{priority_reasoning}` | 근거 1-2줄 |
| `{PLUGIN_VERSION}` | `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` 의 `version` 필드 |
| `{USER}` | `git config user.name` |
| `{AGENT}` | 현재 세션의 Claude 모델명 (예: `Claude Opus 4.7`). 알 수 없으면 `Claude` |
| `{TIMESTAMP}` | `date '+%Y-%m-%d %H:%M %Z'` 출력 |

**Authorship footer**: 템플릿 마지막 블록(`---` 구분선 + 1줄 메타)은 항상 채워서 description 에 포함한다. 비-AI 손수정 이슈와 시각적으로 구분되는 신호 역할이며, ADF 변환 시 horizontal rule + paragraph 노드 한 쌍으로 매핑된다 (Phase 5 ADF 매핑 표 참조).

### Phase 3-1. 중복 탐지 경고

Phase 2 Jira 검색 결과에 **제목 유사도 70% 이상** 또는 **동일 파일 범위** 이슈가 있으면:

```
⚠️ 유사 이슈 발견:
  - {CDS-XXXX}: {제목}  (상태: {status})
  - {CDS-YYYY}: {제목}  (상태: {status})

(a) 신규 등록 진행  (b) 기존 이슈에 코멘트 추가 제안  (c) 중단
```

`AskUserQuestion` 으로 수면화. (b) 선택 시 기존 이슈 키만 출력하고 중단 — 이 커맨드는 코멘트 추가까지 책임지지 않음.

## Phase 4: 그레이존 질문 수면화 (AskUserQuestion)

아래 항목은 에이전트가 자신있게 판정 불가 → 사람에게 질문:

- **이슈 타입**: Bug / Task / Story / Improvement / Documentation (기본 제안값은 Phase 3 에서 추론)
- **우선순위**: Critical / High / Medium / Low (기본 제안값 포함)
- **Assignee**: 본인 / 다른 담당자 / 미정 (미정 시 Jira assignee 공란)
- **재현 세부**: 단계가 불완전한 경우만 추가 질문

답변 반영 후 description 초안 갱신.

## Phase 5: 최종 미리보기 + 등록 (순차)

1. 최종 이슈 메타 표시:
   - 제목: 프롬프트에서 1줄 파생 (예: "[Bug] 이미지 레이어링 유효성 검사 조건별 불일치")
   - 타입 / 우선순위 / assignee
   - description 초안 전문 (사용자 가독성용으로 마크다운 렌더링)
2. **사용자 승인** — 수정 요청 루프.
3. 승인 시 description 을 **ADF (Atlassian Document Format) JSON 으로 변환**한 뒤 임시 JSON 파일을 빌드하고 `acli jira workitem create --from-json <tmp.json>` (Bash) 호출.
   - **이유**: Jira Cloud 의 description 필드는 ADF 만 렌더링됨. 마크다운/wiki markup 은 plain text 로 그대로 노출되어 헤더·리스트·굵게가 적용되지 않음. `--description-file` 에 마크다운을 넘기면 줄바꿈만 보존되고 구조가 사라짐.
   - **JSON 스키마 확인**: 최초 1회 `acli jira workitem create --generate-json` 으로 필드 확인. 최소 키: `projectKey`, `type`, `summary`, `assignee`, `description` (ADF doc).
   - **type 값**: 프로젝트 허용 enum 의 **원어** 사용. acli 가 영문 미인식 시 에러 메시지에 enum 노출 (예: `작업, 하위 작업, 스토리, 버그, 에픽`) — 그대로 사용. 한글 enum 이면 한글 그대로 JSON 에 박는다.
   - **assignee 값**: 이메일 또는 accountId. `@me` 는 프로젝트 권한·할당 가능 사용자 정책에 따라 거절될 수 있어 폴백으로 Preamble 변수 또는 `acli jira auth status` 출력의 Email 을 사용.
   - **우선순위**: 현재 acli `--from-json` 스키마에 priority 필드 없음. 생성 후 `acli jira workitem update --priority <name>` 로 별도 호출하거나 Jira UI 에서 수동 조정. Handoff 에 "우선순위: {suggested} (UI 또는 update 호출 필요)" 명시.
   - **ADF 변환 매핑** (`draft-issue.md` 5섹션 + footer → ADF 노드):
     - `## 헤더` → `{"type":"heading","attrs":{"level":2},"content":[{"type":"text","text":"..."}]}`
     - 단락 → `{"type":"paragraph","content":[{"type":"text","text":"..."}]}`
     - **굵게** → `{"type":"text","text":"...","marks":[{"type":"strong"}]}`
     - `인라인 코드` → `{"type":"text","text":"...","marks":[{"type":"code"}]}`
     - `1. 2. 3.` 번호 리스트 → `{"type":"orderedList","content":[{"type":"listItem","content":[{"type":"paragraph",...}]}, ...]}`
     - `-` 글머리 리스트 → `{"type":"bulletList","content":[...]}`
     - `---` 수평선 → `{"type":"rule"}`
     - footer 라인 (이모지 + 메타) → `{"type":"paragraph","content":[{"type":"text","text":"...","marks":[{"type":"em"}]}]}` (전체 italic 처리)
     - 루트는 `{"type":"doc","version":1,"content":[...]}`
   - acli 미가용 → ADF JSON 을 `.work/drafts/{timestamp}.json` 으로, 마크다운 미리보기를 `.work/drafts/{timestamp}.md` 로 저장하고 수동 등록 안내. Handoff 는 "수동 등록 필요" 로 마감.
4. 성공 시 생성된 이슈 키를 Handoff 에 출력. 우선순위가 기본값으로 들어간 경우 Handoff 에 조정 안내 명시.

## Phase 6: Handoff

```
┌──────────────────────────────────────────────┐
│ 이슈 생성 완료: {new_issue_key}                │
│   제목: {title}                                │
│   타입/우선순위: {type} / {priority}           │
│   Assignee: {assignee or "미정"}               │
│                                               │
│ 다음: 작업 착수 → /pick {new_issue_key}   │
│       (이슈만 등록하고 나중에 작업)             │
└──────────────────────────────────────────────┘
```

---

## 실패/예외 처리

- 빈 프롬프트 → 중단
- acli 미설치/미인증 → Phase 0 에서 감지, Phase 2 중복 탐지 스킵 + Phase 5 자동 폴백 (초안 파일 저장)
- Jira 검색 실패 (acli exit ≠ 0) → 중복 탐지 스킵, 경고 표시 후 계속
- `acli jira workitem create` 실패 (권한·플래그 오류 등) → ADF JSON 을 `.work/drafts/{timestamp}.json` 로, 마크다운 미리보기를 `.work/drafts/{timestamp}.md` 로 함께 저장하고 수동 등록 안내
- type 미인식 에러 (`Please provide valid issue type . Allowed issue types for project are : ...`) → 에러 메시지의 enum 그대로 JSON `type` 필드 치환 후 재시도
- assignee 거절 (`사용자는 이슈를 할당받을 수 없습니다`) → `@me` 였다면 이메일로 폴백 후 재시도

## 원칙

- **중복 탐지 먼저** — 유사 이슈 존재 시 신규 등록을 기본 선택지로 두지 않음
- **그레이존은 무조건 사람에게** — 타입·우선순위·assignee 는 기본값 제안만 하고 확정은 사람
- **description 5섹션 구조 고정** — 팀 전역 일관성. 섹션 변경은 `/tune` 을 통해서만
- **Authorship footer 항상 포함** — `/draft` 로 생성된 이슈는 description 마지막에 작성 메타(에이전트·플러그인 버전·요청자·시각)를 자동 첨부한다. 손수정 이슈와 구분되는 시각 신호이며, 별도 라벨/필드는 두지 않는다.
- 이 커맨드는 **선택 사용**. PM 기획 이슈는 이 커맨드 불필요
