# Business Flows — Long-term Project Memory (optional pattern)

> **Kit gốc không có dữ liệu business-flow thật** — folder này chỉ mô tả **pattern** để dự án tự tạo nếu domain nghiệp vụ đủ phức tạp (nhiều domain, nhiều actor, cần lookup nhanh trước khi viết SPEC). Nếu dự án nhỏ/đơn giản, có thể bỏ qua toàn bộ folder này và chỉ dùng `.claude/context/specification.md`.

## Khi nào cần pattern này

Khi `ba-agent` phải trả lời "feature mới này thuộc domain nào" trước khi biết nên hỏi user câu gì — tức là dự án có **nhiều domain nghiệp vụ tách biệt** (ví dụ: 1 dự án thương mại điện tử có domain Order, Payment, Shipping, Marketing... mỗi domain nhiều actor/story).

## Cấu trúc đề xuất

```
business-flows/
├── README.md                  ← file này — index cách dùng
├── business-flow-index.md     ← master index: tất cả domain + actor liên quan + backlog ID (nếu có)
├── function-list.md            ← (optional) danh sách chi tiết function/story theo epic — có thể lớn, chỉ load khi cần
├── screen-code-rule.md         ← (optional) quy tắc đặt Screen Code nếu dự án cần chuẩn hoá tên màn hình
└── domains/
    ├── <domain-slug-1>.md      ← chi tiết 1 domain: actors, story, flow, priority
    └── <domain-slug-2>.md
```

## Nguồn dữ liệu

Nguồn truth nên là **1 file có cấu trúc** (spreadsheet, Notion database, Backlog export...) mà BA duy trì, sau đó re-generate các file `.md` này từ đó — **không sửa `.md` trực tiếp** nếu có nguồn gốc khác, để tránh lệch dữ liệu.

## Khi nào load file nào (nguyên tắc — áp dụng khi dự án đã tạo các file thật)

| Tình huống | File cần đọc |
|---|---|
| BA tạo SPEC mới, chưa biết feature thuộc domain nào | `business-flow-index.md` để lookup → chọn 1 domain |
| BA đã biết domain | `domains/<slug>.md` tương ứng |
| Tech Lead Design cần hiểu actors/flow trước khi vẽ data model | `domains/<slug>.md` |
| PM cần ước lượng scope theo epic | `function-list.md` (summary by epic) |
| Dev / QC cần đặt screen code mới | `screen-code-rule.md` |

**Đọc on-demand, không load tất cả cùng lúc** — tuân thủ "không đọc rộng ngoài role" của `POLICIES.md`.
</content>
