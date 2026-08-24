import { describe, expect, it } from "vitest";
import { rehypeCodeHighlight } from "@/lib/rehype-code-highlight";

interface Node {
  type: string;
  tagName?: string;
  properties?: { className?: unknown };
  children?: Node[];
  value?: string;
}

/** Cây hast của một fenced code block, đúng hình dạng remark-rehype sinh ra. */
function fence(language: string | null, code: string): { root: Node; code: Node } {
  const codeNode: Node = {
    type: "element",
    tagName: "code",
    properties: language ? { className: [`language-${language}`] } : {},
    children: [{ type: "text", value: code }],
  };
  return {
    root: {
      type: "root",
      children: [{ type: "element", tagName: "pre", children: [codeNode] }],
    },
    code: codeNode,
  };
}

function run(node: Node) {
  rehypeCodeHighlight()(node);
}

function classesOf(node: Node): string[] {
  const own = Array.isArray(node.properties?.className)
    ? (node.properties.className as string[])
    : [];
  return [...own, ...(node.children ?? []).flatMap(classesOf)];
}

function textOf(node: Node): string {
  if (node.type === "text") return node.value ?? "";
  return (node.children ?? []).map(textOf).join("");
}

describe("rehypeCodeHighlight", () => {
  it("tô màu token cho fence có khai ngôn ngữ", () => {
    const { root, code } = fence("typescript", "const a = 1;");
    run(root);
    expect(classesOf(code)).toContain("hljs");
    expect(classesOf(code).some((name) => name.startsWith("hljs-"))).toBe(true);
    expect(textOf(code)).toBe("const a = 1;");
  });

  it("nhận diện ngôn ngữ cho fence trần, để không rơi xuống nhánh inline code", () => {
    const { root, code } = fence(null, "SELECT id FROM orders WHERE status = 'paid';");
    run(root);
    expect(classesOf(code)).toContain("hljs");
  });

  it("để nguyên source mermaid — MermaidBlock cần chuỗi thô", () => {
    const source = "graph TD;\n  A-->B;";
    const { root, code } = fence("mermaid", source);
    run(root);
    expect(classesOf(code)).not.toContain("hljs");
    expect(textOf(code)).toBe(source);
  });

  it("ngôn ngữ lạ vẫn được đánh dấu hljs để giữ nền One Dark", () => {
    const { root, code } = fence("brainfuck", "+[-->-[>>+>-----<<]<--<---]");
    run(root);
    const classes = classesOf(code);
    expect(classes).toContain("hljs");
    expect(classes.some((name) => name.startsWith("hljs-"))).toBe(false);
  });

  it("không đụng vào inline code (code không nằm trong pre)", () => {
    const codeNode: Node = {
      type: "element",
      tagName: "code",
      properties: {},
      children: [{ type: "text", value: "pnpm build" }],
    };
    run({ type: "root", children: [{ type: "element", tagName: "p", children: [codeNode] }] });
    expect(classesOf(codeNode)).toEqual([]);
  });
});
