import { useEffect, useState, type MouseEvent } from "react";
import { FolderOpen } from "lucide-react";
import { commands, isAppCommandError, type DirEntry } from "@/lib/tauri-client";
import { cn } from "@/lib/utils";
import {
  EXPLORER_DIR_PATH_ATTR,
  type ExplorerContextTarget,
} from "@/screens/explorer/explorer-types";
import { FolderTreeNode } from "@/screens/explorer/FolderTreeNode";

function extractErrorMessage(err: unknown): string {
  if (isAppCommandError(err)) return err.message;
  if (err instanceof Error) return err.message;
  return String(err);
}

interface FolderTreeProps {
  rootPath: string;
  rootLabel: string;
  /** Root có ghi được không — quyết định hàng root có menu và có nhận thả
   * file hay không. Xem `ExplorerRootEntry.canModify`. */
  rootCanModify: boolean;
  selectedPath: string | null;
  onSelectFile: (path: string) => void;
  onSelectFolder: (path: string) => void;
  onContextMenu: (target: ExplorerContextTarget) => void;
  dropTargetPath: string | null;
}

/** One root's tree (docsRoot or repositoryRoot) — top-level listing only;
 * every deeper level is fetched lazily by `FolderTreeNode` as the user
 * expands it. The parent gives this a `key` that changes on refresh, so
 * "Làm mới" remounts (and thus fully resets) the whole subtree instead of
 * needing a reload signal threaded through every node. */
export function FolderTree({
  rootPath,
  rootLabel,
  rootCanModify,
  selectedPath,
  onSelectFile,
  onSelectFolder,
  onContextMenu,
  dropTargetPath,
}: FolderTreeProps) {
  const [entries, setEntries] = useState<DirEntry[] | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setEntries(null);
    setErrorMessage(null);
    commands
      .listDirectory(rootPath)
      .then((result) => {
        if (!cancelled) setEntries(result);
      })
      .catch((err) => {
        if (!cancelled) setErrorMessage(extractErrorMessage(err));
      });
    return () => {
      cancelled = true;
    };
  }, [rootPath]);

  function handleRootContextMenu(event: MouseEvent<HTMLButtonElement>) {
    if (!rootCanModify) return;
    event.preventDefault();
    onContextMenu({
      path: rootPath,
      name: rootLabel,
      isDir: true,
      x: event.clientX,
      y: event.clientY,
    });
  }

  // Hàng cho chính root: trước đây cây chỉ vẽ các con của nó, nên không có gì
  // để chuột phải và cũng không có phần tử nào để hit-test lúc thả file — tạo
  // hay thả thẳng vào thư mục gốc của project là bất khả thi.
  const rootRow = (
    <button
      type="button"
      onClick={() => rootCanModify && onSelectFolder(rootPath)}
      onContextMenu={handleRootContextMenu}
      // Luôn nhận thả, kể cả khi chỉ đọc: bỏ thuộc tính này đi thì hit-test
      // trượt hàng root và cú thả bị chuyển hướng đi nơi khác. Ghi được hay
      // không để backend trả lời bằng một lỗi nói rõ.
      {...{ [EXPLORER_DIR_PATH_ATTR]: rootPath }}
      title={rootCanModify ? rootPath : `${rootPath} (không ghi được vào thư mục này)`}
      className={cn(
        "flex w-full items-center gap-1 rounded px-1.5 py-1 text-left hover:bg-muted/60",
        dropTargetPath === rootPath && "bg-primary/15 ring-1 ring-primary/60",
      )}
    >
      <FolderOpen className="size-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
      <span className="truncate text-xs font-semibold">{rootLabel}</span>
      {!rootCanModify && (
        <span className="ml-auto shrink-0 text-[10px] text-muted-foreground">chỉ đọc</span>
      )}
    </button>
  );

  return (
    <div className="py-1">
      {rootRow}
      {errorMessage && <p className="px-3 py-2 text-sm text-destructive">{errorMessage}</p>}
      {!errorMessage && entries === null && (
        <p className="px-3 py-2 text-sm text-muted-foreground">Đang tải...</p>
      )}
      {!errorMessage && entries?.length === 0 && (
        <p className="px-3 py-2 text-sm text-muted-foreground">(thư mục rỗng)</p>
      )}
      {entries?.map((entry) => (
        <FolderTreeNode
          key={entry.path}
          entry={entry}
          depth={1}
          selectedPath={selectedPath}
          onSelectFile={onSelectFile}
          onSelectFolder={onSelectFolder}
          onContextMenu={onContextMenu}
          dropTargetPath={dropTargetPath}
        />
      ))}
    </div>
  );
}
