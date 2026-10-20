# Tabs

Tabs pair index-like labels (modelled on the tabs of a clear folder) with a panel, switching between several pieces of content inside one fixed area.

## When to use
- Parallel content of the same kind where only one view is needed at a time (news categories, fiscal years).
- Avoid when readers need to compare panels side by side, or for page-level navigation (use links).

## Variants
| Figma axis | Prop |
|---|---|
| Tab Type = Top / Bottom / Left / Right | `position` |
| Tab Type = Top Reflow / Bottom Reflow | `reflow` (labels wrap onto several rows) |
| Label Type = Default / Hover / Selected | CSS `:hover` (gray-50 body, gray-420 mark, underline); selected tab = bold label + key-1000 6px mark |
| Selected tab | `value` / `defaultValue` + `onChange` |

Horizontal labels are 57px tall (6px mark + 16px padding, Dns-16N-120); vertical labels 51px with the mark on the outer side. Labels and panel overlap by 1px so borders collapse, and the selected label opens into the panel.

## What the consumer provides
- `items` with `label`, `content`, optional `value` / `disabled`.
- `label` — an accessible name for the tab list.

## Accessibility notes
- WAI-ARIA tabs pattern: `role="tablist"`/`tab`/`tabpanel`, `aria-selected`, `aria-controls`, `aria-labelledby`, `aria-orientation` for vertical lists.
- Roving tabindex: Tab enters the selected tab, Arrow Left/Right (Up/Down when vertical) and Home/End move and select; Tab again moves into the focusable panel.
