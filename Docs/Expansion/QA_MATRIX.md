# QA Matrix

Trạng thái: `NOT_STARTED` / `IMPLEMENTED_UNVERIFIED` (code có, chưa kiểm chứng trong Unity) / `VERIFIED` (có bằng chứng lệnh) / `BLOCKED`.

Mô phỏng (pure C#) được kiểm chứng bằng `dotnet test`; mọi thứ hiển thị trong Unity là tối đa `IMPLEMENTED_UNVERIFIED`.

| Hạng mục | Mô phỏng | Unity | Bằng chứng |
|---|---|---|---|
| Baseline MVP | VERIFIED | IMPLEMENTED_UNVERIFIED | 64/64 test, UnityCheck 0 lỗi |
| Mô hình 12 nguyên tố + ma trận 66 cặp | VERIFIED | IMPLEMENTED_UNVERIFIED | `ElementExpansionTests.EverySixtySixPairHasAnExplicitCategory`, `ContentPassesValidation` |
| 15 phản ứng gốc không đổi | VERIFIED | IMPLEMENTED_UNVERIFIED | `ReactionTests` (16), mô phỏng 60 lượt trùng baseline |
| Status Illuminated/Doom/Root/Poison/Resonant/Unstable | VERIFIED | IMPLEMENTED_UNVERIFIED | 7 test trong `ElementExpansionTests` |
| 25 phản ứng mới + field | VERIFIED (kích hoạt, không NaN, trong trần) | IMPLEMENTED_UNVERIFIED | `EveryReactionResolvesWithinCaps`, `RandomTwelveElementStormStaysBounded` |
| Art/âm thanh nguyên tố mới | VERIFIED (file tồn tại) | IMPLEMENTED_UNVERIFIED (chưa xem trong game) | `AssetContractTests`, `Docs/Previews/expansion_elements.png` |
