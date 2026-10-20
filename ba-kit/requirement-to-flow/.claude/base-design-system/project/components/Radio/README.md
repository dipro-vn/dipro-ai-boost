# Radio

Radio buttons let a person choose exactly one option from a small set.

## When to use
- Mutually exclusive choices with 2–6 visible options (申請者区分, 連絡を希望する時間帯).
- Use `Checkbox` when several can apply and a select menu when the list is long.

## Variants
- Radio Button Units `Size` → `size`: `sm` (24px control, 4px gap), `md` (32px, 8px gap), `lg` (44px, 12px gap, Dns-17 text).
- `State` → real state: `checked` (via `RadioGroup`), `disabled`; hover (solid-gray-420 halo) and focus (system ring) are CSS. `Error` variants → `error`.
- Stacked / Inline sets → `RadioGroup` with `layout="stacked" | "inline"`, `size`, `label`, `error` text.

## What the consumer provides
- `Radio` children with a `value` and the selection text.
- On `RadioGroup`: `label`, optional `requirement` and `supportText`, `value`/`defaultValue` + `onChange(value)`, and an `error` message when validation fails. `name` is generated if omitted.

## Accessibility notes
- Native `<input type="radio">` elements sharing a name, so arrow keys move the selection.
- `RadioGroup` is a `<fieldset>` with the label as `<legend>`; support and error text are linked with `aria-describedby`; options get `aria-invalid` in the error state.
- Prefer pre-selecting nothing unless a safe default exists.
