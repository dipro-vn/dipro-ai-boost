# FormControlLabel

Form control labels name an input or a group of inputs and show whether it is required, plus optional support text.

## When to use
- Above any text field, select, or group of checkboxes / radio buttons.
- Use `as="legend"` inside a `<fieldset>` (CheckboxGroup and RadioGroup do this for you).

## Variants
- Label Units `Size` → `size`: `sm` (Std-16-170, 4px gap), `md` (Std-17-170, 8px gap), `lg` (Std-18-160, 8px gap).
- `Weight` → `weight`: `normal` | `bold`.
- Show Required / Requirements `Condition` → `requirement`: `required` (※必須, error-1), `optional` (※任意), `readonly` (編集不可 badge), `disabled` (無効 badge); omit to hide.
- Show Support Text → `supportText` (Std-16N-170, solid-gray-600).

## What the consumer provides
- The label text as children and `htmlFor` pointing at the control.
- Optional `supportText`; reference it from the control with `aria-describedby={supportId}` (pass `supportId` to fix the id).

## Accessibility notes
- The label row is a real `<label for>`; support text sits outside it so it is not read as part of the name.
- The requirement marker is visible text, but also set `required` / `aria-required` on the control itself.
