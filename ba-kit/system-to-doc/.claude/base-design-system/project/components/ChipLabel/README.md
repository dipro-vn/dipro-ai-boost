# ChipLabel

A small keyword chip that shows a status or category, making lists and table rows easier to scan and sort.

## When to use
- Status columns in tables and lists (開始前 / 作業中 / 完了 / 中止).
- Category tags in front of titles or sentences (新着, 可燃ごみ).
- Not interactive — for removable items use `ChipTag`; for actions use `Button`.

## Variants
| Figma axis | Prop | Values |
|---|---|---|
| Style | `variant` | `text-only`, `outlined` (default, white fill), `filled-1` (50-step tint + border), `filled-2` (solid fill, white text) |
| Color | `color` | `gray` (default), `blue`, `light-blue`, `cyan`, `green`, `lime`, `yellow`, `orange`, `red`, `magenta`, `purple` |
| Front Icon / Icon | `icon` | any icon name, 24px |
| (example override) | `shape` | `rounded` (radius 8, default), `pill` |

Ink per hue: blue-700, light-blue-800, cyan-900, green-800, lime-900, yellow-1000, orange-900, red-900, magenta-800, purple-800; gray uses solid-gray-700 border/fill with solid-gray-800 text. Height 32px, padding 4/8, gap 4, Oln-16N-100.

## What the consumer provides
- A one- or two-word label as children.
- Optional decorative `icon` that reinforces (not replaces) the label.

## Accessibility notes
- Renders a `<span>`; the label text carries the meaning, so never rely on color alone — keep the wording explicit.
- Icons are `aria-hidden`.
