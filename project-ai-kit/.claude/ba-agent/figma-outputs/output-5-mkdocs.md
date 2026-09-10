# Ba Agent — Output 5: MkDocs Site

## Output 5 — MkDocs Site (SPEC published trên browser)

> Publish toàn bộ docs (SPEC + tất cả features) qua MkDocs Material để stakeholder đọc trên browser với nav, search, table of contents.
> Chạy song song trên `http://127.0.0.1:8000`.

**Kiểm tra prerequisites — dò HAI bước, đừng kết luận sau bước 1:**

```bash
command -v mkdocs            # bước 1: binary trên PATH?
python3 -m mkdocs --version  # bước 2: chỉ chạy khi bước 1 trượt
```

`pip install --user` đặt binary vào thư mục kiểu `~/Library/Python/3.x/bin`, mà thư mục đó **thường không có trong `PATH`**. Nên **bước 1 trượt KHÔNG có nghĩa là chưa cài** — rất hay là đã cài rồi và chỉ gọi sai đường. Bước nào chạy được thì dùng đúng dạng đó cho mọi lệnh mkdocs về sau.

**Chỉ khi CẢ HAI bước đều trượt** mới là chưa cài thật. Khi đó: in lệnh dưới đây cho **user tự chạy** — BA **KHÔNG tự cài** (đụng môi trường Python của người ta):

```bash
python3 -m pip install --user -r .claude/templates/mkdocs-requirements.txt
```

Nói luôn với user rằng sau khi cài, gọi `python3 -m mkdocs` là chắc chắn nhất — khỏi phải sửa `PATH`.

**Setup `mkdocs.yml` (chỉ tạo 1 lần cho project):**

Copy template từ `.claude/templates/mkdocs.yml` đến root dự án (cùng cấp `<DOCS_ROOT>`):

```bash
# Tìm parent folder của <DOCS_ROOT>
cp .claude/templates/mkdocs.yml <PROJECT_ROOT>/mkdocs.yml
# Trang chủ của site — thiếu file này thì nav mở ra không có gì
mkdir -p <PROJECT_ROOT>/docs
cp .claude/templates/docs-index.md <PROJECT_ROOT>/docs/index.md
# Thay <TEN_DU_AN> trong CẢ HAI file bằng tên thật của dự án
```

**Kiểm tra `mkdocs.yml` đã có chưa** — nếu có rồi thì skip bước setup.

**Build (BẮT BUỘC khi chạy qua Dipro AI Boost):**

```bash
cd <PROJECT_ROOT>              # nơi có mkdocs.yml
mkdocs build --clean           # nếu bước 1 chạy được
python3 -m mkdocs build --clean  # nếu chỉ bước 2 chạy được
```

`mkdocs build` chạy xong rồi thoát — đó là lệnh dùng trong run do app điều phối. **TUYỆT ĐỐI không chạy `mkdocs serve` trong run điều phối**: nó là server không bao giờ exit, app sẽ đợi tới hết timeout rồi kết luận run bị treo.

**Chạy dev server (chỉ khi user tự chạy tay trong terminal của họ):**

```bash
cd <PROJECT_ROOT>          # nơi có mkdocs.yml
python3 -m mkdocs serve    # dạng chắc chắn nhất, không phụ thuộc PATH
# → http://127.0.0.1:8000
```

MkDocs sẽ tự pick up SPEC.md mới ngay khi BA save file — không cần restart server.

**Nav tự động:**
- `mkdocs-awesome-pages-plugin` scan `docs/features/<feature>/` → tự sinh nav
- Muốn đặt tên riêng cho folder: tạo `.pages` file trong folder đó
- BA không cần sửa `nav:` thủ công

**Output BA cần thông báo user** — BA chỉ `build`, không `serve`, nên đừng nói site "đang chạy":

```
✅ MkDocs site đã build xong: <PROJECT_ROOT>/site/
   Xem trên browser: cd <PROJECT_ROOT> && python3 -m mkdocs serve
   → http://127.0.0.1:8000 — Nav → Features → <tên feature> → SPEC
```
