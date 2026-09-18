# VLearn Interactive Learning Video — Codebase Guide

Đây là codebase prototype cho **video học tập tương tác** có thể tích hợp vào
trang bài học VLearn. Người học xem video recap ngắn, video dừng tại các mốc
`timecode` đã khai báo, người học trả lời checkpoint, đọc giải thích có căn cứ
và chủ động chọn tiếp tục, xem lại hoặc sửa câu trả lời.

> Đây là trải nghiệm học tập/ôn tập, **không phải** game, LMS hoàn chỉnh hoặc
> hệ thống chấm điểm chính thức.

## 1. Mục lục codebase

| Đường dẫn | Mục đích | Khi nào dùng |
| --- | --- | --- |
| [`agent.md`](./agent.md) | Quy tắc bắt buộc cho coding agent: scope, grounding, privacy, logging, test và an toàn `.exe`. | Đọc trước khi sửa hoặc mở rộng code. |
| [`video-generator/`](./video-generator/) | Pipeline Python nhận học liệu, tạo lesson manifest, narration và `recap.mp4`. | Khi cần tạo/cập nhật nội dung bài học. |
| [`interactive-website/`](./interactive-website/) | Website tĩnh HTML/CSS/JavaScript để phát video và checkpoint trong trình duyệt. | Đây là điểm tích hợp hướng tới website VLearn. |
| [`interactive-video-player/`](./interactive-video-player/) | Player desktop Python/Pygame tùy chọn cho demo/offline. | Chỉ dùng khi cần chạy Windows desktop/fullscreen. |

Mỗi module có README riêng với hướng dẫn chi tiết. README này chỉ mô tả cách
chúng hoạt động cùng nhau.

## 2. Kiến trúc và luồng dữ liệu

```text
Học liệu được cấp quyền
(.pdf/.pptx/.md/.txt/.audio/.video)
              |
              v
video-generator
  - trích xuất / phiên âm nguồn
  - tổng hợp nội dung bằng OpenRouter (nếu chạy mode thật)
  - validate lesson schema + citation
  - tạo narration.mp3 và recap.mp4
              |
              v
Bundle bài học
lesson.json + sources.json + recap.mp4 (+ narration.mp3)
              |
       +------+------+
       |             |
       v             v
interactive-website  interactive-video-player
Trình duyệt/VLearn    Desktop Windows tùy chọn
```

### Nguyên tắc của bundle

- `lesson.json` là contract trung tâm: title, narration, scenes, checkpoint,
  đáp án, misconception, explanation và các `source_refs`.
- `sources.json` là catalog citation tối thiểu: mã nguồn, tên file và vị trí.
  Nó **không** chứa toàn bộ text học liệu đã trích xuất.
- `recap.mp4` phải có duration khớp `lesson.json.duration_seconds`; website sẽ
  chặn phiên học nếu media bị lệch đáng kể.
- Tất cả scene/checkpoint phải có citation hợp lệ; citation do model bịa hoặc
  nằm ngoài catalog sẽ bị validator từ chối.

## 3. Yêu cầu môi trường

### Bắt buộc khi tạo video

- Windows PowerShell hoặc terminal tương đương.
- Python 3.10 trở lên.
- [FFmpeg](https://ffmpeg.org/) có trong biến môi trường `PATH`.
- Internet để dùng Edge TTS; mode sinh nội dung thật cần OpenRouter API key.

### Bắt buộc khi chạy website/test web

- Python để chạy static server local.
- Node.js để chạy test của `interactive-website`.

### Bắt buộc khi chạy desktop player

- Python và các package trong
  [`interactive-video-player/requirements.txt`](./interactive-video-player/requirements.txt).

## 4. Cách dùng nhanh: chạy website demo có sẵn

Website hiện có bundle fixture demo để kiểm tra flow ngay. Bundle được đánh dấu
`mock` trên giao diện; không được trình bày là kết quả sinh từ OpenRouter.

```powershell
cd C:\Su\VinLab\Hackathon\codebase\interactive-website
python server.py --port 8000
```

Mở trình duyệt tại:

```text
http://127.0.0.1:8000
```

Thử luồng sau:

1. Bấm phát video.
2. Tại giây 20, video dừng ở checkpoint đầu tiên.
3. Chọn một đáp án hoặc chọn **Chưa chắc, cho mình gợi ý**.
4. Nếu trả lời sai, đọc lời giải trong 5 giây.
5. Chọn **Xem lại 5 giây**, **Sửa câu trả lời** hoặc **Tiếp tục bài**.
6. Chọn **Xem nguồn** để xem citation của checkpoint.
7. Chọn **Tải log phiên này** nếu muốn xuất JSONL; log không tự gửi đến server.

Xem hướng dẫn web đầy đủ tại
[`interactive-website/README.md`](./interactive-website/README.md).

## 5. Tạo video từ học liệu thật

### 5.1 Cài generator

```powershell
cd C:\Su\VinLab\Hackathon\codebase\video-generator
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
ffmpeg -version
```

### 5.2 Thêm học liệu

Tạo `video-generator\input` và chép ít nhất một học liệu thực được cấp quyền:

```powershell
New-Item -ItemType Directory -Force .\input
Copy-Item "C:\duong-dan\bai-giang.pdf" .\input\
```

Các định dạng hỗ trợ: `.md`, `.txt`, `.pptx`, `.pdf`, `.mp3`, `.wav`, `.m4a`,
`.aac`, `.flac`, `.ogg`, `.mp4`, `.mov`, `.webm`, `.mkv`.

Không dùng riêng file template như `mau-kich-ban.md`, `README.md` hoặc
`khung-hinh.md` làm nguồn kiến thức.

### 5.3 Chạy chế độ sinh nội dung thật

```powershell
$env:OPENROUTER_API_KEY="sk-or-v1-..."
$env:OPENROUTER_TEXT_MODEL="openrouter/free"

python agent.py `
  --input ".\input" `
  --prompt "Tạo video ôn tập 60-90 giây, bao phủ ý quan trọng và tạo 3 checkpoint" `
  --output ".\output"
```

Kết quả trong `video-generator\output`:

| File | Nội dung |
| --- | --- |
| `lesson.json` | Manifest cho scenes, checkpoint, đáp án, explanation và citation. |
| `sources.json` | Catalog citation an toàn để hiển thị trên player. |
| `recap.mp4` | Video recap đã render. |
| `narration.mp3` | Giọng đọc TTS. Desktop player cần file này. |
| `transcript.txt` | Lời đọc đã dùng để tạo video. |
| `ai-trace.json` | Trace kỹ thuật đã redaction; không chứa API key. |

### 5.4 Đưa bundle vào website

```powershell
cd C:\Su\VinLab\Hackathon\codebase\video-generator

Copy-Item .\output\lesson.json ..\interactive-website\assets\lesson.json -Force
Copy-Item .\output\sources.json ..\interactive-website\assets\sources.json -Force
Copy-Item .\output\recap.mp4 ..\interactive-website\assets\recap.mp4 -Force

cd ..\interactive-website
python server.py --port 8000
```

Mở `http://127.0.0.1:8000`. Nếu metadata video không khớp duration trong
manifest, website sẽ không bắt đầu session để tránh checkpoint lệch hình.

### 5.5 Chạy fixture offline/mock

Khi chưa có API key hoặc học liệu thật, có thể sinh bundle fixture:

```powershell
cd C:\Su\VinLab\Hackathon\codebase\video-generator
python agent.py `
  --fixture ".\fixtures\demo-lesson.json" `
  --output ".\output"
```

Mode này không gọi OpenRouter và output sẽ ghi `generation.mode: "mock"`.

## 6. Desktop player tùy chọn

Desktop player không thay thế website. Nó chỉ phù hợp demo offline hoặc chạy
full-screen trên Windows.

```powershell
cd C:\Su\VinLab\Hackathon\codebase\interactive-video-player
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

Copy-Item ..\video-generator\output\lesson.json .\assets\lesson.json -Force
Copy-Item ..\video-generator\output\recap.mp4 .\assets\recap.mp4 -Force
Copy-Item ..\video-generator\output\narration.mp3 .\assets\narration.mp3 -Force

python main.py --windowed
```

Có thể build thành `interactive-recap.exe` bằng `build.ps1`, nhưng cần phân
phối minh bạch như ứng dụng Windows có thể tải xuống. **Không được** nhúng,
đổi đuôi hoặc ngụy trang `.exe` thành video trên website.

Xem chi tiết phím điều khiển và build tại
[`interactive-video-player/README.md`](./interactive-video-player/README.md).

## 7. Kiểm thử

Chạy từ thư mục tương ứng.

```powershell
# Generator: schema, citation catalog, rendering contract, TTS và agent.
cd C:\Su\VinLab\Hackathon\codebase\video-generator
python -m unittest discover -s tests -v

# Desktop player: bundle loading, session/checkpoint và JSONL logging.
cd ..\interactive-video-player
python -m unittest discover -s tests -v

# Website: manifest validation, checkpoint state và telemetry allowlist.
cd ..\interactive-website
node --test tests/test_core.mjs
```

Sau khi thay bundle, smoke test thủ công tối thiểu gồm:

- video phát đúng duration;
- video dừng ở mọi checkpoint;
- một câu trả lời đúng và một câu trả lời sai;
- nút gợi ý, xem nguồn, sửa đáp án, xem lại và tiếp tục;
- log tải xuống không chứa API key, source text hoặc dữ liệu nhạy cảm.

## 8. Quy tắc an toàn và giới hạn

- Chỉ dùng học liệu đã được cấp quyền hoặc fixture.
- Không bịa câu trả lời, explanation, citation hoặc timecode.
- Không đưa API key, token, toàn bộ học liệu hoặc câu trả lời tự do vào log.
- Website hiện là static prototype: chưa có login, backend telemetry hay quyền
  truy cập VLearn. Khi tích hợp thật, host VLearn phải chịu trách nhiệm về auth,
  authorization, HTTPS, CSRF/CORS và API logging đã được phê duyệt.
- Không tự mở rộng thành leaderboard, điểm chính thức, hồ sơ học viên dài hạn
  hoặc tutor chat tự do.
- Không ngụy trang hay phân phối `.exe` qua video/website.

Đọc [`agent.md`](./agent.md) để biết đầy đủ contract, quality bar và checklist
bắt buộc trước khi chỉnh sửa hệ thống.
