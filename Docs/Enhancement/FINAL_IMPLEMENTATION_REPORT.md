# Báo cáo triển khai cuối — Gameplay Operations Enhancement

- **Engine:** Unity 6000.4.8f1 (built-in renderer, IMGUI). Kiến trúc 2D không đổi.
- **Môi trường:** Unity Editor/Player **không có** trong môi trường này, nên mọi phần Unity chỉ được type-check bằng `UnityCheck`, **chưa chạy thật**.

## 1. Đã làm (có bằng chứng)

| Hạng mục | Kết quả | Bằng chứng |
|---|---|---|
| AI chọn mục tiêu | Utility 7 thành phần, 5 tactic, hysteresis, AI inspector | `TargetAITests`; A/B so cặp 24.000 run: **8,25% → 9,46%** thắng (p≈5e-14) → `Reports/Balance/ab_targeting.md` |
| Tactic đội | Ảnh hưởng đo được: bot chọn tactic theo preview đợt **9,46% → 12,22%** (p≈3e-65) | `Reports/Balance/ab_bot_tactics.md` |
| Crystal Evolution | 3 nhánh loại trừ, feature flag, lưu trong save, UI. Tác động: +3,5 điểm (bản đầu). Sau retune, 3 nhánh cách nhau ≤2 điểm (CI chồng nhau). | `CrystalEvolutionTests`, `Reports/Balance/ab_crystal_evolution.md`, `Reports/Balance/crystal_paths/` |
| Draft/shop công bằng | Khoá món, slot "lựa chọn chiến lược", reroll tăng giá, offer log tất định | `DraftFairnessTests` |
| Run breakdown | Nguồn sát thương theo loại (không đếm trùng), bước ngoặt, share code | `RunBreakdownTests`, `Reports/RunBreakdown/run_1007.md` |
| Simulator cân bằng | `--batch` (4 policy, Wilson CI, CSV, content hash, song song, chạy lại cho kết quả giống từng byte) | baseline 48.000 run: `Reports/Balance/baseline_legacy_ai/` |
| Kiểm nội dung | `--validate`: 0 lỗi, 2 cảnh báo (wind/earth mỗi nguyên tố chỉ có 1 relic) | `Reports/ContentValidation/` |
| Encounter log | Ngân sách từng đợt cho Classic/Endless/Boss Rush, cờ spike/dip | `Reports/Balance/encounters.md` |
| Hiệu năng headless | Soak 40 đợt Endless: ~0,02 ms/tick, bộ nhớ giữ lại ổn định ~1,5 MB | `Reports/Performance/headless_soak.md` (**không phải** profile Unity) |
| Save | Backup 2 tầng, cách ly file hỏng (`.corrupt`), ghi nguyên tử bằng `File.Replace`, fixture save MVP | `SaveCompatTests` |
| A11y / hiển thị | Gộp số sát thương, cường độ flash, tự tạm dừng khi mất focus, tiết kiệm pin | `PresentationRulesTests` (chỉ phần logic) |
| Phản hồi người chơi | Đánh giá sao + lý do sau mỗi run, chỉ lưu trên máy | test lưu/đọc |
| Kiểm thử | **192/192** test pass; UnityCheck 0 lỗi | `dotnet test Tools/SimHarness/Tests` |

## 2. Phát hiện cân bằng (nói thẳng)
- Tỉ lệ thắng của bot vẫn thấp: khoảng 7–13% tuỳ policy và cờ. Đây là **bot**, không phải người chơi.
- Policy "synergy" (6,9%) **kém hơn** random (9,2%), còn scripted chỉ cao hơn random khoảng 1,7 điểm. Nghĩa là heuristic synergy của bot đang yếu, và chưa chứng minh được lựa chọn draft quan trọng đến mức nào. **Chưa sửa.**
- Đợt 14 và 18 chiếm khoảng 42% số lần thua, chủ yếu do sapper. Encounter log đánh dấu đợt 14 là spike. Đã có hai đòn bẩy cho người chơi: tactic Protect Crystal và Crystal Evolution. **Chưa chỉnh dữ liệu đợt.**

## 3. Chưa làm / bị chặn
- **Chưa** mở Unity, build nền tảng hay profile FPS/GC/draw call trên thiết bị.
- **Chưa** có playtest người thật; tính năng phản hồi đã sẵn nhưng chưa thu thập gì.
- **Chưa** làm: Emergency Swap, ô đội hình, encounter director động, cửa sổ Editor cho validator.
- CI `.github/workflows/simulation.yml` **chưa từng chạy** trên GitHub.

## 4. Tái lập
```
cd Tools/SimHarness
dotnet test Tests
dotnet run --project Balance -c Release -- --validate
dotnet run --project Balance -c Release -- --batch 500 [--no-crystal-evo] [--legacy-targeting] [--bot-tactics] [--crystal-path bastion|pulse|thorn] --out <dir>
dotnet run --project Balance -c Release -- --encounters | --soak 40 | --breakdown 1007
python3 Tools/Reports/ab_compare.py <A_dir> <B_dir> <out.md> "<title>"
```

Xem thêm: `ARCHITECTURE_DELTA.md`, `UX_AND_COMBAT_GUIDE.md`, `RELEASE_CHECKLIST.md`, `PHASE_REPORTS.md`.
