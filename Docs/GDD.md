# Aetherward — Thiết kế trò chơi (GDD)

> Tên làm việc. Cần kiểm tra thương hiệu trước khi phát hành.

## Tổng quan
Auto-battler / crystal defense roguelike 2D nhìn từ trên xuống, cho Windows, Android, iOS. Người chơi chỉ huy **tối đa 6 anh hùng** đứng trên **12 ô phòng thủ** quanh một **Pha Lê** ở trung tâm. Trận đấu tự động; quyết định chiến thuật nằm giữa các đợt: xếp đội hình, chọn thẻ, chiêu mộ, mua di vật, tiến hoá, khế ước. Một lượt chơi gồm **20 đợt**, kết thúc bằng boss **Kẻ Gác Khe Nứt (Rift Warden)**.

## Vòng lặp một lượt
`Menu → Chọn 2 anh hùng (seed, Thăng cấp) → Chuẩn bị → Đợt (tự chiến) → Phần thưởng → Chuẩn bị → … → Đợt 20 → Kết quả → Lưu meta`.

- **Chuẩn bị:** kéo-thả anh hùng (hoặc chạm anh hùng rồi chạm ô) lên 12 ô; đổi chỗ miễn phí; mũi tên đỏ báo làn kẻ địch sắp tới; xem danh sách kẻ địch và gợi ý phản đòn; hồi sinh (Vàng), sửa Pha Lê (Vàng), tiến hoá (Tinh Chất).
- **Đợt:** tick mô phỏng cố định 1/30 s, tốc độ 1×/2×, tạm dừng; anh hùng tự chọn mục tiêu, tự dùng kỹ năng, chỉ di chuyển trong phạm vi canh giữ (leash). Không có điều khiển trực tiếp.
- **Kết thúc đợt:** dọn sạch mọi kẻ địch (thắng đợt) hoặc Pha Lê về 0 (thua lượt). Quá thời gian giới hạn: kẻ địch còn lại "đột phá" gây sát thương lên Pha Lê rồi biến mất → mọi đợt đều kết thúc, không softlock.
- **Hồi phục:** anh hùng còn sống hồi 25% HP sau đợt; anh hùng gục giữ trạng thái gục cho tới khi hồi sinh bằng Vàng (D-11).
- **Phần thưởng theo bảng 20 đợt** (draft, chiêu mộ, cửa hàng 4/9/14/19, di vật 5/15, sự kiện 8, tiến hoá 10, khế ước 15). Tối đa 2 màn hình mỗi đợt.

## Kinh tế
- **Vàng:** thưởng đợt + Vàng khi hạ địch + **lãi** (+1 mỗi 10 Vàng chưa tiêu, tối đa 4) → có lý do để tiết kiệm.
- **Tinh Chất:** từ đợt elite/boss/sự kiện; 3 Tinh Chất cho một lần tiến hoá.
- Giá cửa hàng tăng 3.5%/đợt; đổi (reroll) 2, 3, 4… Vàng mỗi màn.
- Chiêu mộ: anh hùng mới gia nhập ở cấp trung bình đội − 1 (không bị tụt lại).

## Anh hùng, cấp, tiến hoá
12 anh hùng, vai trò và nguyên tố độc lập (bảng đầy đủ: `CONTENT_CATALOG.md`). Mỗi anh hùng có đòn thường, kỹ năng tự động, nội tại, hồ sơ chọn mục tiêu riêng (gần Pha Lê nhất, cụm đông, elite, kết liễu, cơ hội phản ứng…).
- **Cấp trong lượt 1–5** (KN mỗi đợt; boss +1). Cấp 2+ mở **thẻ Chuyên môn** của riêng anh hùng (đổi tham số kỹ năng: số tia sét, số mũi tên, vùng, đất cháy…).
- **Tiến hoá ở cấp 5 + 3 Tinh Chất**: 2 nhánh/anh hùng, luôn đổi cơ chế (ví dụ Ignis: Thiên Thạch có báo trước vs Lưới Than Hồng lan Bỏng; Cinder: sát thủ săn elite vs vệ binh khiêu khích). 24 nhánh đều chạy được (test).

## Nguyên tố và phản ứng
6 nguyên tố, 15 phản ứng theo cặp không phụ thuộc thứ tự. Đòn đánh để lại **hào quang nguyên tố** (gauge, tan sau ~2.5 s). Nguyên tố khác loại chạm vào → phản ứng, tiêu hao gauge, có hồi chiêu riêng trên từng mục tiêu.
- **Chống chuỗi vô hạn:** mọi hiệu ứng mang "thế hệ" (generation). Phản ứng từ đòn trực tiếp là thế hệ 1, hiệu ứng phụ không thể gây phản ứng ở thế hệ ≥ 2 (thẻ huyền thoại *Tràn Nguyên Tố* +1). Ngoài ra: ngân sách 6 phản ứng/giây/mục tiêu và 48 phản ứng/tick toàn trận.
- **Sát thương phản ứng** = (gốc × cấp đợt + hệ số × Công nguồn) × (1 + thưởng phản ứng + Tinh Thông + chỉnh sửa). Bỏ qua Thủ, không bỏ qua kháng.
- Boss: đóng băng ngắn hơn và tăng dần kháng đóng băng, **không bao giờ miễn nhiễm**.

## Kẻ địch, elite, boss
15 loại (gồm 2 boss): cận chiến, chó săn nhanh, bầy nhỏ, lính khiên (chặn đòn trước mặt), pháp sư đánh xa, lính bom (bỏ qua anh hùng, nổ vào Pha Lê), golem kết giới (kháng 1 nguyên tố, có báo hiệu), chiến xa kháng khống chế, kẻ triệu hồi, quỷ cầm cờ (buff), quái lăng kính thích nghi (kháng tối đa 0.45), elite Kẻ Tàn Phá (lao đập có báo trước).
- **Golem Phá Thành (đợt 10):** lao đập báo trước; ở 50% HP có giáp dày 7 s (Nứt Giáp/Siêu Dẫn phá được).
- **Kẻ Gác Khe Nứt (đợt 20):** Pha 1 triệu hồi; Pha 2 đánh dấu một làn, chuỗi đòn báo trước chạy dọc làn + chó săn; Pha 3 tung 3 cú đập rồi **Lộ Sơ Hở** (+50% sát thương nhận) 4.5 s. Có 1.5 s bất tử khi đổi pha.

## Di vật, thẻ, khế ước
- 25 di vật (4 họ: Chiến đấu/Nguyên tố/Phòng thủ/Hỗn loạn) + 3 hợp thể (tự hợp nhất khi có đủ 2 thành phần).
- 46 thẻ: chỉ số, kỹ năng, chuyên môn (12), cộng hưởng đội (6), phản ứng (6), đột biến đổi luật (4), khế ước bị nguyền (4).
- Draft thông minh: luôn có ít nhất 1 thẻ "dùng được ngay" cho đội hiện tại; không trùng, không vượt số tầng, không thẻ không hợp lệ.
- Khế ước đợt 15 hiển thị chính xác bất lợi và yêu cầu xác nhận.

## Meta (không tăng chỉ số vĩnh viễn)
Mở khoá anh hùng (Raiden, Tidal, Glacius, Zephyr, Magnus) và di vật (4) theo cột mốc; bách khoa (anh hùng/phản ứng/di vật/kẻ địch); lịch sử 30 lượt gần nhất (seed, phiên bản, MVP, phản ứng mạnh nhất, HP Pha Lê theo đợt, nguyên nhân thua); Thăng cấp 1–5 mở sau khi thắng.

## Các lối chơi đã kiểm chứng bằng mô phỏng
Thunderstorm (Nước+Sét+Gió), Frozen Fortress (Băng+Đất), Magma Engine (Lửa+Đất), Mixed Burst (Bốc Hơi + chí mạng), Glass Cannon (toàn đánh xa + khế ước), Balanced. Nhịp độ khác nhau rõ (10.5–14.6 phút chiến đấu), xem `BALANCE.md`.
