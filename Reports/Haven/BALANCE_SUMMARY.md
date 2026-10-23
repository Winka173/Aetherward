# Haven — balance sau chuyển đổi

Ngày 2026-10-23. Ascension 0, 12 chiến thuật bot × 20 seed = 240 run mỗi stance; tổng 720 run. Mở toàn bộ content, DynamicParty bật, đội hình mặc định Split.

Mỗi chiến thuật dùng seed `1000 + r * 7919`; biome xoay theo `r % 6`. Mỗi stance có cùng cặp seed/biome. 20 không chia hết cho 6 nên hai biome đầu có 48 run và bốn biome sau có 36 run mỗi stance. Kết quả không phải so sánh trực tiếp với mốc 46/41/32 cũ vốn chỉ dùng Verdant và bộ luật trước thay đổi.

| Stance | Thắng | Tỷ lệ | Đợt đạt trung bình |
|---|---:|---:|---:|
| Defensive | 66/240 | 27.5% | 16.90 |
| Balanced | 83/240 | 34.6% | 17.32 |
| Aggressive | 68/240 | 28.3% | 17.15 |

| Biome | Defensive | Balanced | Aggressive |
|---|---:|---:|---:|
| verdant_sanctuary | 20/48 | 22/48 | 20/48 |
| molten_crater | 10/48 | 16/48 | 13/48 |
| frostfall_bastion | 9/36 | 11/36 | 8/36 |
| shattered_aether | 8/36 | 10/36 | 10/36 |
| stormspire_citadel | 6/36 | 8/36 | 6/36 |
| sunken_archive | 13/36 | 16/36 | 11/36 |

Các tham số PillageRate, GateSlow, stance bonus, UltPower và enemyHpMult giữ nguyên. Lượt đo này thiết lập baseline sau khi đổi hình học, vị trí ban đầu và ultimate; chưa chỉnh chỉ số để ép tỷ lệ thắng về mốc cũ. Chênh lệch theo chiến thuật/biome nằm trong CSV và SUMMARY từng stance.

Tái tạo (build trước, không rebuild cùng lúc các tiến trình đang dùng DLL trên Windows):

```powershell
dotnet build Tools/SimHarness/Balance -c Release
dotnet Tools/SimHarness/Balance/bin/Release/net8.0/Aetherward.Balance.dll --runs 20 --stance Defensive --biome all --out Reports/Haven/Balance/Defensive
dotnet Tools/SimHarness/Balance/bin/Release/net8.0/Aetherward.Balance.dll --runs 20 --stance Balanced --biome all --out Reports/Haven/Balance/Balanced
dotnet Tools/SimHarness/Balance/bin/Release/net8.0/Aetherward.Balance.dll --runs 20 --stance Aggressive --biome all --out Reports/Haven/Balance/Aggressive
```

CSV từng run có thêm `biome` và `stance`; `waves.csv` chứa dữ liệu từng đợt. Log console nằm ở `Reports/haven-balance-*.txt`. Thời gian chạy có thể chịu ảnh hưởng do ba stance chạy đồng thời; không dùng cột ms làm benchmark hiệu năng. Xem `PERF.md` cho probe mô phỏng riêng.
