import { useEffect, useMemo, useState } from "react";
import { save } from "@tauri-apps/plugin-dialog";
import { Activity, DollarSign, FileBarChart, FileDown, Trash2 } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import {
  commands,
  isAppCommandError,
  type PipelineDef,
  type RunHistoryRecord,
} from "@/lib/tauri-client";
import { useAppStore } from "@/state/app-store";
import { ScreenHeader } from "@/components/shell/ScreenHeader";
import { slotDisplayName } from "@/lib/slot-label";

const TABS = ["Theo agent", "Theo stage", "Theo pipeline run", "Lịch sử"] as const;
type Tab = (typeof TABS)[number];

function extractErrorMessage(err: unknown): string {
  if (isAppCommandError(err)) return err.message;
  if (err instanceof Error) return err.message;
  return String(err);
}

interface CostGroup {
  key: string;
  total: number;
  counted: number;
  missing: number;
}

/** AC-E6-13/14 — totals sum only rows WITH cost; missing rows are counted
 * separately and surfaced as a note, never silently treated as 0. */
function groupCosts(records: RunHistoryRecord[], keyOf: (r: RunHistoryRecord) => string): CostGroup[] {
  const groups = new Map<string, CostGroup>();
  for (const r of records) {
    const key = keyOf(r);
    const group = groups.get(key) ?? { key, total: 0, counted: 0, missing: 0 };
    if (r.costUsd != null) {
      group.total += r.costUsd;
      group.counted += 1;
    } else {
      group.missing += 1;
    }
    groups.set(key, group);
  }
  return Array.from(groups.values()).sort((a, b) => b.total - a.total);
}

function slotStageLabel(def: PipelineDef | null, slot: string): string {
  if (!def) return slot;
  for (const stage of def.stages) {
    if (stage.agents.some((a) => a.id === slot)) return stage.label;
  }
  return slot;
}

/** Groups costs by what the node is CALLED, not by its agent file — when
 * two slots share one agent file, keying on the file name collapses their
 * spend into one indistinguishable row (that was stage ② vs stage ⑦ QC
 * before `qc-testing` was dropped). Nicknames aren't available here (this
 * screen loads the pipeline definition only, not the project config), so the
 * kit label does the disambiguating. */
function slotDisplayLabel(def: PipelineDef | null, slot: string): string {
  if (!def) return slot;
  for (const stage of def.stages) {
    const agent = stage.agents.find((a) => a.id === slot);
    if (agent) return slotDisplayName(agent);
  }
  return slot;
}

function CostGroupTable({ title, groups }: { title: string; groups: CostGroup[] }) {
  const maxTotal = Math.max(1, ...groups.map((g) => g.total));
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>{title}</TableHead>
          <TableHead>Tổng chi phí</TableHead>
          <TableHead className="w-40">Phân bổ</TableHead>
          <TableHead>Số lượt</TableHead>
          <TableHead>Thiếu số liệu</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {groups.map((g) => (
          <TableRow key={g.key}>
            <TableCell className="font-mono text-xs">{g.key}</TableCell>
            <TableCell>
              {g.counted > 0 ? `$${g.total.toFixed(4)}` : "không có số liệu"}
            </TableCell>
            <TableCell>
              <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-primary transition-all"
                  style={{
                    width: `${g.counted > 0 ? (g.total / maxTotal) * 100 : 0}%`,
                  }}
                />
              </div>
            </TableCell>
            <TableCell>{g.counted + g.missing}</TableCell>
            <TableCell>{g.missing > 0 ? `${g.missing} lượt chưa được tính vào tổng` : "—"}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

/** `OR_COST_001` — Cost & Reports (AC-E6-12..17, 28). */
export function ReportsScreen() {
  const setScreen = useAppStore((s) => s.setScreen);

  const [tab, setTab] = useState<Tab>("Theo agent");
  const [records, setRecords] = useState<RunHistoryRecord[] | null>(null);
  const [pipelineDef, setPipelineDef] = useState<PipelineDef | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [confirmClear, setConfirmClear] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([commands.listRunHistory(), commands.getPipelineDefinition()])
      .then(([history, def]) => {
        if (cancelled) return;
        setRecords(history);
        setPipelineDef(def);
      })
      .catch((err) => {
        if (!cancelled) setLoadError(extractErrorMessage(err));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const byAgent = useMemo(
    () => groupCosts(records ?? [], (r) => slotDisplayLabel(pipelineDef, r.slot)),
    [records, pipelineDef],
  );
  const byStage = useMemo(
    () => groupCosts(records ?? [], (r) => slotStageLabel(pipelineDef, r.slot)),
    [records, pipelineDef],
  );
  const byFeature = useMemo(() => groupCosts(records ?? [], (r) => r.feature), [records]);

  const totalMissing = (records ?? []).filter((r) => r.costUsd == null).length;

  async function handleExportCsv() {
    setActionError(null);
    setActionMessage(null);
    const path = await save({
      defaultPath: "cost-report.csv",
      filters: [{ name: "CSV", extensions: ["csv"] }],
    });
    if (typeof path !== "string") return;
    try {
      await commands.exportCostCsv(path);
      setActionMessage(`Đã xuất CSV: ${path}`);
    } catch (err) {
      setActionError(extractErrorMessage(err));
    }
  }

  async function handleClearLogs() {
    if (!confirmClear) {
      setConfirmClear(true);
      return;
    }
    setConfirmClear(false);
    setActionError(null);
    setActionMessage(null);
    try {
      const removed = await commands.clearRunLogs();
      setActionMessage(
        `Đã xoá ${removed} file log — số liệu chi phí không bị ảnh hưởng (lưu riêng trong run-history).`,
      );
    } catch (err) {
      setActionError(extractErrorMessage(err));
    }
  }

  const hasRecords = (records?.length ?? 0) > 0;
  const totalCost = (records ?? []).reduce((sum, record) => sum + (record.costUsd ?? 0), 0);
  const countedRecords = (records ?? []).filter((record) => record.costUsd != null).length;

  return (
    <div className="flex h-full flex-col gap-4 overflow-y-auto p-6">
      <ScreenHeader
        title="Cost & Reports"
        description="Theo dõi chi phí, số lượt chạy và kết quả của các agent trong project."
        icon={Activity}
        onBack={() => setScreen("board")}
        actions={
          <>
            <Button variant="outline" size="sm" disabled={!hasRecords} onClick={handleExportCsv}>
              <FileDown />
              Xuất CSV
            </Button>
            <Button variant="outline" size="sm" disabled={!hasRecords} onClick={handleClearLogs}>
              <Trash2 />
              {confirmClear ? "Xác nhận xoá log?" : "Xoá log cũ"}
            </Button>
          </>
        }
      />

      {hasRecords && (
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-xl border border-border bg-card p-4">
            <p className="text-xs text-muted-foreground">Tổng chi phí</p>
            <p className="mt-1 text-xl font-semibold tabular-nums">${totalCost.toFixed(4)}</p>
          </div>
          <div className="rounded-xl border border-border bg-card p-4">
            <p className="text-xs text-muted-foreground">Tổng lượt chạy</p>
            <p className="mt-1 text-xl font-semibold tabular-nums">{records?.length ?? 0}</p>
          </div>
          <div className="rounded-xl border border-border bg-card p-4">
            <p className="text-xs text-muted-foreground">Có số liệu chi phí</p>
            <p className="mt-1 flex items-center gap-2 text-xl font-semibold tabular-nums">
              <DollarSign className="size-4 text-success" aria-hidden="true" />
              {countedRecords}/{records?.length ?? 0}
            </p>
          </div>
        </div>
      )}

      {!hasRecords && records !== null && (
        <div className="flex flex-col items-center gap-2 rounded-xl border border-dashed border-border bg-muted/20 py-10 text-center">
          <FileBarChart className="size-10 text-muted-foreground/40" aria-hidden="true" />
          <p className="text-sm font-medium">Chưa có dữ liệu chạy</p>
          <p className="max-w-md text-xs text-muted-foreground">
            Chạy ít nhất một agent để xem chi phí theo agent, stage hoặc feature.
          </p>
        </div>
      )}
      {totalMissing > 0 && (
        <p className="text-xs text-muted-foreground">
          {totalMissing} lượt chạy không có số liệu chi phí — không được tính vào các tổng bên dưới.
        </p>
      )}

      <div className="flex flex-wrap gap-1 border-b border-border">
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            role="tab"
            aria-selected={tab === t}
            onClick={() => setTab(t)}
            className={cn(
              "rounded-t-lg border-b-2 px-3 py-2 text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              tab === t
                ? "border-primary font-medium text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground",
            )}
          >
            {t}
          </button>
        ))}
      </div>

      {loadError && (
        <Alert variant="destructive">
          <AlertTitle>Không tải được lịch sử</AlertTitle>
          <AlertDescription>{loadError}</AlertDescription>
        </Alert>
      )}
      {actionError && (
        <Alert variant="destructive">
          <AlertTitle>Không thực hiện được</AlertTitle>
          <AlertDescription>{actionError}</AlertDescription>
        </Alert>
      )}
      {actionMessage && (
        <Alert>
          <AlertDescription>{actionMessage}</AlertDescription>
        </Alert>
      )}

      {records === null && !loadError && (
        <div className="flex flex-col gap-3">
          <div className="skeleton h-10 w-full" />
          <div className="skeleton h-10 w-full" />
          <div className="skeleton h-10 w-full" />
        </div>
      )}

      {tab === "Theo agent" && hasRecords && <CostGroupTable title="Agent" groups={byAgent} />}
      {tab === "Theo stage" && hasRecords && <CostGroupTable title="Stage" groups={byStage} />}
      {tab === "Theo pipeline run" && hasRecords && (
        <CostGroupTable title="Feature (pipeline run)" groups={byFeature} />
      )}

      {tab === "Lịch sử" && hasRecords && (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Thời điểm</TableHead>
              <TableHead>Feature</TableHead>
              <TableHead>Agent</TableHead>
              <TableHead>Model</TableHead>
              <TableHead>Kết quả</TableHead>
              <TableHead>Chi phí</TableHead>
              <TableHead>Lần thử</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(records ?? []).map((r, index) => (
              <TableRow key={`${r.startedAt}-${r.feature}-${r.slot}-${index}`}>
                <TableCell className="font-mono text-xs">{r.startedAt}</TableCell>
                <TableCell className="font-mono text-xs">{r.feature}</TableCell>
                <TableCell className="font-mono text-xs">
                  {slotDisplayLabel(pipelineDef, r.slot)}
                </TableCell>
                <TableCell className="font-mono text-xs">{r.model ?? "—"}</TableCell>
                <TableCell>{r.outcome}</TableCell>
                <TableCell>
                  {r.costUsd != null ? `$${r.costUsd.toFixed(4)}` : "không có số liệu"}
                </TableCell>
                <TableCell>{r.attempt}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
