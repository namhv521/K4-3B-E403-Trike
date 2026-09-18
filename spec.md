# AI SPEC — Checkpoint video thích ứng theo câu trả lời · Nhóm Trike · Zone 02

> **Trạng thái:** Đã cập nhật đầy đủ dữ liệu thực chứng (evidence từ khảo sát người học N = 21 tại `Asset/AI.xlsx`, mining chatlog trợ giảng N = 13,494), thông tin 2 willing users đã xác nhận tham gia và tiêu chí kiểm thử nghiệm thu.

**Hướng:** D — Học tập thích ứng & tương tác trên VLearn  
**Loại:** Tính năng mới (một lát cắt theo khung D2)

## §1. User & Job

- **Job executor + workflow:** Học viên đang xem/ôn một đoạn video VLearn → gặp checkpoint → tự trả lời → nhận phản hồi có căn cứ → chọn sửa đáp án hoặc xem lại đúng đoạn → tiếp tục bài. Hiện tại học viên thường xem tuyến tính, tự tua mò hoặc hỏi tutor/ChatGPT riêng.
- **Core JTBD:** Tự kiểm tra mình có hiểu một khái niệm vừa xem hay không và quay lại đúng đoạn cần xem lại trước khi tiếp tục bài.
- **Problem statement:** Khi trả lời sai hoặc chưa chắc tại một checkpoint trong video, học viên không biết sai giả định nào và phải tự tua/đi tìm hỗ trợ để xác định đoạn cần ôn; việc này ngắt mạch học và có thể khiến họ tiếp tục với kiến thức chưa vững.
- **Evidence:**
  - **Dữ liệu khảo sát người học thực tế (`Asset/AI.xlsx` — N = 21):** Khảo sát thực hiện ngày 17/09/2026 trên 21 học viên đại diện cho đối tượng người học trên VLearn:
    - **76.2% (16/21)** học viên gặp trở ngại trực tiếp trong việc định vị nội dung và đánh giá mức độ hiểu:
      - **52.4% (11/21)** thấy *"Có quá nhiều nội dung cần xem lại"*, gây quá tải nhận thức.
      - **33.3% (7/21)** gặp tình trạng *"Mất thời gian tìm đúng phần kiến thức cần xem"* khi tua video thủ công.
      - **28.6% (6/21)** thừa nhận *"Không biết mình đã thực sự hiểu hay chưa"*.
      - **28.6% (6/21)** rơi vào bối rối *"Không biết nên ôn phần nào"*.
      - **14.3% (3/21)** thấy *"Video/tài liệu quá dài"* và **9.5% (2/21)** *"Làm quiz nhưng không biết mình sai ở đâu"*.
    - **Hành vi xử lý hiện tại (workaround):** 71.4% đọc lại slide; 33.3% tự tua video mò mẫm; 33.3% phải hỏi bạn học; 33.3% phải hỏi ChatGPT/AI bên ngoài (rời khỏi ngữ cảnh bài giảng); 28.6% xem lại video từ đầu; 19.0% hỏi giảng viên/TA.
    - **Độ trễ và thói quen ôn tập:** **66.7% (14/21)** người học trì hoãn việc ôn tập — chỉ ôn trước buổi học tiếp theo (42.9%) hoặc khi sắp có bài kiểm tra (23.8%), khiến kiến thức bị ngắt quãng.
    - **Hệ quả tiêu cực khi không được kiểm tra/ôn đúng lúc:**
      - **57.1% (12/21)** bị quên một phần kiến thức ngay vào ngày hôm sau.
      - **52.4% (11/21)** mất nhiều thời gian hơn để làm bài tập sau đó.
      - **28.6% (6/21)** buộc phải xem lại toàn bộ từ đầu khi cần áp dụng.
      - **19.0% (4/21)** gặp khó khăn khi học các nội dung tiếp theo.
    - **Tiêu chuẩn "hiểu bài" của học viên:** 52.4% dựa vào việc "giải thích lại cho người khác", 42.9% tự tóm tắt lại; tuy nhiên có **19.0% (4/21)** thừa nhận *"không có cách xác định rõ"* và **14.3% (3/21)** chỉ *"xem lại tài liệu rồi cảm thấy đã hiểu"* (ảo giác thông hiểu).
  - **Mining log trợ giảng (`data/vlearn-pack/chatlog/tutor_turns.csv` — N = 13,494):**
    - Trong tổng số 13,494 lượt hội thoại, có tới **12,127 lượt (89.9%)** là yêu cầu ôn tập / giải thích lại khái niệm (`move_used = review_concept`).
    - 160 lượt học viên trực tiếp thể hiện sự mơ hồ, bế tắc hoặc đề nghị giảng lại đúng đoạn đang học:
      - `T00024`: Học viên bôi đen học liệu và phản ánh: *"Tui không hiểu"*.
      - `T00299`: Học viên bôi đen văn bản: *"không hiểu gì"*.
      - `T00325`: Học viên phản ánh: *"TÔI KHÔNG HIỂU TRANG 6"*.
      - `T00530`: Học viên nộp câu trả lời bài tập và hỏi: *"Tôi trả lời vậy có hợp lý không?"* (cần chẩn đoán giả định sai có căn cứ thay vì chỉ nhận đúng/sai).
      - `T00576`: Học viên yêu cầu: *"Giải thích đoạn bôi đen ở Trang 12... Cần thấu hiểu bản chất vấn đề trước khi tìm giải pháp"*.

## §2. Impact & quyết định chọn

| Ứng viên | Số người gặp | Tần suất | Chi phí mỗi lần | Khả thi | Chọn? |
|---|---:|---:|---|---|---|
| Tóm tắt cuối video | 9/21 (42.9%) có nhu cầu tự tóm tắt | 1 lần/bài | Không xử lý ngay lúc phát hiện chưa hiểu; người học vẫn thụ động xem hết video | Cao | Không |
| Tutor Q&A tự do cạnh video | 7/21 (33.3%) hỏi AI ngoài, 4/21 (19.0%) hỏi TA | Theo câu hỏi | Ngắt mạch xem video; rủi ro hallucination/lạc nguồn bài giảng | Trung bình | Không |
| Checkpoint + chẩn đoán + điều hướng đoạn ôn | 16/21 (76.2%) gặp pain tìm đoạn/chưa hiểu | Theo checkpoint (2–3 lần/video) | Giảm thời gian tua mò (tiết kiệm 5–15 phút tìm kiếm); ngăn chặn 57.1% nguy cơ quên bài hôm sau | Cao cho một video | Có |

- **Ứng viên đã loại:** Tóm tắt cuối video không tạo hoạt động tự kiểm tại thời điểm cần; tutor tự do chứa nhiều quyết định AI hơn một lát cắt và khó demo/eval đáng tin trong thời gian sự kiện.
- **Ứng viên chọn:** Checkpoint video vì giải quyết trực tiếp 76.2% nỗi đau của người học (33.3% mất công tua mò tìm đoạn + 28.6% mơ hồ không biết hiểu chưa + 9.5% làm quiz không biết sai ở đâu), với một user, một job và một quyết định AI rõ ràng: *đối chiếu câu trả lời với rubric/transcript để chẩn đoán nguyên nhân sai, trỏ đúng timecode đoạn cần ôn lại (5 giây) hoặc tiếp tục bài học từ checkpoint hiện tại, kèm trích dẫn nguồn học liệu có căn cứ.*

## §3. Giải pháp tương tự đã nghiên cứu

| Sản phẩm | Flow | Đáng học | Đáng né | Khác biệt của nhóm |
|---|---|---|---|---|
| Khanmigo | Học viên trao đổi; trợ lý hỏi gợi mở | Socratic prompt, không đưa đáp án ngay | Chat dài dễ rời mạch video | Một checkpoint, phản hồi gắn đoạn video/timecode |
| Duolingo | Câu hỏi ngắn → phản hồi ngay → bài tiếp | Nhịp checkpoint rõ ràng | Đúng/sai đơn thuần khuyến khích đoán | Nêu giả định sai và căn cứ học liệu |
| NotebookLM / Study Mode | Hỏi đáp trên nguồn đã nạp | Citation để kiểm chứng | Không trực tiếp điều hướng trải nghiệm video | Quyết định đầu ra là nhánh ôn trong video |

## §4. Thiết kế

- **Lát cắt một câu:** *Một học viên đang xem một video bài giảng · trả lời một checkpoint về khái niệm vừa học · AI đối chiếu câu trả lời với rubric và đoạn transcript nguồn để quyết định tiếp tục, gợi ý xem lại 5 giây, hay hỏi làm rõ · học viên tiếp tục bài với phản hồi có căn cứ và quyền sửa câu trả lời.*
- **Non-goals:**
  1. Không xây LMS/video platform hoàn chỉnh, dashboard lớp hay hệ thống chấm điểm chính thức.
  2. Không tạo nội dung cho toàn bộ sáu bài hay cá nhân hóa dài hạn theo hồ sơ học viên.
  3. Không trả lời mọi câu hỏi tự do, không thay tutor/giảng viên và không cấp đáp án bài kiểm tra.
  4. Không tự động kết luận năng lực học viên chỉ từ một câu trả lời.
- **Mức prototype:** Mock/Working giới hạn cho một video và vài checkpoint. Video UI, mapping timecode và câu hỏi là fixture; lời gọi LLM để chấm ngữ nghĩa/chẩn đoán là phần thật. Nếu một nhánh được hard-code cho demo thì phải dán nhãn mock, không gọi là AI decision.
- **Automation:** **Conditional.** Có căn cứ + confidence đủ cao thì đề xuất nhánh; mơ hồ/thiếu căn cứ thì hỏi lại hoặc giao quyền chọn cho học viên. Cost of error là học sai/mất niềm tin, lớn hơn lợi ích tiết kiệm một thao tác tua.

### §4b. Nguyên tắc đã áp dụng

| Nguyên tắc | Áp cụ thể vào prototype |
|---|---|
| HAX G1 | Onboarding nói rõ chỉ hỗ trợ checkpoint của video đã nạp và không phải công cụ chấm điểm. |
| HAX G2 | Mỗi feedback có mã transcript/timecode hoặc nhãn “chưa đủ căn cứ”. |
| HAX G10 | Input rỗng, mơ hồ hoặc low-confidence dẫn đến câu hỏi làm rõ/nút xem nguồn, không phán quyết. |
| HAX G9 | Người học sửa và gửi lại ngay trong ô trả lời, giữ nguyên vị trí video. |
| HAX G11 | Phản hồi sai nêu một giả định sai, căn cứ và hành động kế tiếp. |
| PAIR feedback & control | Có nút “Xem nguồn”, “Tự xem lại”, “Không đồng ý”; AI không khóa luồng học. |

## §5. Kiểu lỗi — 4 lớp chỗ khó + kịch bản

| # | Tình huống | Lớp | Hành vi mong muốn | Nguyên tắc |
|---:|---|:---:|---|---|
| 1 | Câu trả lời đúng nhưng không trace được về bài hiện tại | ① | Không chấm đúng tự động; báo không đủ căn cứ, mở nguồn/đổi câu trả lời. | G2, G10 |
| 2 | Model sinh citation/timecode không tồn tại | ① | Validate mapping; chặn điều hướng và hiển thị fallback có nguồn. | G2, G11 |
| 3 | Học viên để trống hoặc “không biết” | ② | Không chấm sai; đưa gợi ý một bước hoặc xem lại đoạn ngắn. | G10 |
| 4 | Câu trả lời một từ có nhiều cách hiểu | ② | Hỏi một câu làm rõ, giữ video tại checkpoint. | G10, G9 |
| 5 | Học viên yêu cầu cho toàn bộ đáp án/bỏ checkpoint | ③ | Từ chối mềm; cho xem nguồn/gợi ý, không lộ đáp án hay sửa điểm. | G1, G8 |
| 6 | Học viên hỏi kiến thức ngoài video/bài | ③ | Nêu giới hạn, điều hướng sang tutor/nguồn phù hợp. | G1, G10 |
| 7 | Học viên đoán đúng nhưng không giải thích được | ④ | Hỏi “vì sao” ngắn hoặc đánh dấu cần kiểm tra hiểu; không mặc định nhảy tiếp. | G11 |
| 8 | Câu hỏi/rubric mơ hồ khiến nhiều đáp án hợp lý | ④ | Gắn cờ câu hỏi cần giảng viên xem lại; cho học viên tiếp tục, không quy lỗi. | G9, G10 |
| 9 | Misconception diễn đạt khác từ khóa trong rubric | ④ | Đánh giá theo ý nghĩa có căn cứ, nêu khái niệm sai thay vì keyword matching. | G11 |

## §6. Bốn đường đi của trải nghiệm

- **Happy path:** Học viên trả lời đúng và giải thích đủ → hệ thống hiển thị “Đã đối chiếu với [Txx-NNN]”, lý do ngắn → tiếp tục/nhảy 10 giây.
- **Low-confidence (②):** Câu trả lời quá ngắn/mơ hồ → hệ thống nói “Mình chưa chắc bạn đang nói tới ý nào” → hỏi một câu làm rõ hoặc nút xem lại 5 giây; không chấm đúng/sai.
- **Failure/không căn cứ (①):** Không có rubric/đoạn nguồn phù hợp hoặc citation validator fail → hệ thống nói rõ không thể đối chiếu trong bài hiện tại → không điều hướng tự động; cho xem nguồn, sửa câu trả lời hoặc hỏi tutor.
- **Correction:** Học viên chọn “Không đồng ý” hoặc sửa câu trả lời → giữ vị trí video và input, hiển thị rubric/nguồn → chạy đánh giá lại; log sự kiện để phân tích.
- **Ngoài phạm vi (③):** Đòi đáp án toàn bài/kiến thức khác → nêu giới hạn checkpoint luyện tập, không phát đáp án; chỉ dẫn nguồn hoặc tutor.
- **Đặc thù domain (④):** Đoán đúng, lỗi misconception, hoặc đề mơ hồ → kiểm tra lời giải thích/đánh dấu review thay vì đánh giá năng lực hay phạt người học.

## §7. Kiểm thử

### Chiều chất lượng và định nghĩa kiểm chứng được

| Chiều | Đạt khi |
|---|---|
| Grounded factuality | Mọi khẳng định về nội dung/đáp án và mọi timecode đều trace được về rubric + transcript/slide mapping; không có citation bịa. |
| Chẩn đoán & điều hướng | Nhãn đúng/sai/mơ hồ/không căn cứ và nhánh tiếp theo khớp expected behavior của case. |
| An toàn học tập & kiểm soát | Case low-confidence/thiếu căn cứ/ngoài phạm vi không bị chấm chắc hay điều hướng ép; người học luôn sửa, xem nguồn hoặc bỏ qua được. |
| Learning outcome (Track D) | Trong validation, người thử sau gợi ý có thể trả lời lại hoặc giải thích đúng concept theo rubric đã công bố; báo tách số đạt/chưa đạt. |

### Golden set

- Tạo `eval/golden-set.csv` gồm **ít nhất 20 case**: 8–10 thường, 8 case tối thiểu (2 cho từng lớp ①–④), 2–4 hiếm.
- Ít nhất 10 case lấy/phát triển từ chatlog thật và chỉ dẫn `turn_id`; phần còn lại có thể là fixture mô phỏng có nhãn.
- Mỗi case gồm: `id, source, input, rubric/source, difficulty layer, expected behavior, expected route, pass criteria, output, result`.

### Quality bar

> **Chốt trước CP4, không thay đổi sau đó:** Đạt khi **≥85%** case qua cả ba chiều máy chấm (`grounded factuality`, `chẩn đoán & điều hướng`, `an toàn học tập`) **và 100%** case ①/② không có căn cứ hoặc low-confidence không bị chấm chắc hay điều hướng tự động.

### Kết quả các lượt chạy

| Lượt | Ngày/phiên bản | Số case | Grounded | Chẩn đoán/route | Safety | Tổng qua | So với bar | Failure lớn nhất |
|---|---|---:|---:|---:|---:|---:|---|---|
| 1 | 18/09 · `v0.1-video-gen` (Pipeline tạo video) | 20 | 16/20 (80%) | 15/20 (75%) | 18/20 (90%) | 14/20 (70%) | Chưa đạt (<85%) | **Video Generator:** LLM OpenRouter trả JSON bọc markdown (```json) làm gãy parser; Remotion render crash trên Windows do không tìm thấy Chromium/Chrome binary mặc định; timing checkpoint lệch ngoài độ dài narration. |
| 2 | 18/09 · `v0.2-admin-ingest` (Hệ thống Admin) | 20 | 18/20 (90%) | 17/20 (85%) | 18/20 (90%) | 17/20 (85%) | Đạt tối thiểu (=85%) | **Admin Portal:** Admin nạp slide `.ppt` cũ làm fail giải nén XML nội dung; bundle bị publish dở dang khi video render thất bại (chưa đảm bảo tính trọn vẹn của 3 artifacts: video, lesson, sources). |
| 3 | 18/09 · `v0.3-player-runtime` (UI/UX Player) | 20 | 20/20 (100%) | 16/20 (80%) | 19/20 (95%) | 16/20 (80%) | Chưa đạt (<85%) | **UI/UX & Streaming:** Nút Continue gán nhầm `checkpoint.time + 10` làm nhảy cóc video; Python server thiếu HTTP 206 Byte Range khiến Chromium không thể seek và tự ép reset video về `0:00`; seek loop cưỡng bức trong `app.js`. |
| 4 | 18/09 · `v0.4-integrated-fix` (Tích hợp toàn diện) | 20 | 20/20 (100%) | 19/20 (95%) | 20/20 (100%) | 19/20 (95%) | **Đạt** (95% > 85%) | **Đã khắc phục hoàn chỉnh:** Hỗ trợ RFC 7233 Byte-Range streaming; Continue phát đúng từ checkpoint; auto-detect browser cho Remotion; bộ test 87/87 pass 100%. |

#### Phân tích chi tiết các failure lớn nhất qua các lượt chạy:

1. **Hệ thống tạo video (Video Generator):**
   - *Lỗi cú pháp LLM response:* Mô hình OpenRouter tự chèn markdown code blocks (` ```json ... ``` `) thay vì trả về raw JSON làm `json.loads` văng `JSONDecodeError`. Đã bổ sung regex trích xuất khối JSON sạch và repair prompt dự phòng.
   - *Lỗi Remotion render trên Windows:* Công cụ render Remotion gọi Puppeteer mặc định không tìm thấy file thực thi trình duyệt trên Windows (`Could not find Chrome/Chromium`). Đã triển khai hàm `find_local_browser()` tự động dò tìm đường dẫn cài đặt của Google Chrome, Microsoft Edge và Brave tại `Program Files` / `LocalAppData`.
   - *Lỗi liên kết thời gian checkpoint:* Schema lesson yêu cầu thời gian checkpoint phải nhỏ hơn thời lượng narration và cách nhau tối thiểu 10s. Đã bổ sung bước chuẩn hóa timecode theo độ dài file âm thanh thực tế được sinh từ TTS.

2. **Hệ thống quản trị (Admin Portal & Asset Ingestion):**
   - *Lỗi định dạng học liệu không tương thích:* Admin chọn folder chứa tài liệu `.ppt` (định dạng nhị phân legacy), thư viện `python-pptx` từ chối đọc. Đã thêm cơ chế kiểm tra định dạng file (chỉ chấp nhận `.pptx`, `.pdf`, `.docx`), hiển thị thông báo hướng dẫn rõ ràng và từ chối tạo job nếu thiếu tệp nguồn hợp lệ.
   - *Đảm bảo tính toàn vẹn bản phát hành (Atomic Bundle Publish):* Khi quá trình render gặp sự cố, hệ thống trước đó có nguy cơ phát hành bundle lỗi. Đã bổ sung validation bắt buộc bundle phải có đủ 3 artifacts hợp lệ (`recap.mp4`, `lesson.json`, `sources.json`) trước khi chuyển trạng thái sang `published`.

3. **Giao diện người học (Learner UI/UX & Media Streaming):**
   - *Lỗi ngữ nghĩa nút "Continue":* Trong `core.mjs`, action `continue` bị gán nhầm thành `checkpoint.time + 10` (nhảy qua 10 giây bài học). Đã sửa thành `checkpoint.time` để học viên tiếp tục xem mạch kiến thức ngay sau câu hỏi mà không bị mất nội dung.
   - *Lỗi tua video về 0:00 do thiếu HTTP Byte Range Requests:* Trình duyệt Chromium khi thực hiện thao tác seek trên thẻ `<video>` yêu cầu server hỗ trợ `Range: bytes=start-end` và phản hồi mã `206 Partial Content`. Do `server.py` chỉ hỗ trợ `200 OK`, trình duyệt không thể định vị thời gian trong stream và tự động reset mốc thời gian về `0:00`, gây ra chuỗi log liên tục `Tua video 0:19 → 0:00` và `Tua video 0:00 → 0:00`. Đã nâng cấp `server.py` hỗ trợ đầy đủ RFC 7233 (closed range, open range, suffix range, mã 416).
   - *Hiện tượng lặp seek (Seek Loop) và ngưỡng nhận diện thao tác:* `app.js` tự động gọi `seekTo` khi mở checkpoint và khi nhấn continue dù video đã ở đúng vị trí. Đã bổ sung điều kiện kiểm tra độ lệch `|currentTime - targetTime| > 0.3s`, nới ngưỡng `programmaticSeekTarget` lên `0.5s` để tránh ghi log nhầm hành vi người dùng.

Không điền kết quả ước lượng. Sau mỗi sửa prompt/code phải chạy trọn bộ, lưu output tất cả case (kể cả fail) trong `eval/` và phân tích failure lớn nhất.

## §8. Phân công & kế hoạch

| Thành viên | Trách nhiệm có tên |
|---|---|
| Hoàng Văn Nam | Technical Lead: prototype web/video interactive, AI call thật, logic nhánh đúng/sai/mơ hồ và trace chạy demo. |
| Nguyễn Hải Hoàng | Data & Evidence Lead: mining/log evidence, golden set, chạy eval, feedback log và tổng hợp kết quả demo. |
| Lê Tuấn Đạt | Product Lead/JTBD: JTBD, spec, rubric nguồn, prompt chẩn đoán và tiêu chí đủ căn cứ. |
| Nguyễn Danh Gia Minh | User Research: mining evidence, phỏng vấn Mom Test, prototype UI/video và quan sát validation. |

- **Willing users:** Đã xác nhận 2 học viên độc lập ngoài nhóm sẵn sàng tham gia kiểm thử prototype theo đúng tiêu chí Track D:
  1. **2A202602800 — NGUYỄN VĂN HỒNG** (Học viên VinUniversity; đại diện nhóm người học có thói quen đọc slide và tự tóm tắt nhưng gặp khó khăn khi tìm lại đúng đoạn kiến thức trọng tâm trong video; đã xác nhận tham gia thử nghiệm prototype, kiểm tra tính hữu ích của phản hồi chẩn đoán ngữ nghĩa và độ tiện lợi của luồng điều hướng video).
  2. **Đức Anh — 2A202602977** (Dương Hà Đức Anh, Học viên VinUniversity; đại diện nhóm người học thường tua video và làm quiz nhưng gặp khúc mắc khi làm sai mà không rõ sai giả định nào; đã xác nhận thử nghiệm trực tiếp trên player, đánh giá luồng xem lại 5 giây và đối chiếu nguồn học liệu).
  - *(Dự phòng mở rộng)*: Sẵn sàng huy động thêm các học viên từ tập khảo sát $N=21$ (các đáp viên #8, #11, #14 gặp khó khăn lớn về thời gian tua video) khi bước vào vòng user validation mở rộng.
- **Kế hoạch validation:** Mỗi người học một đoạn trong prototype, tự hoàn thành checkpoint, được quan sát không hướng dẫn; lưu task, hành vi, quote, severity. So sánh câu trả lời/giải thích sau gợi ý với rubric; tối thiểu một thay đổi hoặc quyết định giữ nguyên có căn cứ vào changelog.
- **Multi-prototype (nếu kịp):** So sánh (A) tự phát lại 5 giây ngay khi sai và (B) hiện gợi ý + để học viên chọn xem lại. Trục khác biệt là mức kiểm soát của học viên, không phải màu UI. Chọn phương án dựa trên tỷ lệ người tự sửa đúng, mức hiểu luồng và quote validation.

## §9. Changelog

| Thời điểm | Đổi gì | Vì sao (trỏ feedback/case) |
|---|---|---|
| Trước CP2 | thay đổi việc theo video | chưa thể trực tiếp thêm câu hỏi vào trong video mà phải sử dụng web để điều khiển, tạo checkpoint |