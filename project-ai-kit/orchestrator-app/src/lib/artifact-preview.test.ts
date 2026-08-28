import { describe, expect, it } from "vitest";
import { isPreviewableArtifact } from "@/lib/artifact-preview";

describe("isPreviewableArtifact", () => {
  it("allows the docs every slot produces", () => {
    expect(isPreviewableArtifact("/docs/features/login/SPEC.md")).toBe(true);
    expect(isPreviewableArtifact("/docs/features/login/design-analysis.md")).toBe(true);
    expect(isPreviewableArtifact("/x/runs/r1/qa-report.md")).toBe(true);
  });

  it("allows exported SVG icons — they are text", () => {
    expect(isPreviewableArtifact("/f/design-resources/icon-home.svg")).toBe(true);
  });

  it("rejects exported raster images — read_artifact decodes UTF-8", () => {
    expect(isPreviewableArtifact("/f/design-resources/logo-header.png")).toBe(false);
    expect(isPreviewableArtifact("/f/design-resources/banner.JPG")).toBe(false);
    expect(isPreviewableArtifact("/f/design-resources/shot.webp")).toBe(false);
  });

  it("treats an extensionless path as text", () => {
    expect(isPreviewableArtifact("/f/NOTES")).toBe(true);
  });

  it("does not read an extension out of a dotfile or a directory name", () => {
    expect(isPreviewableArtifact("/f/.gitignore")).toBe(true);
    expect(isPreviewableArtifact("/some.dir/README")).toBe(true);
  });
});
