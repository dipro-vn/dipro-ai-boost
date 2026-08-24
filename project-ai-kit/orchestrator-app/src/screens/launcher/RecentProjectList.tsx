import { FolderOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { RecentProjectEntry } from "@/lib/tauri-client";

interface RecentProjectListProps {
  entries: RecentProjectEntry[];
  loading: boolean;
  openingLabel: string | null;
  onOpen: (entry: RecentProjectEntry) => void;
  onRemove: (entry: RecentProjectEntry) => void;
}

export function RecentProjectList({
  entries,
  loading,
  openingLabel,
  onOpen,
  onRemove,
}: RecentProjectListProps) {
  if (loading) {
    return (
      <div className="flex flex-col gap-2">
        <div className="skeleton h-12 w-full" />
        <div className="skeleton h-12 w-full" />
      </div>
    );
  }

  if (entries.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 py-6 text-center">
        <FolderOpen className="size-8 text-muted-foreground/40" aria-hidden="true" />
        <p className="text-sm text-muted-foreground">
          Chưa có project nào từng mở.
        </p>
      </div>
    );
  }

  return (
    <ul className="flex flex-col gap-1">
      {entries.map((entry) => {
        const isOpening = openingLabel === entry.label;
        return (
          <li
            key={`${entry.agentsRoot}|${entry.docsRoot}|${entry.repositoryRoot}`}
            className="flex items-center justify-between gap-3 rounded-lg border border-border px-3 py-2 transition-colors hover:bg-muted/50"
          >
            <button
              type="button"
              onClick={() => onOpen(entry)}
              disabled={isOpening}
              className="flex flex-1 flex-col items-start text-left disabled:opacity-60"
            >
              <span className="text-sm font-medium">
                {isOpening ? "Đang mở..." : entry.label}
              </span>
              <span className="font-mono text-xs text-muted-foreground">
                {entry.agentsRoot}
              </span>
            </button>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => onRemove(entry)}
            >
              Xoá
            </Button>
          </li>
        );
      })}
    </ul>
  );
}
