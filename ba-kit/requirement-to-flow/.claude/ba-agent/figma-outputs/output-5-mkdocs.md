# Ba Agent — Output 5: MkDocs Site

## Output 5 — MkDocs Site (SPEC published trên browser)

> Publish toàn bộ docs (SPEC + tất cả features) qua MkDocs Material để stakeholder đọc trên browser với nav, search, table of contents.
> Chạy song song trên `http://127.0.0.1:8000`.

**Kiểm tra prerequisites (1 lần đầu tiên):**

```bash
# Check mkdocs đã install chưa
which mkdocs
# Nếu chưa:
pip install mkdocs mkdocs-material mkdocs-awesome-pages-plugin
```

**Setup `mkdocs.yml` (chỉ tạo 1 lần cho project):**

Copy template từ `.claude/templates/mkdocs.yml` đến root dự án (cùng cấp `<DOCS_ROOT>`):

```bash
# Tìm parent folder của <DOCS_ROOT>
cp .claude/templates/mkdocs.yml <PROJECT_ROOT>/mkdocs.yml
# Thay <TEN_DU_AN> trong file bằng tên thật của dự án
```

**Kiểm tra `mkdocs.yml` đã có chưa** — nếu có rồi thì skip bước setup.

**Chạy dev server (mỗi lần cần preview):**

```bash
cd <PROJECT_ROOT>   # nơi có mkdocs.yml
mkdocs serve
# → http://127.0.0.1:8000
```

MkDocs sẽ tự pick up SPEC.md mới ngay khi BA save file — không cần restart server.

**Nav tự động:**
- `mkdocs-awesome-pages-plugin` scan `docs/features/<feature>/` → tự sinh nav
- Muốn đặt tên riêng cho folder: tạo `.pages` file trong folder đó
- BA không cần sửa `nav:` thủ công

**Output BA cần thông báo user:**

```
✅ MkDocs đang chạy: http://127.0.0.1:8000
   Nav → Features → <tên feature> → SPEC
   (Ctrl+C ở terminal để dừng)
```
