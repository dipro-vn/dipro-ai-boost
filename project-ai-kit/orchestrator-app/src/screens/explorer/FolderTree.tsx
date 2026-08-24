import { useEffect, useState } from "react";
import { commands, isAppCommandError, type DirEntry } from "@/lib/tauri-client";
import type { ExplorerContextTarget } from "@/screens/explorer/explorer-types";
import { FolderTreeNode } from "@/screens/explorer/FolderTreeNode";

function extractErrorMessage(err: unknown): string {
  if (isAppCommandError(err)) return err.message;
  if (err instanceof Error) return err.message;
  return String(err);
}

interface FolderTreeProps {
  rootPath: string;
  selectedPath: string | null;
  onSelectFile: (path: string) => void;
  onContextMenu: (target: ExplorerContextTarget) => void;
}

/** One root's tree (docsRoot or repositoryRoot) — top-level listing only;
 * every deeper level is fetched lazily by `FolderTreeNode` as the user
 * expands it. The parent gives this a `key` that changes on refresh, so
 * "Làm mới" remounts (and thus fully resets) the whole subtree instead of
 * needing a reload signal threaded through every node. */
export function FolderTree({ rootPath, selectedPath, onSelectFile, onContextMenu }: FolderTreeProps) {
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

  if (errorMessage) {
    return <p className="p-3 text-sm text-destructive">{errorMessage}</p>;
  }

  if (entries === null) {
    return <p className="p-3 text-sm text-muted-foreground">Đang tải...</p>;
  }

  if (entries.length === 0) {
    return <p className="p-3 text-sm text-muted-foreground">Thư mục rỗng.</p>;
  }

  return (
    <div className="py-1">
      {entries.map((entry) => (
        <FolderTreeNode
          key={entry.path}
          entry={entry}
          depth={0}
          selectedPath={selectedPath}
          onSelectFile={onSelectFile}
          onContextMenu={onContextMenu}
        />
      ))}
    </div>
  );
}
