import { useEffect, useState } from "react";
import { Settings2 } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ThemeToggle } from "@/components/shell/ThemeToggle";
import { AuthenticationSettings } from "@/screens/settings/AuthenticationSettings";
import { McpStatusPanel } from "@/screens/settings/McpStatusPanel";
import { cn } from "@/lib/utils";
import {
  commands,
  isAppCommandError,
  type AgentConfig,
  type AgentModel,
  type AgentPermissionProfile,
  type FigmaMcpReadiness,
  type McpServer,
  type ProjectConfig,
} from "@/lib/tauri-client";
import { useAppStore } from "@/state/app-store";
import { ScreenHeader } from "@/components/shell/ScreenHeader";

const TABS = ["Agents", "Authentication", "Integrations", "MCP", "Runtime", "Giao diện"] as const;
type Tab = (typeof TABS)[number];

const MODELS: AgentModel[] = ["opus", "sonnet", "haiku"];
const PERMISSIONS: AgentPermissionProfile[] = ["read-only", "write-scoped", "full"];

function extractErrorMessage(err: unknown): string {
  if (isAppCommandError(err)) return err.message;
  if (err instanceof Error) return err.message;
  return String(err);
}

/**
 * `OR_CONF_002` (AC-E1-08..15, 24..28 + AC-E6-21/23). Every edit saves
 * immediately via `set_config` (AC-E1-11) — no separate Save button.
 * Hand-rolled tab switcher, consistent with the app's no-router shell.
 */
export function SettingsScreen() {
  const setScreen = useAppStore((s) => s.setScreen);

  const [tab, setTab] = useState<Tab>("Agents");
  const [config, setConfig] = useState<ProjectConfig | null>(null);
  const [mcpServers, setMcpServers] = useState<McpServer[] | null>(null);
  const [figmaReadiness, setFigmaReadiness] = useState<FigmaMcpReadiness | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      commands.getConfig(),
      commands.getMcpServers(),
      commands.getFigmaMcpReadiness(),
    ])
      .then(([cfg, servers, readiness]) => {
        if (cancelled) return;
        setConfig(cfg);
        setMcpServers(servers);
        setFigmaReadiness(readiness);
      })
      .catch((err) => {
        if (!cancelled) setLoadError(extractErrorMessage(err));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  /** Optimistic update + immediate persist (AC-E1-11). */
  function persist(next: ProjectConfig) {
    setConfig(next);
    setSaveError(null);
    commands
      .setConfig(next)
      // Choosing a different Figma server changes which agents can reach
      // it, so the warning below has to be recomputed — it is derived from
      // the choice that was just saved.
      .then(() => commands.getFigmaMcpReadiness())
      .then(setFigmaReadiness)
      .catch((err) => setSaveError(extractErrorMessage(err)));
  }

  function updateAgent(name: string, patch: Partial<AgentConfig>) {
    if (!config) return;
    const agent = config.agents[name];
    if (!agent) return;
    persist({
      ...config,
      agents: { ...config.agents, [name]: { ...agent, ...patch } },
    });
  }

  const figmaCandidates = (mcpServers ?? []).filter((s) => s.figmaCandidate);

  return (
    <div className="flex h-full flex-col gap-4 overflow-y-auto p-6">
      <ScreenHeader
        title="Settings"
        description="Cấu hình agent, authentication, MCP integrations, runtime và giao diện của project."
        icon={Settings2}
        onBack={() => setScreen("board")}
      />

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
          <AlertTitle>Không tải được cấu hình</AlertTitle>
          <AlertDescription>{loadError}</AlertDescription>
        </Alert>
      )}
      {saveError && (
        <Alert variant="destructive">
          <AlertTitle>Không lưu được thay đổi</AlertTitle>
          <AlertDescription>{saveError}</AlertDescription>
        </Alert>
      )}

      {tab === "Agents" && config && (
        <div className="flex flex-col gap-3">
          <p className="text-xs text-muted-foreground">
            Thay đổi áp dụng cho lần spawn kế tiếp — không ảnh hưởng agent đang chạy (AC-E1-24).
            Max turns hiện chưa enforce được (Claude CLI không hỗ trợ flag tương ứng) — chỉ lưu
            để tham khảo.
          </p>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Agent</TableHead>
                <TableHead>Model</TableHead>
                <TableHead>Max turns</TableHead>
                <TableHead>Timeout (phút)</TableHead>
                <TableHead>Permission profile</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {Object.entries(config.agents).map(([name, agent]) => (
                <TableRow key={name} className={cn(agent.stale && "opacity-50")}>
                  <TableCell className="font-mono text-xs">
                    <div className="flex items-center gap-2">
                      {name}
                      {agent.newly_discovered && <Badge variant="secondary">mới</Badge>}
                      {agent.stale && <Badge variant="outline">không còn trong kit</Badge>}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Select
                      value={agent.model}
                      onValueChange={(value) => updateAgent(name, { model: value as AgentModel })}
                    >
                      <SelectTrigger className="w-28">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {MODELS.map((m) => (
                          <SelectItem key={m} value={m}>
                            {m}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </TableCell>
                  <TableCell>
                    <Input
                      type="number"
                      min={1}
                      className="w-20"
                      value={agent.max_turns}
                      onChange={(e) => {
                        const value = Number(e.target.value);
                        if (Number.isFinite(value) && value >= 1) {
                          updateAgent(name, { max_turns: value });
                        }
                      }}
                    />
                  </TableCell>
                  <TableCell>
                    <Input
                      type="number"
                      min={1}
                      className="w-20"
                      value={agent.timeout_minutes}
                      onChange={(e) => {
                        const value = Number(e.target.value);
                        if (Number.isFinite(value) && value >= 1) {
                          updateAgent(name, { timeout_minutes: value });
                        }
                      }}
                    />
                  </TableCell>
                  <TableCell>
                    <Select
                      value={agent.permission}
                      onValueChange={(value) =>
                        updateAgent(name, { permission: value as AgentPermissionProfile })
                      }
                    >
                      <SelectTrigger className="w-36">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {PERMISSIONS.map((p) => (
                          <SelectItem key={p} value={p}>
                            {p}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {tab === "Authentication" && <AuthenticationSettings />}

      {tab === "Integrations" && (
        <div className="flex flex-col gap-6">
          <Separator />
          <div className="flex flex-col gap-1">
            <h3 className="text-sm font-semibold">Slack</h3>
            <p className="text-xs text-muted-foreground">
              Ngoài phạm vi bản này — quyết định 18/08/2026, xem mục B20 trong
              ASSUMPTIONS-GAPS.md.
            </p>
          </div>
        </div>
      )}

      {tab === "MCP" && (
        <div className="flex flex-col gap-3">
          <McpStatusPanel />

          <Separator />

          <h3 className="text-sm font-semibold">Khai báo trong project</h3>
          <p className="text-xs text-muted-foreground">
            Đọc từ cấu hình MCP của chính project (<code>.mcp.json</code> /{" "}
            <code>.claude/settings.json</code> tại agentsRoot) — chỉ đọc, không sửa được từ đây.
            Bảng này là <em>khai báo</em>; bảng trên là <em>kết nối thật</em>, nên một server có
            thể xuất hiện ở bảng trên mà không có ở đây (khai ở cấu hình global hoặc ở thư mục
            cha). App không lưu và không yêu cầu credentials Figma riêng — MCP server đảm nhiệm
            toàn bộ việc kết nối.
          </p>
          {mcpServers === null ? (
            <div className="flex flex-col gap-2">
              <div className="skeleton h-9 w-full" />
              <div className="skeleton h-9 w-full" />
            </div>
          ) : mcpServers.length === 0 ? (
            <Alert>
              <AlertTitle>Không tìm thấy MCP server nào</AlertTitle>
              <AlertDescription>
                Project chưa khai báo MCP server — stage Design (design-analyst) sẽ không chạy
                được cho tới khi có MCP phục vụ Figma.
              </AlertDescription>
            </Alert>
          ) : (
            <>
              {figmaCandidates.length === 0 && (
                <Alert>
                  <AlertTitle>Không tìm thấy MCP nào phục vụ Figma</AlertTitle>
                  <AlertDescription>
                    Stage Design (design-analyst) sẽ không chạy được cho tới khi project khai
                    báo một MCP server phục vụ Figma.
                  </AlertDescription>
                </Alert>
              )}
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Server</TableHead>
                    <TableHead>Loại</TableHead>
                    <TableHead>Chi tiết</TableHead>
                    <TableHead>Figma</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {mcpServers.map((server) => (
                    <TableRow key={server.name}>
                      <TableCell className="font-mono text-xs">{server.name}</TableCell>
                      <TableCell>{server.kind}</TableCell>
                      <TableCell className="font-mono text-xs">{server.detail}</TableCell>
                      <TableCell>
                        {figmaCandidates.length > 1 && server.figmaCandidate && config ? (
                          <label className="flex items-center gap-1 text-xs">
                            <input
                              type="radio"
                              name="figma-server"
                              className="accent-primary"
                              checked={config.figma_mcp_server === server.name}
                              onChange={() =>
                                persist({ ...config, figma_mcp_server: server.name })
                              }
                            />
                            dùng cho stage Design
                          </label>
                        ) : server.figmaCandidate ? (
                          <Badge variant="secondary">Figma</Badge>
                        ) : null}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              {figmaCandidates.length > 1 && (
                <p className="text-xs text-muted-foreground">
                  Nhiều server có thể phục vụ Figma — chọn server dùng cho stage Design ở cột
                  bên phải.
                </p>
              )}
              {/* Shown even with a single candidate, when no radio appears:
                  which server the agents get told to call is not otherwise
                  visible anywhere. */}
              {figmaReadiness?.resolvedServer && (
                <p className="text-xs text-muted-foreground">
                  Stage Design và Build sẽ dùng MCP{" "}
                  <code className="font-mono">{figmaReadiness.resolvedServer}</code>.
                </p>
              )}
              {figmaReadiness?.resolvedServer &&
                figmaReadiness.agentsMissingTools.length > 0 && (
                  <Alert variant="destructive">
                    <AlertTitle>
                      Agent chưa khai tool của MCP{" "}
                      <code className="font-mono">{figmaReadiness.resolvedServer}</code>
                    </AlertTitle>
                    <AlertDescription>
                      <p>
                        <code className="font-mono">tools:</code> trong file agent là allowlist —
                        tool không có trong đó thì agent KHÔNG gọi được, dù MCP đã kết nối. Các
                        agent sau chưa khai{" "}
                        <code className="font-mono">mcp__{figmaReadiness.toolPrefix}__*</code>:
                      </p>
                      <ul className="mt-1 list-disc pl-4 font-mono text-xs">
                        {figmaReadiness.agentsMissingTools.map((agent) => (
                          <li key={agent}>.claude/agents/{agent}.md</li>
                        ))}
                      </ul>
                      <p className="mt-1">
                        Thêm các tool <strong>ĐỌC</strong> của server này vào{" "}
                        <code className="font-mono">tools:</code> của từng file, hoặc chọn MCP
                        Figma khác ở trên. Design Analyst sẽ bị chặn (không spawn) cho tới khi
                        xử lý; Frontend/Mobile vẫn chạy nhưng chỉ dựa vào{" "}
                        <code className="font-mono">design-analysis.md</code>.
                      </p>
                    </AlertDescription>
                  </Alert>
                )}
            </>
          )}
        </div>
      )}

      {tab === "Runtime" && config && (
        <div className="flex max-w-md flex-col gap-4">
          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium" htmlFor="max-retries">
              Số lần retry tối đa
            </label>
            <Input
              id="max-retries"
              type="number"
              min={0}
              className="w-24"
              value={config.max_retries}
              onChange={(e) => {
                const value = Number(e.target.value);
                if (Number.isFinite(value) && value >= 0) {
                  persist({ ...config, max_retries: value });
                }
              }}
            />
            <p className="text-xs text-muted-foreground">
              Vượt giới hạn thì nút Retry bị vô hiệu. Mặc định 2.
            </p>
          </div>
          <Separator />
          <p className="text-xs text-muted-foreground">
            Timeout cấu hình riêng cho từng agent — xem cột "Timeout (phút)" trong tab Agents.
          </p>
        </div>
      )}

      {tab === "Giao diện" && (
        <div className="flex items-center gap-3">
          <ThemeToggle />
          <p className="text-sm text-muted-foreground">
            Chuyển đổi giữa theme dark và light — áp dụng ngay, lưu theo app.
          </p>
        </div>
      )}
    </div>
  );
}
