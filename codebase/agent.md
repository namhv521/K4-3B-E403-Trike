# Hướng dẫn Agent — VLearn Interactive Learning Video

> Đọc tài liệu này trước khi phân tích, sửa, sinh mã, tạo nội dung, chạy agent, hoặc đề xuất kiến trúc trong `C:\Su\VinLab\Hackathon\codebase`.

## 1. Mục tiêu không được lệch

Xây một trải nghiệm **video học tập tương tác có thể tích hợp vào website chính thức VLearn**. Người học xem một video tổng hợp kiến thức từ bài học, gặp checkpoint ngay tại thời điểm nội dung liên quan, phản hồi, nhận dẫn giải có căn cứ và chủ động tiếp tục hoặc xem lại đúng đoạn cần ôn.

Trải nghiệm được lấy cảm hứng từ nhịp tương tác chính xác của video trò chơi (dừng đúng khoảnh khắc, chọn phương án, phản hồi rồi phân nhánh), **nhưng tuyệt đối là học tập, không biến thành trò chơi hoặc đánh giá năng lực chính thức**.

Một lát cắt phải luôn diễn đạt được trong một câu:

> Một học viên đang xem một video bài giảng, trả lời một checkpoint về khái niệm vừa học; hệ thống đối chiếu câu trả lời với rubric và transcript đã nạp để đưa phản hồi có căn cứ, rồi học viên chọn tiếp tục hoặc xem lại đoạn liên quan.

### Kết quả cần phục vụ

1. **Website tích hợp:** thành phần video có thể được nhúng vào trang bài học chính thức; không thiết kế một sản phẩm độc lập, xa rời luồng học hiện có.
2. **Video tổng hợp kiến thức:** video và checkpoint chỉ được sinh từ học liệu đã được cấp quyền/dữ liệu fixture; nội dung có truy vết về nguồn.
3. **Tương tác theo mốc thời gian chính xác:** checkpoint dừng ở timecode đã khai báo và chỉ phát lại/seek theo timecode xác định; không suy luận vị trí từ số frame không ổn định.
4. **Logging có ích và tối thiểu:** ghi event để phân tích luồng học, điểm kẹt và hiệu quả gợi ý; không thu thập bí mật, dữ liệu nhạy cảm, hoặc toàn bộ nội dung nguồn.
5. **Học viên giữ quyền kiểm soát:** luôn có đường tiếp tục, tự xem lại, sửa câu trả lời, xem nguồn hoặc bỏ qua phù hợp; AI không khóa việc học.

## 2. Phạm vi hiện tại và các giới hạn bắt buộc

### In scope

- Một video/bài học ngắn (mục tiêu hiện tại 60–90 giây) và một số checkpoint minh họa.
- Video recap có narration, cảnh, timecode, câu hỏi, đáp án, misconception và explanation.
- Checkpoint dừng video, thu nhận câu trả lời, hiện phản hồi, rồi điều hướng có kiểm soát.
- Sinh video từ tài liệu học tập, có kiểm tra schema trước khi phát.
- Logging cục bộ hoặc API logging đã được phê duyệt, theo contract allowlist.
- Một lời gọi AI thật cho phần tổng hợp/chẩn đoán nếu prototype yêu cầu; mọi nhánh hard-code phải được gắn nhãn `mock`.
- Đóng gói desktop Windows **như một runtime độc lập tùy chọn** cho demo/offline, nếu vẫn cần.

### Không được tự ý mở rộng thành

- LMS hoàn chỉnh, dashboard lớp, leaderboard công khai, hệ thống chấm điểm chính thức hoặc hồ sơ năng lực dài hạn.
- Tutor chat tự do trả lời mọi kiến thức, tự cấp đáp án bài kiểm tra, hoặc thay thế giảng viên.
- Cá nhân hóa sâu dựa trên lịch sử người học khi chưa có yêu cầu, consent, chính sách lưu giữ và kiểm soát truy cập.
- Nội dung cho toàn bộ khóa học trước khi một video và một flow checkpoint đã được kiểm chứng với người học.
- Cơ chế game hóa làm người học bị áp lực, bị phạt hoặc bị công khai lỗi cá nhân.

Khi một yêu cầu mới vượt phạm vi trên, agent phải nêu rõ trade-off, giữ prototype nhỏ, và đề xuất lát cắt kế tiếp thay vì âm thầm mở rộng.

## 3. Quy tắc tuyệt đối về `.exe`, video và phân phối

**Không bao giờ ngụy trang, nhúng, đổi đuôi, steganography, tải xuống, hoặc phục vụ tệp thực thi `.exe` như thể đó là video.** Hành vi đó gây nguy hiểm cho người dùng, bị trình duyệt/hệ điều hành chặn và không phù hợp để tích hợp website.

Phân biệt đúng hai khái niệm:

- `recap.mp4` là nội dung media không tương tác và được phát bằng trình phát web/desktop.
- `interactive-recap.exe` (nếu được build) là ứng dụng Windows riêng, nhận bàn phím, chạy logic tương tác và ghi log cục bộ. Nó **không phải video**.

Nếu cần phân phối ứng dụng desktop, agent chỉ được làm theo cách minh bạch: nút tải xuống ghi rõ tên file, định dạng, nền tảng Windows, kích thước, phiên bản, checksum/chữ ký nếu có và thông báo bảo mật. Không tự động tải/chạy file, không đặt file thực thi trong thẻ `<video>`, iframe hay URL giả dạng media.

Để có tương tác trên website, dùng HTML5 video/web player và logic web an toàn. Để demo offline, giữ EXE như lựa chọn tách biệt, có tài liệu cài/chạy riêng.

## 4. Nguồn sự thật và an toàn học tập

### Grounding trước khi phản hồi

Mọi khẳng định về kiến thức, đáp án, misconception, citation và timecode phải trace được về ít nhất một trong các nguồn đã duyệt:

- transcript/slide/học liệu của bài hiện tại;
- rubric checkpoint;
- mapping scene/timecode trong `lesson.json`.

Không bịa citation, ID transcript, timestamp hoặc nội dung bài học. Không tìm được căn cứ hoặc validator mapping thất bại thì phải trả về trạng thái `unsupported`/`needs_review`, nói rõ giới hạn và **không tự động seek**.

### Hành vi theo tình huống

| Tình huống | Hành vi bắt buộc |
|---|---|
| Câu trả lời đúng, đủ căn cứ | Nêu lý do ngắn + nguồn/timecode; đề xuất tiếp tục hoặc nhảy theo rule đã công bố. |
| Trả lời sai, xác định được misconception | Nêu một giả định sai, dẫn giải ngắn có nguồn, cho học viên chọn xem lại đoạn liên quan hoặc tự sửa. |
| Rỗng, quá ngắn, mơ hồ hoặc confidence thấp | Không chấm đúng/sai; hỏi một câu làm rõ hoặc cho xem lại đoạn ngắn. |
| Không có nguồn/citation invalid | Không khẳng định; không điều hướng tự động; hiện nguồn, cho sửa hoặc hướng đến tutor/giảng viên. |
| Đòi toàn bộ đáp án, bỏ checkpoint, hỏi ngoài bài | Từ chối mềm, nêu giới hạn của bài luyện tập, chỉ dẫn nguồn/tutor phù hợp. |
| Câu hỏi/rubric mơ hồ hoặc nhiều đáp án hợp lý | Cờ `needs_content_review`; cho học viên tiếp tục, không đổ lỗi hoặc trừ điểm. |
| Đoán đúng nhưng không cho thấy hiểu | Hỏi “vì sao” ngắn hoặc đánh dấu cần kiểm tra hiểu; không tự kết luận đã nắm vững. |

Phản hồi phải tôn trọng, không làm xấu hổ người học. Đây là công cụ luyện tập, không phải thi hay phán quyết năng lực.

## 5. Contract nội dung và “frame-perfect” theo timecode

### Nguồn bundle hiện hữu

`video-generator` tạo bundle tại `C:\Su\VinLab\Hackathon\codebase\video-generator\output`:

- `recap.mp4`
- `narration.mp3`
- `lesson.json`
- `transcript.txt`
- `sources.json`
- `ai-trace.json`

`interactive-video-player` hiện tiêu thụ bản sao của `recap.mp4`, `narration.mp3`, `lesson.json` trong `assets/`. Agent phải giữ đồng bộ contract schema giữa generator, web integration và desktop player; thay đổi schema ở một phía phải cập nhật validator, consumer và test ở các phía liên quan.

### Nguyên tắc timing

- Dùng `checkpoint.time` tính bằng giây làm nguồn sự thật. Kiểm tra checkpoint nằm trong `0 < time < duration_seconds` và cách nhau hơn 10 giây theo validator hiện có.
- Với web, dùng `HTMLVideoElement.currentTime`, các event `timeupdate`/`seeking` và một guard idempotent cho checkpoint đã mở. Nếu cần độ chính xác cao hơn, dùng `requestVideoFrameCallback` khi trình duyệt hỗ trợ, nhưng luôn có fallback dựa trên timecode.
- Với desktop, monotonic clock là playback authority; seek phải đồng bộ video, audio và clock anchor.
- Khi checkpoint được kích hoạt: pause/freeze tại mốc khai báo, render overlay, ngăn phát qua checkpoint khi chưa có action hợp lệ.
- Không dùng “số frame” làm contract giữa các runtime; frame rate, decode, buffering và browser khác nhau có thể làm lệch. Nếu sản phẩm cần frame-exact video thật sự, lưu metadata `fps`, quy đổi frame ↔ timecode rõ ràng và kiểm thử trên media đã encode cố định.
- Không hard-code timestamp, lựa chọn, answer key hay route ở UI. Đọc từ lesson manifest đã validate.

### Luồng mặc định của prototype desktop hiện hữu

- Chọn đúng: hoàn thành checkpoint và seek về trước đúng 10 giây.
- Chọn sai: chỉ mất điểm ở lần thử đầu, hiển thị giải thích đúng 5 giây, sau đó người học chọn phát lại từ đầu (`0`) hoặc tới checkpoint tiếp (`1`).
- Mọi lần thử sau vẫn được log, nhưng không khôi phục điểm lần đầu.

Nếu website áp dụng điều hướng khác (ví dụ “gợi ý xem lại 5 giây”), agent phải ghi rõ đây là rule web mới, cập nhật spec/test/telemetry, không gọi sai là cùng hành vi với desktop.

## 6. Kiến trúc hiện có và hướng tích hợp website

### Thành phần hiện tại

- `interactive-video-player/`: Python 3.10+, `pygame`, OpenCV, PyInstaller. Đây là player fullscreen/offline; `engine.py` chứa state transition; `player.py` là adapter UI/media; `logger.py` ghi JSONL allowlist.
- `video-generator/`: pipeline Python sinh nội dung, narration và video. Chỉ dùng dependency có trong `requirements.txt` trừ khi có lý do rõ ràng, dependency được khai báo và test.

Tài liệu cũ của desktop player nói “replace website”. Đó là quyết định prototype cũ, **không được hiểu là xóa mục tiêu website tích hợp hiện tại**. Khi xây web integration:

1. Không xóa hoặc phá desktop demo chỉ vì thêm web; tái sử dụng `lesson.json` và logic state đã kiểm thử khi phù hợp.
2. Khảo sát ứng dụng VLearn chính thức, auth, frontend stack, API convention, deployment và cách nhúng component trước khi chọn framework hay sửa code.
3. Không tự thêm React/Next.js/backend/cloud database chỉ vì thuận tiện. Chỉ dùng stack đã xác nhận ở host; mọi dependency mới phải có lý do, lockfile, kiểm thử và review bảo mật.
4. Tách rõ: media rendering, state machine/checkpoint, content validation, UI overlay, AI diagnosis và transport logging. Business rule không thuộc riêng UI.
5. Ưu tiên một API/adapter logging và content manifest versioned để desktop và web có thể cùng dùng contract, thay vì sao chép logic lặng lẽ.

## 7. Logging, dữ liệu và riêng tư

Mục tiêu logging là trả lời: người học gặp checkpoint nào, chọn gì, có cần xem lại không, misconception nào lặp lại, và sau gợi ý có tự sửa/giải thích tốt hơn không.

### Allowlist event tối thiểu

Giữ tương thích với `interactive-video-player/logger.py` khi có thể:

```text
session_id, timestamp, event, video_time, checkpoint_id, attempt_number,
selected_answer, is_correct, misconception_id, misconception_label,
action_after_feedback, response_time_ms, score
```

- Event phải có `session_id`, `timestamp`, `event` hợp lệ.
- JSONL hiện hữu là append-only UTF-8 và loại bỏ field ngoài allowlist. Không nới allowlist để log “cho tiện” mà không có mục đích phân tích cụ thể.
- Không log API key, authorization header, cookie/token, prompt bí mật, full transcript, full câu trả lời tự do, dữ liệu nhận dạng trực tiếp, hoặc nội dung học liệu không cần thiết.
- Nếu website gửi event về server: xác thực/ủy quyền phiên, validate schema ở server, rate limit, dùng HTTPS, chỉ cho origin cần thiết, và tách định danh người dùng khỏi telemetry khi có thể.
- Đặt retention policy, thông báo mục đích thu thập và cơ chế consent theo chính sách VLearn trước khi dùng dữ liệu người học thật.

Data trong `C:\Su\VinLab\Hackathon\data` chỉ được dùng trong phạm vi hackathon. Không commit data pack, không public, không cố suy ngược danh tính, không upload cả pack lên công cụ bên ngoài. Chỉ trích dẫn tối thiểu theo quy định dự án.

## 8. Quy trình làm việc bắt buộc cho agent

1. **Đọc ngữ cảnh trước:** kiểm tra `README.md`, `spec-answers.md`, tài liệu module liên quan, schema, tests và git status. Không ghi đè thay đổi chưa commit của người khác.
2. **Nêu lát cắt:** xác nhận user, job, quyết định AI, kết quả; nếu không còn là một câu rõ ràng thì thu nhỏ yêu cầu.
3. **Lập kế hoạch ngắn:** liệt kê file dự kiến, thay đổi contract, rủi ro grounding/timing/privacy và cách kiểm thử.
4. **Thay đổi nhỏ, tương thích:** giữ naming, type/style, Python `unittest`, dependency và cấu trúc của module hiện có. Không refactor rộng không liên quan.
5. **Validate ở biên:** validate lesson manifest, file media, input người dùng, event logging và output AI trước khi dùng/chuyển tiếp.
6. **Test thật:** chạy test module bị tác động và regression suite phù hợp. Với generator/player hiện tại dùng:

   ```powershell
   python -m unittest discover -s tests -v
   ```

   Với web integration, chạy test/lint/build theo script thực tế của ứng dụng host, không bịa lệnh.
7. **Smoke test luồng học:** tối thiểu kiểm tra một câu trả lời đúng, sai, rỗng/mơ hồ, citation fail/không căn cứ, sửa câu trả lời, event log và restart/seek. Xác nhận timecode/route đúng.
8. **Báo cáo trung thực:** nói rõ thay đổi, test đã chạy, kết quả, giới hạn và phần nào mock. Không nói AI decision là thật nếu branch được hard-code.

## 9. Quality bar và validation

Giữ quality bar của prototype hiện tại cho đến khi team chốt lại bằng evidence:

- Ít nhất **85%** golden set qua cả grounded factuality, diagnosis/route và safety.
- **100%** case thiếu căn cứ hoặc low-confidence không bị chấm chắc hoặc bị điều hướng tự động.
- Golden set có ít nhất 20 case, bao phủ nguồn sự thật, mơ hồ, ngoài phạm vi và rủi ro domain; lưu cả output fail và phân tích failure lớn nhất.
- Track học tập cần validation với ít nhất 5 người học ngoài nhóm thực sự hoàn thành một đoạn học; đo kết quả học (trả lời/sự giải thích sau gợi ý), không chỉ đo UI hoặc số lần click.

Mọi metric, quote, người dùng willing-to-test và kết quả chạy phải là thật hoặc gắn nhãn fixture/mock. Không điền số liệu ước lượng.

## 10. Checklist trước khi hoàn tất một thay đổi

- [ ] Vẫn phục vụ website video học tập tương tác, không trôi sang game/LMS/tutor tổng quát.
- [ ] Nội dung, answer key, explanation và timecode có nguồn/rubric/mapping kiểm tra được.
- [ ] Low-confidence, unsupported và ngoài phạm vi có fallback an toàn; người học còn quyền chọn.
- [ ] Không có `.exe` bị ngụy trang thành video hoặc tự động tải/chạy từ web.
- [ ] Không có secret, full source content hoặc dữ liệu nhạy cảm trong log/repo/output.
- [ ] Schema, generator, desktop player và web consumer liên quan đã được cập nhật đồng bộ hoặc compatibility được ghi rõ.
- [ ] Test phù hợp, manifest validation và smoke test checkpoint đã chạy thành công.
- [ ] Tài liệu nêu đúng trạng thái: working, mock hay future work.

## 11. Tài liệu cần ưu tiên đọc

- `C:\Su\VinLab\Hackathon\spec-answers.md` — product scope, error taxonomy, experience paths và quality bar.
- `C:\Su\VinLab\Hackathon\tracks\track-d-adaptive-interactive-learning.md` — mục tiêu Track D và an toàn học tập.
- `C:\Su\VinLab\Hackathon\codebase\interactive-video-player\DESIGN.md` — runtime desktop, timing và log hiện hữu.
- `C:\Su\VinLab\Hackathon\codebase\interactive-video-player\lesson_schema.py` — lesson manifest contract.
- `C:\Su\VinLab\Hackathon\codebase\video-generator\README.md` — pipeline tạo bundle, đầu vào/đầu ra và cách test.

Nếu các tài liệu mâu thuẫn, ưu tiên theo thứ tự: yêu cầu mới được người dùng xác nhận → bảo mật/an toàn người học → `spec-answers.md` đã chốt → contract và tests thực thi → tài liệu cũ. Agent phải ghi rõ mâu thuẫn và cách xử lý, không lặng lẽ chọn một hướng.