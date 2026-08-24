import { describe, expect, it } from "vitest";
import { splitMarkdownBlocks } from "@/lib/markdown-blocks";

describe("splitMarkdownBlocks", () => {
  it("splits paragraphs separated by a blank line", () => {
    const blocks = splitMarkdownBlocks("# Title\n\nFirst paragraph.\n\nSecond paragraph.");
    expect(blocks).toEqual(["# Title", "First paragraph.", "Second paragraph."]);
  });

  it("collapses multiple consecutive blank lines into one boundary", () => {
    const blocks = splitMarkdownBlocks("A\n\n\n\nB");
    expect(blocks).toEqual(["A", "B"]);
  });

  it("does NOT split on a blank line inside a fenced code block", () => {
    const content = [
      "Before.",
      "",
      "```mermaid",
      "flowchart TD",
      "",
      "  A --> B",
      "```",
      "",
      "After.",
    ].join("\n");

    const blocks = splitMarkdownBlocks(content);
    expect(blocks).toEqual([
      "Before.",
      "```mermaid\nflowchart TD\n\n  A --> B\n```",
      "After.",
    ]);
  });

  it("handles an unclosed fence without throwing (treats rest as one block)", () => {
    const content = "Before.\n\n```mermaid\nflowchart TD\n\n  A --> B";
    const blocks = splitMarkdownBlocks(content);
    expect(blocks).toEqual(["Before.", "```mermaid\nflowchart TD\n\n  A --> B"]);
  });

  it("returns an empty array for empty content", () => {
    expect(splitMarkdownBlocks("")).toEqual([]);
  });

  it("returns a single block for content with no blank lines", () => {
    expect(splitMarkdownBlocks("line one\nline two")).toEqual([
      "line one\nline two",
    ]);
  });
});
