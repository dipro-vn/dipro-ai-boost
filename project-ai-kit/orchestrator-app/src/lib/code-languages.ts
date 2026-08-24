import type { LanguageFn } from "highlight.js";
import bash from "highlight.js/lib/languages/bash";
import css from "highlight.js/lib/languages/css";
import dart from "highlight.js/lib/languages/dart";
import diff from "highlight.js/lib/languages/diff";
import ini from "highlight.js/lib/languages/ini";
import java from "highlight.js/lib/languages/java";
import javascript from "highlight.js/lib/languages/javascript";
import json from "highlight.js/lib/languages/json";
import kotlin from "highlight.js/lib/languages/kotlin";
import markdown from "highlight.js/lib/languages/markdown";
import plaintext from "highlight.js/lib/languages/plaintext";
import python from "highlight.js/lib/languages/python";
import rust from "highlight.js/lib/languages/rust";
import scss from "highlight.js/lib/languages/scss";
import sql from "highlight.js/lib/languages/sql";
import swift from "highlight.js/lib/languages/swift";
import typescript from "highlight.js/lib/languages/typescript";
import xml from "highlight.js/lib/languages/xml";
import yaml from "highlight.js/lib/languages/yaml";

/**
 * Grammar được đăng ký cho highlight.js — cố ý KHÔNG dùng bộ `common` (37
 * ngôn ngữ) của lowlight: nó nạp eager vào chunk chính và tốn hơn 100KB
 * gzip cho những ngôn ngữ dự án không bao giờ hiển thị. Danh sách dưới đây
 * bám theo stack thật của kit (NestJS · React · Flutter · PostgreSQL) cộng
 * vài định dạng config hay xuất hiện trong SPEC/DESIGN.
 *
 * Ngôn ngữ ngoài danh sách không lỗi — chỉ mất màu token, vẫn giữ nền One
 * Dark. Thêm ngôn ngữ mới: thêm 1 dòng import ở đây, cả markdown lẫn khung
 * xem file thô đều nhận ngay.
 *
 * Tách khỏi `code-theme.ts` vì file đó chỉ có màu và được `DiffView` dùng —
 * gộp vào sẽ kéo toàn bộ grammar sang chunk của diff viewer (nơi đã có
 * Prism/refractor riêng).
 */
export const CODE_LANGUAGES: Record<string, LanguageFn> = {
  bash,
  css,
  dart,
  diff,
  ini,
  java,
  javascript,
  json,
  kotlin,
  markdown,
  plaintext,
  python,
  rust,
  scss,
  sql,
  swift,
  typescript,
  xml,
  yaml,
};
