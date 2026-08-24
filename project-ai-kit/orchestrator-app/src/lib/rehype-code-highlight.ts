import { createLowlight } from "lowlight";
import { CODE_LANGUAGES } from "@/lib/code-languages";

/** Cây hast tối giản — đủ để đi qua và thay children của `pre > code`.
 * Không import `@types/hast` vì pnpm không hoist nó (chỉ là dep của
 * react-markdown), thêm dependency chỉ để lấy type là không đáng. */
interface HastNode {
  type: string;
  tagName?: string;
  properties?: { className?: unknown };
  children?: HastNode[];
  value?: string;
}

const lowlight = createLowlight(CODE_LANGUAGES);

/** Ngôn ngữ để nguyên văn: `MermaidBlock` cần chuỗi nguồn thô, tô màu sẽ
 * thay children bằng cây `<span>` và làm hỏng nó. */
const PLAIN_TEXT = new Set(["mermaid"]);

function classList(node: HastNode): string[] {
  const raw = node.properties?.className;
  if (Array.isArray(raw)) return raw.map(String);
  if (typeof raw === "string") return raw.split(" ");
  return [];
}

function languageOf(classes: string[]): string | undefined {
  const match = classes.find((name) => name.startsWith("language-") || name.startsWith("lang-"));
  return match?.slice(match.indexOf("-") + 1);
}

function textOf(node: HastNode): string {
  if (node.type === "text") return node.value ?? "";
  return (node.children ?? []).map(textOf).join("");
}

function highlightCodeElement(node: HastNode) {
  const classes = classList(node);
  const language = languageOf(classes);
  if (language && PLAIN_TEXT.has(language)) return;

  const known = language !== undefined && lowlight.registered(language);
  // Class `hljs` gắn cả khi ngôn ngữ lạ — nền One Dark áp theo class này,
  // mất màu token vẫn hơn là rơi xuống nhánh inline code.
  if (!classes.includes("hljs")) classes.unshift("hljs");
  node.properties = { ...node.properties, className: classes };
  if (language !== undefined && !known) return;

  const result = known
    ? lowlight.highlight(language, textOf(node))
    : lowlight.highlightAuto(textOf(node));
  if (result.children.length > 0) node.children = result.children as HastNode[];
}

function walk(node: HastNode, parent: HastNode | null) {
  if (node.tagName === "code" && parent?.tagName === "pre") {
    highlightCodeElement(node);
    return;
  }
  for (const child of node.children ?? []) walk(child, node);
}

/**
 * Rehype plugin tô màu `pre > code` bằng lowlight.
 *
 * Tự viết thay vì dùng `rehype-highlight` vì package đó `import {common}`
 * tĩnh — kéo cả 37 grammar vào chunk chính dù chỉ khai báo vài ngôn ngữ,
 * hơn 100KB gzip cho những thứ dự án không bao giờ hiển thị. Ở đây
 * `CODE_LANGUAGES` là danh sách duy nhất và tree-shake được.
 */
export function rehypeCodeHighlight() {
  return (tree: HastNode) => {
    walk(tree, null);
  };
}
