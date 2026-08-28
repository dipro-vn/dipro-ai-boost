#!/usr/bin/env node
// H01 — chặn Read đối với secret files.
// Nguồn danh sách: .claude/config/restricted-paths.json (dùng chung với rules/SECURITY.md).
// Enforce: PreToolUse matcher "Read" trong .claude/settings.json.

const fs = require('fs');
const path = require('path');

try {
  const payload = JSON.parse(fs.readFileSync(0, 'utf8'));
  const filePath = (payload.tool_input && payload.tool_input.file_path) || '';

  if (!filePath) process.exit(0);

  const cfgPath = path.join(__dirname, '..', 'config', 'restricted-paths.json');
  const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));

  const allow = (cfg.allowExceptions || []).map((r) => new RegExp(r));
  if (allow.some((r) => r.test(filePath))) process.exit(0);

  const deny = (cfg.denyReadPatterns || []).map((r) => new RegExp(r));
  const hit = deny.find((r) => r.test(filePath));

  if (hit) {
    console.error(
      `BLOCKED by H01: "${filePath}" match restricted pattern ${hit}.\n` +
        `Nguồn: .claude/config/restricted-paths.json (đồng bộ với rules/SECURITY.md).\n` +
        `Nếu file này thực sự an toàn (template/example) → thêm vào allowExceptions.`
    );
    process.exit(2);
  }

  process.exit(0);
} catch (e) {
  console.error(`H01 hook internal error: ${e.message}`);
  process.exit(0);
}
