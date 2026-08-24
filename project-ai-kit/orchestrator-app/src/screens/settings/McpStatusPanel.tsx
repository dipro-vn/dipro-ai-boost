import { useCallback, useEffect, useState } from "react";
import { CircleAlert, CircleCheck, CircleX, RefreshCw } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  commands,
  isAppCommandError,
  type McpConnectionStatus,
  type McpStatusEntry,
} from "@/lib/tauri-client";

function extractErrorMessage(err: unknown): string {
  if (isAppCommandError(err)) return err.message;
  if (err instanceof Error) return err.message;
  return String(err);
}

const STATUS_META: Record<
  McpConnectionStatus,
  { label: string; icon: typeof CircleCheck; className: string }
> = {
  connected: { label: "Đã kết nối", icon: CircleCheck, className: "text-success" },
  "needs-auth": { label: "Cần đăng nhập", icon: CircleAlert, className: "text-warning" },
  failed: { label: "Không kết nối được", icon: CircleX, className: "text-destructive" },
};

/**
 * The MCP servers the agents this app spawns can actually reach.
 *
 * Deliberately NOT the same thing as the config table beside it: that one
 * lists what the project's own files declare, this one asks
 * `claude mcp list` — which merges the user-level config with every
 * `.mcp.json` from the project upward AND health-checks each server. A
 * server can be declared and still be unreachable, or reachable and never
 * mentioned in this project's files; both cases only show up here.
 *
 * Not fetched on mount: the health checks take seconds and cost the user a
 * frozen-looking tab every time they open Settings for an unrelated reason.
 */
export function McpStatusPanel() {
  const [entries, setEntries] = useState<McpStatusEntry[] | null>(null);
  const [checkedAt, setCheckedAt] = useState<Date | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const check = useCallback(async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      setEntries(await commands.getMcpStatus());
      setCheckedAt(new Date());
    } catch (err) {
      setErrorMessage(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  // One automatic check when the tab first opens; after that it's manual.
  useEffect(() => {
    void check();
  }, [check]);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-col">
          <h3 className="text-sm font-semibold">Trạng thái kết nối thật</h3>
          <p className="text-xs text-muted-foreground">
            Hỏi <code>claude mcp list</code> — gộp cấu hình MCP global của Claude và mọi{" "}
            <code>.mcp.json</code> từ project trở lên, có kiểm tra kết nối từng server.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {checkedAt && !loading && (
            <span className="text-xs text-muted-foreground">
              Lúc {checkedAt.toLocaleTimeString("vi-VN")}
            </span>
          )}
          <Button variant="outline" size="sm" onClick={check} disabled={loading}>
            <RefreshCw className={loading ? "animate-spin" : undefined} />
            {loading ? "Đang kiểm tra..." : "Kiểm tra lại"}
          </Button>
        </div>
      </div>

      {loading && entries === null && (
        <div className="flex flex-col gap-2">
          <p className="text-xs text-muted-foreground">
            Đang health-check từng MCP server, mất khoảng 10 giây...
          </p>
          <div className="skeleton h-9 w-full" />
          <div className="skeleton h-9 w-full" />
        </div>
      )}

      {errorMessage && (
        <Alert variant="destructive">
          <AlertTitle>Không lấy được trạng thái MCP</AlertTitle>
          <AlertDescription className="break-all">{errorMessage}</AlertDescription>
        </Alert>
      )}

      {entries !== null && entries.length === 0 && !errorMessage && (
        <Alert>
          <AlertTitle>Không có MCP server nào</AlertTitle>
          <AlertDescription>
            Cả cấu hình global lẫn <code>.mcp.json</code> của project đều không khai báo server
            nào.
          </AlertDescription>
        </Alert>
      )}

      {entries !== null && entries.length > 0 && (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Server</TableHead>
              <TableHead>Command / URL</TableHead>
              <TableHead>Trạng thái</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {entries.map((entry) => {
              const meta = STATUS_META[entry.status];
              const Icon = meta.icon;
              return (
                <TableRow key={entry.name}>
                  <TableCell className="font-mono text-xs">{entry.name}</TableCell>
                  <TableCell className="font-mono text-xs break-all">{entry.detail}</TableCell>
                  <TableCell>
                    <span
                      className={`flex items-center gap-1 text-xs ${meta.className}`}
                      title={entry.rawStatus}
                    >
                      <Icon className="size-3.5" aria-hidden="true" />
                      {meta.label}
                    </span>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      )}

      {entries !== null && entries.some((e) => e.status === "needs-auth") && (
        <Alert>
          <AlertTitle>Có server cần đăng nhập</AlertTitle>
          <AlertDescription>
            Chạy <code>claude mcp list</code> hoặc <code>/mcp</code> trong terminal để hoàn tất
            đăng nhập — app không tự xử lý luồng OAuth của MCP.
          </AlertDescription>
        </Alert>
      )}

      {entries !== null && (
        <p className="text-xs text-muted-foreground">
          <Badge variant="outline" className="mr-1">
            Lưu ý
          </Badge>
          Đây là kết nối của <em>các agent do app spawn</em> — bản thân app không nói chuyện MCP.
          Giá trị dạng <code>KEY=…</code> trong cột lệnh đã được che.
        </p>
      )}
    </div>
  );
}
