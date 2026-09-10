/** Extensions `read_artifact` can actually return.
 *
 * The backend reads with `std::fs::read_to_string` (`commands/artifact.rs`),
 * so anything that is not valid UTF-8 comes back as an error rather than
 * content. That was fine while every artifact was Markdown; it stopped being
 * fine once `design-analyst-agent` started exporting `.png` files into
 * `design-resources/` (AC-E2-37a) and they showed up in the artifact list.
 *
 * AC-E3-04a is explicit that those assets are display-only — "chỉ được theo
 * dõi và hiển thị (đường dẫn, danh sách file)" — so a non-previewable
 * artifact is listed, never opened.
 */
const PREVIEWABLE_EXTENSIONS = [
  "md",
  "markdown",
  "txt",
  "json",
  "yaml",
  "yml",
  "svg",
  "csv",
  "ts",
  "tsx",
  "js",
  "jsx",
  "rs",
  "dart",
  "sql",
  "log",
  // BA Output 4 — `<feature>/prototype/index.html`. Đọc như text (xem
  // source), không render: `read_artifact` trả UTF-8 và panel chỉ liệt
  // kê/hiển thị, không execute.
  "html",
  "htm",
];

/** True when `read_artifact` can be expected to return text for this path. */
export function isPreviewableArtifact(path: string): boolean {
  const name = path.split(/[\\/]/).pop() ?? path;
  const dot = name.lastIndexOf(".");
  // No extension at all — treat as text, the same benefit of the doubt the
  // viewer gave every artifact before assets existed.
  if (dot <= 0) return true;
  return PREVIEWABLE_EXTENSIONS.includes(name.slice(dot + 1).toLowerCase());
}
