import { useCallback, useEffect, useRef, useState } from "react";
import { getCurrentWebview } from "@tauri-apps/api/webview";
import { RefreshCw, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { commands, isAppCommandError, type ExplorerRootEntry } from "@/lib/tauri-client";
import { FolderTree } from "@/screens/explorer/FolderTree";
import { ExplorerContextMenu } from "@/screens/explorer/ExplorerContextMenu";
import { ExplorerDeleteDialog } from "@/screens/explorer/ExplorerDeleteDialog";
import { ExplorerEntryDialog } from "@/screens/explorer/ExplorerEntryDialog";
import { ExplorerRenameDialog } from "@/screens/explorer/ExplorerRenameDialog";
import { ExplorerDeleteFileDialog } from "@/screens/explorer/ExplorerDeleteFileDialog";
import {
  EXPLORER_DIR_PATH_ATTR,
  type ExplorerContextTarget,
  type ExplorerCreateKind,
  type ExplorerEntryTarget,
  type ExplorerFolderTarget,
} from "@/screens/explorer/explorer-types";
import { ArtifactModal } from "@/screens/board/ArtifactModal";
import { cn } from "@/lib/utils";

function extractErrorMessage(err: unknown): string {
  if (isAppCommandError(err)) return err.message;
  if (err instanceof Error) return err.message;
  return String(err);
}

interface FolderExplorerSidebarProps {
  onClose: () => void;
}

/**
 * Left rail, pushed in alongside `WorkflowSidebar` when the floating
 * Explorer button (bottom-left of the Board) is toggled open — browses the
 * real filesystem of the open project, usually as one unified tree at the
 * common ancestor of the 3 project roots (see `getExplorerRoots`).
 *
 * Only reachable from the Board (there is no other entry point — this
 * replaced the earlier full-screen Explorer so there is a single place the
 * feature lives, not two divergent UIs for the same data). Manual refresh
 * only, no live watcher — kept simple on purpose.
 */
export function FolderExplorerSidebar({ onClose }: FolderExplorerSidebarProps) {
  const [roots, setRoots] = useState<ExplorerRootEntry[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [activeRootPath, setActiveRootPath] = useState<string | null>(null);
  const [selectedFilePath, setSelectedFilePath] = useState<string | null>(null);
  const [contextTarget, setContextTarget] = useState<ExplorerContextTarget | null>(null);
  const [createRequest, setCreateRequest] = useState<{
    kind: ExplorerCreateKind;
    target: ExplorerFolderTarget;
  } | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<ExplorerFolderTarget | null>(null);
  const [deleteFileTarget, setDeleteFileTarget] = useState<ExplorerFolderTarget | null>(null);
  const [renameTarget, setRenameTarget] = useState<ExplorerEntryTarget | null>(null);
  const [refreshToken, setRefreshToken] = useState(0);
  /** Folder người dùng bấm gần nhất — đích mặc định của paste. */
  const [activeFolderPath, setActiveFolderPath] = useState<string | null>(null);
  const [dropTargetPath, setDropTargetPath] = useState<string | null>(null);
  const [transferMessage, setTransferMessage] = useState<string | null>(null);
  const [transferError, setTransferError] = useState<string | null>(null);
  const sidebarRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    setLoadError(null);
    commands
      .getExplorerRoots()
      .then((result) => {
        if (cancelled) return;
        setRoots(result);
        setActiveRootPath(result[0]?.path ?? null);
      })
      .catch((err) => {
        if (!cancelled) setLoadError(extractErrorMessage(err));
      });
    return () => {
      cancelled = true;
    };
  }, [refreshToken]);

  function handleContextMenu(target: ExplorerContextTarget) {
    setContextTarget(target);
  }

  function requestCreate(kind: ExplorerCreateKind) {
    if (!contextTarget) return;
    setCreateRequest({
      kind,
      target: { path: contextTarget.path, name: contextTarget.name },
    });
    setContextTarget(null);
  }

  function requestDelete() {
    if (!contextTarget) return;
    const target = { path: contextTarget.path, name: contextTarget.name };
    // Folder đi đường có preview + gõ lại tên; file thì thứ bị xoá đang hiện
    // ngay trước mắt nên chỉ cần xác nhận một nhịp.
    if (contextTarget.isDir) {
      setDeleteTarget(target);
    } else {
      setDeleteFileTarget(target);
    }
    setContextTarget(null);
  }

  function requestRename() {
    if (!contextTarget) return;
    setRenameTarget({
      path: contextTarget.path,
      name: contextTarget.name,
      isDir: contextTarget.isDir,
    });
    setContextTarget(null);
  }

  async function handleRename(target: ExplorerEntryTarget, newName: string) {
    await commands.renameExplorerEntry(target.path, newName);
    // Cây được dựng lại từ đĩa nên path cũ không còn tồn tại; bỏ chọn để
    // ArtifactModal không mở một file vừa bị đổi tên.
    setSelectedFilePath((selected) =>
      selected && isInsidePath(selected, target.path) ? null : selected,
    );
    setActiveFolderPath((current) =>
      current && isInsidePath(current, target.path) ? null : current,
    );
    setRefreshToken((token) => token + 1);
  }

  async function handleCreate(kind: ExplorerCreateKind, target: ExplorerFolderTarget, name: string) {
    if (kind === "file") {
      await commands.createExplorerFile(target.path, name);
    } else {
      await commands.createExplorerFolder(target.path, name);
    }
    setRefreshToken((token) => token + 1);
  }

  function isInsidePath(path: string, parent: string): boolean {
    return path === parent || path.startsWith(`${parent}/`) || path.startsWith(`${parent}\\`);
  }

  function handleDeleted(target: ExplorerFolderTarget) {
    setSelectedFilePath((selected) => (selected && isInsidePath(selected, target.path) ? null : selected));
    setActiveFolderPath((current) => (current && isInsidePath(current, target.path) ? null : current));
    setRefreshToken((token) => token + 1);
  }

  /** Đích của một cú THẢ: đúng folder dưới con trỏ, không trúng folder nào thì
   * là root đang mở.
   *
   * Cố tình KHÔNG lùi về `activeFolderPath`: thả là thao tác theo vị trí, nên
   * chuyển hướng nó sang một folder người dùng chỉ bấm lúc trước là âm thầm bỏ
   * file sai chỗ. Đó chính là lý do thả lên hàng root lại báo "đã chép vào
   * <subfolder>". */
  const dropDestination = useCallback(
    (path: string | null) => path ?? activeRootPath,
    [activeRootPath],
  );

  /** Đích của một cú DÁN: không có toạ độ nào để bám, nên đi theo lựa chọn —
   * folder vừa bấm, không có thì root. */
  const pasteDestination = useCallback(
    () => activeFolderPath ?? activeRootPath,
    [activeFolderPath, activeRootPath],
  );

  /** Sự kiện kéo-thả của Tauri chỉ đưa toạ độ vật lý, không đưa phần tử DOM —
   * nên phải hit-test ngược để biết đang ở trên folder nào. */
  const dirPathAtPoint = useCallback((position: { x: number; y: number }) => {
    const ratio = window.devicePixelRatio || 1;
    const element = document.elementFromPoint(position.x / ratio, position.y / ratio);
    if (!element || !sidebarRef.current?.contains(element)) return { inside: false, path: null };
    const row = element.closest(`[${EXPLORER_DIR_PATH_ATTR}]`);
    return { inside: true, path: row?.getAttribute(EXPLORER_DIR_PATH_ATTR) ?? null };
  }, []);

  useEffect(() => {
    let disposed = false;
    let unlisten: (() => void) | undefined;

    void getCurrentWebview()
      .onDragDropEvent((event) => {
        const payload = event.payload;
        if (payload.type === "leave") {
          setDropTargetPath(null);
          return;
        }
        if (payload.type === "enter" || payload.type === "over") {
          const hit = dirPathAtPoint(payload.position);
          setDropTargetPath(hit.inside ? dropDestination(hit.path) : null);
          return;
        }
        if (payload.type !== "drop") return;

        const hit = dirPathAtPoint(payload.position);
        setDropTargetPath(null);
        // Thả ra ngoài Explorer thì không phải việc của nó — đừng nuốt file
        // của người ta vào một folder họ không nhắm tới.
        if (!hit.inside || payload.paths.length === 0) return;
        const destination = dropDestination(hit.path);
        if (!destination) {
          // Im lặng ở đây nghĩa là người dùng thả file rồi không thấy gì xảy
          // ra, không biết vì sao.
          setTransferMessage(null);
          setTransferError("Chưa xác định được thư mục đích để chép file vào.");
          return;
        }

        setTransferError(null);
        setTransferMessage(`Đang chép ${payload.paths.length} file...`);
        commands
          .importExplorerPaths(destination, payload.paths)
          .then((created) => {
            setTransferMessage(`Đã chép ${created.length} file vào ${destination}`);
            setRefreshToken((token) => token + 1);
          })
          .catch((err) => {
            setTransferMessage(null);
            setTransferError(extractErrorMessage(err));
          });
      })
      .then((fn) => {
        if (disposed) fn();
        else unlisten = fn;
      });

    return () => {
      disposed = true;
      unlisten?.();
    };
  }, [dirPathAtPoint, dropDestination]);

  useEffect(() => {
    if (!transferMessage) return;
    const timer = window.setTimeout(() => setTransferMessage(null), 5_000);
    return () => window.clearTimeout(timer);
  }, [transferMessage]);

  useEffect(() => {
    async function handlePaste(event: ClipboardEvent) {
      // Paste vào ô nhập liệu là paste chữ, không phải thả file vào Explorer.
      const node = event.target as HTMLElement | null;
      if (node?.closest("input, textarea, [contenteditable='true']")) return;

      const destination = pasteDestination();
      if (!destination) return;

      const files = Array.from(event.clipboardData?.files ?? []);
      // Copy file trong Finder rồi paste vào webview không phải lúc nào cũng
      // ra `files`: WebKit hay đưa sang dưới dạng đường dẫn text. Nhận cả hai,
      // vì nếu chỉ nhận `files` thì Cmd+V sẽ im lặng không làm gì.
      const pastedPaths = (event.clipboardData?.getData("text/plain") ?? "")
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter((line) => line.length > 0)
        .filter((line) => line.startsWith("/") || /^[A-Za-z]:[\\/]/.test(line));

      if (files.length === 0 && pastedPaths.length === 0) {
        // Không nuốt phím: có thể người dùng đang paste chữ ở chỗ khác.
        return;
      }

      event.preventDefault();
      setTransferError(null);
      try {
        if (files.length > 0) {
          setTransferMessage(`Đang dán ${files.length} file...`);
          for (const file of files) {
            const bytes = Array.from(new Uint8Array(await file.arrayBuffer()));
            await commands.writeExplorerFile(destination, file.name, bytes);
          }
          setTransferMessage(`Đã dán ${files.length} file vào ${destination}`);
        } else {
          setTransferMessage(`Đang chép ${pastedPaths.length} file...`);
          const created = await commands.importExplorerPaths(destination, pastedPaths);
          setTransferMessage(`Đã chép ${created.length} file vào ${destination}`);
        }
        setRefreshToken((token) => token + 1);
      } catch (err) {
        setTransferMessage(null);
        setTransferError(extractErrorMessage(err));
      }
    }

    document.addEventListener("paste", handlePaste);
    return () => document.removeEventListener("paste", handlePaste);
  }, [pasteDestination]);

  return (
    <div ref={sidebarRef} className="flex w-72 shrink-0 flex-col border-r border-border">
      <div className="flex items-center justify-between gap-2 border-b border-border p-3">
        <span className="text-sm font-semibold">Explorer</span>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setRefreshToken((t) => t + 1)}
            disabled={!roots}
            aria-label="Làm mới"
            title="Làm mới"
          >
            <RefreshCw className="size-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Đóng Explorer">
            <X className="size-4" />
          </Button>
        </div>
      </div>

      {/* Chỉ nói về DÁN. Thả thì đi theo con trỏ và đã có folder sáng lên báo
          đích, nên gộp hai thứ vào một nhãn là hứa sai một trong hai. */}
      {(activeFolderPath ?? activeRootPath) && (
        <div className="border-b border-border px-3 py-1.5 text-[11px] text-muted-foreground">
          Dán vào:{" "}
          <span className="font-mono text-foreground" title={activeFolderPath ?? activeRootPath ?? ""}>
            {(activeFolderPath ?? activeRootPath ?? "").split(/[\\/]/).pop()}
          </span>
        </div>
      )}
      {(transferMessage || transferError) && (
        <div
          className={cn(
            "border-b border-border px-3 py-1.5 text-[11px]",
            transferError ? "text-destructive" : "text-muted-foreground",
          )}
        >
          {transferError ?? transferMessage}
        </div>
      )}

      <div className="flex-1 overflow-hidden p-2">
        {loadError && (
          <Alert variant="destructive">
            <AlertTitle>Không lấy được thông tin project</AlertTitle>
            <AlertDescription>{loadError}</AlertDescription>
          </Alert>
        )}

        {!loadError && !roots && <p className="p-2 text-sm text-muted-foreground">Đang tải...</p>}

        {/* 1 root (thường gặp — mọi project có 1 folder cha chung): 1 cây
            duy nhất, không cần tabs. */}
        {roots && roots.length === 1 && (
          <div className="h-full overflow-hidden rounded-lg border border-border">
            <ScrollArea className="h-full">
              <FolderTree
                key={`${roots[0].path}:${refreshToken}`}
                rootPath={roots[0].path}
                rootLabel={roots[0].label}
                rootCanModify={roots[0].canModify}
                selectedPath={selectedFilePath}
                onSelectFile={setSelectedFilePath}
                onSelectFolder={setActiveFolderPath}
                onContextMenu={handleContextMenu}
                dropTargetPath={dropTargetPath}
              />
            </ScrollArea>
          </div>
        )}

        {/* Nhiều root (hiếm — không có folder cha chung): fallback tabs,
            mỗi root 1 tree riêng. */}
        {roots && roots.length > 1 && activeRootPath && (
          <Tabs value={activeRootPath} onValueChange={setActiveRootPath} className="h-full">
            <TabsList>
              {roots.map((root) => (
                <TabsTrigger key={root.path} value={root.path}>
                  {root.label}
                </TabsTrigger>
              ))}
            </TabsList>

            {roots.map((root) => (
              <TabsContent
                key={root.path}
                value={root.path}
                className="overflow-hidden rounded-lg border border-border"
              >
                <ScrollArea className="h-full">
                  <FolderTree
                    key={`${root.path}:${refreshToken}`}
                    rootPath={root.path}
                    rootLabel={root.label}
                    rootCanModify={root.canModify}
                    selectedPath={selectedFilePath}
                    onSelectFile={setSelectedFilePath}
                    onSelectFolder={setActiveFolderPath}
                    onContextMenu={handleContextMenu}
                    dropTargetPath={dropTargetPath}
                  />
                </ScrollArea>
              </TabsContent>
            ))}
          </Tabs>
        )}
      </div>

      <ExplorerContextMenu
        target={contextTarget}
        onCreate={requestCreate}
        onRename={requestRename}
        onDelete={requestDelete}
        onClose={() => setContextTarget(null)}
      />
      <ExplorerEntryDialog
        kind={createRequest?.kind ?? null}
        target={createRequest?.target ?? null}
        onClose={() => setCreateRequest(null)}
        onCreate={handleCreate}
      />
      <ExplorerRenameDialog
        target={renameTarget}
        onClose={() => setRenameTarget(null)}
        onRename={handleRename}
      />
      <ExplorerDeleteDialog
        target={deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onDeleted={handleDeleted}
      />
      <ExplorerDeleteFileDialog
        target={deleteFileTarget}
        onClose={() => setDeleteFileTarget(null)}
        onDeleted={handleDeleted}
      />
      <ArtifactModal path={selectedFilePath} onClose={() => setSelectedFilePath(null)} />
    </div>
  );
}
