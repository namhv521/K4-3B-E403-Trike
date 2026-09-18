# Video Generator Agent

Agent nhận tài liệu bài giảng, tổng hợp kiến thức bằng OpenRouter, tạo câu hỏi
checkpoint, sinh giọng đọc tiếng Việt bằng Edge TTS và dựng `recap.mp4`.

## 1. Chuẩn bị

Yêu cầu: Python 3.10+, FFmpeg trong `PATH`, Internet và OpenRouter API key.

```powershell
cd C:\Su\VinLab\Hackathon\codebase\video-generator
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
ffmpeg -version
```

## 2. Thêm dữ liệu

Tạo folder `input` và chép tài liệu thật vào đó:

```powershell
New-Item -ItemType Directory -Force .\input
Copy-Item "C:\duong-dan\bai-giang.pdf" .\input\
Copy-Item "C:\duong-dan\slide.pptx" .\input\
```

Định dạng hỗ trợ:

- Văn bản: `.md`, `.txt`
- Slide và tài liệu: `.pptx`, `.pdf`
- Audio: `.mp3`, `.wav`, `.m4a`, `.aac`, `.flac`, `.ogg`
- Video: `.mp4`, `.mov`, `.webm`, `.mkv`

Không dùng riêng `mau-kich-ban.md`, `README.md` hoặc `khung-hinh.md` làm đầu
vào. Đây chỉ là file mẫu; agent cần ít nhất một file chứa kiến thức bài giảng.

## 3. Chạy agent thật

```powershell
$env:OPENROUTER_API_KEY="sk-or-v1-..."
$env:OPENROUTER_TEXT_MODEL="openrouter/free"

python agent.py `
  --input ".\input" `
  --prompt "Tạo video ôn tập 60-90 giây, bao phủ các ý quan trọng từ mọi tài liệu và tạo 3 checkpoint" `
  --output ".\output"
```

Agent chia nguồn thành nhiều nhóm, tóm tắt từng nhóm rồi tổng hợp lần cuối để
không bỏ qua các tài liệu nằm cuối folder.

Audio và video đầu vào được chuyển thành văn bản qua OpenRouter transcription.
Giọng đọc đầu ra dùng Edge TTS miễn phí. Có thể đổi giọng:

```powershell
$env:EDGE_TTS_VOICE="vi-VN-NamMinhNeural"
```

Giọng mặc định là `vi-VN-HoaiMyNeural`.

## 4. Chạy bản demo

Bản demo không gọi OpenRouter để tạo nội dung nhưng vẫn gọi Edge TTS để tạo
giọng đọc thật:

```powershell
python agent.py `
  --fixture ".\fixtures\demo-lesson.json" `
  --output ".\output"
```

## 5. Kết quả

Folder `output` gồm:

- `recap.mp4`: video có hình và giọng đọc.
- `narration.mp3`: audio TTS riêng.
- `lesson.json`: cảnh, checkpoint, câu hỏi, đáp án và misconception.
- `transcript.txt`: toàn bộ lời đọc.
- `sources.json`: catalog citation tối thiểu (`ref`, tên file, vị trí), không chứa text học liệu đã trích xuất.
- `ai-trace.json`: model, bước gọi AI và usage trả về.

Để đưa kết quả vào website:

```powershell
Copy-Item .\output\recap.mp4 ..\interactive-website\assets\recap.mp4 -Force
Copy-Item .\output\lesson.json ..\interactive-website\assets\lesson.json -Force
Copy-Item .\output\sources.json ..\interactive-website\assets\sources.json -Force
cd ..\interactive-website
python server.py
```

Mở `http://127.0.0.1:8000`.

## 6. Kiểm tra và xử lý lỗi

Chạy test:

```powershell
python -m unittest discover -s tests -v
```

- `Input does not exist`: tạo folder `input` hoặc dùng đường dẫn tuyệt đối.
- `Input chỉ chứa file mẫu`: thêm nội dung bài giảng thật.
- `OPENROUTER_API_KEY is not configured`: khai báo biến môi trường API key.
- `Edge TTS failed`: kiểm tra Internet rồi chạy lại; agent tự thử tối đa hai lần.
- `FFmpeg is required`: cài FFmpeg và thêm thư mục `bin` vào `PATH`.
