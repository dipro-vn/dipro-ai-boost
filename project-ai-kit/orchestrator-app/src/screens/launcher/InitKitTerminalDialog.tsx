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

/** Chuỗi IME mà cầu nối đã gửi được nhớ trong ngần này, đủ để nhận ra bản sao
 * xterm phát ra sau đó. xterm phát trong một `setTimeout(0)`, nhưng lúc main
 * thread đang bận vẽ TUI thì nhịp đó trôi khá xa. */
const COMPOSITION_ECHO_MS = 500;

/** Kích thước chỗ đỗ lúc terminal chưa từng được hiển thị lần nào. */
const PARKED_WIDTH = 800;
const PARKED_HEIGHT = 480;

/** Đưa host ra ngoài màn hình nhưng GIỮ NGUYÊN kích thước pixel.
 *
 * Không dùng `display:none`/`visibility:hidden`: xterm đo được 0 thì cols/rows
 * tụt về mặc định và toàn bộ khung hình vỡ. Giữ đúng kích thước lúc đang hiện
 * còn để `ResizeObserver` không bắn — PTY không bị resize, Claude không phải
 * vẽ lại, nên mở lại là thấy y nguyên khung hình lúc đóng. */
function parkHost(host: HTMLDivElement, width: number, height: number) {
  host.style.position = "fixed";
  host.style.left = "-100000px";
  host.style.top = "0";
  host.style.width = `${width}px`;
  host.style.height = `${height}px`;
  // Vẫn nằm trong layout thì textarea của xterm vẫn tab tới được dù không ai
  // thấy nó. `inert` gỡ khỏi tab order và a11y tree mà không đụng tới kích
  // thước — khác `visibility: hidden`, thứ làm xterm đo ra 0.
  host.inert = true;
}

function fillHost(host: HTMLDivElement) {
  host.style.position = "static";
  host.style.left = "";
  host.style.top = "";
  host.style.width = "100%";
  host.style.height = "100%";
  host.inert = false;
}

export type InitKitPhase = "starting" | "running" | "finished" | "failed";

interface InitKitTerminalDialogProps {
  open: boolean;
  projectName: string;
  sessionId: string | null;
  output: string[];
  /** Tổng số chunk từ đầu phiên, kể cả chunk đã bị cắt khỏi `output`. Terminal
   * đo tiến độ bằng con số này chứ không bằng `output.length`: khi bộ đệm chạm
   * trần thì `output.length` đứng yên trong lúc dữ liệu mới vẫn về. */
  outputTotal: number;
  phase: InitKitPhase;
  stopped: boolean;
  errorMessage: string | null;
  /** Những mục app còn thấy thiếu trong `AGENTS.md`, đọc từ vòng poll. Terminal
   * chỉ tự đóng khi danh sách này rỗng. */
  pendingReasons: string[];
  onOpenChange: (open: boolean) => void;
  onStop: () => void;
  onRetry: () => void;
}

export function InitKitTerminalDialog({
  open,
  projectName,
  sessionId,
  output,
  outputTotal,
  phase,
  stopped,
  errorMessage,
  pendingReasons,
  onOpenChange,
  onStop,
  onRetry,
}: InitKitTerminalDialogProps) {
  /** Ô trong dialog để cắm terminal vào khi dialog mở. */
  const terminalSlotRef = useRef<HTMLDivElement>(null);
  /** Node thật chứa terminal. Nó sống lâu hơn dialog: dialog đóng thì node này
   * chỉ chuyển chỗ đỗ, không bị huỷ. */
  const hostRef = useRef<HTMLDivElement | null>(null);
  const terminalRef = useRef<Terminal | null>(null);
  const fitAndResizeRef = useRef<(() => void) | null>(null);
  /** Kích thước pixel gần nhất lúc terminal đang hiện, để đỗ đúng cỡ đó. */
  const visibleSizeRef = useRef({ width: PARKED_WIDTH, height: PARKED_HEIGHT });
  /** cols/rows đã báo cho PTY, để không bắn IPC lặp mỗi tick ResizeObserver. */
  const sentSizeRef = useRef<{ cols: number; rows: number } | null>(null);
  /** `outputTotal` đã được ghi vào terminal tới đâu. */
  const writtenTotalRef = useRef(0);

  // Vòng đời terminal bám theo `sessionId`, KHÔNG bám theo `open`. Đóng dialog
  // là Radix unmount `DialogContent`, nên effect phụ thuộc `open` sẽ gọi
  // `dispose()` và lần mở lại phải dựng instance rỗng. Phát lại lịch sử ANSI để
  // bù không cứu được: Claude Code là TUI alt-screen, phát lại cả cuốn phim
  // không dựng lại được khung hình hiện tại, mà lúc phát thì terminal còn đang
  // ở 80x24 mặc định nên càng vỡ.
  useEffect(() => {
    if (!sessionId) return;

    const host = document.createElement("div");
    parkHost(host, visibleSizeRef.current.width, visibleSizeRef.current.height);
    document.body.appendChild(host);

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
    terminal.open(host);
    hostRef.current = host;
    terminalRef.current = terminal;
    sentSizeRef.current = null;
    writtenTotalRef.current = 0;

    const fitAndResize = () => {
      if (host.clientWidth === 0 || host.clientHeight === 0) return;
      fitAddon.fit();
      const sent = sentSizeRef.current;
      if (sent && sent.cols === terminal.cols && sent.rows === terminal.rows) {
        return;
      }
      sentSizeRef.current = { cols: terminal.cols, rows: terminal.rows };
      void commands.resizeInitKit(sessionId, terminal.cols, terminal.rows);
    };
    fitAndResizeRef.current = fitAndResize;

    // Một phím không tới được PTY nghĩa là phiên đã chết (Claude thoát, hoặc
    // session bị thay) — im lặng ở đây thì terminal trông y hệt lúc bình thường
    // và người dùng chỉ thấy "gõ không ăn", nên báo thẳng vào terminal.
    let inputFailed = false;
    const send = (data: string) => {
      commands.sendInitKitInput(sessionId, data).catch((err) => {
        if (inputFailed) return;
        inputFailed = true;
        const message = err instanceof Error ? err.message : String(err);
        terminal.write(`\r\n\x1b[31m[app] Không gửi được phím: ${message}\x1b[0m\r\n`);
      });
    };

    /* Cầu nối cho bộ gõ IME (tiếng Việt có dấu, tiếng Nhật, tiếng Trung).
     *
     * Cầu nối gửi NGAY khi `compositionend`, còn `onData` bỏ bản sao xterm phát
     * ra sau đó. Bản trước làm ngược lại — chờ 30ms xem xterm có tự phát không
     * rồi mới gửi thay — và đó là một cuộc đua: main thread bận vẽ TUI thì 30ms
     * trôi qua dễ dàng, thành ra gửi hai lần. Thứ tự ở đây thì luôn xác định:
     * `compositionend` chạy trước, `setTimeout(0)` của xterm chạy sau. */
    const recentComposed: { text: string; at: number }[] = [];
    const dropComposedEcho = (data: string) => {
      const now = Date.now();
      while (recentComposed.length > 0 && now - recentComposed[0].at > COMPOSITION_ECHO_MS) {
        recentComposed.shift();
      }
      const index = recentComposed.findIndex((entry) => entry.text === data);
      if (index === -1) return false;
      recentComposed.splice(index, 1);
      return true;
    };

    const dataSubscription = terminal.onData((data) => {
      if (dropComposedEcho(data)) return;
      send(data);
    });

    const handleCompositionEnd = (event: CompositionEvent) => {
      const composed = event.data;
      // Bắt ở `document` pha capture, không phải ở textarea: khi WebKit không
      // gắn được composition vào textarea của xterm thì sự kiện mang target
      // khác. Dialog này là modal nên không có ô nhập nào khác để nuốt nhầm.
      if (!composed) return;
      recentComposed.push({ text: composed, at: Date.now() });
      send(composed);
      // Dọn luôn textarea: xterm còn một đường phát thứ hai tính diff giá trị
      // textarea sau `input`, và diff đó không phải lúc nào cũng bằng đúng
      // chuỗi vừa ghép nên `dropComposedEcho` có thể không nhận ra. Dọn sạch
      // thì cả hai đường của xterm đều tính ra chuỗi rỗng.
      if (event.target === terminal.textarea && terminal.textarea) {
        terminal.textarea.value = "";
      }
    };
    document.addEventListener("compositionend", handleCompositionEnd, true);

    const resizeObserver = new ResizeObserver(() => {
      if (host.clientWidth > 0 && host.clientHeight > 0) {
        visibleSizeRef.current = {
          width: host.clientWidth,
          height: host.clientHeight,
        };
      }
      fitAndResize();
    });
    resizeObserver.observe(host);

    return () => {
      dataSubscription.dispose();
      document.removeEventListener("compositionend", handleCompositionEnd, true);
      resizeObserver.disconnect();
      terminal.dispose();
      host.remove();
      hostRef.current = null;
      terminalRef.current = null;
      fitAndResizeRef.current = null;
    };
  }, [sessionId]);

  // Mở/ẩn dialog chỉ là chuyển chỗ đỗ của host, không đụng tới terminal.
  useEffect(() => {
    const host = hostRef.current;
    const terminal = terminalRef.current;
    if (!host || !terminal) return;

    if (open) {
      const slot = terminalSlotRef.current;
      if (!slot) return;
      fillHost(host);
      slot.appendChild(host);
      fitAndResizeRef.current?.();
      terminal.focus();
      return;
    }

    parkHost(host, visibleSizeRef.current.width, visibleSizeRef.current.height);
    document.body.appendChild(host);
  }, [open, sessionId]);

  useEffect(() => {
    const terminal = terminalRef.current;
    if (!terminal) return;
    // Tổng lùi lại nghĩa là phiên khác đã bắt đầu — vẽ lại từ đầu.
    if (outputTotal < writtenTotalRef.current) {
      terminal.reset();
      writtenTotalRef.current = 0;
    }
    const pending = outputTotal - writtenTotalRef.current;
    if (pending <= 0) return;
    // `pending > output.length` khi bộ đệm đã cắt mất chunk cũ — ghi những gì
    // còn giữ được, thà thiếu vài dòng cũ còn hơn đứng im.
    for (const chunk of output.slice(Math.max(0, output.length - pending))) {
      terminal.write(chunk);
    }
    writtenTotalRef.current = outputTotal;
    // `sessionId` không được dùng trong thân effect, nó ở đây làm cớ chạy lại:
    // vài chunk đầu có thể về trước khi terminal kịp tồn tại, và nếu chỉ nghe
    // `output` thì đám đó nằm chờ tới chunk kế tiếp mới được ghi. Effect này
    // khai báo sau effect gắn/tháo nên lúc nó chạy, terminal đã fit đúng cỡ.
  }, [output, outputTotal, sessionId]);

  const active = phase === "starting" || phase === "running";
  const title = active
    ? "Claude /init-kit đang chạy"
    : phase === "finished" && !stopped
      ? "Claude /init-kit đã kết thúc"
      : "Claude /init-kit đã dừng";

  return (
    // Phiên init-kit đang chạy thì không có đường đóng nào ngoài "Dừng
    // init-kit": Esc, click ra ngoài và nút X đều bị chặn. Bỏ dở giữa chừng để
    // lại một project init nửa vời mà màn hình duy nhất nhìn thấy tiến trình
    // lại đã biến mất, nên rời đi phải là một quyết định có chủ đích.
    // `completeInitKit` đóng dialog bằng cách set state thẳng nên không đi qua
    // `onOpenChange`, không bị chốt này chặn.
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!next && active) return;
        onOpenChange(next);
      }}
    >
      <DialogContent
        className="flex h-[88vh] max-w-5xl flex-col overflow-hidden sm:max-w-5xl"
        showCloseButton={!active}
        // Mặc định Radix focus phần tử tabbable đầu tiên khi mount — ở đây là
        // nút đóng, và nó chạy đua với `terminal.focus()` bên dưới. Chặn lại
        // để terminal chắc chắn giữ focus: mở lại dialog là gõ được ngay,
        // không phải bấm vào terminal trước.
        onOpenAutoFocus={(event) => event.preventDefault()}
        onEscapeKeyDown={(event) => {
          if (active) event.preventDefault();
        }}
        onInteractOutside={(event) => {
          if (active) event.preventDefault();
        }}
      >
        <DialogHeader className="pr-8">
          <DialogTitle className="flex items-center gap-2">
            {active ? <LoaderCircle className="animate-spin" /> : <CheckCircle2 />}
            Khởi tạo project: {projectName}
          </DialogTitle>
          <DialogDescription>
            Claude đang chạy trực tiếp trong app. Trả lời các câu hỏi của init-agent ngay trong terminal.
            {active && " Muốn rời khỏi màn hình này thì bấm Dừng init-kit."}
          </DialogDescription>
        </DialogHeader>

        {errorMessage && (
          <div className="rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {errorMessage}
          </div>
        )}

        {/* Claude báo xong không có nghĩa app coi là xong: `initStatus` phải
            `ready` thì terminal mới tự đóng. Hai tiêu chuẩn đó lệch nhau được
            — hay gặp nhất là bảng Repos còn placeholder vì lúc init `repos/`
            chưa có repo nào. Im lặng ở đây là người dùng ngồi nhìn terminal
            không đóng mà không biết còn thiếu gì. */}
        {active && pendingReasons.length > 0 && (
          <div className="rounded-lg border border-warning/50 bg-warning/10 px-3 py-2 text-sm">
            <p className="font-medium">
              Claude đã chạy xong nhưng app vẫn thấy AGENTS.md còn thiếu — terminal
              sẽ tự đóng khi những mục này được điền:
            </p>
            <ul className="mt-1 list-inside list-disc text-xs">
              {pendingReasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
            <p className="mt-1 text-xs text-muted-foreground">
              Có thể trả lời tiếp trong terminal để Claude sửa AGENTS.md, hoặc bấm
              Dừng init-kit rồi xử lý sau.
            </p>
          </div>
        )}

        <div className="min-h-0 flex-1">
          <TerminalFrame title={`${projectName} — ${title}`} className="h-full">
            <div ref={terminalSlotRef} className="h-full min-h-0 w-full p-2" />
          </TerminalFrame>
        </div>

        <DialogFooter className="shrink-0">
          {active ? (
            <Button type="button" variant="destructive" onClick={onStop}>
              <CircleStop />
              Dừng init-kit
            </Button>
          ) : (
            <>
              <Button type="button" variant="outline" onClick={onRetry}>
                <RotateCcw />
                Chạy lại init-kit
              </Button>
              <Button type="button" onClick={() => onOpenChange(false)}>
                Đóng
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
