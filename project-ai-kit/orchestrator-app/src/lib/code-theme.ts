/**
 * One Dark (Atom) — bảng màu duy nhất cho mọi chỗ hiển thị code, **không**
 * đổi theo light/dark mode. Ở light mode nền `bg-muted` cũ chỉ cho chữ đen
 * trên xám nhạt, không phân biệt được keyword/string/comment; giữ code
 * luôn tối là cách duy nhất để một bảng màu phục vụ được cả hai mode.
 *
 * Màu token cho markdown/file thô nằm ở `.hljs-*` trong `index.css` (class
 * do highlight.js sinh). Bảng dưới đây là bản dịch sang tên token của Prism
 * — `react-diff-viewer-continued` dùng Prism (`refractor`), không dùng
 * highlight.js, nên phải khai riêng.
 */
export const ONE_DARK_BG = "#282c34";
export const ONE_DARK_FG = "#abb2bf";

/** Prism token → màu. Truyền vào `highlightTheme` của `ReactDiffViewer`. */
export const ONE_DARK_PRISM_THEME: Record<string, string> = {
  default: ONE_DARK_FG,
  comment: "#5c6370",
  prolog: "#5c6370",
  doctype: "#5c6370",
  cdata: "#5c6370",
  punctuation: ONE_DARK_FG,
  property: "#e06c75",
  tag: "#e06c75",
  boolean: "#d19a66",
  number: "#d19a66",
  constant: "#d19a66",
  symbol: "#e06c75",
  deleted: "#e06c75",
  selector: "#98c379",
  "attr-name": "#d19a66",
  string: "#98c379",
  char: "#98c379",
  builtin: "#e5c07b",
  inserted: "#98c379",
  operator: "#56b6c2",
  entity: "#e06c75",
  url: "#98c379",
  "attr-value": "#98c379",
  keyword: "#c678dd",
  atrule: "#c678dd",
  "class-name": "#e5c07b",
  function: "#61afef",
  regex: "#98c379",
  important: "#c678dd",
  variable: "#e06c75",
};

/** Đuôi file → tên ngôn ngữ. Dùng chung cho highlight.js (file thô) và
 * Prism (diff) — các tên dưới đây đều được cả hai nhận, trừ `dart` mà Prism
 * không có grammar; cả hai bên đều bỏ qua ngôn ngữ lạ mà không lỗi. */
const LANGUAGE_BY_EXTENSION: Record<string, string> = {
  ts: "typescript",
  tsx: "typescript",
  mts: "typescript",
  cts: "typescript",
  js: "javascript",
  jsx: "javascript",
  mjs: "javascript",
  cjs: "javascript",
  json: "json",
  jsonc: "json",
  dart: "dart",
  rs: "rust",
  py: "python",
  rb: "ruby",
  go: "go",
  java: "java",
  kt: "kotlin",
  kts: "kotlin",
  swift: "swift",
  sql: "sql",
  sh: "bash",
  bash: "bash",
  zsh: "bash",
  yml: "yaml",
  yaml: "yaml",
  toml: "ini",
  ini: "ini",
  env: "ini",
  css: "css",
  scss: "scss",
  less: "less",
  html: "xml",
  xml: "xml",
  svg: "xml",
  md: "markdown",
  mdx: "markdown",
  diff: "diff",
  patch: "diff",
};

/** Ngôn ngữ suy ra từ đuôi file, `undefined` nếu không nhận ra. */
export function languageForPath(path: string): string | undefined {
  const extension = path.split(".").pop()?.toLowerCase();
  return extension ? LANGUAGE_BY_EXTENSION[extension] : undefined;
}
