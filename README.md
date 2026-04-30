# oke-sds

SDS workflow Claude Code marketplace.

Generic Jira → Claude Code → GitLab MR 워크플로우 + Confluence 주간보고 자동화.

## 빠른 설치

```bash
cd my-project
npx oke-sds
```

Claude Code 안에서:

```
/plugin install sds-workflow@oke-sds
/plugin install weekly-report@oke-sds
/reload-plugins
/sds-workflow:init
/sds-workflow:weekly-report-init
```

---

### 머신 전역 적용

```bash
npx oke-sds --global   # ~/.claude/settings.json
```

### 팀 공유 레포일 때만 커밋

```bash
git add .claude/settings.json && git commit -m "chore: register oke-sds marketplace"
```

이후 clone 자는 `npx` 단계 불필요. 개인 레포면 커밋하지 말고 그대로.

### 제거

```bash
npx oke-sds --uninstall            # marketplace 엔트리 제거
npx oke-sds --uninstall --global   # user-global 에서 제거
```

플러그인 자체 제거는 Claude Code 안에서 `/plugin uninstall sds-workflow@oke-sds` 등.

### 수동 설치 (npx 안 쓰고)

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
├── bootstrap/                         # npx oke-sds — marketplace 등록 부트스트래퍼
└── plugins/
    ├── sds-workflow/                  # Jira → MR 워크플로우
    └── weekly-report/                 # Confluence 주간보고 자동화
```

## Plugin

| 이름 | 설명 |
|---|---|
| `sds-workflow` | Generic Jira → Claude Code → GitLab MR 워크플로우 (pick/ship/where/draft/autopilot/tune/init) |
| `weekly-report` | Confluence 주간보고 자동화 — 신주차 페이지 생성 + Jira 데이터 자동 채움 |

상세 사용법은 각 plugin 의 `README.md` 참조.

## License

MIT
