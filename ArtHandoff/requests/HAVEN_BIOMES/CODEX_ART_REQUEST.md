# Haven cho năm biome — hợp đồng hình học

Dữ liệu gameplay đã chuyển sang Haven. Đây là gói tham chiếu hình học bổ sung cho R07, không phải batch nhập asset và chưa thay thế INPUT_MANIFEST của pipeline handoff.

- Nguồn chính xác: `Assets/_Aetherward/Resources/Content/biomes.json`; bản trích xuất trong `GEOMETRY.json`.
- Các ảnh `references/<biome>_guide.png` khóa footprint tường (đen), vùng đi (trắng mờ), tâm lane (trắng), cổng (xanh lá), hazard (cam), cover (xanh lơ), vùng bonus (tím).
- Guide 1600×1280 chứa miền **40×32 game unit** để thấy toàn bộ spawn. Đây là bản kỹ thuật, không phải kích thước ảnh nền giao trong game. Khi vẽ nền, dùng framing/PPU từ COMMON_CONTRACT và env metadata; không kéo giãn guide vào ảnh nền 2:1.
- Giữ vị trí và độ rộng lối cổng; không đặt prop chắn khu đi được. Các lane north/south/northeast/southwest cùng đi qua cổng nam; tên lane là ID tương thích wave, không phải hướng spawn.
- molten_crater: bazan, cầu và tiền sảnh hẹp, dung nham; frostfall_bastion: băng và cover; shattered_aether: đá nổi/khe nứt; stormspire_citadel: sân bên rộng, cột sét; sunken_archive: thư viện ngập, bậc nước.
- Frostfall giữ lịch mở lane chéo từ wave 8; Sunken giữ lịch mở lane north/south từ wave 6. Không vẽ chặn vĩnh viễn những lối này.
- Asset đích: `World/bg_molten_crater`, `World/bg_frostfall_bastion`, `World/bg_shattered_aether`, `World/bg_stormspire_citadel`, `World/bg_sunken_archive` cùng metadata môi trường phù hợp.

Áp dụng `ArtHandoff/requests/COMMON_CONTRACT.md` và `ArtProduction/ART_BIBLE.md`. Nền hiện có cho năm biome vẫn là art trước Haven, cần thay trước khi coi hình ảnh hoàn tất.

Tái tạo guide:

```powershell
python Tools/ArtPipeline/layout_guide.py --biome molten_crater --view 40 32 --size 1600 1280 --out ArtHandoff/requests/HAVEN_BIOMES/references/molten_crater
```
