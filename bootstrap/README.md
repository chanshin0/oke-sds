# oke-sds

Claude Code marketplace bootstrapper for [chanshin0/oke-sds](https://github.com/chanshin0/oke-sds).

## Quick install

```bash
cd my-project
npx oke-sds
```

Then, inside Claude Code:

```
/plugin install sds-workflow@oke-sds
/reload-plugins
/sds-workflow:init
```

---

### Apply machine-wide

```bash
npx oke-sds --global   # writes to ~/.claude/settings.json
```

### Commit only if the repo is team-shared

```bash
git add .claude/settings.json
git commit -m "chore: register oke-sds marketplace"
```

Future cloners skip the `npx` step. For personal/solo repos, leave the file uncommitted (or add it to `.gitignore`).

### Uninstall

```bash
npx oke-sds --uninstall              # remove from project scope
npx oke-sds --uninstall --global     # remove from user-global scope
```

This removes only the marketplace entry. Already-installed plugins stay — remove them inside Claude Code:

```
/plugin uninstall sds-workflow@oke-sds
/plugin uninstall weekly-report@oke-sds
```

### Behavior

- Idempotent — safe to run multiple times.
- Migrates legacy `okestro-sds` key automatically.
- Zero dependencies. Node 18+.
