# Ba Agent — Bước 5.5 Visual Recheck

> Sau khi Bước 5 xong (Output 1 + 2 + 3), BA **phải chụp screenshot từng frame** rồi tự đánh giá theo checklist. KHÔNG được báo user "đã xong" nếu chưa qua bước này.

**Quy trình:**

```
For each frame in [Output 1, Output 2, Output 3]:
  1. Call get_screenshot(nodeId, maxDimension=1400, enableBase64Response=true)
  2. Đọc screenshot → tự đánh giá theo checklist 5 tiêu chí bên dưới
  3. Nếu FAIL 1 tiêu chí → fix ngay (viết use_figma call sửa) → chụp lại
  4. Chỉ khi PASS toàn bộ mới sang frame tiếp theo
```

**Checklist 5 tiêu chí (mỗi frame):**

| # | Tiêu chí | PASS khi... | Cách kiểm tra |
|---|---|---|---|
| 1 | **Đủ nội dung theo yêu cầu** | Đã đủ tất cả sections theo skill (VD Output 1: 5 columns + Tech Stack + Sitemap; Output 2: 4 zones; Output 3: mockup + bảng ĐẦY ĐỦ item) | So sánh checklist section trong `ba-figma-output/SKILL.md` |
| 2 | **KHÔNG chồng đè** | `overlapCount == 0` từ phép quét bbox ở **Tiêu chí 7** | ⚠️ **CHẠY TIÊU CHÍ 7 TRƯỚC** (đếm được, khách quan). Zoom screenshot chỉ là bước phụ sau đó để bắt lỗi text/đường kẻ mà bbox không thấy. **Nhìn screenshot rồi kết luận "không đè" là KHÔNG hợp lệ** |
| 3 | **Text đầy đủ, không bị crop** | Mọi label đọc được đầy đủ, không bị cắt cuối câu | Zoom screenshot check text nodes có `...` cuối hoặc content ngắn bất thường |
| 4 | **Đúng vùng (không lệch cột)** | Node của Zone X nằm gọn trong `Z<X>_X` đến `Z<X>_X + Z<X>_W` | Verify X-coordinate của mỗi node ≥ Zone X boundary |
| 5 | **Số lượng item khớp bảng** (chỉ Output 3) | Số badge trên mockup = số dòng trong bảng | Đếm badge trên phone → đếm rows trong table → phải khớp.<br>⚠️ Phép này chỉ đối chiếu **NỘI BỘ**: `0 badge = 0 row` vẫn "khớp" → BẮT BUỘC chạy kèm Tiêu chí 6 + phép đối chiếu với SPEC ở `figma-outputs/output-3-screens.md` |
| 6 | **Không có màn hình trống / node rỗng** (BẮT BUỘC — mọi frame) | Mọi screen mockup có `≥3 child node` VÀ `≥1 text node có ký tự` | Read-back cây node bằng `use_figma` — xem quy trình bên dưới. **KHÔNG được kết luận bằng mắt nhìn screenshot** |
| 9 | **Node nằm trong biên frame** (BẮT BUỘC, chạy TRƯỚC tiêu chí 7) | Mọi node lá trong `[0,W]×[0,H]`, đủ **4 phía** | Script ở **Tiêu chí 9**. ⚠️ Node văng ra ngoài vẫn làm tiêu chí 6/7/8 PASS giả — overlap=0 vì chúng xa nhau |
| 8 | **Phủ đủ chức năng nguồn (FR Coverage)** (BẮT BUỘC khi nguồn đánh số được) | `set(FR nguồn) − set(FR trong artifact) = ∅` | Script ở **Tiêu chí 8** bên dưới. Đây là tiêu chí DUY NHẤT đối chiếu ngược về tài liệu nguồn — 7 tiêu chí kia chỉ kiểm thứ đã vẽ |

---

## ⚠️ Tiêu chí 6 — Non-empty check bằng CÂY NODE (không bằng mắt)

> **Vì sao bắt buộc:** tiêu chí 1-5 đều là "tự chứng thực bằng mắt" — model nhìn screenshot rồi tự kết luận PASS. Màn hình trống là lỗi **rất dễ lọt** qua cách kiểm tra đó, nhất là khi frame có 20+ screen. Dữ liệu cây node là khách quan và đếm được.

**Nguyên nhân kỹ thuật gây màn hình trống (gặp thực tế khi vẽ Figma bằng script):**

| Nguyên nhân | Dấu hiệu nhận biết |
|---|---|
| Script fail giữa chừng (khung phone tạo xong, nội dung chưa kịp vẽ) | Frame chỉ có 0-2 child |
| Thiếu `figma.loadFontAsync` trước khi tạo text | Text node tồn tại nhưng `characters` rỗng |
| Node đặt sai toạ độ, nằm ngoài khung cha → bị clip | Child count đúng nhưng screenshot trắng |
| Batch quá lớn → plugin timeout giữa chừng | Các screen CUỐI của batch bị trống |
| Fill trắng + text trắng | Có node, có ký tự, nhưng không đọc được |

**Quy trình kiểm tra BẮT BUỘC sau khi vẽ xong mỗi frame:**

1. Chạy 1 `use_figma` read-back script duyệt cây node của frame vừa vẽ
2. In bảng kiểm:

```
EMPTY CHECK — Output <N>
| Screen Code | child count | text node | tổng ký tự | Verdict |
|---|---|---|---|---|
| AX_FEAT_001 | 14 | 9 | 212 | ✅ |
| AX_FEAT_002 | 2  | 0 | 0   | ❌ TRỐNG |
```

3. **FAIL nếu bất kỳ dòng nào:** `child count < 3` **HOẶC** `tổng ký tự = 0` **HOẶC** có vùng trắng liên tục > 400px giữa 2 node liền kề (dấu hiệu node bị mất giữa chừng)
4. FAIL → vẽ lại **ĐÚNG screen đó** (scoped fix), KHÔNG vẽ lại cả frame → quay lại bước 1

**Rule phòng ngừa (áp dụng lúc VẼ, không phải lúc check):**
- Tối đa **5 screen / 1 `use_figma` call** — mỗi call trả về số node đã tạo để đối chiếu kỳ vọng
- Khung phone + nội dung bên trong phải nằm trong **CÙNG 1 call** — không tách 2 call (tránh trạng thái "có khung chưa có ruột" khi call sau fail)
- `figma.loadFontAsync` cho **mọi** font dùng, ngay đầu script (xem skill `figma:figma-use`) — đây là nguyên nhân số 1 gây text rỗng

**Bắt buộc in trong Quality Gate O3:** dòng `Empty check: <X>/<N> screens có nội dung` — KHÔNG được báo "đã vẽ xong" chung chung.

---

## ⚠️ Tiêu chí 7 — Overlap check bằng PHÉP QUÉT BBOX (không bằng mắt) — BẮT BUỘC mọi frame

> **Vì sao bắt buộc:** lỗ hổng đã xảy ra thực tế. Agent chụp screenshot, nhìn bằng mắt rồi kết luận "không chồng đè" và báo PASS — trong khi frame đang có **6 cặp box đè nhau thật** (terminal đè NG box, 2 terminal đè nhau, cột phụ đè lên comb báo cáo). Mắt người/model nhìn ảnh thu nhỏ **không thể** phát hiện overlap 20-50px. Toạ độ thì đếm được.

**Chạy NGAY sau khi vẽ xong mỗi frame, TRƯỚC khi chụp screenshot:**

```js
const F = await figma.getNodeByIdAsync("<frameId>");
const fb = F.absoluteBoundingBox;
const boxes = F.findAll(n => n.type === 'RECTANGLE' && n.width > 100 && n.height > 30)
  .map(n => { const b = n.absoluteBoundingBox;
              return b ? {x:b.x-fb.x, y:b.y-fb.y, w:b.width, h:b.height} : null; })
  .filter(Boolean);
const ov = [];
for (let i=0;i<boxes.length;i++) for (let j=i+1;j<boxes.length;j++){
  const a=boxes[i], b=boxes[j];
  const xo = Math.min(a.x+a.w, b.x+b.w) - Math.max(a.x, b.x);
  const yo = Math.min(a.y+a.h, b.y+b.h) - Math.max(a.y, b.y);
  if (xo > 2 && yo > 2) ov.push({ax:a.x,ay:a.y,aw:a.w,ah:a.h,bx:b.x,by:b.y,bw:b.w,bh:b.h});
}
return {boxChecked: boxes.length, overlapCount: ov.length, overlaps: ov.slice(0,8)};
```

**Rule:**
- Lọc `width>100 && height>30` để chỉ so các **box thật** (bỏ đường kẻ 2px, bỏ row bảng cao 22-26px vốn xếp sát nhau hợp lệ)
- Ngưỡng `>2px` để 2 box chạm mép nhau không bị tính là đè
- Dùng `absoluteBoundingBox` (không dùng `n.x/n.y`) vì sau khi **group** thì `x/y` là toạ độ tương đối so với group → so sánh sẽ sai
- **FAIL nếu `overlapCount > 0`** → đọc toạ độ cặp đè ra, dời node, chạy lại cho đến khi bằng 0
- **Bắt buộc in trong mọi Quality Gate:** dòng `Overlap check: 0 chồng đè / <N> box` — thiếu dòng này thì Quality Gate KHÔNG hợp lệ

**Phòng ngừa lúc vẽ (rẻ hơn sửa):** trước khi đặt 1 box cạnh box khác, tính khoảng trống thật: `gap = X_box_phải − (X_box_trái + W_box_trái)`. Nếu `W_box_mới > gap − 40` thì **đổi chỗ đặt** (xuống hàng dưới / sang cột khác), đừng đặt rồi sửa sau.

---

**Format báo cáo recheck (in ra cho user):**

```
🔍 AI Recheck Report — Output <N>

✅ Tiêu chí 1: Đủ nội dung        (đã đủ 4 zones + Tech Stack)
✅ Tiêu chí 2: Không chồng đè      (đã zoom check 5 điểm giao)
✅ Tiêu chí 3: Text đầy đủ         (tất cả nodes readable)
❌ Tiêu chí 4: Đúng vùng           (AY_FEAT_001 tràn sang Non-Happy zone)
   → Fix: dời CA column sang phải 200px, mở rộng frame width
✅ Tiêu chí 5: N/A cho Output này

Kết quả: FAIL → tiến hành fix rồi chụp lại
```

**Nếu FAIL → không được bỏ qua:** phải fix bằng `use_figma` call sửa layout, sau đó chụp lại và recheck.

**Common overlap patterns cần đặc biệt check:**

- Cross-actor arrow đi ngang qua node column khác
- CA column overlap với Non-Happy zone (như đã từng xảy ra)
- Decision node "Accept?" bị đè bởi label "Yes/No"
- Numbered badge (bên trái node) đè lên border của Zone trước
- Text purpose 1 dòng bị crop vì width không đủ
- Cross-session connector chồng lên In-Call node của phía đối diện
- Non-happy flow trigger box overlap với error node bên dưới
- **Output 3 phone đè bảng dưới nếu dùng grid layout** — dùng layout DỌC
- **Output 1 Tech Stack ngang đè Sitemap** — chuyển Tech thành TABLE bên phải Flow

## ⚠️ Tiêu chí 8 — FR Coverage scan (BẮT BUỘC khi nguồn có danh sách chức năng đánh số)

> Sự cố thực tế: 3 chức năng biến mất khỏi SPEC + cả 3 Figma output, 7 tiêu chí còn lại đều PASS vì không tiêu chí nào đối chiếu ngược về tài liệu nguồn. **Tiêu chí 1-7 chỉ kiểm chất lượng thứ đã vẽ, không kiểm thứ đáng lẽ phải vẽ mà không có.**

**PASS khi:** `set(FR nguồn) − set(FR xuất hiện trong artifact) = ∅`

**Cách chạy — SPEC (cột `FR No.` trong bảng `## Screens`):**

```python
import re
s = open('SPEC.md', encoding='utf-8').read()
TOTAL = 58                      # số dòng chức năng trong nguồn — KHÔNG phải số nhóm
SYSTEM_ONLY = {24}              # chức năng batch/cron, đã ghi chú trong FR Register
frs = set()
for m in re.finditer(r'^\| ([\d, ]+) \| [A-Z]{2}_[A-Z]+_\d{3} \|', s, re.M):
    frs |= {int(x) for x in m.group(1).split(',')}
missing = sorted(set(range(1, TOTAL+1)) - frs - SYSTEM_ONLY)
print(f"FR phủ: {len(frs | SYSTEM_ONLY)}/{TOTAL} · THIẾU: {missing or 'KHÔNG'}")
assert not missing, f"FAIL — thiếu FR {missing}"
```

**Cách chạy — Figma Sitemap Output 1 (tag `#N` trên mỗi Hành động):**

```js
const TOTAL = 58, SYSTEM_ONLY = new Set([24]);   // khai báo mốc TRƯỚC khi dùng
const txt = F.findAll(n => n.type === 'TEXT').map(n => n.characters || "").join(" ");
const seen = new Set();
// ⚠️ PHẢI bắt được cả ô gộp "#19,20,21". KHÔNG dùng /#\d+/g — nó chỉ lấy số ĐẦU TIÊN,
//    làm 20 và 21 bị báo thiếu oan. Lỗi này đã xảy ra thật và suýt khiến agent "sửa" bản vẽ đang đúng.
(txt.match(/#\d+(?:\s*,\s*\d+)*/g) || []).forEach(s =>
  s.slice(1).split(",").forEach(v => {
    const n = +v.trim();
    if (n >= 1 && n <= TOTAL) seen.add(n);
  }));
const missing = [];
for (let i = 1; i <= TOTAL; i++) if (!seen.has(i) && !SYSTEM_ONLY.has(i)) missing.push(i);
return { soFRxuatHien: seen.size, FRthieu: missing,
         ketLuan: missing.length ? "FAIL" : "PASS — đủ " + TOTAL + " FR" };
```

**⚠️ Khi gate báo FAIL — XÁC MINH TRƯỚC KHI SỬA BẢN VẼ:**

Checker sai sẽ tạo FAIL giả, và "sửa" theo nó sẽ **phá hỏng artifact đang đúng**. Đã xảy ra 2 lần. Trước khi đụng vào Figma/SPEC, bắt buộc mở đúng 1-2 node/dòng bị báo thiếu và đọc tận mắt:

| Dấu hiệu FAIL giả | Nguyên nhân thường gặp |
|---|---|
| Các số thiếu đều là **phần tử thứ 2, 3** của ô gộp (thiếu 20,21 khi có `#19,20,21`) | Regex chỉ bắt số đầu |
| Số "thiếu" **nhìn thấy rõ trên frame** | Regex/selector sai, không phải artifact sai |
| `soFRxuatHien` **lớn hơn** TOTAL | Đếm trùng, hoặc cộng nhầm SYSTEM_ONLY vào tập đã chứa nó |
| Hai screen báo số của nhau | Zip theo thứ tự `findAll` (≠ thứ tự Y) thay vì match theo khoá |

**Chỉ sửa artifact sau khi đã tự mắt xác nhận nó thực sự thiếu.**

**Bắt buộc in danh sách thiếu kể cả khi rỗng** — báo "đã phủ hết" mà không in `THIẾU: []` là không hợp lệ.

⚠️ **KHÔNG được thay bằng phép so số lượng** (`số màn ≥ số nhóm`). Xem `granularity-principles.md` § **GATE FR COVERAGE** để biết vì sao phép so số lượng luôn PASS sai.

---

## ⚠️ Tiêu chí 9 — Node phải NẰM TRONG BIÊN FRAME (BẮT BUỘC mọi frame, chạy TRƯỚC Tiêu chí 7)

> **Sự cố thực tế:** một lần vẽ đặt `n.x = frame.absoluteBoundingBox.x + x` **trước** `appendChild`. Vì `node.x` là toạ độ **tương đối frame**, toàn bộ 430 node bị dịch đúng một lượng bằng vị trí tuyệt đối của frame và văng ra ngoài. Hậu quả nguy hiểm: **Tiêu chí 6, 7, 8 đều báo PASS** — overlap = 0 (vì các node văng ra xa nhau nên không đè nhau), text không rỗng, FR vẫn đủ. Bản vẽ trông "đạt mọi gate" trong khi thực tế trống trơn.
>
> Lần chẩn đoán đầu còn sai tiếp: chỉ kiểm tràn **phía dưới** (`y + h > frame.height`), trong khi node bị đẩy lên **y âm** nên lọt lưới. **Phải kiểm đủ 4 phía.**

**PASS khi:** mọi node lá nằm trong `[0, frame.width] × [0, frame.height]`

```js
const F = await figma.getNodeByIdAsync("<frameId>");
const fb = F.absoluteBoundingBox;
const outside = [];
for (const n of F.findAll(x => (x.type === 'TEXT' || x.type === 'RECTANGLE') && x.absoluteBoundingBox)) {
  const b = n.absoluteBoundingBox;
  const x = b.x - fb.x, y = b.y - fb.y;
  if (x < 0 || y < 0 || x + b.width > F.width || y + b.height > F.height)   // ĐỦ 4 PHÍA
    outside.push({ t: ('characters' in n ? n.characters : n.name).slice(0,30), x: Math.round(x), y: Math.round(y) });
}
return { soNodeNgoaiFrame: outside.length, viDu: outside.slice(0, 8),
         ketLuan: outside.length ? "FAIL — có node ngoài frame" : "PASS" };
```

**Cách sửa khi FAIL:** dịch node lá về bằng `n.x -= fb.x; n.y -= fb.y`. **Chỉ dịch node lá (TEXT/RECTANGLE), TUYỆT ĐỐI không dịch GROUP** — group thường chứa cả node đang đúng chỗ, dịch group sẽ làm hỏng phần đang đúng.

**Dấu hiệu nhận biết sớm (không cần chạy script):**

| Dấu hiệu | Ý nghĩa |
|---|---|
| `get_screenshot` trả `original_height`/`original_width` **khác** kích thước frame | Có node ngoài biên đang kéo giãn vùng render — KHÔNG được bỏ qua như "artifact của tool" |
| Bounding box của 1 GROUP phình to bất thường (VD `w` 480 → 2949) | Group đang ôm cả node văng ra ngoài |
| Đếm node trong 1 vùng toạ độ cụ thể ra **0** dù vừa vẽ xong | Node không nằm ở nơi tưởng là đã đặt |

---

**Khi tất cả 3 Outputs PASS → mới báo user thành công.**
