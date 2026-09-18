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

**Khi tất cả 3 Outputs PASS → mới báo user thành công.**
