# SearchBox

A site-search field with an optional scope selector, a search button, an advanced-search panel and one-tap keyword shortcuts.

## When to use
- Site-wide or section search (サイト内検索) at the top of a page or in a header.
- Add `scopes` when results can be narrowed to a content type (法令, ファイル, 地図…) before searching.
- Add `filters` for detailed criteria that most people will not need; it stays collapsed behind 詳細検索.
- Add `shortcuts` for frequent queries (マイナンバー, 確定申告).

## Variants
| Figma | Prop |
| --- | --- |
| Size = Large / Medium / Small | `size="lg" \| "md" \| "sm"` (57 / 48 / 40px) |
| Scope (bool) | `scopes` non-empty; Small shows the value only, Large/Medium also show the 検索対象 caption |
| Search Box button (Solid Fill) | `buttonVariant="solid"` (default) |
| Search Button | `buttonVariant="text"` (icon + 検索) |
| Search Button (compact) | `buttonVariant="icon"` (44px) |
| Search Filters Opened / Closed | `filters` + `defaultFiltersOpen` (native `<details>`) |
| Search Shortcuts | `shortcuts` |

## What the consumer provides
- `onSearch(query, scope)` to run the search; the component never navigates on its own.
- The filter form controls inside `filters` and their own submit/clear buttons.
- Placeholder copy and the scope list.

## Accessibility notes
- Wrapped in `<form role="search">`; Enter submits.
- The scope is a native `<select>` laid transparently over the styled caption, so keyboard and screen-reader behaviour are native.
- The icon-only button carries `aria-label` (default 検索). Focus draws the system focus ring (black 4px outline + yellow-300 band) on the field, scope and buttons.
