# Plan — vertical slices (ưu tiên theo giá trị × khả năng kiểm chứng trong môi trường này)

| # | Slice | Phase | Tiêu chí chấp nhận (kiểm được) |
|---|---|---|---|
| S1 | Balance simulator v2: ≥1000 seed, nhiều policy draft, CI-able, khoảng tin cậy, phát hiện outlier, bất biến | 10 | báo cáo `Reports/Balance/` từ mã thật; test bất biến; ghi rõ máy/thời gian |
| S2 | AI utility scoring có thể soi + preset chiến thuật + dữ liệu inspector | 2 | test chuyển mục tiêu/hysteresis/ưu tiên mối đe doạ; tái lập theo seed; cân bằng không tụt |
| S3 | Draft/shop công bằng: lựa chọn khác nhau, ≥1 lựa chọn dùng được, pity, khoá shop, stream RNG riêng | 4 | test xác suất/tái lập/không exploit vàng |
| S4 | Run breakdown: nguồn gốc sát thương (trực tiếp/DoT/phản ứng), closest save, nâng cấp quyết định, báo cáo mẫu thật | 8 | test không đếm đôi; báo cáo mẫu từ seed |
| S5 | Save ops: xoay vòng backup, fixture save cũ, feature flags | 12 | test migration/corrupt/fixture |
| S6 | Content validation CLI + đồ thị proc + báo cáo | 9 | `Reports/ContentValidation/`, exit code ≠ 0 khi lỗi |
| S7 | Crystal Evolution (3 lựa chọn loại trừ, feature flag) + preview tầm/đe doạ | 5 | test hiệu lực/giới hạn; UI unverified |
| S8 | Juice & a11y trình bày: gộp số sát thương, tầng VFX, flash, pause khi mất focus | 1, 7 | type-check; test gộp số (logic thuần); **không kiểm bằng mắt** |
| S9 | Encounter director log + kiểm tra soak | 6 | log ngân sách mỗi đợt, test soak |
| S10 | Docs cuối: FINAL_IMPLEMENTATION_REPORT, ARCHITECTURE_DELTA, UX_AND_COMBAT_GUIDE, RELEASE_CHECKLIST | — | |

Bị chặn (ghi nhận, không giả lập): đo FPS/GC/draw call thật, build nền tảng, playtest người thật, ảnh/clip trong game.
