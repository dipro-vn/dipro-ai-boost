import { useState } from "react";
import { ChartColumn, FolderSync, Settings, Workflow } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { SwitchProjectDialog } from "@/components/shell/SwitchProjectDialog";
import { ThemeToggle } from "@/components/shell/ThemeToggle";
import { useAppStore } from "@/state/app-store";

export function TopBar() {
  const screen = useAppStore((s) => s.screen);
  const setScreen = useAppStore((s) => s.setScreen);
  const projectLabel = useAppStore((s) => s.projectLabel);
  const [switchOpen, setSwitchOpen] = useState(false);

  const inProject = screen !== "launcher";

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-border px-4">
      <div className="flex min-w-0 items-center gap-2.5">
        <span className="flex size-7 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Workflow className="size-4" aria-hidden="true" />
        </span>
        <span className="shrink-0 text-sm font-semibold">Agent Pipeline Orchestrator</span>
        {/* Which project is open was previously nowhere on screen — with
            switching, knowing it becomes essential. */}
        {inProject && projectLabel && (
          <>
            <Separator orientation="vertical" className="h-4" />
            <span className="truncate text-sm text-muted-foreground" title={projectLabel}>
              {projectLabel}
            </span>
          </>
        )}
      </div>
      <div className="flex items-center gap-1">
        {/* Settings needs an open project (config.json lives under it) —
            hidden on the launcher. */}
        {inProject && (
          <>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="icon" onClick={() => setSwitchOpen(true)} aria-label="Đổi project">
                  <FolderSync />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Đổi project</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className={cn(screen === "reports" && "bg-muted text-primary")}
                  onClick={() => setScreen("reports")}
                  aria-label="Mở Cost & Reports"
                >
                  <ChartColumn />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Cost &amp; Reports</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className={cn(screen === "settings" && "bg-muted text-primary")}
                  onClick={() => setScreen("settings")}
                  aria-label="Mở Settings"
                >
                  <Settings />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Settings</TooltipContent>
            </Tooltip>
          </>
        )}
        <ThemeToggle />
      </div>

      <SwitchProjectDialog open={switchOpen} onOpenChange={setSwitchOpen} />
    </header>
  );
}
