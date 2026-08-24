import { useCallback, useEffect, useState } from "react";
import { Eye, EyeOff, FolderSearch, KeyRound, LogIn, RefreshCw, ShieldCheck, Terminal } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import {
  commands,
  isAppCommandError,
  type ClaudeAuthMode,
  type ClaudeAuthStatus,
  type ProjectConfig,
} from "@/lib/tauri-client";

function extractErrorMessage(err: unknown): string {
  if (isAppCommandError(err)) return err.message;
  if (err instanceof Error) return err.message;
  return String(err);
}

function methodLabel(status: ClaudeAuthStatus): string {
  if (status.status === "cli-not-found") return "Claude CLI chưa được cài đặt";
  if (status.status === "not-authenticated") return "Chưa đăng nhập";
  if (status.status === "subscription") return "Claude subscription";
  if (status.status === "console") return "Claude Console";
  if (status.status === "api-key" || status.status === "api-key-override") return "Anthropic API key";
  if (status.status === "expired") return "Credential đã hết hạn";
  return status.method || "Không xác định";
}

function statusTone(status: ClaudeAuthStatus): string {
  if (status.status === "subscription" || status.status === "console" || status.status === "api-key") {
    return "border-success/40 bg-success/5";
  }
  if (status.status === "api-key-override" || status.status === "expired") {
    return "border-warning/50 bg-warning/5";
  }
  return "border-border bg-muted/20";
}

const MODES: Array<{ value: ClaudeAuthMode; label: string; description: string }> = [
  {
    value: "cli-default",
    label: "CLI default",
    description: "Giữ nguyên credential resolution của Claude CLI.",
  },
  {
    value: "subscription",
    label: "Subscription",
    description: "Dùng Claude.ai Pro, Max, Team hoặc Enterprise login.",
  },
  {
    value: "console",
    label: "Claude Console",
    description: "Dùng account Console với API usage billing.",
  },
  {
    value: "api-key",
    label: "Claude API key",
    description: "Dùng API key được lưu trong OS Keychain.",
  },
];

export function AuthenticationSettings() {
  const [status, setStatus] = useState<ClaudeAuthStatus | null>(null);
  const [mode, setMode] = useState<ClaudeAuthMode>("cli-default");
  const [apiKey, setApiKey] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);
  const [loginPending, setLoginPending] = useState(false);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState<"mode" | "login" | "save" | "clear" | "logout" | null>(null);
  const [confirmLogout, setConfirmLogout] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [config, setConfig] = useState<ProjectConfig | null>(null);
  const [cliPathInput, setCliPathInput] = useState("");
  const [savingCliPath, setSavingCliPath] = useState(false);

  const checkStatus = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const next = await commands.getClaudeAuthStatus();
      setStatus(next);
      setMode(next.configuredMode);
      if (next.status === "subscription" || next.status === "console") {
        setLoginPending(false);
      }
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!loginPending) return;
    const timer = window.setInterval(() => {
      void commands
        .getClaudeAuthStatus()
        .then((next) => {
          setStatus(next);
          setMode(next.configuredMode);
          if (next.status === "subscription" || next.status === "console") {
            setLoginPending(false);
            setMessage("Authentication đã hoàn tất.");
          }
        })
        .catch(() => {
          // The explicit refresh button remains the recovery path if the
          // background status check cannot reach the CLI.
        });
    }, 3000);
    return () => window.clearInterval(timer);
  }, [loginPending]);

  useEffect(() => {
    void checkStatus();
  }, [checkStatus]);

  useEffect(() => {
    let cancelled = false;
    commands
      .getConfig()
      .then((next) => {
        if (cancelled) return;
        setConfig(next);
        setCliPathInput(next.claude_cli_path ?? "");
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(extractErrorMessage(err));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Persisting an empty string clears the override — the backend then
  /// falls back to auto-detection on the very next spawn.
  async function saveCliPath() {
    if (!config) return;
    setSavingCliPath(true);
    setMessage(null);
    setError(null);
    const trimmed = cliPathInput.trim();
    try {
      const next: ProjectConfig = { ...config, claude_cli_path: trimmed === "" ? null : trimmed };
      await commands.setConfig(next);
      setConfig(next);
      setMessage(
        trimmed === ""
          ? "Đã xoá đường dẫn thủ công — app sẽ tự dò lại Claude CLI."
          : `Đã lưu đường dẫn Claude CLI: ${trimmed}`,
      );
      await checkStatus();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSavingCliPath(false);
    }
  }

  async function changeMode(nextMode: ClaudeAuthMode) {
    setBusy("mode");
    setMessage(null);
    setError(null);
    try {
      await commands.setClaudeAuthMode(nextMode);
      setMode(nextMode);
      setMessage(`Đã chọn auth mode: ${nextMode}.`);
      await checkStatus();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  async function startLogin(loginMode: "subscription" | "console") {
    setBusy("login");
    setMessage(null);
    setError(null);
    try {
      await commands.setClaudeAuthMode(loginMode);
      await commands.startClaudeLogin(loginMode);
      setMode(loginMode);
      setLoginPending(true);
      setMessage("Đã mở Claude login flow. Hoàn tất trong browser/terminal rồi bấm Kiểm tra lại.");
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  async function saveApiKey() {
    if (!apiKey.trim()) return;
    setBusy("save");
    setMessage(null);
    setError(null);
    try {
      await commands.saveClaudeApiKey(apiKey);
      setApiKey("");
      setMode("api-key");
      setMessage("Đã lưu Claude API key vào OS Keychain. Key không được ghi vào config hoặc log.");
      await checkStatus();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  async function clearApiKey() {
    setBusy("clear");
    setMessage(null);
    setError(null);
    try {
      await commands.clearClaudeApiKey();
      setApiKey("");
      setMessage("Đã xoá Claude API key khỏi OS Keychain và chuyển về CLI default.");
      await checkStatus();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  async function logoutClaude() {
    if (!confirmLogout) {
      setConfirmLogout(true);
      return;
    }
    setBusy("logout");
    setMessage(null);
    setError(null);
    try {
      await commands.logoutClaude();
      setConfirmLogout(false);
      setLoginPending(false);
      setMessage("Đã mở Claude logout flow. Bấm Kiểm tra lại sau khi CLI hoàn tất.");
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="flex max-w-3xl flex-col gap-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="flex items-center gap-2 text-sm font-semibold">
            <ShieldCheck className="size-4 text-primary" aria-hidden="true" />
            Claude authentication
          </h3>
          <p className="mt-1 text-xs text-muted-foreground">
            Chọn credential cho các process Claude do app spawn. Pipeline và agent identity không bị thay đổi.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => void checkStatus()} disabled={loading}>
          <RefreshCw className={cn(loading && "animate-spin")} />
          {loading ? "Đang kiểm tra..." : "Kiểm tra lại"}
        </Button>
      </div>

      {status && (
        <div className={cn("rounded-xl border p-4", statusTone(status))}>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="flex items-start gap-3">
              <span className="mt-0.5 flex size-8 items-center justify-center rounded-lg bg-background/70 text-primary">
                <Terminal className="size-4" aria-hidden="true" />
              </span>
              <div>
                <p className="text-sm font-semibold">{methodLabel(status)}</p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {status.cliAvailable
                    ? status.cliVersion ?? "Claude CLI đã cài đặt"
                    : "Không tìm thấy `claude` — app bundle không kế thừa PATH của terminal"}
                </p>
                {status.cliPath && (
                  <p className="mt-1 font-mono text-xs text-muted-foreground">{status.cliPath}</p>
                )}
                {status.account && <p className="mt-1 text-xs">Account: {status.account}</p>}
                {status.organization && <p className="text-xs">Organization: {status.organization}</p>}
                {status.status === "api-key" && (
                  <p className="mt-1 text-xs text-muted-foreground">
                    Keychain đã có key; request thật sẽ được xác thực ở lần chạy agent kế tiếp.
                  </p>
                )}
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={status.authenticated ? "secondary" : "outline"}>
                {status.status === "api-key" ? "Đã cấu hình" : status.authenticated ? "Connected" : "Cần xử lý"}
              </Badge>
              {status.authenticated && status.status !== "api-key" && status.status !== "api-key-override" && (
                <Button variant="ghost" size="sm" onClick={() => void logoutClaude()} disabled={busy !== null}>
                  {confirmLogout ? "Xác nhận logout" : "Logout CLI"}
                </Button>
              )}
            </div>
          </div>
          {status.envOverrides.length > 0 && (
            <Alert className="mt-3">
              <AlertTitle>Environment override đang tồn tại</AlertTitle>
              <AlertDescription>
                {status.envOverrides.join(", ")} được phát hiện. API key hoặc token có thể override subscription trong non-interactive run.
              </AlertDescription>
            </Alert>
          )}
        </div>
      )}

      <div className="rounded-xl border border-border p-4">
        <h4 className="flex items-center gap-2 text-sm font-semibold">
          <FolderSearch className="size-4 text-primary" aria-hidden="true" />
          Đường dẫn Claude CLI
        </h4>
        <p className="mt-1 text-xs text-muted-foreground">
          Để trống nếu app tự dò được. Cần điền khi mở app từ Finder/Start Menu — bundle không kế thừa
          PATH của terminal, nên CLI cài ở <code className="font-mono">~/.local/bin</code> sẽ không thấy.
          Lấy đường dẫn bằng <code className="font-mono">which claude</code>.
        </p>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <Input
            value={cliPathInput}
            onChange={(event) => setCliPathInput(event.target.value)}
            placeholder="/Users/ban/.local/bin/claude"
            className="min-w-64 flex-1 font-mono text-xs"
            spellCheck={false}
            disabled={config === null}
          />
          <Button
            variant="outline"
            size="sm"
            onClick={() => void saveCliPath()}
            disabled={config === null || savingCliPath}
          >
            {savingCliPath ? "Đang lưu..." : "Lưu"}
          </Button>
        </div>
      </div>

      <div className="flex flex-col gap-2">
        <div>
          <h4 className="text-sm font-semibold">Auth mode của project</h4>
          <p className="mt-1 text-xs text-muted-foreground">Thay đổi áp dụng cho các lần spawn tiếp theo.</p>
        </div>
        <div className="grid gap-2 sm:grid-cols-2" role="radiogroup" aria-label="Claude auth mode">
          {MODES.map((option) => (
            <button
              key={option.value}
              type="button"
              role="radio"
              aria-checked={mode === option.value}
              onClick={() => void changeMode(option.value)}
              disabled={busy !== null}
              className={cn(
                "rounded-xl border p-3 text-left transition-colors hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                mode === option.value ? "border-primary bg-primary/5" : "border-border",
              )}
            >
              <span className="flex items-center gap-2 text-sm font-medium">
                <span className={cn("size-2 rounded-full", mode === option.value ? "bg-primary" : "bg-muted-foreground/30")} />
                {option.label}
              </span>
              <span className="mt-1 block text-xs text-muted-foreground">{option.description}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-xl border border-border p-4">
          <h4 className="flex items-center gap-2 text-sm font-semibold">
            <LogIn className="size-4 text-primary" aria-hidden="true" />
            Subscription / Console
          </h4>
          <p className="mt-1 text-xs text-muted-foreground">
            Claude CLI tự mở browser và tự quản lý OAuth credential. App không nhận hoặc lưu OAuth token.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button size="sm" onClick={() => void startLogin("subscription")} disabled={busy !== null || !status?.cliAvailable}>
              {loginPending && mode === "subscription" ? "Đang chờ login..." : "Subscription login"}
            </Button>
            <Button variant="outline" size="sm" onClick={() => void startLogin("console")} disabled={busy !== null || !status?.cliAvailable}>
              {loginPending && mode === "console" ? "Đang chờ login..." : "Console login"}
            </Button>
          </div>
        </div>

        <div className="rounded-xl border border-border p-4">
          <h4 className="flex items-center gap-2 text-sm font-semibold">
            <KeyRound className="size-4 text-primary" aria-hidden="true" />
            Claude API key
          </h4>
          <p className="mt-1 text-xs text-muted-foreground">
            API key dùng billing pay-as-you-go và được inject chỉ vào child process.
          </p>
          <div className="relative mt-3">
            <Input
              className="pr-10"
              type={showApiKey ? "text" : "password"}
              autoComplete="off"
              value={apiKey}
              placeholder={mode === "api-key" ? "Đã lưu — nhập key mới để thay thế" : "sk-ant-..."}
              disabled={busy !== null}
              onChange={(event) => setApiKey(event.target.value)}
            />
            <Button
              type="button"
              variant="ghost"
              size="icon-xs"
              className="absolute top-1/2 right-1 -translate-y-1/2"
              aria-label={showApiKey ? "Ẩn API key" : "Hiện API key"}
              onClick={() => setShowApiKey((value) => !value)}
              disabled={busy !== null}
            >
              {showApiKey ? <EyeOff /> : <Eye />}
            </Button>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button size="sm" onClick={() => void saveApiKey()} disabled={busy !== null || !apiKey.trim()}>
              {busy === "save" ? "Đang lưu..." : "Lưu API key"}
            </Button>
            <Button variant="ghost" size="sm" onClick={() => void clearApiKey()} disabled={busy !== null || mode !== "api-key"}>
              {busy === "clear" ? "Đang xoá..." : "Xoá key"}
            </Button>
          </div>
        </div>
      </div>

      {message && <Alert><AlertDescription>{message}</AlertDescription></Alert>}
      {error && (
        <Alert variant="destructive">
          <AlertTitle>Không xử lý được authentication</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </div>
  );
}
