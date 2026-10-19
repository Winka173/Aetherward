# Quyết định mở rộng (Expansion Decision Log)

Bổ sung cho `Docs/DECISIONS.md` (D-01..D-18). ID dạng X-nn.

| ID | Quyết định | Lý do |
|---|---|---|
| X-01 | Mở rộng trên nền hiện có, không viết lại. Giữ nguyên ID nội dung, GUID meta (sinh tất định), scene, save. | Hợp đồng không-viết-lại của prompt; nền MVP đã test. |
| X-02 | `Element` là enum **append-only với giá trị số cố định** (None=0…Earth=6, Light=7, Shadow=8, Nature=9, Poison=10, Arcane=11, Void=12). Nội dung/sav dùng **khoá chuỗi**; mảng theo ordinal chỉ trong runtime và `ElementDamage` (save cũ 7 ô nạp đúng). | Hiệu năng mảng trong mô phỏng + ID ổn định. Không có serialize enum theo ordinal ở chỗ nào khác. |
| X-03 | Thêm cả 12 nguyên tố vào hạ tầng ngay Phase 1; **nội dung** (hero/thẻ/relic) bật theo stage E1→E3. | Tránh 3 lần migration hạ tầng; mỗi stage vẫn chơi được. |
| X-04 | 15 phản ứng gốc giữ nguyên code `switch` (đã test, đã cân bằng). Phản ứng mới dùng **op khai báo** trong `reactions.json`. | Không đổi hành vi cũ; nội dung mới sửa không cần code. |
| X-05 | Ma trận 66 cặp: 35 Signature (15 gốc + 20 mới), một số cặp **Generic** có tên riêng theo mẫu dữ liệu (Solar Flare, Glimmer Tide, Hellfire, Black Tide, Paradox), các cặp còn lại Generic tự sinh ("Bùng nổ A·B") hoặc Neutral (cùng tồn tại, có lý do). Không cặp nào bị bỏ qua im lặng; test phủ đủ 66. | Tránh bẫy 66 phản ứng riêng; vẫn đọc được. |
| X-06 | Khi mục tiêu có nhiều aura: duyệt theo (lượng giảm dần, ordinal tăng dần), chọn cặp **có phản ứng** đầu tiên; Neutral thì bỏ qua sang aura kế. Với 6 nguyên tố gốc kết quả giống hệt bản cũ. | Tất định, không phụ thuộc thứ tự Dictionary. |
| X-07 | Zone dữ liệu (`ZoneKind.Field` + `fields` trong `reactions.json`) cho mọi vùng mới; trần số lượng theo loại field. | Không phình `enum`/`switch`; giữ hiệu năng. |
| X-08 | Kỹ năng hero là "kind" dùng lại được; kind mới nằm ở `Battle.SkillsExt.cs`. Không có `if (heroId == …)`. | Đúng hợp đồng data-driven. |
| X-09 | Tường của Borun **không chặn cứng**: là field làm chậm 75% + crack giáp; không thể đặt trong 1.5 đơn vị quanh Pha Lê; tối đa 2–3 tường. | Bảo đảm luôn có đường đi (spec: không chặn vĩnh viễn mọi lối). |
| X-10 | Echo (Caelis, Spellflare, Overcharge) gắn cờ `echo`; cast echo **không** phát sự kiện skill_cast nên không thể echo lại; mỗi hero có hồi echo riêng. | Chống vòng lặp vô hạn. |
| X-11 | Chế độ thứ 4 = **Boss Rush** (không chọn Draft Challenge). | Dùng lại boss + shop, luật khác rõ (chuỗi boss, đội cấp 3, shop mỗi đợt), chi phí kỹ thuật thấp nhất. |
| X-12 | Ascension là dữ liệu `difficulty.json` (module có id), không còn `if (asc >= n)` rải rác; giữ đúng hiệu ứng asc 1–4 cũ cho save cũ. | Data-driven, test được từng bậc. |
| X-13 | Biome = `arenas.json` (nhiều bàn); `ContentDatabase.Arena` giữ là bàn mặc định để code/scene cũ chạy y nguyên. | Tương thích ngược. |
| X-14 | Determinism: **sequence determinism** trên cùng nền tảng (cùng seed + phiên bản nội dung ⇒ cùng chuỗi offer/spawn/kết quả mô phỏng). Float không fixed-point ⇒ không hứa khớp bit giữa nền tảng. Cài đặt đồ hoạ không chạm RNG gameplay (RNG hiển thị là `UnityEngine.Random`). | Khớp D-10; có test. |
