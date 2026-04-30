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

Run inside your project. Adds `chanshin0/oke-sds` to `<cwd>/.claude/settings.json`.

```bash
cd my-project
npx oke-sds
```

### Commit only if the repo is team-shared

If this repo is shared with teammates and you want them to skip the bootstrap step on clone:

```bash
git add .claude/settings.json
git commit -m "chore: register oke-sds marketplace"
```

After this, anyone who clones the repo gets the marketplace registered automatically — they only need to run `/plugin install sds-workflow@oke-sds` inside Claude Code.

If the repo is personal/solo, leave the file uncommitted (or add it to `.gitignore`).

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
