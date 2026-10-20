# MobileMenu

A menu built for tapping on touch screens, used together with the hamburger menu button and a drawer — often the only way to reach some pages on mobile, so it matters a lot.

## When to use
- Inside a `Drawer` opened by `HamburgerMenuButton` on small screens.
- Mirror the site structure of the desktop `HorizontalMenu`/`MegaMenu`, including pages that are otherwise only linked from there.

## Variants
| Figma | Prop |
| --- | --- |
| Moble Menu List State = Default / Selected | `MobileMenuItem current` (key-100 fill, aria-current) |
| Indent = True | `indent` (32px inset); items passed via `items` are indented automatically |
| End-icon + Caret Direction = Right | `drilldown` (link to a deeper level) |
| Caret Direction = Down / Up | `items` (accordion; down when closed, up when open), `open`/`defaultOpen`/`onOpenChange` |
| Show Front-icon / Show Tail-icon | `icon` / `external` |
| Mobile Menu Section Title, Style Default / Section Bar | `MobileMenuSection title` with optional `icon`, or `chip="gray"`/`"key"` (Color Chip) |
| Section Title caret Right / Down / Up | `href` / `collapsible` |
| Solid divider | `MobileMenuDivider` |
| Back Button | `MobileMenuBackButton` |

Rows are 44px tall with 16px content padding, 8px right inset and a 36×36 end-icon area.

## What the consumer provides
- The menu tree as `MobileMenuItem`/`MobileMenuSection` children, with `current` on the page being viewed.
- For multi-level drill-down, the level switching and a `MobileMenuBackButton` above the menu.

## Accessibility notes
- Renders `<nav aria-label>` with nested lists; section titles are headings (`headingLevel`, default h2).
- Accordion rows are `<button aria-expanded aria-controls>`; collapsed lists use `hidden`.
- Hover underlines the label; keyboard focus uses the system yellow/black focus ring.
