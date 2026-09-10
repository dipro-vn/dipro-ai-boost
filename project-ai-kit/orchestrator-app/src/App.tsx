import { Suspense, lazy, useState } from "react";
import { ThemeProvider } from "@/lib/theme-provider";
import { AppShell } from "@/components/shell/AppShell";
import { SplashScreen } from "@/components/shell/SplashScreen";
import { useAppStore } from "@/state/app-store";
import { ProjectLauncherScreen } from "@/screens/launcher/ProjectLauncherScreen";
import { TooltipProvider } from "@/components/ui/tooltip";

/**
 * Chỉ `ProjectLauncherScreen` import tĩnh — nó là screen đầu tiên nên lazy chỉ
 * thêm một round-trip. Bốn screen còn lại kéo theo `react-diff-viewer-continued`,
 * `react-markdown` + `lowlight`, `react-virtuoso`; nạp tĩnh cả bốn nghĩa là lần
 * mở app đầu phải tải và transform toàn bộ dù người dùng chưa vào màn nào.
 * Các screen dùng named export nên phải map sang `default` cho `lazy`.
 */
const PipelineBoardScreen = lazy(() =>
  import("@/screens/board/PipelineBoardScreen").then((m) => ({
    default: m.PipelineBoardScreen,
  })),
);
const ArtifactViewerScreen = lazy(() =>
  import("@/screens/viewer/ArtifactViewerScreen").then((m) => ({
    default: m.ArtifactViewerScreen,
  })),
);
const SettingsScreen = lazy(() =>
  import("@/screens/settings/SettingsScreen").then((m) => ({
    default: m.SettingsScreen,
  })),
);
const ReportsScreen = lazy(() =>
  import("@/screens/reports/ReportsScreen").then((m) => ({
    default: m.ReportsScreen,
  })),
);

function App() {
  const screen = useAppStore((s) => s.screen);
  const [showSplash, setShowSplash] = useState(true);

  return (
    <ThemeProvider>
      <TooltipProvider>
        <AppShell>
          {/* Fallback để trống có chủ đích: khi chunk đã nóng thì chuyển screen
              dưới 100ms, một dòng "Đang tải…" nhấp nháy còn khó chịu hơn. */}
          <Suspense fallback={<div className="h-full w-full bg-background" />}>
            {screen === "launcher" && <ProjectLauncherScreen />}
            {screen === "board" && <PipelineBoardScreen />}
            {screen === "viewer" && <ArtifactViewerScreen />}
            {screen === "settings" && <SettingsScreen />}
            {screen === "reports" && <ReportsScreen />}
          </Suspense>
        </AppShell>
        {showSplash && <SplashScreen onDone={() => setShowSplash(false)} />}
      </TooltipProvider>
    </ThemeProvider>
  );
}

export default App;
