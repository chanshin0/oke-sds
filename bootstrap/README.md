# oke-sds

One-shot bootstrapper for the [chanshin0/oke-sds](https://github.com/chanshin0/oke-sds) Claude Code marketplace.

## Usage

```bash
npx oke-sds
```

What it does:

1. Adds `chanshin0/oke-sds` to your `~/.claude/settings.json` `extraKnownMarketplaces` (idempotent).
2. Prints next steps to install plugins inside Claude Code.

After running, in Claude Code:

```
/plugin install sds-workflow@oke-sds
/sds-workflow:init
```

## Why

- Skip the `/plugin marketplace add` step in Claude Code.
- Run once per machine — repo-level setup is handled by `/sds-workflow:init` inside each project.
- Zero dependencies, runs on Node 18+.
