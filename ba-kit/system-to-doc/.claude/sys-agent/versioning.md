# Versioning — khảo sát lần đầu luôn là ver1

> Kit chạy nhiều lần trên cùng hệ thống: lần đầu dựng baseline (Luồng 1), sau đó mỗi CR (Luồng 2). Folder version là **thứ duy nhất** lần chạy sau đọc lại — agent không nhớ gì giữa các session.
>
> **Quy tắc (R5 · D3 · D4):** chưa có CR → mọi lần `/analyze-system` (chạy lại, thêm nguồn, thêm output, sửa theo góp ý) **ghi vào ver1**, cất bản cũ vào `_internal/history/<YYYYMMDD-HHMM>/` trước khi ghi đè. Có folder CR trỏ tới baseline → baseline đó **khoá**. Baseline mới `ver<N+1>` = baseline `ver<N>` + CR **đã duyệt và đã code xong**, chỉ tạo bằng lệnh `promote`.

---

## 1. Cấu trúc dự án

```
my-project/
├── CLAUDE.md · POLICIES.md · AGENTS.md · templates/ · .claude/     ← kit
├── inputs/            kit có sẵn các folder con — user chỉ việc bỏ file vào
│   ├── repo/          source code (mỗi repo 1 folder con)
│   ├── db/            schema-only dump (.sql)
│   └── cr/            yêu cầu thay đổi (Luồng 2)
├── .auth/             credentials.local.env (tài khoản TEST) + phiên Playwright — KHÔNG commit, KHÔNG copy vào outputs
└── outputs/
    ├── _project/preflight-memory.json   câu trả lời preflight + quyết định lớn + phân loại S1 (dùng chung mọi version, gitignore)
    ├── ver1_011026_baseline/            baseline đầu — chạy lại ghi vào đây (khoá khi có CR-001)
    │   └── _internal/history/20261005-1030/   bản cũ của file bị ghi đè
    ├── CR-001_151026_them-coupon/       CR — version-meta.json: baseline = ver1_011026_baseline
    ├── CR-002_201026_doi-mau-nut/       CR — cũng trỏ ver1
    └── ver2_251026_baseline/            = ver1 + CR-001 (đã duyệt + code xong) — chạy lại ghi vào đây tới khi có CR trỏ ver2
```

Tên folder: baseline `ver<N>_<DDMMYY>_<slug>` · CR `CR-<id>_<DDMMYY>_<slug>` (CR không chiếm số version). **Đọc được layout cũ** `ver<N>_<DDMMYY>_CR-<id>-<slug>` (CR cũ, `N` chung dãy với baseline) — không đổi tên folder cũ. Sinh tên bằng script, không tự đặt tay:

```bash
S=.claude/skills/system-analyst/scripts
python3 $S/version-tool.py next --outputs outputs --slug baseline --create          # Luồng 1
python3 $S/version-tool.py snapshot --ver outputs/ver1_011026_baseline [--files 02_API/API_Doc_X_ver1.xlsx …]
python3 $S/version-tool.py next --outputs outputs --cr-id CR-001 --slug them-coupon --create   # Luồng 2
python3 $S/version-tool.py promote --outputs outputs --cr CR-001 --approved --coded --create   # baseline mới
```

| Lệnh | Kết quả |
|---|---|
| `next` (Luồng 1), chưa có baseline | tạo `ver1_<DDMMYY>_<slug>` (`reuse:false`) |
| `next` (Luồng 1), baseline chưa khoá | trả về **chính baseline đó** (`reuse:true`, kèm lệnh `snapshot`) — `--create` chỉ bổ sung thư mục con còn thiếu |
| `next` (Luồng 1), baseline đã khoá | **exit 3** `locked:true` + `locked_by` — không tạo folder. Báo user "ver<N> đã khoá vì đã có CR …"; CR nào đã duyệt + code xong → `promote`, chưa có → chỉ đọc lại |
| `next --cr-id` | tạo `CR-<id>_<DDMMYY>_<slug>` + `_internal/version-meta.json` (`baseline`); CR đó đã có folder → trả về folder đó (`reuse:true`, snapshot trước khi ghi đè) |
| `snapshot --ver <v>` | copy file sắp bị ghi đè (mặc định: mọi file trừ `_internal/history/`) vào `<v>/_internal/history/<YYYYMMDD-HHMM>/` + `SNAPSHOT.md` |
| `promote --cr … --approved --coded` | tạo `ver<N+1>_<DDMMYY>_<slug>` (`previous_version`, `promoted_crs`). Thiếu `--approved`/`--coded` hoặc CR không trỏ baseline hiện hành → từ chối. Chỉ thêm 2 cờ sau khi **user xác nhận** qua `AskUserQuestion` |

---

## 2. Folder BASELINE (Luồng 1)

```
ver1_011026_baseline/
├── README.md                         ← index: output nào, ở đâu, bao nhiêu, gate ra sao
├── run-log.md
├── 01_Screens/BasicDesign_WEB-01_ver1.xlsx       O1 (1 file / website)
├── 02_API/API_Doc_<sys>_ver1.xlsx                O2
├── 03_DB/DB_Doc_<sys>_ver1.xlsx · ERD_<sys>_ver1.png   O3
├── 04_DesignSystem/STATUS.md · project/           O4 tuỳ chọn (chuẩn chung với designer-kit; per-site: WEB-xx/STATUS.md · project/)
├── 05_Figma/figma-links.md                       O5 (+ link ERD cho O6)
├── 06_Overview/Overview_<sys>_ver1.docx          O6 (nghiệp vụ chính + bảng tổng)
├── 07_BugList/BugList_<sys>_ver1.xlsx            O7 (tuỳ chọn, 1 sheet)
├── 09_DevSetup/DevSetup_<sys>_ver1.md            O9 hướng dẫn chạy local (dev, khi có source)
└── _internal/                                    ← của agent, không phải deliverable
    ├── inventory.xlsx        bộ nhớ máy đọc — Luồng 2 đọc file này
    ├── evidence/  recon/  gates/  narrative.json  business.json  index.json
```

## 3. Folder CR (Luồng 2)

```
CR-001_151026_them-coupon/
├── README.md
├── run-log.md                     baseline: ver1_011026_baseline
├── input/                         CR nguyên văn (file copy / cr-request.md khi dán chat / link.md)
├── CR-001_Impact.xlsx             7 sheet: Summary (công số + số đối tượng) · Estimation (template 見積書) · Screen · API · Database · Figma · Q&A
├── 05_Figma/figma-links.md        link view CR mới
└── _internal/  cr.json · cr-figma.json · figma-js/ · cr-figma-nodes.json · gates/
```

Folder CR **không** copy lại baseline — nó trỏ tới baseline bằng `baseline_version` (`cr.json`) / `baseline` (`_internal/version-meta.json`). Từ lúc có folder CR, baseline đó **khoá**. CR được duyệt **và đã code xong** → `promote` tạo `ver<N+1>` → chạy Luồng 1 mode `DELTA` ghi vào `ver<N+1>` (carry từ `ver<N>` + quét lại phần CR chạm). CR chưa code xong thì baseline vẫn là bản cũ (AS-IS chưa đổi).

---

## 4. Quy tắc

1. **Trước khi chạy — agent tự làm, không hỏi user:** `version-tool.py context --outputs outputs --flow <1|2> [--cr-id]` → Read mọi file trong `read`. Luôn lấy **version mới nhất** (§6).
2. **Tạo / mở folder** (`next --create`) chỉ sau khi user confirm Discovery Brief (Luồng 1) / CR-0 (Luồng 2).
3. **Ghi đè baseline chưa khoá** (chạy lại ver1): trước mỗi lần ghi đè file đã có → `snapshot` (chỉ file sẽ bị thay, hoặc cả folder). Ghi `run-log.md`: lần chạy thứ mấy, nguồn mới là gì, thư mục history vừa tạo. **Không xoá** `_internal/history/`.
3b. **Không bao giờ** sửa baseline đã khoá, folder CR của CR khác, hay folder CR / version layout cũ — kể cả "sửa lỗi chính tả".
4. **Đóng version:** chạy `build-version-index.py <ver>` → `README.md` + `_internal/index.json`; ghi `run-log.md`.
5. Trước khi đóng: `node .claude/hooks/detect-pii.js --scan <ver>` — snapshot chứa PII là đóng băng vĩnh viễn.
6. `.auth/` và mật khẩu **không bao giờ** nằm trong `outputs/`.

---

## 5. `run-log.md`

```markdown
# Run log — ver<N>_<DDMMYY>_<slug>

version_type: BASELINE | CR
baseline: — | ver<K>_<...>
run_mode: FULL | DELTA

## Điều kiện chạy
| Hạng mục | Giá trị |
|---|---|
| Website | WEB-01 https://... (READ_ONLY, role admin/user) |
| Source | REPO-01 ... · REPO-02 ... |
| Database | DUMP inputs/db/schema.sql |
| Figma | input: — · output: <link> |
| Budget crawl | 137/200 URL · 22 phút |

## Discovery Brief
(copy nguyên văn bảng user đã confirm)

## Kết quả gate
| Gate | Kết quả |
|---|---|
| S1 Sensitive | clean |
| V1 Evidence | 9 checks · 9 PASS · 0 FAIL |
| ... | ... |

## Diff so với ver<N-1>   (DELTA)
| Thay đổi | Chi tiết |
|---|---|
| Màn mới | SC-031 |
| API mới | API-045 |
| Open Question đã đóng | Q-003 |

## Không chạy / bị chặn
| Output | Lý do |
|---|---|

## Feedback đã xử lý
| Từ | Nội dung | Đã làm |
|---|---|---|
| ver<K>_<...> / chat | <tóm tắt> | <sửa gì ở version này> |

## Feedback của user
(để trống — agent tự ghi khi user góp ý trong chat; user cũng có thể ghi tay)
```

---

## 6. Resume — agent tự lấy version mới nhất

Đầu **mọi** lần chạy (Luồng 1 và 2), trước câu hỏi đầu tiên:

```bash
python3 .claude/skills/system-analyst/scripts/version-tool.py context --outputs outputs --flow 1            # Luồng 1
python3 .claude/skills/system-analyst/scripts/version-tool.py context --outputs outputs --flow 2 --cr-id CR-001   # Luồng 2 (--cr-id khi CR đã có)
```

| Trường | Agent dùng để |
|---|---|
| `latest` · `latest_type` | Version mới nhất bất kỳ loại — in 1 dòng tình hình cho user |
| `latest_baseline` | Baseline **mới nhất** (+ `locked` · `locked_by` · `promoted_crs` · `history`) — Luồng 1 ghi vào đây khi chưa khoá · Luồng 2 đối chiếu với đây. Không bao giờ dùng baseline cũ hơn trừ khi user chỉ định ở CR-0 [C] |
| `open_crs` | CR trỏ tới baseline mới nhất, chưa `promote` (mỗi CR 1 bản mới nhất). G-R hỏi CR nào đã duyệt + code xong → `promote` → Delta; Luồng 2 kiểm xung đột CR-vs-CR |
| `suggest.flow1_action` | `create_v1` (chưa có gì) · `rerun_in_place` (+ `flow1_target`: ghi vào baseline đó, snapshot trước) · `locked` (+ `locked_hint`: không ghi; promote hoặc chỉ đọc) |
| `latest_by_cr` · `suggest.flow2_rerun_of` | CR đã có → chạy lại từ `cr.json` bản mới nhất của CR đó, không làm lại từ đầu |
| `pending_feedback` | Feedback trong run-log chưa version nào xử lý → áp dụng ở lần này, ghi vào **Feedback đã xử lý** |
| `suggest.flow1_mode` | Mode đề xuất mặc định cho G-R (`FULL` khi chưa có baseline, còn lại `DELTA`) |
| `read` | Danh sách file phải Read trước khi hỏi / phân tích |

Rồi đọc trong version mới nhất:

| Đọc | Để biết |
|---|---|
| `outputs/_project/preflight-memory.json` + `00_Meta` (`preflight-memory.py missing` gộp sẵn) | Câu trả lời preflight cũ → không hỏi lại, chỉ xác nhận 1 bảng (`preflight-questions.md` §0) |
| `01_Function` · `02_Screen` · `07_API` · `10_Site` · `11_Repo` | Đã phủ tới đâu → DELTA chỉ quét phần thiếu |
| `05_Evidence` | Evidence ≤ 30 ngày còn dùng được; quá hạn → chụp lại nếu dòng `Confirmed` |
| `06_OpenQuestions` | Câu còn `Open` → hỏi lại user đã có câu trả lời chưa |
| `run-log.md` mục Feedback | User đã yêu cầu sửa gì |

❌ Bỏ qua version cũ rồi quét lại từ đầu = mất câu trả lời user đã cho, tốn budget.
❌ Copy dòng cũ sang mà không đánh `Carried from ver<K>` = che giấu việc chưa kiểm lại.
❌ Bắt user tự chỉ version, tự mở `run-log.md` để ghi góp ý, tự nhớ chọn Delta — đều là việc của agent.

---

## 7. Feedback & chạy lại — user chỉ cần nói trong chat

| User | Agent tự làm |
|---|---|
| Góp ý trong chat (VD "MD màn coupon cao quá", "thiếu màn đổi mật khẩu") | Xác định version bị góp ý (mặc định = version **mới nhất** cùng loại) → `next` (baseline chưa khoá / CR đó → trả về chính folder đó) → `snapshot` → sửa → ghi góp ý vào **Feedback đã xử lý** của run-log folder đó. Baseline đã khoá → báo user, không sửa |
| Ghi tay vào mục *Feedback của user* trong `run-log.md` (vẫn được) | `context` báo trong `pending_feedback` → lần chạy sau tự áp dụng |
| Báo "CR-001 đã duyệt, đã code xong" — hoặc chạy `/analyze-system` khi baseline đã khoá | G-R hỏi CR nào **đã duyệt và đã lên hệ thống** → `promote --cr … --approved --coded --create` → Delta ghi vào `ver<N+1>` (quét lại phần CR chạm) → baseline mới cho các CR sau. Chưa CR nào xong → báo "ver<N> đã khoá", chỉ đọc lại |

