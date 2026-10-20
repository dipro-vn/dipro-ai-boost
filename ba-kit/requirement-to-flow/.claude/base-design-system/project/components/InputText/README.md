# InputText

A single-line text field for short answers such as a name or phone number, with its own label, support text and error text.

## When to use
- Short, one-line free input (氏名, 電話番号, メールアドレス, 郵便番号). Use `TextArea` for longer free text.
- Split fields (e.g. postal code 3 + 4 digits) by placing two InputTexts side by side; set `inputWidth` to size each field to its expected length.

## Variants
| Figma | Prop |
| --- | --- |
| Size = Large / Medium / Small | `size="lg"` (56px) / `"md"` (48px) / `"sm"` (40px, radius-4) |
| State = Error | `error` or `errorText` (red border, Error Text below in Dns-16N-130) |
| State = Readonly | `readOnly` (dashed border) |
| State = Default Disabled | `disabled` (solid-gray-50 fill, solid-gray-300 border) |
| hover / focus | CSS: black border on hover; system focus ring on focus |
| Input Text Units · Show Label | `label` present or omitted; label style Std-17B-170 (lg, md) / Std-16B-170 (sm) |

## What the consumer provides
- `label`, optional `supportText`, and `required` (※必須) or `optional` (※任意).
- `errorText` worded as a fix (＊…を入力してください。).
- Any native input props (`name`, `type`, `inputMode`, `autoComplete`, `value`/`onChange`) — they go to the `<input>`; `className`/`style` go to the wrapper.

## Accessibility notes
- The label is a real `<label for>`; support and error text are linked via `aria-describedby`; errors set `aria-invalid`.
- `required` sets `aria-required` only — validate and show `errorText` yourself.
- Don't rely on placeholders as labels. Without `label`, pass `aria-label`.
