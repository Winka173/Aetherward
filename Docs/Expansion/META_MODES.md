# Meta & Modes

| Mode | Rules | Mở khoá | Kỷ lục |
|---|---|---|---|
| Classic | 20 đợt soạn sẵn, boss đợt 10 (theo seed/biome) và 20 | Có sẵn | `classic` |
| Endless | Sau đợt 20 lặp đợt 11–20; cấp độ đường cong HP tiếp tục tăng + 25% HP mỗi vòng; đợt chia hết cho 10 là boss; đợt cuối vòng vẫn có thưởng (relic + draft) | Thắng 1 lượt Classic | `endless` |
| Daily Seed | Seed, chiến trường và 2 biến thể (haste/armored/swarm) suy ra từ ngày UTC `yyyymmdd`; người chơi vẫn chọn đội | Có sẵn | `daily:<ngày>` |
| Boss Rush | Mọi boss theo HP tăng dần (hiện 5), mỗi chặng dựa trên đợt boss 10/20 với cấp độ 6→20; đội 4 hero cấp 3 (+2 hero rút tất định), +30 vàng; thưởng relic + chiêu mộ + tiến hoá | Đạt đợt 11 | `bossrush` (không tính vào BestWave) |

Mã: `RunController.NewModeRun`, `WaveAt`, `TotalWaves` (0 = vô tận), `BossRushBosses`; `RunState.Mode/DailyKey/ModeModifiers` (lưu save); `MetaProfile.ModeRecords` (lưu meta). `WaveDef.Level/ScalePct` chỉnh độ khó mà không đổi số đợt.

## Ascension 1–10 (module cộng dồn, `difficulty.json`)
1 frenzy · 2 tốc độ +8%, giá +15% · 3 Pha Lê −15%, khoá 1 ô · 4 sát thương +10%, affix elite · 5 boss nổi giận · **6** HP +10%, reroll +1 · **7** mỗi 8 kẻ thường có 1 elite · **8** sử thi/huyền thoại hiếm hơn 30%, Pha Lê −10% · **9** sát thương +10%, hiểm hoạ nhanh hơn 30% · **10** boss nổi giận mạnh hơn, HP +10%.

## Đo (AutoPilot balanced, 10 seed)
Endless: trung bình đợt 24.5 · Boss Rush: chặng 2.7/5 (0 thắng — chế độ thử thách; cân bằng lại ở Phase 5 khi đủ 12 boss).
