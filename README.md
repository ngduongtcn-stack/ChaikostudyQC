# QC検定れんしゅう帳 — Web học QC検定 4級・3級

Trang web tĩnh, miễn phí hosting, không cần đăng ký tài khoản. Người học có thể:

- Luyện theo từng phân野 (mỗi câu có đáp án + giải thích ngay)
- Thi thử mini (tối đa 20 câu ngẫu nhiên, chấm điểm cuối bài, có thời gian làm)
- Ôn lại câu sai (tự động gom các câu làm sai gần nhất)
- Gửi góp ý cho từng câu (qua Google Form)
- Mỗi phân野 có một trang HTML liệt kê câu hỏi + giải thích → Google đọc được (SEO)

Tiến độ học lưu trong trình duyệt của người học (localStorage), không gửi đi đâu.

## Cấu trúc thư mục

```
qc-site/
├── site.json                 ← tên site, URL, link Google Form
├── build.py                  ← chạy để tạo thư mục dist/
├── src/
│   ├── data/questions.json   ← NGÂN HÀNG CÂU HỎI (sửa ở đây)
│   └── assets/style.css, app.js
└── dist/                     ← kết quả build, đây là thứ đưa lên mạng
```

## Thêm / sửa câu hỏi

Mở `src/data/questions.json`, thêm một khối như sau vào `"questions"`:

```json
{
  "id": "4-023", "level": 4, "topic": "kensa", "status": "draft",
  "question": "Câu hỏi…",
  "choices": ["Lựa chọn ア", "Lựa chọn イ", "Lựa chọn ウ", "Lựa chọn エ"],
  "answer": 0,
  "explanation": "解説（tiếng Nhật）…",
  "explanation_vi": "Giải thích bằng tiếng Việt…"
}
```

- `explanation_vi` (không bắt buộc): giải thích tiếng Việt. Câu nào có trường này thì dưới phần giải thích tiếng Nhật sẽ hiện nút「Xem giải thích bằng tiếng Việt」. Người đọc bật một lần thì web nhớ và tự hiện cho các câu sau. Nên giữ thuật ngữ tiếng Nhật kèm nghĩa, ví dụ 管理限界線 (đường giới hạn kiểm soát).

- `answer`: vị trí đáp án đúng, **đếm từ 0** (0 = ア, 1 = イ, 2 = ウ, 3 = エ). Trên web thứ tự lựa chọn sẽ được xáo trộn.
- `topic`: phải là một `id` trong danh sách phân野 của cấp đó (ở phần `"levels"` đầu file).
- `status`: `"draft"` = chưa kiểm tra, đổi thành `"ok"` sau khi anh/chị đã tự kiểm tra nội dung.
- Không chép nguyên văn từ sách hay đề thi cũ (bản quyền). Tự viết lại câu hỏi và giải thích.

Sau đó chạy:

```bash
python3 build.py          # tạo lại dist/
python3 build.py --check  # chỉ kiểm tra lỗi trong questions.json
```

Script sẽ báo lỗi nếu trùng ID, sai `answer`, sai `topic`…

> Hiện có 46 câu (4級 22, 3級 24), tất cả đang là `draft`. Hãy kiểm tra từng câu trước khi công khai.

## Web được đăng tự động (GitHub Pages + GitHub Actions)

Địa chỉ web: **https://ngduongtcn-stack.github.io/ChaikostudyQC/**

Repository này chứa mã nguồn. Mỗi khi có thay đổi trên nhánh `main`, GitHub tự chạy `build.py` và đăng web mới (file `.github/workflows/pages.yml`). Không cần cài Python, không cần upload thư mục `dist/`.

**Cài đặt một lần:** Settings → Pages → Build and deployment → Source: **GitHub Actions**.

**Thêm/sửa câu hỏi ngay trên trình duyệt (kể cả điện thoại):**
1. Mở `src/data/questions.json` trên GitHub → bấm biểu tượng bút chì (Edit).
2. Sửa nội dung → **Commit changes**.
3. Vào tab **Actions** xem tiến trình. Dấu ✓ xanh = web đã cập nhật (khoảng 1–2 phút). Dấu ✗ đỏ = file có lỗi (sai dấu phẩy, sai `answer`…), bấm vào để xem thông báo lỗi; web cũ vẫn giữ nguyên.

## Để Google tìm thấy

1. Vào **Google Search Console** → thêm trang (URL prefix) → xác minh.
2. Gửi sitemap: `https://<tên-github>.github.io/qc-renshu/sitemap.xml`.
3. Mỗi phân野 có trang riêng (vd. `4kyu/kensa.html`) với tiêu đề kiểu「QC検定4級「検査」練習問題」. Càng nhiều câu hỏi chất lượng, càng dễ lên kết quả tìm kiếm.
4. Liên kết qua lại giữa blog WordPress và web này (mỗi bài blog dẫn link sang phân野 tương ứng).

## Bật chức năng góp ý (Google Form)

1. Tạo Google Form với 2 câu: 「問題ID」 (trả lời ngắn) và 「ご意見」 (đoạn văn).
2. Bấm ⋮ → **Get pre-filled link** (事前入力したURLを取得), điền `TEST` vào ô 問題ID → **Get link** → copy.
3. Link sẽ có dạng `https://docs.google.com/forms/d/e/XXXX/viewform?usp=pp_url&entry.123456=TEST`. Đổi `TEST` thành `{id}`.
4. Dán vào `feedback_form_url` trong `site.json`, chạy lại `build.py`.

Từ đó dưới mỗi câu sẽ có link「この問題について意見を送る」, mở form với ID câu hỏi đã điền sẵn. Câu trả lời xem trong tab "Responses" của form (có thể nối với Google Sheets).

## Về kiếm tiền sau này

- Trang đã có sẵn trang 運営方針・プライバシー (cần cho Google AdSense). Khi có lượng truy cập ổn định, có thể đăng ký AdSense và cập nhật phần プライバシー cho đúng (quảng cáo dùng cookie).
- Hướng khác: bán bộ đề PDF / bài trả phí trên note.com hoặc BOOTH, dẫn link từ web.
