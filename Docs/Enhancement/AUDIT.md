# Audit — Gameplay Feel, Roguelike Depth & Operations

Ngày: 2026-10-19 · Commit gốc: `0981b4d` (sau mở rộng hậu MVP).

## 1. Môi trường & công cụ (đã kiểm tra)
| Mục | Thực tế |
|---|---|
| Unity | 6000.4.8f1 (`ProjectSettings/ProjectVersion.txt`). **Không có Unity Editor trong môi trường này** — không chạy được Play Mode, Profiler, build. |
| Render pipeline | Built-in, IMGUI cho UI, Legacy Input; package: chỉ module Unity cơ bản (không URP/2D packages) |
| Nền tảng đích | Windows, Android, iOS (script build có trong Editor menu, **chưa build lần nào**) |
| CI | Không có `.github/workflows` |
| Kiểm thử | 165 test EditMode chạy qua .NET 8 (`Tools/SimHarness/Tests`, compile cùng file nguồn với Unity); UnityCheck type-check script Unity với DLL tham chiếu 2021.3 |
| Mô phỏng | `Tools/SimHarness/Balance` dùng **chính mã mô phỏng của game** (C# thuần, tick 1/30 s, PCG32 theo stream) |
| Máy | 4 vCPU Intel Xeon 2.10 GHz, 15 GB RAM, .NET 8.0.131, Linux container |
| MCP | Không có Unity/Blender MCP. Có Python (pycairo) cho art thủ tục |

## 2. Kiến trúc gameplay (thực tế từ mã)
- **Tách lớp**: `Scripts/Simulation` (thuần C#, không MonoBehaviour) ↔ `Scripts/Unity` (trình bày IMGUI + SpriteRenderer). Unity chỉ đọc `SimEvent` journal và trạng thái → trình bày không thể đổi kết quả trận.
- State machine lượt chơi: `RunController` (Prepare → Battle → Reward → … → Victory/Defeat), `RunState` lưu được.
- Trận: `Battle` (partial: Damage, Effects, Heroes, Enemies, Statuses, ReactionOps, Biomes, Bosses…), tick cố định, `SpatialGrid` cho truy vấn, pool kẻ địch.
- RNG: `Pcg32.Derive(seed, "label")` — stream riêng cho battle, spawns, offers, traits, boss, hazard, awakening, run pool. **Trình bày dùng RNG riêng của Unity**.
- Chọn mục tiêu: `SelectTarget(h, TargetProfile)` — hồ sơ cố định (Nearest, NearestToCrystal, Cluster, Elite, Execute, ReactionOpportunity, Strongest), có retarget timer; **chưa có điểm utility có thể soi**, chưa có preset chiến thuật.
- Sát thương/hồi/khiên/trạng thái/phản ứng: một đường duy nhất (`DealDamage`, `DamageHero`, `HealHero`, `AddHeroShield`, `ApplyElement`, `ApplyStatus`, `ExecuteAction`) — mọi relic/thẻ/bond đi qua `BattleModifiers`.
- Nội dung: JSON trong `Resources/Content` (+ `ContentValidator`), không dùng ScriptableObject.

## 3. Tồn kho nội dung (sinh từ dữ liệu, xem `Docs/CONTENT_CATALOG.md`)
12 nguyên tố · 40 phản ứng (35 đặc trưng) + chung tự sinh, 66 cặp có phân loại · 36 hero / 72 tiến hoá · 12 trait · 12 bond · 52 kẻ địch (12 boss) · 6 biome · 81 relic (11 hợp thể, 12 keystone) · 80 thẻ · 4 sự kiện · Ascension 1–10 · 4 chế độ. Validator: 0 lỗi; mọi sprite/âm thanh nội dung tồn tại; 0 ID trùng (Add() ném lỗi khi trùng).

## 4. Trải nghiệm & điểm nghẽn đã biết
- Thắng (AutoPilot, toàn bộ nội dung) ≈ 11%; pool khởi đầu ≈ 52% (K-04). Nhạy với hình học làn (K-07).
- Phần thưởng mỗi đợt có thể là 2–3 màn hình liên tiếp (draft + recruit + shop…); chưa đo thời gian trong menu.
- Chưa có tutorial theo ngữ cảnh mới (có `TutorialDone` flag + tutorial cơ bản MVP).
- Cài đặt có: âm lượng, tốc độ mặc định, Reduced VFX, rung màn hình, số sát thương, tương phản cao, FPS mục tiêu, hiển thị tầm. **Thiếu**: cường độ flash, mật độ số sát thương, pause khi mất focus (chỉ có OnApplicationPause), battery saver, colorblind shapes.
- Save: JSON có version + checksum + file backup + ghi tạm rồi rename (Unity). **Thiếu**: xoay vòng nhiều backup, fixture save cũ trong test.
- Số đo hiệu năng: chỉ có `--perf` headless (ms/tick mô phỏng). **Không có số đo FPS/GC/draw call thật**.

## 5. Ánh xạ đề xuất
| Phase | Trạng thái hiện có | Rủi ro | Ghi chú |
|---|---|---|---|
| 1 Juice | partial (FX pool, floating text cap 48, shake, reduced VFX) | trung bình | thiếu gộp số sát thương, tầng VFX, flash intensity; **không thể kiểm bằng mắt** |
| 2 AI utility + inspector + preset | partial (profile cố định) | cao (ảnh hưởng cân bằng) | kiểm được headless |
| 3 Build UX / preview | partial (HeroDetail, evo panel) | trung bình | |
| 4 Draft/shop công bằng | partial (relevance guarantees, reroll) | thấp | thiếu pity, khoá/banish, test xác suất |
| 5 Formation & Crystal Evolution | missing | trung bình | feature flag |
| 6 Encounter director | partial (waves dữ liệu, time limit, breach) | trung bình | thiếu log ngân sách spawn |
| 7 UI/UX/A11y | partial | — | không kiểm được trên thiết bị |
| 8 Run breakdown | partial (RunResults: MVP, defeat source, strongest reaction, history) | thấp | thiếu nguồn gốc sát thương theo loại, closest save |
| 9 Authoring tools | partial (validator + menu Editor) | thấp | thiếu báo cáo CI, kiểm đồ thị proc |
| 10 Balance sim | partial (harness dùng mã thật, 30 seed) | thấp | thiếu 1000 seed, policy, CI, outlier |
| 11 Performance | **blocked** cho số đo thật (không có Unity/thiết bị) | — | chỉ đo được mô phỏng headless |
| 12 Save/ops | partial | thấp | thiếu fixture, xoay vòng backup, feature flags |
| 13 Playtest | **blocked** (không có người chơi thật) | — | chỉ chuẩn bị giao thức |

## 6. Baseline tái lập
`cd Tools/SimHarness && dotnet test Tests` (165/165) · `dotnet build UnityCheck` (0 lỗi) · `dotnet run --project Balance -c Release -- --runs 30` (số liệu trong `Docs/Expansion/BALANCE_REPORT.md`). Rollback: mọi bước là commit riêng trên `main`.
