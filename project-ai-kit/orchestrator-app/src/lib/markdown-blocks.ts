/**
 * Splits markdown into coarse top-level blocks on blank lines, used to
 * virtualize large artifacts (AC-E3-19 — 2000+ line files must stay
 * smooth). Deliberately NOT a full remark-AST walk (see plan §4) — a naive
 * `content.split(/\n{2,}/)` would be wrong because it can cut a fenced
 * code block in half if the block itself contains a blank line (mermaid
 * diagrams often do, for readability). This tracks fence state so a blank
 * line INSIDE a ``` fence is never treated as a block boundary.
 */
export function splitMarkdownBlocks(content: string): string[] {
  const lines = content.split("\n");
  const blocks: string[] = [];
  let current: string[] = [];
  let inFence = false;

  const flush = () => {
    if (current.length > 0) {
      blocks.push(current.join("\n"));
      current = [];
    }
  };

  for (const line of lines) {
    if (/^```/.test(line.trim())) {
      inFence = !inFence;
    }

    if (!inFence && line.trim() === "") {
      flush();
      continue;
    }

    current.push(line);
  }
  flush();

  return blocks;
}
