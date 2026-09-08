# example-project — fixture để test Dipro AI Boost

**Đây là dữ liệu tổng hợp, KHÔNG phải dự án thật** — dựng ra chỉ để mở thử trong Dipro AI Boost (Project Launcher → Pipeline Board).

## Cấu trúc

```
example-project/
├── kit-repo/              ← đóng vai "agentsRoot" (chứa .claude/agents/ + AGENTS.md)
├── docs/                  ← đóng vai "docsRoot" (chứa features/)
├── repos/                 ← đóng vai "repositoryRoot" (chứa các repo — 2/3 "đã clone")
└── sample-inputs/         ← nguyên liệu thô để test luồng Import Input → ba-agent
```

Cố ý **KHÔNG đối xứng** (giống phát hiện A1 trong `docs/orchestrator/ASSUMPTIONS-GAPS.md`) — 3 thư mục không nằm lồng trong nhau, đúng tinh thần app phải hỏi 3 đường dẫn độc lập, không được đoán.

## Nhập vào Project Launcher

Khi mở app, ở màn hình "Mở project mới", chọn `example-project/` làm điểm bắt đầu, sau đó **xác nhận/sửa lại 3 ô** (app có thể tự dò đúng 2/3, ô còn lại phải tự chỉ vì `repos/` không có dấu hiệu để dò tự động):

| Ô | Giá trị |
|---|---|
| Agents root | `example-project/kit-repo` |
| DOCS_ROOT | `example-project/docs` |
| Repository root | `example-project/repos` |

## Dữ liệu mẫu — cố ý trải đều 3 trạng thái MVP1 có thể suy ra

| Feature | Trạng thái mong đợi |
|---|---|
| `user-login` | Gần như toàn bộ node **Done** (SPEC đủ 7 section, có DESIGN.md, design-analysis.md, tasks/, test-cases/) |
| `payment-checkout` | Node BA ở trạng thái **Done (chưa đầy đủ)** — SPEC.md chỉ có 3/7 section bắt buộc |
| `notification-center` | Toàn bộ **Idle** — feature vừa tạo, chưa có gì |

## `sample-inputs/` — nguyên liệu thô để test luồng đầy đủ

Có 2 bộ, dùng thay thế nhau hoặc song song:

| Bộ | Kịch bản | Đặc điểm để test |
|---|---|---|
| `user-signup/` | Greenfield — chức năng hoàn toàn mới | 4 điểm chưa chốt trong biên bản họp |
| `user-login/` | Brownfield — thay màn đăng nhập cũ, phải sống chung với bảng `users` sẵn có | 4 điểm chưa chốt + 1 câu hỏi để ngỏ trong mô tả màn hình; nêu rõ `example-mobile` ngoài phạm vi |

Cả hai đều có file `.env` cố ý để kiểm tra bộ lọc import, và một thư mục con để kiểm tra preview
đọc được thư mục lồng.

### `user-signup/` — chi tiết

Đây **không phải** artifact BMAD, mà là thứ một BA nhận được ngoài đời trước khi có SPEC: email
khách hàng, biên bản họp, ghi chú kỹ thuật, mô tả màn hình vẽ tay. Dùng để chạy thử trọn vẹn
① BA Input → ba-agent → `SPEC.md`.

**Cách chạy:**

1. Trong app, cột **Workflow** bên trái: nếu chưa có `user-signup` thì bấm `+` → nhập
   `user-signup` → Tạo. Nếu đã có sẵn trong danh sách (thư mục `docs/features/user-signup/` đã
   tồn tại) thì chỉ cần bấm chọn nó — bấm `+` với tên trùng sẽ bị từ chối, đúng như thiết kế.
2. Chọn node ① BA ở cây pipeline → panel bên phải hiện form Import Input → chọn thư mục
   `example-project/sample-inputs/user-signup/`.
3. Xem preview rồi bấm chạy.

**Những thứ folder này cố ý dựng để test:**

| Thứ cần test | Cách nó được dựng |
|---|---|
| Bộ lọc file cấm đọc (AC-E2-32) | Có file `.env` — preview phải đưa vào mục **bị bỏ qua**, không copy sang `.ai-boost/inputs/` |
| Preview đọc cả thư mục con | Có thư mục `mo-ta-man-hinh/` với 2 file bên trong |
| Luồng agent hỏi lại (AC-E2-15/16/17) | Biên bản họp cố ý để **4 điểm chưa chốt** → BA phải hỏi thay vì tự bịa, node chuyển `waiting-input`, test được ô trả lời + `--resume` |
| Node `blocked` khi repo chưa clone (AC-E2-11) | Ghi chú kỹ thuật nêu rõ feature đụng `example-mobile` — repo này cố ý chưa clone trong fixture |
| SPEC đủ 7 section | Nguyên liệu đủ để suy ra cả 7 section bắt buộc, trừ những chỗ đã cố ý bỏ ngỏ |

> Lưu ý về một gap đã biết: app **chưa** phân loại file nhị phân (AF-17 — xem `IMPLEMENTATION-STATUS.md`),
> nên nếu bạn tự thêm ảnh/zip vào folder này thì chúng vẫn bị coi là "đọc được" và copy sang cho agent.

## Ecosystem (bảng `## Repos` trong AGENTS.md)

| Repo | Trạng thái mong đợi |
|---|---|
| `example-api` | đã clone (có folder `repos/example-api/`) |
| `example-web` | đã clone (có folder `repos/example-web/`) |
| `example-mobile` | **chưa clone** (không có folder tương ứng — cố ý, để test badge "chưa clone") |

## Agent files trong fixture

`kit-repo/.claude/agents/` mirror đúng 12 agent file thật của kit (gồm `design-analyst-agent.md`, bổ sung ở Phase C — B17 đã đóng). `pm-agent.md` không còn: agent PM đã bị gỡ khỏi kit cùng với `PLAN.md` và tính năng đẩy issue lên Backlog.

## Giới hạn

Chưa có `git init` ở đâu trong fixture này — dùng được để test Project Launcher / Pipeline Board / Artifact Viewer, nhưng **chưa đủ** để test nhánh diff dựa trên git ở T1.6 (sẽ cần bổ sung riêng khi tới lúc, hoặc dùng nhánh snapshot fallback vốn đã hoạt động được với dữ liệu này).
