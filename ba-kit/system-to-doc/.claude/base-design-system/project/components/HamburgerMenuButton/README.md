# HamburgerMenuButton

A clearly labelled button that opens (and closes) the mobile menu, mainly on small screens where space is limited.

## When to use
- In the header on mobile (or narrow desktop) to open a `Drawer` containing a `MobileMenu`.
- Swap `type` to `close` while the menu is open, or use the close variant inside the drawer header.
- Always keep the visible label; an unlabelled hamburger is hard to discover.

## Variants
| Figma | Prop |
| --- | --- |
| Desktop & Mobile Button | `variant="text"` (default): 24px icon + Oln-16N-100 label, 36px tall, radius 6 |
| Icon Button | `variant="icon"`: 44×44, radius 4, glyph with a small caption underneath |
| Type = Menu / Close | `type="menu"` / `type="close"` |
| Lang = JA / EN | `lang="ja"` / `lang="en"` (default labels; override with children) |

Hover: `solid-gray-50` fill, underlined label (text) or 1px black border (icon). Focus: yellow fill + system focus ring.

## What the consumer provides
- `onClick` that toggles the menu, plus `aria-expanded` and `aria-controls` pointing at the drawer/menu.
- Optional custom label as children.

## Accessibility notes
- Renders a native `<button type="button">`; the visible label is the accessible name, so no extra `aria-label` is needed.
- Reflect the open state with `aria-expanded`; return focus to this button when the drawer closes (`Drawer` does this).
