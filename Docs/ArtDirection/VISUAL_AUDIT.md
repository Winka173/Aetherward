# Audit art hiện tại & năng lực công cụ — Visual Direction Reset

## 1. Art hiện tại được tạo bằng gì (kiểm tra thật, không suy đoán)
| Nhóm | Số lượng | Công cụ | Bằng chứng |
|---|---|---|---|
| Hero, enemy, boss, portrait | 392 | Python + **pycairo** (vẽ vector bằng code: spline, ellipse, polygon) | `Tools/AssetGen/art/heroes.py`, `enemies.py`; `Docs/ASSET_MANIFEST.json` |
| Relic, card, icon, UI | 313 | Python + pycairo (glyph trên huy hiệu) | `icons.py`, `glyphs.py`, `expansion_art.py`, `ui.py` |
| Biome backdrop, crystal, VFX | 90 | Python + pycairo (+ Pillow chỉ để resize preview) | `world.py`, `vfx.py` |
| Blender | 0 asset đang dùng | Chỉ có benchmark crystal (đã REWORK, không dùng) | `Reports/ArtQuality/blender_benchmark/DECISION.md` |
| SVG / AI image generation | 0 | Không dùng | — |

Tổng 795/795 asset đang chạy trong game đều do vẽ vector bằng code (pycairo).

## 2. Vì sao kết quả thiếu chiều sâu, chi tiết và thẩm mỹ
Đây là giới hạn của phương pháp, không phải lỗi tham số:
1. **Bảng màu cel shading một tầng.** Mỗi hình chỉ có màu nền + đúng một dải bóng tối dịch chéo + một đốm sáng. Không có ánh sáng môi trường, không có ánh sáng viền, không có ánh sáng phản xạ, không có bóng đổ lên vật khác. Vì vậy mọi vật trông như sticker dán lên nền.
2. **Viền đen dày đồng nhất (~6 px).** Mọi vật đều có cùng độ dày viền nên không có phân cấp thị giác. Viền "nuốt" chi tiết nhỏ ở cỡ mobile.
3. **Tỉ lệ chibi đầu to, thân ngắn** + hình học nguyên khối (ellipse, capsule). Silhouette của 36 hero khác nhau chủ yếu ở màu, mũ và đạo cụ. Dáng người gần như trùng nhau.
4. **Không có vật liệu.** Kim loại, vải, đá, da đều là màu phẳng. Không có độ nhám, phản chiếu hay texture, nên không có cảm giác "premium".
5. **Không có không gian ánh sáng chung.** Hero, quái, crystal và nền được vẽ riêng rẽ. Ánh sáng của crystal, lửa hay phép không chiếu lên cảnh. Đây chính là lý do BEFORE/AFTER gần như giống nhau: lần tái tạo trước chỉ sửa lỗi kỹ thuật (bị cắt mép, pivot, nhánh tiến hoá), **không đổi ngôn ngữ hình ảnh**.
6. **VFX là sprite phẳng.** Vòng, hạt, tia đều đậm như nhau nên thiếu phân cấp (telegraph boss so với phản ứng so với đòn thường).
7. **Backdrop vẽ từ trên xuống, không có tầng xa gần.** Không có sương, không có lớp chồng, không có điểm sáng dẫn mắt.

Kết luận: tiếp tục pycairo chỉ cho ra "recolor của theme cũ". **Không nên dùng nó làm pipeline sản xuất chính** cho phong cách mới. Nó vẫn hữu ích cho icon/UI vector.

## 3. Năng lực công cụ trong môi trường này (đã đo)
| Công cụ | Trạng thái | Giới hạn cụ thể |
|---|---|---|
| Blender 4.0.2 | Có | Chỉ dùng được Cycles CPU, 4 nhân, **không GPU**, **không denoiser** (bản build thiếu OpenImageDenoise). Render 1280×720 mất ~5–15 phút/ảnh. EEVEE crash vì thiếu `libEGL.so.1`. |
| Dựng hình nhân vật bằng script Blender | Làm được, chất lượng có trần | Ghép primitive (cylinder/sphere/cone + bevel + noise material). Đủ cho **benchmark ánh sáng, chất liệu, bố cục**. **Không thay được** sculpt + retopo + rig + texture painting của artist. |
| AI image generation (Stable Diffusion… chạy local) | **BLOCKED** | Network policy chặn `huggingface.co` và `download.pytorch.org`, nên không tải được model và torch. Không có GPU: SD1.5 trên CPU ~1–3 phút/ảnh 512px nếu tải được. Không có credential dịch vụ trả phí. |
| Unity Editor (URP 2D, Shader Graph, VFX Graph, screenshot thật) | **BLOCKED** | Không có Unity trong container, nên **không thể chụp screenshot Unity thật**. Mọi ảnh ở đây là render offline hoặc mockup. |
| Pillow/NumPy | Có | Hậu kỳ (lượng tử hoá palette, vignette, mockup UI). |

## 4. Đề xuất công nghệ (theo thứ tự hiệu quả cho hướng mới)
1. **Concept art bằng AI có kiểm soát style** (SDXL / Flux + LoRA style riêng, ControlNet theo layout gameplay): mở mạng tới `huggingface.co` (+ `download.pytorch.org`). Tốt nhất có GPU. Chỉ dùng làm concept/tham chiếu; giấy phép model phải cho phép thương mại (vd. SD1.5 CreativeML OpenRAIL-M; SDXL-Turbo **không** cho phép).
2. **Blender làm nguồn sprite** cho hướng 2.5D/pixel: model nhân vật bởi artist (hoặc mua bộ asset có giấy phép), rig chung, render 4/8 hướng từ camera gameplay. Pipeline `ap.py render` đã sẵn chỗ cắm.
3. **Unity URP 2D + 2D Lights + Shader Graph** (normal map từ render Blender) để có ánh sáng động: crystal và phép chiếu sáng nhân vật. Cần máy có Unity Editor + GPU.
4. **Hand-paint/paintover** cho hero chính, boss, portrait và UI (Krita/Photoshop), dùng render Blender làm base.
5. Giữ **Art Quality Validator** (đã có) cho mọi hướng: kiểm tra crop, pivot, scale, contrast, CVD, atlas.
