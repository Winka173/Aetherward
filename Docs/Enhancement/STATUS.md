# STATUS — Final Gameplay, Art & Balance (báo cáo tiếng Việt)

Unity 6000.4.8f1 **không có** trong môi trường này: mọi mã Unity chỉ được type-check (UnityCheck 0 lỗi), **chưa chạy trong Editor/thiết bị**. Không có ảnh chụp game thật; ảnh trong `Reports/ArtQuality/` là contact sheet render từ sprite ở kích thước màn hình tính toán.

## Ma trận tính năng
| Phase | Trạng thái | Bằng chứng | Còn thiếu |
|---|---|---|---|
| P1 Synergy Vision | DONE WITH EVIDENCE (logic) / PARTIAL (UI) | `Combat/SynergyVision.cs`, `SynergyVisionTests` (4), overlay `BattleController.Ui.cs DrawSynergyVision` | Chưa nhìn overlay trên màn hình; arena không có vật cản tầm nhìn nên LOS = N/A |
| P2 Training Chamber | DONE WITH EVIDENCE (logic) / PARTIAL (UI) | `Run/TrainingChamber.cs`, `TrainingChamberTests` (3), trang `MenuController.Training.cs` | UI chưa chạy thật |
| P3 Visual evolution identity | DONE WITH EVIDENCE (số liệu) | validator `weak_evolution` 22 → 0; `Reports/ArtQuality/before_after/evolution_*.jpg` | Animation cast/âm thanh riêng từng nhánh: NOT STARTED; human review PENDING |
| P4 Boss readability | DONE WITH EVIDENCE (sim) | `BossTelegraphTests`: 12/12 boss, lead tối thiểu 1,17 s; assist 1× khi 2×; preview không spoil | Độ tương phản telegraph trên màn hình chưa kiểm |
| P5 Discovery Codex | DONE WITH EVIDENCE | `Meta/Discovery.cs`, `DiscoveryCodexTests` (3; fixture MVP + id lạ được giữ) | UI journal/toast chưa chạy thật |
| P6 Battle Insights | DONE WITH EVIDENCE | `Run/BattleInsights.cs`, `BattleInsightsTests` (khớp log + replay), mẫu `Reports/RunBreakdown/run_1007.md` | — |
| P7 Feel/audio polish | PARTIAL | toast nhỏ, telegraph assist, flash scale (trước đó) | Anim cast/hit/recover, SFX mới, preset cường độ: NOT STARTED (không kiểm chứng được nếu không có Unity) |
| P8 Art pipeline + quality gate | DONE WITH EVIDENCE | `Tools/ArtPipeline/` (validate + ap.py), 8 self-test, CI job; 258 sprite tạo lại, 62 lỗi chặn → 0; rollback thử thật | 4/8 hướng: không làm (game dùng 1 hướng lật); SpriteAtlas: chỉ kế hoạch; EEVEE BLOCKED |
| P9 Balance lab | DONE WITH EVIDENCE | `--lab` 3780 run, `Reports/Balance/lab/summary.md`; 2 sửa lỗi có A/B (`lab_ascension_ramp.md`) | A5/A10: 0% thắng với mọi bot — chưa sửa (cần quyết định thiết kế + playtest người) |
| Build Windows/Android/iOS | BLOCKED | — | Cần Unity |

## Số liệu chính
- Art: 795 asset, **0 lỗi chặn** (trước: 62), 206 cảnh báo (halo, tương phản khi mật độ phép cao — cần review). Tạo lại tất định (0 khác biệt khi chạy lại); import có backup/journal, rollback khôi phục đúng từng byte.
- Blender: benchmark Pha lê render được (Cycles CPU) nhưng **REWORK — không dùng** vì kém dễ đọc hơn bản 2D.
- Bot A0 (30 seed × 6 biome): 0,6% (boss_burst) … 24,4% (random). Auto Arrange sửa đường bỏ trống: stall 6,1% → 22,8%.
- Ascension ramp: A10 chết ở đợt ≤2 từ 843 → 336/1260; A0 không đổi.
- Test: C# 221/221, Python 8/8, UnityCheck 0 lỗi.

## Lệnh tái lập
```
dotnet test Tools/SimHarness/Tests
dotnet build Tools/SimHarness/UnityCheck
python3 -m unittest discover -s Tools/ArtPipeline/tests
python3 Tools/ArtPipeline/validate.py
python3 Tools/ArtPipeline/ap.py generate && python3 Tools/ArtPipeline/ap.py diff && python3 Tools/ArtPipeline/ap.py import
python3 Tools/ArtPipeline/ap.py render --stage Temp/ArtStageBlender --only crystal
dotnet run --project Tools/SimHarness/Balance -c Release -- --lab --seeds 30
```

## Blocker còn lại
1. Không có Unity Editor/thiết bị: chưa xem UI/overlay/toast, chưa đo FPS/bộ nhớ, chưa build.
2. Không có playtest người thật; lifts/tỉ lệ thắng là của bot.
3. A5/A10 quá khó với mọi bot; 35% run chạm trần proc — cần review thiết kế.
4. EEVEE (libEGL) không chạy; SpriteAtlas chưa tạo.
