# Báo cáo cuối — Mở rộng hậu MVP Aetherward

**Trung thực trước hết:** toàn bộ công việc được kiểm chứng bằng mô phỏng C# thuần (`dotnet test`, harness cân bằng) và type-check script Unity với DLL tham chiếu. **Chưa mở Unity 6000.4.8f1, chưa build Windows/Android/iOS, chưa chụp màn hình trong game.** Mọi thứ hiển thị trong Unity ở trạng thái `IMPLEMENTED_UNVERIFIED` (xem `QA_MATRIX.md`).

## Đã giao (so với mục tiêu)
| Hạng mục | Mục tiêu | Hiện có |
|---|---|---|
| Nguyên tố chính | 12 | 12 (Time/Crystal giữ là trường phái đặc biệt) |
| Phản ứng | 25–35 đặc trưng, đủ 66 cặp | 35 đặc trưng + 5 chung có tên + chung tự sinh + trung tính; cả 66 cặp có phân loại |
| Hero | 36 | 36, mỗi hero 2 tiến hoá đổi cơ chế (72) |
| Trait / Bond | 12 / ≥8 | 12 / 12 |
| Kẻ địch | 45+ / 6 phe | 52 (40 thường + 12 boss), 7 thẻ phe |
| Boss | 12 | 12 (5 viết tay + 7 bằng mô-đun dữ liệu) |
| Biome | 6 | 6 (hiểm hoạ có cảnh báo, ô đặc tính, che chắn, lịch mở làn) |
| Relic/thẻ | 150+ | 161 (81 relic + 80 thẻ), 11 hợp thể, 12 keystone |
| Thức tỉnh nguyên tố | có | có (sự kiện Elemental Shrine, tối đa 2/lượt) |
| Ascension | 1–10 | 1–10 bằng module |
| Chế độ | Classic/Endless/Daily/+1 | Classic, Endless, Daily Seed, Boss Rush |
| Codex | ma trận phản ứng | tab Ma trận 12×12 + phân trang |

Test: **165/165** pass; UnityCheck 0 lỗi; mọi art/âm thanh nội dung có file (test hợp đồng tài nguyên); art cũ giữ nguyên từng byte qua mọi lần sinh lại.

## Cân bằng (mô phỏng AutoPilot — không phải người chơi)
- Pool khởi đầu (người chơi mới): 6 lối chơi launch ≈ **52%** thắng.
- Toàn bộ nội dung mở khoá: ≈ **11%**. Đã bisect: không có nội dung "hỏng"; giới hạn chủ yếu là bot theo kế hoạch cố định trong pool lớn. **Chưa đạt mục tiêu**, cần playtest người thật (K-04).
- Phát hiện quan trọng: tỉ lệ thắng rất nhạy với hình học làn (K-07); 3 biome mới dùng làn mặc định.
- Chi tiết mọi thí nghiệm: `BALANCE_REPORT.md`, `BIOMES.md`, `META_MODES.md`.

## Lỗi thật đã bắt được nhờ test/đo
Sable chỉ hồi 10% (heal_power 0.1); affix elite cộng dồn kháng thành miễn nhiễm; hiệu ứng `rule` trong tiến hoá bị bỏ qua âm thầm; tượng băng có thể làm kẹt đợt; Siege Colossus một mình gây 44 thất bại; ô phòng thủ Molten Crater đặt xa làn (2/180 thắng).

## Việc cần làm tiếp (theo thứ tự)
1. Mở project trong Unity 6000.4.8f1, chạy `Aetherward > Validate Content and Art`, chơi thử mỗi biome/chế độ, kiểm tra UI mới (chọn chế độ/biome, ma trận codex, gắn kết, thức tỉnh).
2. Playtest người thật với toàn bộ nội dung để xác định K-04 là do bot hay do game.
3. Build Windows/Android/iOS.
