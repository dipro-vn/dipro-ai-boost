import { describe, expect, it } from "vitest";
import { isMissingPathError } from "@/screens/board/agent-run-shared";

describe("isMissingPathError", () => {
  /** Both strings observed verbatim in the first real `user-signup` run,
   * where they made a successful run look broken. */
  it("recognises the probes an agent makes for optional files", () => {
    expect(
      isMissingPathError(
        "File does not exist. Note: your current working directory is /x/y/user-signup.",
      ),
    ).toBe(true);
    expect(
      isMissingPathError("EISDIR: illegal operation on a directory, read '/x/inputs/2026-user'"),
    ).toBe(true);
    expect(isMissingPathError("no such file or directory")).toBe(true);
  });

  /** Real failures must stay red. */
  it("does not swallow genuine errors", () => {
    expect(isMissingPathError("Permission denied")).toBe(false);
    expect(isMissingPathError("API error: rate limit exceeded")).toBe(false);
    expect(isMissingPathError("Tool execution failed")).toBe(false);
  });
});
