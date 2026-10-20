# Kế hoạch vẽ lại toàn bộ art — Aetherward

Phạm vi: vẽ lại **toàn bộ 795 asset** theo hướng Dark Mythic Painterly 2.5D (`ArtProduction/ART_BIBLE.md`). Thêm **~200 asset mới** cho animation. Không giữ lại art cũ nào.

## 1. Phân vai
| Ai | Làm gì |
|---|---|
| **Codex (GPT-6.1 Sol)** | Sản xuất art theo từng batch: image_gen cho nhân vật, icon, card, relic, VFX; Blender cho crystal và battlefield |
| **Claude** (lead) | Viết brief, gọi Codex trực tiếp bằng `codex exec`, nghiệm thu (intake, validator, Unity capture), tích hợp vào Unity, **toàn bộ animation và tech-art** |
| **Bạn** | Duyệt hướng art ở các cổng (G1–G3) |

Cách gọi Codex: Claude gọi trực tiếp (đã kiểm chứng trên máy này). Ngày 2026-10-20, B01 sinh 26 ảnh image_gen; một lần gọi đơn lẻ sinh một frame có ảnh tham chiếu mất ~1 phút 48 giây. Prompt của mọi batch nằm trong repo: `ArtHandoff/requests/<batch>/CODEX_ART_REQUEST.md`.

## 2. Cổng duyệt
| Cổng | Khi nào | Bạn duyệt gì |
|---|---|---|
| **G1 — Style** | Sau B01 | Screenshot Unity thật của B01 so với art cũ, cùng camera. Chỉ khi bạn chấp nhận style thì B02–B17 mới được gửi |
| **G2 — Roster** | Sau B02 + B08 | Hero và enemy đủ animation trong trận thật |
| **G3 — Release** | Sau khi import toàn bộ | Toàn game, mọi biome, hiệu năng |

Nếu bạn không duyệt một batch, asset cũ vẫn được giữ trong game và batch đó quay lại vòng sửa với danh sách lỗi cụ thể.

## 3. Danh sách batch Codex (theo thứ tự)
"Mới" là frame animation chưa có trong game hiện tại. Contract của chúng do Claude định nghĩa, và code dùng ảnh fallback nếu thiếu file.

| Batch | Nội dung | Số file | Phụ thuộc |
|---|---|---|---|
| **B01** | Benchmark + khoá style: Ignis (đủ evo), Terra, Sylph, Marina, 4 enemy, Rift Warden, crystal 3 state, biome Verdant, 12 VFX, 17 icon, 9 UI | 77 | **đang chạy** |
| B02 | Hoàn thiện 7 starter: evo của Terra/Sylph/Marina (12); attack cho 4 hero B01 (12); Cinder, Volt, Freya đầy đủ (30) + 3 portrait | 57 | G1 |
| B03 | tidal, raiden, glacius, zephyr, magnus, seren | 6×10 + 6 = 66 | G1 |
| B04 | nyxara, ashara, nerissa, voltrix, eirwen, kael | 66 | G1 |
| B05 | borun, liora, thalen, vesper, sable, caelis | 66 | G1 |
| B06 | oriane, zerith, maelis, solenne, mirel, veyra | 66 | G1 |
| B07 | isolde, aeris, doran, elowen, morven | 55 | G1 |
| B08 | 9 enemy gốc còn lại (runner, swarmling, shieldbearer, sapper, warded, summoner, banner, mimic, riftling) + elite Ravager (a/b/**attack**); attack cho 4 enemy B01 | 34 | G1 |
| B09 | Faction Iron Legion, Ashen Horde, Voidborn (13 con) | 39 | G1 |
| B10 | Faction Frozen Covenant, Stormspire, Corrupted Wilds, Arcane Fractures (13 con) | 39 | G1 |
| B11 | 11 boss còn lại (a/b/attack/**tell**) + tell/attack cho Rift Warden | ≈ 46 | G1 |
| B11R | **Pilot rig boss**: bộ part tách lớp của Rift Warden để Claude rig trong Unity | ~12 part | B11 |
| B12 | 5 biome còn lại (8 layer + nền phẳng) + overlay 3 nhánh Crystal Evolution (**mới**) | ≈ 48 layer + 5 + 3 | G1 |
| B13 | 64 VFX còn lại (35 field, 8 zone, 8 impact, 11 projectile, spark, coin) + texture particle cho Unity | ≈ 64 + ~20 | G1 |
| B14 | 105 icon còn lại (element, reaction, role, status, trait, ui) | 105 | G1 |
| B15 | 80 card | 80 | B14 (cùng ngôn ngữ medallion) |
| B16 | 81 relic | 81 | B14 |
| B17 | 21 UI còn lại + title emblem + key art menu | ≈ 24 | B14 |

**Tổng:** ~795 asset vẽ lại + ~200 asset animation mới.

Mỗi batch được kiểm tra riêng: `handoff.py intake`, validator, xem trước ở tỉ lệ game, rồi chụp Unity thật với art override. Chỉ sau đó mới import có backup và rollback.

Batch có thể chạy song song 2–3 cái một lúc sau G1. Codex có giới hạn usage của gói ChatGPT, nên nếu bị chặn hạn mức, Claude ghi nhận và chạy tiếp sau.

## 4. Animation & tech-art (Claude làm, tận dụng Unity + Blender)
Hiện trạng đã kiểm chứng: game **không có** Animator, AnimationClip hay ParticleSystem. Mọi chuyển động là code (bob, lunge, flash). Hero chỉ có các frame idle, cast, downed.

| Track | Công cụ | Nội dung |
|---|---|---|
| A1 Frame mới | Unity code + Codex image_gen | Hero: `_attack`, `_evoA_attack`, `_evoB_attack`. Enemy: `_attack`. Boss: `_attack`, `_tell` (giơ vũ khí trong lúc telegraph). Mỗi frame có fallback nên rollout từng phần vẫn an toàn |
| A2 Chuyển động sống | Unity shader (`SpriteLive`) | Thở ở idle, áo choàng/tóc lay theo chiều cao sprite, anticipation và follow-through cho đòn đánh, giật khi trúng đòn, dissolve khi chết (thay việc biến mất tức thì), quái trồi lên từ rift khi spawn, flyer lơ lửng, boss bước rung màn hình |
| A3 Rig boss | Unity (Transform hierarchy + AnimationClip tạo bằng editor script) | Pilot Rift Warden trên bộ part của B11R: idle, walk, slam, tell, exposed. Nếu đạt thì áp cho 12 boss |
| A4 VFX động | **Blender** (sim lửa/khói Mantaflow, nước, sét procedural) → flipbook → **Unity ParticleSystem** (Texture Sheet Animation) | Lửa, khói, nước bắn, sét, vụ nổ phản ứng. Mật độ theo preset Effects Intensity có sẵn |
| A5 Crystal động | **Blender** (dùng lại `crystal.blend` của Codex) | Vòng xoay/nhịp sáng, các mảnh quỹ đạo tách riêng, chuyển trạng thái nứt, **vỡ khi thua** (cell fracture) |
| A6 Nền động | Unity (tách nền 1 sprite thành nhiều layer runtime, dùng layer của Codex) | Sương trôi, lửa brazier (particle), vết nứt rift phát sáng theo nhịp, vũng sáng crystal |
| A7 Ánh sáng | **Unity URP 2D** (spike trên nhánh riêng) | Light2D từ crystal và phép chiếu lên nhân vật, bloom, normal map bake từ Blender cho crystal và môi trường. Quyết định dựa trên screenshot + FPS. Không bật nếu tụt hiệu năng mobile |
| A8 UI động | Unity IMGUI | Lật card, nhấn nút, thanh máu tween, toast |

## 5. Rủi ro đã biết
- **Độ nhất quán nhân vật giữa các frame** (image_gen không tất định).
  - Giảm rủi ro: mỗi nhân vật dùng ảnh tham chiếu từ frame idle đã duyệt (`-i`), sinh theo sheet và lưu prompt.
  - Khi intake, Claude so silhouette và màu giữa các frame.
- **Chi tiết quá dày ở tỉ lệ game:** hero chỉ cao khoảng 60–90 px.
  - Mỗi batch có sheet silhouette và grayscale ở 720p.
  - Lỗi được trả lại Codex kèm crop cụ thể.
- **Frame attack vẽ cả VFX vào sprite:** lỗi này thấy ở lần thử đầu.
  - Brief cấm.
  - Intake kiểm tra vùng phát sáng lệch ra ngoài thân.
- **Nền 2400×1360 không phủ hết màn 20:9 và 4:3.**
  - Ghi nhận cho B12; có thể tăng canvas nền và giữ nguyên PPU.
- **Ở 720p, dock hero che lối vào lane nam và boss** (thấy trong screenshot Unity baseline).
  - Thuộc B17/A8.
