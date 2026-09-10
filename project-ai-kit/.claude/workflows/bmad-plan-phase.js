export const meta = {
  name: 'bmad-plan-phase',
  description: 'BMAD Planning phase — BA → Design (Tech Lead/QC/Designer song song) → Tech Lead Tasks. Dừng lại chờ user duyệt trước khi chạy bmad-build-phase.',
  phases: [
    { title: 'BA', detail: 'Phân tích yêu cầu, tạo SPEC.md' },
    { title: 'Design', detail: 'Tech Lead Design + QC manual TC + Designer Figma — chạy song song' },
    { title: 'Tasks', detail: 'Phân rã DESIGN.md thành task files' },
  ],
}

if (!args?.feature) {
  throw new Error('Thiếu args.feature — cần tên feature (kebab-case) để chạy pipeline')
}

phase('BA')
const spec = await agent(
  `Đọc .claude/agents/ba-agent.md rồi đóng vai BA cho feature "${args.feature}". ` +
  `Định nghĩa hoàn thành là ĐỦ 6 outputs (SPEC.md 11 sections có ## BA Deliverables, 3 Figma frame, prototype/index.html, MkDocs) — không dừng ở SPEC.md. ` +
  // Bước 2b câu 0 / 0.5 của ba-agent.md là hai câu hỏi BẮT BUỘC; workflow
  // này chạy tự động nên phải truyền câu trả lời vào, nếu không agent sẽ
  // dừng lại hỏi hoặc (tệ hơn) tự đoán platform.
  `FIGMA_OUTPUT_URL: ${args.figmaUrl || '(chưa có — bỏ qua Output 1-3, ghi ❌ Skipped vào ## BA Deliverables, vẫn làm Output 0/4/5)'}. ` +
  `TARGET_PLATFORM: ${args.targetPlatform || '(chưa có — hỏi lại, KHÔNG tự suy diễn)'}. ` +
  `Mô tả thêm: ${args.description || '(không có — nếu thiếu thông tin bắt buộc để hoàn thành SPEC thì hỏi lại, không tự giả định)'}`,
  { agentType: 'ba-agent', label: 'ba-agent' }
)
log('BA xong: 6 outputs (xem ## BA Deliverables trong SPEC.md)')

phase('Design')
const [design, testcases, ui] = await parallel([
  () => agent(
    `Đọc .claude/agents/techlead-design-agent.md rồi đóng vai Tech Lead Design, tạo DESIGN.md per repo từ SPEC.md của feature "${args.feature}"`,
    { agentType: 'techlead-design-agent', label: 'techlead-design-agent', phase: 'Design' }
  ),
  () => agent(
    `Đọc .claude/agents/qc-agent.md rồi đóng vai QC, sinh manual test cases (RBT) từ SPEC.md của feature "${args.feature}"`,
    { agentType: 'qc-agent', label: 'qc-agent', phase: 'Design' }
  ),
  () => agent(
    `Đọc .claude/agents/designer-agent.md rồi đóng vai Designer, tạo Figma screens + điền Figma URL vào SPEC.md ## Screens cho feature "${args.feature}"`,
    { agentType: 'designer-agent', label: 'designer-agent', phase: 'Design' }
  ),
])
log('Design phase xong: DESIGN.md (per repo) + test cases + Figma screens')

phase('Tasks')
const tasks = await agent(
  `Đọc .claude/agents/techlead-tasks-agent.md rồi đóng vai Tech Lead Tasks, phân rã DESIGN.md thành task files cho feature "${args.feature}"`,
  { agentType: 'techlead-tasks-agent', label: 'techlead-tasks-agent' }
)
log('Tasks xong: task files đã tạo')

return {
  feature: args.feature,
  spec,
  design,
  testcases,
  ui,
  tasks,
  gate:
    `⏸ GATE — Planning phase xong (SPEC + DESIGN + test cases + Figma + tasks) cho feature "${args.feature}". ` +
    `Review toàn bộ output trước. Khi đã duyệt, chạy: /create-feature ${args.feature} build`,
}
