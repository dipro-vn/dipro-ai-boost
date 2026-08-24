import { Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/lib/theme-provider";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
      aria-label={theme === "dark" ? "Chuyển sang light" : "Chuyển sang dark"}
      title={theme === "dark" ? "Chuyển sang light" : "Chuyển sang dark"}
    >
      {theme === "dark" ? <Sun /> : <Moon />}
    </Button>
  );
}
