# okestro-sds

Okestro SDS 팀 Claude Code marketplace (private).

## 설치

```
/plugin marketplace add chanshin0/okestro-sds
/plugin install sds-workflow@okestro-sds
/reload-plugins
```

private repo 라 GitHub 인증 필요. `gh auth login` 또는 `GITHUB_TOKEN` 환경변수 설정.

## 구조

```
.
├── .claude-plugin/marketplace.json   # 카탈로그
└── plugins/
    └── sds-workflow/                 # plugin 본체 (회사 워크플로우)
```

## Plugin

| 이름 | 설명 |
|---|---|
| `sds-workflow` | Jira → Claude Code → GitLab MR 워크플로우 (pick/ship/land/recap/where/draft/autopilot/tune/init) |

자세한 사용법은 `plugins/sds-workflow/README.md` 참조.
