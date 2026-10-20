# MegaMenu

A wide dropdown opened from a horizontal menu item that can hold more than a plain link list — a title block, link columns and image banners — with a lot of freedom in how the width is used.

## When to use
- For a top-level category in `HorizontalMenu` whose sub pages benefit from grouping, descriptions or visual banners.
- Pass it as the item's `panel`; show `MegaMenuOverlay` behind it while open to dim the page.
- For a short list of links, a simple dropdown list is enough.

## Variants
| Figma | Prop |
| --- | --- |
| Mega Menu / Title | `title`, `description`, `titleLink` (2nd-layer link) |
| Mega Menu / Item Type = Menu | column `{ type: 'menu', items }` |
| Type = Large Banner | column `{ type: 'large-banner', banners: [one] }` (220px image) |
| Type = Banner | column `{ type: 'banner', banners: [two] }` (84px images, 8px apart) |
| Type = Banner and Menu | column `{ type: 'banner-menu', banners: [one], items }` |
| Banner State Hover / Focus | CSS: gray-50 fill + 2px key-900 ring; focus = system ring |
| Text Close Button | rendered when `onClose` is given |
| Overlay Shade | `MegaMenuOverlay` (fixed, `opacity-gray-600`) |

Panel: 32/80/40/80 padding, 40px gaps, 1px black border, elevation 3. Below 1200px the title block moves onto its own row and side padding drops to 32px.

## What the consumer provides
- Title texts, column data and banner images (URL or inline node; images are decorative, the caption is the link text).
- `onClose` to hide the panel (also wired to Escape), and the open/close state in the parent `HorizontalMenu`.

## Accessibility notes
- The panel is a `role="region"` labelled by its heading (`headingLevel`, default h2); links are real `<a>` elements in lists.
- External links get a "新しいタブで開きます" icon label. Return focus to the opening menu item when closing (HorizontalMenu does this on Escape).
