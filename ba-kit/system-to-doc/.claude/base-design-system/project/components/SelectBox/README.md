# SelectBox

A native drop-down for picking one option from a list, styled to the system with label, support text and error text.

## When to use
- Choosing one value from a known, moderately long list (都道府県, 連絡方法). For 2–5 options prefer radio buttons so all choices are visible.
- Date parts (年/月/日) can be built from three SelectBoxes with `selectWidth`; use `DatePicker` when free typing is acceptable.

## Variants
| Figma | Prop |
| --- | --- |
| Size = Large / Medium / Small | `size="lg"` (56px) / `"md"` (48px) / `"sm"` (40px, radius-4) |
| State = Error | `error` or `errorText` (red border, Error Text in Dns-16N-130) |
| State = Disabled | `disabled` |
| hover / focus | CSS: black border on hover; system focus ring on focus |
| Select Box Units · Show Label | `label` present or omitted |

Text is Std-16N-170 in solid-gray-800 with a 16px `arrow_down_300` icon 16px from the right edge.

## What the consumer provides
- `options` (strings, `{value,label}` or `{label, options}` groups) or `<option>` children.
- `placeholder` (default "選択してください"; `null` to omit). With `required` the placeholder can't be re-selected.
- Native select props (`name`, `value`/`onChange`, `defaultValue`) go to the `<select>`; `className`/`style` go to the wrapper.

## Accessibility notes
- Uses a real `<select>` so the platform picker, type-ahead and screen-reader support are preserved.
- Label via `<label for>`; support/error text via `aria-describedby`; errors set `aria-invalid`, `required` sets `aria-required`.
