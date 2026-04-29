# okestro-sds

Okestro SDS 팀 Claude Code marketplace (private).

## 설치

```
/plugin marketplace add chanshin0/okestro-sds
/plugin install sds-workflow@okestro-sds
/plugin install review-tools@okestro-sds
/plugin install dev-analytics@okestro-sds
/plugin install content-creation@okestro-sds
/reload-plugins
```

private repo 라 GitHub 인증 필요. `gh auth login` 또는 `GITHUB_TOKEN` 환경변수 설정.

## 구조

```
.
├── .claude-plugin/marketplace.json   # 카탈로그 (4개 plugin)
└── plugins/
    └── sds-workflow/                 # plugin 본체 (회사 워크플로우)
```

skills 큐레이션은 외부 repo `chanshin0/cc-skills-repo` 를 `git-subdir` 로 sparse-clone 해서 가져옴.

## Plugin

| 이름 | 설명 | source |
|---|---|---|
| `sds-workflow` | Jira → Claude Code → GitLab MR 워크플로우 | local (`./plugins/sds-workflow`) |
| `review-tools` | 답변·결과물 비판적 재검토 | cc-skills-repo |
| `dev-analytics` | Claude Code 사용·코드베이스 메트릭 분석 | cc-skills-repo |
| `content-creation` | 발표·콘텐츠 생산 | cc-skills-repo |

자세한 사용법은 `plugins/sds-workflow/README.md` 참조.
