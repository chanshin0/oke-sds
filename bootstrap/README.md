# oke-sds

One-shot bootstrapper for the [chanshin0/oke-sds](https://github.com/chanshin0/oke-sds) Claude Code marketplace.

## Usage

```bash
# Project scope (default) — writes to ./.claude/settings.json
npx oke-sds

# User-global scope — writes to ~/.claude/settings.json
npx oke-sds --global

npx oke-sds --help
```

## Project mode (default)

Run inside your project. Adds `chanshin0/oke-sds` to `<cwd>/.claude/settings.json`. Commit the file so teammates get marketplace access automatically when they clone.

```bash
cd my-project
npx oke-sds
git add .claude/settings.json
git commit -m "chore: register oke-sds marketplace"
```

## Global mode

Apply to every project on the machine.

```bash
npx oke-sds --global
```

## Next steps (in Claude Code)

```
/plugin install sds-workflow@oke-sds
/sds-workflow:init
```

## Behavior

- Idempotent — safe to run multiple times.
- Migrates legacy `okestro-sds` key automatically.
- Zero dependencies. Node 18+.
