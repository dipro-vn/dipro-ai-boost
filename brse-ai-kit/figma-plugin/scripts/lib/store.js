var fs = require('fs');
var path = require('path');
var crypto = require('crypto');

var DATA_DIR = path.join(__dirname, '..', '..', '.proxy-data');
var KEYS_FILE = path.join(DATA_DIR, 'keys.json');
var USAGE_FILE = path.join(DATA_DIR, 'usage.json');

function ensureDir() {
  if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
}

function readJson(file, fallback) {
  ensureDir();
  try {
    if (!fs.existsSync(file)) return fallback;
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch (e) {
    return fallback;
  }
}

function writeJson(file, data) {
  ensureDir();
  fs.writeFileSync(file, JSON.stringify(data, null, 2), 'utf8');
}

function loadKeys() {
  return readJson(KEYS_FILE, { keys: [] });
}

function saveKeys(data) {
  writeJson(KEYS_FILE, data);
}

function generateKey() {
  return 'bd_' + crypto.randomBytes(24).toString('hex');
}

function listKeys() {
  return loadKeys().keys.filter(function (k) { return k.isActive !== false; });
}

function createKey(name) {
  var data = loadKeys();
  var key = {
    id: crypto.randomUUID(),
    key: generateKey(),
    name: name || 'Default',
    createdAt: new Date().toISOString(),
    isActive: true,
  };
  data.keys.push(key);
  saveKeys(data);
  return key;
}

function deleteKey(id) {
  var data = loadKeys();
  data.keys = data.keys.map(function (k) {
    if (k.id === id) return Object.assign({}, k, { isActive: false });
    return k;
  });
  saveKeys(data);
}

function validateKey(token) {
  if (!token || token === 'local' || token === '9router') return true;
  var keys = listKeys();
  if (!keys.length) return true;
  return keys.some(function (k) { return k.key === token; });
}

function loadUsage() {
  return readJson(USAGE_FILE, { requests: [], daily: {} });
}

function saveUsage(data) {
  var requests = (data.requests || []).slice(-500);
  writeJson(USAGE_FILE, { requests: requests, daily: data.daily || {} });
}

function dateKey(d) {
  return d.toISOString().slice(0, 10);
}

function addUsageRecord(record) {
  var data = loadUsage();
  data.requests = data.requests || [];
  data.daily = data.daily || {};
  data.requests.push(record);

  var dk = dateKey(new Date(record.timestamp));
  if (!data.daily[dk]) {
    data.daily[dk] = { requests: 0, promptTokens: 0, completionTokens: 0, errors: 0 };
  }
  var day = data.daily[dk];
  day.requests += 1;
  day.promptTokens += record.promptTokens || 0;
  day.completionTokens += record.completionTokens || 0;
  if (record.status === 'error') day.errors += 1;

  saveUsage(data);
  return record;
}

module.exports = {
  DATA_DIR: DATA_DIR,
  listKeys: listKeys,
  createKey: createKey,
  deleteKey: deleteKey,
  validateKey: validateKey,
  loadUsage: loadUsage,
  addUsageRecord: addUsageRecord,
  generateKey: generateKey,
};
