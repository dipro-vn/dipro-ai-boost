#!/usr/bin/env node
// Kiểm report_html.mjs trên một báo cáo mẫu: bảng, danh sách, ảnh diff kèm ảnh design và ảnh web, ảnh nhỏ được phóng to,
// chữ lấy từ web/design không thành mã chạy được, và chế độ --inline nhúng ảnh vào file.
// Dùng: node tests/report_html_test.mjs
import fs from 'fs';
import os from 'os';
import path from 'path';
import assert from 'assert';
import { spawnSync } from 'child_process';
import { fileURLToPath } from 'url';
import { PNG } from 'pngjs';

const U = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'report-html-'));
const png = (rel, w, h) => {
  fs.mkdirSync(path.dirname(path.join(dir, rel)), { recursive: true });
  fs.writeFileSync(path.join(dir, rel), PNG.sync.write(new PNG({ width: w, height: h })));
};
png('uicompare/v1/figma-img/1-2.png', 20, 20);
png('uicompare/v1/pixel-1440/act-img/1-2.png', 20, 20);
png('uicompare/v1/pixel-1440/diff/1-2.png', 20, 20);
png('uicompare/v1/dom-1440.png', 400, 300);

fs.writeFileSync(path.join(dir, 'm-uicompare-v1.md'), `# UI Compare: m — v1

| Mục | Nội dung |
|---|---|
| URL | https://example.com/x |

## 4. Có nhưng sai

### SA-01: Nút thiếu viền <script>alert(1)</script>
- **Design:** viền 1px
  nối dòng
- **Ảnh:** \`uicompare/v1/pixel-1440/diff/1-2.png\`
- Link xấu: [bấm](javascript:alert(1)) và ảnh không có: \`uicompare/v1/pixel-1440/diff/9-9.png\`

Toàn trang: \`uicompare/v1/dom-1440.png\`

| Mã | Ảnh |
|---|---|
| SA-09 | ![](uicompare/v1/pixel-1440/diff/1-2.png) |
`);

const run = (...extra) => {
  const r = spawnSync('node', [path.join(U, 'report_html.mjs'), '--md', path.join(dir, 'm-uicompare-v1.md'), ...extra], { encoding: 'utf8' });
  assert.strictEqual(r.status, 0, r.stderr);
  return fs.readFileSync(path.join(dir, 'm-uicompare-v1.html'), 'utf8');
};

const html = run();
assert.ok(html.includes('<table>') && html.includes('<th>Mục</th>'), 'bảng');
assert.ok(html.includes('<h3 id="SA-01">'), 'tiêu đề mục có id để dẫn link');
assert.ok(!html.includes('![]('), 'cú pháp ảnh markdown phải thành ảnh, không in nguyên chữ');
assert.ok(/<b>Design:<\/b> viền 1px\s+nối dòng/.test(html), 'dòng nối của một mục danh sách');
for (const [src, cap] of [['figma-img/1-2.png', 'Design'], ['act-img/1-2.png', 'Web thật'], ['diff/1-2.png', 'Web, khung đỏ = chỗ khác design']]) {
  assert.ok(html.includes(`src="uicompare/v1/${src.startsWith('figma') ? '' : 'pixel-1440/'}${src}"`), 'ảnh ' + src);
  assert.ok(html.includes(cap + ' (phóng to ×6)'), 'ảnh 20px được phóng to: ' + cap);
}
assert.ok(html.includes('src="uicompare/v1/dom-1440.png"') && !html.includes('dom-1440.png (phóng'), 'ảnh lớn giữ nguyên cỡ');
assert.ok(!html.includes('9-9.png"'), 'ảnh không tồn tại thì không chèn thẻ img');
assert.ok(!html.includes('<script>') && html.includes('&lt;script&gt;'), 'chữ trong báo cáo không thành mã chạy được');
assert.ok(!/href="javascript:/i.test(html), 'không tạo link javascript:');
assert.ok(html.includes('<a href="https://example.com/x"'), 'URL thường thành link');

const inlined = run('--inline');
assert.ok(inlined.includes('src="data:image/png;base64,') && !inlined.includes('src="uicompare/'), '--inline nhúng ảnh');

fs.rmSync(dir, { recursive: true });
console.log('report_html: ALL OK');
