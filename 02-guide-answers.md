# Trả lời câu hỏi trong `02-guide.md`

## 0. Giả định và điểm cần chốt

Mô tả công việc trong `README.md` là: học viên trả lời câu hỏi ngay trong video; hệ thống kiểm tra câu trả lời dựa trên bài học và điều hướng sang đoạn phù hợp (đúng: tiếp tục/nhảy 10 giây; sai: nhận gợi ý rồi xem lại 5 giây). Đây là một trải nghiệm học thích ứng, nên phù hợp nhất với **Track D — đề mới cùng khung D2 (học từ lỗi trước)**, không phải Track C. Trước khi nộp, cần đổi trường `Track: C` trong `README.md` và chọn D trong spec để các artifact nhất quán.

Prototype không được coi việc “đúng/sai” là phán quyết không giải thích được: mỗi nhận định phải bám vào một đoạn transcript/slide đã chọn; khi thiếu căn cứ, hệ thống không điều hướng theo câu trả lời đó.

---

## §1. Khám phá

### 1.1 Năm câu hỏi theo thứ tự

1. **Ai trực tiếp làm việc này?**  
   Học viên đang xem một đoạn video bài giảng VLearn lần đầu hoặc ôn lại trước quiz, vừa gặp câu hỏi kiểm tra hiểu bài chen trong video.

2. **Họ cố hoàn thành việc gì?**  
   *Tự kiểm tra mình có hiểu một khái niệm vừa xem hay không và quay lại đúng đoạn cần xem lại trước khi tiếp tục bài.*  
   Câu này không có tên sản phẩm hay AI; dù không có prototype, công việc vẫn tồn tại.

3. **Họ đang làm bằng gì, fail ở đâu, và vì sao chưa bỏ?**

   | Cách hiện tại | Fail ở đâu | Vì sao vẫn dùng |
   |---|---|---|
   | Xem video tuyến tính | Học viên dễ xem tiếp dù chưa hiểu; khi sai không biết sai giả định nào hoặc cần tua về đâu. | Sẵn có, không cần chuẩn bị thêm. |
   | Kéo thanh thời gian/tua lại | Phải tự nhớ đoạn nào liên quan; thao tác thử-sai, dễ tua quá xa hoặc quá gần. | Nhanh nhất trong player hiện tại. |
   | Hỏi tutor/ChatGPT riêng | Câu trả lời có thể không bám đúng video đang xem; ngắt mạch học và khó biết có đáng tin không. | Linh hoạt với câu hỏi tự do. |
   | Bỏ qua câu khó | Không tốn thêm thời gian ngay lúc đó, nhưng tạo lỗ hổng kiến thức và khó ôn sau này. | Deadline/nhịp học khiến học viên ưu tiên đi tiếp. |

4. **Bằng chứng nào cho thấy pain là thật?**  
   Chưa có log evidence trong repo tại thời điểm soạn tài liệu này; không được thay bằng cảm nhận của nhóm. Với Track D, hoàn tất cả hai nguồn sau:
   - **Mining:** đọc trước 30–50 lượt trong `data/vlearn-pack/chatlog/tutor_turns.csv`, sau đó đếm các lượt có tín hiệu học viên chưa hiểu/đòi giải thích lại/tìm đoạn cần xem lại. Lưu quy tắc phân loại, số tổng, mã `turn_id` và ít nhất 5 trích dẫn ngắn.
   - **Phỏng vấn/quan sát:** cho ít nhất 5 học viên ngoài nhóm học một đoạn bằng video hiện tại/prototype. Hỏi về **lần gần nhất** họ không hiểu khi xem video: đã làm gì, tua mất bao lâu, có bỏ qua không. Lưu câu hỏi, người trả lời, nguyên văn câu trả lời và hành vi quan sát được.

5. **Có ít nhất ba hướng nào, tại sao chọn hướng này?**

   | Ứng viên | Người gặp / tần suất / chi phí | Khả thi trong hackathon | Quyết định |
   |---|---|---|---|
   | A. Tóm tắt video sau khi xem | Có thể hữu ích cho phần lớn học viên; nhưng chưa giải quyết khoảnh khắc “vừa sai vừa không biết xem lại đâu”. Cần đo thật. | Dễ build. | Loại: giá trị học chủ động và điều hướng theo lỗi thấp hơn. |
   | B. Tutor hỏi đáp tự do cạnh video | Hữu ích khi có câu hỏi mở; nhưng khó đánh giá đúng/sai và dễ lạc khỏi video đang xem. Cần đo thật. | Trung bình; cần retrieval và UX chat. | Loại ở lát cắt này: quá rộng, nhiều quyết định AI. |
   | C. Câu hỏi checkpoint trong video + gợi ý có căn cứ + điều hướng đoạn ôn | Nhắm đúng lúc học viên cần tự kiểm; mỗi lần tua sai/đi hỏi riêng đều làm gián đoạn mạch học. Cần đo số người, tần suất và số phút thật. | Có thể demo một video, vài checkpoint và một AI decision. | **Chọn**, nếu evidence xác nhận pain. |

Lý do chọn cuối cùng phải thay các mô tả định tính bằng số thật theo công thức: `số học viên gặp × số lần/buổi × số phút hoặc hậu quả/lần`. Không dùng số giả.

### 1.2 Job stories

1. **Khi** vừa xem xong một khái niệm và gặp câu hỏi checkpoint, **tôi muốn** biết câu trả lời của mình đúng ở điểm nào hoặc sai ở giả định nào, **để** không tiếp tục bài với một lỗ hổng kiến thức.
2. **Khi** trả lời chưa đủ căn cứ, **tôi muốn** được đưa về đúng đoạn ngắn liên quan thay vì tua mò cả video, **để** ôn lại nhanh mà không mất mạch học.
3. **Khi** câu hỏi hoặc câu trả lời của tôi không đủ rõ, **tôi muốn** được hỏi lại hoặc xem đáp án có nguồn, **để** không bị chấm sai và vẫn tự quyết định bước tiếp theo.

### 1.3 Phương pháp mining và phỏng vấn phải lưu

**Mining đề xuất**

1. Đọc ngẫu nhiên 30–50 lượt K4 trước; ghi các nhãn sơ bộ: `không hiểu khái niệm`, `xin ví dụ`, `hỏi lại`, `không biết xem phần nào`, `khác`.
2. Chốt quy tắc: một lượt được tính “cần ôn lại” khi câu hỏi trực tiếp thể hiện chưa hiểu hoặc yêu cầu giải thích/xem lại một nội dung vừa học; không tính câu logistics hay câu chào.
3. Chạy đếm trên tập đã định, kiểm tra tay một mẫu của mỗi nhãn; lưu script/bảng đếm và tối thiểu năm `turn_id` minh họa.

**Câu hỏi Mom Test**

- “Lần gần nhất bạn xem video bài giảng mà không hiểu một đoạn, bạn đã làm gì ngay sau đó?”
- “Bạn tua hoặc tìm lại đoạn đó mất khoảng bao lâu? Có lúc nào bạn bỏ qua không?”
- “Bạn có thể kể một lần câu hỏi kiểm tra làm bạn biết mình chưa hiểu không?”
- “Bạn đã thử hỏi ai/công cụ nào? Vì sao cách đó chưa đủ?”

Không hỏi “Bạn có thích tính năng AI tự tua video không?”. Log phải có: người hỏi, người trả lời, thời điểm, câu hỏi nguyên văn, câu trả lời nguyên văn, và không suy đoán danh tính từ data pack.

---

## §2. Thiết kế & Spec

### 2.1 Bốn câu hỏi thiết kế

1. **Giải pháp tương tự:**
   - *Khanmigo:* dùng câu hỏi Socratic thay vì cho đáp án ngay. Học: gợi ý theo bậc để học viên tự sửa. Né: không để chat dài làm rời video.
   - *Duolingo:* checkpoint ngắn, phản hồi ngay sau câu trả lời. Học: phản hồi rõ và nhịp nhanh. Né: chỉ báo đúng/sai không giải thích, có thể biến học thành đoán.
   - *NotebookLM/ChatGPT Study Mode:* trả lời dựa nguồn và gợi mở. Học: hiển thị căn cứ để kiểm chứng. Khác biệt của nhóm: output không phải câu trả lời dài mà là quyết định điều hướng một đoạn video cụ thể.

2. **AI tự làm đến đâu?**  
   Chọn **conditional automation**. AI tự chấm ngữ nghĩa và đề xuất nhánh chỉ khi câu trả lời đối chiếu được với rubric và đoạn nguồn. Học viên chịu hậu quả học sai nếu hệ thống chấm sai; vì vậy không tự coi đáp án là đúng khi confidence thấp, không tự bỏ qua checkpoint quan trọng, và luôn cho học viên xem nguồn/chọn “tự xem lại”. Sửa một điều hướng sai rẻ, nhưng kiến thức sai và niềm tin bị mất là đắt.

3. **Khi sai/không chắc:**
   - Không đủ câu trả lời: hỏi một câu làm rõ hoặc cho chọn “xem lại đoạn liên quan”.
   - Không tìm được căn cứ: hiện “Mình chưa đối chiếu được câu trả lời này với bài học, nên không tự điều hướng”, kèm nút xem đoạn gốc/đổi câu trả lời.
   - Câu trả lời sai: nêu *một* giả định sai, dẫn mã đoạn nguồn, gợi ý ngắn; sau đó để học viên tự trả lời lại hoặc xem lại 5 giây.
   - Học viên không đồng ý: cho sửa câu trả lời, xem rubric/nguồn và tiếp tục theo lựa chọn của họ; log bất đồng để xem lại prompt, không tranh cãi.

4. **“Tốt” là gì?**  
   Tốt là chẩn đoán đúng theo rubric có nguồn, đưa đúng đoạn ôn với gợi ý vừa đủ, và giúp học viên trả lời lại/giải thích lại được. Bar nháp để chốt trước CP4: `≥85%` case qua toàn bộ golden set **và 100% case không có căn cứ hoặc low-confidence không được chấm chắc/điều hướng tự động**. Bar chỉ được giữ nếu nhóm xây đủ golden set và chốt trước deadline; sau đó không đổi để hợp thức hóa kết quả.

### 2.3 Ba cam kết hành vi

- AI luôn phải đối chiếu đáp án với rubric và đoạn nguồn đã chọn, rồi hiển thị mã đoạn/đoạn video làm căn cứ.
- AI không được bịa nội dung bài, gán nhãn năng lực dài hạn cho học viên, hoặc tự động bỏ qua checkpoint quan trọng.
- Nếu dự đoán yếu, học viên có thể sửa câu trả lời hoặc tự xem lại đoạn nguồn; điều này chấp nhận được miễn là hệ thống nói rõ giới hạn và không chấm chắc.

### 2.4 Nguyên tắc HAX/PAIR áp dụng

| Nguyên tắc | Áp dụng cụ thể | Case kiểm |
|---|---|---|
| G1 — làm rõ khả năng | Màn hình đầu nói rõ hệ thống chỉ hỗ trợ checkpoint của video/bài đã nạp, không phải chấm mọi câu hỏi. | C13: hỏi ngoài video. |
| G2 — làm rõ giới hạn | Kết quả có nhãn “đã đối chiếu với [Txx-NNN]” hoặc “chưa đủ căn cứ”. | C11/C12: thiếu nguồn. |
| G10 — thu hẹp khi nghi ngờ | Câu trả lời rỗng/mơ hồ hoặc confidence thấp dẫn tới một câu hỏi làm rõ hay nút xem nguồn, không phán quyết. | C09/C10. |
| G9 — sửa dễ dàng | Ô trả lời giữ nguyên nội dung; học viên sửa và gửi lại mà không mất vị trí video. | C14. |
| G11 — giải thích vì sao | Phản hồi sai chỉ ra giả định sai và đoạn nguồn/timecode dẫn tới bước ôn tiếp theo. | C05/C06. |
| PAIR — feedback & control | Học viên có “Xem nguồn”, “Tự xem lại”, “Không đồng ý với nhận xét”; không bị ép theo nhánh AI. | C15. |

### 2.5 Bốn lớp chỗ khó và kịch bản nên kiểm

| Tình huống | Lớp | Hành vi mong muốn |
|---|---:|---|
| Đáp án đúng về mặt kiến thức nhưng không nằm trong transcript/rubric của bài đang xem | ① | Không tự nhận đúng; nói không đối chiếu được trong phạm vi bài, cho xem nguồn hoặc hỏi giảng viên. |
| Model trích sai mã đoạn/timecode | ① | Chặn output không khớp mapping; hiện lỗi có thể kiểm chứng và không điều hướng. |
| Học viên trả lời “em không biết” hoặc để trống | ② | Không chấm sai; gợi ý một bước hoặc cho xem lại đoạn ngắn. |
| Câu trả lời quá ngắn, có nhiều cách hiểu | ② | Hỏi một câu làm rõ, không đoán ý định. |
| Học viên yêu cầu bỏ checkpoint/cho toàn bộ đáp án bài kiểm tra | ③ | Nói rõ đây là công cụ luyện một checkpoint; có thể xem nguồn/gợi ý, không phát đáp án hay sửa điểm. |
| Học viên hỏi kiến thức thuộc bài khác | ③ | Nêu ngoài phạm vi video hiện tại và hướng tới tutor/nguồn phù hợp. |
| Học viên đoán đúng nhưng không giải thích được | ④ | Không chỉ nhảy 10 giây; hỏi một câu “vì sao” ngắn hoặc đánh dấu cần kiểm tra hiểu. |
| Học viên chọn sai do câu hỏi mơ hồ/lỗi đề | ④ | Không quy lỗi cho học viên; gắn cờ “cần giảng viên xem lại câu hỏi”, cho tiếp tục không phạt. |
| Một misconception thường gặp nhưng diễn đạt khác rubric | ④ | Chấm theo ý nghĩa có căn cứ, chỉ rõ khái niệm cần sửa thay vì khớp từ khóa. |

### 2.6 Golden set và đo

Tạo `eval/golden-set.md` hoặc CSV với tối thiểu 20 case: 8–10 case thường, 2 case cho mỗi lớp ①–④ (8 case), 2–4 case hiếm. Với Track D, ít nhất 10 case cần lấy/phát triển từ chatlog thật và dẫn `turn_id`; không dán nguyên data pack.

Các cột tối thiểu: `id | nguồn/turn_id | input | rubric/đoạn nguồn | lớp | expected behavior | factuality pass | diagnosis/route pass | learner-safety pass | kết quả`. Hai thành viên chấm độc lập 5 case khó trước khi chốt rubric. Mỗi lần chạy phải lưu toàn bộ output, pass/fail và tỷ lệ vào `eval/`; không bỏ case fail.

---

## §3–§5. Build, validate và demo

### Flow demo 5 phút

1. Học viên mở một đoạn video và nhận checkpoint đã công bố phạm vi.
2. **Happy path:** trả lời đúng, hệ thống chỉ ra căn cứ ngắn và chuyển tới đoạn tiếp theo/nhảy 10 giây.
3. **Hard case:** trả lời sai theo misconception, hệ thống chỉ rõ giả định sai, cite đoạn nguồn và phát lại 5 giây; học viên sửa câu trả lời.
4. **Failure case:** input ngoài phạm vi hoặc không đủ căn cứ; hệ thống không bịa/chấm chắc mà chỉ rõ giới hạn và đưa bước tiếp theo.

### Validation cần thực hiện

Mời ít nhất 5 học viên ngoài nhóm (yêu cầu riêng Track D). Giao nhiệm vụ: “Học đoạn này, trả lời checkpoint, nếu chưa chắc hãy dùng cách bạn thấy phù hợp để tiếp tục.” Không hướng dẫn nút bấm. Với mỗi người ghi: vai/người thử, task, hành vi, quote nguyên văn, mức nghiêm trọng; sau đó hỏi “Điều khó hiểu nhất là gì?”, “Bạn tin kết quả không, vì sao?”, “Nếu ngày mai mất tính năng này, bạn tiếc mức nào?”.

Chỉ sửa trước demo những vấn đề lặp lại hoặc có mức nghiêm trọng cao; ghi thay đổi/giữ nguyên/backlog trong changelog. Slide cuối phải báo cả quality bar, kết quả thật và failure lớn nhất, không chỉ báo thành công.