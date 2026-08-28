#!/usr/bin/env node
// H05 — chặn Write/Edit khi content chứa hardcoded secret.
// Enforce: PreToolUse matcher "Write|Edit" trong .claude/settings.json.
// Rules gốc: rules/security-rules.md + POLICIES.md §3.

const fs = require('fs');

try {
  const payload = JSON.parse(fs.readFileSync(0, 'utf8'));
  const input = payload.tool_input || {};
  const content = input.content || input.new_string || '';

  if (!content) process.exit(0);

  const patterns = [
    { name: 'AWS Access Key ID', re: /AKIA[0-9A-Z]{16}/ },
    {
      name: 'AWS Secret Access Key',
      re: /aws_secret_access_key\s*=\s*['"][A-Za-z0-9/+=]{40}['"]/i
    },
    {
      name: 'API key (OpenAI/Anthropic/Stripe style)',
      re: /\b(sk|pk)-[A-Za-z0-9_-]{20,}\b/
    },
    { name: 'GitHub Personal Access Token', re: /\bghp_[A-Za-z0-9]{36}\b/ },
    { name: 'GitHub OAuth Token', re: /\bgho_[A-Za-z0-9]{36}\b/ },
    { name: 'Slack Bot Token', re: /\bxox[baprs]-[A-Za-z0-9-]{10,}\b/ },
    {
      name: 'JWT literal',
      re: /eyJ[A-Za-z0-9\-_=]{10,}\.eyJ[A-Za-z0-9\-_=]{10,}\.[A-Za-z0-9\-_.+/=]{10,}/
    },
    {
      name: 'Postgres connection string với password',
      re: /postgres(?:ql)?:\/\/[^:\s'"]+:[^@\s'"]+@/
    },
    {
      name: 'MySQL connection string với password',
      re: /mysql:\/\/[^:\s'"]+:[^@\s'"]+@/
    },
    {
      name: 'MongoDB connection string với credentials',
      re: /mongodb(?:\+srv)?:\/\/[^:\s'"]+:[^@\s'"]+@/
    },
    {
      name: 'Private key block',
      re: /-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----/
    }
  ];

  const hit = patterns.find((p) => p.re.test(content));

  if (hit) {
    console.error(
      `BLOCKED by H05: phát hiện "${hit.name}" trong nội dung Write/Edit.\n` +
        `Fix: dùng AWS Parameter Store hoặc env var (xem rules/security-rules.md).\n` +
        `Nếu là test/example không dùng thật → dùng placeholder rõ ràng (VD "AKIAIOSFODNN7EXAMPLE").`
    );
    process.exit(2);
  }

  process.exit(0);
} catch (e) {
  console.error(`H05 hook internal error: ${e.message}`);
  process.exit(0);
}
