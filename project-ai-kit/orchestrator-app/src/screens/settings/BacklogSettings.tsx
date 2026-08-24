import { useCallback, useEffect, useState } from "react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { commands, isAppCommandError, type BacklogStatus } from "@/lib/tauri-client";

function extractErrorMessage(err: unknown): string {
  if (isAppCommandError(err)) return err.message;
  if (err instanceof Error) return err.message;
  return String(err);
}

/**
 * Settings › Integrations › Backlog (AC-E1-19..22).
 *
 * The API key lives in component state only long enough to be handed to the
 * backend, which stores it in the OS keychain — it is never written to
 * `config.json`, never logged, and never read back (a saved key comes back
 * as `configured: true`, never as a value).
 */
export function BacklogSettings() {
  const [status, setStatus] = useState<BacklogStatus | null>(null);
  const [domain, setDomain] = useState("");
  const [projectKey, setProjectKey] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [busy, setBusy] = useState<null | "test" | "save" | "clear">(null);
  const [okMessage, setOkMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const load = useCallback(() => {
    commands
      .getBacklogStatus()
      .then((next) => {
        setStatus(next);
        setDomain(next.domain);
        setProjectKey(next.projectKey);
      })
      .catch((err) => setErrorMessage(extractErrorMessage(err)));
  }, []);

  useEffect(load, [load]);

  const keychainBlocked = status !== null && !status.keychainAvailable;
  const disabled = busy !== null || keychainBlocked;

  async function handleTest() {
    setBusy("test");
    setOkMessage(null);
    setErrorMessage(null);
    try {
      const who = await commands.testBacklogConnection(domain, apiKey);
      setOkMessage(`Kết nối OK — Backlog nhận diện bạn là: ${who}`);
    } catch (err) {
      // AC-E1-21 — the backend's verbatim message (HTTP code + body, minus
      // the key) is shown as-is; nothing is prettified away.
      setErrorMessage(extractErrorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  async function handleSave() {
    setBusy("save");
    setOkMessage(null);
    setErrorMessage(null);
    try {
      const who = await commands.saveBacklogCredentials(domain, projectKey, apiKey);
      setApiKey("");
      setOkMessage(`Đã lưu — API key nằm trong OS keychain. Tài khoản: ${who}`);
      load();
    } catch (err) {
      setErrorMessage(extractErrorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  async function handleClear() {
    setBusy("clear");
    setOkMessage(null);
    setErrorMessage(null);
    try {
      await commands.clearBacklogCredentials();
      setApiKey("");
      setOkMessage("Đã xoá cấu hình Backlog khỏi config.json và OS keychain.");
      load();
    } catch (err) {
      setErrorMessage(extractErrorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold">Backlog</h3>
          {status?.configured && <Badge variant="secondary">Đã cấu hình</Badge>}
        </div>
        <p className="text-xs text-muted-foreground">
          Dùng cho phần <strong>kéo trạng thái issue về</strong> (đọc, mỗi 15 phút). Phần{" "}
          <strong>đẩy issue lên</strong> đi qua <code>pm-agent</code> + MCP Backlog của project
          nên không cần credentials ở đây.
        </p>
      </div>

      {keychainBlocked && (
        <Alert variant="destructive">
          <AlertTitle>OS keychain không truy cập được</AlertTitle>
          <AlertDescription>
            {status?.keychainError ?? "Không rõ nguyên nhân."} Phần tích hợp bị vô hiệu hoá — app
            không ghi API key ra file dưới bất kỳ dạng nào.
          </AlertDescription>
        </Alert>
      )}

      <div className="grid gap-3 sm:max-w-lg">
        <div className="flex flex-col gap-1">
          <Label htmlFor="backlog-domain">Domain</Label>
          <Input
            id="backlog-domain"
            value={domain}
            disabled={disabled}
            placeholder="vd: example.backlog.com"
            onChange={(e) => setDomain(e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor="backlog-project">Project key</Label>
          <Input
            id="backlog-project"
            value={projectKey}
            disabled={disabled}
            placeholder="vd: PROJ (phần đầu của issue key PROJ-123)"
            onChange={(e) => setProjectKey(e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor="backlog-key">API key</Label>
          <Input
            id="backlog-key"
            type="password"
            autoComplete="off"
            value={apiKey}
            disabled={disabled}
            placeholder={
              status?.configured ? "Đã lưu trong keychain — nhập lại nếu muốn đổi" : "Dán API key"
            }
            onChange={(e) => setApiKey(e.target.value)}
          />
          <p className="text-xs text-muted-foreground">
            Lưu vào OS keychain, không bao giờ ghi vào <code>config.json</code> — mở file đó chỉ
            thấy domain, project key và tên tham chiếu.
          </p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button variant="outline" onClick={handleTest} disabled={disabled || !apiKey}>
          {busy === "test" ? "Đang kiểm tra..." : "Kiểm tra kết nối"}
        </Button>
        <Button onClick={handleSave} disabled={disabled || !apiKey}>
          {busy === "save" ? "Đang lưu..." : "Lưu"}
        </Button>
        {status?.configured && (
          <Button variant="ghost" onClick={handleClear} disabled={disabled}>
            Xoá cấu hình
          </Button>
        )}
      </div>

      {okMessage && (
        <Alert>
          <AlertTitle>Thành công</AlertTitle>
          <AlertDescription>{okMessage}</AlertDescription>
        </Alert>
      )}
      {errorMessage && (
        <Alert variant="destructive">
          <AlertTitle>Không thành công</AlertTitle>
          <AlertDescription className="font-mono text-xs break-all">
            {errorMessage}
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
