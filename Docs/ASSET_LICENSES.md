# Giấy phép tài sản (Asset Licenses)

| Nhóm | Nguồn | Giấy phép | Ghi chú |
|---|---|---|---|
| Sprite hero, enemy, boss, crystal, arena, VFX, icon, UI skin (`Assets/_Aetherward/Resources/Art/**`) | Sinh hoàn toàn bằng script trong repo: `Tools/AssetGen/art/*.py` (pycairo, vector) | Nguyên bản của dự án | Không dùng ảnh/texture bên ngoài, không AI image generation, không vẽ tay. Tái tạo: `python3 Tools/AssetGen/art/build_all.py`. Danh sách từng file: `Docs/ASSET_MANIFEST.json`. |
| SFX + nhạc (`Assets/_Aetherward/Resources/Audio/**`) | Tổng hợp bằng numpy: `Tools/AssetGen/audio/build_audio.py`, mã hoá OGG bằng ffmpeg/libvorbis | Nguyên bản của dự án | Không dùng sample bên ngoài. Giai điệu viết bằng code (pentatonic/modal). |
| Font Be Vietnam Pro (Black/SemiBold/Medium) | Lấy từ dự án Arcane-Brigade cùng chủ sở hữu (gốc: github.com/bettergui/BeVietnamPro) | SIL Open Font License 1.1 | Kèm `Resources/Fonts/BeVietnamPro-OFL.txt`. Hỗ trợ tiếng Việt. |
| Font Lilita One | Như trên (gốc: Juan Montoreano) | SIL OFL 1.1, Reserved Font Name "Lilita" | Kèm `Resources/Fonts/LilitaOne-OFL.txt`. Chỉ dùng cho chữ số. |

Không có tên nhân vật, thương hiệu hoặc asset của Genshin/Steam hay trò chơi khác. Tên "Aetherward" là tên làm việc, cần kiểm tra thương hiệu trước khi phát hành.


## Art redraw (2026-10, Dark Mythic direction)
- Character, icon, VFX and UI art from batch B01 onward is produced for the project by the art specialist agent (Codex, image generation + Blender) from briefs in `ArtHandoff/requests/`; provenance per file in `Docs/ASSET_MANIFEST.json` and `ArtHandoff/returns/<batch>/DELIVERABLE_MANIFEST.json`.
- Battlefields and the Crystal are rendered by the lead with Blender (`Tools/ArtPipeline/blender/sanctum_env.py`, `crystal_states.py`). Third-party inputs are CC0 only (Poly Haven scans and models), listed with URLs and authors in `ArtProduction/REFERENCE_MANIFEST.json` and re-fetched by `Tools/ArtPipeline/fetch_polyhaven.py`.

## Ultimate cues (2026-10-23)

`Assets/_Aetherward/Resources/Audio/Sfx/ult_*.wav`: 12 cue tổng hợp nguyên bản bằng `Tools/AudioPipeline/ultimate_cues.py` (Python standard library, seed cố định). Không dùng sample bên ngoài. Tái tạo từ repo root bằng `python Tools/AudioPipeline/ultimate_cues.py`; giữ các file `.meta` để GUID Unity ổn định.
