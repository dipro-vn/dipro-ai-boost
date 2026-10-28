# CR view trên Figma (Luồng 2) — format Output 1 / Output 2 + màn đề xuất theo Design System

> Chuẩn vẽ view CR của kit này = **kit `requirement-to-flow` `ba-agent/change-request.md` §3** (CR-1 Flow · CR-2 Screen Flow · CR-3 Screens · CR Change Table, badge NEW/UPD/DEL/AS-IS) + **khung Output 1 / Output 2 mà Luồng 1 đã vẽ** (`output-1-flow.md`, `output-2-screen-flow.md`). Kit này thêm badge `IMPACT` (bị kéo theo) và CR Change Table dạng **thống kê**.
>
> **Quy định bố cục section theo site (20/10/2026):** hệ thống có > 1 site (VD site người dùng + site admin) → **mỗi site 1 Section riêng, không gộp chung** — áp cho **CR-2 Screen Flow** (`CR-2 Screen Flow · <nhãn site> (WEB-xx)`, ④ / ⑦ theo site) và **CR-3 Screens**. Trong section: **site → flow nghiệp vụ → danh sách màn** (CR-3: mỗi flow 1 Section con `Flow <id> — <tên>`; CR-2: mỗi Group = 1 flow). **Section CR-3 nền `#9DA5AD`.** Nhãn / thứ tự site: `site_labels`, `site_order` trong `cr-figma.json`; mỗi màn CR-3 bắt buộc `flow` (id Group CR-2 / lane FL-xx; khác thì thêm `flow_title`). Gate V-CR-FIGMA **check 14**.
>
> **Bản sửa theo feedback CR-001 r2 (14/10/2026):** view CR phải có **NON-HAPPY CASE** ở CR-1 và CR-2 (giống Output 1/2 của requirement-to-flow), **Screen Index có cột Loại** (List / Form / Modal / Popup…), **CR-3 theo format Output 3**: mockup bên trái + mô tả bên phải (mục đích, logic, bảng ITEMS, bảng ERROR SCENARIOS), có cả **màn UPD** (vẽ màn AS-IS và **tô màu phần thay đổi**) và **popup / màn lỗi**. Thiếu → renderer từ chối sinh JS, gate V-CR-FIGMA check 11–13 FAIL.
>
> **Agent viết nội dung** (`_internal/cr-figma.json`), **script vẽ + kiểm**: `render-cr-figma.py` sinh JS → `use_figma` chạy từng file → `99-readback.js` → `verify-cr-figma.py` (V-CR-FIGMA). Không tự viết JS vẽ tay (bố cục lệch Output 1/2 là lỗi đã xảy ra — feedback CR-001).

---

## 1. Bốn sub-view trong 1 Section mới

| Sub-view | Format bắt buộc | Nội dung | Không được |
|---|---|---|---|
| **CR-1 Flow** | Output 1 **dạng use case** (20/10/2026): mỗi lane `FL-xx` = 1 use case — **Actor → đường đi happy (trái → phải) → ✓ KẾT THÚC**, hàng dưới **◇ → NG → ✗ KẾT THÚC**; case chưa chốt = chip "CHƯA CHỐT" dưới lane · bảng **TECHNOLOGY** bên phải (API / bảng / hệ thống ngoài NEW / UPD / IMPACT) | Chỉ lane `FL-xx` của baseline bị CR chạm + lane nghiệp vụ mới (`CR-NEW-n`). **Mỗi lane ≥ 1 nhánh NON-HAPPY**: `◇ decision` → `NG` (đỏ, message thật / đề xuất + đi đâu sau đó) — lane thật sự không có lỗi thì `no_ng: "<lý do>"`. Cột Technology bên phải chỉ công nghệ NEW / UPD / IMPACT | Vẽ lại toàn bộ 10 lane; liệt kê thẻ rời không mũi tên; **lane chỉ có happy path**; **đưa API / bảng / thư viện vào lane** (renderer từ chối) |
| **CR-2 Screen Flow** | Output 2 **site → use case → section** — mỗi Group (= 1 use case) nằm trong **Section con** `Flow <id> — <tên>` của Section site; trong Group (Start ▶ · Screen · ◇ Decision · System · NG inline · **⚠ Popup / màn lỗi** · Terminal) + panel **Edge/Exceptional** + **④ Screen Index** (`# · Ref · Màn hình · Loại · Mô tả · Site · Badge`, **kể cả popup**, dòng `TỔNG = A màn chính + B popup / màn lỗi`) + **⑦ Error / Popup Index** (`E-ID · Màn cha · Hiển thị · Trigger · Message · Đi đâu`) | **Mỗi site 1 Section riêng** (`CR-2 Screen Flow · <site>`, ④ Screen Index + ⑦ của site đó); trong section mỗi Group = 1 flow nghiệp vụ. Chỉ màn có dòng Impact (Screen) + màn dẫn tới (AS-IS). **Mỗi Group ≥ 1 NG / popup lỗi** (hoặc `no_ng`) | Lưới thẻ không mũi tên; vẽ màn ngoài phạm vi; **Screen Index không có cột Loại**; group không có màn / popup lỗi |
| **CR Change Table** | Bảng **thống kê** | Số đối tượng thay đổi theo `NEW / UPD / DEL / IMPACT / Tổng / 実装 MD` × Màn hình · API · Batch · Bảng DB · Cột DB · Rule nghiệp vụ · Liên kết bên thứ 3 · Mockup · Token DS + 実装 MD · 総工数 人日 · 人月 · 最小改修案 / 拡張案 | Liệt kê lại từng hạng mục (chi tiết nằm ở `CR-<id>_Impact.xlsx`) |
| **CR-3 Screens** | **Format Output 3** (requirement-to-flow `output-3-screens.md`): mỗi màn 1 hàng — **mockup BÊN TRÁI** dựng từ token + component Design System · **mô tả BÊN PHẢI**: Loại · Vào từ · Mục đích · Thay đổi so với AS-IS · Logic Happy · bảng **ITEMS** (`# · Item · Mô tả · Action / Behavior · Thay đổi`) · bảng **ERROR SCENARIOS** (`# · Trigger · Hiển thị · Message + Action tiếp theo`) | **Ưu tiên clone UI thật của designer** (khi file Figma có page thiết kế FINAL UI / デザイナー用): copy màn tương ứng, chỉ sửa phần CR đổi, khoanh thay đổi bằng khung nét đứt + nhãn số (không phủ lên UI), gắn plugin data `crkit:src` = node nguồn; màu thật chưa có token DS → V-CR-FIGMA check 10 WARN (bổ sung DS), không FAIL. Lịch tháng tham khảo bố cục lưới 7 cột (ô ngày + trạng thái, ngày tháng khác tô xám, ngày đang chọn viền nổi bật). Chỉ dựng từ token khi không có thiết kế thật. **Site → flow nghiệp vụ → màn**: mỗi site 1 Section `CR-3 Screens · <site_labels> (WEB-xx)` **nền `#9DA5AD`**, trong đó mỗi flow 1 Section con `Flow <id> — <tên>` chứa danh sách màn (renderer tự tạo theo `site_order` → thứ tự Group). Không gộp 2 site chung 1 section. Màn theo phạm vi **CR-3** (§3) — mặc định **NEW + UPD** + popup / màn lỗi có nội dung nghiệp vụ (`shell: modal`). **Màn UPD = vẽ lại màn AS-IS** (theo ảnh evidence / code baseline) và **tô màu block thay đổi** (`chg`: NEW xanh lá · UPD cam · DEL đỏ gạch) + số `①` khớp bảng ITEMS | Vẽ trước khi đọc Design System; tự chế màu / component; **mockup không có mô tả / không có error scenario**; **chỉ vẽ màn NEW bỏ màn UPD**; vẽ màn UPD thành màn mới không phân biệt phần cũ / phần đổi |

Section CR-3 theo site được phép **đặt ngoài section CR, cạnh Output 1 / Output 2 baseline mới nhất** (user yêu cầu 20/10/2026): chuyển ra page, đặt tên `CR-<id> · CR-3 Screens · <site>` và gắn plugin data `crkit.cr = <tên section CR>` — `99-readback.js` tự gom về để chấm V-CR-FIGMA.

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

<!-- CR-2 · CR-3 · CR-3b — 1 lượt, chủ đề "Figma cho yêu cầu thay đổi" (quy tắc gom câu: preflight-questions.md §0). Chữ hiển thị không mã nội bộ -->
```
1. Có vẽ phần thay đổi lên Figma không?
   [A] Có — cùng file đã vẽ luồng của bản khảo sát (<link>)   [B] Có — file / trang khác (Other: link)   [C] Không vẽ lần này
2. (khi vẽ) Vẽ màn hình đề xuất cho những màn nào?
   [A] Màn mới + màn sửa + thông báo lỗi  (đề xuất)   [B] Chỉ màn mới   [C] Tôi chọn màn (Other: tên màn)   [D] Không vẽ màn đề xuất
3. (chỉ khi cần) Màn 「<tên màn>」 cần 「<tên thành phần, ví dụ hộp chọn ngày>」 nhưng bộ quy chuẩn giao diện của <tên website> chưa có; <website khác> thì có.
   [A] Mượn mẫu của <website khác>, ghi "mượn — chờ designer" trên màn   [B] Bỏ phần đó, ghi câu hỏi cho designer
```
<!-- 1 = CR-2 · 2 = CR-3 (luôn hỏi khi CR-2 = A/B, kể cả 1 màn; [A] = NEW + UPD + popup, format Output 3; [C] → map tên màn → Impact ID) · 3 = CR-3b ([A] "from": "<WEB-yy>" · [B] UI-TOKEN-NEW + CQ) -->
Không hỏi CR-3b → không được dùng component site khác. Câu trả lời ghi vào run-log.

## 4. Đọc Design System TRƯỚC khi vẽ CR-3 (bắt buộc — máy kiểm)

1. Với mỗi site có màn đề xuất, **Read**: `outputs/<baseline>/04_DesignSystem/<WEB-xx>/project/README.md` → `tokens.json` → `components/<Comp>/README.md` của component sẽ dùng → `../STATUS.md` (TBD).
2. Ghi danh sách file đã đọc vào `cr-figma.json → screens.ds_read`. Thiếu README / tokens của site → `render-cr-figma.py` **từ chối sinh JS**, V-CR-FIGMA check 10 FAIL.
3. Mỗi block màn chỉ dùng component có trong DS của site (`BLOCK_COMP` trong script). Component chưa có → khai `"from": "<WEB-yy>"` theo câu CR-3b; không khai → script từ chối.
4. Màu / chữ / bo góc / chiều cao control lấy từ `tokens.json` (renderer đọc thẳng). V-CR-FIGMA đọc ngược mọi màu fill trong màn → **màu ngoài token của site (và site mượn) = FAIL**.
5. Font DS không có trên Figma (VD Hiragino Kaku Gothic Pro) → renderer dùng Noto Sans JP và **ghi rõ trên màn** "font thay thế". Không im lặng đổi.
6. Dữ liệu trên màn: bộ mẫu `DATA-PRIVACY.md` §4 (Nguyễn Văn A / 山田太郎 · `user_a@example.com` · `090-0000-0000` · `SO-0001` · `1,000` · Công ty ABC). Figma là cloud — không dữ liệu thật.
7. **Không có Design System** (mọi baseline không có `04_DesignSystem/` — hệ thống không cung cấp UI / Figma, O4 đã skip) → dùng **Base Design System tạm thời** (`.claude/base-design-system/` trong kit — chuẩn UI Nhật DADS + lớp tên chuẩn công ty):
   ```bash
   BDS=.claude/base-design-system
   for W in <WEB-xx có màn đề xuất>; do mkdir -p $V/04_DesignSystem/$W && cp -R $BDS/project $V/04_DesignSystem/$W/; done
   # mỗi site: $V/04_DesignSystem/$W/STATUS.md = copy $BDS/STATUS.md, sửa dòng đầu "- Trạng thái: TBD — BASE tạm thời (hệ thống không có Design System)"
   ```
   - Đọc `$BDS/README.md` + `prompt_design_system.md` (nguyên tắc) rồi bước 1 với `$V/04_DesignSystem/<WEB-xx>/…`; `ds_read` khai đường dẫn trong `$V`.
   - Chạy renderer / V-CR-FIGMA với **`--ds-baseline $V`**. Ref DS ghi `DS:<WEB-xx>:primary` / `DS-component:<WEB-xx>:TextField` (tên chuẩn — alias DADS).
   - Base không có `SideNav` / `Toast` / `AppShell` / `sidebar-width` → shell `mypage` / `admin` bị từ chối: dùng shell `public` / `auth` / `modal`, hoặc hỏi CR-3b `[B]` (UI-TOKEN-NEW + CQ cho designer).
   - Trên mỗi màn CR-3 ghi rõ (note section): "Dựng từ Base Design System (デジタル庁デザインシステム) — hệ thống chưa có Design System, chờ designer xác nhận". Run-log + Q&A sheet: 1 CQ "dùng design system nào cho màn mới".
   - Không publish base thành artifact của hệ thống; không ghi `APPROVED`.
8. **Sau khi CR-3 clone UI thật của designer** mà V-CR-FIGMA check 10 WARN (màu thật chưa có token): mở **version DS mới** (DELTA O4, copy `04_DesignSystem` bản mới nhất) → tra từng màu dùng ở đâu trên UI thật (node Figma, khối nào) → thêm token **tên theo vai trò** + `usage` ghi node nguồn; màu Figma **mâu thuẫn** với website cho cùng vai trò → **chọn website**, ghi `STATUS.md` § Mâu thuẫn và tô lại mockup bằng màu website (không thêm token). Chạy V-DS, rồi V-CR-FIGMA với `--ds-baseline <version DS mới>` → check 10 PASS. Publish artifact chỉ khi user đồng ý (P7b).

## 5. `cr-figma.json` (agent viết)

```json
{"title": "団体利用登録・団体利用受付機能",
 "flows": [{"lane": "FL-08", "title": "Mua vé & thanh toán → đặt chỗ đoàn", "note": "...",
            "nodes": [{"key": "a", "type": "actor", "badge": "NEW", "ref": "IMP-033", "label": "Người phụ trách đoàn"},
                      {"key": "s", "type": "start", "pos": 1, "badge": "NEW", "ref": "IMP-047", "label": "Mở trang đặt chỗ đoàn"},
                      {"key": "d", "type": "decision", "pos": 2, "badge": "IMPACT", "ref": "SC-067", "label": "Còn chỗ?"},
                      {"key": "e1", "type": "end", "pos": 3, "result": "ok", "badge": "NEW", "ref": "IMP-047", "label": "Đặt chỗ đoàn xong"},
                      {"key": "ng", "type": "ng", "pos": 2, "row": 1, "badge": "IMPACT", "ref": "SC-067", "label": "Hết chỗ → báo lỗi"},
                      {"key": "e2", "type": "end", "pos": 3, "row": 1, "result": "fail", "badge": "IMPACT", "ref": "SC-067", "label": "Chọn ngày khác"}],
            "edges": [["a", "s", ""], ["s", "d", ""], ["d", "e1", "Còn"], ["d", "ng", "Hết", "ng"], ["ng", "e2", "", "ng"]]}],
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
- **Bắt buộc mới:** CR-1 lane: ≥ 1 node `type: "ng"` (nối bằng cạnh kiểu `ng` từ decision) hoặc `no_ng`. CR-2 group: ≥ 1 node `type: "ng" | "popup"` với `display` (`Modal|Popup|Toast|Banner|Full screen|Inline|Tooltip|Empty state`) · `trigger` · `msg` (message thật của hệ thống nếu có ở O1 `Screen Error message`; chưa có → message đề xuất ghi rõ `(đề xuất)`) · `parent` (màn cha) · `next`; node `screen` có `stype` + `desc`.
- `site_order` [WEB-xx…] · `site_labels` {WEB-xx: "Màn hình người dùng"} — tên section theo site (không hardcode trong renderer).
- CR-3 item: **`flow`** (id Group CR-2 / lane FL-xx, bắt buộc; ngoài danh sách → thêm `flow_title`), `stype`, `entry`, `purpose`, `changes` (UPD), `happy` [..], `items` [{`n`,`title`,`desc`,`action`,`chg`}], `errors` [{`trigger`,`display`,`msg`}], `base` (UPD: SC- màn gốc), `cq` (câu hỏi chờ). Block có `n` (số item) và `chg` (NEW/UPD/DEL) — số item trong bảng phải có trên mockup. Popup: `shell: "modal"` (+ `scrim`).
- Màn `To verify` ở baseline (chưa quan sát UI) mà vẫn UPD → dựng AS-IS từ code (nhãn trong page) và ghi `cq` "AS-IS dựng từ code — chờ xác nhận UI".
- Không chữ cũ của trạng thái chưa rõ (`inv_schema.LEGACY_WORD`) trong `title` / note / `flows` / `tech` / `screen_groups` (renderer từ chối) — viết "Cần xác nhận — CQ-xxx" / "chưa quan sát" / "chờ khách hàng xác nhận".
- CR-1 node: `type` = `actor · start · step · decision · ng · end · edge` · `pos` 1…6 (cột trái → phải) · `row` 0 = happy, ≥ 1 = non-happy · `end` có `result: ok|fail` · `ref` là SC- / F- / FL- / IMP- (**không** API- / EXT- / `table:` / `column:` — những thứ đó vào `tech`). Bắt buộc: 1 actor · ≥ 1 start · ≥ 1 end ok ở row 0 · NG nào cũng có cạnh đi tiếp. Vẽ lại CR-1 / CR-2 trên section đã có: `--redraw cr1,cr2` (sinh `00-clear.js` lưu bản cũ ra section LƯU TRỮ, `98-restack.js` xếp lại). `type` (CR-2): `start · screen · decision · system · ng · terminal · edge`.
- Cạnh `[from, to, nhãn, kiểu]` — kiểu `ng` (đỏ), `cross` (xanh lá, khác actor), rỗng (xanh dương). **Mọi node trừ `edge`/`tech` phải có ≥ 1 cạnh.**
- Shell CR-3: `public` (AppHeader + PageHeader giữa) · `mypage` (AppHeader + SideNav マイページ) · `admin` (SideNav admin + PageHeader) · `auth` · `modal` · `mobile` (khung SP; DS chưa có token `viewport-mobile` → khai `viewport_width` + `viewport_note`, không tự đặt). Block: `title · breadcrumb · section · text · field · field2 · select · radio · checkbox · buttons · table · badge · card · steps · modal · search · pagination`.

## 6. Chạy

```bash
S=.claude/skills/system-analyst/scripts; V=outputs/<ver CR>; BL=outputs/<baseline>
# 0. use_figma đọc bbox thấp nhất của page (get_metadata) -> Y = đáy + 400
python3 $S/render-cr-figma.py --cr-json $V/_internal/cr.json --view $V/_internal/cr-figma.json --baseline $BL [--ds-baseline outputs/<ver có 04_DesignSystem mới nhất>] \
    --rates .claude/config/md-unit-rates.json --page-id <page id> --y <Y> --out-dir $V/_internal/figma-js
# 1. use_figma lần lượt: 01-shell-flow.js · 02-screen-flow.js · 03-change-table.js · 04-screens-*.js
#    (mỗi call trả bottom/created; lỗi → section chưa đủ: chỉ xoá section của CHÍNH lần chạy này rồi chạy lại từ 01)
# 2. use_figma 99-readback.js -> lưu kết quả thành $V/_internal/cr-figma-nodes.json
python3 $S/verify-cr-figma.py --nodes $V/_internal/cr-figma-nodes.json --cr-json $V/_internal/cr.json \
    --baseline $BL --view $V/_internal/cr-figma.json --out $V/_internal/gates/v-cr-figma.md
# 3. 1 screenshot cả Section (scale nhỏ) để soát chữ bị cắt / chồng — không thay gate
```
V-CR-FIGMA (**14 check**): 1 tên/badge · 2 node → impact thật · 3 màn / luồng bị chạm đều vẽ · 4 AS-IS chỉ hàng xóm 1 bước / lane FL baseline · 5 Change Table = thống kê khớp cr.json · 6 trùng (WARN) · 7 mũi tên thật · 8 legend + không node thiếu badge · 9 không chồng node cũ · 10 CR-3 bám DS · **11 CR-1 mỗi lane có NON-HAPPY · 12 CR-2 mỗi group có màn / popup lỗi, Screen Index có Loại + TỔNG, ⑦ đủ · 13 CR-3 mỗi màn có mô tả + ITEMS + ERROR SCENARIOS, màn UPD tô màu phần đổi, đủ màn NEW + UPD · 14 mỗi site 1 section (CR-2 · CR-3); CR-2 và CR-3 = site → flow / use case → Section con → màn; CR-3 nền #9DA5AD**. `FAIL = 0` mới được báo xong. Sau gate: `get_screenshot` ≥ 3 màn CR-3 (1 NEW · 1 UPD · 1 popup) — che panel phải, nhìn mockup có hiểu màn gì không (Rule S5 Output 3).
