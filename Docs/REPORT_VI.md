# Báo cáo bàn giao — Aetherward 0.1.0

Phiên: Claude Code (cloud container Linux, không có Unity Editor). Nhánh: `main`. Mọi mốc chức năng lớn đã được commit và push lên `main`.

## 1. Đã thực hiện
**Gameplay (pure C#, `Assets/_Aetherward/Scripts/Simulation`)**
- Mô phỏng tick cố định 1/30 s, seed PCG32, chạy 1×/2× cho kết quả giống nhau.
- 12 anh hùng với kỹ năng/nội tại/hồ sơ mục tiêu riêng; 24 nhánh tiến hoá đổi cơ chế; cấp 1–5 trong lượt.
- 6 nguyên tố, 15 phản ứng (gauge, tiêu hao, hồi chiêu theo cặp, giới hạn thế hệ 2, ngân sách proc).
- 15 loại kẻ địch gồm elite Kẻ Tàn Phá, Golem Phá Thành (đợt 10) và Rift Warden 3 pha (đợt 20); AI theo làn, khiêu khích, chặn đường, đánh xa, lính bom, triệu hồi, buff, thích nghi; phục hồi kẹt; hết giờ → đột phá (không softlock).
- 20 đợt dữ liệu; draft thông minh; chiêu mộ; cửa hàng 4/9/14/19; 25 di vật + 3 hợp thể; 46 thẻ (chuyên môn, cộng hưởng, phản ứng, đột biến, khế ước); 3 sự kiện; lãi Vàng; hồi sinh/sửa Pha Lê.
- Kết quả lượt (MVP, phản ứng, kích hoạt di vật, HP Pha Lê theo đợt, "vì sao"), meta (mở khoá, bách khoa, lịch sử, Thăng cấp 1–5), lưu có checksum + backup + migration.

**Unity (`Assets/_Aetherward/Scripts/Unity`, `Editor`)**
- Scene Boot/MainMenu/Battle/Results; `GameRoot` tự khởi tạo dịch vụ.
- Menu có nền sống động, chọn đội (khoá/mở, seed, Thăng cấp), bách khoa, lịch sử, cài đặt (EN/VI, 4 nhóm âm lượng, 2× mặc định, giảm hiệu ứng, rung, số sát thương, tương phản cao, FPS, hiện tầm đánh).
- Chiến trường: view pool, shader nháy khi trúng đòn, VFX/SFX theo sự kiện, tên phản ứng + biểu tượng, thanh boss, banner pha, kéo-thả/chạm-chọn đặt anh hùng, mũi tên làn, khung anh hùng có HP và độ sẵn sàng kỹ năng, overlay debug (F3).
- 7 loại màn thưởng (draft, chiêu mộ, cửa hàng, di vật, tiến hoá, sự kiện, khế ước có xác nhận), tạm dừng/lưu/bỏ lượt, xem build, màn kết quả.
- Editor: Validate Content and Art, Rebuild Scenes, Play From Boot, mô phỏng 6 lối chơi, xoá save, postprocessor texture, build Windows/Android/iOS (menu + batch).

**Asset nguyên bản**: 333 texture (hero 7 tư thế, enemy 2 frame, boss, arena, crystal 3 trạng thái, VFX, icon, UI 9-slice), 43 file âm thanh (SFX theo nguyên tố + 3 vòng nhạc), 811 khoá dịch EN/VI. Tất cả tái tạo được bằng script trong `Tools/`.

## 2. Đã kiểm chứng (bằng chứng thật)
| Hạng mục | Lệnh | Kết quả |
|---|---|---|
| Test mô phỏng | `cd Tools/SimHarness && dotnet test Tests` | **64/64 PASS** |
| Type-check Unity + Editor | `dotnet build UnityCheck` (DLL tham chiếu Unity 2021, không commit) | **0 lỗi** (không thay cho việc mở Unity) |
| Validator nội dung | `ContentPassesValidation` | PASS: tham chiếu chéo, bản dịch en/vi đủ, tooltip không còn token |
| Cân bằng | `dotnet run --project Balance -- --runs 30` | 180 lượt, 105 thắng, **0 lượt kẹt**; `Docs/Balance/` |
| Hiệu năng mô phỏng | `--perf` | 20–82 µs/tick TB, đỉnh ~1.8 ms (desktop) |
| Hình ảnh | contact sheet + composite offline | `Docs/Previews/` (ảnh nguồn và composite có nhãn, **không phải** ảnh chụp Unity) |

Unity Editor: **chưa mở**. Build Windows/Android/iOS: **chưa tạo**. Không có ảnh chụp runtime.

## 3. Chưa xong / blockers
- Chưa chạy trong Unity 6000.4.8f1 → có thể có lỗi chỉ lộ ra khi chạy (khác biệt API 2021↔6000, bố cục IMGUI, cảm giác điều khiển). Cần chủ dự án mở project và làm checklist `Docs/TEST_PLAN.md`.
- PlayMode test đã viết nhưng cần cài Test Framework để chạy.
- Chưa có keystore Android, chứng chỉ iOS; chưa thử thiết bị thật; chưa đo FPS di động.
- Hoạt ảnh là procedural (nhún, co giãn, lao tới, đổi sprite cast) — chưa có animation khung hình vẽ tay; nhạc là bản tổng hợp đơn giản.
- Chưa có chế độ Endless/Daily/Boss Rush (ngoài phạm vi MVP), chưa có gamepad.

## 4. Lỗi và rủi ro
| Mức | Rủi ro | Cách tái hiện / ghi chú |
|---|---|---|
| Cao | Lỗi runtime khi mở Unity lần đầu (import texture/shader, khác biệt API) | Mở project, xem Console; chạy Validate; Play From Boot |
| Trung bình | Bố cục IMGUI chưa được nhìn thấy trên màn hình thật (có thể chồng chữ ở 4:3 hoặc 21:9) | Thử Game view nhiều tỉ lệ |
| Trung bình | Glass Cannon thắng 5/30 trong mô phỏng | `Docs/BALANCE.md` |
| Thấp | Float không fixed-point: replay theo seed có thể lệch nhẹ giữa nền tảng | D-10 |

## 5. Thay đổi thiết kế (so với prompt)
- Dữ liệu nội dung bằng JSON thay ScriptableObject (D-03); UI bằng IMGUI (D-08); không URP/Input System/Test Framework trong manifest (D-01, D-13, D-14).
- Lựa chọn giữa cấp được thể hiện qua thẻ Chuyên môn trong draft (D-06).
- Art vector Python thay Blender (D-07); Blender 4.0.2 có sẵn nhưng không cần cho phong cách này.

## 6. Kế hoạch tiếp theo
1. Mở trong Unity, sửa lỗi runtime, chụp ảnh thật thay composite.
2. Playtest người thật, chỉnh đợt 18–20 và Glass Cannon.
3. Build Windows + Android dev, đo Profiler trên máy tầm trung.
4. Animation khung hình cho hero (cast/hit), thêm nhạc, chế độ Daily Seed.
