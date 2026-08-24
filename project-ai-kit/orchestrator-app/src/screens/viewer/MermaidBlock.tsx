import { useEffect, useId, useState } from "react";
import mermaid from "mermaid";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ErrorBoundary } from "@/components/shell/ErrorBoundary";
import { useInView } from "@/lib/use-in-view";

mermaid.initialize({ startOnLoad: false });

function RawSourceFallback({ source, message }: { source: string; message: string }) {
  return (
    <div className="flex flex-col gap-2">
      <Alert variant="destructive">
        <AlertTitle>Không vẽ được sơ đồ mermaid</AlertTitle>
        <AlertDescription>{message}</AlertDescription>
      </Alert>
      <pre className="overflow-x-auto rounded-lg bg-muted p-3 text-xs">
        <code>{source}</code>
      </pre>
    </div>
  );
}

/**
 * Renders a fenced ```mermaid block. Two layers of failure isolation, per
 * plan: `mermaid.parse` is checked first (catches most syntax errors
 * cleanly), AND the whole thing is wrapped in an `ErrorBoundary` in case
 * `render` itself throws something parse didn't catch — either way, a bad
 * diagram shows its raw source + the error instead of breaking the rest of
 * the document (AC-E3-18).
 *
 * Rendering is deferred until the block scrolls near the viewport
 * (`useInView`) — this, not markdown parsing, is the actual expensive part
 * for a document with many diagrams (AC-E3-19).
 */
function MermaidBlockInner({ source }: { source: string }) {
  const [containerRef, inView] = useInView<HTMLDivElement>();
  const rawId = useId().replace(/[:]/g, "-");
  const [svg, setSvg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!inView) return;
    let cancelled = false;

    async function run() {
      const parseResult = await mermaid
        .parse(source, { suppressErrors: true })
        .catch(() => false as const);

      if (parseResult === false) {
        if (!cancelled) setError("Cú pháp mermaid không hợp lệ.");
        return;
      }

      try {
        const { svg: renderedSvg } = await mermaid.render(`mermaid-${rawId}`, source);
        if (!cancelled) setSvg(renderedSvg);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
        }
      }
    }

    void run();
    return () => {
      cancelled = true;
    };
  }, [inView, source, rawId]);

  if (error) {
    return (
      <div ref={containerRef}>
        <RawSourceFallback source={source} message={error} />
      </div>
    );
  }

  if (!svg) {
    return (
      <div
        ref={containerRef}
        className="h-24 animate-pulse rounded-lg bg-muted"
        aria-label="Đang tải sơ đồ"
      />
    );
  }

  // eslint-disable-next-line react/no-danger -- SVG generated locally by
  // mermaid from a file already read through the app's own path-guard, not
  // untrusted external HTML (same reasoning as skipping rehype-sanitize).
  return <div ref={containerRef} dangerouslySetInnerHTML={{ __html: svg }} />;
}

export function MermaidBlock({ source }: { source: string }) {
  return (
    <ErrorBoundary
      fallback={(err) => (
        <RawSourceFallback source={source} message={err.message} />
      )}
    >
      <MermaidBlockInner source={source} />
    </ErrorBoundary>
  );
}
