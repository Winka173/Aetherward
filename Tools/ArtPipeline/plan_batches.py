#!/usr/bin/env python3
"""Full-redraw batch plan (ArtProduction/REGEN_PLAN.md) -> ArtHandoff/requests/<batch>/batch.json for B02..B17.

  python Tools/ArtPipeline/plan_batches.py [--write] [--briefs]

Checks coverage before writing: every live sprite under Resources/Art is in exactly one batch (B01 included),
and every new animation frame (hero *_attack x3, enemy _attack, boss _attack/_tell) is assigned once.
--briefs also runs `handoff.py request` + `handoff.py brief` for each batch. Exit 1 on a coverage gap.
"""
import argparse
import fnmatch
import glob
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artlib as A  # noqa: E402
from handoff import HANDOFF, jsonc  # noqa: E402

C = A.CONTENT
HEROES = jsonc(os.path.join(C, "heroes.json"))["heroes"]
ENEMIES = jsonc(os.path.join(C, "enemies.json"))["enemies"]
BOSSES = [e["id"] for e in ENEMIES if e.get("boss")]
HERO_FRAMES = ["idle", "cast", "downed", "evoA", "evoA_cast", "evoB", "evoB_cast"]
HERO_NEW = [("attack", "idle"), ("evoA_attack", "evoA"), ("evoB_attack", "evoB")]
B01_REFS_HERO = ["ArtHandoff/returns/B01/exports/Art/Heroes/%s.png" % n for n in
                 ("ignis_idle", "ignis_cast", "ignis_evoA", "terra_idle", "sylph_idle", "marina_idle")]
B01_REFS_ENEMY = ["ArtHandoff/returns/B01/exports/Art/Enemies/%s.png" % n for n in ("grunt_a", "juggernaut_a", "hexcaster_a", "storm_harpy_a")]
B01_REFS_BOSS = ["ArtHandoff/returns/B01/exports/Art/Enemies/rift_warden_a.png"]
B01_REFS_ICON = ["ArtHandoff/returns/B01/exports/Art/Icons/%s.png" % n for n in ("element_fire", "status_burn", "reaction_vaporize", "ui_crystal")]
B01_REFS_UI = ["ArtHandoff/returns/B01/exports/Art/UI/%s.png" % n for n in ("panel_dark", "button_primary_normal", "card_rare")]
B01_REFS_VFX = ["ArtHandoff/returns/B01/exports/Art/Vfx/%s.png" % n for n in ("impact_fire", "zone_burning_ground", "fireball", "telegraph")]
B01_REFS_WORLD = ["ArtHandoff/returns/B01/exports/Art/World/arena_background.png", "ArtHandoff/returns/B01/exports/Art/World/crystal_intact.png",
                  "ArtHandoff/returns/B01/previews/style_frame_1080p.png"]

HERO_NOTE = ("Per hero, generate the identity frame (`_idle`) first, then every other frame with it attached as reference. "
             "The evolution identity frames (`_evoA`, `_evoB`) are generated from the approved `_idle`; their `_cast` / `_attack` from them. "
             "Attack frames: pose only - **never** paint the projectile, beam or slash (VFX are separate sprites); keep the extended weapon "
             "inside the icon box (columns 40-360). Portraits: head and shoulders from the identity frame, same light, dark vignette.")
ENEMY_NOTE = ("Per enemy: `_a` (walk contact, identity frame) first, then `_b` (passing) and `_attack` with `_a` attached as reference. "
              "Respect the size class heights of COMMON_CONTRACT §4. Faction motifs and accents: ART_BIBLE §7 'Enemies / factions / bosses'.")
BOSS_NOTE = ("Bosses are 512x512, shown x1.25 (~230-250 px tall at 1080p). Four frames each: `_a` / `_b` (heavy walk), `_tell` (anticipation "
             "pose held during the ground telegraph - weapon raised, glow building on the weapon only), `_attack` (impact). No red ground glow "
             "(the telegraph sprite owns that); keep space at the feet. Each boss must read as its faction's apex and break the human rhythm.")


def hero_assets(hid, live=True, new=True):
    a = ["Heroes/%s_%s" % (hid, f) for f in HERO_FRAMES] if live else []
    n = [{"id": "Heroes/%s_%s" % (hid, s), "like": "Heroes/%s_%s" % (hid, like)} for s, like in HERO_NEW] if new else []
    return a, n


def hero_group(gid, ids, title, portraits=True):
    assets, new = [], []
    for h in ids:
        a, n = hero_assets(h)
        assets += a
        new += n
        if portraits:
            assets.append("Portraits/" + h)
    return {"id": gid, "title": title, "priority": "P1", "required": True, "assets": assets, "new": new}


def enemy_group(gid, ids, title, with_ab=True):
    assets, new = [], []
    for e in ids:
        if with_ab:
            assets += ["Enemies/%s_a" % e, "Enemies/%s_b" % e]
        new.append({"id": "Enemies/%s_attack" % e, "like": "Enemies/%s_a" % e})
        if e in BOSSES:
            new.append({"id": "Enemies/%s_tell" % e, "like": "Enemies/%s_a" % e})
    return {"id": gid, "title": title, "priority": "P1", "required": True, "assets": assets, "new": new}


def by_tag(tag):
    return [e["id"] for e in ENEMIES if tag in e.get("tags", []) and not e.get("boss")]


def batches():
    hero_ids = [h["id"] for h in HEROES]
    b01_heroes = ["ignis", "terra", "sylph", "marina"]
    rest = [h for h in hero_ids if h not in b01_heroes + ["cinder", "volt", "freya"]]
    out = {}
    # B02: finish the B01 heroes (evolutions + attack frames) and the remaining three starters
    g_finish = {"id": "b01_heroes_finish", "title": "Finish the B01 heroes: evolutions and attack frames", "priority": "P1", "required": True,
                "assets": ["Heroes/%s_%s" % (h, f) for h in ("terra", "sylph", "marina") for f in ("evoA", "evoA_cast", "evoB", "evoB_cast")],
                "new": [n for h in b01_heroes for n in hero_assets(h, live=False)[1]],
                "design": "Use each hero's approved B01 `_idle` export as the identity reference (Ignis: also its approved evoA/evoB)."}
    out["B02"] = {"title": "Starter heroes complete (7 starters)", "goal": "Every starter hero fully drawn: all poses, both evolutions, attack frames, portraits.",
                  "priority": "high", "depends": "G1 (owner approves the B01 style)", "styleRefs": B01_REFS_HERO, "notes": HERO_NOTE,
                  "groups": [g_finish, hero_group("starters", ["cinder", "volt", "freya"], "Cinder, Volt, Freya - full set")]}
    for i, chunk in enumerate([rest[0:6], rest[6:12], rest[12:18], rest[18:24], rest[24:]]):
        b = "B%02d" % (3 + i)
        out[b] = {"title": "Heroes: " + ", ".join(chunk), "goal": "Full set for %d heroes: 7 live poses + 3 new attack frames + portrait each." % len(chunk),
                  "priority": "normal", "depends": "G1; B02 approved as the hero reference", "styleRefs": B01_REFS_HERO, "notes": HERO_NOTE,
                  "groups": [hero_group("heroes", chunk, "Heroes")]}
    launch = ["runner", "swarmling", "shieldbearer", "sapper", "warded", "summoner", "banner", "mimic", "riftling", "ravager"]
    out["B08"] = {"title": "Rift-born launch enemies + elite", "goal": "Every launch enemy redrawn with walk a/b and a new attack frame; attack frames for the B01 enemies.",
                  "priority": "high", "depends": "G1", "styleRefs": B01_REFS_ENEMY, "notes": ENEMY_NOTE,
                  "groups": [enemy_group("launch", launch, "Launch enemies and the Ravager elite"),
                             enemy_group("b01_attack", ["grunt", "juggernaut", "hexcaster", "storm_harpy"], "Attack frames for the B01 enemies", with_ab=False)]}
    f1 = by_tag("iron_legion") + by_tag("ashen_horde") + by_tag("voidborn")
    f2 = [e for e in by_tag("frozen_covenant") + by_tag("stormspire") + by_tag("corrupted_wilds") + by_tag("arcane_fractures") if e != "storm_harpy"]
    out["B09"] = {"title": "Faction enemies I: Iron Legion, Ashen Horde, Voidborn", "goal": "Walk a/b + attack for %d faction enemies." % len(f1),
                  "priority": "normal", "depends": "G1; B08 approved", "styleRefs": B01_REFS_ENEMY, "notes": ENEMY_NOTE,
                  "groups": [enemy_group("factions1", f1, "Iron Legion, Ashen Horde, Voidborn")]}
    out["B10"] = {"title": "Faction enemies II: Frozen Covenant, Stormspire, Corrupted Wilds, Arcane Fractures",
                  "goal": "Walk a/b + attack for %d faction enemies." % len(f2), "priority": "normal", "depends": "G1; B08 approved",
                  "styleRefs": B01_REFS_ENEMY, "notes": ENEMY_NOTE, "groups": [enemy_group("factions2", f2, "Frozen Covenant, Stormspire, Corrupted Wilds, Arcane Fractures")]}
    out["B11"] = {"title": "Bosses", "goal": "All 12 bosses: walk a/b, tell and attack frames (Rift Warden: tell + attack only).",
                  "priority": "normal", "depends": "G1", "styleRefs": B01_REFS_BOSS + B01_REFS_ENEMY[:1], "notes": BOSS_NOTE,
                  "groups": [enemy_group("bosses", [b for b in BOSSES if b != "rift_warden"], "Bosses"),
                             enemy_group("warden", ["rift_warden"], "Rift Warden tell/attack", with_ab=False)]}
    out["B12"] = {"title": "Biomes + Crystal Evolution overlays", "goal": "The five remaining biome battlefields as 8-layer sources + flats, and three new Crystal path overlays.",
                  "priority": "normal", "depends": "G1", "styleRefs": B01_REFS_WORLD,
                  "notes": ("Follow the B01 battlefield method exactly (Blender scene placed from the biome's own arena geometry, ground depth = y / 0.62, ortho "
                            "38.3 deg, 30 units across 2400 px; 8 layers per ART_BIBLE §7; painterly finish that never moves lanes or nodes). Each guide in "
                            "references/guides/ shows THAT biome's lanes, nodes, special-node traits, hazard points and covers - hazard and cover spots must read as "
                            "places where something happens (vents, rift scars, lightning-rod battlements, flooded stairs, ice walls) without glowing like decals. "
                            "Biome identity (from data): molten_crater = basalt bridges over lava, vents beside them; frostfall_bastion = fortress in a blizzard, frozen tiles, "
                            "ice covers, diagonal gates; shattered_aether = floating islands over the rift; stormspire_citadel = citadel on a storm peak, battlements, lightning rods; "
                            "sunken_archive = drowned library, flooded north/south stairs, tome nodes. Keep the ground value budget (15-45%) - the Crystal stays the focal point.\n\n"
                            "Crystal path overlays (new, 320x400, same pivot as the Crystal, transparent except the addition, registered to the B01 crystal_intact): "
                            "`crystal_path_bastion` = a carved stone-and-gold bastion collar and a faint shield shell; `crystal_path_pulse` = an arcane ring-halo of runes "
                            "around the upper crystal; `crystal_path_thorn` = earth-thorn spikes growing from the collar. Overlays are drawn ON TOP of any crystal state."),
                  "groups": [{"id": "biomes", "title": "Biome battlefields", "priority": "P1", "required": True,
                              "assets": ["World/bg_molten_crater", "World/bg_frostfall_bastion", "World/bg_shattered_aether", "World/bg_stormspire_citadel", "World/bg_sunken_archive"]},
                             {"id": "crystal_paths", "title": "Crystal Evolution overlays (new)", "priority": "P2", "required": True,
                              "new": [{"id": "World/crystal_path_%s" % p, "like": "World/crystal_intact"} for p in ("bastion", "pulse", "thorn")]}]}
    out["B13"] = {"title": "VFX", "goal": "Every remaining VFX sprite redrawn in the B01 VFX language.", "priority": "normal", "depends": "G1",
                  "styleRefs": B01_REFS_VFX,
                  "notes": ("Tiers and tint rules: ART_BIBLE §7 'VFX tiers' and COMMON_CONTRACT §4. Fields and zones are top-down circular ground decals "
                            "(the game squashes them to 0.62), soft edges, inner alpha <= 55% so units stay readable on top; their identity comes from the "
                            "field's element and name (table below). Impacts: small, fast-reading, <= 60% alpha over the centre. Projectiles point +X. "
                            "`spark` is WHITE only (tinted). `coin` is a small ancient gold coin with a rune."),
                  "groups": [{"id": "vfx", "title": "VFX", "priority": "P1", "required": True, "assets": ["Vfx/*"]}]}
    out["B14"] = {"title": "Icons", "goal": "All remaining icons in the B01 engraved-medallion language.", "priority": "normal", "depends": "G1",
                  "styleRefs": B01_REFS_ICON,
                  "notes": ("One engraved medallion language (ART_BIBLE §7 'HUD & icons'). Shape carries meaning, colour supports it; readable at 32 px. "
                            "Element icons use the element shape cues; reaction icons combine the two element symbols into one merged motif; status icons are a "
                            "small symbol on a ring; trait icons are a symbol on a hexagonal plate; ui icons are plain glyphs on a small disc. No text."),
                  "groups": [{"id": "icons", "title": "Icons", "priority": "P1", "required": True, "assets": ["Icons/*"]}]}
    out["B15"] = {"title": "Cards", "goal": "All 80 draft cards: painted card art (the frame comes from UI/card_*).", "priority": "normal", "depends": "B14 approved",
                  "styleRefs": B01_REFS_ICON + B01_REFS_UI[2:],
                  "notes": ("160x160 painted vignettes (not medallions): a small scene or object that shows the card's effect, dark mythic palette, one focal "
                            "element-coloured highlight, readable at 96 px. Hero specialization cards (`spec_<hero>_*`) show that hero's signature prop or move in the "
                            "approved hero design. No text."),
                  "groups": [{"id": "cards", "title": "Cards", "priority": "P1", "required": True, "assets": ["Cards/*"]}]}
    out["B16"] = {"title": "Relics", "goal": "All 81 relics as painted artefacts.", "priority": "normal", "depends": "B14 approved", "styleRefs": B01_REFS_ICON,
                  "notes": ("128x128 single artefact objects on transparency, three-quarter view, the shared light rig, rune-etched metal / crystal / bone "
                            "materials; fusion relics (descriptions starting with 'Fusion of') visibly combine their two parent relics. No text."),
                  "groups": [{"id": "relics", "title": "Relics", "priority": "P1", "required": True, "assets": ["Relics/*"]}]}
    out["B17"] = {"title": "UI kit + title", "goal": "Every remaining UI sprite in the B01 HUD language, plus the title emblem.", "priority": "normal",
                  "depends": "G1", "styleRefs": B01_REFS_UI,
                  "notes": ("9-slice rules in COMMON_CONTRACT §4 (border per asset below). Buttons: four tones (primary amber, secondary slate-blue, danger crimson, "
                            "ghost transparent with an engraved outline) x four states (normal, hover = brighter rim, pressed = inset and 2 px lower, disabled = desaturated). "
                            "Card frames by rarity: common iron, rare blue-silver (B01), epic violet-gold, legendary radiant gold with a crystal crown, cursed "
                            "black iron with wine-red rift cracks; centre transparent or near-flat dark. `title_emblem` 1024x320: the game's emblem - the "
                            "holy Crystal in a carved stone ring with wings of light, space left for a separately rendered title text (do not paint letters). "
                            "`vignette`: soft dark edge vignette, black with alpha only."),
                  "groups": [{"id": "ui", "title": "UI", "priority": "P1", "required": True, "assets": ["UI/*"]}]}
    return out


def live_assets():
    return sorted(os.path.relpath(p, A.ART).replace("\\", "/")[:-4] for p in glob.glob(os.path.join(A.ART, "*", "*.png")))


def expand(spec, live):
    ids, new = [], []
    for g in spec["groups"]:
        for pat in g.get("assets", []):
            ids += [a for a in live if fnmatch.fnmatch(a, pat)]
        new += [n["id"] for n in g.get("new", [])]
    return ids, new


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true")
    p.add_argument("--briefs", action="store_true")
    a = p.parse_args()
    live = live_assets()
    plan = batches()
    b01 = A.read_json(os.path.join(HANDOFF, "requests", "B01", "batch.json"))
    seen = {}
    b01_ids, _ = expand(b01, live)
    for x in b01_ids:
        seen.setdefault(x, []).append("B01")
    new_seen = {}
    for b, spec in plan.items():
        ids, new = expand(spec, live)
        for x in ids:
            seen.setdefault(x, []).append(b)
        for x in new:
            new_seen.setdefault(x, []).append(b)
    # B13/B14/B17 use category wildcards: drop what B01 already covers
    for b in ("B13", "B14", "B17", "B15", "B16"):
        for g in plan[b]["groups"]:
            g["assets"] = [x for x in live if any(fnmatch.fnmatch(x, pat) for pat in g["assets"]) and "B01" not in seen.get(x, [])]
    seen = {}
    for x in b01_ids:
        seen.setdefault(x, []).append("B01")
    for b, spec in plan.items():
        for x in expand(spec, live)[0]:
            seen.setdefault(x, []).append(b)
    missing = [x for x in live if x not in seen]
    dupes = {x: v for x, v in seen.items() if len(v) > 1}
    expect_new = {"Heroes/%s_%s" % (h["id"], s) for h in HEROES for s, _ in HERO_NEW}
    expect_new |= {"Enemies/%s_attack" % e["id"] for e in ENEMIES}
    expect_new |= {"Enemies/%s_tell" % b for b in BOSSES}
    expect_new |= {"World/crystal_path_%s" % p for p in ("bastion", "pulse", "thorn")}
    new_missing = sorted(expect_new - set(new_seen))
    new_dupes = {x: v for x, v in new_seen.items() if len(v) > 1}
    counts = {b: sum(len(expand(s, live)[0]) for _ in [0]) for b, s in plan.items()}
    for b, spec in plan.items():
        ids, new = expand(spec, live)
        print("%s %-70s redraw %3d  new %3d" % (b, spec["title"][:70], len(ids), len(new)))
    print("live %d | covered %d (B01 %d) | missing %d | duplicated %d | new frames %d (missing %d, dup %d)" % (
        len(live), len(seen), len(b01_ids), len(missing), len(dupes), len(new_seen), len(new_missing), len(new_dupes)))
    del counts
    if missing or dupes or new_missing or new_dupes:
        print("GAPS:", missing[:20], list(dupes)[:20], new_missing[:20], list(new_dupes)[:20])
        return 1
    if a.write or a.briefs:
        for b, spec in plan.items():
            d = os.path.join(HANDOFF, "requests", b)
            os.makedirs(d, exist_ok=True)
            A.dump_json(dict({"_doc": "Generated by Tools/ArtPipeline/plan_batches.py (full redraw plan). Edit the generator, not this file."}, **spec),
                        os.path.join(d, "batch.json"), indent=1)
            if a.briefs:
                for cmd in ("request", "brief"):
                    r = subprocess.run([sys.executable, os.path.join(A.HERE, "handoff.py"), cmd, "--batch", b], cwd=A.ROOT)
                    if r.returncode:
                        return r.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
