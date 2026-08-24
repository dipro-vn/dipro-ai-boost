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

/**
 * Not `next-themes` — that library targets Next.js SSR and is unnecessary
 * for a Vite SPA. This is the same class-toggle mechanism shadcn/ui and
 * Tailwind already expect (`.dark` on <html>), backed by the Rust
 * `get_theme`/`set_theme` commands (app-level store, not per-project —
 * AC-E1-31/32).
 */
export function ThemeProvider({ children }: { children: ReactNode }) {
  // Default light until the persisted value loads (AC-E1-29).
  const [theme, setThemeState] = useState<Theme>("light");
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    commands
      .getTheme()
      .then((persisted) => {
        if (!cancelled) setThemeState(persisted);
      })
      .finally(() => {
        if (!cancelled) setLoaded(true);
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
    // Fire-and-forget: theme already applied optimistically to the DOM;
    // a persistence failure shouldn't block the UI from reflecting the choice.
    void commands.setTheme(next);
  };

  const toggleTheme = () => setTheme(theme === "dark" ? "light" : "dark");

  // Avoid a light->dark flash: don't render children until the persisted
  // theme has been read once.
  if (!loaded) return null;

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
