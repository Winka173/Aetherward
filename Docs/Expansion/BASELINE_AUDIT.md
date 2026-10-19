# Baseline Audit — trước khi mở rộng (Post-MVP)

Ngày: 2026-10-19 · Commit gốc: `e5c5592` (`main`) · Phiên: Claude Code trong cloud container Linux.

Nguồn sự thật là repository, không phải prompt. Mọi con số dưới đây đếm trực tiếp từ `Assets/_Aetherward/Resources/Content/*.json` và từ lệnh đã chạy.

## 1. Môi trường & công cụ (đã kiểm tra bằng lệnh)
| Công cụ | Có? | Dùng cho |
|---|---|---|
| Unity Editor 6000.4.8f1 | **Không** | — mọi thứ cần Editor là `UNVERIFIED` |
| Unity MCP / Blender MCP / image-gen MCP | **Không** có trong phiên | không gọi; dùng script tái tạo được |
| .NET 8 SDK | Có | build + NUnit test lớp mô phỏng (netstandard2.1, C# 9) |
| DLL tham chiếu UnityEngine 2021.3 (NuGet, không commit) | Có | type-check script Unity/Editor (`dotnet build UnityCheck`) |
| Blender 4.0.2 (`/usr/bin/blender`) | Có | dự phòng pipeline 3D→2D (chưa cần) |
| Python 3 + pycairo + numpy + ffmpeg | Có | sprite vector, VFX, UI, âm thanh tổng hợp OGG |
| Git | Có | commit/push `main` (quyền đã được chủ dự án cho) |

## 2. Cấu trúc kỹ thuật thực tế
- Unity 6000.4.8f1, built-in renderer, chỉ module builtin, **Legacy Input Manager**, UI **IMGUI** (không uGUI/TMP/URP/Input System/Test Framework trong manifest — D-01/D-13/D-14).
- Gameplay là thư viện C# thuần `Aetherward.Simulation` (asmdef `noEngineReferences`), tick cố định 1/30 s, RNG PCG32 tách stream. Unity chỉ hiển thị (`Scripts/Unity`).
- Nội dung là **JSON trong `Resources/Content`** với ID chuỗi ổn định (không ScriptableObject, D-03). Hiệu ứng relic/thẻ/tiến hoá là op khai báo.
- Scene: Boot, MainMenu, Battle, Results (marker tối giản; `GameRoot` gắn controller).
- Save: JSON có checksum + backup + migration, `SaveVersion = 2`; các mảng theo nguyên tố (`ElementDamage`) lưu theo ordinal.

## 3. Nội dung hiện có (đếm thật)
| Hạng mục | Số lượng | Ghi chú |
|---|---|---|
| Nguyên tố | 6 | fire, water, lightning, ice, wind, earth |
| Phản ứng | 15 | đủ 15 cặp, logic trong `switch` của `Battle.Damage.cs` |
| Anh hùng | 12 | Ignis, Cinder, Marina, Tidal, Volt, Raiden, Freya, Glacius, Zephyr, Sylph, Terra, Magnus |
| Tiến hoá | 24 | 2/anh hùng |
| Kẻ địch | 15 | gồm 1 elite (ravager), 2 boss (siegebreaker_golem, rift_warden), 2 summon (swarmling, riftling) |
| Affix | 9 | 6 kháng nguyên tố + hasted/bulwark/unyielding |
| Relic | 28 | 25 thường + 3 hợp thể; 3 công thức fusion |
| Thẻ | 46 | 7 loại (stat, ability, specialization, synergy, reaction, mutation, pact) |
| Wave | 20 | 2 boss (10, 20) |
| Sự kiện | 3 | |
| Arena/biome | 1 | `arcane_sanctuary`, 12 node, 6 lane |
| Chế độ | 1 | Classic 20 đợt |
| Ascension | 0–5 | logic rải rác trong `RunController`/`Battle` (asc≥1 frenzy, ≥2 tốc độ, ≥3 Pha Lê 85%, ≥4 sát thương) |
| Chuỗi dịch | 811 khoá EN + VI | |

## 4. Baseline đã chạy
| Hạng mục | Lệnh | Kết quả |
|---|---|---|
| Test EditMode (ngoài Unity) | `cd Tools/SimHarness && dotnet test Tests` | **64/64 PASS** |
| Type-check Unity + Editor | `dotnet build UnityCheck --no-incremental` | 0 lỗi, 0 cảnh báo |
| Mô phỏng cân bằng | `dotnet run --project Balance -c Release -- --runs 10` | 60 lượt: thunderstorm 4/10, frozen_fortress 8/10, magma_engine 9/10, mixed_burst 7/10, glass_cannon 2/10, balanced 9/10; 0 lượt kẹt |
| Hiệu năng mô phỏng (trước đó) | `--perf` | 20–82 µs/tick TB, đỉnh ~1.8 ms |
| Unity compile/PlayMode/build | — | **UNVERIFIED** (không có Editor) |
| Save/load | test `RunTests` (round-trip, checksum, backup) | PASS |

## 5. Điểm mã cứng ảnh hưởng khi thêm nguyên tố (đã grep)
| Vị trí | Vấn đề | Cách xử lý |
|---|---|---|
| `Enums.cs` `ElementUtil.Count = 7`, `All`, `TryParse`, `Key` | danh sách cứng | enum **append-only** giá trị cố định (Light=7…Void=12); parse/key qua bảng |
| `ElementUtil.PairIndex` = `x*8+y`, mảng 64 | tràn khi >7 | `x*16+y`, mảng 256 (`ElementUtil.PairSlots`) |
| `EnemyUnit.ReactionCooldown[64]`, `ContentDatabase.ReactionByPair[64]` | như trên | dùng `PairSlots` |
| `BattleModifiers.GaugeMult` 7 phần tử | cứng | `new float[ElementUtil.Count]` |
| `ApplyElement` chọn aura mạnh nhất rồi `switch` theo 15 id | không mở rộng | giữ `switch` cho 15 phản ứng gốc (regression), phản ứng mới chạy bằng **op khai báo**; ưu tiên aura theo (lượng, id) tất định |
| Hiệu ứng khi gắn nguyên tố (Fire→Burn, Earth→Crack) viết cứng | không mở rộng | `elements.json` khai báo status khi gắn/làm mới |
| `Ui.ElementColor`, `WorldViews` status icon `switch` | cứng | màu/icon lấy từ dữ liệu nguyên tố |
| `RunState/RunResults/BattleStats.ElementDamage[Count]` | save theo ordinal | ordinal ổn định ⇒ save cũ (7 phần tử) nạp đúng vào 7 ô đầu; có test |
| `ContentDatabase.Arena` duy nhất | không có biome | `arenas.json` nhiều biome, `BattleSetup.Arena` |

## 6. So sánh với kỳ vọng MVP
- Đầy đủ theo code: vòng 20 đợt, 12 node, 6 hero, tuyển mộ, cấp/tiến hoá, auto-combat, thắng/thua, meta, tốc độ 1×/2×, lưu/tiếp tục.
- Chưa kiểm chứng: mọi thứ cần Unity Editor (scene chạy thật, IMGUI trên màn hình thật, build).
- Không có lỗi nền tảng chặn việc mở rộng → tiến hành Phase 1 trên nền hiện có (không viết lại).

## 7. Rủi ro kiến trúc
| Rủi ro | Mức | Giảm thiểu |
|---|---|---|
| Thêm nguyên tố làm đổi hành vi 15 phản ứng cũ | Cao | giữ nguyên code 15 phản ứng; test regression từng cặp; lựa chọn aura tất định giữ kết quả cũ |
| Bùng nổ proc khi nhiều phản ứng/zone mới | Cao | giới hạn thế hệ 2, ngân sách proc/mục tiêu & /tick, trần số zone theo loại, trần stack status |
| 36 hero × UI IMGUI (chọn đội) | Trung bình | lưới có cuộn + lọc nguyên tố |
| Save cũ khi thêm nguyên tố/biome/mode | Trung bình | ordinal ổn định, trường mới có mặc định, test nạp save v2 |
| Không có Unity để xem art/hiệu ứng mới | Cao | contact sheet + composite offline, đánh dấu UNVERIFIED |
| Khối lượng nội dung rất lớn | Cao | theo phase; báo đúng con số thật, không độn |
