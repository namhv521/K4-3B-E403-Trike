# Reflection cá nhân — Hoàng Văn Nam

> Bản nháp này được tổng hợp từ các yêu cầu và quyết định kỹ thuật trong lịch sử làm việc của prototype. Trước khi nộp, tôi cần tự chỉnh lại bằng trải nghiệm và phần đóng góp thực tế của mình; không dùng phần này để thay thế quote hay kết quả validation của người dùng.

## Thông tin cá nhân

- Họ và tên: Hoàng Văn Nam
- Mã học viên: 2A202602853
- Nhóm: _Điền tên nhóm_
- Candidate problem nhóm chọn: Học viên cần ôn lại một bài học qua video ngắn có checkpoint, phản hồi có căn cứ và quyền tự chọn xem lại/tiếp tục.

---

## 1. Tôi đã tham gia vào phần nào?

| Hoạt động | Tôi đã làm gì? (việc cụ thể) | Kết quả / ảnh hưởng tới nhóm |
|---|---|---|
| Phân công CP1 | Nhận nhiệm vụ prototype web, video interactive, AI call thật và logic A/B/C/D; luồng mong muốn là đúng → skip 10 giây, sai → xem lại 5 giây. | Đây là phạm vi được nhóm giao; phần AI call thật và toàn bộ logic A/B/C/D cần tiếp tục đối chiếu bằng commit/demo. |
| Prototype web | Rà soát luồng Admin và Learner của website interactive, tập trung vào catalog lecture, local user và session học. | Luồng demo tách rõ role Admin/User nhưng vẫn dùng được dữ liệu local chung. |
| Dashboard admin | Bố trí lại panel role local và tạo recap, đưa dashboard lớp học xuống toàn chiều rộng; dùng dữ liệu analytics sẵn có để dựng biểu đồ SVG. | Admin có thể xem tiến độ hoàn thành, điểm các phiên hoàn thành và nhịp event mà không thêm thư viện chart, endpoint hay dữ liệu mock. |
| Logic Learner | Kiểm tra nơi local user được persist và nơi trang learner khởi tạo. | Khi learner đổi user trong dropdown, user ID được lưu trước rồi learner page reload để khởi tạo lại theo user đang chọn. |
| Kiểm thử hồi quy | Chạy syntax check, Node test, Python test và `git diff --check` sau thay đổi. | Bản kiểm tra gần nhất có 14/14 Node test và 21/21 Python test pass; thay đổi reload không sửa telemetry, tracking hay điều hướng Admin. |

**Dấu tay rõ nhất của tôi trong artifact cuối:** Tôi góp phần làm rõ trạng thái local learner trong frontend: lựa chọn user được persist, reload có chủ đích chỉ diễn ra khi người học đổi user, và phiên mới đọc lại identity đó trước khi gửi event. Tôi cũng ưu tiên dùng dữ liệu analytics hiện có và test hồi quy thay vì thêm dependency hoặc “làm đẹp” bằng số liệu không kiểm chứng. Tôi chưa dùng log chat này để khẳng định mình đã hoàn tất AI call thật hay tất cả nhánh A/B/C/D; các phần đó cần có commit/demo tương ứng trước khi nộp.

---

## 2. Bảng dùng AI

| Phase | Tôi dùng AI để làm gì? | AI hữu ích ở đâu? | AI sai / hời hợt ở đâu? | Tôi sửa gì bằng nhận định của mình? |
|---|---|---|---|---|
| Rà soát yêu cầu | Tóm tắt các yêu cầu UI và luồng role từ hội thoại. | Gom được các đầu việc: bố cục Admin, chart, catalog lecture và reload learner. | Tóm tắt không thay thế việc đọc code vì không chỉ ra ngay module nào persist user. | Đọc `app.js`, `admin.js`, HTML và test trước khi chọn vị trí sửa. |
| Dashboard | Gợi ý cách trực quan hóa completion, score và activity. | Đề xuất native SVG/DOM phù hợp constraint không thêm chart library. | Có thể biến biểu đồ thành phần trang trí nếu không bám analytics thật. | Chỉ dùng fields đã có như `views`, `completed_sessions`, `sessions`, `recent_events`; thêm test cho transform malformed/empty. |
| Role switching | Phân tích yêu cầu “đổi learner thì refresh”. | Gợi ý persist user trước rồi reload để startup đọc đúng identity. | Có thể đề xuất reload ở Admin dù thao tác chọn user đang nằm ở Learner page. | Xác định `#user-select` và `selectedUserStorageKey` trong `app.js`; chỉ gắn reload ở listener `change`. |
| Kiểm thử | Gợi ý các lệnh syntax/test cần chạy. | Nhắc kiểm tra Node test, Python test và whitespace diff. | Không thể thay thế kết quả chạy thật hoặc browser observation. | Chạy test thật, ghi kết quả pass/fail, và để validation thực tế cho người dùng ngoài nhóm. |

---

## 3. Reflection câu hỏi mở

Trong lần lặp này, tôi nhận ra một yêu cầu UX ngắn như “đổi learner thì refresh” vẫn cần được truy vết qua toàn bộ vòng đời trạng thái trước khi sửa. Ban đầu có thể nghĩ chỉ cần đổi link từ Admin sang User, nhưng user local thực tế được chọn trong dropdown của trang learner và được lưu dưới khóa `vlearn-local-user-id`. Vì vậy tôi chọn lưu giá trị mới trước, rồi gọi reload để hàm khởi tạo đọc lại đúng user thay vì cố cập nhật từng phần của catalog, lesson và telemetry trong trang đang chạy. Quyết định này giữ phạm vi thay đổi nhỏ và không làm ảnh hưởng điều hướng Admin hay cơ chế gửi event hiện có. Tôi cũng học được rằng dashboard không cần thêm thư viện biểu đồ nếu dữ liệu sẵn có và việc biến đổi dữ liệu được tách ra để test. Phần khó hơn giao diện là xác định đâu là dữ liệu thật, đâu là phần cần để trống cho validation; vì vậy tôi không được ghi quote hoặc kết luận về người dùng khi chưa quan sát họ dùng prototype. Các test kỹ thuật pass giúp phát hiện regression, nhưng không chứng minh learner hiểu checkpoint hay thao tác đổi role có dễ hiểu. Khi làm lại, tôi sẽ mời người ngoài nhóm thực hiện một task theo outcome, quan sát họ có nhận ra local user đang đổi hay không, rồi ghi hành vi và quote nguyên văn vào workbook validation. Tôi cũng sẽ đối chiếu ít nhất một thay đổi từ feedback đó vào §9 Changelog của `spec.md`, thay vì chỉ dùng nhận định của nhóm. Bài học lớn nhất là phản hồi kỹ thuật và phản hồi người dùng phải được lưu thành hai loại bằng chứng khác nhau: lượt chạy toàn bộ trong `eval/` và hành vi/quote thực tế trong `validation/`.

---

## 4. Tự kiểm trước khi nộp

- [ ] Tôi đã thay mã học viên, tên nhóm và các mô tả bằng thông tin đúng của bản thân.
- [ ] Tôi đã đối chiếu nội dung với commit/artefact mình thật sự tham gia.
- [ ] Tôi đã bổ sung ít nhất một quan sát hoặc bài học từ validation thật, không tự tạo quote.
- [ ] `eval/` có kết quả của mọi lượt chạy, gồm cả fail (nếu có).
- [ ] `validation/` có log người ngoài nhóm và quyết định thay đổi/giữ nguyên được cập nhật vào `spec.md` §9.
