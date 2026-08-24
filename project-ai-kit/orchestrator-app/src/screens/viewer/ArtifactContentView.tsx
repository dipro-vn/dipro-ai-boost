import { Virtuoso } from "react-virtuoso";
import hljs from "highlight.js/lib/core";
import { CODE_LANGUAGES } from "@/lib/code-languages";
import { languageForPath } from "@/lib/code-theme";
import { cn } from "@/lib/utils";
import { splitMarkdownBlocks } from "@/lib/markdown-blocks";
import { MarkdownRenderer } from "@/screens/viewer/MarkdownRenderer";

for (const [name, language] of Object.entries(CODE_LANGUAGES)) {
  hljs.registerLanguage(name, language);
}

/** Above this many lines the document is split into blocks and virtualized
 * — a 2000-line SPEC.md renders as one React tree otherwise (AC-E3-19). */
export const VIRTUALIZE_LINE_THRESHOLD = 500;

interface ArtifactContentViewProps {
  /** Absolute path of the file being shown — decides markdown vs. raw-text
   * rendering below (folder explorer is the first caller that can open
   * anything other than `.md`; every other existing caller only ever
   * opens markdown by construction, so this was never needed before). */
  path: string;
  content: string;
  lineCount: number;
}

const MARKDOWN_EXTENSION = /\.(md|mdx)$/i;

/**
 * Renders one artifact, virtualizing long ones. Markdown (`.md`/`.mdx`)
 * renders through `MarkdownRenderer` as before; any other extension
 * renders as raw text in a `<pre>` — piping arbitrary files (`.json`,
 * `.ts`, `.env.example`, ...) through the markdown parser mangles them
 * (e.g. `_` read as emphasis).
 *
 * Extracted from `ArtifactViewerScreen` so the modal (`ArtifactModal`) gets
 * the same behaviour — including the mermaid/table support and the
 * virtualization threshold — without a second copy of the logic that could
 * drift from it.
 *
 * Fills its parent, so the caller owns the height (a screen gives it
 * `flex-1`, the modal gives it a `max-h` box).
 */
export function ArtifactContentView({ path, content, lineCount }: ArtifactContentViewProps) {
  const isMarkdown = MARKDOWN_EXTENSION.test(path);

  if (lineCount > VIRTUALIZE_LINE_THRESHOLD) {
    const blocks = isMarkdown ? splitMarkdownBlocks(content) : content.split("\n");
    return (
      <div className={cn("mx-auto h-full max-w-5xl", !isMarkdown && "code-surface")}>
        <Virtuoso
          style={{ height: "100%" }}
          data={blocks}
          itemContent={(_index, block) => (
            <div className={cn("mx-auto max-w-4xl px-4 lg:px-8", isMarkdown ? "py-1" : "py-0")}>
              {isMarkdown ? (
                <MarkdownRenderer content={block} />
              ) : (
                // Trên ngưỡng virtualize, mỗi item chỉ là 1 dòng nên không tô
                // màu token được (chuỗi/comment nhiều dòng sẽ bắt sai) — chỉ
                // giữ nền One Dark cho dễ đọc.
                <pre className="font-mono text-xs whitespace-pre-wrap">{block}</pre>
              )}
            </div>
          )}
        />
      </div>
    );
  }

  return (
    <div className="mx-auto h-full max-w-4xl overflow-auto px-4 py-4 lg:px-8">
      {isMarkdown ? <MarkdownRenderer content={content} /> : <RawText path={path} text={content} />}
    </div>
  );
}

/**
 * File không phải markdown, dưới ngưỡng virtualize — tô màu cả file trong
 * một lần để cấu trúc nhiều dòng (chuỗi, block comment) bắt token đúng.
 *
 * `dangerouslySetInnerHTML` ở đây an toàn: highlight.js escape toàn bộ ký
 * tự HTML của input, và input là file trên đĩa đã qua `resolve_and_guard`
 * phía Rust — cùng nguồn mà `MarkdownRenderer` vẫn đang render.
 */
function RawText({ path, text }: { path: string; text: string }) {
  const language = languageForPath(path);
  const highlighted =
    language && hljs.getLanguage(language)
      ? hljs.highlight(text, { language, ignoreIllegals: true }).value
      : null;

  return (
    <pre className="code-surface overflow-x-auto rounded-lg p-3 font-mono text-xs whitespace-pre-wrap">
      {highlighted === null ? text : <code dangerouslySetInnerHTML={{ __html: highlighted }} />}
    </pre>
  );
}
