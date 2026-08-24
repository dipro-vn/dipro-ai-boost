import { useEffect, useState } from "react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import {
  commands,
  isAppCommandError,
  type ContractLockRecord,
  type ContractLockState,
  type FileViolation,
} from "@/lib/tauri-client";
import { ArtifactModal } from "@/screens/board/ArtifactModal";
import { DiffModal } from "@/screens/board/DiffModal";
import { DiffView } from "@/screens/board/DiffView";
import { PreviewBox } from "@/screens/board/PreviewBox";
import { MarkdownRenderer } from "@/screens/viewer/MarkdownRenderer";

/** Mirrors `domain::contract_lock::ALL_ROLES` — display order. */
const ALL_ROLES = ["BE", "FE", "Mobile", "PM", "QC"] as const;

function extractErrorMessage(err: unknown): string {
  if (isAppCommandError(err)) return err.message;
  if (err instanceof Error) return err.message;
  return String(err);
}

interface ContractLockPanelProps {
  feature: string;
  contractLockState: ContractLockState | undefined;
}

/**
 * AC-E4-08..20 — `OR_GATE_002` equivalent for Phase 2a (create + view
 * history; violation detection is Phase 2b). Same structural pattern as
 * `TriggerGatePanel`: state comes purely from `contractLockState.status`
 * (already computed server-side), refreshed via the existing
 * `EVENT_STATE_CHANGED` push — no manual refetch after an action.
 */
export function ContractLockPanel({ feature, contractLockState }: ContractLockPanelProps) {
  const status = contractLockState?.status ?? "not-ready";
  const missingColumns = contractLockState?.missingColumns ?? [];
  const planMdMissing = contractLockState?.planMdMissing ?? false;
  const applicableRoles = contractLockState?.applicableRoles ?? [];
  const candidateFiles = contractLockState?.candidateFiles ?? [];
  const violatedFiles = contractLockState?.violatedFiles ?? [];
  const runningOnOldContract = contractLockState?.runningOnOldContract ?? false;

  const [fileContents, setFileContents] = useState<Record<string, string>>({});
  const [loadError, setLoadError] = useState<string | null>(null);
  const [currentContents, setCurrentContents] = useState<Record<string, string>>({});

  const [confirmedRoles, setConfirmedRoles] = useState<Set<string>>(new Set());
  const [approverName, setApproverName] = useState("");
  const [locking, setLocking] = useState(false);
  const [lockError, setLockError] = useState<string | null>(null);

  const [showHistory, setShowHistory] = useState(false);
  const [history, setHistory] = useState<ContractLockRecord[] | null>(null);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [expandedLock, setExpandedLock] = useState<number | null>(null);

  /** Nội dung xem toàn màn hình. `content` chỉ có ở bản chụp đã khoá — file
   * trên đĩa lúc đó có thể đã đổi hoặc bị xoá, không đọc lại được. */
  const [preview, setPreview] = useState<
    { path: string; content?: string; subtitle?: string } | null
  >(null);
  const [diffTarget, setDiffTarget] = useState<FileViolation | null>(null);

  // Pre-lock file content preview (AC-E4-16 shows checksum; also render
  // content for context, same pattern `TriggerGatePanel` uses for SPEC.md).
  useEffect(() => {
    if (status !== "pending-review" || candidateFiles.length === 0) {
      setFileContents({});
      return;
    }
    let cancelled = false;
    setLoadError(null);
    Promise.all(
      candidateFiles.map((f) =>
        commands.readArtifact(f.path).then((artifact) => [f.path, artifact.content] as const),
      ),
    )
      .then((entries) => {
        if (!cancelled) setFileContents(Object.fromEntries(entries));
      })
      .catch((err) => {
        if (!cancelled) setLoadError(extractErrorMessage(err));
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [feature, status, candidateFiles.map((f) => f.path).join(",")]);

  // AC-E4-25 — current content for each `Modified` violated file, to diff
  // against `FileViolation.lockedContent`. `Deleted` files have nothing to
  // fetch — the file is gone, that's the whole point.
  useEffect(() => {
    const modifiedPaths = violatedFiles.filter((f) => f.kind === "modified").map((f) => f.path);
    if (status !== "violated" || modifiedPaths.length === 0) {
      setCurrentContents({});
      return;
    }
    let cancelled = false;
    Promise.all(
      modifiedPaths.map((path) =>
        commands.readArtifact(path).then((artifact) => [path, artifact.content] as const),
      ),
    ).then((entries) => {
      if (!cancelled) setCurrentContents(Object.fromEntries(entries));
    });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [feature, status, violatedFiles.map((f) => f.path).join(",")]);

  function toggleRole(role: string) {
    setConfirmedRoles((prev) => {
      const next = new Set(prev);
      if (next.has(role)) next.delete(role);
      else next.add(role);
      return next;
    });
  }

  const allApplicableConfirmed = applicableRoles.every((role) => confirmedRoles.has(role));
  const canLock = allApplicableConfirmed && approverName.trim().length > 0 && !locking;

  async function handleLock() {
    if (!canLock) return;
    setLocking(true);
    setLockError(null);
    try {
      await commands.lockContract(feature, approverName.trim(), Array.from(confirmedRoles));
    } catch (err) {
      setLockError(extractErrorMessage(err));
    } finally {
      setLocking(false);
    }
  }

  /** Shared by `pending-review` (Lock) and `violated` (Re-lock, AC-E4-27) —
   * identical role-confirmation + approver-name form either way. */
  function renderRoleAndApproverForm(buttonLabel: string) {
    return (
      <>
        <div className="flex flex-col gap-2">
          <p className="text-xs font-medium text-muted-foreground">Xác nhận vai trò</p>
          <div className="flex flex-wrap gap-2">
            {ALL_ROLES.map((role) => {
              const applicable = applicableRoles.includes(role);
              const active = confirmedRoles.has(role);
              return (
                <button
                  key={role}
                  type="button"
                  disabled={!applicable}
                  onClick={() => applicable && toggleRole(role)}
                  className={cn(
                    "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                    !applicable && "cursor-not-allowed border-border text-muted-foreground/50",
                    applicable && active && "border-success bg-success/15 text-success",
                    applicable && !active && "border-border text-muted-foreground hover:bg-muted",
                  )}
                >
                  {role}
                  {!applicable ? " — n/a" : active ? " ✓" : ""}
                </button>
              );
            })}
          </div>
          <p className="text-xs text-muted-foreground">
            v1 không xác thực danh tính — các ô này chỉ ghi nhận vai trò, do một người thao tác.
          </p>
        </div>

        <div className="flex flex-col gap-2">
          <label
            className="text-xs font-medium text-muted-foreground"
            htmlFor={`lock-approver-${feature}`}
          >
            Tên người duyệt
          </label>
          <div className="flex gap-2">
            <Input
              id={`lock-approver-${feature}`}
              value={approverName}
              onChange={(e) => setApproverName(e.target.value)}
              placeholder="vd: Nguyễn Văn A"
            />
            <Button disabled={!canLock} onClick={handleLock}>
              {locking ? "Đang khoá..." : buttonLabel}
            </Button>
          </div>
          {lockError && (
            <Alert variant="destructive">
              <AlertTitle>Không khoá được</AlertTitle>
              <AlertDescription>{lockError}</AlertDescription>
            </Alert>
          )}
        </div>
      </>
    );
  }

  function handleToggleHistory() {
    const next = !showHistory;
    setShowHistory(next);
    if (next && history === null) {
      setHistoryError(null);
      commands
        .listContractLocks(feature)
        .then(setHistory)
        .catch((err) => setHistoryError(extractErrorMessage(err)));
    }
  }

  /** Phải render trong từng nhánh status — component thoát sớm ở mỗi nhánh. */
  function renderPreviewModal() {
    return (
      <ArtifactModal
        path={preview?.path ?? null}
        content={preview?.content}
        subtitle={preview?.subtitle}
        onClose={() => setPreview(null)}
      />
    );
  }

  if (status === "not-ready") {
    return (
      <div className="flex flex-col gap-3 rounded-lg border border-border p-3">
        <p className="text-sm text-muted-foreground">
          Chưa tìm thấy bảng "API Definition" trong <code>DESIGN.md</code> nào của feature này —
          Contract Lock chưa mở được.
        </p>
        {planMdMissing && (
          <p className="text-xs text-muted-foreground">
            (Lưu ý: <code>PLAN.md</code> cũng chưa tồn tại — không chặn gate, chỉ là cảnh báo.)
          </p>
        )}
      </div>
    );
  }

  if (status === "not-applicable") {
    return (
      <div className="flex flex-col gap-2 rounded-lg border border-border p-3">
        <Badge variant="secondary">Không áp dụng</Badge>
        <p className="text-sm text-muted-foreground">{contractLockState?.notApplicableReason}</p>
      </div>
    );
  }

  const currentLock = contractLockState?.currentLock;

  if (status === "locked") {
    return (
      <div className="flex flex-col gap-3">
        <Alert>
          <AlertTitle>Đã khoá</AlertTitle>
          <AlertDescription>
            Khoá bởi <strong>{currentLock?.approvedBy}</strong>
            {currentLock?.lockedAt ? ` lúc ${currentLock.lockedAt}` : ""} — vai trò xác nhận:{" "}
            {currentLock?.confirmedRoles.join(", ")}. <code>backend-agent</code> đã được spawn.
          </AlertDescription>
        </Alert>

        <div className="flex flex-col gap-1">
          <p className="text-xs font-medium text-muted-foreground">File đã khoá</p>
          <ul className="flex flex-col gap-1">
            {currentLock?.files.map((f) => (
              <li key={f.path} className="font-mono text-xs text-muted-foreground" title={f.checksumSha256}>
                {f.path}
              </li>
            ))}
          </ul>
        </div>

        <Separator />

        <Button variant="outline" size="sm" onClick={handleToggleHistory}>
          {showHistory ? "Ẩn lịch sử lock" : "Xem lịch sử lock"}
        </Button>

        {showHistory && (
          <div className="flex flex-col gap-2">
            {historyError && (
              <Alert variant="destructive">
                <AlertTitle>Không lấy được lịch sử</AlertTitle>
                <AlertDescription>{historyError}</AlertDescription>
              </Alert>
            )}
            {history === null && !historyError && (
              <div className="flex flex-col gap-2">
                <div className="skeleton h-8 w-full" />
                <div className="skeleton h-8 w-full" />
              </div>
            )}
            {history?.map((record, index) => (
              <div key={`${record.lockedAt}-${index}`} className="rounded-lg border border-border p-2">
                <button
                  type="button"
                  className="flex w-full items-center justify-between text-left text-xs"
                  onClick={() => setExpandedLock(expandedLock === index ? null : index)}
                >
                  <span>
                    {record.lockedAt} — {record.approvedBy}
                  </span>
                  <span className="text-muted-foreground">
                    {expandedLock === index ? "Thu gọn" : "Xem nội dung"}
                  </span>
                </button>
                {expandedLock === index && (
                  <div className="mt-2 flex flex-col gap-3">
                    {record.files.map((f) => (
                      <PreviewBox
                        key={f.path}
                        label={f.path}
                        maxHeightClass="max-h-64"
                        onExpand={() =>
                          setPreview({
                            path: f.path,
                            content: f.content,
                            subtitle: `Nội dung tại thời điểm khoá — ${record.lockedAt}`,
                          })
                        }
                      >
                        <MarkdownRenderer content={f.content} />
                      </PreviewBox>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {renderPreviewModal()}
      </div>
    );
  }

  if (status === "violated") {
    return (
      <div className="flex flex-col gap-4">
        <Alert variant="destructive">
          <AlertTitle>Contract vi phạm</AlertTitle>
          <AlertDescription>
            {violatedFiles.length} file không còn khớp với nội dung đã khoá. Cần Re-lock để tiếp
            tục — stage ⑤+ sẽ không spawn thêm agent nào cho tới lúc đó (AC-E4-23).
          </AlertDescription>
        </Alert>

        {runningOnOldContract && (
          <Alert>
            <AlertTitle>backend-agent đang chạy trên contract cũ</AlertTitle>
            <AlertDescription>
              Agent đang chạy dở không bị dừng, nhưng đang làm việc trên nội dung đã lỗi thời.
            </AlertDescription>
          </Alert>
        )}

        <div className="flex flex-col gap-4">
          {violatedFiles.map((f) =>
            f.kind === "deleted" ? (
              <PreviewBox
                key={f.path}
                label={`${f.path} — đã bị xoá`}
                labelTitle={f.path}
                maxHeightClass="max-h-64"
                onExpand={() =>
                  setPreview({
                    path: f.path,
                    content: f.lockedContent,
                    subtitle: "Nội dung tại thời điểm khoá — file đã bị xoá",
                  })
                }
              >
                <MarkdownRenderer content={f.lockedContent} />
              </PreviewBox>
            ) : currentContents[f.path] ? (
              <PreviewBox
                key={f.path}
                label={`${f.path} — đã bị sửa`}
                labelTitle={f.path}
                maxHeightClass="max-h-64"
                expandLabel="Xem toàn bộ diff"
                onExpand={() => setDiffTarget(f)}
              >
                <DiffView path={f.path} oldValue={f.lockedContent} newValue={currentContents[f.path]} />
              </PreviewBox>
            ) : (
              <div key={f.path} className="flex flex-col gap-2">
                <p className="font-mono text-xs text-muted-foreground">{f.path} — đã bị sửa</p>
                <p className="text-xs text-muted-foreground">Đang tải nội dung hiện tại...</p>
              </div>
            ),
          )}
        </div>

        <p className="text-xs text-muted-foreground">
          App không tự sửa hay hoàn tác file — chỉ hiển thị diff và đường dẫn ở trên để tự xử lý
          bên ngoài (AC-E4-28).
        </p>

        <Separator />

        {renderRoleAndApproverForm("Re-lock")}

        {renderPreviewModal()}
        <DiffModal
          path={diffTarget?.path ?? null}
          oldValue={diffTarget?.lockedContent ?? ""}
          newValue={diffTarget ? (currentContents[diffTarget.path] ?? "") : ""}
          onClose={() => setDiffTarget(null)}
        />
      </div>
    );
  }

  // status === "pending-review"
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="secondary">Chờ duyệt</Badge>
      </div>

      {missingColumns.length > 0 && (
        <Alert variant="destructive">
          <AlertTitle>Bảng API Definition thiếu cột</AlertTitle>
          <AlertDescription>{missingColumns.join(", ")}</AlertDescription>
        </Alert>
      )}
      {planMdMissing && (
        <Alert>
          <AlertTitle>Chưa có PLAN.md</AlertTitle>
          <AlertDescription>Không chặn gate — chỉ là cảnh báo.</AlertDescription>
        </Alert>
      )}
      {loadError && (
        <Alert variant="destructive">
          <AlertTitle>Không đọc được file</AlertTitle>
          <AlertDescription>{loadError}</AlertDescription>
        </Alert>
      )}

      <div className="flex flex-col gap-3">
        <p className="text-xs font-medium text-muted-foreground">
          File sẽ đưa vào khoá ({candidateFiles.length})
        </p>
        {candidateFiles.map((f) => (
          <PreviewBox
            key={f.path}
            label={f.path}
            labelTitle={f.checksumSha256}
            maxHeightClass="max-h-64"
            onExpand={() => setPreview({ path: f.path })}
            expandDisabled={!fileContents[f.path]}
          >
            {fileContents[f.path] && <MarkdownRenderer content={fileContents[f.path]} />}
          </PreviewBox>
        ))}
      </div>

      <Separator />

      {renderRoleAndApproverForm("Lock")}

      {renderPreviewModal()}
    </div>
  );
}
