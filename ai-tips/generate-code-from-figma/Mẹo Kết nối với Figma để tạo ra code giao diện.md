# Mẹo Kết nối với Figma để tạo ra code giao diện (Claude CLI)

Hướng dẫn dùng **Claude CLI + Figma MCP** để đọc thiết kế trực tiếp từ Figma và **generate code FE** bám theo cấu trúc source repo sẵn có của dự án.

---

## Đầu vào

- **Tool:** Claude CLI (Claude Code)
- **Figma Desktop** của dự án — *lưu ý: bản Desktop, không phải web*
- **Copy Link URL section** ở Figma mà bạn muốn generate code (link từ Dev Mode, có chứa `?node-id=`)

## Đầu ra

- **Output 01 —** Đọc từ Figma → file `figma_<ComponentName>_context.md` + ảnh screenshot của node
- **Output 02 —** Generate code từ giao diện đó, bám theo cấu trúc source repo sẵn có (dùng **FE_AGENT**) để code ra đúng chuẩn cấu trúc dự án

---

## Setup cho từng dự án (qua Claude CLI)

Trong root repo dự án (nơi có folder `.claude/`):

- Tạo **`read-figma.md`** → bỏ vào `.claude/commands/` *(tùy chỉnh theo dự án)*
- Tạo **`frontend-agent.md`** → bỏ vào `.claude/agents/` *(tùy chỉnh theo dự án — tải các skill cần thiết bỏ vào `.claude/skills/`)*

📁 **2 file trên được lưu tại đây để tham khảo:**
- [`reference/read-figma.md`](./reference/read-figma.md)
- [`reference/frontend-agent.md`](./reference/frontend-agent.md)

> 💡 **Gợi ý sắp xếp thư mục:** Nên đặt repo code **cùng cấp** với nơi setup Claude ở trên, để agent có thể tham chiếu cross-repo (ví dụ `docs/` và `repository/` nằm chung một parent folder).

---

## Kết nối Figma MCP

### 1. Bật MCP server trong Figma Desktop
- Mở **Figma Desktop** → **Preferences** → bật **Enable local MCP server**
- Login + mở file design cần làm

### 2. Cấu hình Claude CLI (`~/.claude.json`)
```json
{
  "mcpServers": {
    "figma": {
      "url": "http://127.0.0.1:3845/mcp"
    }
  }
}
```
Restart Claude Code → gõ `/mcp` thấy `figma: connected` là OK.

### 3. Copy link node (trong Figma)
- Bật **Dev Mode** (icon `</>` góc phải)
- Click frame/component → **Right-click** → **Copy link to selection**

---

## Flow sử dụng (3 turn)

### Turn 1 — Đọc Figma
```bash
/read-figma <figma-url> <ComponentName> <feature>
```

**Ví dụ:**
```bash
/read-figma https://www.figma.com/design/abc/xyz?node-id=123-456 OrderCard order-management
```

**3 args bắt buộc:**

| Arg | Format | Ví dụ |
|---|---|---|
| `<figma-url>` | Link từ Dev Mode, có `?node-id=` | `https://.../?node-id=123-456` |
| `<ComponentName>` | PascalCase, sẽ là tên file `.tsx` | `OrderCard` |
| `<feature>` | kebab-case, tên feature folder | `order-management` |

Command sẽ ghi ra:
```
{path}/features/<feature>/figma/
├── figma_<ComponentName>_context.md   ← metadata + tokens map + notes
└── figma_<ComponentName>.png          ← screenshot
```

### Turn 2 — Generate code
Copy-paste hint Claude trả ra cuối Turn 1:
```
Hãy là FE AGENT, thực thi code giao diện tại path figma context mới tạo xong:
{path}/features/order-management/figma/figma_OrderCard_context.md
```
FE agent đọc file context → tự quyết định repo target → generate component theo đúng pattern dự án.

### Turn 3 — Verify
```bash
cd <repo>
npm run dev
```
So screenshot Figma vs render thực tế → done.

---

## 🖼️ Hỗ trợ Image & Icon

- Hỗ trợ export **image và icon** trực tiếp từ Figma.
- AI có đầy đủ asset để phân tích, giúp kết quả generate **sát với thiết kế hơn**.

📦 **npm:** <https://www.npmjs.com/package/figma-mcp-console>

---

## Troubleshooting nhanh

| Lỗi | Fix |
|---|---|
| Figma MCP chưa connect | Mở lại Figma Desktop, check Preferences còn bật MCP không, restart Claude Code |
| URL thiếu `node-id` | Copy lại link từ **Dev Mode** (không phải link share thường) |
| Feature folder chưa tồn tại | Claude sẽ hỏi confirm trước khi tạo — trả lời `yes` nếu là feature mới |
| `/read-figma` không nhận diện | Kiểm tra `.claude/commands/read-figma.md` đã tồn tại chưa; restart Claude Code |
