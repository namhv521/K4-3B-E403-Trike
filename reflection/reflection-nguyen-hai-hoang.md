# Reflection cá nhân — Nguyễn Hải Hoàng

> Bản nháp này chỉ dựa trên phân công CP1 do nhóm cung cấp và log chat hiện tại. Trước khi nộp, tôi cần tự chỉnh bằng trải nghiệm, commit và evidence thực tế của mình; không dùng file này để thay thế transcript, quote hay số liệu mining chưa có.

## Thông tin cá nhân

- Họ và tên: Nguyễn Hải Hoàng
- Mã học viên: 2A202602489
- Nhóm: Trike
- Candidate problem nhóm chọn: Học viên cần ôn lại một bài học qua video ngắn có checkpoint, phản hồi có căn cứ và quyền tự chọn xem lại/tiếp tục.

---

## 1. Tôi đã tham gia vào phần nào?

| Hoạt động | Tôi đã làm gì? (việc cụ thể) | Kết quả / ảnh hưởng tới nhóm |
|---|---|---|
| Phân công CP1 | Nhận nhiệm vụ mining evidence, phỏng vấn user, lập bảng đếm pain point và lưu mã hội thoại. | Đây là phạm vi được nhóm giao; cần đối chiếu bằng file mining, log phỏng vấn và mã hội thoại trước khi khẳng định đã hoàn tất. |
| Mining evidence | Chuẩn bị hướng tiếp cận trích nguồn, phân loại pain point và liên kết phát hiện với evidence kiểm lại được. | Giúp problem statement không chỉ dựa trên cảm nhận; log chat hiện tại chưa có bảng mining đã điền. |
| Phỏng vấn user | Phạm vi là hỏi người học về lần gần nhất ôn/tua video và khó khăn khi trả lời checkpoint. | Cần có transcript hoặc quote nguyên văn, người trả lời và thời điểm; chưa có trong log chat. |
| Bảng đếm pain point | Phạm vi là tổng hợp các pain point theo định nghĩa/mẫu số rõ ràng thay vì chọn vài câu nổi bật. | Cần có số đếm, tỷ lệ và ví dụ đã ẩn danh trước khi dùng để ra quyết định sản phẩm. |
| Mã hội thoại | Phạm vi là lưu `turn_id`/conversation ID để truy ngược pain point về dữ liệu gốc. | Tạo được đường trace từ insight đến evidence và case kiểm thử; cần bổ sung artifact tương ứng. |

**Dấu tay rõ nhất của tôi trong artifact cuối:** Tôi phụ trách biến dữ liệu thô thành bằng chứng kiểm lại được cho problem statement và evaluation. Trong log hiện tại mới có thay đổi kỹ thuật của prototype, chưa có evidence mining/phỏng vấn do tôi thực hiện; vì vậy tôi không dùng file này để khẳng định các bảng đếm hay quote đã hoàn thành.

---

## 2. Bảng dùng AI

| Phase | Tôi dùng AI để làm gì? | AI hữu ích ở đâu? | AI sai / hời hợt ở đâu? | Tôi sửa gì bằng nhận định của mình? |
|---|---|---|---|---|
| Rà soát evidence | Hỗ trợ nhóm các chủ đề từ ghi chú hoặc hội thoại. | Có thể gợi ý nhãn pain point và các điểm cần kiểm tra. | Có thể gom nhầm các câu có ngữ cảnh khác nhau hoặc bịa chi tiết thiếu trong nguồn. | Giữ link/mã hội thoại cho từng nhận định và đọc lại nguồn gốc trước khi chốt mã. |
| Chuẩn bị phỏng vấn | Gợi ý câu hỏi mở về lần gần nhất người học ôn hoặc tua video. | Giúp tránh câu hỏi dẫn dắt và mở đầu bằng bối cảnh thật. | Không thay thế người dùng thật; không được biến câu trả lời dự đoán thành hành vi. | Ghi quote nguyên văn, hành vi quan sát được và không pitch UI trong lúc người dùng làm task. |
| Bảng đếm | Hỗ trợ chuẩn hóa tên nhãn và định dạng bảng tổng hợp. | Giảm lỗi thủ công khi nhóm evidence đã được xác nhận. | Không tự quyết định mẫu số, quy tắc mã hóa hoặc ý nghĩa của tỷ lệ. | Ghi rõ mẫu số, quy tắc đếm, case mơ hồ và người kiểm tra độc lập nếu có. |
| Liên kết evaluation | Gợi ý chuyển pain point thành case cho golden set hoặc validation task. | Nhắc kiểm tra case khó ngoài happy path. | Có thể đề xuất case không phản ánh bằng chứng thật. | Chỉ thêm case khi trace được về evidence hoặc yêu cầu đã chốt trong spec. |

---

## 3. Reflection câu hỏi mở

Trong lần lặp này, tôi nhận ra thay đổi kỹ thuật có thể làm prototype chạy tốt hơn nhưng chưa tự chứng minh rằng nó giải quyết đúng khó khăn của người học. Phân công của tôi là cung cấp phần bằng chứng cho quyết định đó: mỗi nhận định về việc ôn video, tua lại đoạn kiến thức hoặc làm sai checkpoint cần có nguồn và cách kiểm lại. Tôi cần tách số đếm khỏi cảm nhận bằng cách ghi rõ đã đọc bao nhiêu mẫu, mã hóa theo quy tắc nào và xử lý các câu mơ hồ ra sao. Khi phỏng vấn, tôi nên hỏi về trải nghiệm thật gần nhất của người dùng thay vì hỏi họ có thích giải pháp không. Nếu có quote, tôi phải chép nguyên văn và không biến “có lẽ sẽ dùng” thành bằng chứng sử dụng thật. Các pain point đã mã hóa cũng cần được dùng để tạo hoặc rà lại golden set, để case kiểm thử không chỉ là happy path. Hiện tại log chat chưa có bảng mining, transcript hay mã hội thoại do tôi tạo, nên việc cần làm trước khi nộp là bổ sung evidence thật rồi liên kết cụ thể vào reflection này.

---

## 4. Tự kiểm trước khi nộp

- [ ] Tôi đã thay tên nhóm và các mô tả bằng thông tin đúng của bản thân.
- [ ] Tôi đã đối chiếu nội dung với commit/artefact mình thật sự tham gia.
- [ ] Có bảng mining với nguồn, mẫu số, quy tắc mã hóa và số đếm.
- [ ] Có log phỏng vấn user với câu hỏi, quote nguyên văn và mã hội thoại/turn ID.
- [ ] Không khẳng định insight nào nếu chưa có bằng chứng kiểm lại được.
