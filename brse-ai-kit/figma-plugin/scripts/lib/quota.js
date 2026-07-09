var fs = require('fs');
var path = require('path');
var os = require('os');
var { spawn } = require('child_process');
var usage = require('./usage');

var CLAUDE_JSON = path.join(os.homedir(), '.claude.json');

function readClaudeAccount() {
  try {
    if (!fs.existsSync(CLAUDE_JSON)) return null;
    var data = JSON.parse(fs.readFileSync(CLAUDE_JSON, 'utf8'));
    return data.oauthAccount || null;
  } catch (e) {
    return null;
  }
}

function resolveClaudeBin() {
  var localJs = path.join(__dirname, '..', '..', 'node_modules', '@anthropic-ai', 'claude-code', 'cli.js');
  if (fs.existsSync(localJs)) return { bin: process.execPath, args: [localJs, '--version'] };
  var localBin = path.join(__dirname, '..', '..', 'node_modules', '.bin', 'claude');
  if (fs.existsSync(localBin)) return { bin: localBin, args: ['--version'] };
  return { bin: 'claude', args: ['--version'] };
}

function checkCliInstalled() {
  return new Promise(function (resolve) {
    var cfg = resolveClaudeBin();
    var proc = spawn(cfg.bin, cfg.args, { stdio: ['ignore', 'pipe', 'pipe'] });
    var out = '';
    proc.stdout.on('data', function (c) { out += c.toString(); });
    proc.on('close', function (code) {
      resolve({ ok: code === 0, version: out.trim() });
    });
    proc.on('error', function () {
      resolve({ ok: false, version: '' });
    });
    setTimeout(function () {
      try { proc.kill('SIGTERM'); } catch (e) {}
      resolve({ ok: false, version: '' });
    }, 5000);
  });
}

function localProxyQuotas(period) {
  var stats = usage.getStats(period || 'today');
  return [
    {
      name: 'Requests (' + (period || 'today') + ')',
      used: stats.totalRequests,
      total: 0,
      unlimited: true,
      remaining: 100,
    },
    {
      name: 'Est. tokens (' + (period || 'today') + ')',
      used: stats.totalTokens,
      total: 0,
      unlimited: true,
      remaining: 100,
    },
  ];
}

async function getQuotaInfo() {
  var account = readClaudeAccount();
  var cli = await checkCliInstalled();
  var todayStats = usage.getStats('today');

  var connection = {
    id: 'claude-code-local',
    provider: 'claude',
    name: 'Claude Code',
    connected: !!(account && account.emailAddress) && cli.ok,
    email: account && account.emailAddress,
    displayName: account && account.displayName,
    organizationName: account && account.organizationName,
    cliVersion: cli.version,
    cliInstalled: cli.ok,
  };

  var quotas = [];
  if (connection.connected) {
    quotas.push({
      name: 'session (5h)',
      used: 0,
      total: 100,
      remaining: 100,
      resetAt: null,
      note: 'Quota Claude subscription — xem chi tiet tai claude.ai/settings/usage',
    });
    quotas.push({
      name: 'weekly (7d)',
      used: 0,
      total: 100,
      remaining: 100,
      resetAt: null,
      note: 'Cap nhat quota day du can OAuth token (nhu 9router Providers)',
    });
  }

  localProxyQuotas('today').forEach(function (q) { quotas.push(q); });

  return {
    plan: connection.connected ? 'Claude Code (subscription)' : 'Not connected',
    connection: connection,
    quotas: quotas,
    message: connection.connected
      ? null
      : 'Chua dang nhap Claude Code. Chay: npm run claude:login',
    localUsage: todayStats,
  };
}

module.exports = {
  getQuotaInfo: getQuotaInfo,
  readClaudeAccount: readClaudeAccount,
};
