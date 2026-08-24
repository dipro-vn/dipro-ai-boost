import { useEffect } from "react";
import { createPortal } from "react-dom";
import { FilePlus, FolderPlus, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ExplorerContextTarget, ExplorerCreateKind } from "@/screens/explorer/explorer-types";

interface ExplorerContextMenuProps {
  target: ExplorerContextTarget | null;
  onCreate: (kind: ExplorerCreateKind) => void;
  onDelete: () => void;
  onClose: () => void;
}

function menuPosition(target: ExplorerContextTarget): { left: number; top: number } {
  const menuWidth = 196;
  const menuHeight = 146;
  return {
    left: Math.max(8, Math.min(target.x, window.innerWidth - menuWidth - 8)),
    top: Math.max(8, Math.min(target.y, window.innerHeight - menuHeight - 8)),
  };
}

export function ExplorerContextMenu({
  target,
  onCreate,
  onDelete,
  onClose,
}: ExplorerContextMenuProps) {
  useEffect(() => {
    if (!target) return;

    function handlePointerDown(event: PointerEvent) {
      const menu = document.querySelector("[data-explorer-context-menu]");
      if (menu && event.target instanceof Node && !menu.contains(event.target)) {
        onClose();
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [onClose, target]);

  if (!target) return null;

  const position = menuPosition(target);
  const itemClassName =
    "flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-left text-xs outline-none hover:bg-muted focus-visible:bg-muted";

  return createPortal(
    <div
      data-explorer-context-menu
      role="menu"
      aria-label={`Thao tác với ${target.name}`}
      tabIndex={-1}
      className="fixed z-[100] w-49 rounded-lg border border-border bg-popover p-1 text-popover-foreground shadow-xl"
      style={position}
    >
      <div className="truncate px-2.5 py-1.5 font-mono text-[11px] text-muted-foreground" title={target.path}>
        {target.name}
      </div>
      <button
        type="button"
        role="menuitem"
        className={itemClassName}
        onClick={() => onCreate("file")}
      >
        <FilePlus className="size-3.5" aria-hidden="true" />
        Tạo file
      </button>
      <button
        type="button"
        role="menuitem"
        className={itemClassName}
        onClick={() => onCreate("folder")}
      >
        <FolderPlus className="size-3.5" aria-hidden="true" />
        Tạo folder
      </button>
      <div className="my-1 h-px bg-border" />
      <button
        type="button"
        role="menuitem"
        className={cn(itemClassName, "text-destructive hover:bg-destructive/10 focus-visible:bg-destructive/10")}
        onClick={onDelete}
      >
        <Trash2 className="size-3.5" aria-hidden="true" />
        Xoá folder
      </button>
    </div>,
    document.body,
  );
}
