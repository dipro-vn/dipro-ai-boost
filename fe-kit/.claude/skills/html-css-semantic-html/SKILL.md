---
name: html-css-semantic-html
description: 
---

# Semantic HTML

**Category:** html-css · **Status:** 🟢 Active

## When to use
Khi dựng cấu trúc trang/section mới hoặc refactor markup `div`-soup.

## Steps
1. Bọc trang bằng landmark: `header`, `nav`, `main` (1 cái/trang), `footer`.
2. Dùng `article` cho nội dung độc lập, `section` cho nhóm có heading riêng.
3. Heading theo bậc liên tục `h1 → h2 → h3`, không nhảy bậc, mỗi trang 1 `h1`.
4. Chọn thẻ theo ngữ nghĩa: `button` cho hành động, `a` cho điều hướng, `ul/ol/li` cho danh sách.
5. Chỉ dùng `div`/`span` khi thuần styling, không có ngữ nghĩa.
6. Mỗi `nav`/`section` lặp lại nên có `aria-label` để phân biệt.

## Template
```html
<header>
  <nav aria-label="Chính">…</nav>
</header>
<main>
  <article>
    <h1>Tiêu đề bài viết</h1>
    <section aria-labelledby="cmt">
      <h2 id="cmt">Bình luận</h2>
    </section>
  </article>
</main>
<footer>…</footer>
```

## Example
**Good:** `main` duy nhất, heading liên tục, `button` cho action, `nav` có nhãn.
**Avoid:** `<div class="button">`, nhiều `h1`, nhảy `h1 → h4`, dùng `div` thay `ul`.

## Checklist
- [ ] Có landmark `main/header/nav/footer`
- [ ] Mỗi trang đúng 1 `h1`, heading không nhảy bậc
- [ ] `button` cho hành động, `a` cho điều hướng
- [ ] `nav`/`section` lặp lại có `aria-label`
