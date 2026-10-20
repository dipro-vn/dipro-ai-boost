# CloseButton

Close buttons dismiss a dialog, drawer or panel, and Action Icons are compact icon-only buttons for in-place actions.

## When to use
- `CloseButton variant="icon"` in tight headers (drawers, mobile menus) where a 44px square fits best; the caption keeps the purpose readable.
- `CloseButton variant="text"` in dialog title areas (it is the close button used by `ModalDialog`).
- `ActionIconButton` for repeated row/card actions (edit, delete, more) where a visible text label would be noisy.

## Variants
| Figma | Prop |
|---|---|
| Icon Close Button, Language=JA / EN | `<CloseButton variant="icon" lang="ja" \| "en">` |
| Text Close Button | `<CloseButton variant="text">` |
| Action Icons, Size=24 / 40 / 44 | `<ActionIconButton size={24 \| 40 \| 44}>` |
| State=Hover / Focus | CSS `:hover` / `:focus-visible` |

## What the consumer provides
- `onClick` to close the surface.
- Optional `children` to override the caption (default 閉じる / Close).
- For `ActionIconButton`: an `icon` name and a required `label`.

## Accessibility notes
- Close buttons carry visible text, so they need no extra `aria-label`.
- `ActionIconButton` sets `aria-label` and `title` from `label`; the glyph is hidden from assistive tech.
- Hover adds a gray fill and a black outline; keyboard focus draws the system focus ring on a yellow-300 fill.
