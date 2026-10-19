# Boss Designs

Quy tắc: không bất tử, không sát thương tức thời vào Pha Lê, mọi đòn lớn đều có cảnh báo, luôn có cửa sổ phản công; mỗi boss có test "không kẹt" (đợt luôn kết thúc).

| Boss | Đợt | Pha / đòn | Cửa sổ phản công | Test |
|---|---|---|---|---|
| Siegebreaker Golem (MVP) | 10 | Đập đất, đánh dấu làn | Giáp vỡ | MVP |
| Ignaroth, Bạo Chúa Than Hồng | 10 (pool) | Dung nham báo trước, gọi Ash Imp; <50%: Quá Nhiệt (kháng Lửa, yếu Nước/Băng) | Xả nhiệt định kỳ (Lộ Sơ Hở) | `IgnarothOverheats…` |
| Seraphyne, Nữ Hoàng Mùa Đông | 10 (Frostfall) | Dấu băng dưới chân anh hùng (báo trước 1.8 s, đóng băng 1 s); 60%: 2 Tượng Băng (giảm 45% sát thương); 45%: bão tuyết làm chậm đòn đánh anh hùng quanh 3.2 m | Phá tượng; yếu Lửa; tượng vỡ khi bà ta chết | `SeraphyneRaises…`, `StatuesGuard…` |
| Gravemaw, Titan Công Thành | 10 (Molten pool) | Rất chậm, giáp 70; mỗi 10 s nã 3 phát quanh Pha Lê (báo trước); 50%: phá vây lao lên 3 m (báo trước) | Sau mỗi loạt pháo: xả giáp −60 thủ trong 4 s | `GravemawVents…` |
| Rift Warden (MVP) | 20 | Nhiều pha | MVP | MVP |


### Boss theo mô-đun dữ liệu (`"boss": "generic"`, `Battle.BossesGeneric.cs`)
Mô-đun: dấu đánh dấu anh hùng (báo trước), triệu hồi (có trần), loạt pháo vào Pha Lê (báo trước, luôn kèm cửa sổ lộ sơ hở), quân hộ vệ giảm sát thương, chuyển pha, lộ sơ hở định kỳ (validator bắt buộc).

| Boss | Đợt | Mô-đun | Phản công |
|---|---|---|---|
| Vaelith, Bạo Chúa Bão Tố | 20 / Stormspire | sét đánh dấu (choáng 0.6s), Storm Wisp, pha 50% nhanh hơn | lộ sơ hở mỗi 14s; yếu Đất |
| Mirrath, Nữ Hoàng Gương | 20 / Sunken Archive | phản 15% kỹ năng, Mirror Knight hộ vệ (−40%) ở 70% và 40% | phá hiệp sĩ; yếu Hư Không |
| Aetherion, Pha Lê Sa Ngã | 20 / Shattered Aether | loạt pháo, dấu Huyền Bí, Chaos Elemental; pha 50% thả Riftling | sau mỗi loạt pháo |
| Thornmother | 10 / Sunken Archive | hồi máu (trừ khi Bỏng/Độc), Blight Shambler, dấu gai (choáng 0.8s) | Lửa |
| Ironclad Warlord | 10 / Stormspire | giáp 45, loạt pháo, Goblin Sprinter | sau mỗi loạt pháo −45% |
| Ashen Matriarch | 10 / Shattered Aether | Ash Imp, dấu lửa; pha 40% thả Ember Hound | Nước |
| Nyxhollow, Hư Không Đói Khát | 20 | dấu hư không, Riftling, Rift Summoner hộ vệ ở 60% | Ánh Sáng |

**12/12 boss**. Test `GenericBossModulesFireAndEveryNewBossResolves`: mỗi boss có cảnh báo, cửa sổ lộ sơ hở, đợt luôn kết thúc.
