import DiffViewer from "react-diff-viewer-continued";
import { ONE_DARK_PRISM_THEME, languageForPath } from "@/lib/code-theme";

interface DiffViewProps {
  oldValue: string;
  newValue: string;
  /** Đường dẫn file, chỉ dùng để suy ra ngôn ngữ tô màu. */
  path?: string;
}

/**
 * AC-E4-25 — thin wrapper around `react-diff-viewer-continued` taking raw
 * content directly, unlike `VersionCompareDialog` (which is wired to
 * `commands.diffArtifact`'s version-id-based lookup). A violation's "old"
 * content already lives in `FileViolation.lockedContent` — no version id
 * to look up, so that heavier component doesn't fit here.
 *
 * `useDarkTheme` cố định `true`: diff dùng chung bảng màu One Dark với mọi
 * vùng code khác trong app, không đổi theo light/dark mode (xem
 * `lib/code-theme.ts`).
 */
export function DiffView({ oldValue, newValue, path }: DiffViewProps) {
  return (
    <DiffViewer
      oldValue={oldValue}
      newValue={newValue}
      splitView
      useDarkTheme
      highlightLanguage={path ? languageForPath(path) : undefined}
      highlightTheme={ONE_DARK_PRISM_THEME}
      hideLineNumbers={false}
    />
  );
}
