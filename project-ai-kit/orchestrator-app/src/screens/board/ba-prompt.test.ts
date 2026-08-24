import { describe, expect, it } from "vitest";
import { buildBaPrompt } from "@/screens/board/BaStepPanel";

const COPIED = "/agents/.orchestrator/inputs/20260818T032139674Z-user-signup";

describe("buildBaPrompt", () => {
  /** The regression this exists for: with only the folder path, the agent
   * read the directory (EISDIR) and then guessed file names that did not
   * exist, burning a full run before giving up. */
  it("names every copied file as an absolute path", () => {
    const prompt = buildBaPrompt(
      COPIED,
      ["01-yeu-cau.md", "mo-ta-man-hinh/man-dang-ky.md"],
      "",
    );

    expect(prompt).toContain(`${COPIED}/01-yeu-cau.md`);
    expect(prompt).toContain(`${COPIED}/mo-ta-man-hinh/man-dang-ky.md`);
    expect(prompt).toContain("Read");
  });

  it("says so explicitly when nothing readable was copied", () => {
    const prompt = buildBaPrompt(COPIED, [], "");
    expect(prompt).toContain("không có file nào đọc được");
  });

  it("appends the user's extra context only when provided", () => {
    expect(buildBaPrompt(COPIED, ["a.md"], "  ")).not.toContain("Bối cảnh thêm");
    expect(buildBaPrompt(COPIED, ["a.md"], "ưu tiên mobile")).toContain(
      "Bối cảnh thêm từ người dùng:\nưu tiên mobile",
    );
  });
});
