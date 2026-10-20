# TableControl

A set of controls that sit above or below a data table to filter, size and act on the rows it shows.

## When to use
- Keyword search over a long data table, with the hit count and a reset.
- Letting people choose how many rows a page shows.
- Grouping table-level actions (印刷, CSVダウンロード, 新規追加) with a vertical divider between groups.

## Variants
| Figma component | Export |
| --- | --- |
| Table Control Search Box | `TableControlSearch` — 312×30 field (gray-600 frame, search icon), xs solid 検索 button, count text, xs text リセット button |
| Items per page | `TableControlItemsPerPage` — 表示件数 label, current value as plain text, others as link-styled buttons |
| Vertical Divider | `TableControlDivider` — 30px, solid-gray-536 |
| Table Controls row | `TableControl` (space-between, 24px gap) and `TableControlGroup` (16px gap) |

## What the consumer provides
- Search: `value`/`defaultValue`, `onSearch`, the formatted `count` (e.g. "25 件") and `onReset` to show the reset button.
- Items per page: `options`, `value`/`defaultValue`, `onChange`.
- Action buttons (`Button size="xs" variant="outlined"`) as children of a `TableControlGroup`.
- Page navigation is not part of this component; place your own pager in the bar.

## Accessibility notes
- The search box is a `form role="search"` with a visually hidden label; Enter submits.
- The count is a `role="status"` so new totals are announced.
- The current page size is marked `aria-current`; other sizes are buttons because they change state rather than navigate.
