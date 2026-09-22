#!/usr/bin/env node
/**
 * Validates the backend kit's own wiring. Run: node .claude/validate-kit.mjs
 *
 * Catches the mechanical failures that silently stop a kit from working:
 * an agent that never registers, a command with no description, a frontmatter
 * value that breaks the YAML parser, a reference to a file that no longer exists.
 *
 * These are all regex-checkable, so they belong here and not in a document
 * that asks a model to remember them.
 */
import { readdirSync, readFileSync, existsSync, statSync } from 'node:fs';
import { join, dirname, basename } from 'node:path';
import { fileURLToPath } from 'node:url';

const KIT = dirname(fileURLToPath(import.meta.url));
const problems = [];
const fail = (file, msg) => problems.push({ file, msg });

/** Minimal frontmatter reader. Returns null when the block is absent. */
function frontmatter(path) {
  const text = readFileSync(path, 'utf8');
  if (!text.startsWith('---\n')) return null;
  const end = text.indexOf('\n---', 4);
  if (end === -1) return null;
  const body = text.slice(4, end);
  const fields = {};
  for (const line of body.split('\n')) {
    if (!line.trim() || line.startsWith('#') || /^\s/.test(line)) continue;
    const at = line.indexOf(':');
    if (at === -1) continue;
    fields[line.slice(0, at).trim()] = line.slice(at + 1).trim();
  }
  return { fields, raw: body };
}

/**
 * A plain YAML scalar cannot contain ": " — the parser reads it as a nested
 * mapping and the whole frontmatter block fails. A quoted value is fine.
 */
function checkScalars(file, raw) {
  for (const line of raw.split('\n')) {
    const at = line.indexOf(':');
    if (at === -1 || /^\s/.test(line)) continue;
    const value = line.slice(at + 1).trim();
    if (!value || /^['"]/.test(value)) continue;
    if (value.includes(': ')) {
      fail(file, `frontmatter value contains ": " and will not parse — quote it or use an em dash: ${line.slice(0, 60)}...`);
    }
  }
}

/**
 * An unknown model value does not fail loudly — the agent or command just does
 * not run on the model the kit intends. Accept the aliases and full model IDs.
 */
const MODEL_ALIASES = new Set(['opus', 'sonnet', 'haiku', 'inherit']);
function checkModel(file, model) {
  if (model === undefined) return;
  const value = model.replace(/^['"]|['"]$/g, '');
  if (MODEL_ALIASES.has(value) || /^claude-[a-z0-9-]+$/.test(value)) return;
  fail(file, `unknown model "${value}" — use opus, sonnet, haiku, inherit, or a full model ID (claude-...)`);
}

/** Same failure mode as model: a typo is not rejected, it is just not applied. */
const EFFORT_LEVELS = new Set(['low', 'medium', 'high', 'xhigh', 'max']);
function checkEffort(file, effort) {
  if (effort === undefined) return;
  const value = effort.replace(/^['"]|['"]$/g, '');
  if (!EFFORT_LEVELS.has(value)) {
    fail(file, `unknown effort "${value}" — use low, medium, high, xhigh, or max`);
  }
}

function listDir(dir, filter) {
  const path = join(KIT, dir);
  if (!existsSync(path)) return [];
  return readdirSync(path).filter(filter).map((f) => join(path, f));
}

// --- agents: need name + description, and name must match the filename -------
for (const file of listDir('agents', (f) => f.endsWith('.md'))) {
  const rel = `agents/${basename(file)}`;
  const fm = frontmatter(file);
  if (!fm) {
    fail(rel, 'no frontmatter — this agent will NOT be registered and cannot be dispatched');
    continue;
  }
  checkScalars(rel, fm.raw);
  const expected = basename(file, '.md');
  if (!fm.fields.name) fail(rel, 'missing required field: name');
  else if (fm.fields.name !== expected) fail(rel, `name "${fm.fields.name}" does not match filename "${expected}"`);
  if (!fm.fields.description) fail(rel, 'missing required field: description');
  else if (!/^Use (when|to|before|after)/i.test(fm.fields.description)) {
    fail(rel, 'description should start with "Use when/to/before" — it states WHEN to dispatch, not what the agent is');
  }
  checkModel(rel, fm.fields.model);
  checkEffort(rel, fm.fields.effort);
}

// --- commands: need a description so they show up usefully in the menu -------
for (const file of listDir('commands', (f) => f.endsWith('.md'))) {
  const rel = `commands/${basename(file)}`;
  const fm = frontmatter(file);
  if (!fm) {
    fail(rel, 'no frontmatter — the command runs but shows no description');
    continue;
  }
  checkScalars(rel, fm.raw);
  if (!fm.fields.description) fail(rel, 'missing required field: description');
  checkModel(rel, fm.fields.model);
}

// --- skills: need name matching the directory, and a trigger description ----
const skillsDir = join(KIT, 'skills');
if (existsSync(skillsDir)) {
  for (const name of readdirSync(skillsDir)) {
    if (!statSync(join(skillsDir, name)).isDirectory()) continue;
    const file = join(skillsDir, name, 'SKILL.md');
    const rel = `skills/${name}/SKILL.md`;
    if (!existsSync(file)) {
      fail(`skills/${name}`, 'directory has no SKILL.md');
      continue;
    }
    const fm = frontmatter(file);
    if (!fm) {
      fail(rel, 'no frontmatter — this skill will NOT be discoverable');
      continue;
    }
    checkScalars(rel, fm.raw);
    if (fm.fields.name !== name) fail(rel, `name "${fm.fields.name}" does not match directory "${name}"`);
    checkModel(rel, fm.fields.model);
    checkEffort(rel, fm.fields.effort);
    if (!fm.fields.description) fail(rel, 'missing required field: description');
    else if (!/^Use (when|before|after|to)/i.test(fm.fields.description)) {
      fail(rel, 'description should start with "Use when/before/after" — it states the trigger, not a table of contents');
    }
  }
}

// --- cross-references: every named agent, skill and command must exist -------
const agentNames = new Set(listDir('agents', (f) => f.endsWith('.md')).map((f) => basename(f, '.md')));
const commandNames = new Set(listDir('commands', (f) => f.endsWith('.md')).map((f) => basename(f, '.md')));
const skillNames = new Set(existsSync(skillsDir) ? readdirSync(skillsDir).filter((n) => statSync(join(skillsDir, n)).isDirectory()) : []);

for (const dir of ['commands', 'agents']) {
  for (const file of listDir(dir, (f) => f.endsWith('.md'))) {
    const rel = `${dir}/${basename(file)}`;
    const text = readFileSync(file, 'utf8');
    for (const [, name] of text.matchAll(/\*\*(backend-[a-z]+)\*\*/g)) {
      if (!agentNames.has(name)) fail(rel, `references unknown agent: ${name}`);
    }
    for (const [, name] of text.matchAll(/`([a-z0-9-]+)` skill/g)) {
      if (!skillNames.has(name)) fail(rel, `references unknown skill: ${name}`);
    }
    for (const [, name] of text.matchAll(/`\/([a-z-]+)`/g)) {
      if (!commandNames.has(name)) fail(rel, `references unknown command: /${name}`);
    }
    if (text.includes('.claude/agents/') || text.includes('/SKILL.md')) {
      fail(rel, 'refers to a file path instead of a registered name — paths do not dispatch anything');
    }
  }
}

// Skills reference other skills and agents too. Command references are not checked
// here: skills legitimately mention commands of external tools (e.g. a source-map tool).
for (const name of skillNames) {
  const file = join(skillsDir, name, 'SKILL.md');
  if (!existsSync(file)) continue;
  const rel = `skills/${name}/SKILL.md`;
  const text = readFileSync(file, 'utf8');
  for (const [, ref] of text.matchAll(/\*\*(backend-[a-z]+)\*\*/g)) {
    if (!agentNames.has(ref)) fail(rel, `references unknown agent: ${ref}`);
  }
  for (const [, ref] of text.matchAll(/`([a-z0-9-]+)` skill/g)) {
    if (!skillNames.has(ref)) fail(rel, `references unknown skill: ${ref}`);
  }
}

// --- settings.json: a syntax error disables every permission rule in it -------
const settingsPath = join(KIT, 'settings.json');
if (existsSync(settingsPath)) {
  try {
    JSON.parse(readFileSync(settingsPath, 'utf8'));
  } catch (error) {
    fail('settings.json', `invalid JSON — Claude Code ignores the file: ${error.message}`);
  }
}

// --- report -----------------------------------------------------------------
const counts = `${agentNames.size} agents, ${commandNames.size} commands, ${skillNames.size} skills`;
if (problems.length === 0) {
  console.log(`kit ok — ${counts}`);
  process.exit(0);
}
console.error(`kit has ${problems.length} problem(s) — ${counts}\n`);
for (const { file, msg } of problems) console.error(`  ${file}\n    ${msg}`);
process.exit(1);
