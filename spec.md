```markdown
# AI SPEC — [Tên lát cắt] · Nhóm [XX] · Zone [X]
Hướng: [ ] A — VLearn  [ ] B — Trợ lý Học viên  [ ] C — Làn mở
Loại: [ ] Tối ưu tính năng có sẵn  [ ] Tính năng mới

## §1. User & Job
- Job executor + workflow (đính kèm worksheet JTBD / ảnh sơ đồ):
- Core JTBD (không tên sản phẩm/AI trong câu):
- Problem statement (KHÔNG chữ AI):
- Evidence (chuẩn A và/hoặc B — log đầy đủ trong repo):
  - Số liệu mining / kết quả khảo sát (n = ?, % xác nhận):
  - ≥5 quote/ví dụ nguyên văn + nguồn:

## §2. Impact & quyết định chọn
- Bảng impact ≥3 ứng viên (bao nhiêu người · tần suất · tốn gì mỗi lần · khả thi):
- Ứng viên ĐÃ LOẠI + vì sao:
- Ứng viên CHỌN + vì sao (bằng số):

## §3. Giải pháp tương tự đã nghiên cứu
- [Sản phẩm 1]: flow / đáng học / đáng né / mình khác gì
- [Sản phẩm 2]: ...

## §4. Thiết kế
- Lát cắt MỘT CÂU (1 user · 1 việc · 1 quyết định AI · 1 kết quả):
- Non-goals (≥3 thứ KHÔNG build):
- Mức prototype nhắm tới: [ ] Sketch [ ] Mock [ ] Working — phần nào mock, phần nào thật:
- Automation: [ ] augment [ ] conditional [ ] automate — lý do theo cost-of-error:
- §4b. Nguyên tắc đã áp dụng (≥4 — HAX/PAIR, xem guide):
  | Nguyên tắc | Áp cụ thể vào đâu trong prototype |
  |---|---|

## §5. Kiểu lỗi — 4 lớp chỗ khó + kịch bản (≥8) [bảng theo guide §2.5]

## §6. Bốn đường đi của trải nghiệm
- Happy path: · Low-confidence (②): · Failure/không căn cứ (①): · Correction (user sửa):
- Khi bị đòi ngoài phạm vi (③): · Case đặc t# AI SPEC — Checkpoint video thích ứng theo câu trả lời · Nhóm 02 · Zone E403

> **Trạng thái:** Bản trả lời để điền vào `spec.md`. Những mục ghi **CHƯA ĐO** phải được thay bằng evidence, tên willing user và kết quả chạy thật trước khi nộp. Không dùng số liệu hoặc quote bịa.

**Hướng:** D — Học tập thích ứng & tương tác trên VLearn  
**Loại:** Tính năng mới (một lát cắt theo khung D2)

## §1. User & Job

- **Job executor + workflow:** Học viên đang xem/ôn một đoạn video VLearn → gặp checkpoint → tự trả lời → nhận phản hồi có căn cứ → chọn sửa đáp án hoặc xem lại đúng đoạn → tiếp tục bài. Hiện tại học viên thường xem tuyến tính, tự tua mò hoặc hỏi tutor/ChatGPT riêng.
- **Core JTBD:** Tự kiểm tra mình có hiểu một khái niệm vừa xem hay không và quay lại đúng đoạn cần xem lại trước khi tiếp tục bài.
- **Problem statement:** Khi trả lời sai hoặc chưa chắc tại một checkpoint trong video, học viên không biết sai giả định nào và phải tự tua/đi tìm hỗ trợ để xác định đoạn cần ôn; việc này ngắt mạch học và có thể khiến họ tiếp tục với kiến thức chưa vững.
- **Evidence:**
  - **CHƯA ĐO:** Mining `data/vlearn-pack/chatlog/tutor_turns.csv` theo quy tắc đã ghi trong `02-guide-answers.md`; báo `n = [tổng lượt đã xét]`, `[x]/[n]` lượt có tín hiệu không hiểu/cần giải thích lại, kèm 5 `turn_id`.
  - **CHƯA ĐO:** Quan sát/phỏng vấn ít nhất 5 học viên ngoài nhóm theo ràng buộc Track D; ghi `n = [x]`, `[y]/[x]` gặp tình huống phải tua/tìm trợ giúp và quote nguyên văn.
  - Không dùng dữ liệu người học thật ngoài data pack; chỉ lưu mã lượt và trích dẫn ngắn theo quy định bảo mật.

## §2. Impact & quyết định chọn

| Ứng viên | Số người gặp | Tần suất | Chi phí mỗi lần | Khả thi | Chọn? |
|---|---:|---:|---|---|---|
| Tóm tắt cuối video | **CHƯA ĐO** | 1 lần/bài | Không xử lý ngay lúc phát hiện chưa hiểu | Cao | Không |
| Tutor Q&A tự do cạnh video | **CHƯA ĐO** | Theo câu hỏi | Ngắt mạch; có rủi ro lạc nguồn | Trung bình | Không |
| Checkpoint + chẩn đoán + điều hướng đoạn ôn | **CHƯA ĐO** | Theo checkpoint | Giảm tua mò/tìm hỗ trợ; cần kiểm chứng learning outcome | Cao cho một video | Có |

- **Ứng viên đã loại:** Tóm tắt cuối video không tạo hoạt động tự kiểm tại thời điểm cần; tutor tự do chứa nhiều quyết định AI hơn một lát cắt và khó demo/eval đáng tin trong thời gian sự kiện.
- **Ứng viên chọn:** Checkpoint video vì có một user, một job và một quyết định AI rõ ràng: *đủ căn cứ để chẩn đoán/điều hướng hay phải hỏi lại/từ chối*. Chỉ chốt lý do bằng số sau khi evidence hoàn tất.

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
| 1 | **CHƯA CHẠY** | 20 | — | — | — | — | — | — |

Không điền kết quả ước lượng. Sau mỗi sửa prompt/code phải chạy trọn bộ, lưu output tất cả case (kể cả fail) trong `eval/` và phân tích failure lớn nhất.

## §8. Phân công & kế hoạch

| Thành viên | Trách nhiệm có tên |
|---|---|
| Hoàng Văn Nam | Technical Lead: prototype web/video interactive, AI call thật, logic nhánh đúng/sai/mơ hồ và trace chạy demo. |
| Nguyễn Hải Hoàng | Data & Evidence Lead: mining/log evidence, golden set, chạy eval, feedback log và tổng hợp kết quả demo. |
| Lê Tuấn Đạt | Product Lead/JTBD: JTBD, spec, rubric nguồn, prompt chẩn đoán và tiêu chí đủ căn cứ. |
| Nguyễn Danh Gia Minh | User Research: mining evidence, phỏng vấn Mom Test, prototype UI/video và quan sát validation. |

- **Willing users:** **CHƯA CÓ TÊN.** Cần ghi ít nhất 5 học viên ngoài nhóm (Track D), trong đó các người đã đồng ý thử; không tự điền tên khi chưa có đồng ý.
- **Kế hoạch validation:** Mỗi người học một đoạn trong prototype, tự hoàn thành checkpoint, được quan sát không hướng dẫn; lưu task, hành vi, quote, severity. So sánh câu trả lời/giải thích sau gợi ý với rubric; tối thiểu một thay đổi hoặc quyết định giữ nguyên có căn cứ vào changelog.
- **Multi-prototype (nếu kịp):** So sánh (A) tự phát lại 5 giây ngay khi sai và (B) hiện gợi ý + để học viên chọn xem lại. Trục khác biệt là mức kiểm soát của học viên, không phải màu UI. Chọn phương án dựa trên tỷ lệ người tự sửa đúng, mức hiểu luồng và quote validation.

## §9. Changelog

| Thời điểm | Đổi gì | Vì sao (trỏ feedback/case) |
|---|---|---|
| Trước CP4 | Chưa có thay đổi đã được validation | Chỉ được bổ sung sau khi có log người thử hoặc failure trong golden set. |hù domain (④):

## §7. Kiểm thử
- Chiều chất lượng + định nghĩa kiểm chứng được:
- Golden set (≥20 case theo cơ cấu trong guide §2.6, file trong eval/):
- Quality bar (chốt từ hạn chốt spec của khoá, giữ nguyên sau đó): "Đạt khi ≥ ___% qua bộ, và ___"
- Kết quả các lượt chạy (bảng % — cập nhật đến trước CP6):

## §8. Phân công & kế hoạch
- Phân công có tên: spec / evidence / prompt / code / demo
- Willing users (≥2 tên) + kế hoạch vòng validation *(bonus, nếu làm)*:
- Multi-prototype (nếu làm): trục khác biệt của ≥2 phương án + lý do chọn:

## §9. Changelog
| Thời điểm | Đổi gì | Vì sao (trỏ về feedback/case nào) |
```
