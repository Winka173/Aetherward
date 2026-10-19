# Build & chạy

## Yêu cầu
- Unity **6000.4.8f1** (cùng phiên bản Arcane-Brigade) + module Windows Build Support (IL2CPP tuỳ chọn), Android Build Support (SDK/NDK/OpenJDK), iOS Build Support (chỉ xuất Xcode).
- Không cần package ngoài; Test Framework chỉ cần khi chạy test trong Unity.

## Mở project
1. Unity Hub → Add → thư mục repo → mở bằng 6000.4.8f1.
2. Lần import đầu: texture được postprocessor áp pivot/PPU/9-slice từ `Tools/AssetGen/import_settings.json`.
3. **Aetherward > Validate Content and Art** → phải "passed".
4. **Aetherward > Play From Boot**.

Nếu scene bị lỗi khi mở: **Aetherward > Rebuild Scenes** tạo lại 4 scene và Build Settings (scene chỉ chứa marker; `GameRoot` tự khởi tạo).

## Build (menu hoặc batch mode)
| Mục tiêu | Menu | Batch `-executeMethod` | Đầu ra |
|---|---|---|---|
| Windows dev | Aetherward > Build > Windows (Development) | `Aetherward.EditorTools.AetherwardBuild.WindowsDevelopment` | `Builds/WindowsDev/Aetherward.exe` |
| Windows release | … Windows (Release) | `…WindowsRelease` | `Builds/Windows/Aetherward.exe` |
| Android APK dev | … Android APK (Development) | `…AndroidDevelopmentApk` | `Builds/Android/Aetherward-dev.apk` |
| Android AAB | … Android AAB (Release, needs keystore) | `…AndroidReleaseAab` | `Builds/Android/Aetherward.aab` |
| iOS | … iOS Xcode Project (build on macOS) | `…IosXcodeProject` | `Builds/iOS/Xcode` |

Ví dụ Windows (PowerShell):
```
& "C:\Program Files\Unity\Hub\Editor\6000.4.8f1\Editor\Unity.exe" -batchmode -quit -projectPath . `
  -executeMethod Aetherward.EditorTools.AetherwardBuild.WindowsRelease -logFile Builds\windows.log
```
Mỗi build chạy validation trước (thất bại → exit code 2), ghi tóm tắt vào `Builds/build_log.txt`. `Builds/` bị `.gitignore`.

## Cấu hình đã đặt sẵn
- Product name `Aetherward`, company `Winka`, package id `com.winka.aetherward` (tên miền giả định của dự án, không mạo danh bên khác — cần xác nhận trước khi phát hành), version `0.1.0`, Android IL2CPP + ARM64, minSdk 25, landscape (trái/phải).
- **Không có** keystore, chứng chỉ ký iOS, tài khoản store. AAB release cần chủ dự án cấu hình keystore cục bộ. iOS: mở `Builds/iOS/Xcode` trên macOS, chọn Team, Archive.

## Công cụ ngoài Unity (đã dùng trong phiên này)
```
cd Tools/SimHarness
dotnet test Tests                                   # 64 test mô phỏng
dotnet run --project Balance -c Release -- --runs 30  # mô phỏng cân bằng
../fetch_unity_refs.sh && dotnet build UnityCheck   # type-check script Unity (DLL tham chiếu, không commit)
python3 Tools/AssetGen/art/build_all.py             # sinh lại art (từ thư mục gốc repo)
python3 Tools/AssetGen/audio/build_audio.py         # sinh lại âm thanh (cần ffmpeg)
python3 Tools/Localization/build_strings.py         # sinh lại bản dịch
python3 Tools/gen_meta.py                           # tạo .meta còn thiếu (GUID tất định)
```
