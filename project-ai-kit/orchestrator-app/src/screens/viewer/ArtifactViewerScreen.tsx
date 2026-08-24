import { useEffect, useState } from "react";
import { FileText, GitCompare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  commands,
  isAppCommandError,
  type ArtifactContent,
} from "@/lib/tauri-client";
import { useAppStore } from "@/state/app-store";
import { ArtifactContentView } from "@/screens/viewer/ArtifactContentView";
import { VersionCompareDialog } from "@/screens/viewer/VersionCompareDialog";
import { ScreenHeader } from "@/components/shell/ScreenHeader";

function extractErrorMessage(err: unknown): string {
  if (isAppCommandError(err)) return err.message;
  if (err instanceof Error) return err.message;
  return String(err);
}

export function ArtifactViewerScreen() {
  const path = useAppStore((s) => s.viewerTarget);
  const setScreen = useAppStore((s) => s.setScreen);

  const [artifact, setArtifact] = useState<ArtifactContent | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [compareOpen, setCompareOpen] = useState(false);

  useEffect(() => {
    if (!path) return;
    let cancelled = false;
    setLoading(true);
    setErrorMessage(null);
    setArtifact(null);

    commands
      .readArtifact(path)
      .then((result) => {
        if (!cancelled) setArtifact(result);
      })
      .catch((err) => {
        if (!cancelled) setErrorMessage(extractErrorMessage(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [path]);

  if (!path) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2 text-center text-sm text-muted-foreground">
        <FileText className="size-10 text-muted-foreground/40" aria-hidden="true" />
        <span>Chưa chọn artifact nào.</span>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="px-4 pt-3">
        <ScreenHeader
          title={path.split("/").pop() ?? path}
          description={path}
          icon={FileText}
          onBack={() => setScreen("board")}
          actions={
            <Button variant="outline" size="sm" onClick={() => setCompareOpen(true)}>
              <GitCompare />
              So sánh phiên bản
            </Button>
          }
        />
      </div>

      <VersionCompareDialog
        path={path}
        open={compareOpen}
        onOpenChange={setCompareOpen}
      />

      <div className="flex-1 overflow-hidden">
        {loading && (
          <div className="flex flex-col gap-3 p-6">
            <div className="skeleton h-5 w-56" />
            <div className="skeleton h-4 w-full" />
            <div className="skeleton h-4 w-11/12" />
            <div className="skeleton h-4 w-4/5" />
          </div>
        )}

        {errorMessage && (
          <div className="p-4">
            <Alert variant="destructive">
              <AlertTitle>Không đọc được artifact</AlertTitle>
              <AlertDescription>{errorMessage}</AlertDescription>
            </Alert>
          </div>
        )}

        {artifact && (
          <ArtifactContentView path={path} content={artifact.content} lineCount={artifact.lineCount} />
        )}
      </div>
    </div>
  );
}
