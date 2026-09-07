# SPEC: Orchestrator — Resume · Cost · Reliability

> EPIC **E6** của sản phẩm Dipro AI Boost. Bối cảnh sản phẩm, data model `.orchestrator/`, non-functional dùng chung → `docs/orchestrator/OVERVIEW.md`. Giả định chưa giải quyết → `docs/orchestrator/ASSUMPTIONS-GAPS.md`.
>
> Nguồn: `SPEC-pipeline-orchestrator.md` v0.1 §F6.1–F6.3.

## Mô tả nghiệp vụ

Một lượt chạy pipeline đầy đủ kéo dài hàng giờ và tiêu tốn tiền thật. Hai câu hỏi luôn được đặt ra mà hiện chưa có cách trả lời:

**"Máy tắt giữa chừng thì sao?"** — Kit stateless theo thiết kế: không có gì ghi lại pipeline đang ở đâu. Đóng máy giữa stage ⑤ thì mở lại phải tự đoán xem đã chạy tới đâu, agent nào xong, agent nào dở. Với một lượt chạy dài nhiều giờ, mất trắng như vậy là không chấp nhận được.

**"Tốn bao nhiêu?"** — Công ty đang bán quy trình này với con số "tiết kiệm 70–75%", dựa trên một phép đo thủ công duy nhất (38 màn hình trong 2.5 giờ). Không có bất kỳ đo đạc tự động nào. Không biết agent nào đắt, stage nào đắt, hay một feature trung bình tốn bao nhiêu.

E6 trả lời cả hai. Trạng thái ghi liên tục vào `state.json` theo cách an toàn với sự cố — mở lại app là thấy đúng chỗ đang dở. Cost bóc từ kết quả mỗi lượt chạy agent, cộng dồn theo agent, theo stage, theo cả pipeline run, và xuất được ra CSV để đưa vào báo cáo ROI cho khách hàng.

Phần thứ ba là xử lý lỗi cho tử tế: agent hỏng thì không được im lặng, không được mất log, và phải có đường đi tiếp — thử lại hoặc bỏ qua có đánh dấu.

> **Lưu ý về mức độ chắc chắn:** cách Claude Code báo cáo cost và cách khôi phục session (`--resume`) là **giả định chưa được kiểm chứng** (`ASSUMPTIONS-GAPS.md` A5). Vì vậy AC dưới đây mô tả **hành vi quan sát được** của app, không đóng băng bất kỳ định dạng dữ liệu cụ thể nào. Spike phải chạy trước MVP 2.

## Actors & Preconditions

| Actor | Vai trò trong feature này |
|---|---|
| **PM** | Actor chính — khôi phục lượt chạy sau sự cố, đọc cost, xuất CSV cho báo cáo |
| **Tech Lead** | Xem cost theo agent để điều chỉnh model mapping (giảm chi phí) |

**Phạm vi repo:** single-repo (`E01`) — **không cần Contract Lock** cho chính feature này.

**Preconditions:**

- E1 đã hoàn tất: project đã mở, `.orchestrator/` tồn tại.
- E2 đã hoàn tất: có engine chạy agent để mà theo dõi trạng thái và cost.
- Spike A5 đã chạy: đã biết Claude Code báo cáo cost và khôi phục session như thế nào.

## Happy Path

### Khôi phục sau sự cố

1. PM chạy pipeline tới stage ⑤. `backend-agent` đang chạy dở thì máy mất điện.
2. PM bật máy, mở app, chọn lại project.
3. App đọc `state.json`, dựng lại toàn bộ trạng thái: stage ①–④ `done`, `backend-agent` được đánh dấu **`interrupted`** (không phải `failed` — app biết nó bị cắt ngang, không phải tự hỏng).
4. Pipeline Board hiện đúng như trước sự cố, kèm banner cho biết lượt chạy này từng bị gián đoạn.
5. PM bấm vào node `backend-agent` → hai lựa chọn: **Resume** (chạy tiếp phiên cũ) hoặc **Re-run** (chạy lại từ đầu).
6. PM chọn Resume. App khôi phục phiên làm việc cũ của agent và chạy tiếp.
7. Toàn bộ log đã ghi trước sự cố vẫn đọc được — không mất.

### Theo dõi chi phí

8. Pipeline chạy xong. PM mở **Cost & Reports** (`OR_COST_001`).
9. Bảng cost theo 3 chiều: **theo agent** (agent nào tốn nhất), **theo stage** (stage nào tốn nhất), **theo lượt chạy** (feature này tổng bao nhiêu).
10. PM thấy `techlead-design-agent` chạy opus chiếm 40% tổng chi phí → cân nhắc đổi model trong Settings.
11. PM bấm **Xuất CSV** → file chứa đủ số liệu để dán vào báo cáo ROI.
12. Tab **Lịch sử** liệt kê các lượt chạy trước, so sánh được chi phí giữa các feature.

### Xử lý lỗi

13. Ở một lượt chạy khác, `qc-automation-agent` chạy 30 phút không xong (website DEV chưa bật).
14. App kill agent, node chuyển `failed`, ghi rõ nguyên nhân là **timeout**, log giữ nguyên.
15. PM bật website rồi bấm **Retry**. App chạy lại agent đó, đếm là lần thử thứ 1.
16. Lần này vẫn hỏng. PM bấm Retry lần nữa — lần thứ 2, chạm giới hạn mặc định.
17. Hỏng tiếp thì nút Retry mờ đi. PM bấm **Skip** — node chuyển `skipped (manual)`, pipeline chạy tiếp stage sau, và trạng thái này hiển thị khác `done` để về sau không ai nhầm là đã chạy.

## Alternative Flows & Edge Cases

| # | Tình huống | Hành vi mong đợi |
|---|---|---|
| AF-1 | `state.json` hỏng (JSON không parse được) | App không crash. Backup thành `state.json.bak`, dựng lại trạng thái từ artifact trên disk (như E3 vẫn làm), báo PM rõ những gì đã mất |
| AF-2 | App bị kill đúng lúc đang ghi `state.json` | Ghi kiểu atomic nên file cũ vẫn nguyên vẹn — không bao giờ có file ghi dở |
| AF-3 | Resume phiên cũ thất bại (phiên hết hạn hoặc không tồn tại) | Báo rõ lý do, chuyển sang gợi ý Re-run. **Không** im lặng chạy lại từ đầu như thể đang resume |
| AF-4 | Nhiều agent cùng `interrupted` (stage song song bị cắt ngang) | Mỗi agent xử lý độc lập — resume/re-run riêng từng cái |
| AF-5 | Process agent còn sống nhưng app đã đóng (agent mồ côi) | Khi mở lại app, phát hiện và báo có process còn chạy; cho chọn gắn lại hoặc kill |
| AF-6 | Không lấy được cost của một lượt chạy agent | Hiện `không có số liệu` cho dòng đó. **Không** ước lượng, **không** điền 0 (0 sẽ làm sai tổng) |
| AF-7 | Tổng cost có dòng thiếu số liệu | Tổng vẫn hiện, kèm ghi chú "chưa tính N lượt chạy thiếu số liệu" |
| AF-8 | Xuất CSV khi chưa có lượt chạy nào | Nút bị vô hiệu kèm giải thích, không xuất file rỗng |
| AF-9 | Agent hỏng ngay khi khởi động (sai model, thiếu quyền) | Phân biệt với lỗi giữa chừng — nêu rõ lỗi ở khâu khởi động và nguyên nhân |
| AF-10 | Retry một agent đã ghi ra artifact ở lần chạy trước | Cảnh báo artifact sẽ bị agent ghi đè trước khi chạy lại |
| AF-11 | PM Skip một agent mà agent sau phụ thuộc vào nó | Cảnh báo rõ agent nào phía sau sẽ chạy thiếu đầu vào, PM tự quyết |
| AF-12 | `.orchestrator/runs/` phình to sau nhiều lượt chạy | Có cách xoá log cũ; xoá log **không** làm mất số liệu cost tổng hợp |
| AF-13 | Đổi model của agent giữa các lượt chạy | Lịch sử cost ghi lại **model thực tế đã dùng** cho từng lượt, không dùng model hiện tại trong config để tính lại |

## Acceptance Criteria

**Trạng thái & khôi phục**

- **AC-E6-01** — Trạng thái từng stage, từng agent, và session id của lượt chạy gần nhất được ghi vào `.orchestrator/state.json`.
- **AC-E6-02** — Mọi thao tác ghi `state.json` là atomic: app bị kill giữa lúc ghi thì file cũ vẫn nguyên vẹn và đọc được, không bao giờ tồn tại file ghi dở.
- **AC-E6-03** — Mở lại app sau khi đóng đột ngột dựng lại đúng trạng thái Pipeline Board như trước thời điểm đóng.
- **AC-E6-04** — Agent đang chạy tại thời điểm app đóng được đánh dấu **`interrupted`**, phân biệt được với `failed` cả trong `state.json` lẫn trên UI.
- **AC-E6-05** — Với agent `interrupted`, app cho chọn **Resume** (chạy tiếp phiên cũ) hoặc **Re-run** (chạy lại từ đầu).
- **AC-E6-06** — Resume thất bại thì app báo rõ lý do và gợi ý Re-run; app **không** âm thầm chạy lại từ đầu trong khi người dùng tưởng đang resume.
- **AC-E6-07** — Log đã ghi trước khi bị gián đoạn vẫn đọc được sau khi mở lại app.
- **AC-E6-08** — `state.json` hỏng thì app backup file hỏng, dựng lại trạng thái từ artifact trên disk, và báo cho người dùng biết những gì không khôi phục được — app không crash.
- **AC-E6-09** — Nhiều agent cùng `interrupted` thì mỗi agent được resume hoặc re-run độc lập.
- **AC-E6-10** — Process agent còn sống sau khi app đóng được phát hiện khi mở lại app, và người dùng chọn được gắn lại hoặc kill.

**Chi phí**

- **AC-E6-11** — Sau mỗi lượt chạy agent, app ghi lại chi phí của lượt đó vào `.orchestrator/runs/`.
- **AC-E6-12** — Màn hình Cost & Reports hiển thị chi phí cộng dồn theo **agent**, theo **stage**, và theo **pipeline run**.
- **AC-E6-13** — Không lấy được chi phí của một lượt chạy thì dòng đó hiện `không có số liệu`. App **không** điền 0 và **không** ước lượng.
- **AC-E6-14** — Tổng chi phí có dòng thiếu số liệu vẫn hiển thị được, kèm ghi chú số lượt chạy chưa được tính vào tổng.
- **AC-E6-15** — Xuất được số liệu chi phí ra file CSV, gồm đủ các chiều agent / stage / run.
- **AC-E6-16** — Chưa có lượt chạy nào thì nút xuất CSV bị vô hiệu kèm giải thích; app không xuất file rỗng.
- **AC-E6-17** — Tab Lịch sử liệt kê các lượt chạy trước, cho so sánh chi phí giữa các feature.
- **AC-E6-18** — Bản ghi chi phí lưu kèm **model thực tế đã dùng** cho lượt chạy đó; đổi model trong Settings về sau **không** làm thay đổi số liệu lịch sử.
- **AC-E6-19** — Chi phí cộng dồn của agent đang chạy được cập nhật ngay trong Log Console trong lúc agent còn chạy (liên kết với `AC-E2-07`).

**Xử lý lỗi**

- **AC-E6-20** — Agent thoát với mã lỗi khác 0 khiến node chuyển `failed`, giữ nguyên toàn bộ log, và hiện nút Retry cùng Skip.
- **AC-E6-21** — Timeout của từng agent cấu hình được riêng, mặc định 30 phút.
- **AC-E6-22** — Agent vượt timeout bị kill và trạng thái ghi rõ nguyên nhân là timeout, phân biệt được với lỗi do agent trả về.
- **AC-E6-23** — Số lần retry tối đa cấu hình được, mặc định 2. Vượt giới hạn thì nút Retry bị vô hiệu.
- **AC-E6-24** — Retry một agent đã từng ghi ra artifact thì app cảnh báo artifact sẽ bị ghi đè trước khi chạy lại.
- **AC-E6-25** — Skip chuyển node sang `skipped (manual)`; trạng thái này hiển thị khác `done` trên Pipeline Board và trong mọi báo cáo.
- **AC-E6-26** — Skip một agent mà agent phía sau phụ thuộc vào thì app cảnh báo nêu đích danh agent sẽ chạy thiếu đầu vào.
- **AC-E6-27** — Lỗi ở khâu khởi động agent (sai model, thiếu quyền) được phân biệt với lỗi giữa chừng, và thông báo nêu rõ nguyên nhân.
- **AC-E6-28** — Có cách xoá log của các lượt chạy cũ; xoá log **không** làm mất số liệu chi phí đã tổng hợp.

## Out of Scope

- **Dự báo chi phí trước khi chạy** — app chỉ đo cái đã xảy ra.
- **Đặt hạn mức chi phí và tự dừng khi vượt** — không thuộc v1.
- **Tự chọn model rẻ hơn để tối ưu chi phí** — app chỉ đưa số liệu, người quyết.
- **Tự resume ngay khi mở app** — luôn phải có thao tác xác nhận của người dùng.
- **Khôi phục trạng thái ở giữa một lượt chạy agent** — đơn vị nhỏ nhất để resume là một lượt chạy agent, không phải từng bước bên trong.
- **Đồng bộ số liệu chi phí lên server tập trung** — CSV là hình thức xuất duy nhất trong v1.
- **Xuất báo cáo dạng PDF hay biểu đồ** — v1 chỉ bảng và CSV.
- **So sánh chi phí AI với chi phí nhân công** — phép tính ROI do người làm ngoài app, dựa trên CSV.

## Screens

| Screen Code | Screen | Actor | App | Screen Type | Mô tả ngắn | Figma Link |
|---|---|---|---|---|---|---|
| `OR_COST_001` | Cost & Reports | PM | E01* | Report | Bảng chi phí theo agent / stage / pipeline run, nút xuất CSV, tab Lịch sử các lượt chạy trước | |

> Nút Resume / Re-run / Retry / Skip nằm trong `OR_EXEC_002` (Agent Detail / Log Console, thuộc E2) và panel chi tiết node của `OR_MONI_001` (Pipeline Board, thuộc E3). E6 chỉ bổ sung một màn hình riêng.
>
> `*` Cột **App** = Epic code của repo đích. Bảng Ecosystem trong `AGENTS.md` của kit hiện còn placeholder, nên `E01` là giá trị **tạm** cho repo desktop app — cần xác nhận lại khi khởi tạo repo thật.
