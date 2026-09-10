import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

const VISIBLE_MS = 350; // đủ để không nháy; app đã sẵn sàng trước mốc này
const EXIT_MS = 300; // phải khớp duration-* dùng cho animate-out bên dưới

interface SplashScreenProps {
  onDone: () => void;
}

/** Overlay chào mừng lúc khởi động — mount đè lên `AppShell` (vốn đã render
 * bình thường phía dưới), tự fade-in rồi fade-out theo timer, gọi `onDone`
 * để cha unmount nó. Tiếp nối liền mạch khối `#boot` tĩnh trong `index.html`
 * (cùng logo, cùng nền), nên đổi bố cục ở đây thì đổi cả bên đó.
 *
 * Không tự xử lý theme: nằm trong `ThemeProvider`, mà provider seed theme
 * đồng bộ từ `localStorage` nên class Tailwind ngữ nghĩa (`bg-background`,
 * `text-foreground`...) đã đúng theme ngay frame đầu. */
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
      <span className="flex max-w-[78vw] items-center rounded-2xl bg-[#013a63] px-6 py-5">
        <img
          src="/logo_dipro.png"
          alt="Dipro AI Boost"
          className="h-auto w-72 max-w-full"
        />
      </span>
      <p className="text-lg font-semibold text-foreground">
        Chào mừng đến với Dipro AI Boost
      </p>
    </div>
  );
}
