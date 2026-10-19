# Biomes (chiến trường chức năng)

Dữ liệu: `Assets/_Aetherward/Resources/Content/biomes.json`. Mã: `Battle.Biomes.cs`, `ContentDatabase.LoadBiomes`, `ContentValidator.CheckBiomes`.

Quy tắc chung (validator kiểm tra):
- Mỗi biome có đúng **12 ô phòng thủ** và **6 slot làn** (các đợt trong `waves.json` tham chiếu slot 0–5); điểm cuối mỗi làn phải nằm sát Pha Lê.
- Hiểm hoạ luôn **có báo trước** (≥0.8 s), trúng cả anh hùng lẫn kẻ địch, gây cho anh hùng tối đa 25% HP tối đa mỗi lần (`heroDamagePct`), không đặt chồng lên Pha Lê.
- Đặc tính ô chỉ được dùng op `stat` (không có cơ chế ẩn).
- Tường/che chắn không bao giờ chặn hoàn toàn làn (test `WallsOnEveryLaneSlowButNeverBlockThePath` đặt tường ở mọi điểm rẽ của mọi làn ở mọi biome).
- Boss pool riêng chỉ được đặt trên đợt boss và chỉ chứa boss; kẻ địch thêm không được là boss.

| Biome | Bố cục | Hiểm hoạ | Ô đặc biệt | Kẻ địch thêm | Boss đợt 10 | Mở khoá |
|---|---|---|---|---|---|---|
| Verdant Sanctuary (mặc định) | 6 làn thoáng (bản đồ MVP) | — | — | — | Siegebreaker / Ignaroth (theo seed) | Có sẵn |
| Molten Crater | Hai cầu bazan: làn Đông+Đông Bắc và Tây+Tây Nam đi chung đoạn qua cầu | Lỗ dung nham: mỗi 9 s phun 2 điểm, báo trước 1.6 s, bán kính 1.3 m, 12% HP anh hùng | Cầu nóng (ô 4, 5, 8, 9): +15% công | Flame Devourer (đợt 6–19) | Ignaroth / Gravemaw | Đạt đợt 7 |
| Frostfall Bastion | Pháo đài; cổng chéo (làn 4/5) chỉ mở từ đợt 8, trước đó dồn sang Đông/Tây | — | Ô băng (4, 6, 8, 10): +25% thủ, đánh chậm hơn 12% | Frost Wraith (đợt 7–19) | Seraphyne | Đạt đợt 11 |

| Shattered Aether | Bố cục làn mặc định (đảo trôi) | Khe nứt aether: mỗi 10s mở 2 điểm, báo trước 1.6s, kéo kẻ địch lại, 8% HP anh hùng | Ô aether (5, 7, 9, 11): +40 Tinh Thông | Chaos Elemental (8–19) | Đ10: Ashen Matriarch; Đ20: Aetherion / Nyxhollow | Thắng 1 lượt |
| Stormspire Citadel | Bố cục làn mặc định (đỉnh bão) | Sét đánh: mỗi 7s 3 điểm, báo trước 1.4s, 10% HP anh hùng | Cột thu lôi (4, 6, 8, 10): đánh nhanh +10% | Storm Wisp (6–19) | Đ10: Ironclad Warlord; Đ20: Vaelith | Đạt đợt 17 |
| Sunken Archive | Bố cục làn mặc định; cầu thang bắc/nam ngập tới đợt 6 | Sóng triều: mỗi 10s 2 điểm, báo trước 1.8s, đẩy lùi kẻ địch, 7% HP anh hùng | Sách cổ (5, 7, 9, 11): hồi chiêu −10% | Arcane Mimic (9–19) | Đ10: Thornmother; Đ20: Mirrath | Đạt đợt 14 |

Che chắn băng (Frostfall): 4 tấm `ice_cover` (bán kính 1 m), mỗi tấm đỡ 8 phát đạn địch rồi vỡ (`Zone.HitsLeft`).

Unity: chọn chiến trường ở màn chọn đội (khoá hiển thị điều kiện mở), nền theo biome (`World/bg_<id>`), màu ô theo đặc tính, cảnh báo hiểm hoạ màu đỏ, bảng chuẩn bị hiển thị tên biome + đặc tính ô + kẻ địch thật của đợt (gồm boss đã chọn và kẻ địch thêm). Trạng thái: **IMPLEMENTED_UNVERIFIED** (chưa mở Unity).

Art: `Tools/AssetGen/art/world.py` vẽ nền từ đúng toạ độ làn/ô/lỗ dung nham trong `biomes.json`; xem `Docs/Previews/bg_molten_crater.png`, `bg_frostfall_bastion.png`.

## Cân bằng (mô phỏng, 20 seed × 9 lối chơi)
| Biome | Tổng thắng |
|---|---|
| Verdant (30 seed) | 80/270 (~30%) |
| Molten Crater | 55/180 (~31%) |
| Frostfall Bastion | 52/180 (~29%) |

Lần đo đầu Molten chỉ 2/180: ô phòng thủ đặt xa làn. Đã dời ô về gần làn (giữ cầu nóng ở đầu cầu) → 55/180. Đây là ví dụ cho việc biome mới phải được đo, không đoán.

## Phase 4c: 3 biome mới (15 seed × 12 lối chơi, `--launch-pool`)
| Biome | Thắng |
|---|---|
| Verdant (tham chiếu) | 54/180 |
| Molten Crater | 61/180 |
| Shattered Aether | 56/180 |
| Stormspire Citadel | 46/180 |
| Sunken Archive | 57/180 |

**Phát hiện**: với làn tự thiết kế, Stormspire/Sunken chỉ 17–18/180; bisect cho thấy không do hiểm hoạ, kẻ địch thêm, đặc tính ô hay boss mà do **hình học làn** (cùng biome dùng bố cục mặc định: 46/180). Các biome mới vì vậy dùng làn mặc định; bản sắc nằm ở hiểm hoạ/ô/kẻ địch/boss/hình nền. Mọi thay đổi làn sau này phải đo lại (K-07).
