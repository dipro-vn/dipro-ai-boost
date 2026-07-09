#!/usr/bin/env node
/**
 * OpenAI-compatible proxy for Claude Code CLI + static bridge for Figma plugin.
 * Replaces 9router — spawns `claude --print` instead of routing through external gateway.
 */
var http = require('http');
var https = require('https');
var fs = require('fs');
var path = require('path');
var { spawn } = require('child_process');

var PORT = Number(process.env.PROXY_PORT || 20128);
var HOST = '127.0.0.1';
var BRIDGE_DIR = path.join(__dirname, '..', 'bridge');
var DASHBOARD_DIR = path.join(__dirname, '..', 'dashboard');
var store = require('./lib/store');
var usage = require('./lib/usage');
var quota = require('./lib/quota');
var TIMEOUT_MS = Number(process.env.PROXY_TIMEOUT_MS || 300000);
var PROXY_URL = 'http://localhost:' + PORT;
var BRIDGE_URL = PROXY_URL + '/bridge.html';
var DASHBOARD_URL = PROXY_URL + '/dashboard';

function resolveClaudeBin() {
  if (process.env.CLAUDE_BIN) return { bin: process.env.CLAUDE_BIN, prefixArgs: [] };
  var cliJs = path.join(__dirname, '..', 'node_modules', '@anthropic-ai', 'claude-code', 'cli.js');
  if (fs.existsSync(cliJs)) return { bin: process.execPath, prefixArgs: [cliJs] };
  var localBin = path.join(__dirname, '..', 'node_modules', '.bin', 'claude' + (process.platform === 'win32' ? '.cmd' : ''));
  if (fs.existsSync(localBin)) return { bin: localBin, prefixArgs: [] };
  return { bin: 'claude', prefixArgs: [] };
}

var CLAUDE_SPAWN = resolveClaudeBin();

var MODEL_MAP = {
  'claude-opus-4': 'opus',
  'claude-opus-4-6': 'opus',
  'claude-opus-4-7': 'opus',
  'claude-opus-4-5-20251101': 'opus',
  'claude-sonnet-4': 'claude-sonnet-4-6',
  'claude-sonnet-4-5': 'claude-sonnet-4-6',
  'claude-sonnet-4-5-20250929': 'claude-sonnet-4-6',
  'claude-sonnet-4-6': 'claude-sonnet-4-6',
  'claude-haiku-4': 'haiku',
  'claude-haiku-4-5': 'haiku',
  'claude-haiku-4-5-20251001': 'haiku',
  opus: 'opus',
  sonnet: 'claude-sonnet-4-6',
  haiku: 'haiku',
};

var DEFAULT_MODEL = 'claude-sonnet-4-6';

function setCors(res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
}

function sendJson(res, status, body) {
  setCors(res);
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(body));
}

function readBody(req) {
  return new Promise(function (resolve, reject) {
    var chunks = [];
    req.on('data', function (c) { chunks.push(c); });
    req.on('end', function () {
      try {
        resolve(JSON.parse(Buffer.concat(chunks).toString('utf8')));
      } catch (e) {
        reject(new Error('Invalid JSON body'));
      }
    });
    req.on('error', reject);
  });
}

function stripProviderPrefix(model) {
  return String(model || DEFAULT_MODEL).replace(/^(?:cc|claude-code)\//, '');
}

function resolveCliModel(model) {
  var stripped = stripProviderPrefix(model);
  return MODEL_MAP[stripped] || MODEL_MAP[stripped.toLowerCase()] || DEFAULT_MODEL;
}

function extractText(content) {
  if (typeof content === 'string') return content;
  if (Array.isArray(content)) {
    return content
      .filter(function (b) { return b && (b.type === 'text' || b.type === 'input_text'); })
      .map(function (b) { return b.text || ''; })
      .join('\n');
  }
  return String(content || '');
}

function messagesToPrompt(messages) {
  var system = '';
  var parts = [];
  for (var i = 0; i < messages.length; i++) {
    var msg = messages[i];
    var text = extractText(msg.content);
    if (msg.role === 'system') system = text;
    else if (msg.role === 'user') parts.push(text);
    else if (msg.role === 'assistant') parts.push('<previous_response>\n' + text + '\n</previous_response>');
  }
  return { prompt: parts.join('\n\n').trim(), system: system };
}

function buildCliPrompt(prompt, system) {
  if (!system) return prompt;
  return '<system_instructions>\n' + system + '\n</system_instructions>\n\n' + prompt;
}

function callClaudeCli(prompt, system, model) {
  return new Promise(function (resolve, reject) {
    var args = CLAUDE_SPAWN.prefixArgs.concat([
      '--print',
      '--model', model,
      '--output-format', 'text',
      '--no-session-persistence',
      '--dangerously-skip-permissions',
    ]);

    var proc = spawn(CLAUDE_SPAWN.bin, args, {
      stdio: ['pipe', 'pipe', 'pipe'],
      cwd: path.join(__dirname, '..'),
      env: Object.assign({}, process.env, {
        ANTHROPIC_DEFAULT_SONNET_MODEL: DEFAULT_MODEL,
        ANTHROPIC_DEFAULT_OPUS_MODEL: 'claude-opus-4-6',
        ANTHROPIC_DEFAULT_HAIKU_MODEL: 'claude-haiku-4-5',
      }),
    });

    var stdout = '';
    var stderr = '';
    var timer = setTimeout(function () {
      proc.kill('SIGTERM');
      reject(new Error('Timeout goi Claude Code (' + (TIMEOUT_MS / 1000) + 's). Thu lai hoac tang PROXY_TIMEOUT_MS.'));
    }, TIMEOUT_MS);

    proc.stdout.on('data', function (c) {
      stdout += c.toString();
    });
    proc.stderr.on('data', function (c) {
      stderr += c.toString();
    });

    proc.on('error', function (err) {
      clearTimeout(timer);
      if (err.code === 'ENOENT') {
        reject(new Error(
          'Claude CLI khong tim thay. Chay: npm install && npm run claude:login'
        ));
      } else {
        reject(err);
      }
    });

    proc.stdin.write(buildCliPrompt(prompt, system));
    proc.stdin.end();

    proc.on('close', function (code) {
      clearTimeout(timer);
      if (code !== 0) {
        reject(new Error((stderr || stdout).trim() || ('Claude CLI exited with code ' + code)));
        return;
      }
      var text = stdout.trim();
      if (!text) reject(new Error('AI tra ve rong.'));
      else resolve(text);
    });
  });
}

function callAnthropicApi(prompt, system, modelName) {
  var apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return Promise.reject(new Error(
      'Khong co Claude CLI va khong co ANTHROPIC_API_KEY. Cai claude CLI hoac dat bien moi truong.'
    ));
  }

  return new Promise(function (resolve, reject) {
    var body = JSON.stringify({
      model: modelName,
      max_tokens: 8192,
      system: system || undefined,
      messages: [{ role: 'user', content: prompt }],
    });

    var req = https.request({
      hostname: 'api.anthropic.com',
      port: 443,
      path: '/v1/messages',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'Content-Length': Buffer.byteLength(body),
      },
    }, function (res) {
      var chunks = [];
      res.on('data', function (c) { chunks.push(c); });
      res.on('end', function () {
        var raw = Buffer.concat(chunks).toString('utf8');
        if (res.statusCode >= 400) {
          reject(new Error('Anthropic API HTTP ' + res.statusCode + ': ' + raw.slice(0, 500)));
          return;
        }
        try {
          var data = JSON.parse(raw);
          var text = (data.content || [])
            .filter(function (b) { return b.type === 'text'; })
            .map(function (b) { return b.text; })
            .join('');
          if (!text.trim()) reject(new Error('AI tra ve rong.'));
          else resolve(text.trim());
        } catch (e) {
          reject(e);
        }
      });
    });

    req.on('error', reject);
    req.setTimeout(TIMEOUT_MS, function () {
      req.destroy();
      reject(new Error('Timeout goi Anthropic API (' + (TIMEOUT_MS / 1000) + 's).'));
    });
    req.write(body);
    req.end();
  });
}

function callAi(prompt, system, requestModel) {
  var cliModel = resolveCliModel(requestModel);

  return callClaudeCli(prompt, system, cliModel);
}

function openAiCompletion(model, text, usageMeta) {
  var promptTokens = (usageMeta && usageMeta.promptTokens) || 0;
  var completionTokens = (usageMeta && usageMeta.completionTokens) || usage.estimateTokens(text);
  return {
    id: 'chatcmpl-' + Date.now(),
    object: 'chat.completion',
    created: Math.floor(Date.now() / 1000),
    model: model,
    choices: [{
      index: 0,
      message: { role: 'assistant', content: text },
      finish_reason: 'stop',
    }],
    usage: {
      prompt_tokens: promptTokens,
      completion_tokens: completionTokens,
      total_tokens: promptTokens + completionTokens,
    },
  };
}

function getBearerToken(req) {
  var auth = req.headers.authorization || req.headers.Authorization || '';
  if (auth.indexOf('Bearer ') === 0) return auth.slice(7).trim();
  return '';
}

function serveStatic(res, filePath, contentType) {
  fs.readFile(filePath, function (err, data) {
    if (err) {
      res.writeHead(404);
      res.end('Not found');
      return;
    }
    setCors(res);
    res.writeHead(200, { 'Content-Type': contentType });
    res.end(data);
  });
}

function serveBridge(req, res, filePath) {
  serveStatic(res, filePath, 'text/html; charset=utf-8');
}

function probeExisting(cb) {
  var req = http.get(PROXY_URL + '/health', function (res) {
    cb(null, res.statusCode === 200);
  });
  req.on('error', function () { cb(null, false); });
  req.setTimeout(2000, function () { req.destroy(); cb(null, false); });
}

var server = http.createServer(function (req, res) {
  var url = req.url || '/';
  var pathname = url.replace(/\?.*$/, '');

  if (req.method === 'OPTIONS') {
    setCors(res);
    res.writeHead(204);
    res.end();
    return;
  }

  if (pathname === '/' || pathname === '/bridge.html') {
    serveBridge(req, res, path.join(BRIDGE_DIR, 'bridge.html'));
    return;
  }

  if (pathname === '/dashboard' || pathname === '/dashboard/') {
    serveStatic(res, path.join(DASHBOARD_DIR, 'index.html'), 'text/html; charset=utf-8');
    return;
  }
  if (pathname.indexOf('/dashboard/') === 0) {
    var dashFile = pathname.replace('/dashboard/', '');
    if (dashFile === 'style.css') {
      serveStatic(res, path.join(DASHBOARD_DIR, 'style.css'), 'text/css; charset=utf-8');
      return;
    }
    if (dashFile === 'app.js') {
      serveStatic(res, path.join(DASHBOARD_DIR, 'app.js'), 'application/javascript; charset=utf-8');
      return;
    }
  }

  if (req.method === 'GET' && pathname === '/api/keys') {
    sendJson(res, 200, { keys: store.listKeys() });
    return;
  }
  if (req.method === 'POST' && pathname === '/api/keys') {
    readBody(req).then(function (body) {
      var key = store.createKey(body && body.name);
      sendJson(res, 200, key);
    }).catch(function (err) {
      sendJson(res, 400, { error: { message: err.message } });
    });
    return;
  }
  if (req.method === 'DELETE' && pathname.indexOf('/api/keys/') === 0) {
    store.deleteKey(pathname.slice('/api/keys/'.length));
    sendJson(res, 200, { ok: true });
    return;
  }
  if (req.method === 'GET' && pathname === '/api/usage/stats') {
    var period = (req.url.match(/[?&]period=([^&]+)/) || [])[1] || '7d';
    sendJson(res, 200, usage.getStats(period));
    return;
  }
  if (req.method === 'GET' && pathname === '/api/quota') {
    quota.getQuotaInfo().then(function (info) {
      sendJson(res, 200, info);
    }).catch(function (err) {
      sendJson(res, 500, { error: { message: err.message } });
    });
    return;
  }

  if (req.method === 'GET' && pathname === '/health') {
    sendJson(res, 200, {
      status: 'ok',
      provider: 'claude-code-cli',
      endpoint: PROXY_URL + '/v1',
      bridge: BRIDGE_URL,
      dashboard: DASHBOARD_URL,
    });
    return;
  }

  if (req.method === 'GET' && (pathname === '/v1/models' || pathname === '/v1')) {
    var now = Math.floor(Date.now() / 1000);
    sendJson(res, 200, {
      object: 'list',
      data: Object.keys(MODEL_MAP).filter(function (k) { return k.indexOf('claude-') === 0; }).map(function (id) {
        return { id: 'cc/' + id, object: 'model', owned_by: 'claude-code', created: now };
      }),
    });
    return;
  }

  if (req.method === 'POST' && pathname === '/v1/chat/completions') {
    var token = getBearerToken(req);
    if (!store.validateKey(token)) {
      sendJson(res, 401, { error: { message: 'Invalid API key' } });
      return;
    }
    readBody(req).then(function (body) {
      if (!body.messages || !body.messages.length) {
        sendJson(res, 400, { error: { message: 'messages is required' } });
        return;
      }
      var parsed = messagesToPrompt(body.messages);
      if (!parsed.prompt) {
        sendJson(res, 400, { error: { message: 'user message is required' } });
        return;
      }
      var model = body.model || 'cc/claude-sonnet-4-6';
      var promptTokens = usage.estimateTokens((parsed.system || '') + parsed.prompt);
      var t0 = Date.now();
      usage.startRequest({ model: model });
      console.log('[proxy] chat request model=' + model + ' promptChars=' + parsed.prompt.length);
      return callAi(parsed.prompt, parsed.system, model).then(function (text) {
        var durationMs = Date.now() - t0;
        var completionTokens = usage.estimateTokens(text);
        usage.endRequest({
          model: model,
          status: 'ok',
          durationMs: durationMs,
          promptTokens: promptTokens,
          completionTokens: completionTokens,
          promptChars: parsed.prompt.length,
          responseChars: text.length,
        });
        console.log('[proxy] chat done in ' + (durationMs / 1000).toFixed(1) + 's, chars=' + text.length);
        sendJson(res, 200, openAiCompletion(model, text, { promptTokens: promptTokens, completionTokens: completionTokens }));
      });
    }).catch(function (err) {
      usage.endRequest({
        model: 'unknown',
        status: 'error',
        error: err.message || String(err),
      });
      console.error('[proxy] chat error:', err.message || err);
      sendJson(res, 500, { error: { message: err.message || String(err) } });
    });
    return;
  }

  res.writeHead(404);
  res.end('Not found');
});

server.on('error', function (err) {
  if (err.code === 'EADDRINUSE') {
    probeExisting(function (_, ok) {
      if (ok) {
        console.log('AI proxy da chay san: ' + PROXY_URL);
        process.exit(0);
      }
      console.error('Port ' + PORT + ' dang bi chiem boi process khac.');
      console.error('Dung process do hoac chay: lsof -i :' + PORT);
      process.exit(1);
    });
    return;
  }
  console.error(err.message || err);
  process.exit(1);
});

function claudeLoggedIn() {
  var acc = quota.readClaudeAccount();
  return !!(acc && acc.emailAddress);
}

// Tự chạy login khi chưa auth (mở trình duyệt để Authorize), thay vì chỉ in lệnh.
function ensureClaudeLogin() {
  if (process.env.ANTHROPIC_API_KEY) {
    console.log('Auth: dung ANTHROPIC_API_KEY (bo qua login OAuth).');
    return;
  }
  if (claudeLoggedIn()) {
    var acc = quota.readClaudeAccount();
    console.log('Auth: da dang nhap Claude Code (' + (acc.emailAddress || '') + ').');
    return;
  }

  // Cần TTY để chạy OAuth interactive. Khi chạy nền (vd. qua setup.sh với stdin
  // /dev/null) thì bỏ qua — bên gọi tự lo login.
  if (!process.stdin.isTTY) {
    console.log('Auth: chua dang nhap Claude Code. Chay: npm run claude:login (hoac dat ANTHROPIC_API_KEY).');
    return;
  }

  console.log('Auth: chua dang nhap — dang mo trinh duyet de Authorize...');
  var args = CLAUDE_SPAWN.prefixArgs.concat(['auth', 'login']);
  var proc;
  try {
    proc = spawn(CLAUDE_SPAWN.bin, args, {
      stdio: 'inherit',
      cwd: path.join(__dirname, '..'),
    });
  } catch (e) {
    console.log('Auth: khong chay duoc login tu dong (' + (e.message || e) + '). Chay tay: npm run claude:login');
    return;
  }
  proc.on('error', function (e) {
    console.log('Auth: khong chay duoc login tu dong (' + (e.message || e) + '). Chay tay: npm run claude:login');
  });
  proc.on('exit', function (code) {
    if (claudeLoggedIn()) {
      var a = quota.readClaudeAccount();
      console.log('Auth: dang nhap thanh cong (' + (a.emailAddress || '') + '). Proxy san sang.');
    } else {
      console.log('Auth: login chua hoan tat (exit ' + code + '). Chay lai: npm run claude:login');
    }
  });
}

server.listen(PORT, HOST, function () {
  console.log('Claude Code proxy: ' + PROXY_URL + '/v1');
  console.log('Dashboard:         ' + DASHBOARD_URL);
  console.log('Bridge iframe:     ' + BRIDGE_URL);
  console.log('AI timeout:        ' + (TIMEOUT_MS / 1000) + 's (PROXY_TIMEOUT_MS)');
  ensureClaudeLogin();
});
