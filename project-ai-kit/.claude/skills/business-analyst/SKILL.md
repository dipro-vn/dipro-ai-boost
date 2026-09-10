---
name: business-analyst
description: >-
  Kỹ thuật discovery cho Business Analyst — cách đặt câu hỏi, đào tới root cause,
  và phát hiện yêu cầu mơ hồ trước khi viết SPEC.
  Quy trình BA đầy đủ (6 outputs, cấu trúc SPEC.md) nằm ở `.claude/agents/ba-agent.md` — file này KHÔNG lặp lại nó.
  Domain và actors cụ thể của dự án: đọc `.claude/context/specification.md` (điền qua `/init-kit`).
  Trigger khi phân tích yêu cầu, tạo SPEC, discovery, requirements gathering, hỏi "feature này làm gì".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, TodoWrite, WebSearch, WebFetch
---

> **Quy trình BA canonical là `.claude/agents/ba-agent.md`** — Definition of Done 6 outputs, 12 câu hỏi bắt buộc, cấu trúc `SPEC.md` 11 sections, Bước 5 vẽ Figma, Bước 5.5/5.6 tự review. Skill này KHÔNG định nghĩa quy trình và KHÔNG định nghĩa deliverable; nó chỉ cung cấp **kỹ thuật khai thác yêu cầu** dùng ở Bước 2.
>
> **Context dự án:** domain, actors, epics — đọc `.claude/context/specification.md` (điền qua `/init-kit`).

# Business Analyst — Kỹ thuật Discovery

**Vai trò:** Phase 1 (Discovery) của BMAD pipeline.

**Phạm vi skill này:** hỏi đúng câu, đào tới nguyên nhân thật, và phát hiện chỗ mơ hồ — trước khi bất kỳ dòng SPEC nào được viết.

## Khi nào dùng

- Đang ở Bước 2 của `ba-agent.md` và câu trả lời của user còn chung chung
- User mô tả **giải pháp** thay vì **vấn đề** ("làm cho tôi cái nút export") — cần đào ngược về nhu cầu
- Một yêu cầu có ≥2 cách hiểu hợp lý (Bước 2a — multiple interpretations)
- Cần định nghĩa Acceptance Criteria đo được từ một mong muốn định tính

## Nguyên tắc

1. **Start with Why** — hiểu vấn đề trước khi bàn giải pháp
2. **Data Over Opinions** — dựa trên bằng chứng, không dựa cảm tính
3. **User-Centric** — luôn quay về nhu cầu người dùng cuối
4. **Clarity Above All** — yêu cầu phải không thể hiểu hai nghĩa
5. **Không đoán mò** — thiếu thông tin thì hỏi, không tự điền (`POLICIES.md` §1)

## Khung câu hỏi discovery

Bổ sung cho 12 câu bắt buộc ở `ba-agent.md` Bước 2b — dùng khi câu trả lời còn mỏng.

### Đào vấn đề
- Vấn đề gì đang tồn tại? Ai gặp phải?
- Hiện tại họ xử lý bằng cách nào?
- Không giải quyết thì thiệt hại gì?
- Vì sao phải làm **bây giờ**?
- Tần suất xảy ra?

### Khám phá giải pháp
- Giải pháp đề xuất là gì? Ai là người dùng đích?
- Năng lực cốt lõi cần có?
- Khác gì so với cách làm hiện tại?
- Có phương án thay thế nào?

### Định nghĩa thành công
- Đo bằng chỉ số nào?
- Sau 3 / 6 / 12 tháng thì "thành công" trông ra sao?
- Tiêu chí nghiệm thu cụ thể là gì? (→ `## Acceptance Criteria` trong SPEC)

## Kỹ thuật phỏng vấn

- **5 Whys** — hỏi "tại sao" 5 lần để chạm nguyên nhân gốc, thay vì dừng ở triệu chứng
- **Jobs-to-be-Done** — hỏi user đang cố **hoàn thành việc gì**, không phải muốn **tính năng gì**
- **SMART** — biến mong muốn định tính thành AC đo được (Specific · Measurable · Achievable · Relevant · Time-bound)

Chi tiết từng khung → [REFERENCE.md](REFERENCE.md) và [resources/interview-frameworks.md](resources/interview-frameworks.md).

## Tài nguyên

| File | Dùng để |
|---|---|
| [REFERENCE.md](REFERENCE.md) | Khung phỏng vấn chi tiết, loại câu hỏi, pitfall thường gặp |
| [resources/interview-frameworks.md](resources/interview-frameworks.md) | Tham chiếu nhanh từng kỹ thuật |
| [scripts/discovery-checklist.sh](scripts/discovery-checklist.sh) | In ra bộ câu hỏi có cấu trúc để dẫn buổi phỏng vấn |

## Chất lượng câu trả lời thu được

Trước khi rời Bước 2, mỗi câu trả lời phải:

- Cụ thể, không thể hiểu hai nghĩa
- Nói được **why**, không chỉ **what**
- Có tiêu chí đo được cho phần sẽ thành Acceptance Criteria
- Nêu rõ rủi ro và phụ thuộc đã biết

Còn chỗ mơ hồ → hỏi tiếp, **không** tự điền giả định vào SPEC (`.claude/rules/RELIABILITY.md`).

## Ghi chú cho LLM

- Dùng TodoWrite theo dõi tiến độ nhiều bước
- Câu trả lời mơ hồ thì hỏi lại, đừng diễn giải hộ
- Dùng khung có cấu trúc (5 Whys, SMART, Jobs-to-be-Done) thay vì hỏi ngẫu hứng
- Xác nhận lại cách hiểu của mình ở mỗi bước
- Deliverable, path file, và bước tiếp theo — theo `ba-agent.md`, không tự đặt ra ở đây

**Nhớ:** Discovery là nền móng. Hiểu sâu trước đã.
