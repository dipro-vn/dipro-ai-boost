# AI Workflow — Basic Design Numbering (Claude → Cursor → Figma)

Tài liệu này mô tả **workflow tổng thể** cho việc đánh số UI element trong Figma, tách rõ:

- **Dev time**: Cursor (IDE) hỗ trợ viết/sửa/debug plugin
- **Runtime**: User chạy plugin trong Figma để đánh số + (tùy chọn) sinh spec

> Ghi chú: Plugin trong repo **không gọi MCP**. MCP (nếu dùng) chỉ phục vụ **dev/debug trong Cursor**.

---

## 1) Tổng quan: 3 bên làm gì?

```mermaid
flowchart TB
  subgraph DEV["① GIAI ĐOẠN DEVELOP — Cursor (IDE)"]
    direction TB
    U1["Developer (bạn)"]
    CUR["Cursor AI\n(viết / sửa plugin)"]
    REPO["Repo local\ncode.js + ui.html"]
    MCP["Figma MCP\n(tùy chọn — đọc layer tree)"]
    FIGDEV["Figma Desktop\nImport plugin Development"]

    U1 -->|"Mô tả bug / yêu cầu"| CUR
    CUR -->|"Sửa code"| REPO
    CUR -.->|"Optional: inspect design"| MCP
    MCP -.->|"get_design_context / use_figma"| FIGDEV
    REPO -->|"Reload plugin"| FIGDEV
  end

  subgraph RUN["② GIAI ĐOẠN RUNTIME — User đánh số trên Figma"]
    direction TB
    U2["User / BrSE"]
    UI["Plugin UI\n(ui.html modal)"]
    CODE["Plugin sandbox\n(code.js)"]
    SCAN["collectElements()\nQuét layer Figma"]
    MATCH{"Khớp prompt\n→ element + số"}
    LOCAL["Local match\n(số: nhãn)"]
    CLAUDE["Claude API\n(Anthropic)"]
    POS["Tính tọa độ\nmarkerPosition"]
    DRAW["drawOverlay()\nVẽ badge đỏ"]
    SPEC["buildSpecResult()\nClaude viết spec BD"]
    CANVAS["Canvas Figma\n__overlay__ + số"]

    U2 -->|"1. Chọn Frame"| UI
    U2 -->|"2. Nhập prompt + API key"| UI
    UI -->|"postMessage"| CODE
    CODE --> SCAN
    SCAN -->|"≤300 candidates\nnodeId, text, path, box"| MATCH
    MATCH -->|"Mode: prompt\n11.1: label"| LOCAL
    MATCH -->|"Mode: prompt\ntự do"| CLAUDE
    MATCH -->|"Mode: auto\nenrich+prefilter"| AUTOPIPE
    AUTOPIPE["enrichCandidates\npreFilter\nautoSelectElementsWithAI"]
    AUTOPIPE --> POS
    LOCAL --> POS
    CLAUDE -->|"JSON nodeId + number"| POS
    POS -->|"Preview"| UI
    U2 -->|"3. Confirm vẽ"| UI
    UI --> DRAW
    DRAW --> CANVAS
    DRAW --> SPEC
    SPEC --> CLAUDE
    SPEC --> UI
    EXPORT["exportExcel() / exportCsv()\nUI: HTML .xls + PNG"]
    PNG["exportFrameWithMarkersPng()\ncode.js"]
    SPEC --> PNG
    PNG --> EXPORT
    SPEC --> EXPORT
  end

  DEV -.->|"Plugin đã build"| RUN
```

---

## 2) Luồng chi tiết khi user bấm chạy (Runtime)

**Mục tiêu phần này**: giải thích rõ **Claude tham gia ở đâu**, **Figma xử lý gì**, và **Cursor không nằm trong runtime**.

```mermaid
sequenceDiagram
  autonumber
  actor User as User / BrSE
  participant UI as Plugin UI<br/>(ui.html)
  participant JS as code.js<br/>(Figma sandbox)
  participant FG as Figma Plugin API<br/>(document / layers)
  participant AI as Claude API<br/>(Anthropic)

  User->>FG: Chọn Frame trên canvas
  User->>UI: Nhập prompt + API key
  User->>UI: Bấm 「Phân tích & xem trước」

  UI->>JS: run-preview { frameId, userPrompt, apiKey }

  JS->>FG: collectElements(frame)
  FG-->>JS: candidates (TEXT, icon, path, x/y)

  alt Prompt dạng "11.1: ラベル" (local đủ)
    JS->>JS: localResolveElementsFromPrompt()
    Note over JS: Không gọi Claude
  else Mô tả tự do / phức tạp
    JS->>AI: selectElementsWithAI()<br/>system + prompt + candidate list
    AI-->>JS: JSON { nodeId, number, label }
  end

  JS->>FG: resolveElementsForDraw()<br/>bbox, marker anchor
  Note over JS,FG: Vị trí số = 100% Figma geometry<br/>AI KHÔNG quyết định x,y

  JS->>UI: preview-ready (bảng Số · Text · Path · x,y)
  User->>UI: Kiểm tra preview → Confirm

  UI->>JS: run-confirm { elements }

  JS->>FG: drawOverlay()<br/>__overlay__ + ellipse đỏ + số
  FG-->>User: Số hiện trên canvas

  User->>UI: Bấm 「Tạo spec bằng AI」
  UI->>JS: generate-spec { numberedItems }
  JS->>JS: buildSpecAiPayload()<br/>nearbyTexts + context
  alt Có API key
    JS->>AI: generateBasicDesignSpecs()
    AI-->>JS: JSON specs[]
    JS->>JS: mergeSpecsWithItems()<br/>fallback nếu thiếu
  else Không API / lỗi
    JS->>JS: buildFallbackSpec() local
  end
  JS->>UI: generate-spec-result
  User->>UI: Sửa modal → Download CSV
```

---

## 3) Cursor nằm ở đâu trong workflow?

```mermaid
flowchart LR
  subgraph RUNTIME["Runtime — User đánh số"]
    F1[Figma] --> P[Plugin]
    P --> C1[Claude API]
    C1 --> P
    P --> F1
  end

  subgraph DEVTIME["Dev time — Làm & debug plugin"]
    CR[Cursor AI] --> R[code.js / ui.html]
    R --> F2[Figma Development]
    CR -.->|Optional| MCP[Figma MCP]
    MCP -.-> F2
  end

  RUNTIME ~~~ DEVTIME

  style RUNTIME fill:#fef3f2,stroke:#E8243C
  style DEVTIME fill:#ebf1fb,stroke:#0C4EAA
```

**Kết luận**:

- Cursor xuất hiện ở **dev time** (viết/sửa/debug code).
- Claude xuất hiện ở **runtime** để **phân tích prompt** (và tùy chọn viết spec).
- Figma đảm nhiệm phần **deterministic**: layer tree, bbox, tọa độ, vẽ overlay.

---

## 4) Phân chia trách nhiệm AI vs không-AI

```mermaid
flowchart TB
  PROMPT["Prompt user\n(từ modal UI)"]

  PROMPT --> AI_BLOCK

  subgraph AI_BLOCK["🤖 Claude (AI)"]
    A1["Đọc mô tả tự do\n(VI / JA / EN)"]
    A2["Chọn nodeId đúng\ntrong danh sách candidate"]
    A3["Gán số thứ tự\ntheo yêu cầu user"]
    A4["Viết spec BD draft\n(bước confirm)"]
  end

  subgraph NOAI["⚙️ Figma + code.js (deterministic)"]
    N1["Quét layer tree\ncollectElements()"]
    N2["Tính path, box, center"]
    N3["Đặt anchor số\n(trái label / trong button / góc icon)"]
    N4["Vẽ overlay\nbadge đỏ trên canvas"]
  end

  AI_BLOCK --> N3
  N1 --> N2
  N2 --> AI_BLOCK
  N3 --> N4
```

---

## 5) One-liner cho slide

> **Cursor** giúp phát triển & debug plugin (MCP là optional để nhìn Figma từ IDE).  
> **Claude** giúp hiểu prompt user để quyết định *item nào mang số nào* và chọn đúng element.  
> **Figma** đảm bảo tọa độ và vẽ số lên canvas một cách deterministic.

