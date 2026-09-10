import { useEffect, useState } from "react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { commands, isAppCommandError, type GateState } from "@/lib/tauri-client";
import { ArtifactModal } from "@/screens/board/ArtifactModal";
import { PreviewBox } from "@/screens/board/PreviewBox";
import { MarkdownRenderer } from "@/screens/viewer/MarkdownRenderer";
import { VersionCompareDialog } from "@/screens/viewer/VersionCompareDialog";

/** The Trigger gate is always about `ba-agent`'s `SPEC.md` — there is no
 * other slot it could concern (AC-E4-01..07 only ever mention `ba-agent`). */
const BA_SLOT = "ba";

function extractErrorMessage(err: unknown): string {
  if (isAppCommandError(err)) return err.message;
  if (err instanceof Error) return err.message;
  return String(err);
}

interface TriggerGatePanelProps {
  feature: string;
  gateState: GateState | undefined;
}

/**
 * AC-E4-01/02/03/04/05/06/07 — `OR_GATE_001` equivalent. State comes purely
 * from `gateState.status` (already computed server-side by
 * `inference::gate_rules`); this component never re-derives the open
 * condition itself. `EVENT_STATE_CHANGED` (already wired in
 * `PipelineBoardScreen`) is what refreshes `gateState` after any action
 * here — no manual refetch needed, same as every other panel in the app.
 */
export function TriggerGatePanel({ feature, gateState }: TriggerGatePanelProps) {
  const status = gateState?.status ?? "not-ready";
  const missingSections = gateState?.missingSections ?? [];

  const [specPath, setSpecPath] = useState<string | null>(null);
  const [specContent, setSpecContent] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [showCompare, setShowCompare] = useState(false);
  const [showFullSpec, setShowFullSpec] = useState(false);

  const [comment, setComment] = useState("");
  const [requestingChanges, setRequestingChanges] = useState(false);
  const [requestError, setRequestError] = useState<string | null>(null);
  const [resumeFailed, setResumeFailed] = useState(false);

  const [approverName, setApproverName] = useState("");
  const [approving, setApproving] = useState(false);
  const [approveError, setApproveError] = useState<string | null>(null);

  useEffect(() => {
    if (status === "not-ready") {
      setSpecPath(null);
      setSpecContent(null);
      return;
    }
    let cancelled = false;
    setLoadError(null);
    commands
      .getNodeDetail(feature, BA_SLOT)
      .then((detail) => {
        if (cancelled) return;
        const path = detail.artifacts[0]?.path ?? null;
        setSpecPath(path);
        if (!path) return undefined;
        return commands.readArtifact(path).then((artifact) => {
          if (!cancelled) setSpecContent(artifact.content);
        });
      })
      .catch((err) => {
        if (!cancelled) setLoadError(extractErrorMessage(err));
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [feature, status]);

  async function handleRequestChanges() {
    if (!comment.trim()) return;
    setRequestingChanges(true);
    setRequestError(null);
    setResumeFailed(false);
    try {
      // AC-E4-04 — same session, via the exact mechanism AC-E2-17 already
      // built (`--resume <session_id>`), just with a PM-authored prompt.
      await commands.sendClarificationAnswer(
        feature,
        BA_SLOT,
        `PM yêu cầu chỉnh sửa SPEC.md — lý do:\n${comment.trim()}`,
      );
      setComment("");
    } catch (err) {
      // AC-E4-05 — session couldn't resume; report clearly and offer the
      // from-scratch fallback below rather than failing silently.
      setRequestError(extractErrorMessage(err));
      setResumeFailed(true);
    } finally {
      setRequestingChanges(false);
    }
  }

  async function handleRerunFromScratch() {
    setRequestingChanges(true);
    setRequestError(null);
    try {
      const summary = await commands.getRunSummary(feature, BA_SLOT);
      const basePrompt = summary?.prompt;
      if (!basePrompt) {
        setRequestError(
          "Không tìm thấy input ban đầu để chạy lại tự động — hãy chạy lại BA Agent thủ công ở bước ①.",
        );
        return;
      }
      const combined = comment.trim()
        ? `${basePrompt}\n\nPM yêu cầu sửa: ${comment.trim()}`
        : basePrompt;
      await commands.startRun(feature, BA_SLOT, combined);
      setComment("");
      setResumeFailed(false);
    } catch (err) {
      setRequestError(extractErrorMessage(err));
    } finally {
      setRequestingChanges(false);
    }
  }

  async function handleApprove() {
    if (!approverName.trim()) return;
    setApproving(true);
    setApproveError(null);
    try {
      // AC-E4-07 — writes the approval and spawns stage ② in parallel;
      // the resulting `EVENT_STATE_CHANGED` is what flips `gateState` to
      // "approved" for this component.
      await commands.approveTriggerGate(feature, approverName.trim());
    } catch (err) {
      setApproveError(extractErrorMessage(err));
    } finally {
      setApproving(false);
    }
  }

  /** Preview SPEC.md dùng chung cho cả `pending-review` và `approved` —
   * khung cuộn thấp trong `ActionPanel` chỉ để liếc, nút phóng to mới là
   * chỗ đọc thật. */
  function renderSpecPreview() {
    if (!specContent || !specPath) return null;
    return (
      <PreviewBox
        label={specPath}
        maxHeightClass="max-h-80"
        onExpand={() => setShowFullSpec(true)}
      >
        <MarkdownRenderer content={specContent} />
      </PreviewBox>
    );
  }

  /** Phải render trong từng nhánh status — component thoát sớm ở mỗi nhánh. */
  function renderSpecModal() {
    return (
      <ArtifactModal
        path={showFullSpec ? specPath : null}
        onClose={() => setShowFullSpec(false)}
      />
    );
  }

  if (status === "not-ready") {
    return (
      <div className="flex flex-col gap-3 rounded-lg border border-border p-3">
        <p className="text-sm text-muted-foreground">
          Chờ BA Agent hoàn thành SPEC.md đầy đủ các section bắt buộc trước khi gate này mở.
        </p>
        {missingSections.length > 0 && (
          <div className="flex flex-col gap-1">
            <p className="text-xs font-medium text-muted-foreground">Section còn thiếu:</p>
            <ul className="list-inside list-disc text-xs text-muted-foreground">
              {missingSections.map((section) => (
                <li key={section}>{section}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  }

  if (status === "approved") {
    return (
      <div className="flex flex-col gap-3">
        <Alert>
          <AlertTitle>Đã duyệt</AlertTitle>
          <AlertDescription>
            Duyệt bởi <strong>{gateState?.approvedBy}</strong>
            {gateState?.approvedAt ? ` lúc ${gateState.approvedAt}` : ""} — stage ② đã được spawn.
          </AlertDescription>
        </Alert>
        {loadError && (
          <Alert variant="destructive">
            <AlertTitle>Không đọc được SPEC.md</AlertTitle>
            <AlertDescription>{loadError}</AlertDescription>
          </Alert>
        )}
        {renderSpecPreview()}
        {renderSpecModal()}
      </div>
    );
  }

  // status === "pending-review"
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="secondary">Chờ duyệt</Badge>
        <Badge variant="secondary">Đủ section</Badge>
        {specPath && (
          <Button variant="outline" size="sm" onClick={() => setShowCompare(true)}>
            So sánh với lần trước
          </Button>
        )}
      </div>

      {loadError && (
        <Alert variant="destructive">
          <AlertTitle>Không đọc được SPEC.md</AlertTitle>
          <AlertDescription>{loadError}</AlertDescription>
        </Alert>
      )}

      {renderSpecPreview()}

      <Separator />

      <div className="flex flex-col gap-2">
        <label
          className="text-xs font-medium text-muted-foreground"
          htmlFor={`gate-comment-${feature}`}
        >
          Nhận xét (bắt buộc để Request changes)
        </label>
        <textarea
          id={`gate-comment-${feature}`}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          rows={3}
          placeholder="Mô tả điều cần sửa trong SPEC.md..."
          className="rounded-lg border border-input bg-transparent px-3 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
        />
        {requestError && (
          <Alert variant="destructive">
            <AlertTitle>Không gửi được yêu cầu sửa</AlertTitle>
            <AlertDescription>{requestError}</AlertDescription>
          </Alert>
        )}
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            disabled={!comment.trim() || requestingChanges}
            onClick={handleRequestChanges}
          >
            {requestingChanges ? "Đang gửi..." : "Yêu cầu sửa"}
          </Button>
          {resumeFailed && (
            <Button
              variant="outline"
              disabled={requestingChanges}
              onClick={handleRerunFromScratch}
            >
              Chạy lại ba-agent từ đầu (giữ nhận xét)
            </Button>
          )}
        </div>
      </div>

      <Separator />

      <div className="flex flex-col gap-2">
        <label
          className="text-xs font-medium text-muted-foreground"
          htmlFor={`gate-approver-${feature}`}
        >
          Tên người duyệt
        </label>
        <div className="flex gap-2">
          <Input
            id={`gate-approver-${feature}`}
            value={approverName}
            onChange={(e) => setApproverName(e.target.value)}
            placeholder="vd: Nguyễn Văn A"
          />
          <Button disabled={!approverName.trim() || approving} onClick={handleApprove}>
            {approving ? "Đang duyệt..." : "Approve"}
          </Button>
        </div>
        {approveError && (
          <Alert variant="destructive">
            <AlertTitle>Không duyệt được</AlertTitle>
            <AlertDescription>{approveError}</AlertDescription>
          </Alert>
        )}
        <p className="text-xs text-muted-foreground">
          v1 không xác thực danh tính — tên này chỉ được ghi lại, không xác minh.
        </p>
      </div>

      {specPath && (
        <VersionCompareDialog path={specPath} open={showCompare} onOpenChange={setShowCompare} />
      )}
      {renderSpecModal()}
    </div>
  );
}
