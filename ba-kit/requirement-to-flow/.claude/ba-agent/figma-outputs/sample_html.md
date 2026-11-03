# Sample HTML — Chuẩn tham chiếu cho HTML Prototype / Viewer

> **File tham chiếu khi sinh HTML** cho Output 4 (requirement-to-flow) và CR HTML viewer (system-to-doc). Rút từ bản thực tế `Project Care Pro/requirement-to-flow/outputs/carepro/prototype/index.html` (141 màn · 587 items · pass 1052 test Playwright).
>
> **Mục đích**: HTML sinh ra phải (1) **xem được như website** · (2) **bấm được** đủ flow · (3) **có mô tả đầy đủ** cho từng màn · (4) **đánh số items** · (5) **mỗi số có mô tả tương ứng** ở panel bên phải.

---

## 1. Bảng phân tích 7 chiều

| Chiều | Yêu cầu | DOM/CSS/JS cốt lõi | Ví dụ Care Pro | Gate kiểm |
|---|---|---|---|---|
| **Cấu trúc** | 1 file HTML standalone · mọi màn là `<section class="scr">` toggle `.on` · 1 màn hiện tại 1 lúc | `<section class="scr" id="scr-<CODE>" data-app="<X>">` | 141 section nested trong `#stage` | `SHAPE` — chỉ 1 `.scr.on` |
| **Action** | Mọi điều hướng = `data-go="<CODE>"` · navigation thật qua `window.go(code, {asPage:bool})` · error bắn qua `window.fireErr(code, i)` | `<button data-go="FC_DASH_001">Đăng nhập</button>` · click handler delegate ở `document` | 363 phần tử `[data-go]` | `NAV` — click thật từng data-go |
| **Style** | CSS tokens `:root` · responsive 1440/1024/375 · grid layout 2 cột (`.cols2` 3fr 2fr) · card system (`.card`, `.solo-card`, `.modal-box`) · brand colors | `:root { --pri, --bg, --card, --tx, --div, --red, --purp }` · `.cols2{display:grid;grid-template-columns:3fr 2fr}` | 15+ token · 3 breakpoint · dev-strip ở cuối màn | `RESP` — 1440/1024/375 không cuộn ngang |
| **Thiết kế view** | Mỗi màn có: breadcrumb · h1 title · subtitle code · nội dung items · dev-nav "Transition theo SPEC" | `.crumb → .pt → .sub → .cols2/.card → .tstrip` | tstrip hiện cả nhánh happy + NG | — |
| **Items (đánh số)** | Mỗi item wrap `.blk` · label `.lbl` + badge area `.pos` + control thật · overlay số qua `data-i` attr + CSS counter | `<div class="blk"><label class="lbl">Input <span class="pos">(Body)</span></label><input placeholder="..."></div>` | 587 items đánh số 100% | `COVERAGE` — mọi `.blk` eligible có `data-i` |
| **Panel mô tả** | Fixed right 340px · hiện khi toggle "Hiện số" · list items với: badge + tag + label + position + preview · click 2 chiều với item trên màn | `.num-panel { position:fixed; right:0; width:340px }` + JS `describe(blk)` sinh entry | 1 entry/item · click panel ↔ highlight item | `PANEL` — số entry = số item |
| **Toggle + navigation** | Nút "Hiện số" cố định góc trên-phải · wrap `window.go` để re-number sau mỗi lần chuyển màn · phím mũi tên ← → chuyển màn | `.num-toggle{position:fixed;top:12px;right:12px}` · `window.go = function(){ ...origGo(); if(show) setTimeout(numberItems, 30); }` | Toggle + ← → + Dev Nav bar | — |

---

## 2. Prototype Contract — bắt buộc

```js
window.__PROTO__ = {
  screens: {
    "FC_AUTH_001": {
      name: "Đăng nhập",
      ty: "Form",                     // Form · List · Detail · Modal · Full screen · Popup
      unk: false,                      // true = màn còn UNKNOWN/INFERENCE
      errs: [                          // đúng thứ tự bảng Non-Happy
        ["E-001", "Validation", "Bỏ trống ID", "Inline error", "Vui lòng nhập ID"]
      ],
      // TUỲ CHỌN cho SPEC panel (output-4-verify.md §items/opens)
      items: [{ no, ja, kind, req, len, init, ex, valid, err:[E-ids], cond, trig }],
      opens: [{ no:"OQ-003", text, ask }]
    }
  }
};
window.go      = function(code, opts) { /* toggle .scr .on; opts.asPage ép mở dạng trang */ };
window.fireErr = function(code, i)    { /* bắn error thứ i (toast/modal/banner/inline/fullscreen) */ };
```

---

## 3. DOM skeleton

```html
<!doctype html><html lang="vi"><head>
  <meta charset="utf-8">
  <title>CarePro — HTML Prototype (Output 4)</title>
  <style>/* :root tokens + layout + components */</style>
</head><body>
  <!-- App shell: header + sidebar + stage -->
  <header class="head"><!-- logo · user menu · notification --></header>
  <nav class="appnav"><!-- menu chính, có data-go --></nav>
  <main id="stage">
    <section class="scr on" id="scr-FC_AUTH_001" data-app="FC">
      <div class="solo-card"><!-- login centered card -->
        <div class="brandlogo">…</div>
        <h1 class="pt">ログイン<span class="ty">Form</span></h1>
        <div class="sub">Đăng nhập · FC_AUTH_001</div>
        <!-- Items — mỗi item = 1 .blk -->
        <div class="blk"><label class="lbl">Input <span class="pos">(Body)</span></label>
          <input type="text" placeholder="Mã pháp nhân">
        </div>
        <div class="blk"><label class="lbl">Input password <span class="pos">(Body)</span></label>
          <input type="password" placeholder="Mật khẩu">
        </div>
        <div class="blk"><a class="lnk" data-go="FC_AUTH_002">Quên mật khẩu?</a></div>
        <div class="blk"><button class="btn primary" data-go="FC_DASH_001">Đăng nhập</button></div>
        <!-- Dev strip — transition theo SPEC để BA kiểm nhánh -->
        <div class="tstrip">
          <div class="ttl">Transition theo SPEC (## Screens):</div>
          <button class="btn" data-go="FC_DASH_001">OK → FC_DASH_001</button>
          <button class="btn" data-go="FC_AUTH_002">Quên MK → FC_AUTH_002</button>
        </div>
      </div>
    </section>
    <section class="scr" id="scr-FC_DASH_001"><!-- màn dashboard với .cols2 --></section>
    <!-- ... 141 màn ... -->
  </main>
  <script>/* D, codes, render(), go(), fireErr() */</script>
</body></html>
```

### Layout 2 cột cho form/detail

```html
<section class="scr" id="scr-FC_CONT_001">
  <div class="crumb"><a data-go="FC_DASH_001">Home</a> / Đăng ký</div>
  <h1 class="pt">Đăng ký dùng thử<span class="ty">Form</span></h1>
  <div class="sub">Đăng ký thông tin pháp nhân · FC_CONT_001</div>
  <div class="cols2">
    <div><!-- Left column: inputs -->
      <div class="blk"><label class="lbl">Input <span class="pos">(Left)</span></label>
        <input type="text" placeholder="Tên pháp nhân">
      </div>
      <!-- ... items trái ... -->
    </div>
    <div><!-- Right column: aux info / summary -->
      <div class="blk"><label class="lbl">Table <span class="pos">(Right)</span></label>
        <table class="dt"><thead><tr><th>Cột</th></tr></thead><tbody><tr><td>...</td></tr></tbody></table>
      </div>
    </div>
  </div>
  <div class="tstrip">…</div>
</section>
```

### Layout modal/popup

```html
<section class="scr" id="scr-FC_CONF_001">
  <div class="modal-wrap">              <!-- nền mờ -->
    <div class="par">Nền: FC_DASH_001 (mờ)</div>
    <div class="modal-box">
      <div class="mh"><b>Confirm Delete / 削除確認</b>
        <button class="x" data-go="FC_DASH_001" aria-label="đóng">✕</button>
      </div>
      <div class="blk">…</div>
    </div>
  </div>
</section>
```

---

## 4. CSS tokens cốt lõi

```css
:root{
  /* Brand */
  --pri:#F4860C; --pri-lt:#FFEFDE;
  /* Surface */
  --bg:#F0F2F5; --card:#fff;
  /* Ink */
  --tx:#1F2328; --tm:#424A53; --tl:#6E777D;
  /* Line */
  --div:#D0D7DE;
  /* Semantic */
  --red:#CF222E; --red-lt:#FFF1F0;
  --purp:#6639BA; --purp-lt:#F1F1FF;   /* UNKNOWN */
}
/* Layout containers */
.cols2{ display:grid; grid-template-columns:3fr 2fr; gap:16px; margin-bottom:14px; }
.cols2.wr{ grid-template-columns:2fr 3fr; }   /* wide-right khi col R có calendar */
.solo-card{ max-width:460px; margin:40px auto; background:rgba(255,255,255,.93);
  border-radius:24px; padding:28px; box-shadow:0 12px 36px rgba(0,0,0,.22); }
.card{ background:var(--card); border-radius:8px; padding:16px; margin-bottom:12px;
  box-shadow:0 1px 2px rgba(0,0,0,.04); }
/* Item wrapper */
.blk{ margin-bottom:14px; }
.lbl{ display:block; font-weight:700; margin-bottom:4px; font-size:12px; }
.pos{ font-weight:400; color:var(--tl); font-size:11px; }
/* Actionable */
.btn{ border:1px solid var(--pri); color:var(--pri); background:#fff;
  border-radius:6px; padding:7px 16px; cursor:pointer; margin:2px 6px 2px 0; }
.btn.primary{ background:var(--pri); color:#fff; }
.lnk{ color:var(--pri); cursor:pointer; text-decoration:underline; }
/* Modal */
.modal-wrap{ position:relative; background:rgba(36,41,47,.45); border-radius:8px; padding:40px 16px; }
.modal-box{ background:#fff; border-radius:10px; max-width:640px; margin:0 auto; padding:18px 20px; }
/* Dev strip */
.tstrip{ margin-top:18px; border-top:1px dashed var(--div); padding-top:10px; }
.tstrip .ttl{ font-size:11px; color:var(--tl); margin-bottom:6px; }
/* UNKNOWN warning */
.unknote{ background:var(--purp-lt); border:1px dashed var(--purp); color:var(--purp);
  border-radius:6px; padding:10px 12px; margin-bottom:12px; }
/* Breadcrumb */
.crumb{ color:var(--tl); font-size:12px; }
/* Responsive */
@media (max-width:1024px){ .cols2{ grid-template-columns:1fr; } }
```

---

## 5. Overlay số item + Panel mô tả — bắt buộc

### 5.1 CSS

```css
/* Pin số đè item */
body.show-nums .scr.on .blk{ position:relative !important; }
body.show-nums [data-i]::before{
  content: attr(data-i);
  position:absolute; top:-10px; left:-12px;
  min-width:22px; height:22px; padding:0 6px; border-radius:11px;
  background:#D6246E; color:#fff;
  font:700 11px system-ui;
  display:inline-flex; align-items:center; justify-content:center;
  border:2px solid #fff; box-shadow:0 1px 4px rgba(0,0,0,.35);
  z-index:50; pointer-events:none;
}
body.show-nums [data-i].flash{ outline:3px solid #F59E0B; outline-offset:2px; }

/* Toggle button */
.num-toggle{ position:fixed; top:12px; right:12px; z-index:9999;
  padding:7px 14px; background:#16324F; color:#fff; border:none;
  border-radius:8px; cursor:pointer; font:600 12.5px system-ui; }
.num-toggle.on{ background:#D6246E; }

/* Panel mô tả */
.num-panel{ position:fixed; top:0; right:0; width:340px; height:100vh;
  background:#fff; border-left:1px solid #DFE4EA;
  box-shadow:-2px 0 10px rgba(0,0,0,.08);
  z-index:9998; overflow:auto; display:none; }
body.show-nums .num-panel{ display:block; }
body.show-nums{ padding-right:340px; }   /* đẩy main sang trái tránh che */

.num-panel .ph{ padding:14px 16px 10px; border-bottom:1px solid #DFE4EA;
  background:#F3F5F8; position:sticky; top:0; }
.num-panel ol{ list-style:none; margin:0; padding:6px 10px 40px; }
.num-panel li{ display:flex; gap:10px; padding:9px 10px;
  border-bottom:1px solid #ECF0F3; cursor:pointer; }
.num-panel li:hover{ background:#F6F8FA; }
.num-panel li.on{ background:#FFF4D6; }
.num-panel li .n{ flex:0 0 24px; height:22px; border-radius:11px;
  background:#D6246E; color:#fff; font:700 11px system-ui;
  display:inline-flex; align-items:center; justify-content:center; }
.num-panel li .tag{ display:inline-block; padding:0 6px; margin-right:4px;
  background:#EEF1F5; color:#55616E; font-size:10px; border-radius:4px; font-weight:600; }
.num-panel li .pos{ color:#8A95A1; font-size:11px; margin-left:5px; }
.num-panel li .prev{ color:#55616E; font-size:12px; margin-top:3px; }
```

### 5.2 JS pattern

```js
(function(){
  function eligibleBlks(scr){
    return [...scr.querySelectorAll('.blk')]
      .filter(el => !el.closest('.tstrip,.mh,.par,.unknote,.scrim'));
  }
  function describe(blk){
    const lbl = blk.querySelector(':scope > .lbl');
    const posEl = lbl?.querySelector('.pos');
    const pos = posEl ? posEl.textContent.trim() : '';
    let name = lbl ? lbl.cloneNode(true) : null;
    if (name){ const p = name.querySelector('.pos'); if (p) p.remove(); name = name.textContent.trim(); }
    const ctl = blk.querySelector('input,textarea,select,button,table,a,.tw,.dt,.cards,.stat');
    let tag = '-', prev = '';
    if (ctl){
      const t = ctl.tagName;
      if (t === 'INPUT'){ tag = ctl.type.toUpperCase(); prev = ctl.placeholder || ctl.value || ''; }
      else if (t === 'TEXTAREA'){ tag = 'TEXTAREA'; prev = ctl.placeholder || ''; }
      else if (t === 'SELECT'){ tag = 'SELECT'; prev = [...ctl.options].slice(0,3).map(o=>o.textContent).join(' / '); }
      else if (t === 'BUTTON'){ tag = 'BUTTON'; prev = ctl.textContent.trim(); }
      else if (t === 'A'){ tag = 'LINK'; prev = ctl.textContent.trim(); }
      else if (t === 'TABLE'){ tag = 'TABLE';
        prev = [...ctl.querySelectorAll('thead th')].slice(0,3).map(x=>x.textContent).join(' · '); }
      else { tag = (ctl.className || t).split(/\s+/)[0].toUpperCase(); prev = ctl.textContent.slice(0,80); }
    }
    return { name: name || prev.slice(0,40), pos, tag, prev,
             isAction: !!blk.querySelector('[data-go],button'), hasLbl: !!lbl };
  }
  function numberItems(){
    const scr = document.querySelector('.scr.on'); if (!scr) return;
    const blks = eligibleBlks(scr);
    blks.forEach((el,i) => el.setAttribute('data-i', i+1));
    const panel = document.querySelector('.num-panel'); if (!panel) return;
    const code = (scr.id||'').replace(/^scr-/,'');
    const title = scr.querySelector('h1')?.childNodes[0].textContent.trim() || code;
    const missing = blks.filter(el => !el.querySelector(':scope > .lbl') &&
                                     !el.querySelector('[data-go],button')).length;
    panel.innerHTML = `<div class="ph"><h3>${title}</h3><div class="meta">${code}</div>
      <div class="cnt${missing?' warn':''}">${blks.length} mục${missing?` · ${missing} thiếu mô tả`:''}</div></div>
      <ol>${blks.map((el,i) => {
        const d = describe(el); const n = i+1;
        return `<li data-i="${n}"${d.isAction?' class="action"':''}>
          <div class="n">${n}</div>
          <div class="body">
            <div class="nm">${d.tag!=='-'?`<span class="tag">${d.tag}</span>`:''}${d.name}
              ${d.pos?`<span class="pos">${d.pos}</span>`:''}</div>
            ${d.prev?`<div class="prev">${d.prev}</div>`:''}
          </div></li>`;
      }).join('')}</ol>`;
  }
  function addToggle(){
    if (document.querySelector('.num-toggle')) return;
    const btn = document.createElement('button');
    btn.className = 'num-toggle'; btn.textContent = 'Hiện số';
    btn.onclick = () => {
      const on = document.body.classList.toggle('show-nums');
      btn.classList.toggle('on', on); btn.textContent = on ? 'Ẩn số' : 'Hiện số';
      if (on) numberItems(); else document.querySelectorAll('[data-i]').forEach(el => el.removeAttribute('data-i'));
    };
    document.body.appendChild(btn);
    const panel = document.createElement('div'); panel.className = 'num-panel';
    document.body.appendChild(panel);
    panel.addEventListener('click', ev => {
      const li = ev.target.closest('li[data-i]'); if (!li) return;
      panel.querySelectorAll('li.on').forEach(x=>x.classList.remove('on'));
      li.classList.add('on');
      const tgt = document.querySelector(`.scr.on [data-i="${li.dataset.i}"]`);
      if (tgt){ tgt.classList.add('flash'); tgt.scrollIntoView({block:'center',behavior:'smooth'});
        setTimeout(()=>tgt.classList.remove('flash'), 1600); }
    });
  }
  // Hook go() để re-number
  const origGo = window.go;
  if (typeof origGo === 'function') {
    window.go = function(){ const r = origGo.apply(this, arguments);
      if (document.body.classList.contains('show-nums')) setTimeout(numberItems, 30); return r; };
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', addToggle);
  else addToggle();
})();
```

---

## 6. Thước đo "được như website"

| Tiêu chí | Pass khi |
|---|---|
| **Mở không cần build/server** | `open index.html` 1 file, không external resource (gate `STATIC` kiểm) |
| **Màn ẩn/hiện qua .on** | `.scr` toggle `.on`, chỉ 1 màn visible (gate `SHAPE`) |
| **Bấm thật từng nút** | `data-go` trỏ màn có thật, click chuyển đúng (gate `NAV` + `REACH`) |
| **Error bắn thật** | `fireErr(code, i)` ra đúng loại (toast/modal/banner/inline/full screen) (gate `ERR`) |
| **Responsive 3 ngưỡng** | 1440 / 1024 / 375 không cuộn ngang (gate `RESP`) |
| **UNKNOWN có placeholder** | Màn `unk:true` hiện `⚠ UNKNOWN BEHAVIOR` (gate `P2`) |
| **0 lỗi JS** | 0 pageerror · 0 console.error · 0 request ra ngoài (gate `RUNTIME`) |
| **Đánh số đủ item** | Mọi `.blk` eligible có `data-i` (gate `COVERAGE` của `verify-prototype-nums.js`) |
| **Mô tả đủ item** | Panel entry khớp số item, mỗi item có `.lbl` hoặc action (gate `PANEL` + `DESC`) |

---

## 7. Mô tả màn hình đầy đủ

Mỗi màn phải có **3 block mô tả** để khách và BA cùng hiểu:

```html
<section class="scr" id="scr-<CODE>">
  <!-- 1. BREADCRUMB — vị trí trong app -->
  <div class="crumb"><a data-go="HOME">Home</a> / <a data-go="PARENT">Parent</a> / Màn hiện tại</div>

  <!-- 2. TITLE + TYPE — tên nghiệp vụ + loại màn -->
  <h1 class="pt">Tên màn tiếng Nhật<span class="ty">Form</span></h1>
  <div class="sub">Mô tả Tiếng Việt · <CODE></div>

  <!-- 3. UNKNOWN NOTE (nếu màn còn open question) -->
  <div class="unknote">⚠ UNKNOWN BEHAVIOR — chờ BRSE confirm · Phạm vi màn này còn câu hỏi mở.</div>

  <!-- Content -->
  …
</section>
```

Thiếu bất kỳ 1 trong 3 → BA phải sửa SPEC trước (missing title / subtitle = SPEC chưa viết `## Screens → <code> → name/jp`).

---

## 8. Mapping SPEC → HTML

| SPEC Element (`## Screens`) | HTML |
|---|---|
| `Code` (SC-xxx hoặc XX_YYYY_NNN) | `id="scr-<CODE>"` |
| `Name` (tiếng Nhật) | `<h1 class="pt">`  |
| `Name VN` | `<div class="sub">` |
| `Type` (Form/List/Detail/Modal) | `<span class="ty">` |
| `Shell` (public/mypage/admin/auth/modal) | `data-app=` + layout container (`.solo-card` cho auth, `.modal-wrap` cho modal) |
| `Items` (bảng Screen Details) | Mỗi row = 1 `<div class="blk">` · `Title` → `<label class="lbl">` · `Position` → `<span class="pos">(Body/Left/Right)` · `Kind` → control thật (input/button/table/...) |
| `Transition` (nhánh happy + NG) | `<div class="tstrip">` ở cuối màn |
| `Non-Happy` (bảng Error) | `errs[]` trong `__PROTO__.screens[code].errs` + `fireErr(code, i)` dựng toast/modal/banner |

---

## 9. Nguồn tham chiếu

- **Bản mẫu thực tế** `Project Care Pro/requirement-to-flow/outputs/carepro/prototype/index.html` (141 màn, 587 items, gate `verify-prototype.js` 1052 pass + `verify-prototype-nums.js` 586/587 numbered)
- **Generator Care Pro** `Project Care Pro/.../prototype/_build/gen_o4.py` + `model.py` + `build_o3v6.py` (Python từ SPEC.md → HTML)
- **Rule chung** `.claude/ba-agent/figma-outputs/output-4-html.md` (Rule P1–P8)
- **Gate interactive** `.claude/skills/business-analyst/scripts/verify-prototype.js` (8 nhóm)
- **Gate numbering** (Care Pro-specific) `.../scripts/verify-prototype-nums.js` (6 nhóm)

---

## 10. Lưu ý khi áp dụng

- **Selector `.blk`** là convention Care Pro — kit khác tự chọn convention (vd `.item`, `.widget`) nhưng phải NHẤT QUÁN để selector `eligibleBlks()` work
- **Toggle button + panel** là **tuỳ chọn** — bật khi khách cần tra cứu item side-by-side; bỏ khi khách chỉ cần demo navigation
- **Overlay số** luôn re-render khi `go()` → wrap `window.go` để tự động
- **Mỗi item CÓ MÔ TẢ** (label hoặc action) — nếu BA viết SPEC thiếu `Title` cho item lẻ, gate `DESC` sẽ FAIL hoặc WARN, báo BA sửa SPEC
