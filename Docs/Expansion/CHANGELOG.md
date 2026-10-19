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

## Phase 1b — Light/Shadow content (2026-10-19)
- **8 hero mới** (20 tổng): Seren (Light, hộ vệ khiên + thanh tẩy), Nyxara (Shadow, Diệt Vong/xử tử), Ashara (Fire, Nhiệt + hồi sinh mỗi đợt), Nerissa (Water, hồi máu theo số phản ứng), Voltrix (Lightning, cột điện nối mạch), Eirwen (Ice, khiên nổ băng), Kael (Wind, lướt + gom địch), Borun (Earth, tường làm chậm không chặn đường). 16 nhánh tiến hoá đổi cơ chế. Mở khoá qua meta.
- **12 trait** run-only (roll có trọng số theo độ hiếm, kiểm tra điều kiện nguyên tố/vai trò, RNG riêng không làm lệch offer khác, lưu save).
- **22 relic** (2 hợp thể mới: Twilight Crown, Aegis of Ages; keystone: Verdict Scale, Radiant Lens, Shadow Contract, Eclipse Engine, Mason's Level), **12 thẻ** (2 cộng hưởng, 2 phản ứng, 8 chuyên môn).
- **Kẻ địch**: Mana Leech (làm chậm hồi chiêu), Crystal Parasite (bám Pha Lê; phản chế: canh lõi/Ánh Sáng/thanh tẩy), Ash Imp (nổ khi chết); **boss Ignaroth** (dung nham báo trước, Ash Imp, pha Quá Nhiệt + cửa sổ xả nhiệt) — boss đợt 10 chọn theo seed (`bossPool`, lưu save).
- **Ascension 1–5 dữ liệu** (`difficulty.json`): giữ nguyên hiệu ứng cũ + giá cửa hàng, ô bị khoá, affix elite, boss nổi giận.
- UI: chọn đội có lọc nguyên tố + phân trang; trait trên thẻ chiêu mộ và bảng hero; ô bị khoá; banner pha boss theo dữ liệu.
- Tài liệu sinh tự động: `HERO_ROSTER.md`, `CONTENT_MATRIX.csv`; `BALANCE_REPORT.md`.
- Test: 99/99 (thêm Trait, Enemy, Difficulty, Asset contract).

## Phase 2a — Biome, kẻ địch, boss (2026-10-19)
- **Hệ thống biome** (`biomes.json`): bố cục ô/làn riêng, hiểm hoạ có báo trước, đặc tính ô (chỉ chỉ số), che chắn phá được, lịch mở làn, kẻ địch thêm, boss pool, thay thế. Validator kiểm tra 12 ô, 6 làn chạm Pha Lê, hiểm hoạ hợp lệ, boss pool… Lưu trong save, chọn ở màn chọn đội, mở khoá qua meta.
- **2 biome**: Molten Crater (cầu bazan, lỗ dung nham, cầu nóng), Frostfall Bastion (ô băng, che chắn băng, cổng chéo mở đợt 8).
- **14 kẻ địch mới** + **2 boss** (Seraphyne, Gravemaw), xem `ENEMY_BESTIARY.md`, `BOSS_DESIGNS.md`. Đã trộn vào đợt thường.
- Unity: nền/nhạc/màu ô theo biome, cảnh báo hiểm hoạ, bảng chuẩn bị dùng kẻ địch thực tế (`RunController.PreviewEnemies`), lane/debug overlay dùng arena của biome, ô chọn biome, ô mở khoá biome ở màn kết quả.
- Art: 32 sprite kẻ địch, 2 nền biome, 2 sprite field (đám bào tử, che chắn băng); art cũ giữ nguyên từng byte.
- Balance harness: `--biome <id>`.
- Sửa test `TwinCasterEchoesWithACooldown` (trước dựa vào 1 seed, nay cộng 6 seed, cùng cửa sổ 40 s).
- Test: 124/124 (thêm `BiomeTests` 10, `EnemyPhase2Tests` 15).

## Phase 2b — Nature/Poison (2026-10-19)
- **4 hero mới** (24 tổng): Liora (Nature, Rễ Nở Hoa trói cả nhóm; Rễ Sâu +30% lên kẻ bị trói), Thalen (Nature, Tường Gai: khiên + gai phản sát thương + khiêu khích; Da Vỏ Cây giảm sát thương theo máu đã mất), Vesper (Poison, Bình Xúc Tác: độc + vũng độc; Xúc Tác +4%/tầng độc, tối đa 30%), Sable (Poison, Chữa Bằng Dịch: lây độc rồi hồi máu theo số kẻ trúng độc, đổi lại người được hồi bị Sốt; Thầy Thuốc Dịch Hạch hồi khi kẻ trúng độc chết). 8 tiến hoá đổi cơ chế (Rừng Hoang, Vườn Bào Tử, Pháo Đài Gai, Xung Phong Rậm Rạp, Hỗn Hợp Dễ Nổ, Chướng Khí, Đại Dịch, Phương Thuốc).
- Boss không bao giờ bị trói tại chỗ (chỉ bị làm chậm); kẻ bay miễn trói.
- **9 relic** (keystone Plague Bell, Worldroot Heart; hợp thể Rot Bloom = Verdant Seed + Venom Vial), **8 thẻ**; luật mới `root_duration`.
- Đề nghị relic theo nguyên tố của đội (relic gắn thẻ nguyên tố: ×2 nếu khớp, ×0.5 nếu không), chiêu mộ ưu tiên theo số phản ứng Signature tạo được với đội — để danh mục lớn vẫn ra lựa chọn phù hợp.
- AutoPilot: lối chơi `verdant_plague` (Liora+Vesper), `thorn_doctor` (Thalen+Sable).
- Lỗi bắt được nhờ test: `heal_power` của Sable là 0.1 (hệ số nhân ⇒ chỉ hồi 10%) → 1.1.
- Affix tương thích: elite không nhận affix kháng nguyên tố mà nó đã kháng ≥30%, không nhận affix tốc độ nếu đã nhanh/bay/bứt tốc, summon không có affix; kháng sau affix bị chặn ở 75% (trước đây Flame Devourer + fireproof = miễn nhiễm Lửa). Validator kiểm affix ghi sẵn trong đợt.
- Test: 136/136 (thêm `NatureHeroTests` 11, test affix).

## Phase 3 — Arcane/Void, đủ 36 hero, relic/fusion/keystone, Thức tỉnh (2026-10-19)
- **12 hero mới (36 tổng)**: Caelis (lặp chiêu đồng minh, chống vòng lặp), Oriane (vòng cổ tự khuếch đại phản ứng), Zerith (khe nứt kéo + Bất Ổn, không kéo vào Pha Lê), Maelis (lá chắn hư không chặn đạn + phong ấn), Solenne (dấu bỏng nổ ở ngưỡng, tiêu dấu trước khi nổ), Mirel (đẩy lùi + dòng nước), Veyra (tích tụ theo mục tiêu, reset khi đổi), Isolde (phá băng), Aeris (dời vùng có giới hạn, không dời tường, không vào Pha Lê), Doran (Thủ → sát thương, tối đa 40%), Elowen (tia sáng chiếu + hồi máu), Morven (gánh sát thương cho đồng minh máu thấp, không xuống dưới 25% HP). 24 tiến hoá đổi cơ chế, 14 field mới.
- **22 relic** (12 thường, 5 keystone ⇒ **12 keystone**, 5 hợp thể ⇒ **11 công thức hợp thể**), **14 thẻ** (2 cộng hưởng Arcane/Void, 12 chuyên môn).
- **Thức tỉnh nguyên tố** (sự kiện Elemental Shrine): hero cấp 2+ cao nhất nhận nguyên tố phụ tạo phản ứng Signature với nguyên tố gốc; tối đa 2/lượt; tất định theo seed; lưu save; mỗi 2 đòn thường gắn nguyên tố có 1 đòn dùng nguyên tố phụ; hiển thị trong bảng hero.
- Validator: hiệu ứng tiến hoá chỉ được dùng `stat` (trước đây op khác bị bỏ qua âm thầm).
- AutoPilot: `arcane_void`.

## Phase 4a — Chế độ & Ascension 6–10 (2026-10-19)
- Endless, Daily Seed, Boss Rush (xem `META_MODES.md`), chọn ở màn chọn đội, kỷ lục theo chế độ, HUD hiển thị "∞".
- Ascension 6–10 với 5 module mới (enemy_hp, reroll_cost, double_elite, rarity_shift, hazard_shift); `MaxAscension` = 10.
- Harness: `--mode`. Test: `ModeTests` (7), 157/157.
