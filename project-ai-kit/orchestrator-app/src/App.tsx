import { ThemeProvider } from "@/lib/theme-provider";
import { AppShell } from "@/components/shell/AppShell";
import { useAppStore } from "@/state/app-store";
import { ProjectLauncherScreen } from "@/screens/launcher/ProjectLauncherScreen";
import { PipelineBoardScreen } from "@/screens/board/PipelineBoardScreen";
import { ArtifactViewerScreen } from "@/screens/viewer/ArtifactViewerScreen";
import { SettingsScreen } from "@/screens/settings/SettingsScreen";
import { ReportsScreen } from "@/screens/reports/ReportsScreen";
import { TooltipProvider } from "@/components/ui/tooltip";

function App() {
  const screen = useAppStore((s) => s.screen);

  return (
    <ThemeProvider>
      <TooltipProvider>
        <AppShell>
          {screen === "launcher" && <ProjectLauncherScreen />}
          {screen === "board" && <PipelineBoardScreen />}
          {screen === "viewer" && <ArtifactViewerScreen />}
          {screen === "settings" && <SettingsScreen />}
          {screen === "reports" && <ReportsScreen />}
        </AppShell>
      </TooltipProvider>
    </ThemeProvider>
  );
}

export default App;
