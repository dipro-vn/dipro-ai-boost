# Versioning — mỗi lần chạy là 1 folder mới

> Kit chạy nhiều lần trên cùng hệ thống: lần đầu dựng baseline (Luồng 1), sau đó mỗi CR (Luồng 2) và mỗi lần hệ thống đổi. Folder version là **thứ duy nhất** lần chạy sau đọc lại — agent không nhớ gì giữa các session.

---

## 1. Cấu trúc dự án

```
my-project/
├── CLAUDE.md · POLICIES.md · AGENTS.md · templates/ · .claude/     ← kit
├── inputs/
│   ├── db/            schema-only dump (.sql)
│   ├── docs/          tài liệu KH (nếu có)
│   └── cr/            yêu cầu thay đổi (Luồng 2)
├── .auth/             phiên đăng nhập Playwright — KHÔNG commit, KHÔNG copy vào outputs
└── outputs/
    ├── ver1_011026_baseline/
    ├── ver2_151026_CR-001-them-coupon/
    └── ver3_201026_CR-002-doi-mau-nut/
```

Tên folder: `ver<N>_<DDMMYY>_<slug>` (CR: `ver<N>_<DDMMYY>_CR-<id>-<slug>`). `N` tăng dần trên **mọi** version (baseline và CR chung một dãy số). Sinh tên bằng script, không tự đặt tay:

```bash
python3 .claude/skills/system-analyst/scripts/version-tool.py next --outputs outputs --slug baseline --create
python3 .claude/skills/system-analyst/scripts/version-tool.py next --outputs outputs --cr-id CR-001 --slug them-coupon --create
```

---

## 2. Folder BASELINE (Luồng 1)

```
ver1_011026_baseline/
├── README.md                         ← index: output nào, ở đâu, bao nhiêu, gate ra sao
├── run-log.md
├── 01_Screens/BasicDesign_WEB-01_ver1.xlsx       O1 (1 file / website)
├── 02_API/API_Doc_<sys>_ver1.xlsx                O2
├── 02_API/CodeMap_<sys>_ver1.png · .md
├── 03_DB/DB_Doc_<sys>_ver1.xlsx · ERD_<sys>_ver1.png   O3
├── 04_DesignSystem/STATUS.md · project/           O4 (chuẩn chung với designer-kit; per-site: WEB-xx/STATUS.md · project/)
├── 05_Figma/figma-links.md                       O5
├── 06_Overview/Overview_<sys>_ver1.docx          O6
├── 07_BugList/BugList_<sys>_ver1.xlsx            O7 (tuỳ chọn)
└── _internal/                                    ← của agent, không phải deliverable
    ├── inventory.xlsx        bộ nhớ máy đọc — Luồng 2 đọc file này
    ├── evidence/  recon/  gates/  flow/  narrative.json  index.json
```

## 3. Folder CR (Luồng 2)

```
ver2_151026_CR-001-them-coupon/
├── README.md
├── run-log.md                     baseline: ver1_011026_baseline
├── input/                         CR nguyên văn (file copy / cr-request.md khi dán chat / link.md)
├── CR-001_Impact.xlsx             2 sheet: Summary (vì sao là CR + tổng MD) · Impact (từng hạng mục)
├── 05_Figma/figma-links.md        link view CR mới
└── _internal/  cr.json · cr-figma-nodes.json · gates/
```

Folder CR **không** copy lại baseline — nó trỏ tới baseline bằng `baseline_version`. CR được duyệt **và đã code xong** → chạy Luồng 1 mode `DELTA` để có baseline mới. CR chưa code xong thì baseline vẫn là bản cũ (AS-IS chưa đổi).

---

## 4. Quy tắc

1. **Trước khi chạy:** `version-tool.py latest-baseline --outputs outputs` (Luồng 1: G-R · Luồng 2: baseline để đối chiếu) và `version-tool.py list --outputs outputs` (CR nào đang mở sau baseline).
2. **Tạo folder mới** chỉ sau khi user confirm Discovery Brief (Luồng 1) / CR-0 (Luồng 2).
3. **Không bao giờ** sửa, ghi đè, xoá nội dung version cũ — kể cả "sửa lỗi chính tả". Sai → tạo version mới.
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

## Feedback của user
(để trống — user ghi vào đây; lần chạy sau agent đọc)
```

---

## 6. Resume — lần chạy sau đọc gì

| Đọc | Để biết |
|---|---|
| `_internal/inventory.xlsx` `00_Meta` | Câu trả lời preflight cũ → làm mặc định đề xuất |
| `01_Function` · `02_Screen` · `07_API` · `10_Site` · `11_Repo` | Đã phủ tới đâu → DELTA chỉ quét phần thiếu |
| `05_Evidence` | Evidence ≤ 30 ngày còn dùng được; quá hạn → chụp lại nếu dòng `Confirmed` |
| `06_OpenQuestions` | Câu còn `Open` → hỏi lại user đã có câu trả lời chưa |
| `run-log.md` mục Feedback | User đã yêu cầu sửa gì |

❌ Bỏ qua version cũ rồi quét lại từ đầu = mất câu trả lời user đã cho, tốn budget.
❌ Copy dòng cũ sang mà không đánh `Carried from ver<K>` = che giấu việc chưa kiểm lại.
