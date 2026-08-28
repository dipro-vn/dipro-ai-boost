#!/usr/bin/env node
// H02 + H03 + H04 — chặn bash command nguy hiểm.
// Enforce: PreToolUse matcher "Bash" trong .claude/settings.json.
// Rules gốc: rules/git-workflow.md + POLICIES.md §3 + rules/POLICY.md.

const fs = require('fs');

try {
  const payload = JSON.parse(fs.readFileSync(0, 'utf8'));
  const cmd = (payload.tool_input && payload.tool_input.command) || '';

  if (!cmd) process.exit(0);

  const rules = [
    {
      id: 'H02',
      re: /git\s+push\s+(?=[^|;&]*--force)(?=[^|;&]*\b(main|develop|master|release\/[\w.-]+)\b)/,
      msg: 'force-push lên protected branch (main/develop/master/release/*) — cấm bởi rules/git-workflow.md'
    },
    {
      id: 'H03',
      re: /--no-verify\b|--no-gpg-sign\b|-c\s+commit\.gpgsign=false/,
      msg: 'bypass git hooks/signing (--no-verify / --no-gpg-sign) — cấm bởi POLICIES.md §3'
    },
    {
      id: 'H04',
      re: /\brm\s+-[rRf]{1,2}\s+(\/(?:\s|$)|~(?:\s|$|\/)|\$HOME|\*(?:\s|$))/,
      msg: 'destructive rm -rf trên root/home/wildcard — cấm bởi rules/POLICY.md'
    }
  ];

  for (const r of rules) {
    if (r.re.test(cmd)) {
      console.error(
        `BLOCKED by ${r.id}: ${r.msg}\n` + `Command: ${cmd}`
      );
      process.exit(2);
    }
  }

  process.exit(0);
} catch (e) {
  console.error(`guard-bash hook internal error: ${e.message}`);
  process.exit(0);
}
