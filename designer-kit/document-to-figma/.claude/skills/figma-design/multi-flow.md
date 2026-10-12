# Multi-flow Figma Structure — Designer output

> **Scope:** Chi tiết structure Figma khi feature có N > 1 business flows.
> **Dùng ở:** `designer-agent.md` (Bước 1.5 — Flow Detection). Agent body chỉ giữ tóm tắt Single vs Multi rule + reference file này khi cần copy rule chi tiết.
> **Nguyên tắc:** N flows trong SPEC ↔ N group frames trong Figma output — 1:1 mapping, thứ tự khớp nhau.

---

## Detection

Sau khi đọc `## BA Deliverables` + `## Flow Tổng Quan` trong SPEC.md, count **N = số business flows**.

| Case | Detection | Figma output structure |
|---|---|---|
| **Single-flow (N = 1)** | SPEC `## Flow Tổng Quan` chỉ có 1 flow | 1 Figma page với tất cả high-fi screens (frames stacked hoặc grid) |
| **Multi-flow (N > 1)** | SPEC có N flows (VD sample-multi-flow-feature: 5 flows) | Figma output CHIA THEO GROUP FLOW (tương tự BA Output 3 v2): N group frames, mỗi group chứa hi-fi screens thuộc flow đó |

---

## Multi-flow rule (khi N > 1)

- **Naming:** Group frame đặt tên `Flow <N> — <Tên business flow>` (ví dụ `Flow 1 — Application`, `Flow 2 — Scout`)
- **Thứ tự groups** trong Figma page **PHẢI khớp** thứ tự flows trong SPEC `## Flow Tổng Quan`
- **Header per group:** label header màu actor + tất cả hi-fi screens thuộc flow đó
- **Gap giữa 2 groups:** MIN 200px (để visual distinguish)
- **Screen dùng cross-flow** (VD Login screen) → vẽ hi-fi 1 lần ở group đầu tiên, các group sau ghi Screen Code + reference
- **Cross-verification:** N groups Designer output = N groups BA Output 2/3

---

## Ví dụ multi-flow Figma output cho sample-multi-flow-feature (5 flows)

```
Page: Design HiFi — sample-multi-flow-feature

┌─── Group Frame 1 — Flow 1 Application (BLUE) ────┐
│  Hi-fi screens: A1_AUTH_001, A1_MOD_001..004,    │
│                 A2_AUTH_001, A2_MOD_001..004     │
└──────────────────────────────────────────────────┘
                    gap 200px
┌─── Group Frame 2 — Flow 2 Scout (GREEN) ─────────┐
│  Hi-fi screens: AX_MDX_001..007, A1_MDX_001..002 │
└──────────────────────────────────────────────────┘
                    gap 200px
┌─── Group Frame 3 — Flow 3 Contract (PURPLE) ─────┐
│  ...                                              │
└──────────────────────────────────────────────────┘
```

**Screens phân bổ per flow** — đọc BA Figma Output 3 v2 (đã group sẵn) làm reference; Designer chỉ upgrade low-fi → hi-fi trong cùng group structure.
