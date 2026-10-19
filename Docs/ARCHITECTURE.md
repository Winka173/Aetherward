# Kiến trúc

## Ranh giới phụ thuộc
```
Aetherward.Simulation (pure C#, noEngineReferences, netstandard2.1 / C# 9)
   Core      Pcg32, Vec2, JsonNode
   Content   Definitions, ContentDatabase (JSON → defs), Localization, EffectDescriber, ContentValidator
   Combat    Battle (partial: Damage/Heroes/Enemies/Effects), HeroFactory, BattleModifiers, SpatialGrid, CombatJournal
   Run       RunState, RunController, DraftGenerator, RunResults, AutoPilot (+Formation)
   Meta      MetaProfile, SaveService (+ISaveStorage), SettingsModel
        ▲
Aetherward.Game (Unity runtime, IMGUI)
   Core      GameRoot (bootstrap, scene flow), App (services), FileSaveStorage, Art (Resources cache), AudioService
   UI        Ui (virtual 1080p layout kit), SharedPanels
   Menu      MenuController, ResultsController
   Battle    BattleController (+.Ui), WorldViews (UnitView, FxSystem, FloatingText), DebugOverlay
        ▲
Aetherward.Editor   Validate Content and Art, Rebuild Scenes, texture postprocessor, Build/*
Tests              EditMode (NUnit, chạy được cả trong Unity lẫn dotnet), PlayMode smoke test
```
UI chỉ đọc state và gọi lệnh của `RunController` (PlaceHero, Revive, RepairCrystal, Evolve, StartWave, Choose, Reroll, Skip, Abandon); mọi lệnh tự kiểm tra pha/chi phí và trả `false` thay vì ném lỗi.

## Mô phỏng
- **Tick cố định 1/30 s**, RNG PCG32 tách stream theo hệ thống (`battle:N`, `spawns:N`, `draft:N:rerolls`, …) → cùng seed cho cùng kết quả trên cùng nền tảng (float, không fixed-point). 2× = nhiều tick hơn mỗi khung hình, kết quả giống 1× (test `TwoTimesSpeedIsJustMoreTicks`).
- **Thứ tự sát thương** (Battle.Damage.cs): `Công × hệ số → (1 + bonus) → chí mạng (≤75%, ≤4×) → 100/(100+Thủ hiệu dụng) → (1 − kháng, kẹp −50%…75%) → dễ tổn thương → khiên → HP`. Phản ứng bỏ qua Thủ.
- **Phản ứng & proc:** generation cap 2, cooldown theo cặp trên từng mục tiêu, ngân sách 6/s/mục tiêu và 48/tick toàn trận; danh sách tạm thuê từ pool để phản ứng lồng nhau không ghi đè lên nhau.
- **Hiệu ứng khai báo:** di vật/thẻ/tiến hoá là danh sách op (`stat`, `crystal`, `enemy`, `reaction`, `gauge`, `healing`, `economy`, `trigger`, `rule`, `skill`, `card`). Combat chỉ đọc op, không đọc tên di vật. `BattleModifiers` được dựng lại mỗi đợt từ `RunState` → không có buff "ma" giữa đợt/lượt.
- **Hiệu năng:** spatial grid 1.5 m dựng lại mỗi tick, truy vấn không cấp phát; tìm mục tiêu giới hạn 40 ứng viên, so sánh uid để quyết định hoà; giới hạn kẻ địch đồng thời 160 (giãn nhịp spawn, không xoá kẻ địch); journal ≤2048 sự kiện/khung. Đo: `Balance/PERF.md`.

## Trình bày (Unity)
- `GameRoot` tạo bởi `[RuntimeInitializeOnLoadMethod(BeforeSceneLoad)]`, sống xuyên scene, gắn controller theo tên scene (Boot/MainMenu/Battle/Results). Nếu scene không có trong Build Settings thì đổi controller tại chỗ → chạy được cả trong scene trống.
- Mọi sprite nạp qua `Resources.Load<Sprite>("Art/…")`; mọi view được pool (UnitView, projectile, zone, telegraph, FX). Shader `Aetherward/SpriteFlash` cho hit flash; MaterialPropertyBlock chỉ gán khi đang nháy để giữ batching.
- IMGUI: layout ảo cao 1080 trong safe area, cỡ chữ tính theo pixel thật mỗi khung (chữ sắc nét), nút ≥ 88 px ảo (~44 dp), không có thông tin chỉ hiện khi hover (mọi chi tiết mở bằng chạm).
- Lưu: `persistentDataPath/saves/{meta,run,settings}.json`, ghi file tạm rồi thay thế, bản `.bak`, checksum FNV, phiên bản + migration (v1→v2). File hỏng → dùng `.bak` → hồ sơ sạch (báo trên menu).

## Dữ liệu & ID
Nội dung trong `Assets/_Aetherward/Resources/Content/*.json` với ID chuỗi ổn định; chuỗi hiển thị qua khoá `hero.<id>.name`, `card.<id>.desc`, … Tooltip sinh từ dữ liệu (`Localization.Fill`, `EffectDescriber`). `ContentValidator` kiểm tra tham chiếu chéo, giới hạn giá trị, nhánh tiến hoá, tên op/trigger/rule, độ phủ bản dịch en/vi và tooltip không còn token `{…}`.

## Pipeline asset
`Tools/AssetGen/art/build_all.py` (pycairo) → PNG + `import_settings.json` → `Tools/gen_meta.py` tạo `.meta` với GUID tất định (md5 đường dẫn); `AetherwardTexturePostprocessor` áp lại pivot/PPU/9-slice khi import. `Tools/AssetGen/audio/build_audio.py` (numpy + ffmpeg) → OGG. `Tools/Localization/build_strings.py` → `loc_en.json`, `loc_vi.json`.
