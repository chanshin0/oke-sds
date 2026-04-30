---
description: 현재 상태를 감지해 다음 액션 안내
argument-hint: "[--force] [--dry-run]"
entry-mode: readonly
required-permission: default
---


## Preamble

> 본문 실행 전 `${CLAUDE_PLUGIN_ROOT}/workflow/preamble.md` 를 Read 하여 공통 설정 로드 절차를 수행한다. 이 절차에서 추출한 `PROJECT_KEY` 를 이슈키 정규식·브랜치 패턴 매칭에 사용한다.

# /where

**은유**: 지금 궤도상 **어디에 있는지** 묻는다. 위치에 맞는 다음 행위를 라우팅.

**목적**: 현재 저장소 상태(브랜치/플랜/커밋/MR) + Jira 상태를 감지해 다음에 실행할 적절한 커맨드로 자동 라우팅.

인자:
- `--force` — 안전 게이트 우회 (위험)
- `--dry-run` — 라우팅 결정만 출력, 실행 안 함

---

## Step 1: 상태 감지 (단일 메시지 병렬 호출)

아래를 병렬 실행:

- `git branch --show-current` (Bash)
- `git status --short` (Bash)
- `git log --oneline -5` (Bash)
- Glob `.work/CDS-*.md` — 최근 작업 컨텍스트
- `git log remote-sds/${MR_TARGET_BRANCH}..HEAD --oneline` (Bash) — 로컬 커밋 존재 여부

현재 브랜치에서 이슈 키 추출 (`{type}/CDS-XXXX-{slug}` 패턴).

이슈 키가 있으면 추가 병렬:
- `.work/{issue_key}.md` Read — 상태 블록·플랜 섹션·MR URL
- `acli jira workitem view {issue_key} --json` (Bash) — 현재 Jira status
  - `command -v acli` 실패 또는 `acli jira auth status` 실패 → 이 단계 스킵. Jira 축은 `unknown` 으로 처리하여 라우팅 (해당 축 의존 경고만 스킵).

## Step 2: 상태 결정

수집한 정보로 아래 **4 축**으로 상태 분류:

| 축 | 값 |
|----|----|
| 브랜치 | `main` / `issue_branch` |
| 플랜 | `없음` / `있음` / `escape_hatch` |
| 로컬 커밋 | `없음` / `있음(미푸시)` / `푸시됨` |
| MR | `없음` / `opened` / `merged` / `closed` |
| Jira | `TO DO` / `IN PROGRESS` / `RESOLVE` |

## Step 3: 라우팅 (9 routes)

| # | 조건 | 제안 액션 |
|---|------|---------|
| A | `main` 브랜치 + 작업 컨텍스트 없음 | "새 이슈 집기 — `/pick CDS-XXXX`" |
| B | `main` 브랜치 + 미해결 이슈 컨텍스트 존재 (MR merged 아님) | "이전 이슈 복귀: `git checkout {branch}` 제안, 또는 `/land`" |
| C | 이슈 브랜치 + 플랜 없음 | "`/pick {issue_key}` — 플랜 단계부터 재시작" |
| D | 이슈 브랜치 + 플랜 있음 + 로컬 변경 없음 | "구현 시작 — 플랜의 '구현 접근' 단계 따라 진행" |
| E | 이슈 브랜치 + 플랜 있음 + 로컬 커밋 있음 + 미푸시 | "`/ship` — 검증·커밋·MR 출하" |
| F | 이슈 브랜치 + MR `opened` | "리뷰 대기 중. 머지 후 `/land {issue_key}`" |
| G | 이슈 브랜치 + MR `merged` + Jira `IN PROGRESS` | "`/land {issue_key}` — Jira RESOLVE 전환 + 정리" |
| H | 이슈 브랜치 + MR `merged` + Jira `RESOLVE` + `main` 미 체크아웃 | "정리만 남음: `git checkout main && git pull && git branch -d {branch}`" |

매칭 조건이 여러 개면 **더 진행된 상태** 를 선택 (H > G > F > E > D > C > B > A).

## Step 4: 안전 게이트

라우팅 결정 후 실행 전에 아래를 검사:

1. **미커밋 변경** (`git status --short` 비어있지 않음) — 다음 액션이 브랜치 스위치/삭제면 경고.
2. **플랜 일관성** — route E (`/ship`) 제안 시 플랜 "영향 범위" 와 diff 일치 여부 미리 경고.
3. **Jira 상태 불일치** — 브랜치는 이슈 중인데 Jira 가 `TO DO` → 경고 (Phase 2 전환 누락 가능성).
4. **머지된 브랜치에서 신규 커밋** — merged MR 에 추가 커밋이 있으면 경고 (새 브랜치 권장).

게이트 하나라도 트리거되면 경고 표시 후 사용자 확인 요청. `--force` 사용 시 게이트 우회.

## Step 5: 제안 출력 + 실행

### Dry-run (`--dry-run`) 또는 안전 게이트 트리거 시

```
┌─────────────────────────────────────────────┐
│ 현재 위치                                     │
│   브랜치: {branch}                            │
│   Jira: {status}                             │
│   플랜: {있음/없음/escape_hatch}               │
│   로컬 커밋: {N}개 (미푸시 {M}개)              │
│   MR: {없음/opened/merged}                    │
│                                              │
│ 제안 액션: {route_label}                      │
│   → {command}                                │
│                                              │
│ [경고] {gate_message}                         │
└─────────────────────────────────────────────┘
```

사용자 확인 후 명령 실행.

### 기본 (게이트 통과 + dry-run 아님)

제안 액션 출력 후 **즉시 해당 커맨드 실행 제안** (AskUserQuestion 으로 실행 여부 확인).

- `/pick` / `/ship` / `/land` 는 본 명령 내부에서 직접 실행하지 않고, 사용자에게 "다음 커맨드 입력" 을 유도 (슬래시 커맨드는 사용자가 호출).

---

## 실패/예외 처리

- acli 미설치/미인증 또는 Jira 조회 실패 → Jira 축은 `unknown` 으로 두고 라우팅. 해당 축 의존 경고 스킵.
- `.work/{issue_key}.md` 미존재 → 플랜 축 `없음` 처리.
- 브랜치 패턴 불일치 → route A/B 후보만 고려.

## 원칙

- **읽기 전용**. 이 커맨드는 상태 변경을 하지 않음 (브랜치 스위치·커밋·Jira 전환 모두 금지).
- 라우팅 결정의 근거를 항상 상태 블록으로 노출 (사용자가 판단 가능하도록).
- `--force` 는 게이트만 우회, 파괴적 작업은 여전히 금지.
