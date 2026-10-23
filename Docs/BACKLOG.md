# Aetherward: việc còn lại

Cập nhật 2026-10-23. Gameplay Haven và toàn bộ artifact của nhánh `art/b01-benchmark` đã được đưa vào đợt bàn giao `main` theo yêu cầu chủ dự án. Báo cáo: `Reports/Haven/IMPLEMENTATION.md`.

Cách đọc:
- **[GAME]** là việc gameplay hoặc code.
- **[ART]** do tool khác làm sau. Phần này chỉ ghi yêu cầu kỹ thuật và hợp đồng file để tool đó làm đúng.
- **[TECH]** là pipeline, công cụ, dọn dẹp.

## 0. Trạng thái hiện tại (đã xong)
- **Gameplay Dynamic Party:** 3 stance, 3 đội hình (Split / Boss Focus / Swarm), vị trí chuẩn bị lấy từ planner chiến đấu. 36 hero có cấu hình ultimate riêng, tên/mô tả EN/VI và 12 cue âm thanh nguyên tố.
- **Map pháo đài (Haven):** cả 6 biome có walk / walls / gate; giữ hazard, cover và lịch mở lane. Tìm đường qua cổng, chặn dash xuyên tường, quái ground chậm ở cổng và cướp phá có nguồn sát thương. **240/240 test EditMode qua .NET harness đạt**; PlayMode chưa chạy được vì Unity thiếu license hợp lệ.
- **Hệ hiển thị:** camera gần hơn có tracking và ưu tiên cổng nam, unit to hơn, chuyển động mượt, hoạt ảnh nhiều pose (walk 4 pose, windup/strike/follow, thở), VFX nhiều lớp, sương, bụi sáng, HUD mới.
- **Art benchmark đã vào game:**
  - R01: 4 hero, 4 quái, elite, boss.
  - R02: VFX.
  - R03: HUD.
  - R05: 25 frame hoạt ảnh hero.
  - Nền pháo đài tạm vẽ bằng SDXL.
- **Bằng chứng:** ảnh Unity thật trong `Reports/ArtQuality/` (R01_*, R02_bursts, R03_hud, R07_ultimates, H01_haven, H02_haven_paint).

## 1. Gameplay [GAME]
- [x] **Haven cho 5 biome còn lại:** molten_crater, frostfall_bastion, shattered_aether, stormspire_citadel, sunken_archive. Tọa độ hazard/cover được đặt lại; test kiểm tra vùng đi và đường qua từng cổng. Nền art tương ứng vẫn chờ mục 2.
- [x] **Thay UI 12 node:** chuẩn bị bằng stance/đội hình, bỏ kéo-thả và sprite node; bỏ validator đúng 12 node; bot không chấm điểm node. Slot/API node cũ chỉ giữ cho save và test benchmark tương thích.
- [x] **Ascension `sealed_gate`:** thay `blocked_node`; chọn cổng đang dùng theo seed/wave, chuyển nhóm địch sang lối khác, hiển thị cổng bị phong ấn và lưu save.
- [x] **Area traits:** bonus phụ thuộc vị trí hiện tại, tự mất khi rời vùng. Các trường `node` của save cũ vẫn được đọc.
- [x] **Synergy Vision / Incoming / Insights:** dùng cổng vật lý và stance; bốn lane vào cổng nam được gom chung; giải thích sát thương pillage theo nguồn. Coverage là dự báo tầm giao chiến, không đảm bảo chặn hết địch.
- [x] **AI:** pathfinding qua vùng nối; kiểm tra clearance cả segment di chuyển/dash; Balanced đứng gần cổng hơn; Split / Boss Focus / Swarm điều khiển phân bổ tuyến đầu. Training Chamber có cùng lựa chọn stance/đội hình.
- [x] **Ultimate:** 36 cấu hình riêng với 7 kiểu thi triển, số đòn/bán kính/tích năng lượng/CC/hồi máu/khiên khác nhau; tên/mô tả EN/VI ở chi tiết và tooltip; 12 cue tổng hợp nguyên bản. Art burst còn thiếu vẫn ở mục 2.4.
- [x] **Feel code:** dock chiến đấu thu từ 150 xuống 80 UI unit mỗi chân dung; cảnh báo cướp phá hiển thị rõ số địch trong sân. Cần xác nhận bố cục trên Unity/mobile khi chạy được Editor.
- [x] **Balance chạy lại:** 240 run mỗi stance, tổng 720, xoay đủ 6 biome với cùng seed/biome giữa stance. Giữ thành **66/240**, Giữ cổng **83/240**, Xuất kích **68/240**. Xem `Reports/Haven/BALANCE_SUMMARY.md` và CSV từng stance. Đây là baseline mới, không so trực tiếp với mốc chỉ Verdant cũ; chưa tinh chỉnh để ép về tỷ lệ cũ.
- [x] **Test mô phỏng:** 240/240 đạt; gồm Haven, không xuyên tường/dash, gate slow và ngoại lệ flyer, pillage/source log, area trait, formation, ultimate và save tương thích. Log `Reports/haven-editmode-tests.txt`.
- [x] **Compile Unity/Editor:** 0 lỗi, 0 cảnh báo với DLL Unity 6000.4.8f1; `Reports/haven-unity-compile.txt`.
- [x] **Probe hiệu năng mô phỏng:** 160 quái × 6 biome, p95 0,55–3,21 ms/tick trên .NET desktop. Xem `Reports/Haven/PERF.md`; không bao gồm VFX/render/audio và không thay cho đo thiết bị.
- [ ] **PlayMode:** đã thử chạy batchmode, Unity trả exit 198: `No valid Unity Editor license found`. Log `Logs/haven-playmode.log`. Cần kích hoạt license Editor hợp lệ rồi chạy lại test PlayMode.
- [ ] **Kiểm định hình ảnh/thiết bị:** đo frame time/GC với VFX nhiều lớp, kiểm dock/cảnh báo/tooltip trên desktop và mobile. Chưa thể xác nhận khi PlayMode bị chặn.
- [ ] **Duyệt balance:** review chênh lệch theo biome/chiến thuật trong CSV, nhất là nhóm nature/poison và Stormspire; chỉ retune khi có mục tiêu tỷ lệ thắng được thống nhất.

Lệnh tái tạo:

```powershell
dotnet test Tools/SimHarness/Tests
dotnet build Tools/SimHarness/Balance -c Release
dotnet Tools/SimHarness/Balance/bin/Release/net8.0/Aetherward.Balance.dll --runs 20 --stance Balanced --biome all --out Reports/Haven/Balance/Balanced
```

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
   - Cần thêm nền pháo đài cho 5 biome kia. Gameplay đã xong; guide + hình học + brief trong `ArtHandoff/requests/HAVEN_BIOMES/`. Art cũ của 5 biome chưa khớp tường/cổng Haven.
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
   - **Tạm bỏ trong đợt gameplay này:** art do tool khác làm theo mục 2; không tiếp tục tải model ngoài repo.
2. **Dung lượng:** `D:\hf_cache` là cache thừa, bị chặn xóa tự động nên cần xóa tay. Ổ D đang gần đầy.
3. **Blender pipeline:**
   - `Tools/ArtPipeline/blender/sanctum_env.py` hỗ trợ cả map mở lẫn Haven (bật khi arena có `walls`).
   - `toon_pass.py` tự xóa các pass EXR sau khi render.
   - Pipeline vẽ lại local: `sdxl_paint.py`, chạy bằng venv `C:\Users\Winka\Tools\sdxl`.
4. **Artifact:** quy ước lưu ở `Docs/ARTIFACT_STORAGE.md`: manifest/runtime trong Git, bản gốc giữ tại `ArtHandoff/returns/<batch>/`, cache tại `ArtCache/`. Toàn bộ artifact art hiện có được commit cùng đợt bàn giao này theo yêu cầu chủ dự án; cache bị Git bỏ qua vẫn ở local.
5. **Bàn giao main:** chủ dự án yêu cầu commit và push toàn bộ lên `main` ngày 2026-10-23. Việc sản xuất art hàng loạt vẫn chờ duyệt benchmark; đưa code lên main không tự đánh dấu art hoặc PlayMode đã nghiệm thu.
