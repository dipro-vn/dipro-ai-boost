# LanguageSelector

The language selector lets a person choose the preferred language in which content is shown; it pairs an icon opener with a menu list of languages.

## When to use
- In the site header of services offered in several languages, usually at the top right.
- Not for choosing a language as form data (use a select or radio group).

## Variants
- `Icon Openers Caret Type=Down | Up` → driven by open state (`open` / `defaultOpen`); the caret flips when the menu is shown.
- `State=Default | Hover | Focus` → CSS: hover fills `solid-gray-50` with a 1px black border; focus draws the system focus ring.
- `Language Selector Icons Icon Type=Language` → the built-in 30px language glyph with a "LANG" caption.
- Menu list (Small): 160px panel, `solid-gray-420` border, `elevation-1`, 36px items; the selected item is `key-100` with a check icon.
- `align="end" | "start"` chooses which edge of the opener the menu lines up with.

## What the consumer provides
- `languages`: `[{ value, label, lang, href? }]`, labels written in their own language.
- `value` + `onChange` (or `defaultValue`), and optionally `open` + `onOpenChange`.

## Accessibility notes
- The opener is a `button` with `aria-expanded` / `aria-controls` and an accessible name including the current language.
- Options are links with `lang` / `hreflang`; the selected one has `aria-current="true"`.
- Arrow Up/Down, Home/End move between options; Escape closes and returns focus to the opener; clicking outside closes.
- The "LANG" caption is rendered as text (the source uses vector letterforms).
