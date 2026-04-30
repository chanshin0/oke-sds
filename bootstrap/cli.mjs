#!/usr/bin/env node
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";

const MARKETPLACE_KEY = "oke-sds";
const MARKETPLACE_REPO = "chanshin0/oke-sds";
const LEGACY_KEY = "okestro-sds";
const LEGACY_REPO = "chanshin0/okestro-sds";
const SETTINGS_PATH = join(homedir(), ".claude", "settings.json");

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

function readSettings() {
  if (!existsSync(SETTINGS_PATH)) return {};
  try {
    return JSON.parse(readFileSync(SETTINGS_PATH, "utf8"));
  } catch (e) {
    fail(`Failed to parse ${SETTINGS_PATH}: ${e.message}`);
  }
}

function writeSettings(settings) {
  mkdirSync(dirname(SETTINGS_PATH), { recursive: true });
  writeFileSync(SETTINGS_PATH, JSON.stringify(settings, null, 2) + "\n");
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

function main() {
  checkNode();

  log(`${c.bold}oke-sds bootstrapper${c.reset}`);
  log(`${c.dim}Registering marketplace: ${MARKETPLACE_REPO}${c.reset}\n`);

  const current = readSettings();
  const { settings, added, removedLegacy } = mergeMarketplace(current);

  if (added || removedLegacy) {
    writeSettings(settings);
    if (removedLegacy) {
      log(`${c.green}✓${c.reset} Removed legacy "${LEGACY_KEY}" → ${LEGACY_REPO}`);
    }
    if (added) {
      log(`${c.green}✓${c.reset} Registered "${MARKETPLACE_KEY}" → ${MARKETPLACE_REPO}`);
    }
    log(`${c.dim}  ${SETTINGS_PATH}${c.reset}`);
  } else {
    log(`${c.yellow}•${c.reset} "${MARKETPLACE_KEY}" already registered — skipping`);
  }

  log("");
  log(`${c.bold}Next steps${c.reset} ${c.dim}(in Claude Code, inside your project)${c.reset}`);
  log(`  ${c.cyan}1.${c.reset} /plugin install sds-workflow@oke-sds`);
  log(`  ${c.cyan}2.${c.reset} /sds-workflow:init`);
  log("");
  log(`${c.dim}Optional: /plugin install weekly-report@oke-sds${c.reset}`);
}

main();
