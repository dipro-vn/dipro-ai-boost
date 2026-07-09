#!/usr/bin/env node
/**
 * Run Auto AI selection step (same prompt as code.js) on scan JSON from use_figma.
 * Usage: node scripts/run-auto-ai-remote.js < scan.json
 */
const http = require('http');
const https = require('https');

const ENDPOINT = (process.env.ROUTER_ENDPOINT || 'http://localhost:20128/v1').replace(/\/+$/, '');
const MODEL = process.env.ROUTER_MODEL || 'cc/claude-sonnet-4-6';

const AUTO_SELECT_SYSTEM =
  'You are a UI Basic Design numbering assistant.\n\n' +
  'Select only UI elements that should be described in a Basic Design document.\n\n' +
  'Select: screen title, section title, tab, breadcrumb item, form label, input, select, ' +
  'checkbox, radio, button, action icon, table column header, table row header, menu item, ' +
  'pagination control, search condition label, output field label.\n\n' +
  'Do NOT select: breadcrumb separators, pure values (numbers, dates, money, sample data), ' +
  'table body cell values, decorative text, duplicate child text when parent should be selected.\n\n' +
  'Table/seat map: select column headers and ONE representative for repeated seat buttons (seat map grid), not every A1-E10.\n\n' +
  'Action rules (MUST select):\n' +
  '- Footer/header buttons: Cancel, Save, Apply, Confirm payment, Back links.\n' +
  '- Quantity +/- buttons, Add participant button.\n' +
  '- For identical row/seat action icons, select ONE topmost representative per icon type.\n\n' +
  'Button/input: prefer container/parent; do not select parent and child duplicate.\n\n' +
  'Output JSON only:\n' +
  '{"items":[{"number":1,"nodeId":"...","label":"...","itemType":"...","reason":"...","confidence":0.95}],"ignored":[{"nodeId":"...","reason":"..."}]}';

function readStdin() {
  return new Promise(function(resolve, reject) {
    var chunks = [];
    process.stdin.on('data', function(c) { chunks.push(c); });
    process.stdin.on('end', function() {
      try { resolve(JSON.parse(Buffer.concat(chunks).toString('utf8'))); }
      catch (e) { reject(e); }
    });
    process.stdin.on('error', reject);
  });
}

function formatLine(c, idx) {
  var line = (idx + 1) + '. nodeId=' + c.nodeId + ' [' + c.type + '] text="' + (c.text || c.label || c.name) + '"';
  line += ' roleHint=' + (c.roleHint || '');
  if (c.isAction) line += ' action=must_select';
  line += ' @' + (c.pos || '');
  return line;
}

function postJson(url, body) {
  return new Promise(function(resolve, reject) {
    var u = new URL(url);
    var lib = u.protocol === 'https:' ? https : http;
    var data = JSON.stringify(body);
    var req = lib.request({
      hostname: u.hostname,
      port: u.port,
      path: u.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer local',
        'Content-Length': Buffer.byteLength(data),
      },
    }, function(res) {
      var chunks = [];
      res.on('data', function(c) { chunks.push(c); });
      res.on('end', function() {
        var raw = Buffer.concat(chunks).toString('utf8');
        if (res.statusCode >= 400) return reject(new Error('HTTP ' + res.statusCode + ': ' + raw.slice(0, 500)));
        try { resolve(JSON.parse(raw)); } catch (e) { reject(e); }
      });
    });
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

async function main() {
  var scan = await readStdin();
  var selectable = (scan.selectable || []).slice(0, 140);
  var user =
    'Frame context:\n' +
    '- name: "' + (scan.frameName || '') + '"\n' +
    '- size: ' + (scan.frameSize ? scan.frameSize.width + 'x' + scan.frameSize.height : '') + '\n' +
    '- selectable: ' + selectable.length + ' (CHI duoc chon tu list nay)\n\n' +
    '=== SELECTABLE ===\n' +
    selectable.map(formatLine).join('\n') + '\n\n' +
    'Task: Select UI items to number for Basic Design. Top-to-bottom, left-to-right. ' +
    'MUST include action=must_select items. One representative per repeated seat/delete icon type. ' +
    'Return strict JSON. Minimum confidence 0.75.';

  console.error('Calling Claude Code proxy (' + MODEL + ') with ' + selectable.length + ' candidates...');
  var data = await postJson(ENDPOINT + '/chat/completions', {
    model: MODEL,
    max_tokens: 3500,
    stream: false,
    messages: [
      { role: 'system', content: AUTO_SELECT_SYSTEM },
      { role: 'user', content: user },
    ],
  });

  var text = '';
  if (data.choices && data.choices[0] && data.choices[0].message) {
    text = data.choices[0].message.content || '';
  }
  text = text.replace(/```json|```/g, '').trim();
  var start = text.indexOf('{');
  var end = text.lastIndexOf('}');
  var parsed;
  try {
    parsed = JSON.parse(text.slice(start, end + 1));
  } catch (e) {
    console.error('AI raw response (first 2000 chars):', text.slice(0, 2000));
    throw e;
  }

  var map = {};
  selectable.forEach(function(c) { map[c.nodeId] = c; });

  var items = (parsed.items || []).filter(function(it) {
    return it.nodeId && map[it.nodeId] && (it.confidence == null || it.confidence >= 0.75);
  });

  items.sort(function(a, b) {
    var na = map[a.nodeId], nb = map[b.nodeId];
    if (!na || !nb) return 0;
    return na.y - nb.y || na.x - nb.x;
  });
  items.forEach(function(it, i) { it.number = String(i + 1); });

  console.log(JSON.stringify({
    frameName: scan.frameName,
    method: 'Auto AI (hybrid + Claude Code) — remote test',
    totalScanned: scan.totalScanned,
    selectableCount: scan.selectableCount,
    selectedCount: items.length,
    items: items.map(function(it) {
      var orig = map[it.nodeId] || {};
      return {
        number: it.number,
        nodeId: it.nodeId,
        label: it.label || orig.text,
        itemType: it.itemType || orig.roleHint,
        confidence: it.confidence,
        reason: it.reason,
        isAction: !!orig.isAction,
      };
    }),
  }, null, 2));
}

main().catch(function(err) {
  console.error(err.message || err);
  process.exit(1);
});
