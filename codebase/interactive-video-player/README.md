# Interactive Recap Video Player

Ứng dụng desktop phát video recap toàn màn hình và hiển thị câu hỏi ngay trên
khung hình. Đây không phải website và không cần HTTP server.

## Cài đặt

```powershell
cd C:\Su\VinLab\Hackathon\codebase\interactive-video-player
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Cập nhật bài recap từ agent

Chạy `video-generator` trước, sau đó sao chép ba artifact:

```powershell
Copy-Item ..\video-generator\output\lesson.json .\assets\lesson.json -Force
Copy-Item ..\video-generator\output\recap.mp4 .\assets\recap.mp4 -Force
Copy-Item ..\video-generator\output\narration.mp3 .\assets\narration.mp3 -Force
```

## Chạy

Toàn màn hình:

```powershell
python main.py
```

Chế độ cửa sổ để kiểm thử:

```powershell
python main.py --windowed
```

## Phím điều khiển

- `Space`: phát hoặc tạm dừng video.
- `A`, `B`, `C`, `D`: trả lời checkpoint.
- `0`: học lại từ đầu sau khi xem lời giải sai đủ 5 giây.
- `1`: chuyển tới checkpoint tiếp theo sau khi xem lời giải.
- `R`: bắt đầu phiên mới sau khi hoàn thành.
- `Esc`: thoát.

Điểm chỉ tính lần trả lời đầu tiên. Các lần trả lời sau và misconception vẫn
được ghi vào `runtime-logs/YYYY-MM-DD.jsonl`.

## Đóng gói Windows EXE

```powershell
.\build.ps1
```

Kết quả: `dist\interactive-recap.exe`. File EXE chứa sẵn bài recap hiện có;
chạy lại script build sau khi thay asset bằng bài học mới.

## Kiểm thử

```powershell
python -m unittest discover -s tests -v
```
