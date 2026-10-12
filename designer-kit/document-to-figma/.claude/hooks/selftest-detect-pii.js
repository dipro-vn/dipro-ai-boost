#!/usr/bin/env node
// Self-test cho H06 — chung minh hook that su chan, va that su cho du lieu mau di qua.
// Chay lai sau MOI lan sua detect-pii.js hoac pii-patterns.json:
//   node .claude/hooks/selftest-detect-pii.js
//
// Gate bao "khong phat hien gi" chua chung minh duoc gi: mot hook hong cung im lang.

const { execFileSync } = require('child_process');
const path = require('path');

const HOOK = path.join(__dirname, 'detect-pii.js');

const CASES = [
  // [ten, payload, exit ky vong]
  ['Email that trong Write',        { tool_name: 'Write', tool_input: { file_path: 'SPEC.md', content: 'Lien he: tanaka.taro@abc.co.jp' } }, 2],
  ['SDT VN trong Edit',             { tool_name: 'Edit',  tool_input: { file_path: 'SPEC.md', new_string: 'Hotline 0912345678' } }, 2],
  ['SDT JP',                        { tool_name: 'Write', tool_input: { file_path: 'a.md', content: 'TEL 090-1234-5678' } }, 2],
  ['So the tin dung',               { tool_name: 'Write', tool_input: { file_path: 'a.md', content: '4111 1111 1111 1111' } }, 2],
  ['AWS access key',                { tool_name: 'Write', tool_input: { file_path: 'a.md', content: 'AKIAQ7RTYUIOPASDFGHJ' } }, 2],
  ['JWT token',                     { tool_name: 'Write', tool_input: { file_path: 'a.md', content: 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dBjftJeZ4CVPmB92K27uhbUJU1p1r_wW1gFWFOEjXk' } }, 2],
  ['Connection string co password', { tool_name: 'Bash',  tool_input: { command: 'psql postgres://admin:S3cretPass@db.abc.jp/prod' } }, 2],
  ['Gan gia tri cho password',      { tool_name: 'Write', tool_input: { file_path: 'a.md', content: 'password: Tr0ub4dor&3xyz' } }, 2],
  ['Password tro toi bien moi truong', { tool_name: 'Write', tool_input: { file_path: 'a.md', content: 'password: process.env.DB_PASSWORD' } }, 0],
  ['AWS key mau trong tai lieu',    { tool_name: 'Write', tool_input: { file_path: 'a.md', content: 'AKIAIOSFODNN7EXAMPLE' } }, 0],
  ['Day PII len Figma (MCP)',       { tool_name: 'mcp__plugin_figma_figma__use_figma', tool_input: { code: 'createText("yamada@client.co.jp")' } }, 2],
  ['Day PII len Backlog (MCP)',     { tool_name: 'mcp__backlog__add_issue', tool_input: { summary: 'Loi cua user taro@abc.co.jp' } }, 2],

  ['Bo du lieu mau chuan',          { tool_name: 'Write', tool_input: { file_path: 'SPEC.md', content: 'user_a@example.com / 090-0000-0000 / Nguyen Van A' } }, 0],
  ['Placeholder password',          { tool_name: 'Write', tool_input: { file_path: 'a.md', content: 'password: <your-password>' } }, 0],
  ['Tool ngoai pham vi quet',       { tool_name: 'Read',  tool_input: { file_path: '/etc/hosts' } }, 0],
  ['File trong allowlist',          { tool_name: 'Write', tool_input: { file_path: '.claude/rules/DATA-PRIVACY.md', content: 'vi du: tanaka@abc.co.jp' } }, 0],
  ['Van ban thuong khong co PII',   { tool_name: 'Write', tool_input: { file_path: 'a.md', content: 'Man hinh dang nhap co o nhap email va mat khau' } }, 0],
];

let pass = 0, fail = 0;
console.log('# Self-test H06 — detect-pii\n');
console.log('| Ca kiem tra | Ky vong | Thuc te | Ket qua |');
console.log('|---|---|---|---|');

for (const [name, payload, want] of CASES) {
  let got = 0;
  try {
    execFileSync('node', [HOOK], { input: JSON.stringify(payload), stdio: ['pipe', 'pipe', 'pipe'] });
  } catch (e) {
    got = e.status === undefined ? -1 : e.status;
  }
  const ok = got === want;
  ok ? pass++ : fail++;
  const label = (n) => (n === 2 ? 'CHAN' : n === 0 ? 'cho qua' : 'exit ' + n);
  console.log(`| ${name} | ${label(want)} | ${label(got)} | ${ok ? 'PASS' : '**FAIL**'} |`);
}

console.log(`\n**${CASES.length} ca · ${pass} PASS · ${fail} FAIL**`);
console.log('\nLUU Y: hook chi doc TEXT. Khong quet duoc noi dung anh .png/.jpg —');
console.log('screenshot chua email that van lot qua. Chan bang quy trinh, khong bang script.');
process.exit(fail ? 1 : 0);
