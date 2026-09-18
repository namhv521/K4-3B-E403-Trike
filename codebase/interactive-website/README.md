# VLearn Interactive Website

Web player để nhúng vào trang bài học VLearn. Trang phát `recap.mp4`, đọc
`lesson.json`, dừng theo timecode checkpoint và chỉ lưu telemetry allowlist trong
tab hiện tại. Khi trả lời sai, lời giải được giữ trên màn hình đủ 5 giây trước
khi mở các lựa chọn xem lại, sửa đáp án hoặc tiếp tục. Không phân phối `.exe`.

Bảng **Log thao tác trực tiếp** bên dưới video hiển thị ngay các phím đã bấm,
click trên control, play/pause, thao tác tua và các event checkpoint. Log không
ghi nội dung nguồn hoặc dữ liệu nhập tự do. Bundle fixture cục bộ không gửi log;
bundle được publish từ Admin gửi event allowlist ẩn danh đến server localhost.

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
node --test tests/test_core.mjs tests/test_admin_core.mjs
python -m unittest discover -s tests -v
```

## Hai role local prototype

Chạy server sau để dùng cả hai màn hình:

```powershell
python server.py --port 8000
```

- **Admin:** mở `http://127.0.0.1:8000/admin`, chọn Lecture 1–4 làm đích,
  chọn folder học liệu, nhập yêu cầu recap và tạo/cập nhật lecture đó. Khi job
  thành công video chỉ được publish sau khi đủ ba artifact hợp lệ; bản video cũ
  vẫn giữ được nếu generation thất bại. Dashboard theo lecture hiển thị users
  local, lượt xem, hoàn thành, checkpoint sai nhiều và event gần đây. Admin có
  nút tạo user test local.
- **User:** mở `http://127.0.0.1:8000`, chọn user local và lecture. Lecture 1
  được seed sẵn từ `assets` (video Bản đồ AI trong 85 giây hiện tại); Lecture
  2–4 chờ Admin publish video. Player giữ checkpoint, dẫn giải nguồn, log trực
  tiếp và kết quả cuối video. Event allowlist gắn user local được gửi đến cùng
  telemetry store và xuất hiện ở Admin trong tối đa 5 giây.

Role này chỉ mô phỏng luồng trên localhost; link chuyển User/Admin và user local
không phải login hay quyền production.
Prompt tạo video chỉ được lưu tạm trong job nội bộ để gọi generator và bị xóa khi
job kết thúc; prompt không xuất hiện trong status API hay dashboard. Timeline chỉ
project session ID ngẫu nhiên, timestamp, loại event, checkpoint và đúng/sai;
không hiển thị input bàn phím/chuột hoặc nội dung nguồn.

## Remotion renderer

Agent giữ Python/OpenRouter làm lớp tổng hợp và grounding, Edge TTS làm giọng
đọc, sau đó render visual bằng Remotion `Series`/subtitle trong
`../video-generator/remotion-recap`. Cài một lần trước khi tạo job:

```powershell
cd ..\video-generator\remotion-recap
npm install
cd ..\..\interactive-website
```

Job admin đặt `VLEARN_RENDERER=remotion`. Cách render concept-card FFmpeg cũ
chỉ còn fallback rõ ràng cho test/khôi phục local (`VLEARN_RENDERER=ffmpeg`).
Kiểm tra TypeScript của composition bằng `npm run typecheck` trong thư mục
`video-generator/remotion-recap`.

Khi tích hợp vào VLearn thật, giữ `core.mjs` làm state/validation contract; host
chịu trách nhiệm xác thực, authorization, HTTPS, CSRF/CORS, consent và retention
telemetry đã được phê duyệt. Không nhúng hoặc tải `interactive-recap.exe` qua website.
