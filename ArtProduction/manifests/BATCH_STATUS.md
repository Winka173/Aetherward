# Batch status

Statuses: NOT_STARTED | BRIEF_READY | SENT_TO_CODEX | RETURNED | VALIDATING | NEEDS_REVISION | UNITY_VERIFIED | APPROVED | INTEGRATED | BLOCKED.
APPROVED needs the owner. INTEGRATED needs an import into Assets/ with backup + journal.

| Batch | Content | Redraw | New frames | Depends | Status |
|---|---|---|---|---|---|
| B01 | Benchmark + style lock | 77 | 0 | - | UNITY_VERIFIED (77/77, intake 0 blocking, validator 0 blocking; Unity captures 2560x1440/1280x720 with the Blender 2K battlefield + crystal); owner approval pending |
| B02 | Starter heroes complete (7 starters) | 36 | 21 | G1 (owner approves the B01 style) | SENT_TO_CODEX (2026-10-20 21:12, gpt-6.1-sol) |
| B03 | Heroes: tidal, raiden, glacius, zephyr, magnus, seren | 48 | 18 | G1; B02 approved as the hero reference | BRIEF_READY |
| B04 | Heroes: nyxara, ashara, nerissa, voltrix, eirwen, kael | 48 | 18 | G1; B02 approved as the hero reference | BRIEF_READY |
| B05 | Heroes: borun, liora, thalen, vesper, sable, caelis | 48 | 18 | G1; B02 approved as the hero reference | BRIEF_READY |
| B06 | Heroes: oriane, zerith, maelis, solenne, mirel, veyra | 48 | 18 | G1; B02 approved as the hero reference | BRIEF_READY |
| B07 | Heroes: isolde, aeris, doran, elowen, morven | 40 | 15 | G1; B02 approved as the hero reference | BRIEF_READY |
| B08 | Rift-born launch enemies + elite | 20 | 14 | G1 | BRIEF_READY |
| B09 | Faction enemies I: Iron Legion, Ashen Horde, Voidborn | 26 | 13 | G1; B08 approved | BRIEF_READY |
| B10 | Faction enemies II: Frozen Covenant, Stormspire, Corrupted Wilds, Arcane Fractures | 26 | 13 | G1; B08 approved | BRIEF_READY |
| B11 | Bosses | 22 | 24 | G1 | BRIEF_READY |
| B12 | Biomes + Crystal Evolution overlays | 5 | 3 | G1 | MOVED TO LEAD: biomes rendered in Blender (sanctum_env.py --biome); overlays still for Codex |
| B13 | VFX | 64 | 0 | G1 | BRIEF_READY |
| B14 | Icons | 105 | 0 | G1 | BRIEF_READY |
| B15 | Cards | 80 | 0 | B14 approved | BRIEF_READY |
| B16 | Relics | 81 | 0 | B14 approved | BRIEF_READY |
| B17 | UI kit + title | 21 | 0 | G1 | BRIEF_READY |

Updated by the lead after every state change. Evidence lives in ArtProduction/reviews/<batch>/.

Environment (lead, Blender 4.5): World/arena_background 4080x2304 @ PPU 120 + crystal_{intact,cracked,critical} in ArtProduction/generated/World (UNITY_VERIFIED as overrides, not imported).
