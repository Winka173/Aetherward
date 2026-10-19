# Kế hoạch mở rộng (Post-MVP)

Thứ tự phụ thuộc: hạ tầng dữ liệu → nguyên tố/phản ứng → hero/trait → kẻ địch/boss → biome → relic/fusion → chế độ/ascension → bond/codex → cân bằng. Mỗi phase phải tự chơi được và test được. Phạm vi tính theo năng lực, không hứa lịch.

## Phase 1 — Hạ tầng + Light/Shadow + Heroes Unbound
1. **Mô hình 12 nguyên tố** (thêm cả 6 nguyên tố vào enum ngay để hạ tầng ổn định; nội dung bật theo stage): `Light=7, Shadow=8, Nature=9, Poison=10, Arcane=11, Void=12`. `elements.json` mô tả màu, status, stage.
2. **Hệ status dùng chung** (`Battle.Statuses.cs`): burn, armor_crack, slow, stun, vulnerable, illuminate, doom, root, poison, resonant, unstable, brittle, reaction_vuln. Dùng bởi nguyên tố, phản ứng, kỹ năng, relic.
3. **Phản ứng khai báo**: `reactions.json` có `ops` (damage/status/apply/zone/pull/knock/chain/consume/hero_shield/hero_heal/crystal_shield/cleanse/delayed/echo/refund/suppress/spread). 15 phản ứng gốc giữ code cũ. `fields` mô tả zone dữ liệu (`ZoneKind.Field`). Ma trận 66 cặp: Signature / Generic / Neutral / BlockedByDesign.
4. **Light/Shadow**: Illuminated (thanh tẩy buff/khiên địch, giảm sát thương địch), Doom (stack, xử tử dưới ngưỡng, boss nhận thêm sát thương). Phản ứng: Eclipse, Hallowed Bulwark, Solar Flare, Glimmer Tide, Hellfire, Black Tide.
5. **Hero**: Seren (Light), Nyxara (Shadow) + 6 hero H1: Ashara, Nerissa, Voltrix, Eirwen, Kael, Borun — kỹ năng/nội tại/2 nhánh tiến hoá đổi cơ chế thật.
6. **Trait** (12): roll khi tuyển mộ, có điều kiện hợp lệ, lưu trong `HeroRunState`.
7. **Relic +20, thẻ +10**, **kẻ địch** Mana Leech, Crystal Parasite, **boss** Ignaroth (đợt 10 biến thể / Boss Rush), **difficulty.json** Ascension 1–5 dạng module.

## Phase 2 — Corrupted Realms + Nature/Poison
- Nature (Rooted, vùng sinh trưởng), Poison (stack, Corroded, lây khi chết, có trần).
- Phản ứng: Wildfire, Overgrowth, Toxic Shock, Venom Shards, Sanctuary, Plague, Blight Garden, Toxic Combustion, Venom Flow, Frost Roots.
- Hero: Liora, Thalen, Vesper, Sable.
- **Biome**: `arenas.json` nhiều bàn; Verdant Sanctuary (gốc), Molten Crater (dung nham định kỳ, cầu hẹp), Frostfall Bastion (ô băng, vỏ băng phá được, lane mở dần). Kiểm tra đường đi.
- 12 kẻ địch mới có phản chế, affix dữ liệu + luật xung khắc, boss Seraphyne, Gravemaw.

## Phase 3 — Aether Convergence + Arcane/Void
- Arcane (Resonant, echo có giới hạn), Void (Unstable, sụp đổ có giới hạn).
- Phản ứng: Overcharge, Spellflare, Mana Tide, Singularity, Gravemaw (field), Abyss Mark, Prism Chant, Astral Seal, Paradox.
- Hero: Caelis, Oriane, Zerith, Maelis + Solenne, Mirel, Veyra, Isolde, Aeris, Doran + Elowen, Morven ⇒ **36**.
- Relic +20, ≥10 fusion, ≥12 keystone, **Elemental Awakening**.

## Phase 4 — Endless Fracture
- Biome Shattered Aether, Stormspire Citadel, Sunken Archive ⇒ 6.
- Chế độ: Endless (wave director sau đợt 20, rút lui tự nguyện), Daily Seed, **Boss Rush** (chế độ thứ 4 — chi phí thấp, khác biệt rõ: chuỗi boss, shop mỗi đợt, đội khởi đầu cấp 3).
- Ascension 6–10, kẻ địch tới 45+, boss tới 12.

## Phase 5 — Legends of Aether
- ≥8 Hero Bond tương tác thật, codex ma trận phản ứng, lịch sử lượt mở rộng, đạt 150+ relic/thẻ có ý nghĩa, batch cân bằng hàng trăm seed, tài liệu.

## Phase 6 — RC (có điều kiện)
- Cần thiết bị/Unity thật; không tự phát hành.

## Thiết kế nguyên tố mới (chốt)
| Nguyên tố | Status khi gắn | Quy tắc |
|---|---|---|
| Light | Illuminated 4 s | khi gắn: xoá 50% khiên, buff tốc/giáp của địch; địch gây −15% sát thương; không chồng |
| Shadow | Doom +1 (tối đa 5) | non-boss: HP ≤ 4%×stack ⇒ bị xử tử (elite: một nửa ngưỡng); boss: +3%/stack sát thương nhận |
| Nature | Rooted 0.8 s | đứng yên nhưng vẫn đánh; miễn root 1.5 s sau đó; boss ⇒ chậm 30% thay vì root |
| Poison | +1 stack (tối đa 10), 5 s | DoT/stack; ≥5 stack: Corroded (−30% giáp); chết ⇒ lây ½ stack sang 1 địch gần (độ sâu lây ≤ 2) |
| Arcane | Resonant 5 s | phản ứng kế tiếp trên mục tiêu +30% sát thương rồi tiêu thụ |
| Void | Unstable +1 (tối đa 3) | đủ 3 ⇒ sụp đổ nhỏ: hút nhẹ (bán kính 1.6, không với boss) + sát thương Void; hồi 2 s |

Time / Crystal là **trường phái đặc biệt**, không phải nguyên tố chính, không vào ma trận cặp.
