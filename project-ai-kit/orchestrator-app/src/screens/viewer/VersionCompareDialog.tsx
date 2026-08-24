import { useEffect, useState } from "react";
import DiffViewer from "react-diff-viewer-continued";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ONE_DARK_PRISM_THEME, languageForPath } from "@/lib/code-theme";
import {
  commands,
  isAppCommandError,
  type DiffResult,
  type VersionRef,
} from "@/lib/tauri-client";

function extractErrorMessage(err: unknown): string {
  if (isAppCommandError(err)) return err.message;
  if (err instanceof Error) return err.message;
  return String(err);
}

function sourceLabel(source: DiffResult["source"]): string {
  switch (source) {
    case "git":
      return "Đang so sánh theo lịch sử git";
    case "snapshot":
      return "Đang so sánh theo snapshot cục bộ (không phải git repo)";
    case "current":
      return "";
  }
}

interface VersionCompareDialogProps {
  path: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/** AC-E3-21/22 — chọn 2 phiên bản của 1 artifact và xem diff side-by-side. */
export function VersionCompareDialog({
  path,
  open,
  onOpenChange,
}: VersionCompareDialogProps) {
  const [versions, setVersions] = useState<VersionRef[] | null>(null);
  const [listError, setListError] = useState<string | null>(null);
  const [fromId, setFromId] = useState<string | null>(null);
  const [toId, setToId] = useState<string | null>(null);

  const [diff, setDiff] = useState<DiffResult | null>(null);
  const [diffError, setDiffError] = useState<string | null>(null);
  const [diffLoading, setDiffLoading] = useState(false);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    setVersions(null);
    setListError(null);
    setFromId(null);
    setToId(null);
    setDiff(null);
    setDiffError(null);

    commands
      .listArtifactVersions(path)
      .then((result) => {
        if (cancelled) return;
        setVersions(result);
        // Default to comparing the 2 most recent versions when there are
        // enough to compare — result[0] is always "current".
        if (result.length >= 2) {
          setFromId(result[1].id);
          setToId(result[0].id);
        }
      })
      .catch((err) => {
        if (!cancelled) setListError(extractErrorMessage(err));
      });

    return () => {
      cancelled = true;
    };
  }, [open, path]);

  useEffect(() => {
    if (!fromId || !toId) return;
    let cancelled = false;
    setDiffLoading(true);
    setDiffError(null);

    commands
      .diffArtifact(path, fromId, toId)
      .then((result) => {
        if (!cancelled) setDiff(result);
      })
      .catch((err) => {
        if (!cancelled) setDiffError(extractErrorMessage(err));
      })
      .finally(() => {
        if (!cancelled) setDiffLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [path, fromId, toId]);

  const canCompare = (versions?.length ?? 0) >= 2;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex h-[85vh] max-w-4xl flex-col overflow-hidden sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle>So sánh phiên bản</DialogTitle>
          <DialogDescription className="truncate font-mono text-xs">
            {path}
          </DialogDescription>
        </DialogHeader>

        {listError && (
          <Alert variant="destructive">
            <AlertTitle>Không lấy được danh sách phiên bản</AlertTitle>
            <AlertDescription>{listError}</AlertDescription>
          </Alert>
        )}

        {versions && !canCompare && (
          <Alert>
            <AlertTitle>Chưa có phiên bản để so sánh</AlertTitle>
            <AlertDescription>
              Artifact này mới chỉ có 1 phiên bản (hiện tại) — cần ít nhất 2
              phiên bản để so sánh.
            </AlertDescription>
          </Alert>
        )}

        {versions && canCompare && (
          <>
            <div className="flex items-center gap-2">
              <Select value={fromId ?? undefined} onValueChange={setFromId}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Từ phiên bản..." />
                </SelectTrigger>
                <SelectContent>
                  {versions.map((v) => (
                    <SelectItem key={v.id} value={v.id}>
                      {v.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <span className="text-xs text-muted-foreground">→</span>
              <Select value={toId ?? undefined} onValueChange={setToId}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Đến phiên bản..." />
                </SelectTrigger>
                <SelectContent>
                  {versions.map((v) => (
                    <SelectItem key={v.id} value={v.id}>
                      {v.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {diff && (
              <p className="text-xs text-muted-foreground">
                {sourceLabel(diff.source)}
              </p>
            )}

            <div className="min-h-0 flex-1 overflow-auto rounded-lg border border-border">
              {diffLoading && (
                <div className="flex flex-col gap-3 p-6">
                  <div className="skeleton h-5 w-40" />
                  <div className="skeleton h-4 w-full" />
                  <div className="skeleton h-4 w-11/12" />
                  <div className="skeleton h-4 w-4/5" />
                </div>
              )}

              {diffError && (
                <div className="p-4">
                  <Alert variant="destructive">
                    <AlertTitle>Không tính được diff</AlertTitle>
                    <AlertDescription>{diffError}</AlertDescription>
                  </Alert>
                </div>
              )}

              {diff && !diffLoading && !diffError && (
                <DiffViewer
                  oldValue={diff.fromContent}
                  newValue={diff.toContent}
                  splitView
                  useDarkTheme
                  highlightLanguage={languageForPath(path)}
                  highlightTheme={ONE_DARK_PRISM_THEME}
                  hideLineNumbers={false}
                />
              )}
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
