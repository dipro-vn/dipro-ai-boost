# CR view trên Figma (Luồng 2) — format Output 1 / Output 2 + màn đề xuất theo Design System

> Chuẩn vẽ view CR của kit này = **kit `requirement-to-flow` `ba-agent/change-request.md` §3** (CR-1 Flow · CR-2 Screen Flow · CR-3 Screens · CR Change Table, badge NEW/UPD/DEL/AS-IS) + **khung Output 1 / Output 2 mà Luồng 1 đã vẽ** (`output-1-flow.md`, `output-2-screen-flow.md`). Kit này thêm badge `IMPACT` (bị kéo theo) và CR Change Table dạng **thống kê**.
>
> **Agent viết nội dung** (`_internal/cr-figma.json`), **script vẽ + kiểm**: `render-cr-figma.py` sinh JS → `use_figma` chạy từng file → `99-readback.js` → `verify-cr-figma.py` (V-CR-FIGMA). Không tự viết JS vẽ tay (bố cục lệch Output 1/2 là lỗi đã xảy ra — feedback CR-001).

---

## 1. Bốn sub-view trong 1 Section mới

| Sub-view | Format bắt buộc | Nội dung | Không được |
|---|---|---|---|
| **CR-1 Flow** | Output 1 **Phần A** (lane `FL-xx`: ACTOR → TRIGGER → FUNCTION → TECHNOLOGY → OUTCOME · cột EDGE / EXCEPTIONAL) + **Phần B** Technology | Chỉ lane `FL-xx` của baseline bị CR chạm + lane nghiệp vụ mới (`CR-NEW-n`). Cột Technology bên phải chỉ công nghệ NEW / UPD / IMPACT | Vẽ lại toàn bộ 10 lane; liệt kê thẻ rời không mũi tên |
| **CR-2 Screen Flow** | Output 2 **Group** (Start ▶ · Screen · ◇ Decision · System · NG inline · Terminal) + panel **Edge/Exceptional** + bảng **④ Screen Index** (phạm vi CR) | 1 Group / cụm màn bị chạm, mỗi site 1 Group riêng. Chỉ màn có dòng Impact (Screen) + màn dẫn tới (AS-IS) | Lưới thẻ không mũi tên; vẽ màn ngoài phạm vi |
| **CR Change Table** | Bảng **thống kê** | Số đối tượng thay đổi theo `NEW / UPD / DEL / IMPACT / Tổng / 実装 MD` × Màn hình · API · Batch · Bảng DB · Cột DB · Rule nghiệp vụ · Liên kết bên thứ 3 · Mockup · Token DS + 実装 MD · 総工数 人日 · 人月 · 最小改修案 / 拡張案 | Liệt kê lại từng hạng mục (chi tiết nằm ở `CR-<id>_Impact.xlsx`) |
| **CR-3 Screens** | Màn đề xuất dựng từ **token + component Design System baseline** | Màn theo phạm vi user chọn ở **CR-3** (câu hỏi §3) | Vẽ trước khi đọc Design System; tự chế màu / component |

Vị trí: Section `CR-<id> — <tiêu đề> (baseline ver<K> → ver<N>)` dưới bbox thấp nhất của node cũ **≥ 400 px**. Không `remove / move / resize / recolor / relabel` node Output 1/2 baseline hay CR khác.

## 2. Badge — mọi node đúng 1 badge, tên `<BADGE> · <REF> · <nhãn>`

| Badge | Fill / stroke | Dùng cho |
|---|---|---|
| `NEW` | `#EDFDF0` / `#1A7F37` | thêm mới |
| `UPD` | `#FFF9EB` / `#F4860C` nét đứt | sửa (sub-text "cũ → mới") |
| `DEL` | `#FFF6F5` / `#CF222E` nét đứt, gạch ngang | bỏ |
| `IMPACT` | `#FBEEFF` / `#6639BA` nét đứt | không sửa nhưng bị kéo theo — ghi "qua <API / table>" |
| `AS-IS` | `#F6F8FA` / `#D0D7DE`, opacity 0.6 | ngữ cảnh: hàng xóm 1 bước hoặc lane `FL-xx` baseline |

`REF` = Baseline Ref của dòng Impact (SC-/F-/API-/EXT-/`table:`/`column:`) · hạng mục NEW chưa có trong baseline → **Impact ID**. NG giữ ngữ nghĩa Output 2 bằng **vạch đỏ bên trái** + tiền tố `NG ·` (màu nền vẫn là badge). Decision `◇`, Start `▶`. Legend ở góc trên trái Section.

## 3. Câu hỏi (AskUserQuestion) trước khi vẽ

```
CR-2. Vẽ view CR lên Figma?
  [A] Có — cùng file flow của baseline (<figma_output_url>)   [B] Có — file/page khác (Other: link)   [C] Không vẽ lần này
CR-3. Màn đề xuất (CR-3 Screens) — phạm vi?   (chỉ hỏi khi CR-2 = A/B; luôn hỏi, kể cả khi chỉ có 1 màn)
  [A] Màn NEW   [B] Màn NEW + UPD   [C] Chọn màn (Other: Impact ID)   [D] Không vẽ màn đề xuất
CR-3b. (chỉ khi màn cần component Design System của site chưa có — STATUS.md ghi TBD)
  <Component> chưa có ở <WEB-xx>, site <WEB-yy> có. Xử lý:
  [A] Mượn mẫu của <WEB-yy>, ghi "MƯỢN — chờ designer" trên màn   [B] Bỏ block đó, ghi UI-TOKEN-NEW + CQ cho designer
```
Không hỏi CR-3b → không được dùng component site khác. Câu trả lời ghi vào run-log.

## 4. Đọc Design System TRƯỚC khi vẽ CR-3 (bắt buộc — máy kiểm)

1. Với mỗi site có màn đề xuất, **Read**: `outputs/<baseline>/04_DesignSystem/<WEB-xx>/project/README.md` → `tokens.json` → `components/<Comp>/README.md` của component sẽ dùng → `../STATUS.md` (TBD).
2. Ghi danh sách file đã đọc vào `cr-figma.json → screens.ds_read`. Thiếu README / tokens của site → `render-cr-figma.py` **từ chối sinh JS**, V-CR-FIGMA check 10 FAIL.
3. Mỗi block màn chỉ dùng component có trong DS của site (`BLOCK_COMP` trong script). Component chưa có → khai `"from": "<WEB-yy>"` theo câu CR-3b; không khai → script từ chối.
4. Màu / chữ / bo góc / chiều cao control lấy từ `tokens.json` (renderer đọc thẳng). V-CR-FIGMA đọc ngược mọi màu fill trong màn → **màu ngoài token của site (và site mượn) = FAIL**.
5. Font DS không có trên Figma (VD Hiragino Kaku Gothic Pro) → renderer dùng Noto Sans JP và **ghi rõ trên màn** "font thay thế". Không im lặng đổi.
6. Dữ liệu trên màn: bộ mẫu `DATA-PRIVACY.md` §4 (Nguyễn Văn A / 山田太郎 · `user_a@example.com` · `090-0000-0000` · `SO-0001` · `1,000` · Công ty ABC). Figma là cloud — không dữ liệu thật.

## 5. `cr-figma.json` (agent viết)

```json
{"title": "団体利用登録・団体利用受付機能",
 "flows": [{"lane": "FL-08", "title": "Mua vé & thanh toán → đặt chỗ đoàn", "note": "...",
            "nodes": [{"key": "a", "col": "actor", "badge": "NEW", "ref": "IMP-033", "label": "Người phụ trách đoàn", "sub": "..."},
                      {"key": "f2", "col": "function", "row": 1, "type": "decision", "badge": "IMPACT", "ref": "table:ticket_booking_schedules", "label": "Còn chỗ (dùng chung)?"}],
            "edges": [["a", "t", ""], ["f", "f2", "", ""], ["f2", "ng", "NG", "ng"]]}],
 "tech": [{"badge": "UPD", "ref": "EXT-001", "label": "GMO Payment Gateway", "sub": "đổi số tiền giao dịch"}],
 "screen_groups": [{"id": "G1", "title": "Đặt chỗ đoàn", "site": "WEB-02",
                    "nodes": [{"key": "s", "type": "start", "badge": "AS-IS", "ref": "SC-046", "label": "Vào từ お知らせ / URL riêng"},
                              {"key": "n1", "type": "screen", "badge": "NEW", "ref": "IMP-047", "label": "団体専用予約"},
                              {"key": "e1", "type": "edge", "badge": "IMPACT", "ref": "table:ticket_booking_schedules", "label": "Sức chứa dùng chung — CQ-010"}],
                    "edges": [["s", "n1", ""]]}],
 "screens": {"ds_read": ["outputs/ver1_.../04_DesignSystem/WEB-02/project/README.md", "outputs/ver1_.../04_DesignSystem/WEB-02/project/tokens.json"],
             "items": [{"badge": "NEW", "ref": "IMP-046", "site": "WEB-02", "shell": "auth", "label": "[WEB-02] 団体登録",
                        "blocks": [{"t": "title", "text": "団体登録"}, {"t": "field", "label": "団体名・法人名", "required": true, "placeholder": "例：Công ty ABC"},
                                   {"t": "table", "cols": ["No", "領収書番号"], "rows": [["1", "R-0001"]], "from": "WEB-01"},
                                   {"t": "buttons", "items": [{"text": "確認する", "variant": "solid"}]}]}]}}
```
- `col` (CR-1): `actor · trigger · function · technology · outcome · edge`; `row` ≥ 1 cho decision / NG treo dưới. `type` (CR-2): `start · screen · decision · system · ng · terminal · edge`.
- Cạnh `[from, to, nhãn, kiểu]` — kiểu `ng` (đỏ), `cross` (xanh lá, khác actor), rỗng (xanh dương). **Mọi node trừ `edge`/`tech` phải có ≥ 1 cạnh.**
- Shell CR-3: `public` (AppHeader + PageHeader giữa) · `mypage` (AppHeader + SideNav マイページ) · `admin` (SideNav admin + PageHeader) · `auth`. Block: `title · breadcrumb · section · text · field · field2 · select · radio · checkbox · buttons · table · badge · card · steps · modal · search · pagination`.

## 6. Chạy

```bash
S=.claude/skills/system-analyst/scripts; V=outputs/<ver CR>; BL=outputs/<baseline>
# 0. use_figma đọc bbox thấp nhất của page (get_metadata) -> Y = đáy + 400
python3 $S/render-cr-figma.py --cr-json $V/_internal/cr.json --view $V/_internal/cr-figma.json --baseline $BL \
    --rates .claude/config/md-unit-rates.json --page-id <page id> --y <Y> --out-dir $V/_internal/figma-js
# 1. use_figma lần lượt: 01-shell-flow.js · 02-screen-flow.js · 03-change-table.js · 04-screens-*.js
#    (mỗi call trả bottom/created; lỗi → section chưa đủ: chỉ xoá section của CHÍNH lần chạy này rồi chạy lại từ 01)
# 2. use_figma 99-readback.js -> lưu kết quả thành $V/_internal/cr-figma-nodes.json
python3 $S/verify-cr-figma.py --nodes $V/_internal/cr-figma-nodes.json --cr-json $V/_internal/cr.json \
    --baseline $BL --view $V/_internal/cr-figma.json --out $V/_internal/gates/v-cr-figma.md
# 3. 1 screenshot cả Section (scale nhỏ) để soát chữ bị cắt / chồng — không thay gate
```
V-CR-FIGMA: 1 tên/badge · 2 node → impact thật · 3 màn / luồng bị chạm đều vẽ · 4 AS-IS chỉ hàng xóm 1 bước / lane FL baseline · 5 Change Table = thống kê khớp cr.json · 6 trùng (WARN) · 7 mũi tên thật · 8 legend + không node thiếu badge · 9 không chồng node cũ · 10 CR-3 bám DS. `FAIL = 0` mới được báo xong.
