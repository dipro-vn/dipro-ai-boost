import { useState } from "react";
import { FolderPlus, Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface WorkflowSidebarProps {
  features: string[];
  activeFeature: string | null;
  onSelect: (feature: string) => void;
  /** Rejects with a backend message on an invalid or duplicate name; the
   * form keeps what was typed so it can be corrected. */
  onCreate: (name: string) => Promise<void>;
  /** Opens the confirm dialog — deletion itself happens there, never from
   * this button. */
  onRequestDelete: (feature: string) => void;
}

/**
 * Left rail of the Pipeline Board: every feature under
 * `<docsRoot>/features/`, plus the only in-app way to start a new one
 * (AC-E2-24).
 *
 * Lists features read from disk, not "features created here" — a feature
 * made by `/create-spec` outside the app is just as real, and the whole app
 * derives state from the filesystem rather than from its own bookkeeping.
 */
export function WorkflowSidebar({
  features,
  activeFeature,
  onSelect,
  onCreate,
  onRequestDelete,
}: WorkflowSidebarProps) {
  const [adding, setAdding] = useState(false);
  const [name, setName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function cancel() {
    setAdding(false);
    setName("");
    setError(null);
  }

  async function submit() {
    const trimmed = name.trim();
    if (!trimmed || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      await onCreate(trimmed);
      cancel();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex h-full w-48 shrink-0 flex-col border-r border-border lg:w-56">
      <div className="flex items-center justify-between gap-2 p-3">
        <h2 className="text-sm font-semibold">Workflow</h2>
        {!adding && (
          <Button
            variant="ghost"
            size="icon"
            className="size-7"
            aria-label="Thêm feature"
            title="Thêm feature mới"
            onClick={() => setAdding(true)}
          >
            <Plus />
          </Button>
        )}
      </div>

      {adding && (
        <div className="flex flex-col gap-2 px-3 pb-3">
          <Input
            autoFocus
            value={name}
            disabled={submitting}
            placeholder="vd: user-login"
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") void submit();
              if (e.key === "Escape") cancel();
            }}
          />
          <p className="text-xs text-muted-foreground">
            Chữ thường, số và dấu gạch ngang.
          </p>
          {error && <p className="text-xs text-destructive">{error}</p>}
          <div className="flex gap-2">
            <Button size="sm" onClick={submit} disabled={!name.trim() || submitting}>
              {submitting ? "Đang tạo..." : "Tạo"}
            </Button>
            <Button size="sm" variant="ghost" onClick={cancel} disabled={submitting}>
              Huỷ
            </Button>
          </div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto px-2 pb-3">
        {features.length === 0 ? (
          <div className="flex flex-col items-center gap-2 px-1 py-6 text-center">
            <FolderPlus className="size-7 text-muted-foreground/40" aria-hidden="true" />
            <p className="text-xs text-muted-foreground">
              Chưa có feature nào. Bấm + để tạo feature đầu tiên.
            </p>
          </div>
        ) : (
          <ul className="flex flex-col gap-0.5">
            {features.map((feature) => (
              <li key={feature} className="group relative">
                <button
                  type="button"
                  onClick={() => onSelect(feature)}
                  aria-current={feature === activeFeature}
                  className={cn(
                    // Right padding leaves room for the delete button so a
                    // long name never renders underneath it.
                    "w-full truncate rounded-md py-1.5 pr-8 pl-2 text-left text-sm",
                    feature === activeFeature
                      ? "bg-accent font-medium text-accent-foreground"
                      : "text-muted-foreground hover:bg-accent/50",
                  )}
                  title={feature}
                >
                  {feature}
                </button>
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label={`Xoá feature ${feature}`}
                  title="Xoá feature"
                  // Hidden until hover/focus: destructive actions should not
                  // sit permanently under the cursor of a list you click to
                  // navigate. Still reachable by keyboard via focus.
                  className="absolute top-0.5 right-1 size-6 text-muted-foreground opacity-0 group-hover:opacity-100 hover:text-destructive focus-visible:opacity-100"
                  onClick={() => onRequestDelete(feature)}
                >
                  <Trash2 />
                </Button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
