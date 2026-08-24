import { useEffect, useState } from "react";
import { Maximize2 } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { commands, type ArtifactContent } from "@/lib/tauri-client";
import { extractErrorMessage } from "@/screens/board/agent-run-shared";
import { ArtifactContentView } from "@/screens/viewer/ArtifactContentView";
import { useAppStore } from "@/state/app-store";

interface ArtifactModalProps {
  /** Absolute artifact path; `null` closes the modal. */
  path: string | null;
  onClose: () => void;
  /** Nội dung có sẵn (snapshot đã khoá) — khi truyền vào, modal render
   * thẳng chuỗi này thay vì đọc `path` từ đĩa, vì file trên đĩa có thể đã
   * đổi hoặc không còn tồn tại. */
  content?: string;
  /** Thay cho `path` ở dòng mô tả, để nói rõ đang xem bản chụp nào. */
  subtitle?: string;
}

function fileName(path: string): string {
  return path.split("/").pop() ?? path;
}

/**
 * Reads a generated artifact without leaving the Board — opened
 * automatically when a run finishes and produced one, and by clicking any
 * file in a node's artifact list.
 *
 * Deliberately not a replacement for `ArtifactViewerScreen`: that one owns
 * version comparison and the full-height reading experience, and this modal
 * links to it. Both render through `ArtifactContentView`, so a 2000-line
 * SPEC.md is virtualized in either.
 */
export function ArtifactModal({ path, onClose, content, subtitle }: ArtifactModalProps) {
  const openArtifact = useAppStore((s) => s.openArtifact);
  const [artifact, setArtifact] = useState<ArtifactContent | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    setArtifact(null);
    setErrorMessage(null);
    if (!path) return;
    if (content !== undefined) {
      setArtifact({ content, sizeBytes: content.length, lineCount: content.split("\n").length });
      return;
    }
    let cancelled = false;
    commands
      .readArtifact(path)
      .then((result) => {
        if (!cancelled) setArtifact(result);
      })
      .catch((err) => {
        if (!cancelled) setErrorMessage(extractErrorMessage(err));
      });
    return () => {
      cancelled = true;
    };
  }, [path, content]);

  return (
    <Dialog open={path !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="flex h-[85vh] max-w-4xl flex-col overflow-hidden sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle>{path ? fileName(path) : ""}</DialogTitle>
          <DialogDescription className={cn("truncate text-xs", subtitle === undefined && "font-mono")}>
            {subtitle ?? path}
          </DialogDescription>
        </DialogHeader>

        <div className="min-h-64 flex-1 overflow-hidden rounded-lg border border-border">
          {errorMessage ? (
            <div className="p-4">
              <Alert variant="destructive">
                <AlertTitle>Không đọc được artifact</AlertTitle>
                <AlertDescription>{errorMessage}</AlertDescription>
              </Alert>
            </div>
          ) : artifact && path ? (
            <ArtifactContentView path={path} content={artifact.content} lineCount={artifact.lineCount} />
          ) : (
            <div className="flex flex-col gap-3 p-6">
              <div className="skeleton h-5 w-56" />
              <div className="skeleton h-4 w-full" />
              <div className="skeleton h-4 w-11/12" />
              <div className="skeleton h-4 w-4/5" />
            </div>
          )}
        </div>

        {content === undefined && (
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                if (path) openArtifact(path);
                onClose();
              }}
              disabled={!path}
            >
              <Maximize2 />
              Mở toàn màn hình
            </Button>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  );
}
