# oke-sds

SDS workflow Claude Code marketplace.

Generic Jira → Claude Code → GitLab MR 워크플로우 + Confluence 주간보고 자동화. 회사 식별자는 모두 placeholder 화돼있어 어떤 환경에서도 사용 가능 (자세한 셋업은 `plugins/sds-workflow/README.md`).

## 설치

```
/plugin marketplace add chanshin0/oke-sds
/plugin install sds-workflow@oke-sds
/plugin install weekly-report@oke-sds
/reload-plugins
```

## 구조

```
.
├── .claude-plugin/marketplace.json    # 카탈로그
└── plugins/
    ├── sds-workflow/                  # Jira → MR 워크플로우
    └── weekly-report/                 # Confluence 주간보고 자동화
```

## Plugin

| 이름 | 설명 |
|---|---|
| `sds-workflow` | Generic Jira → Claude Code → GitLab MR 워크플로우 (pick/ship/land/where/draft/autopilot/tune/init) |
| `weekly-report` | Confluence 주간보고 자동화 — 신주차 페이지 생성 + Jira 데이터 자동 채움 |

상세 사용법은 각 plugin 의 `README.md` 참조.

## License

MIT
