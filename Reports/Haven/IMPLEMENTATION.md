# Haven gameplay — báo cáo 2026-10-23

Đã triển khai phần gameplay/code của BACKLOG. Theo yêu cầu chủ dự án ngày 2026-10-23, code, báo cáo, manifest và toàn bộ art return hiện có được commit để bàn giao lên `main`. Nội dung art nguồn được giữ nguyên.

## Hành vi mới

- Cả 6 biome có pháo đài ba cổng, hazard/cover và lịch mở lane được giữ theo biome. Năm biome mới dùng cùng silhouette pháo đài Verdant để tái sử dụng hợp đồng art, với approach/apron khác nhau.
- Người chơi chọn stance và Split/Boss Focus/Swarm; chuẩn bị hiển thị đúng post dự báo bởi Battle. Các số node chỉ còn phục vụ tương thích save/benchmark. Node scoring và kéo-thả không còn trong luồng chơi.
- Ascension phong ấn một entrance đang hoạt động và đổi tuyến nhóm địch, lưu cổng/formation trong save. Area trait cập nhật theo vị trí hiện tại thay cho slot xuất phát.
- Navigation tìm đường trên lưới dùng chung theo arena, đi qua vùng walk nối nhau với clearance tường/Pha Lê. Di chuyển và dash kiểm tra segment để không cắt ngang tường. Hero vẫn có leash khi giao chiến; đường vòng có thể tạm vượt leash thẳng.
- Cổng nam gom bốn lane trong báo cáo coverage. Incoming hiển thị entrance thực tế, Insights tổng hợp sát thương theo cổng và tái dựng coverage đầu wave. Pillage có log nguồn enemy/lane; HUD hiển thị số kẻ xâm nhập.
- 36 ultimate có tên/mô tả EN/VI, cấu hình riêng trên hero, 7 kiểu thi triển, CC/hồi máu/khiên/tích năng lượng khác nhau. Cue nguyên tố tổng hợp bằng script, không dùng sample bên ngoài. Art VFX chưa có vẫn dùng fallback.
- Dock chiến đấu nhỏ hơn; chi tiết/tooltip có ultimate. Training sử dụng cùng planner và có stance/formation, báo cáo mở riêng để không đè các nút cấu hình.

## Kiểm chứng

- `Reports/haven-editmode-tests.txt`: **240/240 test đạt**, gồm 9 test Haven mới cùng test biome/difficulty đã đổi theo cơ chế mới.
- `Reports/haven-unity-compile.txt`: Unity runtime và Editor compile **0 lỗi / 0 cảnh báo** với reference DLL 6000.4.8f1.
- `Reports/ContentValidation/report.md`: **0 lỗi**, 2 cảnh báo thiếu relic tag wind/earth có sẵn; không chặn nội dung.
- `BALANCE_SUMMARY.md`: **720 run**, 240/stance. Defensive 66/240, Balanced 83/240, Aggressive 68/240. Mỗi chiến thuật có 20 seed xoay 6 biome; bộ seed/biome ghép cặp giữa stance. Các núm balance toàn cục giữ nguyên; đây là baseline mới.
- `PERF.md`: probe late-wave và 160 quái cho mỗi biome, 900 tick/biome. P95 0,55–3,21 ms/tick; max có spike đến 17,43 ms. Chỉ mô phỏng .NET desktop, chưa đo VFX/Unity/mobile.
- `git diff --check` và Python compile được kiểm tra trước bàn giao.

## Phần còn chờ

PlayMode đã được gọi bằng Unity 6000.4.8f1 `-batchmode -nographics -runTests -testPlatform PlayMode`; Editor dừng với exit 198 vì không có license hợp lệ. Không có kết quả PlayMode pass và không có ảnh Unity mới trong phiên này. Log tại `Logs/haven-playmode.log` (Logs bị Git bỏ qua). Chạy lại sau khi kích hoạt license, rồi kiểm frame time/GC với VFX trên thiết bị.

Nền cũ của 5 biome chưa thể hiện tường/cổng mới. `ArtHandoff/requests/HAVEN_BIOMES/` có guide và bản trích hình học cho tool art. Handoff pipeline vẫn cần request/INPUT_MANIFEST thực trước khi nhập batch. Art sản xuất hàng loạt chờ benchmark được duyệt theo backlog; chủ dự án đã yêu cầu bàn giao code trực tiếp lên main. TRELLIS tùy chọn được hoãn vì art dùng tool khác; không xóa cache ngoài repo hoặc tải model trong phiên gameplay.

## Tái tạo compile

```powershell
dotnet build Tools/SimHarness/UnityCheck --no-restore --verbosity quiet '-p:UnityManagedPath=C:/Program Files/Unity/Hub/Editor/6000.4.8f1/Editor/Data/Managed'
```

Các lệnh balance và mô tả sample nằm trong `BALANCE_SUMMARY.md`. Build xong trước khi chạy nhiều tiến trình để tránh Windows khóa DLL đầu ra.
