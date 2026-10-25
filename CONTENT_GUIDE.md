# Quy trình thêm câu hỏi định kỳ (Chủ nhật & thứ Tư)

Tài liệu này là quy trình chuẩn cho mỗi lần chạy tự động. Lần chạy nào cũng làm đúng các bước dưới đây, theo thứ tự.

Mục tiêu: 4級 500 câu, 3級 1.000 câu, rồi đề thi thử (4級 10 đề, 3級 20 đề, mỗi đề 50 câu, mở dần tự động).

Phân野 được chia theo 分野 như đề thi thật (trường `domain` của từng topic trong `questions.json`):
- 4級: 実践分野, 手法分野, 企業活動の基本 (đỗ khi tổng ≥ 70%).
- 3級: 手法分野 và 実践分野, mỗi phần 50% số câu của đề thi thử (đỗ khi tổng ≥ 70% **và** mỗi phần ≥ 50%). `make_exams.py` chỉ tạo đề 3級 khi mỗi phần có đủ 25 câu chưa dùng, nên phần nào thiếu thì `plan.py` sẽ tự ưu tiên phần đó. Đây là việc làm thêm bằng dung lượng dư: **ưu tiên chất lượng hơn số lượng**. Thiếu câu hay còn hơn câu trùng hoặc sai.

## Cấu hình: `content-plan.json`

- `paused`: `true` → lần chạy chỉ báo cáo, không soạn câu mới.
- `per_run.sun` / `per_run.wed`: số câu soạn cho lần Chủ nhật / thứ Tư. Chủ repo có thể sửa số `wed` trong ngày thứ Tư (sau khi xem dung lượng còn lại), trước giờ chạy buổi tối.
- `topic_targets`: số câu mục tiêu theo từng phân野.
- `exhausted`: phân野 đã hết nội dung mới (soạn tiếp chỉ ra câu trùng) → bỏ qua.
- `exam`: cỡ đề thi thử, số đề tối đa, mốc đạt.

## Các bước

Làm việc ở thư mục gốc của repo. File tạm để ở thư mục scratchpad/tmp, **không commit**.

### 1. Lập kế hoạch
```bash
python3 tools/plan.py --day sun   # hoặc --day wed
```
Nếu kết quả là "paused" hoặc "Đã đạt mục tiêu" → bỏ qua bước 2–5, chỉ làm bước 6–8.

### 2. Đọc tài liệu trước khi soạn
- `src/data/theory.json`: phần lý thuyết của các phân野 được phân công.
- Toàn bộ câu hỏi hiện có của các phân野 đó trong `src/data/questions.json`, để **không soạn lại ý đã có** (cùng khái niệm, cùng cách hỏi, chỉ đổi chữ cũng tính là trùng).

### 3. Soạn câu hỏi ứng viên
Trước tiên xem `src/data/reserve.json` (kho dự trữ): đây là những câu đã qua kiểm tra ở lần trước nhưng chưa dùng, và sẽ được dùng trước. Với mỗi phân野, lấy số câu được phân công trừ đi số câu dự trữ của phân野 đó, rồi soạn khoảng **phần còn lại + 20%** (để bù câu bị loại). Ghi vào `candidates.json` dạng danh sách:

```json
{"id": "c01", "level": 3, "topic": "kanrizu", "question": "…", "choices": ["…","…","…","…"],
 "answer": 1, "explanation": "解説…", "explanation_vi": "Giải thích…"}
```

Quy tắc chất lượng:
- **Tự viết.** Không chép hay diễn đạt sát nghĩa từ sách, đề thi cũ hay trang web khác.
- Tiếng Nhật tự nhiên theo văn phong đề thi QC検定; dùng thuật ngữ hiện hành (ví dụ 日本産業規格, JIS Z 9020-2 cho quy tắc biểu đồ kiểm soát).
- 4 lựa chọn, **chỉ một đáp án đúng rõ ràng**; các phương án sai phải hợp lý (lỗi hay gặp, khái niệm dễ nhầm), không vô lý.
- Đa dạng dạng câu hỏi: định nghĩa, ví dụ áp dụng, tính toán, chọn câu「適切でないもの」, phân biệt hai khái niệm gần nhau, đọc tình huống thực tế ở nhà máy.
- Câu tính toán: **tính lại mọi con số bằng Python**; ưu tiên số đẹp; phương án sai nên là kết quả của lỗi thường gặp (chia n thay vì n−1, một phía/hai phía…).
- `explanation` (tiếng Nhật): 2–4 câu, nói vì sao đúng và vì sao phương án dễ nhầm là sai.
- `explanation_vi`: tiếng Việt tự nhiên; giữ thuật ngữ tiếng Nhật kèm nghĩa trong ngoặc, ví dụ 管理限界線 (đường giới hạn kiểm soát).
- Không dùng thông tin dễ thay đổi theo thời gian (ngày thi, lệ phí, số liệu thống kê mới nhất…).
- 3級 có thể hỏi cả kiến thức 4級, nhưng phải ở mức sâu hơn.
- Phân野 実践 (品質の概念, 管理の方法, 品質保証, 品質経営の要素) cần câu hỏi tình huống thực tế ở nơi làm việc, không chỉ hỏi định nghĩa.

### 4. Kiểm tra độc lập (bắt buộc)
```bash
python3 tools/blind.py candidates.json blind.json
```
Giao `blind.json` cho **một tác tử phụ riêng** (Agent tool, general-purpose). Tác tử này không biết đáp án và không xem `candidates.json`. Yêu cầu nó:
- tự giải từng câu, câu tính toán thì tính bằng Python;
- trả về `checker.json`: `[{"id": "c01", "answer": 1, "confident": true, "note": ""}]`;
- đặt `confident: false` nếu câu mơ hồ, có hơn một đáp án hợp lý, sai kiến thức hoặc tiếng Nhật khó hiểu, và ghi lý do vào `note`.

Sau đó:
```bash
python3 tools/compare.py candidates.json checker.json verified.json
```
Chỉ những câu khớp đáp án **và** `confident: true` mới được giữ. Câu bị loại thì bỏ, không sửa rồi thêm lại trong cùng lần chạy.

### 5. Chống trùng và thêm vào ngân hàng
```bash
python3 tools/add_questions.py verified.json --alloc "$(python3 tools/plan.py --day sun --json)" --reserve src/data/reserve.json
```
(Thay `sun` bằng `wed` ở lần thứ Tư.) Script dùng kho dự trữ trước, giới hạn đúng số câu đã phân công cho từng phân野, loại câu gần giống câu đã có, gán ID mới và đặt `status: "checked"` (đã qua kiểm tra độc lập, chưa qua người duyệt). Câu đạt nhưng dư được cất lại vào kho dự trữ cho lần sau.

Nếu một phân野 có **hơn một nửa** số câu ứng viên bị loại vì trùng, phân野 đó coi như đã hết nội dung mới: thêm nó vào `exhausted` trong `content-plan.json`.

### 6. Đề thi thử
```bash
python3 tools/make_exams.py
```
Tự tạo đề mới khi đủ 50 câu chưa dùng. Đề cũ không bao giờ bị thay đổi.

### 7. Build thử, commit và đẩy lên
```bash
python3 build.py && rm -rf dist
git add -A
git commit -m "Add N questions (4級 a, 3級 b) — YYYY-MM-DD"   # kèm dòng ghi công theo quy định của phiên
git push origin main
```
Chờ GitHub Actions ("Build and deploy site") chạy xong với trạng thái thành công.

### 8. Báo cáo cho chủ repo
Ngắn gọn, bằng tiếng Việt:
- số câu đã thêm (4級 / 3級), số câu bị loại và lý do chính;
- tổng hiện tại so với mục tiêu, số đề thi thử;
- phân野 nào mới được đánh dấu hết nội dung;
- 3 câu ngẫu nhiên vừa thêm (ID + câu hỏi), để chủ repo kiểm tra ngẫu nhiên.

## Trạng thái câu hỏi
- `draft`: Claude soạn, chưa qua kiểm tra độc lập (46 câu đầu và 30 câu đợt 2).
- `checked`: đã qua kiểm tra độc lập tự động.
- `ok`: chủ repo đã tự đọc và xác nhận.
