# HorizontalMenu

A horizontal row of top-level menu items, shown consistently across a site or app, that leads people to the page they want and helps them move around.

## When to use
- As the global navigation in the header (`HeaderContainer` nav slot) on desktop widths.
- For categories that open a dropdown or `MegaMenu`, give the item a `panel`; plain destinations get an `href`.
- On narrow screens switch to `HamburgerMenuButton` + `Drawer` + `MobileMenu`.

## Variants
| Figma | Prop |
| --- | --- |
| State = Default / Selected | `current` on an item (key-1000 text, 4px key-900 underline) |
| State = … : Hover / … : Focus | CSS `:hover` (gray-50 fill, 2px black underline) and `:focus-visible` (yellow fill, radius 8, system ring) |
| Caret = None / Down / Up | none for links; Down when an expandable item is closed, Up when open |
| Show Front-icon | `icon` on an item (24px) |

Items are 64px tall, 20px side padding, 4px gap, Dns-16B-130 labels; the bar has a 1px `solid-gray-420` bottom rule.

## What the consumer provides
- `items` with labels and either `href` or `panel`/`expandable`.
- Optionally controlled `expandedIndex` + `onExpandedChange` (e.g. to show an overlay shade while a mega menu is open).

## Accessibility notes
- Renders `<nav aria-label>` with a list; the current page link gets `aria-current="page"`.
- Expandable items are `<button aria-expanded aria-controls>`; Escape closes the open panel and returns focus to its button; clicking outside closes it.
