---
name: mui-theme-customization
description: 
---

# Theme Customization

**Category:** mui · **Status:** 🟢 Active

## When to use
Khi cần tùy biến palette, typography, hoặc default style của component MUI ở cấp toàn app.

## Steps
1. Định nghĩa theme tập trung qua `createTheme`, bọc app bằng `ThemeProvider`.
2. Khai báo màu trong `palette` (`primary`, `secondary`, `error`...) thay vì rải hex trong code.
3. Đặt typography (`fontFamily`, scale `h1..body2`) một chỗ.
4. Override mặc định component qua `components.MuiX.defaultProps` / `styleOverrides`.
5. Truy cập token qua `sx`/`theme.palette`, không hardcode lại giá trị đã có trong theme.

## Template
```tsx
const theme = createTheme({
  palette: { primary: { main: '#1976d2' }, text: { secondary: '#5f6b7a' } },
  typography: { fontFamily: 'Inter, sans-serif', button: { textTransform: 'none' } },
  components: {
    MuiButton: { defaultProps: { disableElevation: true },
      styleOverrides: { root: { borderRadius: 8 } } },
  },
});

<ThemeProvider theme={theme}><App /></ThemeProvider>
```

## Example
**Good:** màu/typography khai báo trong theme, override default qua `components`, dùng lại token khắp app.
**Avoid:** hardcode hex/font trong từng component, lặp `sx` giống nhau thay vì set default ở theme.

## Checklist
- [ ] Palette & typography khai báo tập trung trong theme
- [ ] Override default component qua `components.MuiX`
- [ ] Component tham chiếu token thay vì hardcode
