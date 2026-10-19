# Kiểm tra môi trường (Environment Audit)

Ngày: 2026-10-19 · Phiên làm việc: Claude Code (cloud container Linux, không phải máy Windows của chủ dự án).

## Repository
- `Winka173/Aetherward`: rỗng khi bắt đầu (không có commit, không có project Unity). Không có file nào bị ghi đè.
- Tham chiếu chất lượng: `Winka173/Arcane-Brigade` (Unity **6000.4.8f1**, built-in render pipeline, chỉ dùng các module builtin, UI vẽ bằng IMGUI, font OFL trong `Resources/Fonts`). Aetherward dùng lại cấu hình `ProjectSettings/` và bộ package builtin của dự án này làm nền đã được chứng minh mở được bằng 6000.4.8f1, đổi tên/ID cho Aetherward.

## Công cụ có trong container
| Công cụ | Trạng thái | Ghi chú |
|---|---|---|
| Unity Editor | **Không có** | Không cài được trên Linux container này (không có Unity Hub/licence). Mọi bước cần Editor đều được đánh dấu *chưa kiểm chứng trong Unity*. |
| .NET SDK 8.0.131 | Có (cài từ Ubuntu archive) | Dùng để build/test toàn bộ lớp mô phỏng (pure C#, `netstandard2.1`, C# 9 — khớp giới hạn của Unity 6). |
| UnityEngine reference DLL | Tải từ NuGet (`UnityEngine.Modules 2021.3.33`, `Unity3D.UnityEngine.UI`) | **Chỉ để type-check** lớp presentation Unity ngoài Editor; không commit (`Tools/UnityRefs/` bị ignore). API 2021.3 ≈ API dùng trong 6000.4; khác biệt nhỏ vẫn có thể xuất hiện khi mở bằng Unity thật. |
| Blender 4.0.2 | Có (apt) | Có sẵn cho pipeline 3D→2D; pipeline art chính chọn vector 2D (xem DECISIONS D-07). |
| Python 3.13 + numpy, Pillow, pycairo | Có | Sinh sprite vector, VFX, UI skin, âm thanh tổng hợp, contact sheet. |
| MCP Unity Editor / Blender MCP / image generation | **Không có** trong phiên này | Không giả lập; dùng script tái tạo được thay thế. |
| Git | Có | Commit lên `main` theo yêu cầu chủ dự án. |

## Hệ quả
1. Lớp mô phỏng gameplay (combat, nguyên tố, phản ứng, wave, draft, shop, relic, tiến hoá, save) **được compile và test thật** bằng `dotnet test` và chạy mô phỏng cân bằng headless bằng `dotnet run`.
2. Lớp Unity (MonoBehaviour, scene, IMGUI, editor tools) được compile-check với DLL tham chiếu, **chưa chạy trong Unity Editor**. Chủ dự án cần mở bằng Unity 6000.4.8f1 trên Windows và chạy menu `Aetherward > Validate Content` + Test Runner để xác nhận.
3. Không có build Windows/Android/iOS nào được tạo trong phiên này. Script build (`Aetherward > Build > ...`) đã viết sẵn nhưng chưa thực thi.
4. Không có ảnh chụp màn hình từ Unity; ảnh preview trong `Docs/Previews/` là contact sheet của asset nguồn do pipeline Python sinh ra, không phải capture runtime.
