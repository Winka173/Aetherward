# QA Matrix

Trạng thái: `NOT_STARTED` / `IMPLEMENTED_UNVERIFIED` (code có, chưa kiểm chứng trong Unity) / `VERIFIED` (có bằng chứng lệnh) / `BLOCKED`.

Mô phỏng (pure C#) được kiểm chứng bằng `dotnet test`; mọi thứ hiển thị trong Unity là tối đa `IMPLEMENTED_UNVERIFIED`.

| Hạng mục | Mô phỏng | Unity | Bằng chứng |
|---|---|---|---|
| Baseline MVP | VERIFIED | IMPLEMENTED_UNVERIFIED | 64/64 test, UnityCheck 0 lỗi |
| Mô hình 12 nguyên tố + ma trận 66 cặp | VERIFIED | IMPLEMENTED_UNVERIFIED | `ElementExpansionTests.EverySixtySixPairHasAnExplicitCategory`, `ContentPassesValidation` |
| 15 phản ứng gốc không đổi | VERIFIED | IMPLEMENTED_UNVERIFIED | `ReactionTests` (16), mô phỏng 60 lượt trùng baseline |
| Status Illuminated/Doom/Root/Poison/Resonant/Unstable | VERIFIED | IMPLEMENTED_UNVERIFIED | 7 test trong `ElementExpansionTests` |
| 25 phản ứng mới + field | VERIFIED (kích hoạt, không NaN, trong trần) | IMPLEMENTED_UNVERIFIED | `EveryReactionResolvesWithinCaps`, `RandomTwelveElementStormStaysBounded` |
| Art/âm thanh nguyên tố mới | VERIFIED (file tồn tại) | IMPLEMENTED_UNVERIFIED (chưa xem trong game) | `AssetContractTests`, `Docs/Previews/expansion_elements.png` |
| 8 hero Phase 1 + 16 tiến hoá | VERIFIED (cast trong đợt thật) | IMPLEMENTED_UNVERIFIED | `EveryHeroSkillCastsInARealWave`, `EveryEvolutionBuildsAndCasts` |
| Trait (12) | VERIFIED | IMPLEMENTED_UNVERIFIED | `TraitTests` (6) |
| Mana Leech / Crystal Parasite / Ash Imp / Ignaroth | VERIFIED | IMPLEMENTED_UNVERIFIED | `EnemyExpansionTests` (6) |
| Boss pool đợt 10 (tất định, lưu save) | VERIFIED | — | `BossPoolChoiceIsDeterministicSavedAndUsed` |
| Ascension 1–5 module | VERIFIED | IMPLEMENTED_UNVERIFIED | `DifficultyTests` (5) |
| Relic/thẻ mới (34) | VERIFIED (validator, mô tả sinh từ dữ liệu) | IMPLEMENTED_UNVERIFIED | `ContentPassesValidation` |
| Cân bằng Phase 1 | ĐO ĐƯỢC, chưa đạt mục tiêu | — | `BALANCE_REPORT.md` |
| Hệ thống biome + 2 biome | VERIFIED | IMPLEMENTED_UNVERIFIED | `BiomeTests` (10): làn tới Pha Lê, tường không chặn, hiểm hoạ, che chắn, lịch làn, đặc tính ô, save, mở khoá, không kẹt |
| 14 kẻ địch Phase 2 | VERIFIED | IMPLEMENTED_UNVERIFIED (sprite chỉ xem qua contact sheet) | `EnemyPhase2Tests` |
| Seraphyne / Gravemaw | VERIFIED (pha, cửa sổ, không kẹt) | IMPLEMENTED_UNVERIFIED | `SeraphyneRaises…`, `StatuesGuard…`, `GravemawVents…` |
| Cân bằng Phase 2a | ĐO ĐƯỢC | — | `BALANCE_REPORT.md`, `BIOMES.md` |
