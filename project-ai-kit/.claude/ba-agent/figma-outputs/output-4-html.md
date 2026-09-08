# Ba Agent — Output 4: HTML Prototype

## Output 4 — HTML Prototype (Local)

> Dựng prototype chạy được trên browser để stakeholder confirm UI trước khi Designer vẽ Figma HiFi.

**Tạo file:** `<DOCS_ROOT>/features/<feature>/prototype/index.html`

**Yêu cầu prototype:**
- **Standalone** — 1 file HTML duy nhất, không cần build, mở thẳng bằng `open index.html`
- **Mobile viewport** — width 390px, cố định (giống iPhone 14)
- **All screens** — mỗi screen là 1 div, toggle `display` để chuyển màn hình
- **Interactive** — buttons/taps navigate đúng luồng Happy Case
- **Dev Nav bar** — thanh navigation ở dưới để jump thẳng vào bất kỳ screen nào khi review
- **Error states** — simulate toast/modal cho non-happy cases quan trọng
- **Timers** — nếu feature có countdown/timer, implement đúng

**Sau khi tạo:**
```bash
open <DOCS_ROOT>/features/<feature>/prototype/index.html
```

**Kỹ thuật Figma (cho Output 1-3) — thứ tự KHÔNG được sai:**
```js
// ✅ ĐÚNG
tx.resize(width, 10);         // 1. resize trước
tx.textAutoResize = "HEIGHT"; // 2. set SAU resize
tx.characters = content;      // 3. text wrap đúng
curY += tx.height + gap;      // 4. tích lũy Y chính xác → không overlap

// ❌ SAI — resize() reset textAutoResize = "NONE"
tx.textAutoResize = "HEIGHT";
tx.resize(width, 10);         // → height = 10 mãi → text chồng nhau
```
