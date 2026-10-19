# Art Direction

- **Phong cách:** cartoon fantasy 2D, tỉ lệ ~2.5 đầu, viền mực đậm (#1C1730), màu phẳng + một lớp cel-shade (lệch phải/dưới) + highlight mềm (trên/trái). Cùng ngôn ngữ thị giác với Arcane-Brigade (viền dày, màu bão hoà) nhưng nhân vật là người/anh hùng, không phải thú cưng.
- **Silhouette hero:** khác nhau bằng hình khối, không chỉ màu: mũ trùm nhọn (Ignis), tóc gai (Cinder/Volt), tóc dài (Marina/Freya), mũ trùm + khăn che (Tidal), khăn quàng (Raiden), mũ giáp kín (Glacius), sừng (Terra), mohawk (Magnus), búi tóc lông vũ (Zephyr), đuôi ngựa (Sylph). Vũ khí: trượng, đại kiếm lửa, roi nước, cột dẫn điện, dao đôi, khiên tháp băng, quạt, cung, búa, găng.
- **Tư thế:** idle, cast, downed (nằm, khử màu + sao choáng), tiến hoá A (vầng hào quang vàng + huy hiệu sao), tiến hoá B (cánh màu nguyên tố + huy hiệu kim cương). Hit flash, nhún, nghiêng khi tấn công là animation procedural trong Unity.
- **Enemy:** họ "rift monster": mỗi archetype một silhouette (imp tròn, chó săn dài, blob nhỏ, khiên tháp, pháp sư áo choàng, goblin ôm bom, golem có vòng ward, quái giáp gai, người triệu hồi, kẻ cầm cờ, quái pha lê, elite sừng có vương miện, linh hồn, Golem boss, Rift Warden).
- **Nguyên tố (không chỉ dựa vào màu):** Lửa = ngọn lửa/sao gai, Nước = giọt/vòng bắn tung, Sét = tia gấp khúc, Băng = mảnh tinh thể/bông tuyết, Gió = vòng cung xoáy, Đất = đá vụn. Âm thanh riêng cho từng nguyên tố.
- **Độ phân giải:** hero canvas 320px (PPU 200 ≈ 1.6 unit), enemy 256px, boss 512px (PPU 160), arena 2400×1360 (PPU 80). Đủ nét ở 1080p; ở 4K hero ~225px.
- **Kiểm duyệt:** contact sheet trong `Docs/Previews/` (ảnh nguồn, không phải capture runtime Unity).
