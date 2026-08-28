import { FileText } from "lucide-react";
import { useEffect, useState } from "react";
import { isPreviewableArtifact } from "@/lib/artifact-preview";
import { commands, isAppCommandError, type NodeDetail } from "@/lib/tauri-client";
import { useAppStore } from "@/state/app-store";

interface ArtifactSummaryProps {
  feature: string;
  slotId: string;
  /** Bump this to force a refetch (e.g. right after a run finishes) without
   * waiting for `feature`/`slotId` to change. */
  refreshKey?: number;
  /** Opens the file in a modal on the Board. Falls back to the full-screen
   * viewer when omitted. */
  onOpenArtifact?: (path: string) => void;
}

/** Shared by every step panel (`ba` and generic) — artifact list + cost +
 * last-updated, fetched via `get_node_detail`. */
export function ArtifactSummary({
  feature,
  slotId,
  refreshKey,
  onOpenArtifact,
}: ArtifactSummaryProps) {
  const openArtifact = useAppStore((s) => s.openArtifact);
  const open = onOpenArtifact ?? openArtifact;
  const [detail, setDetail] = useState<NodeDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setErrorMessage(null);
    commands
      .getNodeDetail(feature, slotId)
      .then((result) => {
        if (!cancelled) setDetail(result);
      })
      .catch((err) => {
        if (!cancelled) {
          setErrorMessage(isAppCommandError(err) ? err.message : String(err));
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [feature, slotId, refreshKey]);

  if (loading) {
    return (
      <div className="flex flex-col gap-2">
        <div className="skeleton h-3 w-16" />
        <div className="skeleton h-4 w-40" />
        <div className="skeleton h-3 w-full" />
        <div className="skeleton h-3 w-full" />
      </div>
    );
  }
  if (errorMessage) {
    return <p className="text-xs text-destructive">{errorMessage}</p>;
  }
  if (!detail) return null;

  return (
    <div className="flex flex-col gap-2">
      <div>
        <h4 className="mb-1.5 text-xs font-medium text-muted-foreground">Artifact</h4>
        {detail.artifacts.length === 0 ? (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <FileText className="size-3.5 text-muted-foreground/50" aria-hidden="true" />
            Chưa có artifact nào.
          </div>
        ) : (
          <ul className="flex flex-col gap-1">
            {detail.artifacts.map((artifact) =>
              isPreviewableArtifact(artifact.path) ? (
                <li key={artifact.path}>
                  <button
                    type="button"
                    onClick={() => open(artifact.path)}
                    className="text-left font-mono text-xs text-primary underline-offset-2 hover:underline"
                  >
                    {artifact.label}
                  </button>
                </li>
              ) : (
                // Binary asset (exported .png and friends): listed with its
                // path, not clickable — `read_artifact` decodes UTF-8 and
                // would just throw. AC-E3-04a wants these visible, not
                // openable.
                <li key={artifact.path}>
                  <span
                    title={artifact.path}
                    className="font-mono text-xs text-muted-foreground"
                  >
                    {artifact.label}
                  </span>
                </li>
              ),
            )}
          </ul>
        )}
      </div>
      <div className="flex flex-col gap-1 text-xs">
        <div className="flex justify-between">
          <span className="text-muted-foreground">Thời gian</span>
          <span>{detail.updatedAt ?? "—"}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Cost</span>
          <span>{detail.costUsd != null ? `$${detail.costUsd.toFixed(4)}` : "—"}</span>
        </div>
      </div>
    </div>
  );
}
