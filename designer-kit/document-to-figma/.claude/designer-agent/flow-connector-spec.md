# Flow Connectors (đường nối giữa các màn hình)

> **BẮT BUỘC** sau khi vẽ xong màn hình (Bước 5.7 của `.claude/agents/designer-agent.md`). Mục đích: ai mở Figma cũng thấy **màn nào dẫn tới màn nào, bằng hành động gì** — không phải đoán thứ tự các frame.
> Format mẫu (đã đo): section `AI_Generate_Tồn Kho Company | 棚卸報告 (法人Web)`, node `34847:83576`, file `VKAAOyoSPvgoB3H2qdeeV3` — 25 màn · 24 đường nối · 1 legend.

---

## 1. Nguyên tắc

| # | Rule |
|---|---|
| 1 | **Mọi màn hình trong section phải nằm trên ít nhất 1 đường nối** (vào hoặc ra). Màn mồ côi = chưa xong. Màn vào đầu tiên (entry) chỉ cần đường ra |
| 2 | **1 chuyển tiếp = 1 đường nối + 1 nhãn**. Không có đường nối "trơn" không nhãn |
| 3 | Chuyển tiếp lấy từ **nguồn**: prototype / `SPEC.md ## Flow Tổng Quan` · `## Screen Details` (cột Navigation) / tài liệu thiết kế. **KHÔNG tự suy** màn A dẫn tới màn B. Nguồn không nói → `AskUserQuestion`, không nối bừa |
| 4 | Đường nối **không được xuyên qua thân frame màn hình** — chỉ chạy trong khe giữa các cột/hàng hoặc lề ngoài |
| 5 | Mũi tên luôn ở **đầu đích**. Một chiều. Hai chiều thật sự → 2 đường riêng, 2 nhãn |

## 2. Style (đo từ file mẫu)

| Thuộc tính | Giá trị | Token |
|---|---|---|
| Màu đường + mũi tên | `#0A69D9` | `colors.primitives.blue.500` |
| Độ dày nét | **3 px**, góc vuông (miter), không bo | — |
| Mũi tên | Tam giác đặc ≈ **17 × 15 px**, đầu nhọn chạm đúng mép đích | — |
| Tên node đường | `flow · <nhãn JP>` | — |
| Tên node nhãn | `flowlabel · <nhãn JP>` | — |
| Nhãn — font | Noto Sans JP **Medium 14px**, màu `#0A69D9` | `font.text sm.medium` (14/20) |
| Nhãn — nội dung | **2 dòng**: dòng 1 = JP (hành động/điều kiện), dòng 2 = VN | — |
| Legend | Noto Sans JP Medium **18px**, màu `#424A54` | `colors.components.text.middle` |

## 3. Hình học

Lưới màn hình trong mẫu: frame rộng **1440**; bước cột **1800** (khe ngang **360**); khe dọc giữa hàng **≥ 640**. Giữ đúng để có chỗ cho đường nối và nhãn.

| Loại | Điểm đầu → điểm cuối | Nhãn đặt |
|---|---|---|
| **Ngang** (màn kề nhau cùng hàng) | mép phải A → mép trái B, dài đúng khe 360; cao độ = phần tử kích hoạt (mẫu: `A.y + 260`) | Phía **trên** đường: `x = đầu đường + 10`, `y = đường − 52`, rộng 340 × cao 34 |
| **Dọc** (A trên, B dưới cùng cột) | giữa đáy A (`A.x + 720`) → giữa đỉnh B | Bên phải đường: `x = đường + 14`, `y = A.bottom + 30` |
| **Khuỷu** (đích ở hàng khác / không kề) | từ đáy A đi xuống vào **kênh ngang** nằm trong khe giữa hai hàng → chạy ngang → rẽ xuống đỉnh B (mũi tên ngay trên label của B) | Trên đoạn ngang, cách điểm rẽ ~ 30 px |
| **Quay lại / vòng** (về màn trước đó) | thoát mép trái A → đi ra **lề trái** (`x = cột đầu − 150`) → xuống/lên → vào mép trái đích | Cạnh đoạn dọc ở lề, rộng 150 |
| **Tỏa nhánh** (1 màn → nhiều biến thể) | **1 trục chung** đi xuống từ A, 1 kênh ngang, mỗi biến thể 1 nhánh rẽ xuống + **nhãn riêng** | Mỗi nhánh 1 nhãn, đặt cạnh điểm rẽ xuống |

- Nhiều đường cùng xuất phát từ **một** màn: lệch điểm xuất phát (so le ±280 px quanh tâm) để không chồng đè — mẫu: `4720` và `5000` cùng thoát từ frame tâm `4720`.
- Hai đường dùng chung 1 kênh ngang được phép chồng đoạn chung (trục tỏa nhánh), **không** được chồng đoạn có nhãn khác nhau.

## 4. Legend (1 khối, trên-trái cụm section)

`legend · state flow` — y ≈ 80 phía trên hàng nhãn màn hình đầu tiên, 3 dòng 18px `#424A54`:
1. Tiêu đề: `Luồng trạng thái · <JP>`
2. Ý nghĩa: `Mũi tên xanh = hành động/điều kiện chuyển từ màn hình này sang màn hình khác (nguồn: <tài liệu>, <N> view)`
3. Cách đọc các hàng: `Hàng 1: <luồng chính> · Hàng 2: <lỗi / modal> · …`

## 5. Cách dựng (Plugin API)

```js
// Lấy toạ độ từ frame đã vẽ — KHÔNG hard-code
const A = figma.getNodeById(idA), B = figma.getNodeById(idB)
const BLUE = {r:0x0A/255, g:0x69/255, b:0xD9/255}

function flow(points, jpLabel) {                 // points: [[x,y],...] toạ độ tuyệt đối trong section
  const v = figma.createVector()
  v.name = `flow · ${jpLabel}`
  v.vectorPaths = [{ windingRule: 'NONE',
    data: points.map((p,i)=>`${i?'L':'M'} ${p[0]} ${p[1]}`).join(' ') }]
  v.strokes = [{type:'SOLID', color: BLUE}]
  v.strokeWeight = 3; v.strokeJoin = 'MITER'; v.fills = []
  // mũi tên: tam giác 17×15 đặt tại điểm cuối, xoay theo hướng đoạn cuối
  const tip = points[points.length-1]
  const head = figma.createPolygon(); head.pointCount = 3
  head.resize(17, 15); head.fills = [{type:'SOLID', color: BLUE}]
  head.name = `flow · ${jpLabel} · arrow`
  // ... đặt tâm head sao cho đỉnh nhọn = tip; rotation: xuống 0° · phải -90° · trái 90° · lên 180°
  return [v, head]
}
```

> ⚠️ Đoạn code trên là **mẫu cấu trúc**, chưa chạy thử trong repo này. Sau khi dựng PHẢI `get_screenshot` kiểm mũi tên chạm đúng mép, đúng hướng — không tin code mà không nhìn ảnh.
> Nếu `fromPath` / `strokeCap = ARROW_EQUILATERAL` hoạt động trong file của bạn thì dùng được thay cho tam giác rời; chốt cách nào thì dùng thống nhất cả section.

Nhãn: `figma.createText()` → `loadFontAsync({family:'Noto Sans JP', style:'Medium'})`, `characters = jp + '\n' + vn`, `fontSize 14`, màu `BLUE`, `textAutoResize = 'HEIGHT'`, `resize(340, …)`.

## 6. Kiểm tra (DoD) — trước khi báo xong

| # | Kiểm tra | Cách |
|---|---|---|
| 1 | **Không màn mồ côi**: mọi frame màn hình có ≥ 1 đường vào/ra (trừ khi nguồn nói đó là màn độc lập — ghi chú ở legend) | Lập bảng `frame → số đường`; phải không có số 0 |
| 2 | Số đường nối = số chuyển tiếp trong nguồn | Đối chiếu danh sách chuyển tiếp đã lập ở Bước 5.7a |
| 3 | Mỗi đường có 1 nhãn 2 dòng JP/VN, nằm trên/cạnh đường, không chồng frame | `get_screenshot` + quét bbox nhãn vs frame |
| 4 | **Không đường nào xuyên thân frame** | Script: với mỗi đoạn thẳng của đường, kiểm giao với bbox mọi frame màn hình (trừ đúng frame nguồn/đích ở điểm đầu/cuối) → 0 giao |
| 5 | Mũi tên chạm mép đích, đúng hướng | `get_screenshot` phóng đại từng điểm cuối |
| 6 | Style đúng §2 (màu, 3 px, 17×15, font nhãn) | `get_design_context` 1 đường + 1 nhãn |
| 7 | Có legend §4 | — |
| 8 | Ghi vào `screen-index.md` bảng chuyển tiếp: `Từ → Đến · Nhãn JP · Nhãn VN · node ID đường` | — |

## 7. Cấm

- ❌ Nối theo thứ tự frame trên canvas thay vì theo nguồn
- ❌ Đường không nhãn / nhãn chung chung ("Tiếp theo")
- ❌ Đường xuyên qua thân frame; đường chồng lên nhãn của frame khác
- ❌ Vẽ mũi tên bằng text `→` hoặc ký tự
- ❌ Bỏ màn hình khỏi flow vì "khó nối" — hỏi user
- ❌ Sửa/xoá đường nối của lần vẽ trước khi chưa hỏi (scoped update — chỉ thêm/sửa đường thuộc phạm vi yêu cầu)
