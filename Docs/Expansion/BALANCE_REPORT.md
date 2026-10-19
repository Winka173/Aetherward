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
