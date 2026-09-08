import { useState } from "react";
import { FolderPlus } from "lucide-react";
import { open } from "@tauri-apps/plugin-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface CreateProjectFormProps {
  submitting: boolean;
  onSubmit: (name: string, parentPath: string) => void;
  onCancel: () => void;
}

export function CreateProjectForm({
  submitting,
  onSubmit,
  onCancel,
}: CreateProjectFormProps) {
  const [name, setName] = useState("");
  const [parentPath, setParentPath] = useState("");

  async function browseParent() {
    const selected = await open({ directory: true, multiple: false });
    if (typeof selected === "string") setParentPath(selected);
  }

  const trimmedName = name.trim();
  const trimmedParent = parentPath.trim();
  const canSubmit = trimmedName !== "" && trimmedParent !== "" && !submitting;
  const destination =
    trimmedName && trimmedParent
      ? `${trimmedParent.replace(/[\\/]+$/, "")}/${trimmedName}`
      : "Chọn thư mục và nhập tên project để xem đường dẫn";

  return (
    <form
      className="flex flex-col gap-4"
      onSubmit={(event) => {
        event.preventDefault();
        if (canSubmit) onSubmit(trimmedName, trimmedParent);
      }}
    >
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="new-project-name">Tên project</Label>
        <Input
          id="new-project-name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="vd: es-kitchen"
          autoFocus
        />
        <p className="text-xs text-muted-foreground">
          App sẽ tạo một thư mục con theo tên này trong thư mục đã chọn.
        </p>
      </div>

      <div className="flex flex-col gap-1.5">
        <Label htmlFor="new-project-parent">Lưu project tại</Label>
        <div className="flex gap-2">
          <Input
            id="new-project-parent"
            value={parentPath}
            onChange={(event) => setParentPath(event.target.value)}
            placeholder="Chọn thư mục cha"
            className="font-mono text-sm"
          />
          <Button
            type="button"
            variant="outline"
            onClick={() => void browseParent()}
          >
            <FolderPlus />
            Chọn thư mục
          </Button>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-muted/30 p-3">
        <p className="text-xs font-medium">Đường dẫn project</p>
        <p className="mt-1 break-all font-mono text-xs text-muted-foreground">
          {destination}
        </p>
        <p className="mt-2 text-xs text-muted-foreground">
          App sẽ tạo `.claude/`, `docs/features/`, `repos/` và `.ai-boost/`,
          sau đó mở Claude để chạy init-kit trong app.
        </p>
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <Button
          type="button"
          variant="ghost"
          onClick={onCancel}
          disabled={submitting}
        >
          Huỷ
        </Button>
        <Button type="submit" disabled={!canSubmit}>
          {submitting ? "Đang tạo..." : "Tạo project"}
        </Button>
      </div>
    </form>
  );
}
