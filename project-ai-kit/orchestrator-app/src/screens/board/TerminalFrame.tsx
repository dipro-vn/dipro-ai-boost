import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface TerminalFrameProps {
  title: string;
  children: ReactNode;
  className?: string;
}

/**
 * Shared terminal chrome (dark surface + traffic-light header) used by both
 * the BA panel's live log and the generic panel's "can't run yet"
 * placeholder, so every node's action pane has the same visual "terminal
 * slot" whether or not it currently has anything to show.
 *
 * The body background is a fixed dark surface regardless of the app's
 * light/dark theme (a terminal reads as a terminal either way) — so text
 * inside MUST use the fixed `text-zinc-*` palette below, never
 * theme-relative tokens like `text-foreground`/`text-muted-foreground`,
 * which would go dark-on-dark in light mode.
 */
export function TerminalFrame({ title, children, className }: TerminalFrameProps) {
  return (
    <div className={cn("flex flex-col overflow-hidden rounded-lg border border-border", className)}>
      <div className="flex items-center gap-1.5 border-b border-zinc-800 bg-zinc-900 px-3 py-1.5">
        <span className="size-2.5 rounded-full bg-red-500/70" aria-hidden="true" />
        <span className="size-2.5 rounded-full bg-yellow-500/70" aria-hidden="true" />
        <span className="size-2.5 rounded-full bg-green-500/70" aria-hidden="true" />
        <span className="ml-2 truncate font-mono text-[11px] text-zinc-400">{title}</span>
      </div>
      <div className="min-h-0 flex-1 bg-zinc-950">{children}</div>
    </div>
  );
}
