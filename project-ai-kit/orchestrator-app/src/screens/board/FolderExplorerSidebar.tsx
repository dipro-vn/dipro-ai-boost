import { useEffect, useState } from "react";
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
import type {
  ExplorerContextTarget,
  ExplorerCreateKind,
  ExplorerFolderTarget,
} from "@/screens/explorer/explorer-types";
import { ArtifactModal } from "@/screens/board/ArtifactModal";

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
  const [refreshToken, setRefreshToken] = useState(0);

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
    setDeleteTarget({ path: contextTarget.path, name: contextTarget.name });
    setContextTarget(null);
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
    setRefreshToken((token) => token + 1);
  }

  return (
    <div className="flex w-72 shrink-0 flex-col border-r border-border">
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
                selectedPath={selectedFilePath}
                onSelectFile={setSelectedFilePath}
                onContextMenu={handleContextMenu}
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
                    selectedPath={selectedFilePath}
                    onSelectFile={setSelectedFilePath}
                    onContextMenu={handleContextMenu}
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
        onDelete={requestDelete}
        onClose={() => setContextTarget(null)}
      />
      <ExplorerEntryDialog
        kind={createRequest?.kind ?? null}
        target={createRequest?.target ?? null}
        onClose={() => setCreateRequest(null)}
        onCreate={handleCreate}
      />
      <ExplorerDeleteDialog
        target={deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onDeleted={handleDeleted}
      />
      <ArtifactModal path={selectedFilePath} onClose={() => setSelectedFilePath(null)} />
    </div>
  );
}
