import { useEffect, useState } from "react";
import { Workflow } from "lucide-react";
import { cn } from "@/lib/utils";

const VISIBLE_MS = 1400; // thời gian hiện rõ trước khi bắt đầu tắt
const EXIT_MS = 300; // phải khớp duration-* dùng cho animate-out bên dưới

interface SplashScreenProps {
  onDone: () => void;
}

/** Overlay chào mừng lúc khởi động — mount đè lên `AppShell` (vốn đã render
 * bình thường phía dưới), tự fade-in rồi fade-out theo timer, gọi `onDone`
 * để cha unmount nó. Không tự xử lý theme: luôn mount sau khi `ThemeProvider`
 * đã resolve xong (`theme-provider.tsx`'s `if (!loaded) return null`), nên
 * class Tailwind ngữ nghĩa (`bg-background`, `bg-primary`...) tự lên đúng
 * theme từ frame đầu. */
export function SplashScreen({ onDone }: SplashScreenProps) {
  const [exiting, setExiting] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setExiting(true), VISIBLE_MS);
    return () => clearTimeout(t);
  }, []);

  useEffect(() => {
    if (!exiting) return;
    const t = setTimeout(onDone, EXIT_MS);
    return () => clearTimeout(t);
  }, [exiting, onDone]);

  return (
    <div
      className={cn(
        "fixed inset-0 z-50 flex flex-col items-center justify-center gap-4 bg-background",
        exiting
          ? "animate-out fade-out-0 duration-300"
          : "animate-in fade-in-0 zoom-in-95 duration-500",
      )}
    >
      <span className="flex size-14 items-center justify-center rounded-2xl bg-primary text-primary-foreground">
        <Workflow className="size-7" aria-hidden="true" />
      </span>
      <p className="text-lg font-semibold text-foreground">
        Chào mừng đến với Agent Pipeline Orchestrator
      </p>
    </div>
  );
}
