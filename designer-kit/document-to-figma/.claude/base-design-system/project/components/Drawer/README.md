# Drawer

A modal panel that slides a separate block of information in from off-screen, covering the page from the right, from the left or full-screen.

## When to use
- To hold the `MobileMenu` opened by `HamburgerMenuButton` on small screens.
- For secondary content that must be dealt with before returning to the page. It is always modal; for non-blocking content use an inline region instead.

## Variants
| Figma | Prop |
| --- | --- |
| Right / Left / Full overlay | `side="right"` (default) / `"left"` / `"full"` |
| Header bar with Text Close Button (閉じる) | always rendered; `closeLabel` to change the text |
| Content area (16/24 padding) | `children` |

The panel is 390px wide (full width on narrow screens), the header bar is 68px with 16px side padding, and the backdrop uses `opacity-gray-600`.

## What the consumer provides
- `open` + `onOpenChange` (or `defaultOpen` for uncontrolled use) and the trigger button with `aria-expanded`/`aria-controls`.
- Content, typically a `MobileMenu`; an optional `title` or `aria-label` to name the dialog.

## Accessibility notes
- Uses native `<dialog>` with `showModal()`: the page behind is inert, focus moves to the close button (or an element marked `data-autofocus`) and stays inside.
- Escape and a click on the backdrop close it; focus then returns to the element that opened it.
- Respects `prefers-reduced-motion` for the slide-in animation.
