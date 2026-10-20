# TextArea

A multi-line field for free-form answers, with label, support text, an optional letter counter and error text.

## When to use
- Open comments, inquiries or descriptions (ご意見・ご要望, 問題の詳細). Use `InputText` for one-line answers.
- Add `maxCount` whenever there is a length limit and state it in `supportText` (e.g. "100文字以内").

## Variants
| Figma | Prop |
| --- | --- |
| Text Area Units · Size = Large / Medium / Small | `size="lg"` (label Std-18B-160) / `"md"` (Std-17B-170) / `"sm"` (Std-16B-170, 4px label gap) |
| Text Area Fields · State = Error | `error` or `errorText`; also automatic when the count exceeds `maxCount` |
| State = Readonly | `readOnly` (dashed border) |
| State = Disabled | `disabled` |
| hover / focus | CSS: black border on hover; system focus ring on focus |
| Show Count / Letter Counter Type | `maxCount` + `showCount`; counter turns red (Type=Error) over the limit |

The field is 120px tall (pad 16, radius 8, Dns-16N-130 text) and can be resized vertically; change the starting height with `height`.

## What the consumer provides
- `label`, optional `supportText`, `required`/`optional`, `maxCount`, `errorText`.
- Native textarea props (`name`, `value`/`onChange`, `rows`…) go to the `<textarea>`; `className`/`style` go to the wrapper.

## Accessibility notes
- Real `<label for>`; support text, counter and error text are linked with `aria-describedby`; errors set `aria-invalid`.
- Native `maxlength` is intentionally not applied so pasted text over the limit stays visible and fixable; the counter announces "文字数 n/100文字".
