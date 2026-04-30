#!/usr/bin/env node
import {
  readFileSync,
  writeFileSync,
  mkdirSync,
  existsSync,
  realpathSync,
} from "node:fs";
import { homedir } from "node:os";
import { dirname, join, resolve } from "node:path";

const MARKETPLACE_KEY = "oke-sds";
const MARKETPLACE_REPO = "chanshin0/oke-sds";
const LEGACY_KEY = "okestro-sds";
const LEGACY_REPO = "chanshin0/okestro-sds";

const c = {
  reset: "\x1b[0m",
  bold: "\x1b[1m",
  dim: "\x1b[2m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  cyan: "\x1b[36m",
  red: "\x1b[31m",
};

function log(msg) {
  process.stdout.write(msg + "\n");
}

function fail(msg) {
  process.stderr.write(`${c.red}✗${c.reset} ${msg}\n`);
  process.exit(1);
}

function checkNode() {
  const major = Number(process.versions.node.split(".")[0]);
  if (major < 18) {
    fail(`Node.js 18+ required. Current: ${process.versions.node}`);
  }
}

function parseArgs(argv) {
  const args = { global: false, help: false };
  for (const a of argv.slice(2)) {
    if (a === "--global" || a === "-g") args.global = true;
    else if (a === "--help" || a === "-h") args.help = true;
    else fail(`Unknown argument: ${a}`);
  }
  return args;
}

function printHelp() {
  log(`${c.bold}oke-sds${c.reset} — Claude Code marketplace bootstrapper`);
  log("");
  log(`${c.bold}Usage${c.reset}`);
  log(`  npx oke-sds              ${c.dim}# project scope (./.claude/settings.json)${c.reset}`);
  log(`  npx oke-sds --global     ${c.dim}# user scope (~/.claude/settings.json)${c.reset}`);
  log(`  npx oke-sds --help`);
  log("");
  log(`${c.bold}Project mode${c.reset} ${c.dim}(default)${c.reset}`);
  log(`  Writes to <cwd>/.claude/settings.json — commit it to share with team.`);
  log(`  Future cloners get marketplace access automatically.`);
  log("");
  log(`${c.bold}Global mode${c.reset}`);
  log(`  Writes to ~/.claude/settings.json — applies across all projects on this machine.`);
}

function readSettings(path) {
  if (!existsSync(path)) return {};
  try {
    return JSON.parse(readFileSync(path, "utf8"));
  } catch (e) {
    fail(`Failed to parse ${path}: ${e.message}`);
  }
}

function writeSettings(path, settings) {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, JSON.stringify(settings, null, 2) + "\n");
}

function mergeMarketplace(settings) {
  const existing =
    settings.extraKnownMarketplaces &&
    typeof settings.extraKnownMarketplaces === "object" &&
    !Array.isArray(settings.extraKnownMarketplaces)
      ? { ...settings.extraKnownMarketplaces }
      : {};

  let removedLegacy = false;
  if (
    existing[LEGACY_KEY] &&
    existing[LEGACY_KEY].source?.repo === LEGACY_REPO
  ) {
    delete existing[LEGACY_KEY];
    removedLegacy = true;
  }

  const current = existing[MARKETPLACE_KEY];
  const desired = {
    source: { source: "github", repo: MARKETPLACE_REPO },
    autoUpdate: true,
  };

  const alreadyCorrect =
    current &&
    current.source?.source === desired.source.source &&
    current.source?.repo === desired.source.repo &&
    current.autoUpdate === desired.autoUpdate;

  if (alreadyCorrect && !removedLegacy) {
    return { settings, added: false, removedLegacy };
  }

  return {
    settings: {
      ...settings,
      extraKnownMarketplaces: { ...existing, [MARKETPLACE_KEY]: desired },
    },
    added: !alreadyCorrect,
    removedLegacy,
  };
}

function resolveSettingsPath(useGlobal) {
  return useGlobal
    ? join(homedir(), ".claude", "settings.json")
    : resolve(process.cwd(), ".claude", "settings.json");
}

function canonical(p) {
  try {
    return realpathSync(p);
  } catch {
    return resolve(p);
  }
}

function guardProjectMode(useGlobal) {
  if (useGlobal) return;
  if (canonical(process.cwd()) === canonical(homedir())) {
    fail(
      `cwd is your home directory (${homedir()}).\n` +
        `  Project mode would write to ~/.claude/settings.json — same as --global.\n` +
        `  → cd into a project first, or pass --global if that's what you want.`
    );
  }
}

function main() {
  const args = parseArgs(process.argv);
  if (args.help) {
    printHelp();
    return;
  }

  checkNode();
  guardProjectMode(args.global);

  const settingsPath = resolveSettingsPath(args.global);
  const scopeLabel = args.global ? "user-global" : "project";

  log(`${c.bold}oke-sds bootstrapper${c.reset} ${c.dim}(${scopeLabel} scope)${c.reset}`);
  log(`${c.dim}Target: ${settingsPath}${c.reset}\n`);

  const current = readSettings(settingsPath);
  const { settings, added, removedLegacy } = mergeMarketplace(current);

  if (added || removedLegacy) {
    writeSettings(settingsPath, settings);
    if (removedLegacy) {
      log(`${c.green}✓${c.reset} Removed legacy "${LEGACY_KEY}" → ${LEGACY_REPO}`);
    }
    if (added) {
      log(`${c.green}✓${c.reset} Registered "${MARKETPLACE_KEY}" → ${MARKETPLACE_REPO}`);
    }
  } else {
    log(`${c.yellow}•${c.reset} "${MARKETPLACE_KEY}" already registered — skipping`);
  }

  log("");
  if (!args.global) {
    log(`${c.bold}Tip${c.reset} ${c.dim}— commit .claude/settings.json so teammates get marketplace access automatically:${c.reset}`);
    log(`  ${c.cyan}git add .claude/settings.json && git commit -m "chore: register oke-sds marketplace"${c.reset}`);
    log("");
  }
  log(`${c.bold}Next steps${c.reset} ${c.dim}(in Claude Code, inside your project)${c.reset}`);
  log(`  ${c.cyan}1.${c.reset} /plugin install sds-workflow@oke-sds`);
  log(`  ${c.cyan}2.${c.reset} /sds-workflow:init`);
  log("");
  log(`${c.dim}Optional: /plugin install weekly-report@oke-sds${c.reset}`);
}

main();
