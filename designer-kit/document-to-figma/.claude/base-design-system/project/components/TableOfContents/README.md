# TableOfContents

A table of contents gathers the headings of a long page into a linked list placed at the top of the page; it can be layered like a bulleted list.

## When to use
- Long articles or guidance pages with several sections that readers may want to jump between.
- Not for site navigation across pages — use global or local navigation for that.

## Variants
| Figma axis | Prop |
|---|---|
| Type = Borderless | `type="borderless"` (default, no padding) |
| Type = Border Dotted | `type="border-dotted"` (1px dotted solid-gray-420, padding 12/24/24/20) |
| Type = Border Solid | `type="border-solid"` |
| List with List Marks Indent 0 / 32 | top-level items / `children` |
| Headings Size=16 | `{ heading }` entries that start a group |

Rows use 8px vertical padding, a 24px marker box with a 6px disc, and Std-16N-170 links.

## What the consumer provides
- `items` in page order with `label` + `href` to in-page anchors; optional `children` (one level) and `{ heading }` group labels.
- Optional `title` (default このページの目次) and `current` for the section in view.

## Accessibility notes
- Rendered as `<nav>` labelled by its title, with real `<ul>`/`<li>` lists so screen readers announce item counts and nesting.
- Links use the system link colors and focus ring; `current` sets `aria-current="location"`.
