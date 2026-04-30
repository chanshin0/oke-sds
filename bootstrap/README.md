# oke-sds

Claude Code marketplace bootstrapper for [chanshin0/oke-sds](https://github.com/chanshin0/oke-sds).

## Quick install

```bash
cd my-project
npx oke-sds
```

이후 Claude Code 안에서:

```
/plugin install sds-workflow@oke-sds
/reload-plugins
/sds-workflow:init
```

---

### 머신 전역 적용

```bash
npx oke-sds --global   # ~/.claude/settings.json
```

### 팀 공유 레포일 때만 커밋

```bash
git add .claude/settings.json
git commit -m "chore: register oke-sds marketplace"
```

이후 clone 자는 `npx` 단계 불필요. 개인/솔로 레포면 커밋하지 말고 그대로 두거나 `.gitignore` 추가.

### 제거

```bash
npx oke-sds --uninstall              # project scope
npx oke-sds --uninstall --global     # user-global scope
```

`extraKnownMarketplaces` 의 `oke-sds` 엔트리만 제거. 이미 `/plugin install` 한 플러그인은 그대로 — 빼려면 Claude Code 안에서:

```
/plugin uninstall sds-workflow@oke-sds
/plugin uninstall weekly-report@oke-sds
```

### 동작

- Idempotent — 여러 번 실행해도 안전
- 옛 `okestro-sds` 키 자동 마이그레이션
- 의존성 0, Node 18+
