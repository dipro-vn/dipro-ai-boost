# Combobox

A form control for choices the standard controls handle poorly: a select-style picker with a filterable list box (single or multiple), or a text input that suggests matching entries as you type.

## When to use
- `mode="select"` (Combobox Select) when the answer must be one of a long list — municipalities, offices, staff — and people benefit from filtering, optgroups or picking several (`multiple`).
- `mode="input"` (Combobox Input) when free text is allowed but common answers should be suggested (names, addresses).
- Prefer a plain select or radio buttons for short lists (under about 7 items).

## Variants
| Figma | Prop |
| --- | --- |
| Combobox Select / Combobox Input | `mode="select" \| "input"` |
| Size = Large / Medium / Small | `size="lg" \| "md" \| "sm"` |
| State = Default / Open | closed / open (click, ArrowDown; `defaultOpen`) |
| List Item Select Multiple (checkbox) + Chip Label in slot + Control | `multiple` |
| Select Slot Overflow ("…" chip) | `maxChips` |
| Optgroup + Indent | option `group` |
| List Item Disabled / Optgroup Disabled | option `disabled` |
| Select Slot State = Error / Disabled | `error`, `disabled` |
| List Box State = Loading / No Results | `loading`, empty filter result |
| Narrowed-Down Range | automatic highlight of the filter match |

Hover, Focus (active option: yellow-300 with black inset), Selected (key-100, bold) and Selected Focus are behaviour, not props.

## What the consumer provides
- `options` (strings or `{value,label,group,disabled}`) and `label`.
- `onChange` for the value; `onInputChange` + `loading` for server-side suggestions.
- `name` to submit with a normal form.

## Accessibility notes
- Select mode: the slot is a `<button aria-haspopup="listbox" aria-expanded>`. Opening moves focus to the filter field, which is the `role="combobox"` controlling the `role="listbox"` via `aria-activedescendant`.
- Keys: ArrowDown/ArrowUp open and move, Home/End jump, Enter selects (single closes and returns focus to the slot; multiple toggles), Escape closes, Tab closes and moves on. In input mode Escape on a closed list clears the text.
- Options use `aria-selected`; multiple lists set `aria-multiselectable`. Optgroups are `role="group"` labelled by their heading. Loading and no-results messages are `role="status"`.
