---
description: Tạo danh sách User Story (Epic → User Story, xlsx) từ SPEC đã có — on-demand, không vẽ Figma. Dùng: /user-stories [Epic hoặc phạm vi]
---

Đọc `.claude/ba-agent/user-stories.md`, `.claude/ba-agent/story-splitting.md` và `.claude/ba-agent/ac-standard.md`, rồi thực hiện **Output US — Danh sách User Story** (Bước 5.9 của `ba-agent.md`) cho phạm vi: **$ARGUMENTS**

Bắt buộc theo đúng thứ tự, không được rút gọn:

1. **Input Gate** — kiểm `SPEC.md` có `## Acceptance Criteria` (theo `ac-standard.md`) và `## Screens` có cột `FR No.`. Thiếu → in `Input Gate US: BLOCKED` và hỏi user, không tự bịa AC
2. **`AskUserQuestion`** — có dùng Epic không · phạm vi (toàn bộ FR / một Epic). Không tự quyết
3. Viết `<output-folder>/user-stories/USER-STORIES.md` — **tối đa 2 tầng Epic → User Story**, không Level 1-2-3
4. Tự đánh giá INVEST từng Story; áp dụng `story-splitting.md` (Spike khi chưa ước lượng được, **không ghi estimate**)
5. Chạy `export-user-stories.py` **kèm `--spec <SPEC.md>`** — `FAIL = 0` mới có xlsx; in `US COUNT` + `US COVERAGE — THIẾU: []` + danh sách AC mồ côi (WARN)
6. Thêm row `User Stories` vào `SPEC.md ## BA Deliverables`, snapshot theo `versioning.md` Rule 2e
7. In report theo mẫu ở Bước 5.9

Cấm: vẽ / gắn tag Story lên Sitemap hoặc Figma · chép nội dung AC vào xlsx · điền Estimate / Ưu tiên · dùng số Story làm mốc "đã đủ".

Nếu `$ARGUMENTS` rỗng → hỏi phạm vi ở bước 2, không tự chọn toàn bộ.
