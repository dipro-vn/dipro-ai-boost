var store = require('./store');

var activeRequest = null;

function estimateTokens(text) {
  return Math.max(1, Math.ceil(String(text || '').length / 4));
}

function startRequest(meta) {
  activeRequest = {
    id: meta.id || String(Date.now()),
    model: meta.model || 'unknown',
    startedAt: Date.now(),
    source: meta.source || 'proxy',
  };
  return activeRequest;
}

function endRequest(meta) {
  var started = activeRequest;
  activeRequest = null;
  var durationMs = meta.durationMs != null ? meta.durationMs : 0;
  if (started && !meta.durationMs) durationMs = Date.now() - started.startedAt;

  var record = {
    timestamp: new Date().toISOString(),
    model: meta.model || (started && started.model) || 'unknown',
    status: meta.status || 'ok',
    durationMs: durationMs,
    promptTokens: meta.promptTokens || 0,
    completionTokens: meta.completionTokens || 0,
    totalTokens: (meta.promptTokens || 0) + (meta.completionTokens || 0),
    promptChars: meta.promptChars || 0,
    responseChars: meta.responseChars || 0,
    error: meta.error || '',
    source: meta.source || (started && started.source) || 'proxy',
  };
  store.addUsageRecord(record);
  return record;
}

function periodStart(period) {
  var now = Date.now();
  if (period === 'today') {
    var d = new Date();
    d.setHours(0, 0, 0, 0);
    return d.getTime();
  }
  if (period === '24h') return now - 86400000;
  if (period === '7d') return now - 7 * 86400000;
  if (period === '30d') return now - 30 * 86400000;
  return 0;
}

function getStats(period) {
  var since = periodStart(period || '7d');
  var data = store.loadUsage();
  var requests = (data.requests || []).filter(function (r) {
    return new Date(r.timestamp).getTime() >= since;
  });

  var stats = {
    period: period || '7d',
    totalRequests: 0,
    totalPromptTokens: 0,
    totalCompletionTokens: 0,
    totalTokens: 0,
    errorCount: 0,
    avgDurationMs: 0,
    byModel: {},
    recentRequests: [],
  };

  var durationSum = 0;
  requests.forEach(function (r) {
    stats.totalRequests += 1;
    stats.totalPromptTokens += r.promptTokens || 0;
    stats.totalCompletionTokens += r.completionTokens || 0;
    stats.totalTokens += r.totalTokens || ((r.promptTokens || 0) + (r.completionTokens || 0));
    if (r.status === 'error') stats.errorCount += 1;
    durationSum += r.durationMs || 0;

    var m = r.model || 'unknown';
    if (!stats.byModel[m]) {
      stats.byModel[m] = { requests: 0, promptTokens: 0, completionTokens: 0 };
    }
    stats.byModel[m].requests += 1;
    stats.byModel[m].promptTokens += r.promptTokens || 0;
    stats.byModel[m].completionTokens += r.completionTokens || 0;
  });

  if (stats.totalRequests) stats.avgDurationMs = Math.round(durationSum / stats.totalRequests);
  stats.recentRequests = requests.slice(-20).reverse();
  stats.activeRequest = activeRequest;
  return stats;
}

module.exports = {
  estimateTokens: estimateTokens,
  startRequest: startRequest,
  endRequest: endRequest,
  getStats: getStats,
};
