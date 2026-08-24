import { useState, type MouseEvent } from "react";
import { ChevronRight, File, Folder, FolderOpen, Lock } from "lucide-react";
import { commands, isAppCommandError, type DirEntry } from "@/lib/tauri-client";
import { cn } from "@/lib/utils";
import type { ExplorerContextTarget } from "@/screens/explorer/explorer-types";

function extractErrorMessage(err: unknown): string {
  if (isAppCommandError(err)) return err.message;
  if (err instanceof Error) return err.message;
  return String(err);
}

interface FolderTreeNodeProps {
  entry: DirEntry;
  depth: number;
  selectedPath: string | null;
  onSelectFile: (path: string) => void;
  onContextMenu: (target: ExplorerContextTarget) => void;
}

/** One row of the folder explorer's tree, plus its lazily-loaded children.
 * Restricted files (per the project's `.claude/config/restricted-paths.json`
 * — same source `ImportFilter` reads) show a lock icon and can't be opened;
 * restricted directories still expand normally — the restriction is about
 * content exposure, not directory existence. */
export function FolderTreeNode({ entry, depth, selectedPath, onSelectFile, onContextMenu }: FolderTreeNodeProps) {
  const [expanded, setExpanded] = useState(false);
  const [children, setChildren] = useState<DirEntry[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  function toggleExpand() {
    if (!entry.isDir) return;
    if (expanded) {
      setExpanded(false);
      return;
    }
    setExpanded(true);
    if (children !== null) return;
    setLoading(true);
    setErrorMessage(null);
    commands
      .listDirectory(entry.path)
      .then(setChildren)
      .catch((err) => setErrorMessage(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }

  function handleRowClick() {
    if (entry.isDir) {
      toggleExpand();
      return;
    }
    if (entry.isRestricted) return;
    onSelectFile(entry.path);
  }

  function handleContextMenu(event: MouseEvent<HTMLButtonElement>) {
    if (!entry.isDir || !entry.canModify) return;
    event.preventDefault();
    onContextMenu({
      path: entry.path,
      name: entry.name,
      x: event.clientX,
      y: event.clientY,
    });
  }

  const isSelected = !entry.isDir && selectedPath === entry.path;

  return (
    <div>
      <button
        type="button"
        onClick={handleRowClick}
        onContextMenu={handleContextMenu}
        disabled={!entry.isDir && entry.isRestricted}
        className={cn(
          "flex w-full items-center gap-1 rounded px-1.5 py-1 text-left text-sm hover:bg-muted/60 disabled:cursor-not-allowed disabled:opacity-50",
          isSelected && "bg-muted text-primary",
        )}
        style={{ paddingLeft: `${depth * 16 + 6}px` }}
          title={
            entry.isRestricted
              ? "File bị hạn chế đọc (khớp restricted-paths.json)"
              : !entry.canModify && entry.isDir
                ? "Folder chỉ đọc hoặc thuộc vùng được bảo vệ"
                : entry.name
          }
      >
        {entry.isDir ? (
          <ChevronRight
            className={cn("size-3.5 shrink-0 text-muted-foreground transition-transform", expanded && "rotate-90")}
            aria-hidden="true"
          />
        ) : (
          <span className="inline-block size-3.5 shrink-0" />
        )}
        {entry.isDir ? (
          expanded ? (
            <FolderOpen className="size-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
          ) : (
            <Folder className="size-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
          )
        ) : (
          <File className="size-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
        )}
        <span className="truncate font-mono text-xs">{entry.name}</span>
        {entry.isRestricted && (
          <Lock className="ml-auto size-3 shrink-0 text-muted-foreground" aria-hidden="true" />
        )}
      </button>

      {expanded && entry.isDir && (
        <div>
          {loading && (
            <p
              className="py-1 text-xs text-muted-foreground"
              style={{ paddingLeft: `${(depth + 1) * 16 + 6}px` }}
            >
              Đang tải...
            </p>
          )}
          {errorMessage && (
            <p
              className="py-1 text-xs text-destructive"
              style={{ paddingLeft: `${(depth + 1) * 16 + 6}px` }}
            >
              {errorMessage}
            </p>
          )}
          {children && children.length === 0 && (
            <p
              className="py-1 text-xs text-muted-foreground"
              style={{ paddingLeft: `${(depth + 1) * 16 + 6}px` }}
            >
              (thư mục rỗng)
            </p>
          )}
          {children?.map((child) => (
            <FolderTreeNode
              key={child.path}
              entry={child}
              depth={depth + 1}
              selectedPath={selectedPath}
              onSelectFile={onSelectFile}
              onContextMenu={onContextMenu}
            />
          ))}
        </div>
      )}
    </div>
  );
}
