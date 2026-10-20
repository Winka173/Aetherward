# Sprite atlas plan (packed and checked here; not imported into Unity)

Tight-rect shelf packing, 2 px padding, 2048² pages, pages in `Temp/ArtAtlas/`. Unity SpriteAtlas assets are NOT generated: that needs the Unity Editor (BLOCKED in this environment). The game currently loads single textures via Resources.

| Group | Sprites | Full-rect MB (RGBA32) | Packed pages | Packed MB (RGBA32) | ASTC 6x6 MB (est.) | Bleed issues |
|---|---|---|---|---|---|---|
| Cards | 80 | 7.8 | 1 | 16.0 | 1.8 | 0 |
| Enemies | 104 | 44.0 | 3 | 48.0 | 5.3 | 0 |
| Heroes | 252 | 153.8 | 7 | 112.0 | 12.4 | 0 |
| Icons | 122 | 5.7 | 1 | 16.0 | 1.8 | 0 |
| Portraits | 36 | 5.1 | 1 | 16.0 | 1.8 | 0 |
| Relics | 81 | 5.1 | 1 | 16.0 | 1.8 | 0 |
| UI | 30 | 5.0 | 1 | 16.0 | 1.8 | 0 |
| Vfx | 76 | 14.5 | 1 | 16.0 | 1.8 | 0 |
| World | 14 | 76.5 | — | — | — | backgrounds stay single textures |
