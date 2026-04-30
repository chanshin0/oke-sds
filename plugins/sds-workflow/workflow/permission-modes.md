# 권한 모드 안내 (CLI × Mode 매트릭스)

`workflow/preamble.md` 의 **Phase 0.5 (Entry Switch)** 에서 fail-fast 또는 권장 안내를 출력할 때 참조하는 reference. 커맨드 frontmatter 의 `entry-mode` 와 현재 CLI / 권한 모드 조합으로 분기한다.

---

## 1. entry-mode 정의

| entry-mode | 의미 | 적용 커맨드 |
|---|---|---|
| `autopilot` | 자율 운행 — 중간 prompt 발생 시 워크플로 깨짐. 무권한 prompt 모드 강제. | `/autopilot` |
| `interactive` | 사용자 관찰 하 단계별 진행. prompt 발생해도 안전. accept-edits 권장. | `/init`, `/pick`, `/ship`, `/land`, `/draft`, `/tune` |
| `readonly` | 상태 조회만. Plan mode 까지 허용. | `/where` |

---

## 2. 권한 모드 분류 (Claude Code 기준)

| mode 키 | Claude Code 명칭 | 동작 |
|---|---|---|
| `bypass` | Bypass permissions | 전부 자동 승인 (`--dangerously-skip-permissions`) |
| `accept-edits` | Auto-accept edits | Edit/Write 자동, Bash 는 prompt |
| `default` | Default | Edit/Write/Bash 매번 prompt |
| `plan` | Plan mode | Edit/Write/Bash 차단 (읽기 전용) |

다른 CLI 의 등가 모드:

| CLI | bypass 등가 | plan 등가 |
|---|---|---|
| Claude Code | Bypass permissions | Plan mode |
| Cursor | Auto-Run / YOLO | Ask mode |
| Codex CLI | `--full-auto` | (없음, 수동 승인 강제) |

---

## 3. 분기 매트릭스

행: 현재 mode, 열: 커맨드의 entry-mode. 셀: Phase 0.5 가 취할 행동.

| ↓mode \\ entry→ | `autopilot` | `interactive` | `readonly` |
|---|---|---|---|
| **bypass** | ✅ 진행 | ✅ 진행 | ✅ 진행 |
| **accept-edits** | ⚠️ Bash prompt 위험 안내 후 사용자 결정 | ✅ 진행 | ✅ 진행 |
| **default** | ❌ **즉시 중단** + 재시작 안내 | ⚠️ N회 prompt 안내 후 진행 | ✅ 진행 |
| **plan** | ❌ **즉시 중단** | ❌ **즉시 중단** (시뮬레이션 사고 방지) | ✅ 진행 |

---

## 4. 모드 추정 (probe)

런타임에 모드를 직접 조회하는 API 가 없으므로 **무해 probe** 로 간접 추정:

```bash
echo MODE_PROBE_OK
```

- 즉시 응답 (no prompt) → `bypass` 또는 `accept-edits` 추정 (Bash 자동 승인 영역)
- 사용자에게 prompt 발생 (모델이 감지) → `default`
- Bash 차단 / 거부 → `plan`

`accept-edits` 와 `bypass` 는 Bash 차원에서 구별 어렵다. autopilot 분기에서만 차이 의미가 있으므로, **Bash prompt 가 한 번이라도 발생하는지** 만 신경 쓰면 됨.

---

## 5. CLI 별 재시작 안내 메시지 (autopilot 차단 시)

| CLI | 안내 |
|---|---|
| **Claude Code (CLI)** | 세션 종료 후 `claude --dangerously-skip-permissions` 로 재시작. 또는 현재 세션에서 `Shift+Tab` 두 번 (Bypass 모드 진입). |
| **Claude Code (desktop/web)** | 세션 설정에서 "Bypass permissions" 토글을 켠 뒤 재시도. |
| **Cursor** | Settings → Cursor Tab → Auto-Run mode 활성화 후 재시도. |
| **Codex CLI** | `codex --full-auto` 로 재시작. |
| **알 수 없음** | 이 CLI 의 "권한 자동 승인" 모드를 활성화한 뒤 재시도. 모르면 README 의 PERMISSIONS 섹션 참조. |

---

## 6. CLI 감지 휴리스틱

```bash
if [ -n "${CLAUDE_PLUGIN_ROOT}" ]; then
  CLI="claude-code"
elif [ -n "${CURSOR_TRACE_ID}" ] || [ -n "${CURSOR_AGENT}" ]; then
  CLI="cursor"
elif [ -n "${CODEX_HOME}" ] || [ -n "${OPENAI_CODEX}" ]; then
  CLI="codex"
else
  CLI="unknown"
fi
```

(Cursor / Codex 환경변수 키는 향후 검증 + 보정 필요. 현시점은 best-effort.)

---

## 7. 안내 출력 포맷 (preamble 표준)

Phase 0.5 가 사용자에게 보일 출력 템플릿:

**autopilot 차단 (default/plan 모드)**:
```
[sds-workflow] ❌ /{command} 진입 거부

이 커맨드의 entry-mode 는 `autopilot` 으로, 중간 권한 prompt 가 발생하면
워크플로가 깨진다. 현재 세션은 `{detected_mode}` 모드로 추정됨.

다음 중 하나로 재시작 후 다시 호출:
  {cli_specific_guidance}

자세한 내용: ${CLAUDE_PLUGIN_ROOT}/workflow/permission-modes.md
```

**interactive default 모드 안내**:
```
[sds-workflow] ⚠️ /{command} default 모드에서 실행

이 명령은 약 N 회 prompt 가 발생할 수 있다.
원활한 진행을 원하면 `Shift+Tab` 한 번으로 accept-edits 모드를 권장.

진행한다.
```

**plan 모드 차단 (interactive/autopilot 공통)**:
```
[sds-workflow] ❌ /{command} 는 Plan mode 에서 실행 불가

Plan mode 는 Bash/Edit 가 차단되어 워크플로 시뮬레이션 사고 위험이 있다.
`Shift+Tab` 두 번으로 Bypass 모드 또는 Default 모드로 전환 후 재시도.
```

---

## 8. 변경 시 영향

이 파일 변경 시:
- `workflow/preamble.md` Phase 0.5 의 분기 표·메시지 템플릿 동기화
- 신규 커맨드 추가 시 entry-mode 부착 + 위 표에 등재 검토
