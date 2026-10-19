# Enemy Bestiary (mở rộng)

Mọi cơ chế đọc từ `params` trong `enemies.json` (không theo id); mã ở `Battle.EnemiesExt.cs`, `Battle.EnemiesExt2.cs`. Kháng nguyên tố tối đa 75%, không miễn nhiễm hoàn toàn (validator).

| Kẻ địch | Phe | Cơ chế | Phản chế | Test |
|---|---|---|---|---|
| Mana Leech | Voidborn | Anh hùng trong 2.6 m hồi chiêu chậm 35% | Ưu tiên hạ, Kiên Định, thanh tẩy | `ManaLeechSlows…` |
| Crystal Parasite | Voidborn | Lao qua anh hùng, bám Pha Lê, giảm 60% sát thương khi không ai canh lõi | Canh lõi, Ánh Sáng/thanh tẩy gỡ ra | `CrystalParasite…`, `GuardingTheCore…` |
| Ash Imp | Ashen Horde | Nổ khi chết | Hạ ở xa anh hùng | `AshImpBursts…` |
| Goblin Sprinter | Iron Legion | Bứt tốc ×1.9 mỗi 4 s | Làm chậm, trói rễ, phủ làn | `GoblinSprinter…` |
| Ironback Golem | Iron Legion | Đòn thường chỉ gây 50% đến khi giáp nứt/Ăn Mòn | Chiêu, phản ứng, Đất, Độc | `IronbackPlates…` |
| Spirit Splitter / Wisp | Voidborn | Tách thành 2 Đốm khi chết; Đốm không tách nữa | Sát thương diện rộng | `SpiritSplitter…` |
| Flame Devourer | Ashen Horde | Kháng Lửa 60%, mỗi đòn Lửa tăng tốc (tối đa +30%); yếu Nước | Đổi nguồn sát thương, Bốc Hơi | `FlameDevourer…` |
| Frost Wraith | Frozen Covenant | Giảm 35% sát thương trừ khi bị Chiếu Sáng; bỏ qua vùng mặt đất | Ánh Sáng, dồn sát thương | `FrostWraith…` |
| Storm Harpy | Stormspire | Bay thẳng tới Pha Lê qua tường/vùng; cận chiến đánh thường chỉ 50% | Tầm xa | `StormHarpy…` |
| Stone Burrower | Iron Legion | Đi ngầm (không bị đánh/gắn nguyên tố), trồi lên gần lõi sau cảnh báo 1.2 s | Đứng vòng trong | `StoneBurrower…` |
| Void Priest | Voidborn | Niệm 0.8 s hồi 6% HP cho địch quanh 2.6 m; choáng sẽ ngắt | Choáng/đóng băng, hạ trước | `VoidPriest…` |
| Hex Binder | Arcane Fractures | Mỗi 6 s Câm Lặng anh hùng gần nhất 2.5 s | Kiên Định, thanh tẩy | `HexBinder…` |
| Siege Colossus | Iron Legion | Dừng cách lõi 5.5 m, nã pháo (báo trước 1.8 s) vào Pha Lê | Anh hùng cánh/tầm xa | `SiegeColossus…` |
| Soul Binder | Voidborn | Liên kết ≤3 đồng minh: chúng nhận ít 40%, phần đó dồn vào kẻ trói | Hạ kẻ trói, AoE | `SoulBinder…` |
| Spore Carrier | Corrupted Wilds | Chết để lại đám bào tử hồi máu cho địch | Hạ xa đám đông, Lửa | `SporeCarrier…` |
| Ice Statue | Frozen Covenant | Tượng bất động của Seraphyne, giảm 45% sát thương cho bà ta; vỡ khi bà ta chết | Lửa | `StatuesGuardSeraphyne…` |

Xuất hiện: các kẻ địch Phase 2 đã được trộn (số lượng nhỏ, thay một phần grunt/runner) vào đợt 4–19 của chế độ thường, và thêm theo biome.

Tổng hiện tại: 35 kẻ địch (gồm 5 boss). Mục tiêu 45+ ở Phase 4.
