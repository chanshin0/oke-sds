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
├── commands/                       # 공유 슬래시 커맨드 (TBD)
└── skills/
    ├── ai-readiness-cartography/   # 레포 AI-Ready 감사 + HTML 대시보드 생성
    └── presentation_slides/        # YouTube 영상용 다크 테마 HTML 슬라이드 세트 자동 생성
```

## Skills

### `ai-readiness-cartography`

임의 레포를 **AI-Ready v2 루브릭** (100점 · 7 카테고리) 으로 감사하고 단일 HTML 대시보드 + ROI 순 액션 리스트를 출력. 트리거 예시:

- "이 레포 AI-readiness 지도 그려줘"
- "코드베이스가 코딩 에이전트 친화적인지 점수 매겨줘"
- "ai-readiness-cartography"

### `presentation_slides`

YouTube 영상용 **다크 테마 HTML 슬라이드 세트** (개별 HTML + index.html 허브) 자동 생성. 대본(`script.md`) 기반 섹션 자동 도출 또는 직접 슬라이드 목록 지정 가능. hero-cards / roadmap / comparison / step-flow / diagram / grid 등 8가지 레이아웃, 키보드 네비게이션, 페이지 전환 애니메이션 포함. 트리거 예시:

- "프레젠테이션 슬라이드 만들어줘"
- "이 대본으로 HTML 슬라이드 생성"
- "발표 슬라이드 HTML"

원본: [chanshin0/cc-skills-repo](https://github.com/chanshin0/cc-skills-repo). 정적 복사본이라 원본 업데이트는 수동 sync 필요.

## 커맨드

추후 추가 예정 — 현재는 스킬 호스팅 전용.
