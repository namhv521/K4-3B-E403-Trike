# Reflection cá nhân — Lê Tuấn Đạt

> Bản nháp này chỉ dựa trên phân công CP1 do nhóm cung cấp và log chat hiện tại. Trước khi nộp, tôi cần tự chỉnh bằng trải nghiệm, commit và evidence thực tế của mình; không dùng file này để thay thế log chạy, quote user test hay golden-set output chưa có.

## Thông tin cá nhân

- Họ và tên: Lê Tuấn Đạt
- Mã học viên: 2A202602623
- Nhóm: _Điền tên nhóm_
- Candidate problem nhóm chọn: Học viên cần ôn lại một bài học qua video ngắn có checkpoint, phản hồi có căn cứ và quyền tự chọn xem lại/tiếp tục.

---

## 1. Tôi đã tham gia vào phần nào?

| Hoạt động | Tôi đã làm gì? (việc cụ thể) | Kết quả / ảnh hưởng tới nhóm |
|---|---|---|
| Phân công CP1 | Nhận nhiệm vụ logging, leaderboard, user test, feedback log, golden set, demo và tổng hợp kết quả. | Đây là phạm vi được nhóm giao; từng phần cần commit hoặc evidence tương ứng trước khi khẳng định đã hoàn tất. |
| Logging | Phạm vi là ghi nhận sự kiện/kết quả cần thiết cho việc theo dõi prototype và đánh giá. | Log chat hiện tại chỉ xác nhận prototype có telemetry/session events, chưa xác nhận phần logging do tôi triển khai. |
| Leaderboard | Phạm vi là làm rõ dữ liệu và cách hiển thị tiến độ/xếp hạng nếu tính năng này còn thuộc lát cắt sản phẩm. | Chưa có artifact leaderboard trong log chat; không đưa vào demo như tính năng đã hoàn thiện nếu chưa có bằng chứng. |
| Golden set và lượt chạy | Chuẩn bị cách lưu case, input, output, pass/fail và failure lớn nhất qua từng lần chạy. | Có template trong `eval/`; kết quả kỹ thuật hiện có là 14/14 Node test và 21/21 Python test pass, chưa phải golden set AI hoàn chỉnh. |
| User test, feedback log và demo | Phạm vi là ghi task, quan sát, quote, severity, tổng hợp quyết định và đưa evidence vào demo. | Có template `validation/` nhưng chưa có log người dùng thật được điền trong chat; cần bổ sung trước CP5. |

**Dấu tay rõ nhất của tôi trong artifact cuối:** Tôi phụ trách làm cho kết quả được ghi nhận có cấu trúc: log an toàn, golden set, feedback log và kết luận demo dựa trên dữ liệu. Tôi chỉ dùng kết quả 14/14 Node test và 21/21 Python test như evidence test hồi quy hiện có, không suy rộng thành kết quả validation hay hiệu quả học tập.

---

## 2. Bảng dùng AI

| Phase | Tôi dùng AI để làm gì? | AI hữu ích ở đâu? | AI sai / hời hợt ở đâu? | Tôi sửa gì bằng nhận định của mình? |
|---|---|---|---|---|
| Thiết kế log | Gợi ý trường cần ghi cho event, run log và feedback log. | Nhắc phân biệt technical run với user validation. | Có thể đề xuất thu thập quá nhiều dữ liệu hoặc bỏ qua privacy/redaction. | Chỉ log dữ liệu cần thiết, dùng allowlist và kiểm tra output trước khi lưu/chia sẻ. |
| Golden set | Gợi ý case thường, case khó và cấu trúc expected output. | Hỗ trợ rà thiếu coverage và failure mode. | Có thể sinh case nghe hợp lý nhưng không bám spec/evidence. | Chốt pass/fail theo quality bar trong spec, lưu mọi lượt chạy gồm cả fail. |
| User test | Hỗ trợ soạn task theo outcome và câu hỏi sau khi dùng. | Nhắc người điều phối im lặng quan sát và log quote nguyên văn. | Không thể thay thế quan sát người dùng thật hay tự tạo quote. | Mời người ngoài nhóm, ghi hành vi trước rồi mới diễn giải severity/decision. |
| Demo/tổng hợp | Gợi ý cách trình bày pass rate, failure và thay đổi sau feedback. | Giúp tách kết quả tốt với limitation còn lại. | Có thể làm slide đẹp nhưng che mất failure chưa giải quyết. | Luôn nêu failure lớn nhất, evidence nguồn và điều chưa được validation. |

---

## 3. Reflection câu hỏi mở

Vai trò của tôi nối phần prototype với bằng chứng nhóm có thể trình bày. Log hiện tại cho thấy việc chạy syntax check, Node test, Python test và `git diff --check` là cần thiết để biết thay đổi có gây regression không. Tuy nhiên, một tỷ lệ test kỹ thuật pass không nói người học có hiểu checkpoint hoặc có tự tìm được luồng xem lại hay không. Vì vậy tôi cần ghi tách các loại kết quả: lượt chạy kỹ thuật ở `eval/`, còn hành vi và quote của người ngoài nhóm ở `validation/`. Golden set cũng phải giữ tất cả lượt chạy, kể cả fail, để không chỉ show số đẹp sau khi sửa. Với user test, tôi cần giao task theo outcome, im lặng quan sát và chép nguyên văn lời người dùng thay vì giải thích UI cho họ. Nếu feedback chỉ là lời khen chung chung, tôi cần đổi task khó hơn hoặc hỏi lại về thao tác cụ thể. Phần leaderboard chưa có bằng chứng trong log hiện tại, nên tôi không nên đưa nó vào demo như một tính năng đã hoàn thiện. Việc cần làm trước khi nộp là điền dữ liệu thật vào các template, tổng hợp một failure đáng kể và trỏ ít nhất một quyết định thay đổi vào changelog.

---

## 4. Tự kiểm trước khi nộp

- [ ] Tôi đã thay tên nhóm và các mô tả bằng thông tin đúng của bản thân.
- [ ] Tôi đã đối chiếu nội dung với commit/artefact mình thật sự tham gia.
- [ ] `eval/` có golden set và toàn bộ lượt chạy, gồm cả fail.
- [ ] `validation/` có task, hành vi, quote, severity và quyết định từ người ngoài nhóm.
- [ ] Demo/tổng hợp tách rõ test kỹ thuật, golden set và validation người dùng.
