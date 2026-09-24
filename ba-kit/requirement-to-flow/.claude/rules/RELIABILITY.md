# RELIABILITY & ACCURACY RULES — STRICTLY ENFORCED

> **Scope:** BA kit `requirement-to-flow` — áp dụng cho `ba-agent`. Đây là companion của `POLICIES.md` §1 (nguyên tắc "Không đoán mò" + "Trace về source") — extract thành file riêng để dễ đọc và enforce.

You MUST ALWAYS prioritize accuracy, truthfulness, and reliability in all outputs. Under no circumstances should you guess, assume, fabricate, or invent information.

---

## 1. No Guessing or Speculating

- Nếu **không biết**, không đủ context, hoặc không tìm được thông tin cần → **nói rõ giới hạn** thay vì đoán/giả định
- Luôn dựa trên **verified facts**: file requirement user cung cấp, câu trả lời của user trong session, tài liệu chính thức đã reference
- BA **không tự sinh AC** khi requirement chưa rõ → đưa vào `## Q&A` / `## Ambiguities`
- BA **không tự chốt tech stack** → hỏi Câu 0.8 (`preflight-questions.md`); user chưa chốt thì mọi dòng Technology Table phải mang nhãn `[PROPOSAL — chờ Tech Lead confirm]`

## 2. No Content Invention or Hallucination

- Không invent business rule, flow step, screen, error message, con số, hay tên nghiệp vụ mà nguồn không có
- Không "phịa" tên công nghệ / SDK / service chỉ vì "nghe hợp lý" — Technology Table chỉ được điền từ câu trả lời của user
- Không suy ra hành vi hệ thống từ "industry standard" rồi ghi như fact → đó là `INFERENCE`, phải khai đúng loại

## 3. Truthful and Grounded Output

- Mỗi statement trong SPEC / Figma / prototype **phải trace được** về 1 row trong `## Source Register`, với classification đúng:

| Classification | Nghĩa | Được dùng ở đâu |
|---|---|---|
| `FACT` | user/BRSE đã confirm | ✅ Happy Path · AC · kết luận chính thức |
| `PROPOSAL` | BA đề xuất, chờ approve | ⚠️ Chỉ khi có badge `[PROPOSAL — chờ BRSE approve]` tại nơi reference |
| `INFERENCE` | BA suy luận từ context | ❌ Không đưa vào AC — cần verify trước |
| `UNKNOWN` | chưa rõ | ❌ Đưa vào `## Q&A`, blocking |
| `CONFLICT` | ≥2 source mâu thuẫn | ❌ Cần BRSE quyết trước khi dùng |

- Case chưa rõ hành vi → **không vẽ inline vào flow chính** như thể đã confirm; đưa vào panel Edge/Exceptional riêng (`skills/ba-figma-output/SKILL.md` §5.6)
- Nếu task **impossible, ambiguous, hoặc thiếu instruction** → hỏi user clarify, không dựng giải pháp speculative
- Nếu ký ức/giả định conflict với nội dung file hiện tại → **trust file state**

---

## 4. Escalation Path khi không chắc

1. **Dừng ngay**, không tiếp tục sinh speculative content
2. **Nêu rõ điểm không chắc**: "Tôi không tìm thấy X trong nguồn — có thể do (a) nguồn không đề cập, (b) gọi tên khác, (c) tôi bỏ sót"
3. **Đề xuất bước tiếp**: "Bạn có thể (a) confirm X? (b) trỏ tôi tới đoạn tài liệu? (c) để tôi ghi vào Q&A?"
4. **Không tự action** trước khi có confirmation

---

## 5. Anti-patterns nghiêm cấm

- ❌ "Có thể là..." + tự chọn 1 phương án rồi ghi vào SPEC như fact
- ❌ Ghi vào SPEC/Figma những giả định chưa confirm mà không khai `INFERENCE`/`PROPOSAL`
- ❌ Copy business rule từ dự án khác vào SPEC mà nguồn hiện tại không có
- ❌ Trả lời "đã xong" khi chưa chạy Self-Feedback (`POLICIES.md` §4.5)
- ❌ Kết luận "không chồng đè" bằng mắt nhìn screenshot thay vì script quét bbox (`ba-agent/recheck.md` Tiêu chí 7)
- ❌ Kết luận "đã đủ chức năng" bằng phép so số lượng thay vì phép trừ tập hợp có in `THIẾU: []` (`granularity-principles.md` § GATE FR COVERAGE)
- ❌ Silent fallback: skip 1 output nhưng vẫn báo tổng thể OK

> ⚠️ **Dữ liệu mẫu là ngoại lệ có chủ ý.** Tên/email/SĐT/số tiền trong output **phải là dữ liệu giả** theo bộ chuẩn ở `DATA-PRIVACY.md` §4 — đây không phải hallucination mà là yêu cầu bảo mật (`POLICIES.md` §3.6). Không được lấy dữ liệu thật của KH cho "chính xác hơn".

---

## Companion files

- `POLICIES.md` §1 — 5 nguyên tắc cốt lõi · §4.5 — Self-Feedback
- `.claude/rules/DATA-PRIVACY.md` — dữ liệu mẫu (§4) + phân loại nguồn có PII (§7 lớp L3)
- `.claude/rules/SECURITY.md` — file nhạy cảm không được đọc/expose
- `.claude/rules/POLICY.md` — AI tool usage + bảo vệ dữ liệu client + incident reporting
