# sds-common

특정 업무에 묶이지 않는 **공유 커맨드 + 스킬** 모음. `sds-workflow` (Jira→MR) / `weekly-report` (Confluence) 와 독립적으로 동작.

## 설치

```
/plugin install sds-common@oke-sds
/reload-plugins
```

## 구성

```
sds-common/
├── .claude-plugin/plugin.json
├── commands/                # 공유 슬래시 커맨드 (TBD)
└── skills/
    └── ai-readiness-cartography/   # 레포 AI-Ready 감사 + HTML 대시보드 생성
```

## Skills

### `ai-readiness-cartography`

임의 레포를 **AI-Ready v2 루브릭** (100점 · 7 카테고리) 으로 감사하고 단일 HTML 대시보드 + ROI 순 액션 리스트를 출력. 트리거 예시:

- "이 레포 AI-readiness 지도 그려줘"
- "코드베이스가 코딩 에이전트 친화적인지 점수 매겨줘"
- "ai-readiness-cartography"

원본: [chanshin0/cc-skills-repo](https://github.com/chanshin0/cc-skills-repo). 정적 복사본이라 원본 업데이트는 수동 sync 필요.

## 커맨드

추후 추가 예정 — 현재는 스킬 호스팅 전용.
