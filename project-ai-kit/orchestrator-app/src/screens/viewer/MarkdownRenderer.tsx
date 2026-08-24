import { lazy, Suspense } from "react";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import { rehypeCodeHighlight } from "@/lib/rehype-code-highlight";

const MermaidBlock = lazy(() =>
  import("@/screens/viewer/MermaidBlock").then((module) => ({ default: module.MermaidBlock })),
);

/**
 * `pre` is overridden to a no-op wrapper — `code` decides for itself
 * whether it needs a `<pre>` (regular fenced code) or not (mermaid, which
 * renders its own container). Fenced code is distinguished from inline
 * code by the `language-*` / `hljs` className that rehype sets on fenced
 * blocks and never on inline spans — there is no reliable `inline` prop in
 * react-markdown v9+ to check instead.
 */
const components: Components = {
  pre: ({ children }) => <>{children}</>,
  code: ({ className, children, ...props }) => {
    const classes = typeof className === "string" ? className.split(" ") : [];
    const languageClass = classes.find((name) => name.startsWith("language-"));
    const isFenced = languageClass !== undefined || classes.includes("hljs");

    if (!isFenced) {
      return (
        <code
          className="code-surface rounded px-1 py-0.5 font-mono text-xs"
          {...props}
        >
          {children}
        </code>
      );
    }

    if (languageClass === "language-mermaid") {
      return (
        <Suspense
          fallback={
            <div className="skeleton my-3 h-40 w-full" aria-label="Đang tải sơ đồ" />
          }
        >
          <MermaidBlock source={String(children).replace(/\n$/, "")} />
        </Suspense>
      );
    }

    return (
      <pre className="code-surface overflow-x-auto rounded-lg p-3 text-xs">
        <code className={className} {...props}>
          {children}
        </code>
      </pre>
    );
  },
  table: ({ children, ...props }) => (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm" {...props}>
        {children}
      </table>
    </div>
  ),
  th: ({ children, ...props }) => (
    <th className="border border-border bg-muted px-2 py-1 text-left" {...props}>
      {children}
    </th>
  ),
  td: ({ children, ...props }) => (
    <td className="border border-border px-2 py-1" {...props}>
      {children}
    </td>
  ),
};

export function MarkdownRenderer({ content }: { content: string }) {
  return (
    <div className="prose prose-sm max-w-none dark:prose-invert">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeCodeHighlight]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
