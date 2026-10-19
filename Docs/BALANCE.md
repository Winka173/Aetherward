# Cân bằng

Mọi số liệu dưới đây là **giả thuyết khởi đầu** được kiểm tra bằng mô phỏng headless, chưa qua người chơi thật.

## Công thức (khớp code, tooltip sinh từ dữ liệu)
- Sát thương trực tiếp: `Công × hệ số × (1 + bonus) × chí mạng × 100/(100 + Thủ) × (1 − kháng) × dễ tổn thương`. Chí mạng ≤ 75%, hệ số chí mạng ≤ 4×.
- Phản ứng: `(gốc × (1 + 0.12 × (đợt−1)) + hệ số × Công nguồn) × (1 + thưởng phản ứng + 2·EM/(EM+150) + chỉnh sửa)` × hệ số hiệu ứng; bỏ qua Thủ.
- Nứt Giáp: −30% Thủ mỗi tầng (tối đa −90%). Siêu Dẫn: −40% Thủ, −25% kháng.
- HP kẻ địch theo đợt: `× (1 + 0.19(w−1) + 0.015(w−1)²)`; sát thương `× (1 + 0.07(w−1))`. Thăng cấp: +8%/cấp và các luật bổ sung.
- Anh hùng: HP/Công `× 1.12^(cấp−1)` (giá trị riêng từng anh hùng), +2 Thủ/cấp, +8 EM/cấp. Khiên ≤ 60% HP tối đa; khiên Pha Lê ≤ 30%.
- Kinh tế: Vàng khởi đầu 8; thưởng đợt 10→30; lãi +1/10 Vàng (tối đa 4); KN để lên cấp 2/4/6/9 (cấp 5 sau đợt 9 → tiến hoá ở đợt 10).

## Kết quả mô phỏng (`Docs/Balance/`)
180 lượt (30 seed × 6 lối chơi, mở khoá toàn bộ, autopilot theo kịch bản): **105 chiến thắng, 0 lượt kẹt (softlock)**.

| Lối chơi | Thắng | Phút chiến đấu | Phản ứng/lượt | Đợt hay thua |
|---|---|---|---|---|
| Thunderstorm | 17/30 | 13.2 | 1300 | 19–20 |
| Frozen Fortress | 20/30 | 14.6 | 1274 | 19–20 |
| Magma Engine | 23/30 | 12.9 | 1032 | rải rác 8–19 |
| Mixed Burst | 21/30 | 12.7 | 1193 | 18 |
| Glass Cannon | 5/30 | 10.5 | 921 | 19 |
| Balanced | 19/30 | 12.8 | 1104 | 18, 20 |

- Thời lượng chiến đấu trung bình 37–44 s/đợt (mục tiêu 35–55 s). Cộng thời gian chọn giữa đợt (ước ~20 s × 20) → một lượt khoảng 19–22 phút ở tốc độ 1×.
- Nhịp độ khác nhau rõ: Frozen Fortress chậm và chắc (14.6 phút), Glass Cannon nhanh và mong manh (10.5 phút).
- Điểm nghẽn hiện tại: đợt 18–20 (lính bom + boss). Wave 9 (golem kết giới) phạt đội một nguyên tố.

## Các thay đổi đã làm sau mô phỏng
1. Pass 1: đợt 2 bớt chó săn; tăng mật độ đợt 5+ (×1.5/×1.8); đường cong HP dốc hơn; cắt đợt lính bom 13/18 và golem kết giới đợt 9; tăng HP Golem/Warden; sửa đường KN để tiến hoá ở đợt 10.
2. Sửa lỗi: Mưa của *Torrent Caller* nhân Công hai lần → lối Thunderstorm thắng 12/12 giả tạo; sau sửa còn 17/30.
3. Pass 2: Glass Cannon nhận thêm thưởng sát thương (khế ước +50%, di vật +45% / −25% HP Pha Lê) — vẫn 5/30 vì đội toàn đánh xa bị hạ ở đợt 19. Đây là lối "rủi ro cao" theo thiết kế; cần thử người chơi thật trước khi chỉnh tiếp.

## Hạn chế của dữ liệu
- Autopilot là heuristic: luôn xếp đội hình hợp lý, không mắc lỗi người chơi, nhưng cũng không tối ưu như người giỏi.
- Mô phỏng mở khoá toàn bộ nội dung; người chơi mới chỉ có 7 anh hùng và 21 di vật khởi đầu.
- Float không fixed-point: tái lập chính xác trên cùng nền tảng; giữa các CPU/IL2CPP có thể lệch nhỏ.
- Hiệu năng (`Balance/PERF.md`): 20–82 µs/tick trung bình, đỉnh ~1.8 ms (desktop .NET JIT, có cả GC/JIT). Ở 2× (2 tick/khung) ngân sách mô phỏng < 1 ms/khung trên desktop; **chưa đo trên thiết bị di động**.

## Cách chạy lại
```
cd Tools/SimHarness
dotnet run --project Balance -c Release -- --runs 30            # 6 lối chơi → Docs/Balance/*.csv, SUMMARY.md
dotnet run --project Balance -c Release -- --runs 30 --asc 3     # thử Thăng cấp 3
dotnet run --project Balance -c Release -- --perf                # Docs/Balance/PERF.md
dotnet run --project Balance -c Release -- --snapshot 14 --time 26 --strategy thunderstorm --out /tmp/snap
python3 Tools/AssetGen/preview/compose_frame.py /tmp/snap/snapshot_w14.json frame.png
```
