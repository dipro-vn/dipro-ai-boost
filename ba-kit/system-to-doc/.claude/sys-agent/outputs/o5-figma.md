# O5 — Figma flow dự án (Output 1 Flow tổng quan + Output 2 Screen flow)

> **Yêu cầu:** dùng toàn bộ input + output đã sinh ở trên · hỏi user link Figma · vẽ **figma_output1** và **figma_output2** từ hệ thống có sẵn, **cách vẽ y hệt kit `requirement-to-flow`**.
>
> Chạy **cuối Luồng 1** (sau O1–O4), chỉ khi P8 có link. Thành phẩm: node trên Figma + `05_Figma/figma-links.md`.

---

## 1. Quy tắc vẽ = copy nguyên từ requirement-to-flow

| Đọc | Nội dung |
|---|---|
| `.claude/skills/ba-figma-output/SKILL.md` §0–§5, §7–§11 | Màu, typography, helper function, layout Output 1 + Output 2, chia call, recheck |
| `.claude/sys-agent/figma/shared-rules.md` | **Gate ảnh mẫu** (mở `skills/ba-figma-output/examples/final_output_<N>.png` + tả lại bố cục bằng lời TRƯỚC mọi `use_figma`), quy tắc URL, Strict Mode |
| `.claude/sys-agent/figma/output-1-flow.md` | Output 1: Flow Candidate Matrix, Merge Log, Phần A/B/C |
| `.claude/sys-agent/figma/output-2-screen-flow.md` | Output 2: Group, Combined Detail, bảng ④⑤⑥⑦, Error strip ⑧ |
| `.claude/sys-agent/figma/granularity-principles.md` | Gộp/tách flow, GATE FR COVERAGE |
| `.claude/sys-agent/figma/recheck.md` | Recheck bằng script: Tiêu chí 6 · 7 (bbox overlap) · 8 (coverage) · 9 (trong biên frame) |
| `.claude/sys-agent/figma/code-patterns.md` | Snippet `use_figma` |
| Skill `figma:figma-use` | BẮT BUỘC load trước mọi `use_figma` |

Đường dẫn `.claude/ba-agent/<file>` nhắc trong các file copy → đọc `.claude/sys-agent/figma/<file>`.

---

## 2. Bảng thay thế — kit kia đọc SPEC.md, kit này đọc inventory

| Kit forward cần | Kit này dùng | Ghi chú |
|---|---|---|
| FR Register / `FR No.` | `01_Function` / **`F-xxx`** | Tag Sitemap `#F-012`. GATE FR COVERAGE: `set(F-id) − set(F-id đã gắn tag) = ∅` |
| `ACTOR_LIST` (Câu 0.10) | Giá trị `01_Function.Primary Actor` + role ở `10_Site.Roles Observed` | Không cần hỏi lại |
| Tech stack (Câu 0.8) → Technology Table | `11_Repo.Stack` + `recon/code/*/stack.json` + `09_Integration` | Đều là **FACT từ code** — không cần nhãn `[PROPOSAL]` |
| `FLOW_GRANULARITY` (Câu 0.9) | Mặc định **Standard** | Test E ngưỡng 8–10 flow |
| `## Screens` (Screen Code, loại hiển thị) | `02_Screen`: **`SC-xxx`** + `Screen Name` + `Type` (List/Detail/Form/Modal/Error) + `Site` | Nhiều website → mỗi site 1 nhóm, ghi `WEB-xx` trên nhãn group |
| `## Screen Details` — error display `E-xxx` | Message Code trong O1 (`Screen Error message` / `Common mesage`) + bảng ERROR SCENARIOS | Bảng ⑦ = 100% message code của O1. O1 chưa xong → làm O1 trước |
| `## Non-Happy Case` | ERROR SCENARIOS của O1 | |
| Source Register `FACT` / `INFERENCE` / `UNKNOWN` | `Status`: `Confirmed` = FACT · `To verify` / `Inferred` = INFERENCE · `UNKNOWN` = UNKNOWN | Chỉ `Confirmed` được vẽ inline (NG); còn lại → **Edge / Exceptional panel**. Trên Figma **không in chữ `UNKNOWN`** — viết "chưa quan sát" / "chưa xác định" / "màn chưa có tiêu đề" |
| Màn chuyển tiếp (arrow) | `02_Screen.Entry From` + `→ SC-xxx` trong cột P/Q của O1 + link trong `pages.json` | Arrow không có bằng chứng → nét đứt + ghi `Inferred` |
| `## BA Deliverables` (ghi ngược node URL) | `05_Figma/figma-links.md` | |
| Technology Stack (Phần B) | `07_API` (group/handler) + `09_Integration` | Lane use case **không** ghi API / bảng / thư viện (feedback 20/10/2026); việc tự động ghi bằng lời trong lane (`⏱ Tự động: …`) |

**Không áp dụng ở kit này** (bỏ qua khi file copy nhắc tới):

| Nhắc trong file copy | Ở kit này |
|---|---|
| Output 3 (HiFi screens), Output 4 (HTML prototype), Output 5 (Basic Design) | **Luồng 1: không vẽ** (O1 xlsx là Basic Design). **Luồng 2: có** — CR-3 *màn đề xuất* cho màn NEW / UPD, bắt buộc đọc Design System baseline trước + hỏi CR-3 / CR-3b (`figma/cr-view.md`) |
| Bước 5.4 Output OQ (`open-questions.md`, `open_questions.xlsx`) | Câu hỏi treo nằm ở `06_OpenQuestions` → Phụ lục A của O6. Không vẽ OQ view |
| Câu preflight 0.x của BA | Đã có P0–P11 của kit này |
| Gate B1/B2 chọn vẽ 1 hay nhiều flow | Vẫn áp dụng khi N flow > 10 — hỏi user bằng `AskUserQuestion` |

---

## 3. Quy trình

| # | Bước | Điều kiện chuyển tiếp |
|---|---|---|
| 1 | Có `figma_output_url` (P8). Link page cụ thể, file `/design/` | Không có → O5 = ⬜, `build-version-index --skip "O5=<lý do>"` |
| 2 | Load skill `figma:figma-use` + `ba-figma-output`; **mở ảnh mẫu** `examples/final_output_1.png`, `final_output_2.png`, tả lại bố cục | Đã tả bằng lời |
| 3 | Output 1: lập Flow Candidate Matrix từ `01_Function` → Merge Log → mỗi flow giữ lại = **1 use case** (actor · bắt đầu · đường đi · ✓ kết thúc · non-happy → ✗ kết thúc) → in `SITEMAP COVERAGE … THIẾU: []` | THIẾU ≠ [] → không vẽ |
| 4 | Vẽ Output 1 → recheck Tiêu chí 9 → 7 → 8 (script) | overlap = 0 |
| 5 | **Gate A** (`AskUserQuestion`): Output 1 đúng chưa, vẽ tiếp Output 2? | User đồng ý |
| 6 | Output 2: **mỗi site 1 Section riêng** (không gộp site người dùng + admin chung 1 section), trong section **site → use case (Section con `FL-xx · <tên>`, cùng tên lane Output 1) → màn**; bảng ④ Screen Index = mọi `SC-` trong scope; ⑦ = mọi message code O1 | Đếm: `số node màn = số SC trong scope` |
| 7 | Vẽ Output 2 → recheck 9 → 7 → 6 + quét chữ `UNKNOWN` trên cả 2 frame | overlap = 0, không node rỗng, `UNKNOWN` = 0 |
| 8 | Ghi `05_Figma/figma-links.md` | Link node từng frame |

`figma-links.md`:
```markdown
# Figma — ver<N>
File: <figma_output_url>
| Output | Frame | Node URL | Số node màn / flow | Recheck |
|---|---|---|---|---|
| Output 1 — Flow tổng quan | <tên frame> | https://www.figma.com/design/<KEY>/<NAME>?node-id=<a-b> | N flow · F-coverage n/N | overlap 0 · THIẾU [] |
| Output 2 — Screen flow | ... | ... | m màn · k message | overlap 0 |
```

---

## 4. Bảo mật

- ⚠️ **Figma là cloud bên ngoài.** Chỉ vẽ: tên màn, ID, nhãn chức năng, message lỗi (văn bản hệ thống). **Không** vẽ dữ liệu người dùng, không upload screenshot có dữ liệu thật.
- Hook H06 chặn PII trong mọi call `mcp__*figma*`. Bị chặn → thay dữ liệu mẫu rồi vẽ lại, không lách.
- Luồng 2 (CR) **không bao giờ** sửa frame này — vẽ section CR mới **theo đúng khung Output 1 / Output 2 ở file này** (`flow-2-change-request.md` §5 · `figma/cr-view.md`).

## Quy định bố cục section theo site (20/10/2026)

Áp cho **Output 2 (Screen flow)** ở Luồng 1 và **CR-2 / CR-3** ở Luồng 2 (`figma/cr-view.md`):

| Quy định | Chi tiết |
|---|---|
| > 1 site → tách section | Mỗi site (VD `WEB-02` người dùng · `WEB-01` admin) 1 Section riêng; **không gộp chung** |
| Thứ bậc trong section | **site → flow / use case → section → danh sách màn** (Output 2 / CR-2: mỗi Group = 1 use case, nằm trong Section con riêng; CR-3: mỗi flow 1 Section con `Flow <id> — <tên>`) |
| Nền section màn đề xuất (Output 3 / CR-3) | Fill **`#9DA5AD`** (mockup trắng nổi trên nền xám) |
| Máy kiểm | Luồng 2: V-CR-FIGMA check 14. Luồng 1: recheck theo checklist này trước Gate B |

## Output 1 dạng use case + Sitemap rút gọn (20/10/2026)

Feedback khách: Output 1 kiểu cột ACTOR → TRIGGER → FUNCTION → TECHNOLOGY → OUTCOME khó đọc. Kit này đổi (chi tiết `figma/output-1-flow.md` mục ⚠ đầu file):

| Phần | Vẽ gì |
|---|---|
| A | 1 lane = 1 use case: Actor → đường đi happy → ✓ kết thúc; hàng dưới non-happy → ✗ kết thúc. Không technology / function / mã trong lane |
| B | Bảng Technology Stack giữ nguyên |
| C | Sitemap Site → Actor / vai trò → Nhóm chức năng → Màn (tên dễ hiểu, không hành động, không endpoint; mã SC chỉ ở tên layer để kiểm phủ) |

Output 2: site → use case → section (`figma/output-2-screen-flow.md` mục ⚠). Luồng 2: CR-1 / CR-2 cùng quy tắc (`figma/cr-view.md`, `render-cr-figma.py`, V-CR-FIGMA check 11 · 14).
