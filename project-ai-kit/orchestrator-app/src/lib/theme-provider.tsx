import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { commands, type Theme } from "@/lib/tauri-client";

interface ThemeContextValue {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

/** Bản sao theme trong `localStorage`, đọc được **đồng bộ** ngay frame đầu.
 * Rust (`get_theme`/`set_theme` → `settings.json` trong AppData) vẫn là nguồn
 * sự thật; đây chỉ là cache read-through để không phải chờ một vòng IPC mới
 * vẽ được gì. Cùng key với đoạn script inline trong `index.html` — sửa ở đây
 * thì phải sửa cả ở đó. */
const THEME_STORAGE_KEY = "dipro-theme";

function readCachedTheme(): Theme {
  try {
    const cached = localStorage.getItem(THEME_STORAGE_KEY);
    if (cached === "light" || cached === "dark") return cached;
  } catch {
    // localStorage có thể throw (private mode, storage bị chặn) — rơi về default.
  }
  return "light";
}

function cacheTheme(theme: Theme) {
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // Ghi cache hỏng không ảnh hưởng gì: Rust vẫn giữ giá trị thật.
  }
}

/**
 * Not `next-themes` — that library targets Next.js SSR and is unnecessary
 * for a Vite SPA. This is the same class-toggle mechanism shadcn/ui and
 * Tailwind already expect (`.dark` on <html>), backed by the Rust
 * `get_theme`/`set_theme` commands (app-level store, not per-project —
 * AC-E1-31/32).
 */
export function ThemeProvider({ children }: { children: ReactNode }) {
  // Seed đồng bộ từ cache để paint đúng theme ngay frame đầu; mặc định "light"
  // khớp DEFAULT_THEME phía Rust (AC-E1-29).
  const [theme, setThemeState] = useState<Theme>(readCachedTheme);

  useEffect(() => {
    let cancelled = false;
    void commands
      .getTheme()
      .then((persisted) => {
        if (cancelled) return;
        setThemeState(persisted);
        cacheTheme(persisted);
      })
      .catch(() => {
        // Không có backend Tauri (chạy `pnpm dev` thuần trong trình duyệt) thì
        // giữ nguyên giá trị cache — không còn gì chặn việc render nữa.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  const setTheme = (next: Theme) => {
    setThemeState(next);
    cacheTheme(next);
    // Fire-and-forget: theme already applied optimistically to the DOM;
    // a persistence failure shouldn't block the UI from reflecting the choice.
    void commands.setTheme(next);
  };

  const toggleTheme = () => setTheme(theme === "dark" ? "light" : "dark");

  return (
    <ThemeContext.Provider value={{ theme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within a ThemeProvider");
  return ctx;
}
