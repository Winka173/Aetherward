# Changelog

## 0.1.0 — 2026-10-19 (phiên Claude Code đầu tiên)
- Khởi tạo project Unity 6000.4.8f1 (cấu hình dựa trên Arcane-Brigade), harness .NET.
- Mô phỏng chiến đấu tất định: 12 anh hùng, 24 tiến hoá, 15 kẻ địch (2 boss), 6 nguyên tố, 15 phản ứng, chống chuỗi proc.
- Lớp run: draft thông minh, chiêu mộ, cửa hàng, 25 di vật + 3 hợp thể, 46 thẻ, sự kiện, khế ước, lãi Vàng, meta, lưu có checksum/backup/migration.
- Art vector + âm thanh tổng hợp (nguyên bản), bản dịch EN/VI 811 khoá, tooltip sinh từ dữ liệu.
- Lớp Unity: menu, chọn đội, bách khoa, lịch sử, cài đặt, chiến trường, HUD, 7 loại màn thưởng, tạm dừng, kết quả; editor tools và script build.
- 64 test tự động; 180 lượt mô phỏng cân bằng; composite offline.
- Sửa lỗi: Mưa của Torrent Caller nhân Công hai lần.
- Sửa sau review lớp Unity: overlay (tạm dừng, cài đặt, xem build, tiến hoá, xác nhận khế ước) chặn click/phím Space/kéo-thả bên dưới; vòng lặp ưu đãi dừng khi danh sách đổi trong frame; nút Đóng cài đặt không còn đè hàng FPS; cache style không phình theo màu; xoá save ngay khi Pha Lê vỡ (không chơi lại đợt thua); không attach controller hai lần; object world/debug/backdrop gắn dưới controller; bỏ qua âm `cast_none` và sprite relic không tồn tại.
