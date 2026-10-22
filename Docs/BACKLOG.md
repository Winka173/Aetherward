# Aetherward: việc còn lại

Cập nhật 2026-10-22. Nhánh `art/b01-benchmark`, commit mới nhất `513b3ee`.

Cách đọc:
- **[GAME]** là việc gameplay hoặc code.
- **[ART]** do tool khác làm sau. Phần này chỉ ghi yêu cầu kỹ thuật và hợp đồng file để tool đó làm đúng.
- **[TECH]** là pipeline, công cụ, dọn dẹp.

## 0. Trạng thái hiện tại (đã xong)
- **Gameplay Dynamic Party:** hero di chuyển theo vai trò, có 3 stance và ultimate theo nguyên tố.
- **Map pháo đài (Haven):** hiện chỉ có biome `verdant_sanctuary`. Gồm tường, 3 cổng, quái dồn chậm ở cổng, cướp phá khi lọt vào sân. 231/231 test EditMode đạt.
- **Hệ hiển thị:** camera gần hơn có tracking và ưu tiên cổng nam, unit to hơn, chuyển động mượt, hoạt ảnh nhiều pose (walk 4 pose, windup/strike/follow, thở), VFX nhiều lớp, sương, bụi sáng, HUD mới.
- **Art benchmark đã vào game:**
  - R01: 4 hero, 4 quái, elite, boss.
  - R02: VFX.
  - R03: HUD.
  - R05: 25 frame hoạt ảnh hero.
  - Nền pháo đài tạm vẽ bằng SDXL.
- **Bằng chứng:** ảnh Unity thật trong `Reports/ArtQuality/` (R01_*, R02_bursts, R03_hud, R07_ultimates, H01_haven, H02_haven_paint).

## 1. Gameplay [GAME], ưu tiên cao
1. **Haven cho 5 biome còn lại:** molten_crater, frostfall_bastion, shattered_aether, stormspire_citadel, sunken_archive.
   - Mỗi biome cần một arena `walk` / `walls` / `gate` trong `Resources/Content/biomes.json`, theo mẫu `verdant_haven`.
   - Giữ bản sắc từng biome: hazard, cover, lane mở dần theo wave.
   - Khi đã có tọa độ hazard mới thì kiểm lại `hazards` và `covers`.
2. **Bỏ hẳn hệ 12 node cũ.** Node hiện chỉ còn là đội hình xuất phát. Việc cần làm:
   - đổi UI kéo-thả thành chọn đội hình hoặc stance (`BattleController.HandlePlacementInput`, `SyncPrepViews`, `UpdateNodes`);
   - bỏ yêu cầu "đúng 12 node" trong `ContentValidator`;
   - đổi module Ascension `blocked_node` thành dạng khác, ví dụ "cổng bị phong ấn";
   - đổi `nodeTraits` thành vùng (area traits);
   - viết lại phần chấm điểm node trong `AutoPilot` và `TrainingChamber`;
   - save vẫn đọc `"node"` của save cũ để tương thích.
3. **Synergy Vision và báo cáo lane** đang tính theo node (`SynergyVision.cs`, panel Incoming báo "lane covered"). Cần đổi sang theo cổng và stance.
4. **Balance sau Haven** (bot, 240 run mỗi stance):

   | Stance | Thắng |
   |---|---|
   | Giữ thành | 46 |
   | Giữ cổng | 41 |
   | Xuất kích | 32 |
   | Mốc cũ | khoảng 38 |

   - Cần chạy lại khi đã có Haven cho mọi biome.
   - Lệnh: `dotnet Tools/SimHarness/Balance/bin/Debug/net8.0/Aetherward.Balance.dll --runs 20 --stance <X>`, rồi tổng hợp bằng `ArtCache/benchsum.py`.
   - Các núm chỉnh: `Battle.Party.cs` (PillageRate, GateSlow, DefensiveHold, GateHoldDamage, AggressiveMomentum, SallyGoldPct), `Battle.Ultimates.cs` (UltPower, UltSeconds), `economy.json` (`enemyHpMult` 1.25).
5. **AI party còn yếu:**
   - Ở stance Cân bằng, hero vẫn hay tụ quanh bệ crystal.
   - Chưa có tìm đường quanh vật cản: hero chỉ bị kẹp trong các hình chữ nhật đi được.
   - Chưa có lựa chọn "Split / Boss Focus / Swarm" như master prompt gợi ý.
6. **Ultimate:**
   - Chưa có ultimate riêng cho từng hero; hiện mới theo nguyên tố.
   - Chưa có mô tả trong UI và tooltip.
   - Chưa có âm thanh riêng; đang tạm dùng `react_explosion`.
7. **Feel:**
   - Dock hero còn che sân trước cổng nam. Cần thu nhỏ hoặc cho dock tự ẩn khi đánh.
   - Cảnh báo "Crystal bị cướp phá" khi quái lọt vào sân cần hiện rõ hơn.
8. **Test và kiểm định:**
   - Chưa chạy lại PlayMode test sau khi đổi map.
   - Cần viết test cho Haven: hero không xuyên tường, quái chậm ở cổng, pillage.
   - Cần kiểm hiệu năng khi quái đông với VFX nhiều lớp.

## 2. Art [ART], tool khác làm
Hợp đồng kỹ thuật bắt buộc: `ArtHandoff/requests/COMMON_CONTRACT.md` (mục 4–10), style ở `ArtProduction/ART_BIBLE.md` v3.

Quy trình nhập:
1. Tool đặt file vào `ArtHandoff/returns/<batch>/exports/Art/...`.
2. Chạy `python Tools/ArtPipeline/handoff.py intake --batch <B>`.
3. Chạy `handoff.py stage --batch <B>`.
4. Chạy `ap.py import --stage ArtCache/ArtStage-import-<B>`.

Batch nào chưa có `requests/<B>/INPUT_MANIFEST.json` thì phải chạy `handoff.py request --batch <B>` trước.

1. **Nền pháo đài vẽ tay (R07):** thay bản SDXL tạm.
   - Brief: `ArtHandoff/requests/R07/CODEX_ART_REQUEST.md`.
   - Bản dẫn đường khóa tường, cổng và lane: `ArtHandoff/requests/R07/references/haven_guide.png`.
   - Hoàn thiện ảnh: `python Tools/ArtPipeline/paint_finish.py --paint <png> --asset World/arena_background --env-from Assets/_Aetherward/Resources/Art/World/arena_background_env.json`.
   - Cần thêm nền pháo đài cho 5 biome kia sau khi làm xong mục 1.1.
2. **Hoạt ảnh quái và boss (R05 phần còn thiếu):** 12 frame bị chặn vì Codex hết hạn mức.
   - Gồm `Enemies/<grunt|runner|hexcaster|juggernaut|ravager>_c/_d/_windup` và `rift_warden_c/_d`.
   - Brief: `ArtHandoff/requests/R05/CODEX_ART_REQUEST.md`.
3. **Sản xuất hàng loạt theo style v3** (chỉ làm sau khi chủ dự án duyệt benchmark):
   - **Hero:** 32 hero còn lại. Mỗi hero cần idle, walk_a/b/c/d, windup, attack, follow, cast, downed, idle_b, evoA/evoB (+cast/attack) và portrait.
   - **Quái thường:** khoảng 30, mỗi con a/b/c/d, windup, attack.
   - **Boss:** 11, mỗi con a/b/c/d, tell, attack.
   - Thiết kế từng nhân vật: `ArtProduction/designs/heroes.json`, `enemies.json`.
   - Các batch B04–B17 cũ là style v2, đã bỏ. Chỉ dùng phần danh sách asset của chúng.
4. **VFX còn lại:**
   - Impact và projectile cho các nguyên tố chưa có: wind, earth, light, shadow, void, arcane, nature, poison.
   - Khoảng 40 sprite `field_*` và `zone_*`.
   - Hình nổ vẽ tay `burst_<element>` cho các nguyên tố ngoài lửa, băng, sét, nước. Ultimate của các nguyên tố này đang dùng khói hoặc sương thay tạm.
5. **Icon:** reaction, relic, card, element theo style v3.
6. **Thử nghiệm 3D (tùy chọn):** ảnh A-pose của Glacius đã có ở `ArtHandoff/returns/R06/exports/`. Bản cài TRELLIS.2 local ở `C:\Users\Winka\Tools\trellis2` chưa cài xong (xem mục 3).

## 3. Kỹ thuật và dọn dẹp [TECH]
1. **TRELLIS.2:** lần cài cuối bị dừng khi đang tải model.
   - Chạy lại khối lệnh cài trong `C:\Users\Winka\Tools\trellis2\server.log`, hoặc chạy `tools\projectorz-internal.bat` từ thư mục `tools`.
   - Cần khoảng 30 GB trống.
   - Nếu art sẽ do tool khác làm thì có thể bỏ việc này.
2. **Dung lượng:** `D:\hf_cache` là cache thừa, bị chặn xóa tự động nên cần xóa tay. Ổ D đang gần đầy.
3. **Blender pipeline:**
   - `Tools/ArtPipeline/blender/sanctum_env.py` hỗ trợ cả map mở lẫn Haven (bật khi arena có `walls`).
   - `toon_pass.py` tự xóa các pass EXR sau khi render.
   - Pipeline vẽ lại local: `sdxl_paint.py`, chạy bằng venv `C:\Users\Winka\Tools\sdxl`.
4. **Artifact chưa commit:** `Docs/ASSET_MANIFEST.json` và thư mục `ArtHandoff/returns/` (bản gốc từ Codex) chưa được commit. Cần quyết định lưu ở đâu.
5. **Merge:** nhánh `art/b01-benchmark` chưa merge vào `main`. Nên review và tạo PR khi benchmark được duyệt.
