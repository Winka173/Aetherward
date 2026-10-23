# Lưu artifact của Aetherward

Đường dẫn chuẩn cho asset chạy game là `Assets/_Aetherward/Resources/Art/`; metadata nguồn gốc là `Docs/ASSET_MANIFEST.json`. Tiếp tục giữ manifest trong Git.

Bản gốc do tool art trả về tiếp tục nằm trong `ArtHandoff/returns/<batch>/`. Theo yêu cầu chủ dự án ngày 2026-10-23, toàn bộ bản gốc hiện có được commit cùng code và báo cáo để bàn giao lên main. Không di chuyển file khỏi đường dẫn này. Các thư mục nguồn này không phải bản sao runtime để Unity import trực tiếp. Bản Git trên origin giữ nguyên batch kèm DELIVERABLE_MANIFEST để đối chiếu nguồn gốc.

Brief và guide nhỏ được giữ trong `ArtHandoff/requests/`; báo cáo kiểm định trong `Reports/`. `ArtCache/` chứa staging, render tạm và backup import có thể tái tạo, tiếp tục bị Git bỏ qua. Không xóa cache ở ổ khác qua pipeline repo.

Gói `ArtHandoff/requests/HAVEN_BIOMES/` là tài liệu hình học cho năm biome, không phải batch art đã được nghiệm thu. Tạo batch request/INPUT_MANIFEST bằng pipeline handoff khi bắt đầu sản xuất nền.

Đợt bàn giao main bao gồm manifest và art return hiện có, không chỉnh sửa nội dung art nguồn. Sản xuất art hàng loạt vẫn chờ benchmark được chủ dự án duyệt theo BACKLOG.
