# Benchmark 3 hướng hình ảnh — Visual Direction Reset

> **Loại bằng chứng:** tất cả ảnh dưới đây là **OFFLINE RENDER (Blender Cycles CPU, model dựng bằng script) + UI MOCKUP (Pillow)**.
> **Không phải screenshot Unity**, vì môi trường này không có Unity Editor. Ảnh "hiện tại" là **offline composite** dựng từ snapshot simulator (đã có từ trước).
> Chưa thay asset nào trong game, chưa xoá asset cũ. Chờ bạn chọn hướng.

## 1. Cách làm
- **Một cảnh chung cho cả 3 hướng** (`Tools/ArtPipeline/blender/direction_benchmark.py`):
  - **Đơn vị:** crystal ở trung tâm, 6 hero thuộc 6 class khác nhau (Guardian, Pyromancer, Ranger, Cleric, Shadowblade, Berserker), 4 kiểu quái (ghoul, brute, wraith, cultist) và 1 boss (Molten Colossus) kèm telegraph.
  - **Môi trường:** arena đá, lane, cột đổ, brazier, cây chết.
  - **VFX:** lửa, sét, băng.
  - **Đồng nhất giữa các hướng:** cùng camera ortho 3/4 (cao 38°), cùng vị trí, cùng tỉ lệ. Chỉ khác ánh sáng, tone và hậu kỳ.
- **Hậu kỳ + UI mockup** (`Tools/ArtPipeline/direction_post.py`):
  - **HUD:** wave, thanh máu crystal, thanh máu boss, cảnh báo "SLAM INCOMING", dock 6 hero.
  - **Portrait:** cắt từ chính render, không vẽ riêng.
  - **Không có vòng range debug**, chỉ có vòng class dưới chân hero.
- **Thời gian render** (4 nhân CPU, không GPU, không denoiser):

  | Hướng | Thông số | Thời gian |
  |---|---|---|
  | Mythic | 1280×720, 192 spp | 552 s |
  | Painterly | 1280×720, 160 spp | 189 s |
  | Pixel | 640×360, 160 spp | 53 s |

## 2. File để review
| File | Nội dung |
|---|---|
| `Reports/ArtDirection/benchmarks/compare_all_720p.png` | Lưới 2×2: hiện tại / A / B / C ở 720p |
| `Reports/ArtDirection/benchmarks/{mythic,pixel,painterly}_1080p.png` | Từng hướng ở 1080p |
| `Reports/ArtDirection/benchmarks/units_closeup.png` | Kiểm tra mobile: cả khung ở 640×360 + vùng trung tâm phóng 2× |
| `Reports/ArtDirection/raw/*.png` | Render gốc chưa có UI |
| `Reports/ArtDirection/versions/v1, v2` | Các phiên bản trước (xem mục 5) |

## 3. Đánh giá (trung thực, theo tiêu chí bạn đặt)
Thang điểm 1–5. Điểm là nhận định của tôi khi xem ảnh, không phải số đo tự động.

| Tiêu chí | Hiện tại (cartoon) | A. Dark Mythic | B. Pixel Art | C. Painterly 2.5D |
|---|---|---|---|---|
| Silhouette phân biệt class | 2: dáng giống nhau, khác màu/mũ | 3: khiên, cung, áo choàng, rìu đọc được | 2: mất chi tiết ở 640×360 | 3: như A, mềm hơn |
| Boss nổi bật, nguy hiểm | 2: quái mắt tròn dễ thương | **4**: khối đá to, mạch magma, đứng trên cao | 3: khối tối, mất magma | 4 |
| Crystal là tâm điểm | 3 | **5**: là nguồn sáng chính, đổ bóng toả ra | 3: xám trắng, mất cyan | 4 |
| Chiều sâu, chất liệu, ánh sáng | 1: phẳng | **4**: ánh sáng chung, bóng đổ, đá/kim loại/vải | 3 | 4: nét cọ (Kuwahara), ấm |
| Phân cấp VFX (telegraph > phản ứng > đòn thường) | 2: mọi thứ đậm như nhau | 4: telegraph đỏ phát sáng mạnh nhất | 3: telegraph còn viền | 4 |
| Đọc được ở mobile (640×360) | 4: tương phản cao, nhưng ồn | 3: phần ngoài arena quá tối | 2: grey cast, khó tách hero | 3 |
| Nhất quán camera/tỉ lệ/ánh sáng | 2 | 5: một cảnh, một nguồn sáng | 5 | 5 |
| Sức hút ("premium") | 2 | **4** | 2 | 3–4 |

**Điểm yếu thật của cả 3 benchmark:**
- Nhân vật được ghép bằng script từ primitive, nên trông như **tượng mô hình/figurine**: không có khuôn mặt, tay hay nếp vải.
- Ghoul vẫn trông giống "cừu". Lane phía bắc vẫn giống tấm ván.

Đây là **trần chất lượng của việc dựng model bằng code**, không phải trần của hướng art. Benchmark chứng minh được **ánh sáng, chất liệu, bố cục, phân cấp VFX và camera**. Nó **không** chứng minh chất lượng nhân vật cuối cùng.

**Lưu ý về camera:**
- Game hiện tại gần như nhìn từ trên xuống; benchmark dùng 3/4 (38°) để có chiều sâu và khối.
- Đổi sang 3/4 làm boss/hero cao che một phần lane phía sau. Cần kiểm tra lại trong Unity (sorting theo trục Y, giới hạn chiều cao sprite).
- Không cần đổi gameplay. Đây là thay đổi về trình bày.

## 4. Khuyến nghị
**Hướng A — Dark Mythic Fantasy**, mượn hậu kỳ nét cọ nhẹ của C cho portrait/key art.
- **Lý do:** A là hướng duy nhất cải thiện rõ cả 3 điểm bạn phàn nàn (chiều sâu, ánh sáng, độ "premium"), trong khi vẫn giữ crystal làm tâm điểm và telegraph dễ đọc.
- **B (pixel)** chỉ đẹp khi có palette vẽ tay và artist dọn từng frame. Pipeline tự động (lượng tử hoá palette) cho kết quả xám và mất màu gameplay, nên không khuyến nghị nếu không có pixel artist.
- **C** đẹp ở ảnh tĩnh, nhưng hiệu ứng Kuwahara làm nhòe chi tiết nhỏ ở mobile.

**Phần ngoài arena của A quá tối ở mobile:** khi triển khai, cần nâng ambient vùng lane lên khoảng 15–20%. Quái phải luôn đọc được.

## 5. Phiên bản và thay đổi
| Phiên bản | Thay đổi | Lý do |
|---|---|---|
| v0 (preview) | Camera 52°, ortho 26 | Quá xa, đơn vị quá nhỏ; quá tối; volume nhiễu; telegraph đè crystal |
| v1 | Camera 38°/ortho 19, sáng hơn, volume 0.004, telegraph đặt trước boss, painterly chuyển sang hoàng hôn | Crystal có 2 đốm trắng như "mắt"; lane giống tấm gỗ; nền quá nâu |
| v2 | Lane lún + displace, nền tối hơn, ghoul gầy hơn có gai xương, brazier dịu hơn, pixel giữ 10 màu accent | "Mắt" vẫn còn |
| **v3 (hiện tại)** | **Nguyên nhân thật của "mắt":** bán kính đèn crystal (0.6) lớn hơn apothem của crystal (~0.56) nên quả cầu đèn xuyên qua mặt. Sửa: bán kính 0.1, crystal không đổ bóng (để ánh sáng ra được arena), giảm xuống 1200 W | — |

## 6. Giới hạn công cụ (đã đo) và cách khắc phục
| Giới hạn | Ảnh hưởng | Cách khắc phục |
|---|---|---|
| Không có Unity Editor | Không có screenshot thật, không test được URP 2D Lights/Shader Graph | Chạy trên máy có Unity 2022.3 + URP; tôi đã chuẩn bị pipeline sẵn |
| AI image generation bị chặn (`huggingface.co`, `download.pytorch.org`) | Không tạo được concept art có kiểm soát style | Thêm 2 domain vào **Allowed domains** của environment (Network access). Tốt nhất có GPU |
| Blender: chỉ CPU, không OIDN, EEVEE crash (thiếu libEGL) | Render chậm, phải khử nhiễu bằng median | Máy có GPU hoặc bản Blender có OIDN |
| Dựng model bằng script | Nhân vật trông như figurine | Model do artist làm (sculpt/retopo/rig), hoặc bộ asset có giấy phép thương mại, hoặc paintover lên render |

## 7. Bước tiếp theo sau khi bạn duyệt (chưa làm)
1. Chốt **style guide** cho hướng được chọn: palette, key/rim light, độ dày viền (không viền đen đồng nhất), phân cấp VFX, tỉ lệ nhân vật.
2. **Golden set** khoảng 10 asset (1 hero mỗi class, 2 quái, 1 boss, crystal, 1 nền) theo hướng mới. Chạy qua Art Quality Validator. So sánh before/after ở cùng camera.
3. Chỉ khi golden set đạt mới triển khai theo batch (`build.py --scope ...`): có backup, giữ GUID, rollback được. Asset cũ vẫn được giữ.
4. Trong Unity: URP 2D + Light2D cho crystal và phép, normal map xuất từ render Blender. Chụp screenshot thật để xác nhận.
