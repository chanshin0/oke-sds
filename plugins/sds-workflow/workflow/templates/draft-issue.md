<!--
  /draft 가 Jira 이슈 description 초안 작성 시 사용하는 템플릿.
  5개 섹션 고정 — 순서·헤더 변경 금지 (팀 전역 일관성).
  플레이스홀더는 자유 프롬프트 + 병렬 수집 결과에서 자동 주입.

  ⚠️ 이 마크다운은 사용자 미리보기 + 논리적 구조 정의용이다.
  Jira Cloud 의 description 필드는 ADF (Atlassian Document Format) JSON 만 렌더링하므로
  실제 등록은 `commands/draft.md` Phase 5 의 ADF 변환 매핑 표대로
  본 템플릿 각 섹션을 ADF 노드로 변환해 `acli jira workitem create --from-json` 으로 제출한다.
  마크다운을 그대로 description-file 로 넘기면 plain text 로 노출되어 구조가 사라진다.
-->

## 배경

{background — 발견 경위·맥락 2-4줄}

## 재현

{reproduction — 가능하면 단계별. 재현 불가면 "재현 불가 — 관찰 사례만" 명시}
1.
2.
3.

**관찰된 동작**: {observed}
**기대 동작**: {expected}

## 영향 범위

{impact — 영향 받을 파일·컴포넌트·사용자 시나리오}
- 파일 후보: {file_candidates}
- 관련 과거 이슈: {related_past_issues}

## 불확실성 / 가정

{uncertainties — 에이전트가 판단 불가해 사람에게 확인 필요한 지점}

## 우선순위 제안

- 제안 우선순위: {suggested_priority}
- 제안 타입: {suggested_type}
- 사유: {priority_reasoning}

---

🤖 작성: sds-workflow `/draft` (plugin v{PLUGIN_VERSION}) · 요청자: {USER} · 에이전트: {AGENT} · 작성 일시: {TIMESTAMP}
