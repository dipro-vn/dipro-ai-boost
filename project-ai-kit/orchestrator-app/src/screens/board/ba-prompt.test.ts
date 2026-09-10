import { describe, expect, it } from "vitest";
import {
  buildBaPrompt,
  isFigmaDesignPageUrl,
  TARGET_PLATFORMS,
} from "@/screens/board/BaStepPanel";

const COPIED = "/agents/.ai-boost/inputs/20260818T032139674Z-user-signup";
const FIGMA = "https://www.figma.com/design/abc123/Kit?node-id=12-34";

function prompt(
  files: string[] = ["a.md"],
  context = "",
  figmaUrl = FIGMA,
  platform = "Mobile app",
) {
  return buildBaPrompt(COPIED, files, context, figmaUrl, platform);
}

describe("buildBaPrompt", () => {
  /** The regression this exists for: with only the folder path, the agent
   * read the directory (EISDIR) and then guessed file names that did not
   * exist, burning a full run before giving up. */
  it("names every copied file as an absolute path", () => {
    const result = prompt(["01-yeu-cau.md", "mo-ta-man-hinh/man-dang-ky.md"]);

    expect(result).toContain(`${COPIED}/01-yeu-cau.md`);
    expect(result).toContain(`${COPIED}/mo-ta-man-hinh/man-dang-ky.md`);
    expect(result).toContain("Read");
  });

  it("says so explicitly when nothing readable was copied", () => {
    expect(prompt([])).toContain("không có file nào đọc được");
  });

  it("appends the user's extra context only when provided", () => {
    expect(prompt(["a.md"], "  ")).not.toContain("Bối cảnh thêm");
    expect(prompt(["a.md"], "ưu tiên mobile")).toContain(
      "Bối cảnh thêm từ người dùng:\nưu tiên mobile",
    );
  });

  /** Bước 2b câu 0.5 is a mandatory question and an orchestrated run has
   * nobody to answer it — the URL the user typed has to arrive with the
   * prompt or Outputs 1-3 never get drawn. */
  it("carries the Figma URL and forbids the agent picking another file", () => {
    const result = prompt();
    expect(result).toContain(FIGMA);
    expect(result).toContain("KHÔNG hỏi lại");
    expect(result).toContain("KHÔNG tự tạo page mới");
  });

  /** The panel no longer lets a run start without a URL (`canSubmit`), and
   * the Rust gate blocks a BA spawn without a write-capable Figma MCP. This
   * branch survives as defence for the paths that bypass the panel — a Retry
   * replaying an older stored prompt, and `bmad-plan-phase.js`. */
  it("tells the agent to skip Outputs 1-3 and carry on when no URL was given", () => {
    const result = prompt(["a.md"], "", "");
    expect(result).toContain("BỎ QUA Output 1-3");
    expect(result).toContain("❌ Skipped");
    expect(result).toContain("vẫn làm Output 0/4/5");
  });

  /** The viewport rides along so the agent never has to look the mapping
   * up — "không tự suy diễn", made literal. */
  it("injects the platform together with its pinned viewport", () => {
    expect(prompt()).toContain("Mobile app — viewport 375×812");
    expect(prompt(["a.md"], "", FIGMA, "Website")).toContain("Website — viewport 1440×1024");
  });

  it("pins the same 4 viewports ba-agent.md calls CHUẨN CỨNG", () => {
    expect(TARGET_PLATFORMS.map((p) => `${p.value} ${p.viewport}`)).toEqual([
      "Mobile app 375×812",
      "Web app 375×812",
      "Website 1440×1024",
      "iPad/Tablet 1024×768",
    ]);
  });
});

describe("buildBaPrompt without a requirements folder", () => {
  function noFolder(context: string) {
    return buildBaPrompt(null, [], context, FIGMA, "Mobile app");
  }

  /** Told to "analyse the copied input" with no folder, the agent goes
   * hunting for files that do not exist instead of reading the text it was
   * handed. */
  it("says outright that there are no files to read", () => {
    const result = noFolder("Admin cần export danh sách user ra CSV");
    expect(result).toContain("KHÔNG cung cấp folder tài liệu");
    expect(result).toContain("đừng đi tìm");
    expect(result).not.toContain("đã được copy sẵn");
  });

  /** Same text, different role — as the only input it is the requirement,
   * and labelling it "bối cảnh thêm" reads as an aside. */
  it("promotes the context box from an aside to the requirement", () => {
    const result = noFolder("Admin cần export danh sách user ra CSV");
    expect(result).toContain("Mô tả yêu cầu từ người dùng:\nAdmin cần export danh sách user ra CSV");
    expect(result).not.toContain("Bối cảnh thêm từ người dùng");
  });

  it("still carries the Figma URL and the platform", () => {
    const result = noFolder("bất kỳ");
    expect(result).toContain(FIGMA);
    expect(result).toContain("Mobile app — viewport 375×812");
  });

  /** With a folder the box goes back to being supplementary. */
  it("keeps the aside wording when a folder was given", () => {
    const result = buildBaPrompt(COPIED, ["a.md"], "ưu tiên mobile", FIGMA, "Mobile app");
    expect(result).toContain("Bối cảnh thêm từ người dùng");
    expect(result).not.toContain("Mô tả yêu cầu từ người dùng");
  });
});

describe("isFigmaDesignPageUrl", () => {
  it("accepts a Figma Design URL", () => {
    expect(isFigmaDesignPageUrl(FIGMA)).toBe(true);
    expect(isFigmaDesignPageUrl(`  ${FIGMA}  `)).toBe(true);
    expect(isFigmaDesignPageUrl("https://figma.com/design/abc/Kit")).toBe(true);
  });

  /** FigJam has no real viewport, so Output 3's mockups cannot be drawn to
   * the sizes the kit pins; `/file/` is the legacy shape. */
  it("rejects FigJam, legacy URLs, other hosts and junk", () => {
    expect(isFigmaDesignPageUrl("https://www.figma.com/board/abc/Kit")).toBe(false);
    expect(isFigmaDesignPageUrl("https://www.figma.com/file/abc/Kit")).toBe(false);
    expect(isFigmaDesignPageUrl("https://notfigma.com/design/abc")).toBe(false);
    expect(isFigmaDesignPageUrl("https://evil-figma.com.attacker.net/design/abc")).toBe(false);
    expect(isFigmaDesignPageUrl("not a url")).toBe(false);
    expect(isFigmaDesignPageUrl("")).toBe(false);
  });
});
