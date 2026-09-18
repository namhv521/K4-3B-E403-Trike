# Reflection cá nhân — Nguyễn Danh Gia Minh

> Bản nháp này chỉ dựa trên phân công CP1 do nhóm cung cấp và log chat hiện tại. Trước khi nộp, tôi cần tự chỉnh bằng trải nghiệm, commit và evidence thực tế của mình; không dùng file này để thay thế JTBD, prompt, source mapping hay output AI chưa có.

## Thông tin cá nhân

- Họ và tên: Nguyễn Danh Gia Minh
- Mã học viên: 2A202602441
- Nhóm: _Điền tên nhóm_
- Candidate problem nhóm chọn: Học viên cần ôn lại một bài học qua video ngắn có checkpoint, phản hồi có căn cứ và quyền tự chọn xem lại/tiếp tục.

---

## 1. Tôi đã tham gia vào phần nào?

| Hoạt động | Tôi đã làm gì? (việc cụ thể) | Kết quả / ảnh hưởng tới nhóm |
|---|---|---|
| Phân công CP1 | Nhận nhiệm vụ JTBD/spec, thiết kế logic AI, prompt và tiêu chí kiểm tra câu hỏi/đáp án có đủ căn cứ từ bài học. | Đây là phạm vi được nhóm giao; phần JTBD, prompt và logic AI cần có artifact/commit tương ứng trước khi khẳng định đã hoàn tất. |
| JTBD | Phạm vi là xác định người học, thời điểm cần ôn/tua video, outcome mong muốn và lựa chọn thay thế hiện có. | Candidate problem trong log hướng tới video ngắn có checkpoint và phản hồi có căn cứ; chưa có log xác nhận JTBD do tôi viết. |
| Spec | Phạm vi là biến JTBD thành boundary, metric, hard case và changelog kiểm lại được. | `spec.md` có quality dimensions, hard cases và validation plan, nhưng chat không xác nhận mục nào do tôi thực hiện. |
| Logic AI và prompt | Phạm vi là thiết kế cách AI tạo/đánh giá phản hồi, gồm fallback cho câu trả lời mơ hồ, thiếu căn cứ hoặc ngoài phạm vi. | Chưa có prompt version, output AI hoặc kết quả chạy do tôi tạo trong log chat. |
| Tiêu chí đủ căn cứ | Phạm vi là kiểm tra question, answer, explanation và timecode có trace được về transcript, slide hoặc source bài học. | Giữ phản hồi có căn cứ thay vì tự tin đoán; cần bổ sung rubric/source mapping và case pass/fail. |

**Dấu tay rõ nhất của tôi trong artifact cuối:** Tôi phụ trách biến yêu cầu “phản hồi có căn cứ” thành điều kiện kiểm tra được: câu hỏi, đáp án, giải thích và timecode phải trace được về bài học; khi không đủ căn cứ thì hệ thống cần dùng fallback an toàn thay vì tự chấm chắc. Log chat hiện tại chưa có artifact cụ thể do tôi tạo, nên tôi không dùng file này để khẳng định phần prompt/logic AI đã hoàn tất.

---

## 2. Bảng dùng AI

| Phase | Tôi dùng AI để làm gì? | AI hữu ích ở đâu? | AI sai / hời hợt ở đâu? | Tôi sửa gì bằng nhận định của mình? |
|---|---|---|---|---|
| JTBD/spec | Hỗ trợ tóm tắt candidate problem, giả định và các hard case cần đưa vào spec. | Gợi ý cấu trúc job statement, outcome và boundary. | Có thể biến suy đoán thành nhu cầu người dùng nếu thiếu evidence. | Chỉ chốt JTBD sau khi đối chiếu mining/phỏng vấn và ghi rõ điều chưa biết. |
| Thiết kế prompt | Gợi ý prompt structure, output schema và fallback. | Hỗ trợ nghĩ đến low-confidence, thiếu căn cứ và ngoài phạm vi. | Có thể trả lời nghe thuyết phục nhưng không trace được nguồn bài học. | Bắt buộc source/timecode mapping; thiếu mapping thì không khẳng định đáp án. |
| Rubric grounded | Hỗ trợ chuyển tiêu chí chất lượng thành checklist/case kiểm thử. | Gợi ý kiểm tra question, answer, explanation và citation. | Không tự biết transcript/slide nào là nguồn đúng nếu input thiếu hoặc sai. | So khớp từng trường với source thật, lưu expected behavior trong golden set. |
| Đánh giá output | Hỗ trợ nhận diện failure mode và nhóm output lỗi. | Tạo điểm khởi đầu để rà case khó. | Không thể tự làm trọng tài cuối cùng cho chất lượng học tập. | Dùng quality bar đã chốt, chấm case khó độc lập và lưu failure trong `eval/`. |

---

## 3. Reflection câu hỏi mở

Điểm quan trọng của phần JTBD và spec là không mô tả sản phẩm như mục tiêu tự thân. Từ log hiện tại, lát cắt đang hướng tới người học cần ôn lại một lecture, gặp checkpoint và có quyền xem nguồn, xem lại hoặc tiếp tục. Để biến mô tả này thành spec tốt, tôi cần xác định rõ người học nào, lúc nào họ phải tua video và tiêu chí nào cho thấy họ đã hiểu lại concept. Tôi cũng cần tách logic AI khỏi UI: một biểu đồ hoặc reload user không chứng minh câu hỏi và đáp án có căn cứ. Tiêu chí cần kiểm tra là mọi question, answer, explanation và timecode đều trace được về nguồn bài học; nếu thiếu mapping thì phải dùng fallback an toàn thay vì khẳng định. Các hard case trong spec như câu trả lời mơ hồ, không đủ căn cứ, ngoài phạm vi hoặc đoán đúng nhưng chưa hiểu cần có expected behavior rõ ràng trong golden set. Trong chat chưa có prompt version hoặc output để đánh giá, nên ưu tiên tiếp theo của tôi là bổ sung chúng và ghi failure thật, không tự tuyên bố AI call đúng. Sau đó tôi có thể dùng log validation để xem người học có hiểu phản hồi có căn cứ hay không, thay vì chỉ đánh giá chất lượng câu chữ của AI.

---

## 4. Tự kiểm trước khi nộp

- [ ] Tôi đã thay tên nhóm và các mô tả bằng thông tin đúng của bản thân.
- [ ] Tôi đã đối chiếu nội dung với commit/artefact mình thật sự tham gia.
- [ ] Có JTBD với người dùng cụ thể, job statement, alternatives và evidence.
- [ ] Có spec/prompt/rubric do tôi phụ trách hoặc có liên kết commit rõ ràng.
- [ ] Tiêu chí grounded liên kết được question/answer/explanation/timecode tới nguồn và có golden-set case.
