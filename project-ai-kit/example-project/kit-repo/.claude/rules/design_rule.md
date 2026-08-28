# Design System — Token Reference

> **Purpose:** AI design input. Apply these tokens exactly when generating UI, components, or specifications for the product.

> **Font:** Noto Sans JP (default)

---

## 1. Color Primitives

Raw palette. Do not use these directly in components — reference via Semantics or Components layer.

### 1.1 Blue


| Token                        | Hex         |
| ---------------------------- | ----------- |
| `colors.primitives.blue.50`  | `#e5f6ffff` |
| `colors.primitives.blue.100` | `#ceedffff` |
| `colors.primitives.blue.200` | `#97d3ffff` |
| `colors.primitives.blue.300` | `#61b3ffff` |
| `colors.primitives.blue.400` | `#218bffff` |
| `colors.primitives.blue.500` | `#0969daff` |
| `colors.primitives.blue.600` | `#0550aeff` |
| `colors.primitives.blue.700` | `#033d8bff` |
| `colors.primitives.blue.800` | `#0a3069ff` |
| `colors.primitives.blue.900` | `#002155ff` |


### 1.2 Gray


| Token                        | Hex         |
| ---------------------------- | ----------- |
| `colors.primitives.gray.50`  | `#f6f8faff` |
| `colors.primitives.gray.100` | `#eaeef2ff` |
| `colors.primitives.gray.200` | `#d0d7deff` |
| `colors.primitives.gray.300` | `#afb8c1ff` |
| `colors.primitives.gray.400` | `#8c959fff` |
| `colors.primitives.gray.500` | `#6e7781ff` |
| `colors.primitives.gray.600` | `#57606aff` |
| `colors.primitives.gray.700` | `#424a53ff` |
| `colors.primitives.gray.800` | `#32383fff` |
| `colors.primitives.gray.900` | `#24292fff` |


### 1.3 Red


| Token                       | Hex         |
| --------------------------- | ----------- |
| `colors.primitives.red.50`  | `#fff6f5ff` |
| `colors.primitives.red.100` | `#ffe5e4ff` |
| `colors.primitives.red.200` | `#ffbbb9ff` |
| `colors.primitives.red.300` | `#ff8182ff` |
| `colors.primitives.red.400` | `#fa4549ff` |
| `colors.primitives.red.500` | `#cf222eff` |
| `colors.primitives.red.600` | `#a40e26ff` |
| `colors.primitives.red.700` | `#82071eff` |
| `colors.primitives.red.800` | `#660018ff` |
| `colors.primitives.red.900` | `#4c0014ff` |


### 1.4 Orange


| Token                          | Hex         |
| ------------------------------ | ----------- |
| `colors.primitives.orange.50`  | `#fff9ebff` |
| `colors.primitives.orange.100` | `#feedc7ff` |
| `colors.primitives.orange.200` | `#fdda8aff` |
| `colors.primitives.orange.300` | `#fbc14eff` |
| `colors.primitives.orange.400` | `#faa51dff` |
| `colors.primitives.orange.500` | `#f4860cff` |
| `colors.primitives.orange.600` | `#d86107ff` |
| `colors.primitives.orange.700` | `#b3410aff` |
| `colors.primitives.orange.800` | `#91320fff` |
| `colors.primitives.orange.900` | `#782a0fff` |


### 1.5 Yellow


| Token                          | Hex         |
| ------------------------------ | ----------- |
| `colors.primitives.yellow.50`  | `#fef9e8ff` |
| `colors.primitives.yellow.100` | `#fef0c3ff` |
| `colors.primitives.yellow.200` | `#fee28aff` |
| `colors.primitives.yellow.300` | `#fdd147ff` |
| `colors.primitives.yellow.400` | `#fac215ff` |
| `colors.primitives.yellow.500` | `#eab308ff` |
| `colors.primitives.yellow.600` | `#ca9a04ff` |
| `colors.primitives.yellow.700` | `#a16207ff` |
| `colors.primitives.yellow.800` | `#854d0eff` |
| `colors.primitives.yellow.900` | `#713f12ff` |


### 1.6 Green


| Token                         | Hex         |
| ----------------------------- | ----------- |
| `colors.primitives.green.50`  | `#edfdf0ff` |
| `colors.primitives.green.100` | `#c5f7d0ff` |
| `colors.primitives.green.200` | `#6fdd8bff` |
| `colors.primitives.green.300` | `#4ac26bff` |
| `colors.primitives.green.400` | `#2da44eff` |
| `colors.primitives.green.500` | `#1a7f37ff` |
| `colors.primitives.green.600` | `#116329ff` |
| `colors.primitives.green.700` | `#044f1eff` |
| `colors.primitives.green.800` | `#003d16ff` |
| `colors.primitives.green.900` | `#002d11ff` |


### 1.7 Purple


| Token                          | Hex         |
| ------------------------------ | ----------- |
| `colors.primitives.purple.50`  | `#fbefffff` |
| `colors.primitives.purple.100` | `#ecd8ffff` |
| `colors.primitives.purple.200` | `#d8b9ffff` |
| `colors.primitives.purple.300` | `#c297ffff` |
| `colors.primitives.purple.400` | `#a475f9ff` |
| `colors.primitives.purple.500` | `#8250dfff` |
| `colors.primitives.purple.600` | `#6639baff` |
| `colors.primitives.purple.700` | `#512a97ff` |
| `colors.primitives.purple.800` | `#3e1f79ff` |
| `colors.primitives.purple.900` | `#2e1461ff` |


### 1.8 Black &amp; White


| Token                     | Hex         |
| ------------------------- | ----------- |
| `colors.primitives.black` | `#000000ff` |
| `colors.primitives.white` | `#ffffffff` |


---

## 2. Color Semantics

Semantic layer maps primitive colors to intent. Use these in design decisions.


| Token                           | Maps to Primitive                 | Intent                      |
| ------------------------------- | --------------------------------- | --------------------------- |
| `colors.semantics.company.50`   | `{colors: primitives.blue.50}`    | Brand / primary action      |
| `colors.semantics.company.100`  | `{colors: primitives.blue.100}`   | Brand / primary action      |
| `colors.semantics.company.200`  | `{colors: primitives.blue.200}`   | Brand / primary action      |
| `colors.semantics.company.300`  | `{colors: primitives.blue.300}`   | Brand / primary action      |
| `colors.semantics.company.400`  | `{colors: primitives.blue.400}`   | Brand / primary action      |
| `colors.semantics.company.500`  | `{colors: primitives.blue.500}`   | Brand / primary action      |
| `colors.semantics.company.600`  | `{colors: primitives.blue.600}`   | Brand / primary action      |
| `colors.semantics.company.700`  | `{colors: primitives.blue.700}`   | Brand / primary action      |
| `colors.semantics.company.800`  | `{colors: primitives.blue.800}`   | Brand / primary action      |
| `colors.semantics.company.900`  | `{colors: primitives.blue.900}`   | Brand / primary action      |
| `colors.semantics.neutral.50`   | `{colors: primitives.gray.50}`    | UI structure, text, borders |
| `colors.semantics.neutral.100`  | `{colors: primitives.gray.100}`   | UI structure, text, borders |
| `colors.semantics.neutral.200`  | `{colors: primitives.gray.200}`   | UI structure, text, borders |
| `colors.semantics.neutral.300`  | `{colors: primitives.gray.300}`   | UI structure, text, borders |
| `colors.semantics.neutral.400`  | `{colors: primitives.gray.400}`   | UI structure, text, borders |
| `colors.semantics.neutral.500`  | `{colors: primitives.gray.500}`   | UI structure, text, borders |
| `colors.semantics.neutral.600`  | `{colors: primitives.gray.600}`   | UI structure, text, borders |
| `colors.semantics.neutral.700`  | `{colors: primitives.gray.700}`   | UI structure, text, borders |
| `colors.semantics.neutral.800`  | `{colors: primitives.gray.800}`   | UI structure, text, borders |
| `colors.semantics.neutral.900`  | `{colors: primitives.gray.900}`   | UI structure, text, borders |
| `colors.semantics.negative.50`  | `{colors: primitives.red.50}`     | Error, destructive, danger  |
| `colors.semantics.negative.100` | `{colors: primitives.red.100}`    | Error, destructive, danger  |
| `colors.semantics.negative.200` | `{colors: primitives.red.200}`    | Error, destructive, danger  |
| `colors.semantics.negative.300` | `{colors: primitives.red.300}`    | Error, destructive, danger  |
| `colors.semantics.negative.400` | `{colors: primitives.red.400}`    | Error, destructive, danger  |
| `colors.semantics.negative.500` | `{colors: primitives.red.500}`    | Error, destructive, danger  |
| `colors.semantics.success.50`   | `{colors: primitives.green.50}`   | Success, confirmation       |
| `colors.semantics.success.100`  | `{colors: primitives.green.100}`  | Success, confirmation       |
| `colors.semantics.success.200`  | `{colors: primitives.green.200}`  | Success, confirmation       |
| `colors.semantics.success.300`  | `{colors: primitives.green.300}`  | Success, confirmation       |
| `colors.semantics.success.400`  | `{colors: primitives.green.400}`  | Success, confirmation       |
| `colors.semantics.success.500`  | `{colors: primitives.green.500}`  | Success, confirmation       |
| `colors.semantics.info.50`      | `{colors: primitives.blue.50}`    | Informational               |
| `colors.semantics.info.100`     | `{colors: primitives.blue.100}`   | Informational               |
| `colors.semantics.info.200`     | `{colors: primitives.blue.200}`   | Informational               |
| `colors.semantics.info.300`     | `{colors: primitives.blue.300}`   | Informational               |
| `colors.semantics.info.400`     | `{colors: primitives.blue.400}`   | Informational               |
| `colors.semantics.info.500`     | `{colors: primitives.blue.500}`   | Informational               |
| `colors.semantics.warning.50`   | `{colors: primitives.yellow.50}`  | Warning, caution            |
| `colors.semantics.warning.100`  | `{colors: primitives.yellow.100}` | Warning, caution            |
| `colors.semantics.warning.200`  | `{colors: primitives.yellow.200}` | Warning, caution            |
| `colors.semantics.warning.300`  | `{colors: primitives.yellow.300}` | Warning, caution            |
| `colors.semantics.warning.400`  | `{colors: primitives.yellow.400}` | Warning, caution            |
| `colors.semantics.warning.500`  | `{colors: primitives.yellow.500}` | Warning, caution            |
| `colors.semantics.app.50`       | `{colors: primitives.yellow.50}`  | App-facing UI accent        |
| `colors.semantics.app.100`      | `{colors: primitives.yellow.100}` | App-facing UI accent        |
| `colors.semantics.app.200`      | `{colors: primitives.yellow.200}` | App-facing UI accent        |
| `colors.semantics.app.300`      | `{colors: primitives.yellow.300}` | App-facing UI accent        |
| `colors.semantics.app.400`      | `{colors: primitives.yellow.400}` | App-facing UI accent        |
| `colors.semantics.app.500`      | `{colors: primitives.yellow.500}` | App-facing UI accent        |
| `colors.semantics.app.600`      | `{colors: primitives.yellow.600}` | App-facing UI accent        |
| `colors.semantics.app.700`      | `{colors: primitives.yellow.700}` | App-facing UI accent        |
| `colors.semantics.app.800`      | `{colors: primitives.yellow.800}` | App-facing UI accent        |
| `colors.semantics.app.900`      | `{colors: primitives.yellow.900}` | App-facing UI accent        |
| `colors.semantics.admin.50`     | `{colors: primitives.orange.50}`  | Admin-facing UI accent      |
| `colors.semantics.admin.100`    | `{colors: primitives.orange.100}` | Admin-facing UI accent      |
| `colors.semantics.admin.200`    | `{colors: primitives.orange.200}` | Admin-facing UI accent      |
| `colors.semantics.admin.300`    | `{colors: primitives.orange.300}` | Admin-facing UI accent      |
| `colors.semantics.admin.400`    | `{colors: primitives.orange.400}` | Admin-facing UI accent      |
| `colors.semantics.admin.500`    | `{colors: primitives.orange.500}` | Admin-facing UI accent      |


---

## 3. Color Components

Component-specific color tokens. Use these directly when building UI components.


| Token                                | Maps to                           | Usage                                               |
| ------------------------------------ | --------------------------------- | --------------------------------------------------- |
| `colors.components.slot.fill`        | `{colors: primitives.purple.100}` | Slot/placeholder UI (e.g. empty state, drag target) |
| `colors.components.slot.stroke`      | `{colors: primitives.purple.600}` | Slot/placeholder UI (e.g. empty state, drag target) |
| `colors.components.slot.label.fill`  | `{colors: primitives.purple.600}` | Slot/placeholder UI (e.g. empty state, drag target) |
| `colors.components.divider.low`      | `{colors: semantics.neutral.100}` | Divider lines, separators                           |
| `colors.components.divider.middle`   | `{colors: semantics.neutral.200}` | Divider lines, separators                           |
| `colors.components.divider.high`     | `{colors: semantics.neutral.300}` | Divider lines, separators                           |
| `colors.components.text.low`         | `{colors: semantics.neutral.500}` | Body text hierarchy                                 |
| `colors.components.text.middle`      | `{colors: semantics.neutral.700}` | Body text hierarchy                                 |
| `colors.components.text.high`        | `{colors: semantics.neutral.900}` | Body text hierarchy                                 |
| `colors.components.text.disabled`    | `{colors: semantics.neutral.500}` | Body text hierarchy                                 |
| `colors.components.text.placeholder` | `{colors: semantics.neutral.500}` | Body text hierarchy                                 |
| `colors.components.skeleton.fill`    | `{colors: semantics.neutral.200}` | Loading skeleton fill                               |
| `colors.components.ring.normal`      | `#096cdcff`                       | Focus ring / outline                                |


---

## 4. Typography

### 4.1 Primitives

#### Font Family


| Token                            | Value          |
| -------------------------------- | -------------- |
| `typography.font-family.mono`    | `BIZ UDGothic` |
| `typography.font-family.default` | `Noto Sans JP` |


#### Font Size


| Token                     | Value (px) |
| ------------------------- | ---------- |
| `typography.font-size.12` | `12px`     |
| `typography.font-size.14` | `14px`     |
| `typography.font-size.16` | `16px`     |
| `typography.font-size.18` | `18px`     |
| `typography.font-size.20` | `20px`     |
| `typography.font-size.24` | `24px`     |
| `typography.font-size.28` | `28px`     |
| `typography.font-size.32` | `32px`     |
| `typography.font-size.36` | `36px`     |
| `typography.font-size.42` | `42px`     |
| `typography.font-size.48` | `48px`     |
| `typography.font-size.54` | `54px`     |


#### Font Weight


| Token                           | Value |
| ------------------------------- | ----- |
| `typography.font-weight.normal` | `400` |
| `typography.font-weight.bold`   | `700` |
| `typography.font-weight.medium` | `500` |


#### Line Height


| Token                       | Value (px) |
| --------------------------- | ---------- |
| `typography.line-height.18` | `18px`     |
| `typography.line-height.20` | `20px`     |
| `typography.line-height.24` | `24px`     |
| `typography.line-height.28` | `28px`     |
| `typography.line-height.32` | `32px`     |
| `typography.line-height.36` | `36px`     |
| `typography.line-height.44` | `44px`     |
| `typography.line-height.48` | `48px`     |
| `typography.line-height.56` | `56px`     |
| `typography.line-height.64` | `64px`     |
| `typography.line-height.72` | `72px`     |
| `typography.line-height.84` | `84px`     |


#### Letter Spacing


| Token                              | Value (em) |
| ---------------------------------- | ---------- |
| `typography.letter-spacing.normal` | `0em`      |
| `typography.letter-spacing.wide`   | `0.02em`   |
| `typography.letter-spacing.wider`  | `0.05em`   |
| `typography.letter-spacing.widest` | `0.1em`    |


### 4.2 Text Styles (Composed)

Combined styles for direct application. Use these when assigning typography to UI elements.


| Style                     | Weight        | Size | Line Height | Usage hint                  |
| ------------------------- | ------------- | ---- | ----------- | --------------------------- |
| `font.display md.regular` | 400 (regular) | 36px | 44px        | Hero / page title           |
| `font.display md.medium`  | 500 (medium)  | 36px | 44px        | Hero / page title           |
| `font.display md.bold`    | 700 (bold)    | 36px | 44px        | Hero / page title           |
| `font.display sm.regular` | 400 (regular) | 32px | 36px        | Section header              |
| `font.display sm.medium`  | 500 (medium)  | 32px | 36px        | Section header              |
| `font.display sm.bold`    | 700 (bold)    | 32px | 36px        | Section header              |
| `font.display xs.regular` | 400 (regular) | 24px | 28px        | Sub-section / modal title   |
| `font.display xs.medium`  | 500 (medium)  | 24px | 28px        | Sub-section / modal title   |
| `font.display xs.bold`    | 700 (bold)    | 24px | 28px        | Sub-section / modal title   |
| `font.text xl.regular`    | 400 (regular) | 20px | 24px        | Card title, large body      |
| `font.text xl.medium`     | 500 (medium)  | 20px | 24px        | Card title, large body      |
| `font.text xl.bold`       | 700 (bold)    | 20px | 24px        | Card title, large body      |
| `font.text lg.regular`    | 400 (regular) | 18px | 24px        | Subheading, emphasized body |
| `font.text lg.medium`     | 500 (medium)  | 18px | 24px        | Subheading, emphasized body |
| `font.text lg.bold`       | 700 (bold)    | 18px | 24px        | Subheading, emphasized body |
| `font.text md.regular`    | 400 (regular) | 16px | 24px        | Default body text           |
| `font.text md.medium`     | 500 (medium)  | 16px | 24px        | Default body text           |
| `font.text md.bold`       | 700 (bold)    | 16px | 24px        | Default body text           |
| `font.text sm.regular`    | 400 (regular) | 14px | 20px        | Secondary body, labels      |
| `font.text sm.medium`     | 500 (medium)  | 14px | 20px        | Secondary body, labels      |
| `font.text sm.bold`       | 700 (bold)    | 14px | 20px        | Secondary body, labels      |
| `font.text xs.regular`    | 400 (regular) | 12px | 18px        | Caption, helper text, badge |
| `font.text xs.medium`     | 500 (medium)  | 12px | 18px        | Caption, helper text, badge |
| `font.text xs.bold`       | 700 (bold)    | 12px | 18px        | Caption, helper text, badge |


---

## 5. Border Radius

### 5.1 Primitives


| Token                                   | Value                 |
| --------------------------------------- | --------------------- |
| `borders.primitives.border-radius.none` | `0px`                 |
| `borders.primitives.border-radius.xs`   | `2px`                 |
| `borders.primitives.border-radius.sm`   | `4px`                 |
| `borders.primitives.border-radius.md`   | `6px`                 |
| `borders.primitives.border-radius.lg`   | `8px`                 |
| `borders.primitives.border-radius.xl`   | `12px`                |
| `borders.primitives.border-radius.2xl`  | `16px`                |
| `borders.primitives.border-radius.3xl`  | `24px`                |
| `borders.primitives.border-radius.full` | `9999px (full round)` |


### 5.2 Semantics

Apply these semantic tokens to components — not the raw primitives.


| Token                                       | Maps to                                    | Value    | Usage                                            |
| ------------------------------------------- | ------------------------------------------ | -------- | ------------------------------------------------ |
| `borders.semantics.border-radius.divide`    | `{borders: primitives.border-radius.none}` | `0px`    | Layout dividers (no radius)                      |
| `borders.semantics.border-radius.minimum`   | `{borders: primitives.border-radius.xs}`   | `2px`    | All non-divider elements minimum                 |
| `borders.semantics.border-radius.notice`    | `{borders: primitives.border-radius.sm}`   | `4px`    | System notification elements                     |
| `borders.semantics.border-radius.action`    | `{borders: primitives.border-radius.md}`   | `6px`    | Actionable / clickable elements (buttons, chips) |
| `borders.semantics.border-radius.halfmodal` | `{borders: primitives.border-radius.lg}`   | `8px`    | Bottom sheet / half modal                        |
| `borders.semantics.border-radius.modal`     | `{borders: primitives.border-radius.xl}`   | `12px`   | Full modal dialogs                               |
| `borders.semantics.border-radius.round`     | `{borders: primitives.border-radius.full}` | `9999px` | Pill badges, avatars, tags                       |


---

## 6. Spacing

Padding scale. Use for margin, padding, gap in layouts.


| Token                 | Value   |
| --------------------- | ------- |
| `spacing.padding.0`   | `0px`   |
| `spacing.padding.2`   | `2px`   |
| `spacing.padding.4`   | `4px`   |
| `spacing.padding.6`   | `6px`   |
| `spacing.padding.8`   | `8px`   |
| `spacing.padding.12`  | `12px`  |
| `spacing.padding.16`  | `16px`  |
| `spacing.padding.20`  | `20px`  |
| `spacing.padding.24`  | `24px`  |
| `spacing.padding.32`  | `32px`  |
| `spacing.padding.40`  | `40px`  |
| `spacing.padding.48`  | `48px`  |
| `spacing.padding.56`  | `56px`  |
| `spacing.padding.72`  | `72px`  |
| `spacing.padding.88`  | `88px`  |
| `spacing.padding.104` | `104px` |
| `spacing.padding.120` | `120px` |


---

## 7. Sizing (Max-width)

Max-width breakpoints for containers and modals.


| Token                  | Value    |
| ---------------------- | -------- |
| `sizing.max-width.xs`  | `320px`  |
| `sizing.max-width.sm`  | `384px`  |
| `sizing.max-width.md`  | `448px`  |
| `sizing.max-width.lg`  | `512px`  |
| `sizing.max-width.xl`  | `576px`  |
| `sizing.max-width.2xl` | `672px`  |
| `sizing.max-width.3xl` | `768px`  |
| `sizing.max-width.4xl` | `896px`  |
| `sizing.max-width.5xl` | `1024px` |
| `sizing.max-width.6xl` | `1152px` |
| `sizing.max-width.7xl` | `1280px` |


---

## 8. Effects (Box Shadow)


| Token                      | Color       | Offset X | Offset Y | Radius | Spread | Usage                          |
| -------------------------- | ----------- | -------- | -------- | ------ | ------ | ------------------------------ |
| `effect.box-shadow.base`   | `#000000ff` | `0`      | `0`      | `0`    | `0`    | No shadow (flat surface)       |
| `effect.box-shadow.flat`   | `#0000000d` | `0`      | `1`      | `0`    | `0`    | Subtle lift, 1px bottom tint   |
| `effect.box-shadow.raise`  | `#0000000d` | `0`      | `1`      | `2`    | `0`    | Card / raised surface          |
| `effect.box-shadow.stick`  | ``          | ``       | ``       | ``     | ``     | Sticky header / fixed element  |
| `effect.box-shadow.float`  | ``          | ``       | ``       | ``     | ``     | Floating UI (tooltip, popover) |
| `effect.box-shadow.popout` | ``          | ``       | ``       | ``     | ``     | Dropdown, modal, highest layer |


---

## 9. AI Usage Rules

When generating any UI or design spec, follow these rules:

**Colors**

- Never use raw hex values. Always reference token names.
- Use `colors.components.*` for component-level color decisions.
- Use `colors.semantics.*` for state-driven color (error, success, warning...).
- Use `colors.primitives.*` only when defining new semantic/component tokens.

**Typography**

- Default font: `Noto Sans JP`. Mono/code font: `BIZ UDGothic`.
- Body default: `font.text md.regular` (16px / 24px line-height).
- Never invent a font size outside the defined scale.
- Apply weights via `typography.font-weight.*` tokens (400 / 500 / 700 only).

**Border Radius**

- Always apply via `borders.semantics.border-radius.*` — not raw primitives.
- Buttons, chips, inputs → `action` (6px)
- Modals → `modal` (12px)
- Bottom sheets → `halfmodal` (8px)
- Pill / badge / avatar → `round` (9999px)

**Spacing**

- Use only values from `spacing.padding.*` scale.
- Common gaps: 4, 8, 12, 16, 24, 32px.

**Elevation**

- Apply `effect.box-shadow.*` based on element layer:
  - Base content → `flat`
  - Cards → `raise`
  - Sticky bars → `stick`
  - Tooltips, popovers → `float`
  - Modals, dropdowns → `popout`

---

## 10. Per-Site Layout Rules

> Section này RỖNG trong kit gốc — mỗi repo trong bảng Ecosystem cần 1 sub-section riêng (viewport, layout structure, sidebar width, common components...), do `designer-agent` điền dần khi đọc Figma thật của dự án lần đầu. Format tham khảo (nhân bản cho mỗi repo):

### \<Tên repo\> — \<vai trò\> (\<mô tả ngắn\>)

**Color theme:** _(token chính dùng cho button primary/active state)_

**Viewport:** _(kích thước chuẩn — desktop 1440×1024 hay mobile 390×844...)_

**Layout structure:** _(sơ đồ ASCII layout tổng quan)_

| Yếu tố | Giá trị |
|---|---|
| ... | ... |

**Navigation:** _(pattern sidebar/top-nav/bottom-nav)_

**Screen naming convention:** _(quy tắc đặt tên frame Figma)_

---

## 11. Figma → Token Quick Lookup (per repo)

_(điền dần khi Designer đọc Figma thật của từng repo — mapping hex code Figma → token trong section 1-3)_

| Repo | Primary button hex | Token | Nguồn |
|---|---|---|---|

**Shared error / success / warning** — tất cả repo:
| Intent | Token | Hex |
|---|---|---|
| Error / Destructive | `colors.semantics.negative.500` | `#cf222e` |
| Success / Confirm | `colors.semantics.success.400` | `#2da44e` |
| Warning | `colors.semantics.warning.400` | `#fac215` |
| Info | `colors.semantics.info.500` | `#0969da` |
| Text primary | `colors.components.text.high` | `#24292f` |
| Text secondary | `colors.components.text.middle` | `#424a53` |
| Text disabled | `colors.components.text.low` | `#6e7781` |
| Border default | `colors.components.divider.middle` | `#d0d7de` |
| Background page | `colors.semantics.neutral.50` | `#f6f8fa` |
