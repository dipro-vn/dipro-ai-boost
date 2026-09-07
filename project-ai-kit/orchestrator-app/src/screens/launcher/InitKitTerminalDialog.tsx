import { useEffect, useRef } from "react";
import { FitAddon } from "@xterm/addon-fit";
import { Terminal } from "@xterm/xterm";
import "@xterm/xterm/css/xterm.css";
import { CheckCircle2, CircleStop, LoaderCircle, RotateCcw } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { TerminalFrame } from "@/screens/board/TerminalFrame";
import { commands } from "@/lib/tauri-client";

export type InitKitPhase = "starting" | "running" | "finished" | "failed";

interface InitKitTerminalDialogProps {
  open: boolean;
  projectName: string;
  sessionId: string | null;
  output: string[];
  phase: InitKitPhase;
  stopped: boolean;
  errorMessage: string | null;
  onOpenChange: (open: boolean) => void;
  onStop: () => void;
  onRetry: () => void;
}

export function InitKitTerminalDialog({
  open,
  projectName,
  sessionId,
  output,
  phase,
  stopped,
  errorMessage,
  onOpenChange,
  onStop,
  onRetry,
}: InitKitTerminalDialogProps) {
  const terminalContainerRef = useRef<HTMLDivElement>(null);
  const terminalRef = useRef<Terminal | null>(null);
  const writtenChunksRef = useRef(0);
  const resizeObserverRef = useRef<ResizeObserver | null>(null);

  useEffect(() => {
    if (!open || !sessionId || !terminalContainerRef.current) return;

    const terminal = new Terminal({
      cursorBlink: true,
      fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
      fontSize: 13,
      scrollback: 10_000,
      theme: {
        background: "#09090b",
        foreground: "#f4f4f5",
        cursor: "#f4f4f5",
      },
    });
    const fitAddon = new FitAddon();
    terminal.loadAddon(fitAddon);
    terminal.open(terminalContainerRef.current);
    terminalRef.current = terminal;
    writtenChunksRef.current = 0;

    const fitAndResize = () => {
      fitAddon.fit();
      void commands.resizeInitKit(sessionId, terminal.cols, terminal.rows);
    };
    const dataSubscription = terminal.onData((data) => {
      void commands.sendInitKitInput(sessionId, data);
    });
    resizeObserverRef.current = new ResizeObserver(fitAndResize);
    resizeObserverRef.current.observe(terminalContainerRef.current);
    fitAndResize();
    terminal.focus();

    return () => {
      dataSubscription.dispose();
      resizeObserverRef.current?.disconnect();
      resizeObserverRef.current = null;
      terminal.dispose();
      terminalRef.current = null;
    };
  }, [open, sessionId]);

  useEffect(() => {
    const terminal = terminalRef.current;
    if (!terminal) return;
    if (writtenChunksRef.current > output.length) {
      terminal.reset();
      writtenChunksRef.current = 0;
    }
    for (const chunk of output.slice(writtenChunksRef.current)) {
      terminal.write(chunk);
    }
    writtenChunksRef.current = output.length;
  }, [output]);

  const active = phase === "starting" || phase === "running";
  const title = active
    ? "Claude /init-kit đang chạy"
    : phase === "finished" && !stopped
      ? "Claude /init-kit đã kết thúc"
      : "Claude /init-kit đã dừng";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex h-[88vh] max-w-5xl flex-col overflow-hidden sm:max-w-5xl">
        <DialogHeader className="pr-8">
          <DialogTitle className="flex items-center gap-2">
            {active ? <LoaderCircle className="animate-spin" /> : <CheckCircle2 />}
            Khởi tạo project: {projectName}
          </DialogTitle>
          <DialogDescription>
            Claude đang chạy trực tiếp trong app. Trả lời các câu hỏi của init-agent ngay trong terminal.
          </DialogDescription>
        </DialogHeader>

        {errorMessage && (
          <div className="rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {errorMessage}
          </div>
        )}

        <div className="min-h-0 flex-1">
          <TerminalFrame title={`${projectName} — ${title}`} className="h-full">
            <div ref={terminalContainerRef} className="h-full min-h-0 w-full p-2" />
          </TerminalFrame>
        </div>

        <DialogFooter className="shrink-0">
          {active ? (
            <Button type="button" variant="destructive" onClick={onStop}>
              <CircleStop />
              Dừng init-kit
            </Button>
          ) : (
            <Button type="button" variant="outline" onClick={onRetry}>
              <RotateCcw />
              Chạy lại init-kit
            </Button>
          )}
          <Button type="button" onClick={() => onOpenChange(false)}>
            {active ? "Ẩn terminal" : "Đóng"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
