# ResourceList

A resource list shows a set of objects that share the same structure — e.g. records, statements or applications — so their status can be scanned in one list.

## When to use
- Lists of similar records (受診記録, 給与明細, 申請履歴) where each row has a title plus a few attributes and maybe an action.
- Add a checkbox control to pick several rows for a bulk action, or radio controls to choose exactly one.
- Use a table instead when people need to compare many columns.

## Variants
| Figma | Prop |
|---|---|
| List Style / Frame Style | `ResourceList variant="list"` / `"frame"` |
| … with Form Controls, Control Type Checkbox / Radio Button | `control="checkbox"` / `"radio"` (+ `name`) |
| Interaction Inline / Whole | `interaction="inline"` / `"whole"` |
| State Link | item `href` (title is a link) |
| State Selected / Selected: hover | item `checked` / `defaultChecked` (CSS `:has(:checked)`) |
| State Disabled / Disabled: Selected | item `disabled` (whole rows grey out entirely) |
| State Hover / Focus | CSS `:hover`, `:focus-visible` |
| Show Label / Sublabel / Support Text / Front Icon / Function Button | item `label` / `sublabel` / `supportText` / `icon` / `action` |

## What the consumer provides
`ResourceListItem` children with a `title` and any of `label`, `supportText`, `sublabel`, `icon`; an `href`/`onClick` for navigation; an `action` (label + handler) for a per-row menu; checked state for form controls.

## Accessibility notes
- The list is a `<ul>`; each row an `<li>`. Inline: the title is the link and the control is labelled by the title. Whole: the contents area is a single `<a>`, `<button>` or `<label>` so the whole row is one target.
- The action button is icon-only — always give `action.label`.
- Selected rows use `key-50` fill plus a darker border, not color alone (the control shows the checked state).
- Focus uses the system yellow + black ring around the focused link, control or row.
