# design-system/ — Design system của dự án

Folder này **đang trống**. Lần chạy đầu, Designer Agent hỏi nguồn design system (link Figma / tài liệu / link artifact / codebase / 1–5 màn Figma mẫu), phân tích đầy đủ rồi dựng tại đây và publish thành **Design System artifact** trên claude.ai để bạn duyệt:

```
design-system/
├── STATUS.md          ← trạng thái, link artifact, platform, TBD, mâu thuẫn, changelog
└── project/           ← nội dung artifact: design-system.json · tokens.json · README.md · components/ · assets/
```

Chuẩn định dạng: `.claude/designer-agent/design-system-format.md`. Chưa có nguồn design system → agent dừng lại, không vẽ.
