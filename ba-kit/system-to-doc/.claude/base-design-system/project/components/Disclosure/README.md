# Disclosure

A disclosure folds supplementary information beneath the main content and reveals it on demand.

## When to use
- Optional detail that supports a statement (address lists, release notes, eligibility fine print).
- To fold whole parallel sections, use `Accordion` instead.

## Variants
| Figma axis | Prop |
|---|---|
| Expand = False / True | `open` / `defaultOpen` + `onOpenChange` |
| Stete (State) = Default / Hover | CSS `:hover` (label underline, tinted control) |
| Disclosure Controls Down / Up | arrow_drop_down_circle icon rotates with the expanded state |
| Return (Default / Hover) | `returnLink` (+ `returnLabel`); hover uses link hover color |

Summary row: 24px control, 8px gap, Std-16N-170 label, 24px bottom padding. Content is indented 32px left and right with 16px gaps.

## What the consumer provides
- `summary` text and the content as children.
- `returnLink` for long content so readers can jump back to the summary.

## Accessibility notes
- Uses native `<details>`/`<summary>`, so the toggle is announced as expandable and content stays searchable by the browser.
- Keyboard: Tab to the summary, Enter/Space toggles; focus shows the system focus ring.
