# List

A bulleted or numbered list for enumerating one or more items.

## When to use
- `List` (bulleted) for unordered items such as required documents.
- `List ordered` for steps or legal-style numbered clauses (第１, （１）, （ア）, イロハ…).
- Nest a `List` inside a `ListItem` for sub-items; each level indents 32px.

## Variants
| Figma | Prop | Values |
|---|---|---|
| List with List Marks / with Numbers | `ordered` | `false` (default) / `true` |
| Markers / List Mark Style | `marker` | `disc`, `circle`, `square`, `square-outlined` (default by depth: disc → circle → square) |
| Markers / List Mark Size | `markerSize` | 4, 6 (default), 8, 10 |
| Markers / Number Type | `numbering` | `decimal` 1. · `upper-alpha` A. · `lower-alpha` a. · `upper-roman` I. · `lower-roman` i. · `dai-fullwidth` 第１ · `dai-kanji` 第一 · `fullwidth` １ · `kanji` 一 · `paren-fullwidth` （１） · `paren-kanji` （一） · `katakana` ア · `paren-katakana` （ア） · `iroha` イ · `paren-iroha` （イ） · `circled` ① |
| Spacing | `spacing` | 4, 8 (default), 12 px above and below each item |
| Indent | `indent` / nesting | 0, 32, 64 |
| Link / Show Tail-icon | `ListItem href`, `external` | link text (blue-1000, underlined) with 16px new-window icon |

Markers sit in a 32px column (bullets centred in 32×27, numbers left-aligned); text is Std-16N-170 solid-gray-800.

## What the consumer provides
- `ListItem` children with short, parallel wording; nested `List`s inside items.
- `start` / `value` when numbering must continue across lists.

## Accessibility notes
- Renders real `<ul>`/`<ol>` with `role="list"` (kept because list-style is removed).
- Bullets are `aria-hidden`; number markers are visible text so references like 「第２（１）」 match what is read aloud.
