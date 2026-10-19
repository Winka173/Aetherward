# Changelog mở rộng

## Phase 0 — Audit (2026-10-19)
- Baseline: 64/64 test, type-check Unity 0 lỗi, 60 lượt mô phỏng 0 kẹt. Xem `BASELINE_AUDIT.md`.
- Kế hoạch & quyết định: `EXPANSION_PLAN.md`, `DECISIONS.md`.

## Phase 1a — Hạ tầng 12 nguyên tố (2026-10-19)
- `Element` append-only: Light=7, Shadow=8, Nature=9, Poison=10, Arcane=11, Void=12; `PairIndex = x*16+y` (256 ô).
- `elements.json`: màu, status, stage, op khi gắn/làm mới aura (Fire→Burn, Earth→Nứt Giáp chuyển từ code sang dữ liệu, hành vi giữ nguyên).
- Hệ status dùng chung `Battle.Statuses.cs`: Illuminated, Doom (xử tử), Rooted (miễn nhiễm 1.5s), Poison (≤10 stack, Corroded, lây ≤2 lần), Resonant, Unstable (sụp đổ có hồi), Brittle, Reaction-vuln, Mark, Seal.
- Phản ứng khai báo `Battle.ReactionOps.cs` (20 op) + `fields` (zone dữ liệu, `ZoneKind.Field`). 20 phản ứng Signature mới + 5 Generic có tên + 23 Generic tự sinh + 3 Neutral ⇒ đủ 66 cặp. `worldCooldown` cho phản ứng buff đội.
- Chọn aura tất định: bỏ qua cặp Neutral; với 6 nguyên tố gốc kết quả **giống hệt** (mô phỏng 60 lượt cho kết quả trùng từng con số với baseline).
- Unity: màu nguyên tố/icon status/sprite field đọc từ dữ liệu; tên phản ứng chung ghép từ hai nguyên tố; âm thanh phản ứng lấy từ dữ liệu.
- Art: 6 icon nguyên tố, đạn + va chạm, 13 icon status, 25 icon phản ứng + icon chung, 10 sprite field; âm thanh hit/cast 6 nguyên tố + 6 họ phản ứng.
- `AssetManifest` (C#) liệt kê mọi art/âm thanh nội dung yêu cầu; test `AssetContractTests` kiểm file tồn tại.
- Sửa lỗi tất định của pipeline art: `vfx.py` dùng `hash()` (bị salt mỗi lần chạy) → `crc32`; 2 texture impact đổi chi tiết ngẫu nhiên một lần.
- Tài liệu sinh tự động: `ELEMENT_REACTION_MATRIX.md`.
