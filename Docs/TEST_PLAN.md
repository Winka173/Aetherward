# Kế hoạch kiểm thử

## Tự động — đã chạy trong phiên này (dotnet, ngoài Unity)
`cd Tools/SimHarness && dotnet test Tests` → **64/64 PASS** (NUnit 3.14, .NET 8). Các file test nằm trong `Assets/_Aetherward/Tests/EditMode/` và cũng chạy trong Unity Test Runner.

| Nhóm | Test tiêu biểu |
|---|---|
| Nội dung | `ContentLoadsWithExpectedCounts`, `ContentCatalogMeetsMvpCounts`, `ContentPassesValidation` (tham chiếu chéo, bản dịch en/vi đủ, tooltip hết token) |
| Sát thương | `DefenseFormulaReducesPhysicalDamage`, `ReactionDamageIgnoresDefenseButNotResistance`, `CritChanceIsCappedAndMultiplierBounded`, `ShieldAbsorbsBeforeHpAndHealingDoesNotOverflow`, `ShieldbearerBlocksFrontalHits` |
| Phản ứng | 15 cặp giao hoán, `ReactionConsumesExistingGauge`, `GaugeDecaysOverTime`, `SamePairHasAntiRepeatCooldown`, `GenerationCapBlocksSecondaryChains`, `PerTargetBudgetCapsReactionsPerSecond`, `RainstormSpreadsWetButSecondaryChainsStayBounded`, `BurnTickCanTriggerVaporizeOnWetTarget`, `FreezeStuns…BossesBuildResistance`, `ElementalMirrorStaysBoundedInDenseCrowds` |
| AI / wave | `DeadTargetsAreReleasedByHeroes`, `StuckEnemiesAreNudgedForward`, `DownedHeroStopsActingAndReleasesEngagedEnemies`, `TimeoutBreachResolvesWave`, `NoHeroesMeansEnemiesDamageCrystalAndWaveStillResolves`, `AdaptiveEnemiesGainPartialResistanceOnly` |
| Anh hùng | `EveryHeroSkillCastsInARealWave` (12), `EveryEvolutionBuildsAndCasts` (24), `EvolvedHeroChangesMechanicsInBattle` |
| Run | draft không trùng/không sai điều kiện, luôn có thẻ cộng hưởng, max stacks, giá cửa hàng tăng & thiếu Vàng, tiến hoá cần cấp + Tinh Chất, hợp thể, khế ước trừ HP chính xác, hồi sinh, lãi Vàng, modifier không rò rỉ sang lượt mới, 2 lượt cùng seed giống nhau |
| Lưu | round-trip run + meta, file hỏng → .bak → mặc định, migration v1→v2, meta chỉ mở khoá (không tăng chỉ số) |
| Toàn lượt | 6 lối chơi chạy trọn 20 đợt không kẹt; `TwoTimesSpeedIsJustMoreTicks`; `JournalNeverGrowsUnbounded`; `SameSeedReplaysIdentically` |

Ngoài ra: `Tools/SimHarness/UnityCheck` type-check toàn bộ script Unity + Editor với DLL tham chiếu Unity (0 lỗi). Đây **không** phải chạy trong Unity.

## Tự động — chưa chạy (cần Unity 6000.4.8f1)
- `Assets/_Aetherward/Tests/PlayMode/RunFlowPlayModeTests.cs`: Boot → Menu → Battle → đặt anh hùng → đợt 1 → phần thưởng → Abandon → Results → Menu.
- Cần cài **Test Framework** (Window > Package Manager > Unity Registry > Test Framework) vì manifest chỉ dùng module builtin (D-01). Sau đó Window > General > Test Runner > EditMode / PlayMode > Run All.

## Kiểm thử thủ công trong Unity (checklist cho chủ dự án)
1. Mở project bằng 6000.4.8f1 → chờ import → **Aetherward > Validate Content and Art** phải báo "Validation passed".
2. Mở `Assets/_Aetherward/Scenes/Boot.unity` → Play (hoặc **Aetherward > Play From Boot**). Splash → Menu có nền đấu trường và 6 anh hùng nhún nhảy.
3. Lượt mới → chọn 2 anh hùng → Bắt đầu. Kiểm tra: mũi tên đỏ trên làn, kéo-thả và chạm-chọn đều đặt được anh hùng, nút Tự sắp xếp.
4. Bắt đầu đợt: số sát thương, phản ứng có tên + biểu tượng, nút 2×, FX-, tạm dừng (Esc), F3 hiện tầm đánh.
5. Sau đợt: draft 3 thẻ (chạm để chọn rồi "Nhận"), đổi thẻ trừ Vàng, Bỏ qua. Đợt 2: chiêu mộ. Đợt 4: cửa hàng. Đợt 5: di vật. Đợt 8: sự kiện. Đợt 10: Golem + tiến hoá. Đợt 15: khế ước có hộp xác nhận.
6. Tạm dừng → Lưu và về menu → "Chơi tiếp" khôi phục đúng đợt/phần thưởng.
7. Cài đặt: đổi Tiếng Việt (mọi chữ đổi, dấu hiển thị đúng), âm lượng 4 nhóm, giảm hiệu ứng, rung, tương phản cao, FPS.
8. Tỉ lệ màn hình: Game view 16:9, 19.5:9, 4:3, 21:9 — HUD trong safe area, không chữ bị cắt.
9. Kết quả: biểu đồ anh hùng/phản ứng, dòng "vì sao", mở khoá, Lượt mới (seed mới).
10. Ghi lại lỗi Console (không được có lỗi đỏ trong một đợt bình thường).

## Thiết bị
Chưa thử trên Android/iOS/PC thật. Cần đo FPS bằng Profiler trên một máy Android tầm trung (đợt 18–20, giảm hiệu ứng tắt/bật).
