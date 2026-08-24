import type { ReactNode } from "react";
import { TopBar } from "@/components/shell/TopBar";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-screen flex-col bg-background text-foreground">
      <TopBar />
      <div className="flex-1 overflow-auto">{children}</div>
    </div>
  );
}
