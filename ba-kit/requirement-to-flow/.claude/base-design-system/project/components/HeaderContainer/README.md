# HeaderContainer

The site header shell that holds the various components placed in a header, organised into separate areas because it can contain many of them.

## When to use
- At the top of every page of a site or service, as the `<header>` landmark.
- Use `slim` when the logo, a short menu and a few utilities fit on one row; use `full` when the horizontal menu needs the whole width.

## Variants
| Figma | Prop |
| --- | --- |
| Wide: Slim | `layout="slim"` (default): one row, 32px padding, 20px gaps, 56px areas |
| Wide: Full | `layout="full"`: logo + utility (64px) on top, menu on its own row below |
| Area 1 ロゴ | `title` (+ `titleHref`) text slot, or `logo` for a real logo |
| Area 2 ヘッダーコンテナアイテム | `utility` |
| Area 3 水平メニュー | `nav` |

Below 768px the padding drops to 16px and the bar is at least 68px tall.

## What the consumer provides
- The site name (or logo node with proper alt text) and the link to the top page.
- Utility items (links, language selector, search, `HamburgerMenuButton`) and the `HorizontalMenu`; hide the menu and show the hamburger on small screens.

## Accessibility notes
- Renders a `<header>` landmark; put only one per page at the top level.
- The nav slot is a plain container — `HorizontalMenu` provides its own `<nav aria-label>`.
