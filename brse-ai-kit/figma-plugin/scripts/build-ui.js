#!/usr/bin/env node
/**
 * Inline ExcelJS browser bundle into ui.html.
 * Figma plugin UI often fails to load external <script src> — inline is reliable.
 */
const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..");
const uiPath = path.join(root, "src", "ui.html");
const excelSrc = path.join(root, "node_modules", "exceljs", "dist", "exceljs.bare.min.js");
const vendorDest = path.join(root, "src", "vendor", "exceljs.bare.min.js");

const BEGIN = "<!-- __EXCELJS_INLINE_BEGIN__ -->";
const END = "<!-- __EXCELJS_INLINE_END__ -->";

if (!fs.existsSync(excelSrc)) {
  console.error("Missing exceljs. Run: npm install");
  process.exit(1);
}

fs.mkdirSync(path.dirname(vendorDest), { recursive: true });
fs.copyFileSync(excelSrc, vendorDest);

const excelJs = fs.readFileSync(excelSrc, "utf8").replace(/\n?\/\/# sourceMappingURL=.*$/gm, "");
let html = fs.readFileSync(uiPath, "utf8");

// Strip any previous inline/external ExcelJS block
const bridgeIdx = html.indexOf("var ROUTER_BRIDGE_URL");
if (bridgeIdx < 0) {
  console.error("Could not find ROUTER_BRIDGE_URL anchor in ui.html");
  process.exit(1);
}

const iframeEnd = html.lastIndexOf("</iframe>", bridgeIdx);
const headPart = html.slice(0, iframeEnd + "</iframe>".length);
const tailPart = html.slice(bridgeIdx);

// Remove leading <script> if tail was wrapped, and strip ALL trailing closing
// tags (</script>/</body>/</html>) so repeated builds stay idempotent.
const cleanTail = tailPart
  .replace(/^[\s\n]*<script>[\s\n]*/, "")
  .replace(/(?:\s*<\/(?:script|body|html)>\s*)+$/i, "");
const inlineBlock =
  "\n\n" + BEGIN + "\n<script>\n" + excelJs + "\n</script>\n" + END + "\n<script>\n" + cleanTail;

const rebuilt = headPart + inlineBlock + "\n</script>\n</body>\n</html>\n";
fs.writeFileSync(uiPath, rebuilt);
console.log("Inlined exceljs.bare.min.js into src/ui.html (" + Math.round(rebuilt.length / 1024) + " KB)");
