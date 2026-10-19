# Known Issues (mở rộng)

| ID | Mức | Vấn đề | Tái hiện / ghi chú |
|---|---|---|---|
| K-01 | Cao | Chưa mở project trong Unity 6000.4.8f1: mọi thay đổi Unity chỉ được type-check với DLL 2021.3 | Mở project → Console; `Aetherward > Validate Content and Art`; `Play From Boot` |
| K-02 | Trung bình | Chưa có build Windows/Android/iOS | `Aetherward > Build > …` trên máy có module |
| K-03 | Trung bình | Art/VFX mới chỉ xem được qua contact sheet, chưa xem trên màn hình game | `Docs/Previews/` |
| K-04 | Cao | Khi mở khoá toàn bộ nội dung, lối chơi kịch bản thắng ít hơn baseline (pool hero/relic loãng, đội nhiều cặp Generic); lối chơi khởi đầu bằng 2 hero mở rộng chỉ ~0–1/30 với AutoPilot | `dotnet run --project Tools/SimHarness/Balance -c Release -- --runs 30` so với `--launch-pool`; xem `BALANCE_REPORT.md` |
| K-05 | Thấp | Tư thế gục của Borun (và Magnus từ MVP) bị cắt nhẹ ở đáy canvas | `Docs/Previews/heroes.png` |
| K-06 | Thấp | Lỗ dung nham Molten Crater nằm sát mép sông dung nham trên nền (hình hơi chồng mép) | `Docs/Previews/bg_molten_crater.png` |
| K-07 | Trung bình | Tỉ lệ thắng (AutoPilot) rất nhạy với hình học làn: thay đổi nhỏ của điểm làn làm tỉ lệ thắng giảm 3×. Chưa rõ do đội hình bot hay do game; 3 biome mới tạm dùng làn mặc định | `--biome` + so sánh `BIOMES.md` |
