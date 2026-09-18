# VLearn Interactive Website

Web player tĩnh để nhúng vào trang bài học VLearn. Trang phát `recap.mp4`, đọc
`lesson.json`, dừng theo timecode checkpoint và chỉ lưu telemetry allowlist trong
tab hiện tại. Khi trả lời sai, lời giải được giữ trên màn hình đủ 5 giây trước
khi mở các lựa chọn xem lại, sửa đáp án hoặc tiếp tục. Không có backend, không
tự gửi log và không phân phối `.exe`.

Bảng **Log thao tác trực tiếp** bên dưới video hiển thị ngay các phím đã bấm,
click trên control, play/pause, thao tác tua và các event checkpoint. Log không
ghi nội dung nguồn hoặc dữ liệu nhập tự do.

Repository có kèm một bundle fixture mock để kiểm tra luồng web ngay. Banner trên
trang sẽ ghi rõ đây là mock; thay bằng bundle sinh từ học liệu trước khi demo/nộp.

## Chạy local

1. Sinh hoặc dùng bundle đã validate từ `..\\video-generator\\output`.
2. Chép đúng ba artifact vào `assets`:

   ```powershell
   Copy-Item ..\video-generator\output\lesson.json .\assets\lesson.json -Force
   Copy-Item ..\video-generator\output\sources.json .\assets\sources.json -Force
   Copy-Item ..\video-generator\output\recap.mp4 .\assets\recap.mp4 -Force
   ```

3. Chạy web server chỉ bind localhost:

   ```powershell
   python server.py --port 8000
   ```

4. Mở `http://127.0.0.1:8000`.

## Kiểm thử

```powershell
node --test tests/test_core.mjs
```

Khi tích hợp vào VLearn thật, giữ `core.mjs` làm state/validation contract; host
chịu trách nhiệm xác thực, authorization, HTTPS, CSRF/CORS và telemetry API đã
được phê duyệt. Không nhúng hoặc tải `interactive-recap.exe` qua website.
