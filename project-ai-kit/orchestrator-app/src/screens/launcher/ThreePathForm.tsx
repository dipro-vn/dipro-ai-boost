import { useState } from "react";
import { open } from "@tauri-apps/plugin-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { ProjectPaths } from "@/lib/tauri-client";

interface PathFieldProps {
  id: string;
  label: string;
  hint: string;
  value: string;
  onChange: (value: string) => void;
}

/**
 * Each of the 3 roots browses completely independently — no field is
 * constrained to live under another. A1 proved a real project's
 * repositoryRoot can be a SIBLING of agentsRoot, not nested under it, so
 * any cross-field validation here would be actively wrong.
 */
function PathField({ id, label, hint, value, onChange }: PathFieldProps) {
  async function browse() {
    const selected = await open({ directory: true, multiple: false });
    if (typeof selected === "string") onChange(selected);
  }

  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={id}>{label}</Label>
      <div className="flex gap-2">
        <Input
          id={id}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={hint}
          className="font-mono text-sm"
        />
        <Button type="button" variant="outline" onClick={browse}>
          Chọn thư mục
        </Button>
      </div>
    </div>
  );
}

interface ThreePathFormProps {
  initial: ProjectPaths;
  /** Thư mục người dùng đã chọn ở bước trước — gốc để dựng bố cục mặc định. */
  rootHint: string;
  submitting: boolean;
  onSubmit: (paths: ProjectPaths, label: string) => void;
  onCancel: () => void;
}

export function ThreePathForm({
  initial,
  rootHint,
  submitting,
  onSubmit,
  onCancel,
}: ThreePathFormProps) {
  const [agentsRoot, setAgentsRoot] = useState(initial.agentsRoot);
  const [docsRoot, setDocsRoot] = useState(initial.docsRoot);
  const [repositoryRoot, setRepositoryRoot] = useState(initial.repositoryRoot);
  const [label, setLabel] = useState("");

  /** Bố cục quy ước cho một project mới. Cố ý là một NÚT chứ không phải
   * điền sẵn: `detect_project_paths` để trống khi không dò ra là hành vi có
   * chủ đích (AC-E1-03 — không dò ra thì để trống, KHÔNG đoán). Người dùng
   * bấm mới là chọn, app điền sẵn mới là đoán. */
  function applyDefaultLayout() {
    const base = rootHint.replace(/\/+$/, "");
    setAgentsRoot(base);
    setDocsRoot(`${base}/docs`);
    setRepositoryRoot(`${base}/repos`);
  }

  const canSubmit =
    agentsRoot.trim() !== "" &&
    docsRoot.trim() !== "" &&
    repositoryRoot.trim() !== "" &&
    label.trim() !== "" &&
    !submitting;

  return (
    <form
      className="flex flex-col gap-4"
      onSubmit={(e) => {
        e.preventDefault();
        if (canSubmit) {
          onSubmit({ agentsRoot, docsRoot, repositoryRoot }, label.trim());
        }
      }}
    >
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="project-label">Tên project</Label>
        <Input
          id="project-label"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          placeholder="vd: es-kitchen"
        />
      </div>

      <PathField
        id="agents-root"
        label="Agents root — thư mục chứa .claude/agents/"
        hint="Chưa có cũng được — app sẽ tạo thư mục khi mở"
        value={agentsRoot}
        onChange={setAgentsRoot}
      />
      <PathField
        id="docs-root"
        label="DOCS_ROOT — thư mục chứa features/"
        hint="Chưa có cũng được — app sẽ tạo thư mục khi mở"
        value={docsRoot}
        onChange={setDocsRoot}
      />
      <PathField
        id="repository-root"
        label="Repository root — thư mục chứa các repo source"
        hint="Chưa có cũng được — app sẽ tạo thư mục khi mở"
        value={repositoryRoot}
        onChange={setRepositoryRoot}
      />

      <div className="flex items-center justify-between gap-2 pt-2">
        {rootHint ? (
          <Button type="button" variant="outline" size="sm" onClick={applyDefaultLayout}>
            Dùng bố cục mặc định
          </Button>
        ) : (
          <span />
        )}
        <div className="flex gap-2">
          <Button type="button" variant="ghost" onClick={onCancel}>
            Huỷ
          </Button>
          <Button type="submit" disabled={!canSubmit}>
            {submitting ? "Đang mở..." : "Mở project"}
          </Button>
        </div>
      </div>
    </form>
  );
}
