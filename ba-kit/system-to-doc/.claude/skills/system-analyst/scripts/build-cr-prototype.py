#!/usr/bin/env python3
# build-cr-prototype.py — HTML viewer cho CR-3 màn đề xuất.
#
# BẮT BUỘC chạy SAU bước 6 Figma CR-3 + 6a export PNG. HTML đóng gói: ảnh thật từ Figma +
# overlay số item + panel bên phải (search · chips · cards) — format mượn từ ES-Station
# `screen-design-doc`. Mục đích: khách Nhật không có tài khoản Figma mở xem được offline.
#
# TEMPLATE CHUẨN: xem `../../../sys-agent/figma/sample_html.md` — bảng phân tích 7 chiều,
# CSS tokens, overlay số + panel pattern. HTML sinh ra phải khớp thước đo §6 của sample_html.
#
# Usage:
#   python3 build-cr-prototype.py \
#     --cr-json <ver>/_internal/cr.json \
#     --screens-dir <ver>/_internal/screens \
#     --out <ver>/CR-<id>_screens.html \
#     [--figma-url https://figma.com/design/<fileKey>/...] \
#     [--items-json <ver>/_internal/cr-figma-items.json]  # ref_uniq → items[{n,label,ax,ay,w,h,kind,desc}]
#
# Overlay số chỉ hiện khi item có `ax, ay, w, h` (toạ độ trên mockup gốc). Script tự tính
# scale theo kích thước ảnh render thực tế. Không có pos → panel vẫn hiển thị, không overlay.
import argparse, base64, html, json, os, re, sys

CHG_LABEL = {"NEW": "Mới", "UPD": "Cập nhật", "DEL": "Xoá", "AS-IS": "Giữ nguyên", "IMPACT": "Ảnh hưởng"}

# Noise labels — bỏ khi extract từ Figma (tên internal của BA/Designer)
NOISE_LABELS = {"label-text", "chg-label", "container", "text", "icon", "spacer", "divider", "row", "col"}


def esc(s):
    return html.escape(str(s or ""), quote=True)


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def embed_image(path):
    try:
        with open(path, "rb") as f:
            b = base64.b64encode(f.read()).decode("ascii")
        return "data:image/png;base64," + b
    except OSError:
        return None


def figma_link(base, node_id):
    if not base or not node_id:
        return None
    sep = "&" if "?" in base else "?"
    return "%s%snode-id=%s" % (base, sep, node_id.replace(":", "-"))


def classify_item(label, w, h):
    """Đoán loại item từ label + kích thước. Mục / Nút / Khu vực / Nhập / Bảng / Link."""
    s = (label or "").lower()
    if any(k in s for k in ("btn", "button", "ボタン", "検索", "変える", "出力", "ログアウト", "リセット")):
        return "Nút"
    if any(k in s for k in ("input", "text-input", "textbox", "search")):
        return "Nhập"
    if any(k in s for k in ("table", "一覧", "リスト", "list")):
        return "Bảng"
    if any(k in s for k in ("link", "a href", "リンク")) or (w > 80 and h < 24 and "-" in s):
        return "Liên kết"
    if w >= 400 and h >= 50:
        return "Khu vực"
    if w >= 150 and h <= 32:
        return "Hiển thị"
    return "Mục"


def pick_items(raw_items, limit=18):
    """Lọc + prioritize items từ Figma text extract. Giữ tối đa `limit` items."""
    if not raw_items:
        return []
    cleaned = []
    for it in raw_items:
        lbl = (it.get("label") or "").strip()
        if not lbl or lbl.lower() in NOISE_LABELS:
            continue
        if re.match(r"^(group|frame|rectangle|vector|ellipse|line|image)\s*\d*$", lbl.lower()):
            continue
        if len(lbl) <= 1:
            continue
        cleaned.append(it)
    # sort reading order (top → bottom, left → right)
    cleaned.sort(key=lambda it: (int(it.get("ay", 0) / 40), it.get("ax", 0)))
    # Dedup consecutive by label (collapse repeated placeholders)
    out = []
    last = None
    for it in cleaned:
        if it["label"] == last:
            continue
        out.append(it)
        last = it["label"]
    # Prioritize if too many: keep items with longer labels OR larger size
    if len(out) > limit:
        scored = sorted(out, key=lambda it: (len(it["label"]), it.get("w", 0) * it.get("h", 0)), reverse=True)
        kept = set(id(it) for it in scored[:limit])
        out = [it for it in out if id(it) in kept]
        out.sort(key=lambda it: (int(it.get("ay", 0) / 40), it.get("ax", 0)))
    # Attach ordinal n + kind
    for i, it in enumerate(out, start=1):
        it["n"] = str(i)
        it["kind"] = it.get("kind") or classify_item(it["label"], it.get("w", 0), it.get("h", 0))
    return out


# ---------- CSS (adapted from ES-Station screen-design-doc sample) ----------
CSS = r"""
:root{
  --bg:#F3F5F8; --panel:#FFFFFF; --ink:#18212B; --ink2:#55616E; --ink3:#8A95A1;
  --line:#DFE4EA; --line2:#C9D1DA;
  --navy:#16324F; --blue:#1D4ED8; --blue-s:#EAF0FD;
  --pink:#D6246E; --pink-s:#FCEAF2;
  --amber:#B45309; --amber-s:#FEF3C7;
  --green:#047857; --green-s:#E3F5EE;
  --red:#B42318; --red-s:#FDECEA;
  --sel:#F59E0B;
  --f:system-ui,-apple-system,"Hiragino Kaku Gothic ProN","Noto Sans JP","Meiryo",sans-serif;
  --fm:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
*{box-sizing:border-box}
html,body{margin:0;height:100%}
body{background:var(--bg);color:var(--ink);font:13px/1.55 var(--f);display:flex;flex-direction:column;overflow:hidden}
button{font:inherit;cursor:pointer}

/* top bar */
.top{height:52px;flex:0 0 52px;background:var(--navy);color:#fff;display:flex;align-items:center;gap:14px;padding:0 16px}
.top .ttl{font-weight:800;font-size:14px;white-space:nowrap}
.top .sub{color:#B8C7D6;font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.top .sp{flex:1}
.top .nav-sel{background:#0F2338;color:#fff;border:1px solid #294B6B;border-radius:7px;padding:6px 10px;font:inherit;min-width:300px;max-width:460px}
.top .nav-sel option{background:#0F2338;color:#fff}
.top .nav-sel optgroup{color:#8DA7C2}
.top .nbtn{background:transparent;color:#C5D3E0;border:1px solid #294B6B;border-radius:6px;padding:5px 10px;font-size:12px}
.top .nbtn:hover{background:#0F2338;color:#fff}
.top .nbtn:disabled{opacity:.35;cursor:not-allowed}
.top .counter{color:#B8C7D6;font-size:12px}
.banner{background:#B42318;color:#fff;padding:8px 16px;font-size:12.5px;text-align:center;flex:0 0 auto}
.banner strong{font-weight:800}

/* layout: center + right (left nav skipped per feedback) */
.main{flex:1;display:grid;grid-template-columns:minmax(0,1fr) 460px;min-height:0}
.ctr{display:flex;flex-direction:column;min-width:0;min-height:0}
.ch{padding:12px 18px;background:var(--panel);border-bottom:1px solid var(--line);display:flex;gap:12px;align-items:flex-start}
.ch .t1{font:600 11px var(--fm);color:var(--blue)}
.ch .t2{font-size:15px;font-weight:800;margin-top:2px}
.ch .t3{font-size:12px;color:var(--ink2);margin-top:3px}
.ch .btns{margin-left:auto;display:flex;gap:6px;flex-shrink:0}
.btn{border:1px solid var(--line2);background:#fff;border-radius:7px;padding:6px 11px;font-size:12px;color:var(--ink)}
.btn:hover{background:#F5F7FA}
.btn.pri{background:var(--blue);color:#fff;border-color:var(--blue)}
.btn.pri:hover{background:#1E40AF}
.stage{flex:1;position:relative;overflow:auto;background:#E7EBF0;display:flex;align-items:flex-start;justify-content:center;padding:18px}
.img-wrap{position:relative;max-width:100%;display:inline-block;background:#fff;border:1px solid var(--line);box-shadow:0 2px 10px rgba(0,0,0,.06);border-radius:4px;overflow:hidden}
.img-wrap img{display:block;max-width:100%;height:auto}
.img-wrap .noimg{padding:40px;color:var(--ink2);text-align:center;background:#fff;min-width:560px}
.overlay{position:absolute;left:0;top:0;width:100%;height:100%;pointer-events:none}
.overlay .pin{position:absolute;transform:translate(-50%,-50%);background:var(--pink);color:#fff;font:700 11.5px/1 var(--f);min-width:22px;height:22px;padding:0 6px;border-radius:12px;display:inline-flex;align-items:center;justify-content:center;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.3);pointer-events:auto;cursor:pointer;transition:transform .15s}
.overlay .pin.area{background:var(--blue)}
.overlay .pin:hover{transform:translate(-50%,-50%) scale(1.15);z-index:2}
.overlay .pin.on{background:var(--sel);transform:translate(-50%,-50%) scale(1.3);z-index:3}
.legend{position:absolute;right:12px;bottom:10px;background:rgba(255,255,255,.94);border:1px solid var(--line);border-radius:8px;padding:5px 10px;font-size:11px;color:var(--ink2);display:flex;gap:12px;z-index:3}
.legend i{display:inline-block;width:11px;height:11px;border-radius:6px;vertical-align:-1px;margin-right:4px}

/* right panel */
.side{background:var(--panel);border-left:1px solid var(--line);display:flex;flex-direction:column;min-height:0}
.sh{padding:12px 16px 10px;border-bottom:1px solid var(--line)}
.sh .row{display:flex;gap:8px;align-items:center}
.sh h3{margin:0;font-size:14px;font-weight:800}
.sh .cnt{color:var(--ink3);font-size:12px;margin-left:auto}
.sh input{width:100%;margin-top:8px;border:1px solid var(--line2);border-radius:7px;padding:7px 10px;font:inherit}
.sh input:focus{outline:2px solid var(--blue-s);border-color:var(--blue)}
.chips{display:flex;gap:5px;margin-top:8px;flex-wrap:wrap}
.chips button{border:1px solid var(--line2);background:#fff;border-radius:14px;padding:3px 10px;font-size:11.5px;color:var(--ink2)}
.chips button.on{background:var(--navy);border-color:var(--navy);color:#fff;font-weight:600}
.chips button.warn{border-color:var(--red);color:var(--red);font-weight:700}
.chips button.warn.on{background:var(--red);border-color:var(--red);color:#fff}
.list{flex:1;overflow:auto;padding:8px 10px 40px}
.note{margin:2px 4px 10px;padding:9px 12px;border-radius:8px;background:#F4F6F9;color:var(--ink2);font-size:12px;border-left:3px solid var(--blue)}
.it{border:1px solid var(--line);border-radius:10px;margin:0 0 8px;background:#fff;transition:box-shadow .15s}
.it.on{border-color:var(--sel);box-shadow:0 0 0 3px rgba(245,158,11,.22)}
.it .hd{display:flex;gap:10px;align-items:flex-start;padding:9px 11px;cursor:pointer}
.bdg{flex:0 0 auto;min-width:26px;height:23px;padding:0 7px;border-radius:11px;color:#fff;font:700 11.5px/23px var(--f);text-align:center}
.bdg.area{background:var(--blue)} .bdg.leaf{background:var(--pink)}
.it .nm{font-weight:700;font-size:13px;line-height:1.4;padding-top:2px;flex:1;min-width:0}
.it .meta{display:flex;gap:4px;flex-wrap:wrap;margin-top:4px}
.tag{font-size:10.5px;border-radius:5px;padding:1px 7px;background:#EEF1F5;color:var(--ink2);line-height:17px}
.tag.req{background:var(--red-s);color:var(--red);font-weight:700}
.tag.new{background:var(--green-s);color:var(--green);font-weight:700}
.tag.upd{background:var(--amber-s);color:var(--amber);font-weight:700}
.it .one{color:var(--ink2);font-size:12px;margin-top:4px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.it.open .one{display:none}
.it .bd{display:none;border-top:1px solid var(--line);padding:9px 11px 11px;background:#FAFBFC}
.it.open .bd{display:block}
dl{margin:0;display:grid;grid-template-columns:92px 1fr;gap:5px 10px;font-size:12px}
dt{color:var(--ink3);font-weight:600}
dd{margin:0;white-space:pre-wrap;word-break:break-word}
.muted{color:var(--ink3);padding:12px;font-size:12px}
.about{padding:12px}
.about h4{margin:0 0 6px;font-size:13px;color:var(--navy)}
.about p{margin:0 0 8px;font-size:12.5px;color:var(--ink2)}

/* responsive */
@media (max-width:1180px){.main{grid-template-columns:minmax(0,1fr) 380px}}
@media (max-width:900px){body{overflow:auto}.main{grid-template-columns:1fr;grid-template-rows:auto 70vh auto}.side{min-height:60vh}}
"""

# ---------- JS ----------
JS_TMPL = r"""
var ORDER = __ORDER__;
var SCREENS = __SCREENS__;
var cur = 0, FILTER = 'all', Q = '';

function go(idx){
  if (idx < 0 || idx >= ORDER.length) return;
  cur = idx;
  var code = ORDER[cur], s = SCREENS[code];
  // Top header
  document.getElementById('vCode').textContent = code;
  document.getElementById('vName').textContent = s.title || '';
  document.getElementById('vState').textContent = (s.badge==='NEW'?'Màn mới':'Cập nhật') + (s.base ? (' · gốc: ' + s.base) : '') + ' · ' + (s.site || '') + (s.detail ? ' · ' + s.detail : '');
  // Image
  var wrap = document.getElementById('stageWrap');
  wrap.innerHTML = '';
  if (s.img){
    var iw = document.createElement('div'); iw.className='img-wrap';
    var img = document.createElement('img'); img.src = s.img; img.alt = code;
    iw.appendChild(img);
    var ov = document.createElement('div'); ov.className='overlay';
    (s.items||[]).forEach(function(it){
      if (it.ax == null || it.ay == null || !s.origW || !s.origH) return;
      var cx = (it.ax + it.w/2) / s.origW * 100;
      var cy = (it.ay + it.h/2) / s.origH * 100;
      // Bỏ pin nằm ngoài khung ảnh (item scroll-below-viewport, item downsample lệch).
      // Card panel vẫn giữ — chỉ không vẽ pin trên ảnh.
      if (!isFinite(cx) || !isFinite(cy) || cx < 0 || cx > 100 || cy < 0 || cy > 100) return;
      var p = document.createElement('div');
      p.className = 'pin' + (it.kind==='Khu vực' ? ' area' : '');
      p.textContent = it.n;
      p.style.left = cx + '%';
      p.style.top = cy + '%';
      p.dataset.n = it.n;
      p.title = it.label || '';
      ov.appendChild(p);
    });
    iw.appendChild(ov);
    var lg = document.createElement('div'); lg.className='legend';
    lg.innerHTML = '<span><i style="background:#1D4ED8"></i>Khu vực</span><span><i style="background:#D6246E"></i>Mục</span><span><i style="background:#F59E0B"></i>Đang chọn</span>';
    iw.appendChild(lg);
    wrap.appendChild(iw);
  } else {
    var ph = document.createElement('div'); ph.className='img-wrap';
    ph.innerHTML = '<div class="noimg">Chưa export ảnh từ Figma cho màn <code>' + code + '</code>.<br>Chạy <code>get_screenshot(fileKey, nodeId)</code> rồi lưu <code>_internal/screens/' + code + '.png</code> và rebuild.</div>';
    wrap.appendChild(ph);
  }
  // Panel
  renderPanel(s);
  // Dropdown + counter
  var sel = document.getElementById('nav-sel'); if (sel) sel.value = code;
  document.getElementById('counter').textContent = (cur+1) + ' / ' + ORDER.length;
  document.querySelector('.nbtn.prev').disabled = cur === 0;
  document.querySelector('.nbtn.next').disabled = cur === ORDER.length - 1;
}

function esc(s){ var m={'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}; return String(s==null?'':s).replace(/[&<>"']/g, function(c){return m[c];}); }

function renderPanel(s){
  var items = s.items || [], errs = s.errors || [];
  var sh = document.getElementById('sh');
  sh.innerHTML = '<div class="row"><h3>Định nghĩa mục</h3><span class="cnt">' + items.length + ' mục</span></div>' +
    '<input id="q" type="text" placeholder="Tìm theo tên, nội dung" value="' + esc(Q) + '">' +
    '<div class="chips">' +
      '<button data-f="all" class="' + (FILTER==='all'?'on':'') + '">Tất cả (' + items.length + ')</button>' +
      '<button data-f="new" class="' + (FILTER==='new'?'on':'') + '">Chỉ Mới</button>' +
      '<button data-f="err" class="' + (FILTER==='err'?'on':'') + (errs.length?' warn':'') + '">Lỗi (' + errs.length + ')</button>' +
      '<button data-f="info" class="' + (FILTER==='info'?'on':'') + '">Nghiệp vụ</button>' +
    '</div>';
  var list = document.getElementById('list');
  if (FILTER === 'err') {
    list.innerHTML = errs.length ? errs.map(function(e,i){
      return '<div class="it"><div class="hd"><span class="bdg leaf">E'+String(i+1).padStart(2,'0')+'</span>' +
        '<div class="nm">'+esc(e.trigger||'')+'<div class="meta"><span class="tag">'+esc(e.display||'')+'</span></div>' +
        '<div class="one">'+esc(e.msg||'')+'</div></div></div></div>';
    }).join('') : '<div class="muted">Không có lỗi.</div>';
    return;
  }
  if (FILTER === 'info') {
    list.innerHTML = '<div class="about">' +
      (s.purpose ? '<h4>Mục đích</h4><p>'+esc(s.purpose)+'</p>' : '') +
      (s.happy ? '<h4>Happy case</h4><p>'+esc(s.happy)+'</p>' : '') +
      (s.stype ? '<h4>Loại màn</h4><p>'+esc(s.stype)+'</p>' : '') +
      (s.base ? '<h4>Màn gốc</h4><p><code>'+esc(s.base)+'</code></p>' : '') +
      (s.figmaUrl ? '<h4>Nguồn</h4><p><a href="'+esc(s.figmaUrl)+'" target="_blank">Mở trên Figma ↗</a></p>' : '') +
      (!s.purpose && !s.happy ? '<p class="muted">Chưa có mô tả nghiệp vụ (cr.json chưa có purpose/happy).</p>' : '') +
      '</div>';
    return;
  }
  var filtered = items;
  if (FILTER === 'new') filtered = items.filter(function(it){ return (it.chg||'').toUpperCase()==='NEW'; });
  if (Q) {
    var q = Q.toLowerCase();
    filtered = filtered.filter(function(it){
      return (it.label||'').toLowerCase().indexOf(q) >= 0 || (it.desc||'').toLowerCase().indexOf(q) >= 0;
    });
  }
  if (!filtered.length) { list.innerHTML = '<div class="muted">Không có mục nào.</div>'; return; }
  list.innerHTML = filtered.map(function(it){
    var kindCls = it.kind==='Khu vực' ? 'area' : 'leaf';
    return '<div class="it" data-n="'+esc(it.n)+'">' +
      '<div class="hd"><span class="bdg '+kindCls+'">'+esc(it.n)+'</span>' +
      '<div class="nm">'+esc(it.label||'')+
      '<div class="meta"><span class="tag">'+esc(it.kind||'Mục')+'</span>' +
      (it.chg==='NEW'?'<span class="tag new">Mới</span>':'') + (it.chg==='UPD'?'<span class="tag upd">Cập nhật</span>':'') +
      '</div>' +
      (it.desc ? '<div class="one">'+esc(it.desc)+'</div>' : '') + '</div></div>' +
      (it.desc || it.label ? '<div class="bd"><dl>' +
        (it.desc ? '<dt>Mô tả</dt><dd>'+esc(it.desc)+'</dd>' : '') +
        '<dt>Vị trí</dt><dd>' + (it.ax!=null ? ('x='+it.ax+', y='+it.ay+', '+it.w+'×'+it.h+' px (gốc Figma)') : '(không có toạ độ)') + '</dd>' +
        '</dl></div>' : '') +
      '</div>';
  }).join('');
}

document.addEventListener('DOMContentLoaded', function(){
  go(0);
  document.getElementById('nav-sel').addEventListener('change', function(e){
    var i = ORDER.indexOf(e.target.value); if (i>=0) go(i);
  });
  document.querySelector('.nbtn.prev').addEventListener('click', function(){ go(cur-1); });
  document.querySelector('.nbtn.next').addEventListener('click', function(){ go(cur+1); });
  document.addEventListener('keydown', function(e){
    if (e.target.matches('input,select,textarea')) return;
    if (e.key === 'ArrowLeft') go(cur-1);
    else if (e.key === 'ArrowRight') go(cur+1);
  });
  document.addEventListener('click', function(ev){
    var ch = ev.target.closest('.chips button');
    if (ch){ FILTER = ch.dataset.f; renderPanel(SCREENS[ORDER[cur]]); return; }
    var pin = ev.target.closest('.overlay .pin');
    if (pin){
      document.querySelectorAll('.overlay .pin.on').forEach(function(e){e.classList.remove('on');});
      document.querySelectorAll('.list .it.on').forEach(function(e){e.classList.remove('on');});
      pin.classList.add('on');
      var it = document.querySelector('.list .it[data-n="'+pin.dataset.n+'"]');
      if (it){ it.classList.add('on','open'); it.scrollIntoView({block:'nearest',behavior:'smooth'}); }
      return;
    }
    var card = ev.target.closest('.list .it');
    if (card){
      document.querySelectorAll('.list .it.on').forEach(function(e){e.classList.remove('on');});
      document.querySelectorAll('.overlay .pin.on').forEach(function(e){e.classList.remove('on');});
      card.classList.toggle('open');
      card.classList.add('on');
      var p = document.querySelector('.overlay .pin[data-n="'+card.dataset.n+'"]');
      if (p){ p.classList.add('on'); p.scrollIntoView({block:'nearest',behavior:'smooth'}); }
    }
  });
  document.addEventListener('input', function(ev){
    if (ev.target.id === 'q'){ Q = ev.target.value; renderPanel(SCREENS[ORDER[cur]]); }
  });
});
"""


def dropdown(by_site, site_labels, screen_items_count):
    parts = ['<select id="nav-sel" class="nav-sel">']
    for st, screens in by_site.items():
        parts.append('<optgroup label="%s">' % esc(site_labels.get(st) or st))
        for s in screens:
            chg = (s.get("badge") or "").upper()
            n = screen_items_count.get(s["ref"], 0)
            lbl = "%s — %s (%s, %d mục)" % (s["ref"], (s.get("title") or s.get("label") or "")[:60], CHG_LABEL.get(chg, chg), n)
            parts.append('<option value="%s">%s</option>' % (esc(s["ref"]), esc(lbl)))
        parts.append("</optgroup>")
    parts.append("</select>")
    return "".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cr-json", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--screens-dir")
    ap.add_argument("--figma-url")
    ap.add_argument("--items-json", help="file JSON ref_uniq → items[{label,ax,ay,w,h}] (optional override)")
    ap.add_argument("--verify", action="store_true", help="chạy verify-cr-prototype.js (Playwright) sau khi build; FAIL → exit 1")
    a = ap.parse_args()

    if not os.path.exists(a.cr_json):
        print("❌ Không thấy cr.json: " + a.cr_json); sys.exit(2)
    cr = load_json(a.cr_json)
    meta = cr.get("meta") or {}
    view = cr.get("view") or {}
    scr = (view.get("screens") or {}).get("items") or []
    # Fallback cr-figma.json
    if not scr:
        cf_path = os.path.join(os.path.dirname(a.cr_json), "cr-figma.json")
        if os.path.exists(cf_path):
            cf = load_json(cf_path)
            view = cf
            scr = (cf.get("screens") or {}).get("items") or []
            if not meta.get("title"):
                meta["title"] = cf.get("title") or ""
    # Nodes map
    nodes_map = {}
    nodes_path = os.path.join(os.path.dirname(a.cr_json), "cr-figma-nodes.json")
    if os.path.exists(nodes_path):
        try:
            nd = load_json(nodes_path)
            if isinstance(nd, dict) and "nodes" in nd and isinstance(nd["nodes"], list):
                for n in nd["nodes"]:
                    if n.get("kind") == "mockup" and n.get("ref") and n.get("id"):
                        nodes_map[n["ref"]] = n["id"]
            elif isinstance(nd, dict) and "screens" in nd:
                for s in nd["screens"]:
                    if s.get("ref") and s.get("nodeId"):
                        nodes_map[s["ref"]] = s["nodeId"]
            elif isinstance(nd, dict):
                nodes_map = {k: v for k, v in nd.items() if isinstance(v, str)}
        except (ValueError, OSError):
            pass
    # Items override from external JSON
    items_override = {}
    if a.items_json and os.path.exists(a.items_json):
        try:
            items_override = load_json(a.items_json) or {}
        except (ValueError, OSError):
            pass

    proposed = [s for s in scr if (s.get("badge") or "").upper() in ("NEW", "UPD")]
    if not proposed:
        print("❌ Không có màn NEW/UPD."); sys.exit(1)

    site_order = view.get("site_order") or []
    site_labels = view.get("site_labels") or {}
    by_site, seen = {}, []
    for s in proposed:
        st = s.get("site") or "DEFAULT"
        if st not in by_site:
            by_site[st] = []; seen.append(st)
        by_site[st].append(s)
    ordered_sites = [st for st in site_order if st in by_site] + [st for st in seen if st not in site_order]
    by_site_ordered = {st: by_site[st] for st in ordered_sites}
    screen_order = [s["ref"] for st in ordered_sites for s in by_site_ordered[st]]

    # Build screen data
    screens_data = {}
    counts = {}
    missing_imgs = []
    for s in proposed:
        ref = s["ref"]
        # Image
        img_data = None
        orig_w, orig_h = None, None
        if a.screens_dir:
            png = os.path.join(a.screens_dir, ref + ".png")
            if os.path.exists(png):
                img_data = embed_image(png)
                # Read PNG header dimensions (for aspect fallback)
                try:
                    with open(png, "rb") as f:
                        f.seek(16); w = int.from_bytes(f.read(4), "big"); h = int.from_bytes(f.read(4), "big")
                    orig_w, orig_h = w, h
                except OSError:
                    pass
            else:
                missing_imgs.append(ref)
        # Prefer Figma coord-space dims when override provides them (correct overlay for downsampled PNGs)
        ov = items_override.get(ref) or {}
        if ov.get("origW") and ov.get("origH"):
            orig_w, orig_h = int(ov["origW"]), int(ov["origH"])
        # Items (priority: cr-figma.json items → items_override → empty)
        raw_items = s.get("items") or []
        if not raw_items and ref in items_override:
            raw_items = items_override[ref].get("items") or []
        items = pick_items(raw_items, limit=18)
        counts[ref] = len(items)
        # Errors + purpose: items-override wins khi có (demo), production dùng cr.json
        ov_ref = items_override.get(ref, {})
        errors = ov_ref.get("errors") or s.get("errors") or []
        purpose = ov_ref.get("purpose") or s.get("purpose") or ""
        detail = ov_ref.get("detail", "")
        # Compose
        screens_data[ref] = {
            "title": s.get("title") or s.get("label") or ref,
            "badge": (s.get("badge") or "").upper(),
            "site": site_labels.get(s.get("site"), s.get("site")) or "",
            "base": s.get("base") or "",
            "purpose": purpose,
            "detail": detail,
            "happy": s.get("happy") or "",
            "stype": s.get("stype") or "",
            "img": img_data,
            "origW": orig_w,
            "origH": orig_h,
            "items": items,
            "errors": errors,
            "figmaUrl": figma_link(a.figma_url, nodes_map.get(ref)),
        }

    cr_id = meta.get("cr_id") or "CR"
    title = meta.get("title") or ""

    # Banner
    banner = ('<div class="banner">⚠ <strong>CR — màn đề xuất</strong> · '
              '<strong>%d màn</strong> của <code>%s</code> · %s</div>') % (len(proposed), esc(cr_id), esc(title))

    # Top bar
    top = (
        '<div class="top">'
        '<div class="ttl">%s</div>'
        '<div class="sub">%s · %d màn đề xuất</div>'
        '<div class="sp"></div>'
        '<button class="nbtn prev" title="Màn trước (←)">◀ Trước</button>'
        '%s'
        '<button class="nbtn next" title="Màn sau (→)">Sau ▶</button>'
        '<span class="counter" id="counter">1 / %d</span>'
        '</div>'
    ) % (esc(cr_id), esc(title), len(proposed), dropdown(by_site_ordered, site_labels, counts), len(proposed))

    body = (
        '%s%s'
        '<div class="main">'
        '  <section class="ctr">'
        '    <div class="ch">'
        '      <div style="min-width:0">'
        '        <div class="t1" id="vCode"></div>'
        '        <div class="t2" id="vName"></div>'
        '        <div class="t3" id="vState"></div>'
        '      </div>'
        '      <div class="btns">'
        '        <button class="btn" onclick="document.querySelectorAll(\'.list .it.open\').forEach(e=>e.classList.remove(\'open\'))">Thu gọn</button>'
        '        <button class="btn pri" id="figmaBtn">↗ Mở trên Figma</button>'
        '      </div>'
        '    </div>'
        '    <div class="stage"><div id="stageWrap"></div></div>'
        '  </section>'
        '  <aside class="side">'
        '    <div class="sh" id="sh"></div>'
        '    <div class="list" id="list"></div>'
        '  </aside>'
        '</div>'
    ) % (top, banner)

    js = (JS_TMPL
          .replace("__ORDER__", json.dumps(screen_order, ensure_ascii=False))
          .replace("__SCREENS__", json.dumps(screens_data, ensure_ascii=False)))

    # Patch: Figma button handler + wire figmaUrl
    extra_js = r"""
document.addEventListener('DOMContentLoaded', function(){
  document.getElementById('figmaBtn').addEventListener('click', function(){
    var s = SCREENS[ORDER[cur]]; if (s && s.figmaUrl) window.open(s.figmaUrl, '_blank');
  });
});
"""

    page = (
        '<!doctype html><html lang="vi"><head><meta charset="utf-8">'
        '<title>%s — Màn đề xuất</title>'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<style>%s</style></head><body>%s'
        '<script>%s</script><script>%s</script>'
        '</body></html>'
    ) % (esc(cr_id + " · " + title), CSS, body, js, extra_js)

    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(page)

    kb = os.path.getsize(a.out) // 1024
    nnew = sum(1 for s in proposed if (s.get("badge") or "").upper() == "NEW")
    nupd = sum(1 for s in proposed if (s.get("badge") or "").upper() == "UPD")
    total_items = sum(counts.values())
    print("✅ Build xong: %s (%d KB)" % (a.out, kb))
    print("   %d màn (%d NEW, %d UPD) · %d site · %d/%d có ảnh · %d items tổng"
          % (len(proposed), nnew, nupd, len(by_site_ordered), len(proposed) - len(missing_imgs), len(proposed), total_items))
    if missing_imgs:
        print("⚠ Thiếu ảnh %d màn: %s" % (len(missing_imgs), ", ".join(missing_imgs[:8]) + (" ..." if len(missing_imgs) > 8 else "")))

    if a.verify:
        import subprocess
        gate = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify-cr-prototype.js")
        if not os.path.exists(gate):
            print("⚠ Không thấy verify-cr-prototype.js — bỏ qua gate.")
        else:
            print("\n--- Chạy gate verify-cr-prototype.js ---")
            report = os.path.splitext(a.out)[0] + ".verify.md"
            rc = subprocess.call(["node", gate, a.out, "--out", report])
            if rc != 0:
                sys.exit(rc)


if __name__ == "__main__":
    main()
