# Versioning — snapshot mỗi lần chạy

> Kit này chạy nhiều lần trên cùng một hệ thống (hệ thống đổi, scope mở rộng, bổ sung role mới). Không có versioning thì không biết lần này khác lần trước chỗ nào.

---

## 1. Cấu trúc

```
<OUT>/
├── latest/                                  ← luôn là bản mới nhất
│   ├── 01_HighLevel_<system>_v<N>.docx
│   ├── 01_Inventory_<system>_v<N>.xlsx      ← artifact nội bộ agent
│   ├── 02_BugList_<system>_v<N>.xlsx        ← nếu có chạy O2B
│   ├── flow/{flow.json,flow.png}
│   ├── narrative.json
│   ├── evidence/
│   └── recon/
└── versions/
    ├── v1_23092026/
    └── v2_15102026/
        ├── (bản sao đầy đủ của latest tại thời điểm đó)
        ├── gates/{v1,v2,v3,v5,v8,selftest}.md
        └── run-log.md
```

Tên folder: `v<N>_<DDMMYYYY>`. `N` tăng dần, **không** đánh theo ngày.

---

## 2. Quy tắc

1. **Trước khi chạy:** đọc `versions/` → xác định `N` tiếp theo.
2. **Trước khi ghi đè `latest/`:** copy `latest/` hiện tại sang `versions/v<N-1>_.../` nếu chưa có.
3. **Sau khi mọi gate PASS:** snapshot `latest/` sang `versions/v<N>_.../` + ghi `run-log.md`.
4. **Không bao giờ** sửa nội dung version cũ.

---

## 3. `run-log.md` per version

```markdown
# Run log — v<N>_<DDMMYYYY>

## Điều kiện chạy
| Hạng mục | Giá trị |
|---|---|
| run_mode | FULL / DELTA / READ_ONLY_REVIEW |
| Đọc từ version | v<N-1> hoặc — |
| Scope (G0) | ... |
| Crawl mode (G2) | ... |
| Budget dùng | 137/200 URL · 22 phút |

## Discovery Brief
(copy nguyên văn bảng đã cho user confirm)

## Kết quả gate
| Gate | Kết quả |
|---|---|
| V1 Evidence | 9 checks · 9 PASS · 0 FAIL |
| V2 Inventory | 16 checks · ... |
| V3 High Level | 12 checks · ... |
| V5 Flow | 9 checks · ... |
| V8 Bug List | 14 checks · ... / ⬜ không chạy |
| V9 Self-test | 20 ca · 20 PASS |

## Diff so với v<N-1>
| Thay đổi | Chi tiết |
|---|---|
| Function mới | F-045, F-046 |
| Function đổi Status | F-012 To verify → Confirmed (EV-0210) |
| Screen mới | SC-031 |
| Open Question đã đóng | Q-003 |
| Open Question mới | Q-011 |
| Bảng DB mới | — |

## Feedback của user
(để trống — user ghi vào đây rồi trigger lại agent)
```

---

## 4. Resume — lần chạy sau đọc gì

Agent **BẮT BUỘC** đọc `versions/v<N-1>/01_Inventory_*.xlsx` trước khi crawl:

| Đọc sheet | Để biết |
|---|---|
| `00_Meta` | Scope cũ, câu trả lời G0–G8, vùng cấm chạm, budget đã dùng |
| `01_Function` / `02_Screen` | Đã phủ tới đâu → chỉ crawl phần thiếu (mode `DELTA`) |
| `05_Evidence` | Evidence còn dùng được (≤ 30 ngày) hay phải chụp lại |
| `06_OpenQuestions` | Câu hỏi còn `Open` → hỏi lại user xem đã có câu trả lời chưa |

Sau đó chạy **Gate G-R** để user chọn `FULL` / `DELTA` / `READ_ONLY_REVIEW`.

❌ Bỏ qua version cũ rồi crawl lại từ đầu = mất mọi câu trả lời user đã cho, tốn budget vô ích.
