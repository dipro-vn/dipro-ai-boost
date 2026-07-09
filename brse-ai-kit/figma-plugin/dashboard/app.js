(function () {
  var TITLES = { overview: 'Overview', endpoint: 'Endpoint & Keys', usage: 'Usage', quota: 'Quota Tracker' };

  function $(id) { return document.getElementById(id); }
  function fmt(n) { return (n || 0).toLocaleString(); }
  function fmtTime(iso) {
    try { return new Date(iso).toLocaleString(); } catch (e) { return iso; }
  }
  function fmtMs(ms) {
    if (!ms) return '—';
    if (ms < 1000) return ms + 'ms';
    return (ms / 1000).toFixed(1) + 's';
  }

  function toast(msg) {
    var el = $('toast');
    el.textContent = msg;
    el.classList.add('show');
    setTimeout(function () { el.classList.remove('show'); }, 2200);
  }

  function api(path, opts) {
    return fetch(path, opts).then(function (r) {
      return r.json().then(function (j) {
        if (!r.ok) throw new Error((j.error && j.error.message) || j.message || 'Request failed');
        return j;
      });
    });
  }

  function switchTab(tab) {
    document.querySelectorAll('.nav-item').forEach(function (b) {
      b.classList.toggle('active', b.dataset.tab === tab);
    });
    document.querySelectorAll('.tab-panel').forEach(function (p) {
      p.classList.toggle('active', p.id === 'tab-' + tab);
    });
    $('page-title').textContent = TITLES[tab] || tab;
    if (tab === 'usage') loadUsage();
    if (tab === 'quota') loadQuota();
    if (tab === 'endpoint') loadEndpoint();
  }

  function loadHealth() {
    return api('/health').then(function (h) {
      $('status-dot').className = 'status-dot ok';
      $('status-label').textContent = 'Proxy online';
      $('ov-endpoint').textContent = h.endpoint || 'http://localhost:20128/v1';
      return h;
    }).catch(function () {
      $('status-dot').className = 'status-dot err';
      $('status-label').textContent = 'Offline';
    });
  }

  function loadOverview() {
    return api('/api/usage/stats?period=today').then(function (s) {
      $('ov-requests').textContent = fmt(s.totalRequests);
      $('ov-tokens').textContent = fmt(s.totalTokens);
      $('ov-latency').textContent = fmtMs(s.avgDurationMs);
      $('ov-errors').textContent = fmt(s.errorCount);
    });
  }

  function loadEndpoint() {
    return loadHealth().then(function (h) {
      $('endpoint-url').value = h.endpoint || 'http://localhost:20128/v1';
      return api('/v1/models');
    }).then(function (m) {
      var el = $('models-list');
      el.innerHTML = '';
      (m.data || []).forEach(function (model) {
        var tag = document.createElement('span');
        tag.className = 'tag';
        tag.textContent = model.id;
        el.appendChild(tag);
      });
      return loadKeys();
    });
  }

  function loadKeys() {
    return api('/api/keys').then(function (data) {
      var tbody = $('keys-list');
      tbody.innerHTML = '';
      (data.keys || []).forEach(function (k) {
        var tr = document.createElement('tr');
        tr.innerHTML =
          '<td>' + (k.name || 'Key') + '</td>' +
          '<td><code class="key-mono">' + k.key + '</code></td>' +
          '<td>' + fmtTime(k.createdAt) + '</td>' +
          '<td><button class="btn btn-sm btn-danger" data-del="' + k.id + '">delete</button></td>';
        tbody.appendChild(tr);
      });
      tbody.querySelectorAll('[data-del]').forEach(function (btn) {
        btn.onclick = function () {
          if (!confirm('Xóa API key này?')) return;
          api('/api/keys/' + btn.dataset.del, { method: 'DELETE' }).then(loadKeys);
        };
      });
    });
  }

  function loadUsage() {
    var period = $('usage-period').value;
    return api('/api/usage/stats?period=' + period).then(function (s) {
      $('us-requests').textContent = fmt(s.totalRequests);
      $('us-prompt').textContent = fmt(s.totalPromptTokens);
      $('us-completion').textContent = fmt(s.totalCompletionTokens);
      $('us-errors').textContent = fmt(s.errorCount);

      var byModel = $('usage-by-model');
      byModel.innerHTML = '';
      Object.keys(s.byModel || {}).forEach(function (model) {
        var row = s.byModel[model];
        var tr = document.createElement('tr');
        tr.innerHTML = '<td><code>' + model + '</code></td><td>' + row.requests +
          '</td><td>' + fmt(row.promptTokens) + '</td><td>' + fmt(row.completionTokens) + '</td>';
        byModel.appendChild(tr);
      });

      var recent = $('usage-recent');
      recent.innerHTML = '';
      (s.recentRequests || []).forEach(function (r) {
        var tr = document.createElement('tr');
        var st = r.status === 'ok' ? '<span class="status-ok">ok</span>' : '<span class="status-err">error</span>';
        tr.innerHTML = '<td>' + fmtTime(r.timestamp) + '</td><td><code>' + r.model +
          '</code></td><td>' + fmt(r.totalTokens) + '</td><td>' + fmtMs(r.durationMs) +
          '</td><td>' + st + '</td>';
        recent.appendChild(tr);
      });
    });
  }

  function loadQuota() {
    return api('/api/quota').then(function (q) {
      var c = q.connection || {};
      $('quota-name').textContent = c.name || 'Claude Code';
      $('quota-email').textContent = c.email
        ? (c.displayName || '') + ' · ' + c.email + (c.organizationName ? ' · ' + c.organizationName : '')
        : 'Chưa đăng nhập';
      var badge = $('quota-badge');
      badge.textContent = c.connected ? 'Connected' : 'Disconnected';
      badge.className = 'badge ' + (c.connected ? 'ok' : 'err');

      var grid = $('quota-bars');
      grid.innerHTML = '';
      (q.quotas || []).forEach(function (quota) {
        var remaining = quota.remaining != null ? quota.remaining : (
          quota.unlimited ? 100 : (quota.total ? Math.round((quota.total - quota.used) / quota.total * 100) : 0)
        );
        var color = remaining > 70 ? 'green' : remaining >= 30 ? 'yellow' : 'red';
        var card = document.createElement('div');
        card.className = 'quota-card';
        card.innerHTML =
          '<h3>' + quota.name + '</h3>' +
          '<div class="quota-bar"><div class="quota-fill ' + color + '" style="width:' + Math.min(100, remaining) + '%"></div></div>' +
          '<div class="quota-meta"><span>' + fmt(quota.used) + ' / ' + (quota.unlimited ? '∞' : fmt(quota.total)) + '</span>' +
          '<span>' + remaining + '% left</span></div>' +
          (quota.note ? '<p class="hint">' + quota.note + '</p>' : '');
        grid.appendChild(card);
      });
      $('quota-message').textContent = q.message || '';
    });
  }

  document.querySelectorAll('.nav-item').forEach(function (btn) {
    btn.onclick = function () { switchTab(btn.dataset.tab); };
  });

  $('refresh-btn').onclick = function () {
    loadHealth();
    loadOverview();
    var active = document.querySelector('.nav-item.active');
    if (active) switchTab(active.dataset.tab);
    toast('Đã refresh');
  };

  $('usage-period').onchange = loadUsage;

  $('create-key-btn').onclick = function () {
    var name = prompt('Tên API key:', 'Figma Plugin');
    if (!name) return;
    api('/api/keys', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name }),
    }).then(function (k) {
      toast('Key created — copy ngay');
      loadKeys();
    }).catch(function (e) { toast(e.message); });
  };

  document.querySelectorAll('[data-copy]').forEach(function (btn) {
    btn.onclick = function () {
      var input = $(btn.dataset.copy);
      navigator.clipboard.writeText(input.value).then(function () { toast('Copied'); });
    };
  });

  loadHealth();
  loadOverview();
  setInterval(function () {
    loadHealth();
    if (document.querySelector('#tab-overview.active')) loadOverview();
  }, 15000);
})();
