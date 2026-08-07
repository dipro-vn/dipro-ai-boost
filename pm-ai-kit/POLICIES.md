# PM AI Kit — Policies

## Nguyên tắc cốt lõi

| Policy | Nội dung |
|---|---|
| **Không đoán mò** | Khi thiếu thông tin → hỏi user, không tự bịa |
| **Stateless** | Mỗi session độc lập — đọc context từ file, không nhớ session trước |
| **Bảo mật** | Không in API key ra màn hình. Không commit local.json |

## AI không được phép

- ❌ Tự `git commit` / `git push` khi không được yêu cầu
- ❌ Hard-code secret / API key / token trong code
- ❌ In API key hoặc nội dung local.json ra màn hình (chỉ hiển thị `***`)
- ❌ Commit `local.json`, `data/*.json` chứa dữ liệu thật lên git

## File cấm đọc / expose

- `local.json` — chứa API key dạng plaintext
- `.env*`
- Bất kỳ file chứa credentials

## Khi thiếu thông tin → BẮT BUỘC hỏi

Không bao giờ tự giả định. Thà hỏi 1 câu thừa còn hơn làm sai.
