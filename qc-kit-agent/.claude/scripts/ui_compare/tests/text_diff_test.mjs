// Dùng: node tests/text_diff_test.mjs
import assert from 'assert';
import { textDiff } from '../text_diff.mjs';
const F = [
  { id: 'bar', type: 'frame', parent: 'root' }, { id: 't0', type: 'text', parent: 'bar', text: '9:41' },
  { id: 't1', type: 'text', parent: 'root', text: 'アカウントに\nログイン' }, { id: 't2', type: 'text', parent: 'root', text: 'パスワード' },
  { id: 't3', type: 'text', parent: 'root', text: '新規登録' },
];
const D = [{ i: 1, tag: 'h1', text: 'アカウントに ログイン' }, { i: 2, tag: 'label', text: 'パスワード 必須' }, { i: 3, tag: 'a', text: 'ヘルプ' }, { i: 4, tag: 'div', text: '' }];
const r = textDiff(F, D, ['bar']);
assert.deepStrictEqual(r.missingOnWeb.map(x => x.text), ['新規登録'], 'xuống dòng/khoảng trắng khác nhau vẫn khớp; chữ trong thanh trạng thái bị loại');
assert.deepStrictEqual(r.extraOnWeb.map(x => x.text), ['パスワード 必須', 'ヘルプ']);
console.log('text_diff: ALL OK');
