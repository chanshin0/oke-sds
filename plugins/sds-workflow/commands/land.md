---
description: MR 수동 머지 후 — Jira RESOLVE 전환
argument-hint: "CDS-XXXX"
---


## Preamble

> 본문 실행 전 `${CLAUDE_PLUGIN_ROOT}/workflow/preamble.md` 를 Read 하여 공통 설정 로드 절차를 수행한다. 이 절차에서 추출한 `PROJECT_KEY`·`TRANSITIONS` 등 변수를 이하 Phase 에서 사용한다.

# /land

**은유**: 리뷰어가 활주로를 열어주면(머지) 비행기(브랜치)가 **착륙**한다. 비행 기록(로컬 브랜치)은 보존한다.

**목적**: MR 머지 후 Jira RESOLVE 전환. 로컬 브랜치·체크아웃은 건드리지 않는다 (작업 내역 보존 — 재참조·cherry-pick 여지를 남긴다).

인자 `$ARGUMENTS` 에서 이슈 키 추출. 생략 시 `.work/` 최근 파일에서 추정 (없으면 요청).

---

## Phase 0: 사전 점검

- `command -v acli` — acli 설치 확인. 미설치 → Phase 2 Jira 전환 단계를 스킵 + Handoff 에 "Jira RESOLVE: 수동 필요" 표기.
- 설치됨 + 미인증 (`acli jira auth status` 실패) → 동일 취급.

## Phase 1: MR 상태 확인 (순차)

1. `.work/{issue_key}.md` 에서 MR URL 추출 → MR ID 파싱.
2. `glab mr view {mr_id} --output json` 실행.
3. `state` 필드가 `merged` 인지 확인.
   - `opened` → 중단. "MR 미머지 상태. 머지 후 재시도" 안내.
   - `closed` (비머지) → 중단. "MR 이 머지 없이 닫힘. Jira 상태 수동 판단 필요" 안내.
   - `merged` → Phase 2 진행.

## Phase 2: Jira RESOLVE 전환

- `acli jira workitem transition {issue_key} --status "RESOLVE"` (Bash) — IN PROGRESS → RESOLVE
  - Phase 0 에서 acli 미가용 판정 시 스킵 + Handoff 에 "Jira RESOLVE: 수동 필요" 표기.
  - acli 호출 실패 (exit ≠ 0) → 기록 후 수동 안내.

**로컬 git 정리 없음**. 브랜치 삭제·체크아웃 전환·pull 은 수행하지 않는다 (작업 내역 보존). 청소가 필요하면 사용자가 수동으로 처리 (예: `git branch -d {branch}`, `git checkout {target}`).

## Phase 3: `.work/{issue_key}.md` 상태 갱신

- 상태 블록: `MR-ed` → `Merged`
- 다음 액션: "완료 보고 (`/recap`)"
- MR 섹션에 `머지 완료` 표시

## Phase 4: Handoff

```
┌──────────────────────────────────────────────┐
│ 착륙 완료: {issue_key}                         │
│   Jira: RESOLVE                              │
│   로컬 브랜치 보존: {branch}                   │
│                                               │
│ 다음: 결과 보고 → /recap {issue_key}        │
│       (Confluence 까지 → /recap {issue_key} --confluence) │
│       또는 다음 이슈 → /pick CDS-YYYY      │
│       상태 확인 → /where                   │
└──────────────────────────────────────────────┘
```

---

## 실패/예외 처리

- 이슈 키 추론 실패 → 사용자에게 명시 요청
- MR URL 파싱 실패 → `.work/{issue_key}.md` 확인 후 수기 입력 요청
- acli 미설치/미인증 → Phase 2 Jira 전환 스킵, Handoff 에 "Jira RESOLVE: 수동 필요" 표기
- Jira transition 실패 (acli exit ≠ 0) → 권한/status 명 불일치 가능성. `acli jira workitem transition --help` 로 플래그 확인, 수동 전환 안내

## 원칙

- **파괴적 작업 금지**: `git branch -D`, `git reset --hard`, force push 등.
- **로컬 작업 내역 보존**: 머지된 브랜치를 자동 삭제하지 않는다. 재참조·cherry-pick·히스토리 추적 여지를 남긴다. 사용자가 원할 때 수동으로 정리.
- MR 미머지 상태에서는 RESOLVE 전환 금지.
- **착륙만 담당**. 결과 보고·Confluence 는 `/recap` 이 담당.
