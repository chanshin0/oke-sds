---
description: 플러그인 업데이트 절차 안내 — 3줄 슬래시 커맨드 시퀀스
---

# /sds-workflow:update

**목적**: 팀원이 dev 브랜치에서 `git pull` 로 플러그인 source 를 갱신한 뒤 Claude Code 캐시에 반영하는 절차를 한 번의 커맨드로 안내.

**한계**: Claude Code 는 슬래시 커맨드를 다른 슬래시 커맨드에서 직접 invoke 할 수 없다 (공식 제약). 이 커맨드는 사용자가 순차 입력할 **3줄 시퀀스를 그대로 출력** 한다.

---

## 동작

사용자에게 아래를 출력하고 종료한다. 다른 설명 최소:

---

플러그인 업데이트 절차. 다음 3줄을 순차 입력하세요:

```
/plugin marketplace update
/plugin install sds-workflow@remote-ceph-admin
/reload-plugins
```

**버전 bump 되지 않은 source 를 강제 반영하려면**: 2번째 줄 앞에 `/plugin uninstall sds-workflow@remote-ceph-admin` 먼저 실행. SPEC.md 의 버전 bump 규약이 지켜지면 불필요.

반영 안 되면 Claude Code 재시작.

---

## 참조

- SPEC.md 확정 사항 "플러그인 버전 bump 규약" — 머지마다 patch version 1단계 bump
- 호출 계기: `git pull` 로 플러그인 source 가 갱신된 직후 팀원 스스로 실행. (이전 버전에 있던 SessionStart hook 자동 안내는 0.3.3 에서 폐기 — `CHANGELOG.md` 참조.)
