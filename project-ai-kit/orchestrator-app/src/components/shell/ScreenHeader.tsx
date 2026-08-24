import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ScreenHeaderProps {
  title: string;
  description?: string;
  icon?: LucideIcon;
  onBack?: () => void;
  actions?: ReactNode;
}

/** Shared header for secondary screens. Keeps back navigation, title rhythm,
 * and action placement consistent without introducing a router. */
export function ScreenHeader({ title, description, icon: Icon, onBack, actions }: ScreenHeaderProps) {
  return (
    <div className="flex flex-wrap items-start gap-3 border-b border-border pb-4">
      {onBack && (
        <Button variant="ghost" size="icon" onClick={onBack} aria-label="Quay lại">
          <ArrowLeft />
        </Button>
      )}
      {Icon && (
        <span className="mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
          <Icon className="size-4" aria-hidden="true" />
        </span>
      )}
      <div className="min-w-0 flex-1">
        <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
        {description && <p className="mt-1 max-w-3xl text-xs leading-relaxed text-muted-foreground">{description}</p>}
      </div>
      {actions && <div className="ml-auto flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}
