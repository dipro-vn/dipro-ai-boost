# Checkbox

Checkboxes let a person pick any number of options from a list, or turn a single option on or off.

## When to use
- Several independent choices where zero, one or many may apply (受け取り方法, 利用する手続き).
- A single agreement or opt-in (同意する) that is confirmed by a submit button.
- For exactly-one choices use `Radio`; for settings applied immediately use `Switch`.

## Variants
- Checkbox Units `Size` → `size`: `sm` (24px control, 4px gap, 40px row), `md` (32px, 8px gap, 48px row), `lg` (44px, 12px gap, 60px row, Dns-17 text).
- `State` → real state: `checked`/`defaultChecked`, `indeterminate`, `disabled`; hover (solid-gray-420 halo), focus (system ring) are CSS. `Error` variants → `error`.
- Stacked / Inline sets → `CheckboxGroup` with `layout="stacked" | "inline"`, `size`, `label` (Show Label), `error` text (Show Error Text).

## What the consumer provides
- Selection text as children; `name`/`value` and other input props go to the `<input>`.
- For groups: `label`, optional `requirement` (`required`, `optional`…) and `supportText`, and an `error` message string when validation fails.

## Accessibility notes
- A native `<input type="checkbox">` inside a `<label>`, so the whole row (text included) is the click target.
- `indeterminate` sets the native property, announced as "mixed".
- `CheckboxGroup` is a `<fieldset>` whose `<legend>` is the label; support and error text are linked with `aria-describedby`, and children get `aria-invalid` in the error state.
- Disabled colours fail contrast by design; explain why an option is unavailable.
