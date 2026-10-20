# Table

A data table that lays out records in rows and columns so people can scan, compare and act on them; the dense size suits system screens with lots of data.

## When to use
- Structured data with the same attributes per record (申請一覧, 手数料一覧).
- Use `size="dense"` on admin / back-office screens; keep `default` for public pages.
- Pair with `TableControl` for search, page size and bulk actions.

## Variants
| Figma axis | Prop |
| --- | --- |
| Size = Default / Dense | `size="default"` (cells 20/16 padding, Std-16N-170) · `"dense"` (12/16, Dns-16N-130) |
| Border = Bottom & Right / Bottom / None | `border="grid"` (default) · `"horizontal"` · `"none"` |
| State = Stripe | `striped` (gray-50 on even rows) |
| State = Hover | `hoverable` (key-50 on the hovered row) |
| State = Selected | `selectedKeys` (key-100 + `aria-selected`) |
| Header Cell Sort State = NA / Default / Hover | `columns[].sortable`; hover thickens the underline |
| Sort Icons = Default / Ascending / Descending | follows the current `sort` / `defaultSort` |
| Cell with Link, Link Area = Data / Cell | `columns[].href(row)` + `linkArea="data"` (default) or `"cell"` |
| Front-icon | `columns[].icon` (header), `columns[].cellIcon` (body) |

Header cells are gray-100 with a black bottom rule and gray-500 dividers; body rules are gray-420, or gray-500 when stripe, hover or selection is used. The table has a gray-420 outer frame.

## What the consumer provides
- `columns` (key, label, optional render / sortable / href / rowHeader / align) and `rows` (objects with a unique `id` or a `rowKey`).
- Sorting is built in for uncontrolled use; pass `sort` + `onSortChange` (and `manualSort`) to sort on the server.
- A `caption` or `aria-label` naming the table.

## Accessibility notes
- Sortable headers are `<button>`s inside `<th aria-sort>`, so the state is announced.
- `rowHeader` columns render `<th scope="row">`.
- Cell links get the system focus ring; a whole-cell link turns yellow-300 with a 4px black inner frame on focus.
- Wide tables scroll horizontally inside their wrapper instead of breaking the page.
