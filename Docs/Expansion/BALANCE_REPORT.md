# Balance Report (mở rộng)

Mọi số liệu là **mô phỏng headless** (`Tools/SimHarness/Balance`, AutoPilot theo kịch bản), không phải người chơi thật. 30 seed/lối chơi, Ascension 0, mở khoá toàn bộ nội dung.

## Phase 1 (Light/Shadow, 8 hero, 22 relic, 12 thẻ, 4 kẻ địch, Ignaroth)
| Lối chơi | Toàn bộ nội dung | Chỉ hero/relic launch (`--launch-pool`) | Baseline MVP (60 lượt, phase 0) |
|---|---|---|---|
| thunderstorm | 13/30 | 16/30 | 4/10 |
| frozen_fortress | 9/30 | 20/30 | 8/10 |
| magma_engine | 14/30 | 21/30 | 9/10 |
| mixed_burst | 14/30 | 21/30 | 7/10 |
| glass_cannon | 7/30 | 10/30 | 2/10 |
| eclipse (mới: Seren+Nyxara) | 5/30 | — | — |
| engineers (mới: Borun+Voltrix) | 7/30 | — | — |
| phoenix_gale (mới: Ashara+Kael) | 7/30 | — | — |
| balanced | 18/30 | — | 9/10 |

### Phân tích (đã đo)
- Kẻ địch mới (Mana Leech, Crystal Parasite) + Ignaroth: ảnh hưởng nhỏ — với pool launch, tỉ lệ thắng gần baseline.
- Nguyên nhân chính là **loãng pool**: `--launch-heroes` (relic mới vẫn bật) cho frozen 17/30, `--launch-relics` cho 12/30 ⇒ hero mới chiếm phần lớn mức giảm. Số phản ứng/lượt giảm (~1300 → ~750) vì đội "cầu vồng" gặp nhiều cặp Generic/Neutral hơn cặp Signature.
- Đã chỉnh: Ashara (nhiệt từ sát thương 50→30, nổ 1.8→1.5), Borun (Công 22→26, tường nghiền 0.2, Gia Cố 12%), Nyxara (0.8→1.1, hồi 6s), Ignaroth (HP 1800, dung nham 1.3×, triệu hồi 11s), giảm số Leech/Parasite; chiêu mộ 4 lựa chọn, ưu tiên hero tạo phản ứng Signature với đội; AutoPilot tránh relic rủi ro khi lối chơi không chấp nhận.

### Kết luận & độ tin cậy
- Người chơi mới: hero mới **bị khoá** lúc đầu (mở dần theo meta) ⇒ trải nghiệm gần cột "launch pool" (~50–70% với lối chơi có định hướng).
- Lối chơi toàn bộ nội dung thấp hơn mục tiêu; **chưa cân bằng xong** — để lại cho pass cân bằng tổng thể ở Phase 5 khi đủ 36 hero (KNOWN_ISSUES K-04). Độ tin cậy trung bình: AutoPilot không chơi tối ưu như người.

## Phase 2a (14 kẻ địch + 2 boss + 2 biome)
| Lối chơi | Trước Phase 2a | Sau (Verdant) | Molten Crater (20 seed) | Frostfall (20 seed) |
|---|---|---|---|---|
| thunderstorm | 13/30 | 12/30 | 9/20 | 9/20 |
| frozen_fortress | 9/30 | 9/30 | 5/20 | 9/20 |
| magma_engine | 14/30 | 12/30 | 7/20 | 5/20 |
| mixed_burst | 14/30 | 12/30 | 11/20 | 7/20 |
| glass_cannon | 7/30 | 5/30 | 1/20 | 2/20 |
| eclipse | 5/30 | 2/30 | 6/20 | 1/20 |
| engineers | 7/30 | 5/30 | 5/20 | 5/20 |
| phoenix_gale | 7/30 | 8/30 | 0/20 | 4/20 |
| balanced | 18/30 | 15/30 | 11/20 | 10/20 |
| **Tổng** | 94/270 | 80/270 | 55/180 | 52/180 |

- Lần trộn đầu kẻ địch mới vào đợt thường khiến Siege Colossus một mình gây 44 thất bại ở đợt 17 ⇒ giảm (HP 360, thủ 25, tầm 5.5 m, nã mỗi 6 s, sức 0.8×), lùi thời điểm xuất hiện; bớt Splitter/Burrower/Devourer ở đợt 6/13; Void Priest đợt 18 còn 1.
- Molten ban đầu 2/180 vì ô đặt xa làn ⇒ dời ô (xem `BIOMES.md`).
- Vẫn thấp hơn trước ~15% (nhiễu 30 seed khá lớn); điểm nghẽn chính vẫn là các đợt cũ (9, 14, 18 — Sapper). Hero Nature/Poison (Phase 2b) có phản chế trực tiếp (Rooted, Corroded). Cân bằng tổng ở Phase 5 (K-04).

## Phase 2b (Liora, Thalen, Vesper, Sable; 9 relic, 8 thẻ)
Sát thương mỗi hero (đợt 8, cấp 3, cùng Terra, 60 s, trung bình 4 seed): hero mới nằm trong khoảng của roster cũ (Thalen 765 ~ Borun 536/Terra 1034; Liora 1016; Sable 1067 + hồi máu; Vesper 1745). ⇒ Không phải hero quá yếu/mạnh.

| Lối chơi | Toàn bộ nội dung | `--launch-pool` |
|---|---|---|
| thunderstorm | 10/30 | 12/30 |
| frozen_fortress | 10/30 | 20/30 |
| magma_engine | 7/30 | 20/30 |
| mixed_burst | 10/30 | 16/30 |
| glass_cannon | 8/30 | 9/30 |
| eclipse | 1/30 | 9/30 |
| engineers | 1/30 | 7/30 |
| phoenix_gale | 1/30 | 9/30 |
| verdant_plague (mới) | 1/30 | 2/30 |
| thorn_doctor (mới) | 0/30 | 1/30 |
| balanced | 14/30 | 15/30 |

- Khoảng cách lớn giữa hai cột xác nhận nguyên nhân chính là **loãng pool** (24 hero, 59 relic). Đã thêm trọng số relic theo nguyên tố và chiêu mộ theo số Signature — các lối chơi launch tăng nhẹ (60→63 tổng).
- Các lối chơi khởi đầu bằng 2 hero mở rộng (eclipse, engineers, phoenix, verdant_plague, thorn_doctor) **rất yếu với AutoPilot** (~0–1/30). Một phần do danh sách ưu tiên của bot; một phần do cặp khởi đầu thiếu sát thương diện rộng sớm. **Chưa giải quyết** — mục tiêu chính của pass cân bằng Phase 5 (K-04).

## Phase 3 (36 hero, 81 relic, 80 thẻ)
| Cấu hình (balanced, 60 seed) | Thắng |
|---|---|
| Cuối Phase 2 (`5f504a9`) | 24/60 |
| Phase 3 logic (`0f3984f`) | 7/60 |
| `0f3984f` bỏ 12 hero P3 | 13/60 |
| `0f3984f` bỏ 12 hero + 17 relic P3 | 22/60 (≈ trước) |
| Hiện tại (đề nghị theo nguyên tố ×3/×0.3, bảo đảm ≥1 relic hợp đội & ≥1 hero Signature mỗi lượt đề nghị, bot đánh giá vai trò/độ liên quan) | 13/60 |

Toàn bộ 12 lối chơi (30 seed): 26–32/360 (~8%); `--launch-pool`: 117/360 (~33%).
- **Bisect đã đo**: không có hero/relic P3 nào "hỏng" riêng lẻ; sát thương từng hero mới nằm trong dải roster (đã buff nhẹ Mirel, Oriane, Isolde, Veyra). Sụt giảm là **loãng pool nhân lên** (hero và relic mỗi loại ~½ tỉ lệ thắng). Sự kiện Elemental Shrine không phải nguyên nhân.
- Thử đảo trọng số chiêu mộ sang "cùng nguyên tố" — không đổi (10/60), đã hoàn tác.
- Ý nghĩa: người chơi mới chỉ có hero/relic khởi đầu (mở dần) ⇒ gần cột launch; với toàn bộ nội dung, AutoPilot không xây được đội nhất quán. **Chưa giải quyết** — mục tiêu số 1 của Phase 5 (K-04, mức Cao).

## Phase 5 — pass cân bằng
Thử nghiệm đã đo (30 seed × 12 lối chơi):
| Thay đổi | Toàn bộ nội dung | `--launch-pool` |
|---|---|---|
| Trước pass | 26–32/360 | 108/360 |
| Run pool (18 hero / 45 relic mỗi lượt, có trọng số) | 32 | — |
| Thử: +20% Công/HP cho 24 hero mở rộng (đã hoàn tác) | 39 | — |
| `enemyHpGrowthQuad` 0.015 → 0.013 (giữ) | 41 | 122 (6 lối chơi launch: 93/180 ≈ 52%) |

Kết luận đã đo:
- Lối chơi launch hồi phục về ~52% (Phase 1: ~60%) sau khi kẻ địch/boss mới khiến khó hơn.
- Toàn bộ nội dung với AutoPilot vẫn ~11%. Bisect cho thấy không có món nội dung hỏng; tăng sức mạnh hero mở rộng chỉ giúp ít; giới hạn đề nghị (run pool, bảo đảm liên quan) không giúp ⇒ giới hạn chủ yếu là **bot theo kế hoạch cố định** trong pool lớn. Người chơi thật thích nghi được, nhưng chưa có playtest để xác nhận (K-04).
- Lối chơi khởi đầu bằng cặp hero mở rộng thiên khống chế/hỗ trợ (verdant_plague, thorn_doctor, arcane_void) chết rải rác ở đợt 9–19 như các đội khác nhưng thường hơn: cặp khởi đầu thiếu sát thương sớm.
- Run pool được giữ vì lý do thiết kế (mỗi lượt khác nhau, đề nghị mạch lạc), không phải vì cải thiện số liệu.
