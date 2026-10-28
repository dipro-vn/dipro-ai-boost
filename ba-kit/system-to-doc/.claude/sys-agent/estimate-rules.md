# 見積書 Luồng 2 — quy tắc phân rã chức năng (`estimate.json`)

> Lý do có file này: Estimation sinh 1 dòng / impact bị CEO đánh giá **không dùng được** (review `docs/review/2026-10-19_estimation-AI-vs-FINAL.md`, L1–L10). 見積書 gửi KH viết theo **chức năng**, giống bản FINAL CR-001.
> Script: `estimate_core.py` · `build-estimate.py` · `verify-estimate.py` (V-EST) · `selftest-estimate.py`. Bảng công số: `.claude/config/function-rates.json`. Template: `templates/template_mitsumori.xlsx` (bóc bằng `extract-mitsumori-template.py`).

## 1. Hai lớp, một nguồn

| | File | Đọc bởi | Từ |
|---|---|---|---|
| Phân tích ảnh hưởng | `CR-<id>_Impact.xlsx` (7 sheet; sheet Estimation = bản **vi nội bộ** của 見積書, thêm cột Impact + căn cứ) | Dipro (PM, dev) | `cr.json` + `estimate.json` |
| **Báo giá** | `CR-<id>_見積書.xlsx` (詳細見積書 + 前提条件・留意事項, **tiếng Nhật thuần**) | KH | `estimate.json` |

`cr.json` = đối tượng kỹ thuật (API, cột DB, màn, rule). `estimate.json` = chức năng KH đọc được. Mỗi dòng estimate giữ `impacts: [IMP-…]` để truy ngược — gate E8 bắt impact NEW / UPD (trừ Mockup) chưa thuộc dòng nào.

## 2. Phân rã

| Quy tắc | Đúng | Sai |
|---|---|---|
| Section theo **site / người dùng**: `user` ユーザー予約サイト · `sa` 運営管理サイト · `admin` 施設管理サイト · `common` 全システム (DB, hồi quy) | Màn dùng chung nhiều role → 1 dòng ở `sa`, đổi nhãn section qua `meta.section_labels` | Section theo mục yêu cầu `CR-001.x` |
| 1 dòng = **màn × thao tác** (一覧 / 詳細 / 登録・編集 / 公開停止 / CSV / mail) | 「商品一覧 › 公開区分の表示」 | 「API-107 · API danh sách vé」 |
| Cùng thao tác ở 2 site khác màn = 2 dòng | SA 予約変更 + ADMIN 予約変更 | Gộp 1 dòng "API-111;API-013" |
| Mỗi mẫu mail = 1 dòng `MAIL-TEMPLATE` | | |
| **Phương án thay thế = dòng riêng** + `pattern` + `◯`, khai `combos` để in bảng tổng theo tổ hợp | ①-A ◯ / ①-B ◉ · trang mới / bản đơn giản | Cờ option + câu hỏi CQ |
| Mockup **không** thành dòng 実装 (đã ở cột UI/UX); IMPACT → 1 dòng `REGRESSION` / nhóm, `req: false` | | Dòng "UI-NEW × 6" ở cột 実装 |
| Chức năng có sẵn chỉ xác nhận → `EXISTING-CONFIRM` (実装 0, 要件 / テスト / 管理 cố định 0.5) | | Bỏ qua → KH không thấy đã xét |
| Câu hỏi chưa rõ → `confirm` ({ja, vi}) — in thành 【見積もり前提・確認事項】 trong 改修内容; câu trả lời giả định = đề xuất của Dipro | | "Chờ CQ-005" |

## 3. Công số

- AI chỉ **chọn `code` + `qty`**; 実装 = `function-rates[code].md × qty` do script tính. Cần lệch → `impl_override` + `override_note` (V-EST WARN E6).
- Hệ số công đoạn đọc từ `_meta` của template (FINAL: 要件 ×0.2 · UI ×0.3 màn mới lớn `ui: L` / ×0.2 `M` / `-` không UI · テスト ×0.5 · 管理 ×0.2 · 人月 = 人日 / 20). `req: false` cho DB / hồi quy.
- `function-rates.json` hiệu chỉnh từ dòng `from` của FINAL CR-001; `selftest-estimate.py --golden <FINAL>` kiểm mọi dòng `from` nằm trong `range`. Status `DRAFT` → V-EST WARN; PM / Tech Lead duyệt (`APPROVED`) trước khi gửi KH.
- `Step 1` = cơ bản, `Step 2` = mở rộng / làm sau; `◉` bắt buộc, `◯` tuỳ chọn. Tổng Step 1 / Step 2 / 全ての機能 / 人月 là công thức **phủ đủ dải dòng** (E3 — FINAL CR-001 từng sai `SUM(J19:J106)`).

## 3b. Văn phong — bắt buộc đọc `sys-agent/writing-style.md` trước khi viết

Mọi chữ khách đọc (cột 改修内容, tiền đề, câu hỏi) viết theo **10 quy tắc** ở `writing-style.md`: theo điều người dùng thấy, có nhãn 【想定する対応内容】 / 【提案する対応方法】 / 【見積もり前提・確認事項】 + gạch đầu dòng, câu đầy đủ, tên màn / nút đúng như màn hình, không mã nội bộ, không viết tắt nội bộ, bản Việt dịch đầy đủ.
Câu hỏi gửi khách khai trong `estimate.json → questions` (chỉ câu **nghiệp vụ**; giao diện nhỏ / kỹ thuật / môi trường để ở sheet Q&A nội bộ của Impact). Điều đã có chức năng sẵn để xử lý (VD dừng bán bằng lịch bán có sẵn) → **ghi thành tiền đề, không hỏi**.

## 4. Bản KH (ja) — cấm

Chữ tiếng Việt · mã nội bộ `IMP- / API- / CQ- / SC- / EXT- / FL- / DS-` · `column: / table:` · "TBD" · ghi chú nội bộ (đơn giá nội bộ, man-month nội bộ, xung đột To verify). Gate E4 chặn. Sheet 前提条件・留意事項 đủ 4 khối (E7): 前提条件 · 既存システムへの影響 · クライアント側で事前に決定・準備が必要な事項 · 想定されるリスク — lấy từ `cr.json` (not_cr, recommendation, risk, questions).

## 5. Lệnh

```bash
S=.claude/skills/system-analyst/scripts; V=outputs/<ver>
python3 $S/build-estimate.py --estimate $V/_internal/estimate.json --cr-json $V/_internal/cr.json --out $V/CR-<id>_見積書.xlsx
python3 $S/verify-estimate.py $V/CR-<id>_見積書.xlsx --estimate $V/_internal/estimate.json --cr-json $V/_internal/cr.json --out $V/_internal/gates/v-est.md
python3 $S/build-cr-impact.py --cr-json $V/_internal/cr.json --rates .claude/config/md-unit-rates.json --out $V/CR-<id>_Impact.xlsx --estimate $V/_internal/estimate.json
python3 $S/verify-cr-impact.py $V/CR-<id>_Impact.xlsx --cr-json … --baseline … --estimate $V/_internal/estimate.json
python3 $S/verify-estimate.py "<見積書 bất kỳ>.xlsx" --scan-only      # kiểm dải công thức tổng của 1 báo giá có sẵn
```

Mẫu công ty đổi layout → bóc lại: `extract-mitsumori-template.py --src "<見積書 mới>.xlsx" --out templates/template_mitsumori.xlsx` (dò cột theo header, không cố định vị trí).
