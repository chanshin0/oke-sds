# weekly-report

Confluence 주간보고 자동화 plugin.

매주 신주차 페이지를 자동 생성하고 Jira 이슈를 사용자 행에 자동 채워넣는다. 자율 운행 시 Mon (create) / Wed (refresh) 스케줄로 사용자 PC 꺼져있어도 동작 (별도 cron/cloud trigger 필요).

## 사전 요구사항

| 항목 | 내용 |
|---|---|
| Python 3.10+ | scripts 실행 |
| Atlassian API Token | 환경변수 `ATLASSIAN_API_TOKEN` (Confluence/Jira REST 호출) |
| `.team-workflow/workflow.yml` | `sds-workflow:init` 으로 생성 또는 수동 작성 |
| Confluence 페이지 구조 | 주간보고 루트 → 반기/월 폴더 → 주차 페이지 (4-column 테이블 per user row) |

## 설정

`.team-workflow/workflow.yml` 의 `confluence.weekly_report` 섹션:

```yaml
confluence:
  base_url: "https://<your-team>.atlassian.net/wiki"
  space_key: "<SPACE>"
  weekly_report:
    root_id: "1234567890"           # 주간보고 루트 페이지 ID (필수)
    template_source_id: ""          # 선택 — 첫 실행 시 명시 source. 비우면 자동 선택.
```

## 그룹 라벨 (`GROUP_LABEL`)

자동 생성 블록은 첫 `<li>` 의 `<p>` 텍스트로 식별된다. 환경변수로 override:

```bash
export WEEKLY_REPORT_GROUP_LABEL="MyTeam"
```

기본값 `TEAM`. 너의 Confluence 템플릿에 맞춰 설정.

## 커맨드

| 커맨드 | 역할 |
|---|---|
| `/weekly-report:init` | 주간보고 시스템 첫 부팅 — 루트 페이지 ID 등 설정 검증 |
| `/weekly-report:create` | 신주차 페이지 생성 (이전주 차주 → 신주차 금주 이월) |
| `/weekly-report:update-mine` | 본인 행만 Jira 이슈로 자동 갱신 |
| `/weekly-report:update-all` | 모든 사용자 행 자동 갱신 (라우틴용) |

## 구조

```
weekly-report/
├── .claude-plugin/plugin.json
├── README.md
├── commands/
│   ├── weekly-report-init.md
│   ├── weekly-report-create.md
│   ├── weekly-report-update-mine.md
│   └── weekly-report-update-all.md
└── scripts/
    ├── weekly_report_create.py
    ├── weekly_report_update_mine.py
    ├── weekly_report_update_all.py
    ├── weekly_report_lib_check.py
    └── weekly_report_lib/
        ├── __init__.py
        ├── clients.py        # Confluence/Jira REST 클라이언트
        └── page_ops.py       # XHTML 외과적 편집 헬퍼
```

## 권장 퍼미션 사전 허용

`.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(python3:*)",
      "Bash(${CLAUDE_PLUGIN_ROOT}/scripts/*.py:*)"
    ]
  }
}
```
