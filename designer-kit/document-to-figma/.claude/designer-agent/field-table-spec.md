# Field Description Table — bảng mô tả các trường trong màn hình

> **BẮT BUỘC** sau khi vẽ xong màn hình (Bước 5.6 / K8 của `designer-agent.md`). Là **output thứ 2 của Designer** cạnh Figma frames và Screen Index (`screen-index-spec.md`).
> Mục đích: dev/QC/BA mở Figma là thấy **từng trường (item) trên màn hình** — loại input, bắt buộc, min/max, điều kiện hiển thị, trigger, validation, ví dụ, error message — ở cả JP và VI.
> Format mẫu: node `34325:198362` (group LOGIN, file `VKAAOyoSPvgoB3H2qdeeV3`) — 1 banner "Flow note" xanh + 1 bảng 2 nửa (JP | VI).

---

## 1. Nguyên tắc nguồn dữ liệu — **KHÔNG SUY DIỄN**

| Thứ tự ưu tiên | Nguồn | Cách lấy |
|---|---|---|
| 1 | **Tài liệu có sẵn item** (HTML prototype, tài liệu thiết kế) (vd file `Thiết_kế_màn_hình_*.html` có `window.KD_DATA.views[].rows[]`) | Copy **nguyên văn** từng trường. Không viết lại, không rút gọn, không dịch lại |
| 2 | `SPEC.md` → `## Screen Details` / `## Screens` / Basic Design (.xlsx) / tài liệu user đã chọn ở Bước 0 | Copy nguyên văn các cột tương ứng |
| 3 | Không có cả 2 | **DỪNG, hỏi user** (AskUserQuestion: cung cấp nguồn / cho phép Designer đề xuất & đánh dấu `[Đề xuất]`). Không tự bịa |

- Ô nguồn để trống → để `-` (không tự điền).
- Nguồn không có cột MIN/MAX riêng → dùng 1 cột `桁数・範囲` lấy nguyên văn từ trường `len`.
- Mỗi hàng phải truy ngược được về 1 dòng của nguồn (cùng số `No`).

## 2. Cấu trúc 1 khối (1 khối / 1 màn hình chính)

```
Fields · <Screen Code>                (FRAME dọc, gap 24, không nền)
├─ Flow note                          (banner xanh: ✅ <CODE> <tên ja> | <tên vi>  ……  Nguồn: <file> · trạng thái #<n> · <N> mục)
└─ Table                              (rộng 4268; 1 header row + N hàng)
```

- Banner: nền `#EAFBF0`, viền 3px `#1CCE66`, radius 8, chữ `#1CCE66` Bold 36; bên phải ghi nguồn (22px). Tên màn **gắn hyperlink NODE** tới frame màn hình đã vẽ.
- **1 khối cho mỗi màn hình chính**; popup/biến thể cùng Screen Code dùng chung khối của màn chính (ghi chú ở dòng nguồn). Nếu popup có hàng item riêng trong nguồn thì thêm khối riêng `Fields · <CODE>-<popup>`.
- Màn hình có nhiều trạng thái (state) trong nguồn: chọn **trạng thái đầy đủ nhất** (thường `#001`/state khởi tạo) cho khối; ghi `Nguồn: … trạng thái #<n>`.

## 3. Cột (24 cột = 12 JP + 12 VI, theo đúng mẫu `34325:198362`)

| # | JP (header) | VI (header) | Nguồn (tài liệu, vd `rows[]`) | Rộng |
|---|---|---|---|---|
| 1 | No | No | `no` | 62 |
| 2 | 項目名 | Tên mục | `ja` / `vi` | 192 |
| 3 | 必須 | Bắt buộc | `reqP[0]` / `reqP[1]` | 90 |
| 4 | 入力形式 | Loại input | `kind[0]` / `kind[1]` | 120 |
| 5 | 桁数・範囲 | Độ dài / phạm vi | `len[0]` / `len[1]` | 150 |
| 6 | 初期値 | Giá trị ban đầu | `init[0]` / `init[1]` | 140 |
| 7 | 表示条件 | Điều kiện hiển thị | `cond[0]` / `cond[1]` | 140 |
| 8 | 詳細 | Chi tiết | `detail[0]` / `detail[1]` | 420 |
| 9 | トリガー | Trigger | `trig[0]` / `trig[1]` | 100 |
| 10 | バリデーション | Validation | `valid[0]` / `valid[1]` | 260 |
| 11 | 例 | Ví dụ | `ex[0]` / `ex[1]` | 160 |
| 12 | エラーメッセージ | Error message | `err[*][0]` nối `\n` / `err[*][1]` nối `\n` | 300 |

- Nửa VI lặp lại cột `No`. **Bỏ** `編集可否` và `検証タイミング` của mẫu vì tài liệu không có dữ liệu tương ứng (không suy diễn). Nếu nguồn có → thêm cột.
- Cột `詳細` rộng nhất và **xuống dòng** (không cắt chữ).

## 4. Style (đo từ mẫu)

| Phần tử | Giá trị |
|---|---|
| Header row | nền `#CDF4D3`, chữ Bold 14, cao ≥ 64 |
| Cột `No` + `項目名`/`Tên mục` (cả 2 nửa) | nền `#CDF4D3`, chữ Bold |
| Ô thường | nền trắng, viền 1 `#C9CFD6`, chữ Regular 14 `#1E1E1E`, padding 10/8, cao tối thiểu 48, **hug theo nội dung** |
| Ô rỗng | `-` |
| Font | Family của Design System dự án; có JP/VI thì chọn family hỗ trợ glyph (vd Noto Sans JP). Mẫu dùng Inter 16 — không dùng nếu thiếu glyph |

## 5. Vị trí trên canvas

- Tạo **SECTION riêng** cho bảng mô tả trường của mỗi group, đặt **ngay dưới** section màn hình tương ứng (cách ≥ 500px), tên: `AI_Generate_Mô tả trường | <tên group>`. Rộng ≈ 4428.
- Trong section: các khối xếp dọc theo thứ tự Screen Code, cách nhau 300px (script `relayout`).
- Không đặt đè lên frame màn hình hoặc Screen Index.

## 6. Cách dựng

> Figma Plugin API ở file Design **không có `figma.createTable`** (chỉ FigJam). Dùng auto-layout: Table = frame dọc; mỗi row = frame ngang; mỗi cell = frame dọc FIXED width, `layoutSizingVertical = FILL` để cả hàng cao bằng ô cao nhất.

1. Trích dữ liệu từ nguồn → file JSON trung gian (mỗi khối ≤ ~45k ký tự/lần gọi `use_figma`; vượt thì tách nhiều lần, section dùng lại theo tên).
2. Lưu builder (≈4.4k ký tự) bằng `page.setSharedPluginData('<namespace ≥ 3 ký tự>', 'fieldlib', LIB)` → mỗi lần gọi nạp lại bằng `new AsyncFunction('figma', LIB)(figma)`; **xóa** (`setSharedPluginData(..., '')`) khi xong.
3. Với mỗi màn: tạo khối (banner + table), banner hyperlink NODE → frame màn.
4. `relayout(section)` sắp xếp theo tên, đặt lại y; resize section.
5. `get_screenshot` 1–2 khối, kiểm tra không cắt chữ, cột đúng, số hàng = số dòng nguồn.

## 7. Definition of Done — Field Table
- [ ] Mỗi màn hình chính có 1 khối `Fields · <CODE>`; banner hyperlink đúng frame.
- [ ] **Số hàng = số dòng của nguồn** (đối chiếu bằng script đếm), nội dung nguyên văn, không suy diễn.
- [ ] JP | VI song song, đủ 24 cột; ô rỗng = `-`.
- [ ] Style đúng §4; không cắt chữ.
- [ ] Section nằm dưới section màn hình, không chồng frame; builder lib đã xóa khỏi plugin data.
- [ ] Ghi vào `output/<feature>/screen-index.md` mục "Field tables" (node ID từng khối) và cập nhật dòng chân của frame Screen Index.
