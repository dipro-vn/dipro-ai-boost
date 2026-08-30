export const meta = {
  name: 'bmad-build-phase',
  description: 'BMAD Build+Test phase — Backend (migration + API + Contract) → Frontend/Mobile song song → QC Automation (Playwright E2E). Chạy sau khi bmad-plan-phase đã được user duyệt.',
  phases: [
    { title: 'Backend', detail: 'Backend implement task Phase 1→2 — output bảng API Contract' },
    { title: 'Frontend/Mobile', detail: 'Song song, dùng API Contract + design-analysis.md' },
    { title: 'QC', detail: 'E2E automation (Playwright headed)' },
  ],
}

if (!args?.feature) {
  throw new Error('Thiếu args.feature — cần tên feature (kebab-case) để chạy pipeline')
}

const STOP_INSTRUCTION =
  'Sau khi in Output, DỪNG LẠI — không hỏi thêm câu hỏi xác nhận bước tiếp theo (vd "bạn có muốn tôi tiếp tục không?").'

// ---------- Backend: migration + API + API Contract ----------
phase('Backend')

const be = await agent(
  `Đọc .claude/agents/backend-agent.md rồi đóng vai Backend Developer, implement các task Phase 1→2 (DB migration + API) ` +
  `cho feature "${args.feature}" — task files nằm trong <DOCS_ROOT>/features/${args.feature}/<backend-repo>/tasks/ ` +
  `(xem <DOCS_ROOT> thật và tên repo vai trò backend trong AGENTS.md section Ecosystem). ` +
  `Chạy lint + test + coverage của chính các task đó tới khi xanh trước khi in Output. ` +
  `Output PHẢI kèm bảng API Contract đầy đủ (method, path, request, response). ${STOP_INSTRUCTION}`,
  { agentType: 'backend-agent', label: 'backend-agent' }
)
log('Backend implement xong — chuyển sang Frontend/Mobile.')

// ---------- Frontend/Mobile: song song, dùng API Contract của BE ----------
phase('Frontend/Mobile')

const designAnalysisPath = `<DOCS_ROOT>/features/${args.feature}/design-analysis.md`

const [fe, mobile] = await parallel([
  () =>
    agent(
      `Đọc .claude/agents/frontend-agent.md rồi đóng vai Frontend Developer, implement task Phase 3 cho feature "${args.feature}" ` +
      `— áp dụng cho tất cả repo vai trò frontend liên quan tới feature này (xem AGENTS.md Ecosystem). ` +
      `Trước khi code: (1) paste bảng API Contract sau vào section "## API Contract" của task file Phase 3 tương ứng ` +
      `(giữ đúng bước 5b trong AGENTS.md — FE không tự đoán endpoint):\n${JSON.stringify(be)}\n` +
      `(2) đọc "${designAnalysisPath}" (output của design-analyst-agent — screens đã phân tích + bảng asset export) nếu file tồn tại, ` +
      `dùng làm nguồn design chính. Rồi mới implement theo Step1→Step2→Step3, chạy lint + type-check + test tới khi xanh. ${STOP_INSTRUCTION}`,
      { agentType: 'frontend-agent', label: 'frontend-agent', phase: 'Frontend/Mobile' }
    ),
  () =>
    agent(
      `Đọc .claude/agents/mobile-agent.md rồi đóng vai Mobile Developer, implement task Phase 3 cho feature "${args.feature}" ` +
      `(bỏ qua và trả về "no mobile scope" nếu dự án không có repo vai trò mobile, hoặc feature này không chạm repo đó). ` +
      `Trước khi code: (1) paste bảng API Contract sau vào section "## API Contract" của task file Phase 3 tương ứng:\n${JSON.stringify(be)}\n` +
      `(2) đọc "${designAnalysisPath}" (output của design-analyst-agent) nếu file tồn tại, dùng làm nguồn design chính. ` +
      `Rồi mới implement, chạy flutter analyze + flutter test tới khi xanh. ${STOP_INSTRUCTION}`,
      { agentType: 'mobile-agent', label: 'mobile-agent', phase: 'Frontend/Mobile' }
    ),
])
log('Frontend/Mobile implement xong — chuyển sang QC Automation.')

// ---------- QC Automation ----------
phase('QC')
const automation = await agent(
  `Đọc .claude/agents/qc-automation-agent.md rồi đóng vai QC Automation, test feature "${args.feature}" bằng Playwright E2E (headed mode). ` +
  `Nếu chưa có repo E2E testing (xem section "E2E Testing" trong AGENTS.md) hoặc website DEV chưa chạy → dừng lại, báo rõ điều kiện còn thiếu thay vì đoán.`,
  { agentType: 'qc-automation-agent', label: 'qc-automation-agent', phase: 'QC' }
)

return {
  feature: args.feature,
  be,
  fe,
  mobile,
  automation,
}
