"""Procedural hero sprites: 20 humanoid heroes x (idle, cast, downed, evolution A, evolution B) + portraits.

Each hero is assembled from parametric parts (body build, outfit, hair/headgear, face, prop) so the
silhouettes differ by more than colour: hoods vs spikes vs crowns vs helmets, robes vs armour vs
cloaks, staffs vs swords vs shields vs bows. Canvas 320x320, feet at y=292.
"""
import math
import cairo
from toolkit import (INK, Canvas, hex2rgb, mix, shade, light, grey, paint, flat, stroke, glow, sparkle,
                     smooth_closed, smooth_open, ellipse_path, rrect_path, poly_path, star_path, outlined_line)

W = H = 320
GROUND = 292
CX = 160

SKIN = {
    "fair": hex2rgb("#ffe0c8"), "light": hex2rgb("#f6c9a4"), "tan": hex2rgb("#d99a6c"),
    "brown": hex2rgb("#a8693f"), "deep": hex2rgb("#6e4127"),
    "bark": hex2rgb("#b98d5e"),
    "stone": hex2rgb("#a8a49a"),
}

ELEMENT = {
    "fire": (hex2rgb("#ff5a2c"), hex2rgb("#ffb230")),
    "water": (hex2rgb("#2f8cff"), hex2rgb("#5fe0ff")),
    "lightning": (hex2rgb("#8c4dff"), hex2rgb("#ffe14a")),
    "ice": (hex2rgb("#7fd8ff"), hex2rgb("#e8fbff")),
    "wind": (hex2rgb("#2fd39a"), hex2rgb("#c4ffd9")),
    "earth": (hex2rgb("#b9773a"), hex2rgb("#8fc24a")),
    "light": (hex2rgb("#ffd84a"), hex2rgb("#fff7cc")),
    "shadow": (hex2rgb("#a3306b"), hex2rgb("#3a0f2c")),
    "nature": (hex2rgb("#3fa34d"), hex2rgb("#b6ec6a")),
    "poison": (hex2rgb("#a8e030"), hex2rgb("#6a2a9a")),
    "arcane": (hex2rgb("#ff5fd2"), hex2rgb("#ffd6f6")),
    "void": (hex2rgb("#5146d9"), hex2rgb("#140c38")),
}

HEROES = {
    "ignis": dict(element="fire", skin="light", build="slim", outfit="robe", head="hood_point", hair="#5a2a1c",
                  main="#d8322a", second="#ffb13b", trim="#ffd75e", prop="ember_staff", eyes="#3a1a10"),
    "cinder": dict(element="fire", skin="tan", build="broad", outfit="plate", head="spiky", hair="#ff4b26",
                   main="#3b3446", second="#ff7a2a", trim="#ffc04a", prop="flame_greatsword", eyes="#2a120a"),
    "marina": dict(element="water", skin="fair", build="slim", outfit="robe", head="long_flow", hair="#2a6fe8",
                   main="#f2fbff", second="#36b6e8", trim="#7ce9ff", prop="wave_staff", eyes="#163a74"),
    "tidal": dict(element="water", skin="brown", build="normal", outfit="tunic", head="hood_round", hair="#13314a",
                  main="#1f8fa0", second="#0f4e66", trim="#7ff3ff", prop="water_whips", eyes="#0b2a3a", mask=True),
    "volt": dict(element="lightning", skin="light", build="slim", outfit="coat", head="spiky_tall", hair="#ffe04a",
                 main="#5b2fb0", second="#2a1a5c", trim="#ffe04a", prop="conductor_rods", eyes="#2a1050"),
    "raiden": dict(element="lightning", skin="tan", build="lean", outfit="tunic", head="short_messy", hair="#262038",
                   main="#232a52", second="#8c4dff", trim="#ffd23a", prop="twin_daggers", eyes="#1a1230", scarf="#ffd23a"),
    "freya": dict(element="ice", skin="fair", build="slim", outfit="gown", head="long_straight", hair="#e6f3ff",
                  main="#8fd6ff", second="#4a7fd6", trim="#ffffff", prop="ice_wand", eyes="#2a4a8a", crown=True, cape="#4a7fd6"),
    "glacius": dict(element="ice", skin="light", build="broad", outfit="heavy_armor", head="helm_visor", hair="#3a5a7a",
                    main="#b9d8f0", second="#5f8fc0", trim="#e8fbff", prop="tower_shield", eyes="#1a2a4a"),
    "zephyr": dict(element="wind", skin="deep", build="slim", outfit="mantle", head="bun", hair="#9ff2cf",
                   main="#e9fff4", second="#2fbf86", trim="#c4ffd9", prop="fan", eyes="#13352a"),
    "sylph": dict(element="wind", skin="light", build="lean", outfit="cloak", head="ponytail", hair="#3d8f4a",
                  main="#4fc98a", second="#2a5a3a", trim="#d6ffe6", prop="longbow", eyes="#173a22"),
    "terra": dict(element="earth", skin="brown", build="broad", outfit="stone_armor", head="helm_horn", hair="#4a2f1c",
                  main="#8a6a4a", second="#5a8a3a", trim="#d9b56a", prop="hammer", eyes="#2a1a0e"),
    "magnus": dict(element="earth", skin="tan", build="huge", outfit="belted", head="mohawk", hair="#c97a2a",
                   main="#6a4a2e", second="#9ac24a", trim="#e0b060", prop="gauntlets", eyes="#2a160a"),
    # ---- expansion heroes (parts defined in the "expansion parts" section at the end of this file)
    "seren": dict(element="light", skin="tan", build="broad", outfit="tabard", head="sun_helm", hair="#7a4a24",
                  main="#c3cadb", second="#e8b730", trim="#fff1b8", prop="sun_shield_sword", eyes="#6a4a10", tabard="#fff6dc"),
    "nyxara": dict(element="shadow", skin="fair", build="slim", outfit="long_cloak", head="crescent_hood", hair="#2a1030",
                   main="#2e1d40", second="#a3306b", trim="#f0cfe2", prop="chain_staff", eyes="#c0204a"),
    "ashara": dict(element="fire", skin="brown", build="broad", outfit="phoenix_plate", head="plume_helm", hair="#3a1a10",
                   main="#8a2228", second="#ff8a2a", trim="#ffd24a", prop="flame_sabre", eyes="#3a1408"),
    "nerissa": dict(element="water", skin="deep", build="slim", outfit="sea_robe", head="pearl_veil", hair="#2c2c66",
                    main="#3fc2a2", second="#1f7a8c", trim="#fff4ea", prop="conch_staff", eyes="#1a4a5a"),
    "voltrix": dict(element="lightning", skin="light", build="normal", outfit="engineer", head="goggles_messy", hair="#ff8a2a",
                    main="#3c4a6c", second="#ffd23a", trim="#ffe14a", prop="wrench_staff", eyes="#2a2050", backpack="coils"),
    "eirwen": dict(element="ice", skin="brown", build="broad", outfit="frost_plate", head="winged_helm", hair="#f2f6ff",
                   main="#e4f1ff", second="#6fa6e0", trim="#bff4ff", prop="crystal_shield_mace", eyes="#1a3a6a"),
    "kael": dict(element="wind", skin="light", build="lean", outfit="wraps", head="topknot", hair="#1c1c28",
                 main="#2c3c4c", second="#e9e3cf", trim="#2fd39a", prop="war_fans", eyes="#173a22", sash="#2fd39a"),
    "borun": dict(element="earth", skin="deep", build="huge", outfit="apron", head="flat_cap", hair="#b0582a",
                  main="#5a7a9a", second="#7a5030", trim="#e0b060", prop="stone_gauntlet", eyes="#2a160a",
                  cap="#6e6a5c", backpack="plans"),
    # ---- nature / poison expansion heroes (parts in the "nature & poison parts" section at the end of this file).
    # evo_spec: per-branch spec overrides; the drawers also read spec["_evo"] for branch-specific gear.
    "liora": dict(element="nature", skin="light", build="slim", outfit="moss_cloak", head="leaf_crown", hair="#9a4a2a",
                  main="#4f8a3a", second="#7a5a3a", trim="#ff9cc6", prop="blossom_staff", eyes="#2a4a1a", dress="#efe6c8",
                  evo_halo=False, evo_wings=False, downed_y=222,
                  evo_spec={"A": dict(main="#3f7a32"), "B": dict(main="#79b85a", dress="#fffaf0")}),
    "thalen": dict(element="nature", skin="bark", build="broad", outfit="bark_armor", head="antler_helm", hair="#5f9a34",
                   main="#7a5534", second="#4f8a3a", trim="#c8e86a", prop="thorn_shield", eyes="#2a3a10",
                   evo_wings=False, downed_y=218,
                   evo_spec={"A": dict(prop="thorn_tower", main="#6a4a2c"),
                             "B": dict(prop="thorn_whip", main="#94683e", stance_lean=5)}),
    "vesper": dict(element="poison", skin="tan", build="normal", outfit="alchemist_coat", head="alchemist_goggles",
                   hair="#d4cce6", main="#5a3d6e", second="#2e2a24", trim="#d9a441", prop="flask", eyes="#3a1a4a",
                   evo_wings=False, downed_y=224,
                   evo_spec={"A": dict(main="#4a3448"), "B": dict(main="#4a2f66")}),
    "sable": dict(element="poison", skin="fair", build="lean", outfit="plague_robe", head="plague_beak", hair="#1c1a24",
                  main="#2e2b36", second="#4a3a2a", trim="#8a7aa0", prop="censer", eyes="#2a1a3a", hat="#24212c",
                  mask="#ece0c4", feather="#26222e", evo_wings=False, downed_y=226,
                  evo_spec={"A": dict(main="#1e1b24", hat="#16141c", mask="#a89c86", feather="#18151e", trim="#ffd35a"),
                            "B": dict(main="#f4f2ea", second="#6fbf4a", trim="#a8e030", hat="#f4f2ea", mask="#fffaf0",
                                      feather="#d8dce0")}),
    # ---- wave-3 heroes (parts in the "wave-3 parts" section at the end of this file). Extra opt-in keys:
    # sleeve ("skin" = bare arms), fx_glow (light glow colour for void/shadow, whose secondary is near-black).
    "caelis": dict(element="arcane", skin="fair", build="slim", outfit="layered_robe", head="mirror_circlet", hair="#4a2a6a",
                   main="#6c3ab8", second="#ff5fd2", trim="#ffd6f6", prop="rune_book", eyes="#5a1a6a", layer="#a780e8",
                   evo_wings=False, evo_halo=False, downed_y=224,
                   evo_spec={"A": dict(main="#9a86e0", layer="#efe8fb"),
                             "B": dict(main="#4a1f8a", layer="#7a3cc8", trim="#ff9ae6", prop="arcane_orbs", stance_lean=4)}),
    "oriane": dict(element="arcane", skin="light", build="normal", outfit="tailcoat", head="conductor_hat", hair="#ff8fd0",
                   main="#2c2450", second="#f8f2ff", trim="#ff5fd2", prop="baton", eyes="#4a1a5a", hat="#1e1838",
                   evo_wings=False, evo_halo=False, downed_y=224,
                   evo_spec={"A": dict(main="#3a2a6a", prop="long_baton"),
                             "B": dict(outfit="sigil_plate", prop="rune_shield", main="#5a4f9a", second="#e4e0f8", trim="#ff9ae6")}),
    "zerith": dict(element="void", skin="tan", build="lean", outfit="star_cloak", head="rift_hood", hair="#eceaff",
                   main="#1e1a48", second="#5146d9", trim="#a89cff", prop="star_gauntlet", eyes="#7a6ae8", fx_glow="#8a7cff",
                   evo_wings=False, evo_halo=False, downed_y=224,
                   evo_spec={"A": dict(main="#241c52"),
                             "B": dict(prop="void_daggers", trim="#a89cff", stance_lean=4)}),
    "maelis": dict(element="void", skin="light", build="broad", outfit="obsidian_plate", head="void_helm", hair="#d8d0ff",
                   main="#2e2848", second="#5146d9", trim="#a89cff", prop="portal_shield", eyes="#3a2a8a", fx_glow="#8a7cff",
                   evo_wings=False, evo_halo=False, downed_y=212,
                   evo_spec={"A": dict(prop="null_bastion", main="#26203c"),
                             "B": dict(prop="portal_glaive", main="#3a3460", second="#6a5ae8", trim="#a89cff")}),
    "solenne": dict(element="fire", skin="light", build="slim", outfit="scribe_robe", head="scribe_beret", hair="#e8622a",
                    main="#f2e2c0", second="#c8402a", trim="#ffb230", prop="burning_quill", eyes="#5a2a10",
                    evo_wings=False, evo_halo=False, downed_y=224,
                    evo_spec={"A": dict(prop="burning_scroll", main="#5a1e22", second="#ff8a2a"),
                              "B": dict(prop="ember_lantern", main="#f6e6cc", second="#e8842a", trim="#ffd27a")}),
    "mirel": dict(element="water", skin="brown", build="slim", outfit="river_dress", head="shell_crown", hair="#cfd8ff",
                  main="#2a50c0", second="#bff4ff", trim="#ffc8b4", prop="water_ribbon", eyes="#1a2a6a",
                  evo_wings=False, evo_halo=False, downed_y=212,
                  evo_spec={"A": dict(prop="flood_trident", main="#1e3a96", trim="#ffc8b4"),
                            "B": dict(prop="heal_orb", main="#f2fbff", second="#5fc8ff", trim="#ffc8b4")}),
    "veyra": dict(element="lightning", skin="brown", build="lean", outfit="ranger_jacket", head="ranger_visor", hair="#e8ecf4",
                  main="#2e3550", second="#d9803a", trim="#ffe14a", prop="arc_bow", eyes="#2a1a40", hood="#4a3a2a",
                  evo_wings=False, evo_halo=False, downed_y=224,
                  evo_spec={"A": dict(prop="heavy_bow", main="#3a3a2e"),
                            "B": dict(prop="split_bow", main="#2a2a5a")}),
    "isolde": dict(element="ice", skin="fair", build="slim", outfit="frost_coat", head="ice_braid", hair="#f2f6ff",
                   main="#2f4f8f", second="#e8f6ff", trim="#bff4ff", prop="frost_lance", eyes="#1a3a7a",
                   evo_wings=False, evo_halo=False, downed_y=224,
                   evo_spec={"A": dict(main="#3a64b0"),
                             "B": dict(prop="glacier_gauntlet", main="#3a4a68", trim="#d9a441")}),
    "aeris": dict(element="wind", skin="tan", build="slim", outfit="oracle_robe", head="oracle_veil", hair="#1e2a48",
                  main="#f2f8ff", second="#2fd39a", trim="#d9a441", prop="chime_staff", eyes="#1a4a4a",
                  evo_wings=False, evo_halo=False, downed_y=224,
                  evo_spec={"A": dict(prop="wind_loom"),
                            "B": dict(prop="chain_talisman", main="#3e4a54", second="#1f7a5a", trim="#9affc8")}),
    "doran": dict(element="earth", skin="stone", build="huge", outfit="stone_gi", head="stone_brow", hair="#ece6d8",
                  main="#7a3a24", second="#d8b878", trim="#8fc24a", prop="granite_fists", eyes="#2a1a0e", headband="#c8402a",
                  sleeve="skin", evo_wings=False, evo_halo=False, downed_y=222,
                  evo_spec={"A": dict(prop="boulder_shield"),
                            "B": dict(prop="fracture_fists", build="broad", stance_lean=6)}),
    "elowen": dict(element="light", skin="light", build="slim", outfit="cantor_robe", head="radiant_hair", hair="#ffd04a",
                   main="#fffaf0", second="#ffc93a", trim="#ffb84a", prop="songbook", eyes="#7a5a10",
                   evo_wings=False, evo_halo=False, downed_y=224,
                   evo_spec={"A": dict(main="#fffdf6"),
                             "B": dict(prop="solar_lance", main="#f4ecd8")}),
    "morven": dict(element="shadow", skin="fair", build="broad", outfit="tattered_mail", head="gloom_hood", hair="#1a1418",
                   main="#3a3644", second="#4a1e3a", trim="#d860a0", prop="gloom_glaive", eyes="#ff5ab0", hood="#24202c",
                   fx_glow="#d8509a", evo_wings=False, evo_halo=False, downed_y=222,
                   evo_spec={"A": dict(prop="dread_shield"),
                             "B": dict(prop="soul_scythe", main="#4a3a48", trim="#ff8ac8")}),
}

EVOLUTIONS = {
    # branch -> (accent override, emblem, aura colour hint)
    "A": dict(accent="#ffd35a", emblem="crown"),
    "B": dict(accent=None, emblem="wings"),
}

LW = 6.0  # main ink width


# ============================================================================ body parts

def build_metrics(build):
    return {
        "slim": dict(shoulder=46, waist=36, hip=40, arm=15, leg=14, neck=0),
        "lean": dict(shoulder=48, waist=36, hip=38, arm=15, leg=15, neck=0),
        "normal": dict(shoulder=52, waist=42, hip=42, arm=16, leg=16, neck=0),
        "broad": dict(shoulder=62, waist=48, hip=46, arm=19, leg=18, neck=0),
        "huge": dict(shoulder=70, waist=52, hip=48, arm=22, leg=19, neck=0),
    }[build]


def draw_legs(ctx, spec, m, pose):
    boot = shade(hex2rgb(spec["second"]), 0.35)
    pants = shade(hex2rgb(spec["main"]), 0.45)
    for side in (-1, 1):
        x = CX + side * (m["hip"] * 0.45)
        top = 236
        def leg(c, x=x):
            rrect_path(c, x - m["leg"], top, m["leg"] * 2, GROUND - top - 8, m["leg"])
        paint(ctx, leg, pants, lw=LW, hi=False)
        def foot(c, x=x, side=side):
            ellipse_path(c, x + side * 4, GROUND - 8, m["leg"] + 7, 11)
        paint(ctx, foot, boot, lw=LW, hi_size=0.5)


def torso_path(spec, m, lean=0.0):
    s, w, hp = m["shoulder"], m["waist"], m["hip"]
    top, bottom = 164, 250
    o = spec["outfit"]
    if o in NAT_TORSO_SHAPES:
        return nat_torso_path(spec, s, w, hp, top, lean)
    if o in W3_TORSO_SHAPES:
        return w3_torso_path(spec, s, w, hp, top, lean)
    if o in EXT_TORSO_SHAPES:
        return ext_torso_path(o, s, w, hp, top, lean)
    if o in ("robe", "gown"):
        bottom = GROUND - 6
        flare = hp + (26 if o == "gown" else 18)
        pts = [(CX - s * 0.62 + lean, top), (CX + s * 0.62 + lean, top), (CX + s + lean * 0.6, top + 16),
               (CX + w + 2, 214), (CX + flare, bottom - 4), (CX, bottom + 4), (CX - flare, bottom - 4),
               (CX - w - 2, 214), (CX - s + lean * 0.6, top + 16)]
    elif o in ("cloak", "mantle"):
        bottom = 262
        pts = [(CX - s * 0.6 + lean, top - 2), (CX + s * 0.6 + lean, top - 2), (CX + s + 8 + lean * 0.6, top + 22),
               (CX + hp + 16, bottom), (CX, bottom + 8), (CX - hp - 16, bottom), (CX - s - 8 + lean * 0.6, top + 22)]
    else:
        pts = [(CX - s * 0.6 + lean, top), (CX + s * 0.6 + lean, top), (CX + s + lean * 0.6, top + 14),
               (CX + w, 212), (CX + hp, bottom), (CX, bottom + 6), (CX - hp, bottom), (CX - w, 212),
               (CX - s + lean * 0.6, top + 14)]
    return lambda c: smooth_closed(c, pts, 0.42)


def draw_torso(ctx, spec, m, lean=0.0):
    main, second, trim = hex2rgb(spec["main"]), hex2rgb(spec["second"]), hex2rgb(spec["trim"])
    o = spec["outfit"]
    path = torso_path(spec, m, lean)
    paint(ctx, path, main, lw=LW, shade_dir=(0.45, 0.25), hi_pos=(-0.25, -0.35))
    ctx.save()
    ctx.new_path()
    path(ctx)
    ctx.clip()
    # outfit-specific detail inside the torso silhouette
    if o in ("robe", "gown"):
        flat(ctx, lambda c: rrect_path(c, CX - 13 + lean * 0.3, 168, 26, 140, 10), second)
        stroke(ctx, lambda c: (c.move_to(CX - 13 + lean * 0.3, 175), c.line_to(CX - 13 + lean * 0.3, 300)), INK, 3)
        stroke(ctx, lambda c: (c.move_to(CX + 13 + lean * 0.3, 175), c.line_to(CX + 13 + lean * 0.3, 300)), INK, 3)
        flat(ctx, lambda c: rrect_path(c, CX - 60, 218, 120, 14, 7), trim)
        stroke(ctx, lambda c: rrect_path(c, CX - 60, 218, 120, 14, 7), INK, 3)
    elif o in ("plate", "heavy_armor", "stone_armor"):
        plate = second if o != "heavy_armor" else light(main, 0.25)
        paint(ctx, lambda c: smooth_closed(c, [(CX - 34, 176), (CX + 34, 176), (CX + 30, 222), (CX, 236), (CX - 30, 222)], 0.4),
              plate, lw=4, hi_size=0.6)
        if o == "plate":
            for i in range(3):
                stroke(ctx, lambda c, i=i: (c.move_to(CX - 20 + i * 20, 188), c.line_to(CX - 14 + i * 14, 222)), trim, 3)
        if o == "stone_armor":
            for (x, y) in ((CX - 14, 196), (CX + 12, 206), (CX - 4, 220)):
                stroke(ctx, lambda c, x=x, y=y: (c.move_to(x - 6, y), c.line_to(x + 5, y + 4)), INK, 3)
        flat(ctx, lambda c: rrect_path(c, CX - 56, 232, 112, 12, 5), trim)
        stroke(ctx, lambda c: rrect_path(c, CX - 56, 232, 112, 12, 5), INK, 3)
    elif o == "coat":
        flat(ctx, lambda c: poly_path(c, [(CX - 4, 166), (CX + 4, 166), (CX + 26, 260), (CX - 26, 260)]), second)
        stroke(ctx, lambda c: (c.move_to(CX - 4, 166), c.line_to(CX - 26, 262)), INK, 3)
        stroke(ctx, lambda c: (c.move_to(CX + 4, 166), c.line_to(CX + 26, 262)), INK, 3)
        for i in range(3):
            paint(ctx, lambda c, i=i: ellipse_path(c, CX + 14, 190 + i * 18, 4, 4), hex2rgb(spec["trim"]), lw=2, hi=False, shade_amt=0)
        # lightning trim zigzag on hem
        stroke(ctx, lambda c: smooth_open(c, [(CX - 60, 244), (CX - 40, 236), (CX - 26, 248)], 0), trim, 4)
    elif o in ("tunic", "belted"):
        flat(ctx, lambda c: rrect_path(c, CX - 60, 222, 120, 14, 6), second if o == "tunic" else hex2rgb("#4a3020"))
        stroke(ctx, lambda c: rrect_path(c, CX - 60, 222, 120, 14, 6), INK, 3)
        paint(ctx, lambda c: rrect_path(c, CX - 11, 220, 22, 18, 4), trim, lw=3, hi=False)
        if o == "tunic":
            stroke(ctx, lambda c: (c.move_to(CX - 18, 168), c.line_to(CX, 196), c.line_to(CX + 18, 168)), trim, 4)
    elif o in ("cloak", "mantle"):
        stroke(ctx, lambda c: smooth_open(c, [(CX - 30, 190), (CX - 24, 240), (CX - 28, 262)]), shade(main, 0.4), 4)
        stroke(ctx, lambda c: smooth_open(c, [(CX + 30, 190), (CX + 24, 240), (CX + 28, 262)]), shade(main, 0.4), 4)
        if o == "mantle":
            # feather layer across the shoulders
            for i in range(9):
                x = CX - 64 + i * 16
                paint(ctx, lambda c, x=x: smooth_closed(c, [(x - 9, 168), (x + 9, 168), (x + 6, 200), (x, 210), (x - 6, 200)], 0.5),
                      second if i % 2 else light(second, 0.25), lw=3, hi=False)
    elif o in EXT_OUTFITS:
        ext_torso_detail(ctx, spec, m, lean)
    ctx.restore()
    if o in EXT_OUTFITS:
        ext_torso_overlay(ctx, spec, m, lean)


def draw_arm(ctx, spec, m, shoulder, hand, sleeve_color, skin, behind=False):
    """Arm as a thick tapered stroke with ink border; sleeve over the upper part, round hand."""
    sx, sy = shoulder
    hx, hy = hand
    mx, my = (sx + hx) / 2 + (6 if hx > sx else -6), (sy + hy) / 2
    width = m["arm"] * 2
    outlined_line(ctx, [(sx, sy), (mx, my), (hx, hy)], sleeve_color, width, width + LW * 1.6)
    # cuff
    ex, ey = (mx * 0.4 + hx * 0.6), (my * 0.4 + hy * 0.6)
    paint(ctx, lambda c: ellipse_path(c, ex, ey, m["arm"] + 2, m["arm"] * 0.75, math.atan2(hy - my, hx - mx) + math.pi / 2),
          light(sleeve_color, 0.15), lw=3.5, hi=False)
    paint(ctx, lambda c: ellipse_path(c, hx, hy, m["arm"] * 0.85, m["arm"] * 0.85), skin, lw=4.5, hi_size=0.6)


def head_path(cx=CX, cy=112, rx=54, ry=50):
    def p(c):
        smooth_closed(c, [(cx - rx, cy - 6), (cx - rx * 0.72, cy - ry * 0.9), (cx, cy - ry), (cx + rx * 0.72, cy - ry * 0.9),
                          (cx + rx, cy - 6), (cx + rx * 0.82, cy + ry * 0.62), (cx + rx * 0.3, cy + ry * 0.98),
                          (cx - rx * 0.3, cy + ry * 0.98), (cx - rx * 0.82, cy + ry * 0.62)], 0.55)
    return p


def draw_face(ctx, spec, cx=CX, cy=118, mood="calm", downed=False):
    eye = hex2rgb(spec["eyes"])
    if downed:
        for side in (-1, 1):
            x = cx + side * 19
            stroke(ctx, lambda c, x=x: (c.move_to(x - 7, cy - 7), c.line_to(x + 7, cy + 7), c.move_to(x + 7, cy - 7), c.line_to(x - 7, cy + 7)), INK, 4)
        stroke(ctx, lambda c: smooth_open(c, [(cx - 8, cy + 24), (cx, cy + 20), (cx + 8, cy + 24)]), INK, 3.5)
        return
    for side in (-1, 1):
        x = cx + side * 19
        if mood == "focus":
            paint(ctx, lambda c, x=x: ellipse_path(c, x, cy + 2, 8.5, 10), eye, lw=3, hi=False, shade_amt=0)
        else:
            paint(ctx, lambda c, x=x: ellipse_path(c, x, cy, 9, 13), eye, lw=3, hi=False, shade_amt=0)
        flat(ctx, lambda c, x=x: ellipse_path(c, x - 3, cy - 5, 3.6, 4.4), (1, 1, 1))
        flat(ctx, lambda c, x=x: ellipse_path(c, x + 3, cy + 4, 1.8, 1.8), (1, 1, 1), 0.85)
        # brows
        tilt = 4 if mood == "focus" else 0
        stroke(ctx, lambda c, x=x, side=side: (c.move_to(x - 9, cy - 18 - (tilt if side < 0 else 0)),
                                               c.line_to(x + 9, cy - 18 - (tilt if side > 0 else 0))), INK, 3.2)
    blush = mix(SKIN[spec["skin"]], hex2rgb("#ff6a7a"), 0.55)
    for side in (-1, 1):
        flat(ctx, lambda c, side=side: ellipse_path(c, cx + side * 33, cy + 14, 9, 5), blush, 0.55)
    if spec.get("mask"):
        return
    if mood == "focus":
        paint(ctx, lambda c: ellipse_path(c, cx, cy + 22, 6, 5), hex2rgb("#7a2a3a"), lw=3, hi=False, shade_amt=0)
    else:
        stroke(ctx, lambda c: smooth_open(c, [(cx - 7, cy + 20), (cx, cy + 25), (cx + 7, cy + 20)]), INK, 3.2)


# ============================================================================ hair & headgear

def draw_hair_back(ctx, spec):
    hair = hex2rgb(spec["hair"])
    h = spec["head"]
    if h == "long_flow":
        paint(ctx, lambda c: smooth_closed(c, [(CX - 58, 96), (CX + 58, 96), (CX + 70, 170), (CX + 82, 236), (CX + 50, 226),
                                                 (CX + 30, 196), (CX - 30, 196), (CX - 52, 230), (CX - 80, 232), (CX - 68, 168)], 0.5),
              hair, lw=LW)
    elif h == "long_straight":
        paint(ctx, lambda c: rrect_path(c, CX - 64, 84, 128, 150, 40), hair, lw=LW)
    elif h == "ponytail":
        paint(ctx, lambda c: smooth_closed(c, [(CX + 40, 74), (CX + 74, 80), (CX + 94, 130), (CX + 84, 186), (CX + 70, 160), (CX + 62, 110)], 0.5),
              hair, lw=LW)
    elif h == "bun":
        paint(ctx, lambda c: ellipse_path(c, CX, 52, 26, 22), hair, lw=LW)
    elif h == "hood_point" or h == "hood_round":
        hood = hex2rgb(spec["main"]) if h == "hood_point" else hex2rgb(spec["second"])
        paint(ctx, lambda c: smooth_closed(c, [(CX - 70, 150), (CX - 72, 100), (CX - 50, 60), (CX, 44), (CX + 50, 60),
                                                 (CX + 72, 100), (CX + 70, 150), (CX, 160)], 0.5), shade(hood, 0.2), lw=LW)
    elif h in EXT_HEADS:
        ext_hair_back(ctx, spec)


def draw_hair_front(ctx, spec, element_color):
    hair = hex2rgb(spec["hair"])
    h = spec["head"]
    main, second, trim = hex2rgb(spec["main"]), hex2rgb(spec["second"]), hex2rgb(spec["trim"])
    if h == "hood_point":
        def hood(c):
            smooth_closed(c, [(CX - 64, 120), (CX - 62, 76), (CX - 30, 50), (CX + 6, 6), (CX + 18, 2), (CX + 30, 40),
                              (CX + 60, 70), (CX + 66, 120), (CX + 46, 92), (CX, 78), (CX - 46, 92)], 0.45)
        paint(ctx, hood, main, lw=LW, hi_pos=(-0.2, -0.2))
        stroke(ctx, lambda c: smooth_open(c, [(CX - 60, 108), (CX - 40, 90), (CX, 80), (CX + 40, 90), (CX + 60, 108)]), trim, 5)
        # flame tip
        paint(ctx, lambda c: smooth_closed(c, [(CX + 10, 6), (CX + 26, -2), (CX + 22, 12), (CX + 34, 10), (CX + 20, 26)], 0.6),
              hex2rgb("#ffb230"), lw=3.5, hi=False)
    elif h == "hood_round":
        hood = second
        paint(ctx, lambda c: smooth_closed(c, [(CX - 64, 124), (CX - 60, 72), (CX - 20, 52), (CX + 20, 52), (CX + 60, 72),
                                                 (CX + 64, 124), (CX + 44, 92), (CX, 82), (CX - 44, 92)], 0.5), hood, lw=LW)
    elif h in ("spiky", "spiky_tall"):
        tall = 1.4 if h == "spiky_tall" else 1.0
        pts = [(CX - 58, 118), (CX - 70, 86), (CX - 54, 82), (CX - 62, 46 - 10 * tall), (CX - 34, 62), (CX - 26, 18 - 20 * tall),
               (CX - 4, 54), (CX + 12, 10 - 24 * tall), (CX + 24, 56), (CX + 50, 26 - 14 * tall), (CX + 48, 66), (CX + 74, 60),
               (CX + 60, 88), (CX + 64, 118), (CX + 40, 92), (CX + 16, 102), (CX - 8, 86), (CX - 30, 100), (CX - 44, 90)]
        paint(ctx, lambda c: poly_path(c, pts), hair, lw=LW, hi_pos=(-0.25, -0.3))
    elif h == "short_messy":
        pts = [(CX - 60, 116), (CX - 64, 76), (CX - 40, 52), (CX - 10, 44), (CX + 26, 46), (CX + 56, 64), (CX + 64, 100),
               (CX + 58, 116), (CX + 46, 92), (CX + 30, 104), (CX + 18, 86), (CX - 4, 100), (CX - 18, 84), (CX - 40, 96)]
        paint(ctx, lambda c: smooth_closed(c, pts, 0.35), hair, lw=LW)
    elif h in ("long_flow", "long_straight"):
        pts = [(CX - 62, 124), (CX - 60, 80), (CX - 30, 56), (CX + 10, 52), (CX + 48, 62), (CX + 64, 92), (CX + 64, 126),
               (CX + 50, 100), (CX + 30, 82), (CX + 4, 92), (CX - 22, 80), (CX - 46, 98)]
        paint(ctx, lambda c: smooth_closed(c, pts, 0.45), hair, lw=LW)
    elif h == "ponytail":
        pts = [(CX - 60, 116), (CX - 58, 76), (CX - 24, 54), (CX + 22, 52), (CX + 56, 70), (CX + 62, 112), (CX + 44, 88),
               (CX + 10, 84), (CX - 20, 92), (CX - 44, 98)]
        paint(ctx, lambda c: smooth_closed(c, pts, 0.45), hair, lw=LW)
        paint(ctx, lambda c: ellipse_path(c, CX + 58, 82, 8, 8), hex2rgb(spec["trim"]), lw=3.5, hi=False)
    elif h == "bun":
        pts = [(CX - 60, 112), (CX - 56, 76), (CX - 20, 58), (CX + 20, 58), (CX + 56, 76), (CX + 60, 112), (CX + 40, 86),
               (CX, 80), (CX - 40, 86)]
        paint(ctx, lambda c: smooth_closed(c, pts, 0.5), hair, lw=LW)
        # feather pin
        paint(ctx, lambda c: smooth_closed(c, [(CX + 18, 40), (CX + 50, 12), (CX + 44, 36)], 0.6), hex2rgb(spec["second"]), lw=3.5, hi=False)
    elif h == "helm_visor":
        helm = light(main, 0.1)
        paint(ctx, lambda c: smooth_closed(c, [(CX - 66, 130), (CX - 64, 70), (CX - 30, 46), (CX + 30, 46), (CX + 64, 70),
                                                 (CX + 66, 130), (CX + 50, 108), (CX - 50, 108)], 0.5), helm, lw=LW, hi_size=0.7)
        paint(ctx, lambda c: smooth_closed(c, [(CX - 8, 46), (CX + 8, 46), (CX + 12, 18), (CX, 6), (CX - 12, 18)], 0.5), trim, lw=4)
        stroke(ctx, lambda c: smooth_open(c, [(CX - 56, 100), (CX, 92), (CX + 56, 100)]), second, 6)
    elif h == "helm_horn":
        helm = shade(main, 0.15)
        for side in (-1, 1):
            paint(ctx, lambda c, side=side: smooth_closed(c, [(CX + side * 46, 78), (CX + side * 82, 54), (CX + side * 90, 24),
                                                               (CX + side * 68, 52), (CX + side * 50, 64)], 0.5), hex2rgb("#efe0c0"), lw=4.5)
        paint(ctx, lambda c: smooth_closed(c, [(CX - 64, 112), (CX - 60, 70), (CX - 24, 50), (CX + 24, 50), (CX + 60, 70),
                                                 (CX + 64, 112), (CX + 40, 94), (CX - 40, 94)], 0.5), helm, lw=LW)
        flat(ctx, lambda c: rrect_path(c, CX - 56, 86, 112, 10, 5), hex2rgb(spec["trim"]))
        stroke(ctx, lambda c: rrect_path(c, CX - 56, 86, 112, 10, 5), INK, 3)
    elif h == "mohawk":
        pts = [(CX - 16, 70), (CX - 12, 30), (CX - 2, 8), (CX + 12, 2), (CX + 22, 22), (CX + 18, 60), (CX + 14, 74)]
        paint(ctx, lambda c: smooth_closed(c, pts, 0.5), hair, lw=LW)
    elif h in EXT_HEADS:
        ext_hair_front(ctx, spec, element_color)
    if spec.get("crown"):
        def crown(c):
            poly_path(c, [(CX - 40, 70), (CX - 34, 36), (CX - 20, 58), (CX - 8, 24), (CX, 50), (CX + 8, 24), (CX + 20, 58),
                          (CX + 34, 36), (CX + 40, 70), (CX, 78)])
        paint(ctx, crown, hex2rgb("#bff4ff"), lw=4.5, hi_size=0.7)
        sparkle(ctx, CX + 8, 34, 7)


def draw_scarf(ctx, spec, flutter=0):
    col = hex2rgb(spec["scarf"])
    paint(ctx, lambda c: smooth_closed(c, [(CX - 46, 154), (CX + 46, 154), (CX + 40, 176), (CX - 40, 176)], 0.4), col, lw=4.5)
    paint(ctx, lambda c: smooth_closed(c, [(CX + 30, 166), (CX + 86 + flutter, 168), (CX + 104 + flutter, 158), (CX + 92 + flutter, 184),
                                             (CX + 40, 182)], 0.5), col, lw=4.5)


def draw_cape(ctx, spec, lean=0):
    col = hex2rgb(spec["cape"])
    paint(ctx, lambda c: smooth_closed(c, [(CX - 50, 164), (CX + 50, 164), (CX + 84, 270), (CX + 50, 284), (CX, 276),
                                             (CX - 50, 284), (CX - 84, 270)], 0.5), shade(col, 0.15), lw=LW)


# ============================================================================ props

def draw_prop(ctx, spec, hand, pose, element):
    kind = spec["prop"]
    ec, ec2 = ELEMENT[element]
    hx, hy = hand
    trim = hex2rgb(spec["trim"])
    wood = hex2rgb("#8a5a34")
    metal = hex2rgb("#cfd6e6")
    if kind in ("ember_staff", "wave_staff", "ice_wand"):
        top = (hx + 10, hy - (150 if kind != "ice_wand" else 104))
        bottom = (hx - 4, hy + (40 if kind != "ice_wand" else 12))
        outlined_line(ctx, [bottom, top], wood if kind != "ice_wand" else hex2rgb("#a8c8f0"), 9, 16, smooth=False)
        if kind == "ember_staff":
            glow(ctx, top[0], top[1] - 6, 46, ec2, 0.7 if pose == "cast" else 0.45)
            paint(ctx, lambda c: smooth_closed(c, [(top[0] - 14, top[1] + 4), (top[0] + 14, top[1] + 4), (top[0] + 10, top[1] - 4),
                                                     (top[0], top[1] + 6)], 0.5), trim, lw=4, hi=False)
            paint(ctx, lambda c: ellipse_path(c, top[0], top[1] - 12, 16, 16), ec2, lw=4.5, hi_size=0.8)
            paint(ctx, lambda c: smooth_closed(c, [(top[0] - 8, top[1] - 14), (top[0], top[1] - 40), (top[0] + 9, top[1] - 16),
                                                     (top[0], top[1] - 4)], 0.6), ec, lw=3, hi=False)
        elif kind == "wave_staff":
            glow(ctx, top[0], top[1] - 6, 44, ec2, 0.55)
            paint(ctx, lambda c: smooth_closed(c, [(top[0] - 6, top[1] + 6), (top[0] - 22, top[1] - 12), (top[0] - 8, top[1] - 34),
                                                     (top[0] + 18, top[1] - 30), (top[0] + 22, top[1] - 10), (top[0] + 8, top[1] - 4),
                                                     (top[0] + 6, top[1] - 18), (top[0] - 4, top[1] - 14), (top[0] + 4, top[1] + 4)], 0.55),
                  ec, lw=4.5, hi_size=0.7)
            paint(ctx, lambda c: ellipse_path(c, top[0] + 1, top[1] - 18, 6, 6), ec2, lw=2.5, hi=False)
        else:
            glow(ctx, top[0], top[1], 38, ec2, 0.6)
            paint(ctx, lambda c: poly_path(c, [(top[0], top[1] - 26), (top[0] + 12, top[1]), (top[0], top[1] + 14), (top[0] - 12, top[1])]),
                  ec, lw=4, hi_size=0.8)
            sparkle(ctx, top[0] - 2, top[1] - 6, 7)
    elif kind == "flame_greatsword":
        ang = -1.1 if pose != "cast" else -0.95   # raised (a flat cast swing ran 90px off the canvas)
        L = 150
        tip = (hx + math.cos(ang) * L, hy + math.sin(ang) * L)
        nx, ny = -math.sin(ang), math.cos(ang)
        base = (hx + math.cos(ang) * 22, hy + math.sin(ang) * 22)
        blade = [(base[0] + nx * 15, base[1] + ny * 15), (tip[0] + nx * 8, tip[1] + ny * 8), (tip[0] + math.cos(ang) * 22, tip[1] + math.sin(ang) * 22),
                 (tip[0] - nx * 8, tip[1] - ny * 8), (base[0] - nx * 15, base[1] - ny * 15)]
        glow(ctx, (base[0] + tip[0]) / 2, (base[1] + tip[1]) / 2, 70, ec, 0.35)
        paint(ctx, lambda c: poly_path(c, blade), hex2rgb("#3a3240"), lw=LW, hi_size=0.5)
        inner = [(base[0] + nx * 6, base[1] + ny * 6), (tip[0], tip[1]), (base[0] - nx * 6, base[1] - ny * 6)]
        flat(ctx, lambda c: poly_path(c, inner), ec2, 0.95)
        guard = [(base[0] + nx * 26, base[1] + ny * 26), (base[0] - nx * 26, base[1] - ny * 26)]
        outlined_line(ctx, guard, trim, 10, 17, smooth=False)
        outlined_line(ctx, [(hx - math.cos(ang) * 18, hy - math.sin(ang) * 18), base], wood, 9, 16, smooth=False)
    elif kind == "water_whips":
        for side, (sx, sy) in ((1, hand), (-1, (2 * CX - hx, hy))):
            pts = [(sx, sy), (sx + side * 22, sy + 12), (sx + side * 40, sy - 14), (sx + side * 52, sy + 8), (sx + side * 64, sy - 20)]
            if pose == "cast":
                pts = [(sx, sy), (sx + side * 18, sy - 28), (sx + side * 44, sy - 40), (sx + side * 58, sy - 70), (sx + side * 70, sy - 66)]
            outlined_line(ctx, pts, ec, 10, 17)
            outlined_line(ctx, pts[:-1], ec2, 4, 4)
            glow(ctx, pts[-1][0], pts[-1][1], 22, ec2, 0.6)
    elif kind == "conductor_rods":
        for i, (ox, oy) in enumerate(((-82, -40), (84, -60))):
            x, y = CX + ox, 170 + oy + (-20 if pose == "cast" else 0)
            glow(ctx, x, y - 30, 34, ec2, 0.55)
            outlined_line(ctx, [(x, y), (x + 4, y - 64)], metal, 9, 16, smooth=False)
            paint(ctx, lambda c, x=x, y=y: ellipse_path(c, x + 4, y - 70, 9, 9), ec2, lw=3.5, hi=False)
            paint(ctx, lambda c, x=x, y=y: rrect_path(c, x - 6, y - 4, 20, 10, 4), trim, lw=3, hi=False)
            stroke(ctx, lambda c, x=x, y=y: (c.move_to(x + 4, y - 80), c.line_to(x - 6, y - 92), c.line_to(x + 8, y - 100), c.line_to(x - 2, y - 114)),
                   ec2, 3.5)
    elif kind == "twin_daggers":
        for side, (sx, sy) in ((1, hand), (-1, (2 * CX - hx, hy))):
            ang = -0.9 if side > 0 else -2.25
            if pose == "cast":
                ang = -0.3 if side > 0 else -2.85
            tip = (sx + math.cos(ang) * 60, sy + math.sin(ang) * 60)
            nx, ny = -math.sin(ang), math.cos(ang)
            paint(ctx, lambda c, sx=sx, sy=sy, tip=tip, nx=nx, ny=ny: poly_path(c, [(sx + nx * 7, sy + ny * 7), tip, (sx - nx * 7, sy - ny * 7)]),
                  metal, lw=4.5, hi_size=0.6)
            stroke(ctx, lambda c, sx=sx, sy=sy, tip=tip: (c.move_to(sx, sy), c.line_to(tip[0], tip[1])), ec2, 2.5)
    elif kind == "tower_shield":
        sx, sy = 2 * CX - hx - 8, hy - 40
        glow(ctx, sx, sy, 80, ec2, 0.35)
        def shield(c):
            smooth_closed(c, [(sx - 38, sy - 62), (sx + 38, sy - 62), (sx + 44, sy + 20), (sx, sy + 72), (sx - 44, sy + 20)], 0.35)
        paint(ctx, shield, mix(ec, (1, 1, 1), 0.35), lw=LW, alpha=0.95, hi_size=0.8)
        paint(ctx, lambda c: smooth_closed(c, [(sx - 14, sy - 30), (sx + 14, sy - 30), (sx + 18, sy + 6), (sx, sy + 30), (sx - 18, sy + 6)], 0.4),
              ec2, lw=3.5, hi=False)
        sparkle(ctx, sx - 18, sy - 40, 9)
    elif kind == "fan":
        fx, fy = hx + 4, hy - 30 if pose != "cast" else hy - 50
        def fan(c):
            c.move_to(fx, fy + 34)
            c.arc(fx, fy + 34, 66, -math.pi * 0.95, -math.pi * 0.05)
            c.close_path()
        paint(ctx, fan, hex2rgb(spec["second"]), lw=LW, hi_size=0.6)
        for i in range(6):
            a = -math.pi * 0.95 + i * math.pi * 0.9 / 5
            stroke(ctx, lambda c, a=a: (c.move_to(fx, fy + 34), c.line_to(fx + math.cos(a) * 62, fy + 34 + math.sin(a) * 62)), INK, 2.5)
        flat(ctx, lambda c: (c.arc(fx, fy + 34, 26, -math.pi * 0.95, -math.pi * 0.05), c.line_to(fx, fy + 34), c.close_path()), ec2, 0.9)
    elif kind == "longbow":
        bx = 2 * CX - hx - 14
        top, bottom = (bx + 10, hy - 126), (bx + 10, hy + 56)
        def bow(c):
            smooth_open(c, [top, (bx - 30, hy - 40), (bx - 34, hy - 30), (bx - 30, hy - 20), bottom])
        stroke(ctx, bow, INK, 15)
        stroke(ctx, bow, wood, 8)
        stroke(ctx, lambda c: (c.move_to(*top), c.line_to(*bottom) if pose != "cast" else c.line_to(bx + 34, hy - 34)), hex2rgb("#f0f0f0"), 2.5)
        if pose == "cast":
            stroke(ctx, lambda c: (c.move_to(bx + 34, hy - 34), c.line_to(*bottom)), hex2rgb("#f0f0f0"), 2.5)
            outlined_line(ctx, [(bx + 36, hy - 34), (bx - 70, hy - 34)], hex2rgb("#e8e0d0"), 4, 9, smooth=False)
            glow(ctx, bx - 74, hy - 34, 26, ec2, 0.8)
    elif kind == "hammer":
        ang = -1.25 if pose != "cast" else -2.2
        head = (hx + math.cos(ang) * 112, hy + math.sin(ang) * 112)
        outlined_line(ctx, [(hx - math.cos(ang) * 22, hy - math.sin(ang) * 22), head], wood, 10, 17, smooth=False)
        ctx.save()
        ctx.translate(*head)
        ctx.rotate(ang + math.pi / 2)
        paint(ctx, lambda c: rrect_path(c, -40, -24, 80, 46, 10), hex2rgb("#8f8a86"), lw=LW, hi_size=0.6)
        paint(ctx, lambda c: rrect_path(c, -14, -26, 28, 50, 6), ec2, lw=3.5, hi=False)
        ctx.restore()
    elif kind == "gauntlets":
        for side, (sx, sy) in ((1, hand), (-1, (2 * CX - hx, hy))):
            glow(ctx, sx, sy, 34, ec2, 0.35 if pose != "cast" else 0.6)
            paint(ctx, lambda c, sx=sx, sy=sy: smooth_closed(c, [(sx - 26, sy - 18), (sx + 26, sy - 18), (sx + 30, sy + 14), (sx, sy + 28), (sx - 30, sy + 14)], 0.5),
                  hex2rgb("#8a8478"), lw=LW, hi_size=0.7)
            for k in range(3):
                paint(ctx, lambda c, sx=sx, sy=sy, k=k: ellipse_path(c, sx - 14 + k * 14, sy - 16, 6, 5), ec2, lw=2.5, hi=False)
    elif kind in EXT_PROPS:
        ext_prop(ctx, spec, hand, pose, element)


# ============================================================================ assembly

BETWEEN_ARMS_PROPS = ("tower_shield", "longbow", "sun_shield_sword", "crystal_shield_mace", "thorn_shield", "thorn_tower",
                      "rune_shield", "portal_shield", "null_bastion", "arc_bow", "heavy_bow", "split_bow", "boulder_shield",
                      "dread_shield")


# Downed pose: vertical placement so the lying figure rests on the ground line (row ~298) instead of
# running off the canvas bottom. Measured with Tools/ArtPipeline (validator 'cropped_silhouette'); re-measure if a hero changes.
DOWNED_Y = {'aeris': 235, 'ashara': 219, 'borun': 218, 'caelis': 240, 'cinder': 226, 'doran': 211, 'eirwen': 211, 'elowen': 230, 'freya': 229, 'glacius': 204, 'ignis': 240, 'isolde': 237, 'kael': 198, 'liora': 238, 'maelis': 211, 'magnus': 210, 'marina': 235, 'mirel': 196, 'morven': 225, 'nerissa': 223, 'nyxara': 237, 'oriane': 221, 'raiden': 227, 'sable': 218, 'seren': 218, 'solenne': 240, 'sylph': 214, 'terra': 226, 'thalen': 208, 'tidal': 199, 'vesper': 235, 'veyra': 230, 'volt': 239, 'voltrix': 226, 'zephyr': 240, 'zerith': 234}

# Runtime frames are drawn into a larger canvas so raised staffs, bows, hair spikes and hood tips are never
# cropped (validator check "cropped_silhouette"). The figure keeps its 320-unit geometry and PPU, so its
# on-screen size is unchanged; only the transparent margin grows. Portraits keep the tight 320 canvas.
FRAME = 400
FRAME_OFFSET = (40, 80)
FRAME_FOOT_ROW = 292 + FRAME_OFFSET[1]


def hero_sprite(hero_id, pose="idle", evo=None, size=W, framed=False):
    spec = dict(HEROES[hero_id])
    element = spec["element"]
    ec, ec2 = ELEMENT[element]
    if evo == "A":
        spec["trim"] = "#ffd35a"
    elif evo == "B":
        spec["trim"] = "#%02x%02x%02x" % tuple(int(v * 255) for v in ec2)
    spec.update(spec.get("evo_spec", {}).get(evo, {}))
    if evo_kit(hero_id, evo):
        # Evolved outfit takes on the element colour (palette shift is half of the branch identity).
        to_hex = lambda c: "#%02x%02x%02x" % tuple(int(max(0, min(1, v)) * 255) for v in c)  # noqa: E731
        spec["main"] = to_hex(mix(hex2rgb(spec["main"]), shade(ec, 0.25), 0.5))
        spec["second"] = to_hex(mix(hex2rgb(spec["second"]), ec2, 0.35))
    spec["_evo"], spec["_pose"] = evo, pose
    if framed:
        k = size / W
        cv = Canvas(int(FRAME * k), int(FRAME * k), 1.0)
        cv.ctx.translate(FRAME_OFFSET[0] * k, FRAME_OFFSET[1] * k)
        cv.ctx.scale(k, k)
    else:
        cv = Canvas(size, size, size / W)
    ctx = cv.ctx
    base_matrix = ctx.get_matrix()
    m = build_metrics(spec["build"])
    skin = SKIN[spec["skin"]]
    downed = pose == "downed"
    if downed:
        # lying on the ground: rotate the figure about its centre and shrink to fit the canvas
        ctx.translate(CX, DOWNED_Y.get(hero_id, spec.get("downed_y", 236)))
        ctx.rotate(-1.45)
        ctx.scale(0.72, 0.72)
        ctx.translate(-CX, -180)
    lean = 6 if pose == "cast" else spec.get("stance_lean", 0)
    fx2 = hex2rgb(spec["fx_glow"]) if spec.get("fx_glow") else ec2  # opt-in: light glow for dark secondaries

    kit = evo_kit(hero_id, evo)
    if evo:
        aura = fx2 if evo == "B" else hex2rgb("#ffd35a")
        glow(ctx, CX, 180, 150, aura, 0.38)
        if kit:
            kit_back(ctx, kit, spec, m, pose, lean, ec, ec2)
        elif evo == "B":
            for side in (-1, 1) if spec.get("evo_wings", True) else ():
                wing = [(CX + side * 30, 176), (CX + side * 120, 112), (CX + side * 142, 150), (CX + side * 118, 176),
                        (CX + side * 132, 206), (CX + side * 92, 210), (CX + side * 56, 214)]
                paint(ctx, lambda c, wing=wing: smooth_closed(c, wing, 0.45), mix(ec2, (1, 1, 1), 0.35), lw=4.5, alpha=0.9, hi_size=0.7)
        elif spec.get("evo_halo", True):
            stroke(ctx, lambda c: ellipse_path(c, CX, 42, 48, 12), hex2rgb("#ffd35a"), 6)
            stroke(ctx, lambda c: ellipse_path(c, CX, 42, 48, 12), INK, 2)

    if spec.get("cape"):
        draw_cape(ctx, spec, lean)
    ext_back_items(ctx, spec, pose, lean)
    draw_hair_back(ctx, spec)

    # arms behind/in front depending on pose
    sleeve = hex2rgb(spec["main"]) if spec["outfit"] not in ("belted",) else skin
    if spec["outfit"] == "heavy_armor" or spec["outfit"] == "stone_armor":
        sleeve = shade(hex2rgb(spec["main"]), 0.1)
    if spec.get("sleeve"):  # opt-in: "skin" for bare arms, or a sleeve colour
        sleeve = skin if spec["sleeve"] == "skin" else hex2rgb(spec["sleeve"])
    left_sh = (CX - m["shoulder"] + 8 + lean, 182)
    right_sh = (CX + m["shoulder"] - 8 + lean, 182)
    if pose == "cast":
        left_hand = (CX - m["shoulder"] - 32, 150)
        right_hand = (CX + m["shoulder"] + 26, 124)
    else:
        left_hand = (CX - m["shoulder"] - 10, 236)
        right_hand = (CX + m["shoulder"] + 12, 230)

    draw_legs(ctx, spec, m, pose)
    draw_torso(ctx, spec, m, lean)
    if spec["prop"] in BETWEEN_ARMS_PROPS:
        draw_arm(ctx, spec, m, left_sh, left_hand, sleeve, skin)
        draw_prop(ctx, spec, right_hand, pose, element)
        draw_arm(ctx, spec, m, right_sh, right_hand, sleeve, skin)
    else:
        draw_arm(ctx, spec, m, left_sh, left_hand, sleeve, skin)
        draw_arm(ctx, spec, m, right_sh, right_hand, sleeve, skin)

    # shoulder pads for armoured builds
    if spec["outfit"] in ("plate", "heavy_armor", "stone_armor"):
        pad = hex2rgb(spec["second"]) if spec["outfit"] != "heavy_armor" else light(hex2rgb(spec["main"]), 0.2)
        if spec["outfit"] == "stone_armor":
            pad = hex2rgb("#8f8a86")
        for side in (-1, 1):
            paint(ctx, lambda c, side=side: smooth_closed(c, [(CX + side * (m["shoulder"] - 30) + lean, 162), (CX + side * (m["shoulder"] + 14) + lean, 166),
                                                               (CX + side * (m["shoulder"] + 16) + lean, 196), (CX + side * (m["shoulder"] - 14) + lean, 192)], 0.5),
                  pad, lw=LW, hi_size=0.6)
    elif spec["outfit"] in EXT_OUTFITS:
        ext_shoulders(ctx, spec, m, lean)
    if spec.get("scarf"):
        draw_scarf(ctx, spec, 10 if pose == "cast" else 0)
    if kit:
        kit_body(ctx, kit, spec, m, pose, lean, ec, ec2)

    # head
    hx = CX + lean * 0.6
    ctx.save()
    ctx.translate(lean * 0.6, 0)
    paint(ctx, head_path(), skin, lw=LW, shade_dir=(0.5, 0.3), shade_amt=0.22, hi_pos=(-0.25, -0.25))
    if spec["head"] not in ("helm_visor",):
        draw_face(ctx, spec, mood="focus" if pose == "cast" else "calm", downed=downed)
    else:
        # visor slit with glowing eyes
        flat(ctx, lambda c: rrect_path(c, CX - 44, 108, 88, 22, 10), hex2rgb("#1b2440"))
        for side in (-1, 1):
            glow(ctx, CX + side * 18, 119, 14, ec2, 0.9)
            flat(ctx, lambda c, side=side: ellipse_path(c, CX + side * 18, 119, 6, 3.5), (1, 1, 1))
        paint(ctx, lambda c: smooth_closed(c, [(CX - 60, 130), (CX + 60, 130), (CX + 50, 158), (CX - 50, 158)], 0.4), light(hex2rgb(spec["main"]), 0.1), lw=LW)
    if spec.get("mask"):
        paint(ctx, lambda c: smooth_closed(c, [(CX - 50, 128), (CX + 50, 128), (CX + 40, 160), (CX, 166), (CX - 40, 160)], 0.4),
              hex2rgb(spec["main"]), lw=LW - 1)
    draw_hair_front(ctx, spec, ec)
    ctx.restore()
    if kit:
        kit_head(ctx, kit, spec, m, pose, lean, ec, ec2)

    if spec["prop"] not in BETWEEN_ARMS_PROPS:
        draw_prop(ctx, spec, right_hand, pose, element)
    nat_front_fx(ctx, spec, pose)

    if pose == "cast":
        glow(ctx, left_hand[0], left_hand[1], 40, fx2, 0.75)
        sparkle(ctx, left_hand[0] - 12, left_hand[1] - 18, 10)
        sparkle(ctx, left_hand[0] + 16, left_hand[1] - 6, 6)
    if evo:
        emblem_col = hex2rgb("#ffd35a") if evo == "A" else fx2
        paint(ctx, lambda c: star_path(c, CX + lean, 196, 13, 6, 5) if evo == "A" else poly_path(c, [(CX + lean, 182), (CX + 10 + lean, 196), (CX + lean, 210), (CX - 10 + lean, 196)]),
              emblem_col, lw=3.5, hi=False)
    if downed:
        ctx.set_matrix(base_matrix)
        for i in range(3):
            a = i * 2.1 + 0.4
            sparkle(ctx, 96 + math.cos(a) * 30, 214 + math.sin(a) * 10, 9, hex2rgb("#ffe46a"))
        # desaturate the whole sprite for a clear "downed" read
        img = cv.surface
        desaturate(img, 0.55)
    return cv


def desaturate(surface, amount):
    import array
    surface.flush()
    w, h, stride = surface.get_width(), surface.get_height(), surface.get_stride()
    buf = surface.get_data()
    for y in range(h):
        row = y * stride
        for x in range(w):
            i = row + x * 4
            b, g, r, a = buf[i], buf[i + 1], buf[i + 2], buf[i + 3]
            if a == 0:
                continue
            l = int(0.3 * r + 0.59 * g + 0.11 * b)
            buf[i] = int(b + (l * 0.9 - b) * amount)
            buf[i + 1] = int(g + (l * 0.9 - g) * amount)
            buf[i + 2] = int(r + (l - r) * amount)
    surface.mark_dirty()


def portrait(hero_id, size=192):
    """Head-and-shoulders badge from the idle pose, framed with the element colour."""
    src = hero_sprite(hero_id, "idle", None, 320).surface
    ec, ec2 = ELEMENT[HEROES[hero_id]["element"]]
    cv = Canvas(size, size)
    ctx = cv.ctx
    r = size / 2 - 6
    grad = cairo.RadialGradient(size / 2, size * 0.35, 4, size / 2, size / 2, r)
    grad.add_color_stop_rgb(0, *light(ec2, 0.3))
    grad.add_color_stop_rgb(1, *shade(ec, 0.35))
    ctx.arc(size / 2, size / 2, r, 0, 2 * math.pi)
    ctx.set_source(grad)
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    s = size / 210.0
    ctx.scale(s, s)
    ctx.set_source_surface(src, -(160 - 105), -20)
    ctx.paint()
    ctx.restore()
    ctx.arc(size / 2, size / 2, r, 0, 2 * math.pi)
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(8)
    ctx.stroke()
    ctx.arc(size / 2, size / 2, r - 6, 0, 2 * math.pi)
    ctx.set_source_rgba(*ec2, 0.9)
    ctx.set_line_width(3)
    ctx.stroke()
    return cv


# ============================================================================ expansion parts
# New head / outfit / prop / back-item kinds used by the expansion heroes (seren, nyxara, ashara, nerissa,
# voltrix, eirwen, kael, borun). The original drawing functions dispatch here through the EXT_* sets.

EXT_HEADS = ("sun_helm", "crescent_hood", "plume_helm", "pearl_veil", "goggles_messy", "winged_helm", "topknot", "flat_cap",
             "leaf_crown", "antler_helm", "alchemist_goggles", "plague_beak",
             "mirror_circlet", "conductor_hat", "rift_hood", "void_helm", "scribe_beret", "shell_crown", "ranger_visor",
             "ice_braid", "oracle_veil", "stone_brow", "radiant_hair", "gloom_hood")
EXT_OUTFITS = ("tabard", "long_cloak", "phoenix_plate", "sea_robe", "engineer", "frost_plate", "wraps", "apron",
               "moss_cloak", "bark_armor", "alchemist_coat", "plague_robe",
               "layered_robe", "tailcoat", "sigil_plate", "star_cloak", "obsidian_plate", "scribe_robe", "river_dress",
               "ranger_jacket", "frost_coat", "oracle_robe", "stone_gi", "cantor_robe", "tattered_mail")
EXT_TORSO_SHAPES = ("long_cloak", "sea_robe")
EXT_PROPS = ("sun_shield_sword", "chain_staff", "flame_sabre", "conch_staff", "wrench_staff", "crystal_shield_mace",
             "war_fans", "stone_gauntlet", "blossom_staff", "thorn_shield", "thorn_tower", "thorn_whip", "flask", "censer",
             "rune_book", "arcane_orbs", "baton", "long_baton", "rune_shield", "star_gauntlet", "void_daggers",
             "portal_shield", "null_bastion", "portal_glaive", "burning_quill", "burning_scroll", "ember_lantern",
             "water_ribbon", "flood_trident", "heal_orb", "arc_bow", "heavy_bow", "split_bow", "frost_lance",
             "glacier_gauntlet", "chime_staff", "wind_loom", "chain_talisman", "granite_fists", "boulder_shield",
             "fracture_fists", "songbook", "solar_lance", "gloom_glaive", "dread_shield", "soul_scythe")

STONE = hex2rgb("#8f8a86")
BRASS = hex2rgb("#d9a441")
COPPER = hex2rgb("#d9803a")


def hands_for(spec, pose):
    """(left_hand, right_hand) exactly as hero_sprite places them."""
    m = build_metrics(spec["build"])
    if pose == "cast":
        return (CX - m["shoulder"] - 32, 150), (CX + m["shoulder"] + 26, 124)
    return (CX - m["shoulder"] - 10, 236), (CX + m["shoulder"] + 12, 230)


def ext_torso_path(o, s, w, hp, top, lean):
    if o == "long_cloak":
        bottom = GROUND - 10
        pts = [(CX - s * 0.6 + lean, top - 4), (CX + s * 0.6 + lean, top - 4), (CX + s + 10 + lean * 0.6, top + 22),
               (CX + hp + 22, bottom - 20), (CX + hp + 34, bottom + 2), (CX + 20, bottom - 4), (CX - 6, bottom + 4),
               (CX - hp - 30, bottom), (CX - hp - 22, bottom - 22), (CX - s - 10 + lean * 0.6, top + 22)]
        return lambda c: smooth_closed(c, pts, 0.4)
    # sea_robe: flowing robe with a scalloped, wave-like hem that trails to one side
    bottom = GROUND - 6
    pts = [(CX - s * 0.62 + lean, top), (CX + s * 0.62 + lean, top), (CX + s + lean * 0.6, top + 16), (CX + w + 2, 214),
           (CX + hp + 22, bottom - 18), (CX + hp + 40, bottom + 2), (CX + hp + 10, bottom - 6), (CX + 22, bottom + 4),
           (CX + 4, bottom - 6), (CX - 18, bottom + 4), (CX - hp - 18, bottom - 4), (CX - hp - 8, bottom - 22),
           (CX - w - 2, 214), (CX - s + lean * 0.6, top + 16)]
    return lambda c: smooth_closed(c, pts, 0.45)


def ext_torso_detail(ctx, spec, m, lean):
    """Detail painted inside the torso clip."""
    main, second, trim = hex2rgb(spec["main"]), hex2rgb(spec["second"]), hex2rgb(spec["trim"])
    o = spec["outfit"]
    if o == "tabard":
        # plate under the tabard: segmented chest plates showing at the sides
        for side in (-1, 1):
            for i in range(3):
                y = 186 + i * 16
                stroke(ctx, lambda c, side=side, y=y: (c.move_to(CX + side * 26, y), c.line_to(CX + side * 56, y + 4)), shade(main, 0.35), 3)
        flat(ctx, lambda c: rrect_path(c, CX - 60, 232, 120, 12, 5), second)
        stroke(ctx, lambda c: rrect_path(c, CX - 60, 232, 120, 12, 5), INK, 3)
    elif o == "long_cloak":
        # crimson lining showing through the front split, and a dark inner dress
        flat(ctx, lambda c: poly_path(c, [(CX - 8 + lean, 168), (CX + 8 + lean, 168), (CX + 40, 300), (CX - 40, 300)]), second)
        flat(ctx, lambda c: poly_path(c, [(CX - 2 + lean, 176), (CX + 2 + lean, 176), (CX + 24, 300), (CX - 24, 300)]), shade(main, 0.4))
        for side in (-1, 1):
            stroke(ctx, lambda c, side=side: (c.move_to(CX + side * 8 + lean, 168), c.line_to(CX + side * 40, 300)), INK, 3.5)
        # sigil stitching on the cloak edge
        stroke(ctx, lambda c: smooth_open(c, [(CX - 70, 270), (CX - 30, 282), (CX + 10, 278), (CX + 60, 288)]), trim, 3, 0.7)
    elif o == "phoenix_plate":
        paint(ctx, lambda c: smooth_closed(c, [(CX - 34, 176), (CX + 34, 176), (CX + 30, 222), (CX, 236), (CX - 30, 222)], 0.4),
              shade(main, 0.25), lw=4, hi_size=0.6)
        # flame emblem on the breastplate
        paint(ctx, lambda c: smooth_closed(c, [(CX, 186), (CX + 10, 202), (CX + 14, 214), (CX, 226), (CX - 14, 214),
                                                 (CX - 8, 200)], 0.5), second, lw=3, hi=False)
        flat(ctx, lambda c: smooth_closed(c, [(CX, 202), (CX + 6, 214), (CX, 222), (CX - 6, 214)], 0.5), trim)
        flat(ctx, lambda c: rrect_path(c, CX - 60, 232, 120, 12, 5), trim)
        stroke(ctx, lambda c: rrect_path(c, CX - 60, 232, 120, 12, 5), INK, 3)
    elif o == "sea_robe":
        flat(ctx, lambda c: poly_path(c, [(CX - 10 + lean * 0.3, 166), (CX + 10 + lean * 0.3, 166), (CX + 34, 300), (CX - 26, 300)]), second)
        stroke(ctx, lambda c: (c.move_to(CX - 10 + lean * 0.3, 166), c.line_to(CX - 26, 300)), INK, 3)
        stroke(ctx, lambda c: (c.move_to(CX + 10 + lean * 0.3, 166), c.line_to(CX + 34, 300)), INK, 3)
        # foam-wave pattern around the hem
        for k, y in enumerate((258, 272)):
            pts = [(CX - 90 + i * 15, y + (-5 if (i + k) % 2 else 5)) for i in range(13)]
            stroke(ctx, lambda c, pts=pts: smooth_open(c, pts), light(main, 0.55), 4)
        flat(ctx, lambda c: rrect_path(c, CX - 60, 214, 120, 12, 6), trim)
        stroke(ctx, lambda c: rrect_path(c, CX - 60, 214, 120, 12, 6), INK, 3)
        paint(ctx, lambda c: ellipse_path(c, CX + 4, 220, 8, 8), hex2rgb("#ffffff"), lw=3, hi_size=0.6)
    elif o == "engineer":
        # backpack straps, toolbelt with pouches
        for side in (-1, 1):
            flat(ctx, lambda c, side=side: rrect_path(c, CX + side * 26 - 6, 160, 12, 70, 4), hex2rgb("#3a2a20"))
            stroke(ctx, lambda c, side=side: rrect_path(c, CX + side * 26 - 6, 160, 12, 70, 4), INK, 2.5)
            paint(ctx, lambda c, side=side: rrect_path(c, CX + side * 26 - 7, 192, 14, 9, 3), BRASS, lw=2.5, hi=False)
        flat(ctx, lambda c: rrect_path(c, CX - 60, 222, 120, 14, 6), hex2rgb("#6a4428"))
        stroke(ctx, lambda c: rrect_path(c, CX - 60, 222, 120, 14, 6), INK, 3)
        for x in (CX - 36, CX + 24):
            paint(ctx, lambda c, x=x: rrect_path(c, x - 2, 230, 18, 20, 4), hex2rgb("#8a5a34"), lw=3, hi=False)
        paint(ctx, lambda c: rrect_path(c, CX - 10, 220, 20, 18, 4), BRASS, lw=3, hi=False)
        # lightning-bolt patch
        paint(ctx, lambda c: poly_path(c, [(CX - 4, 176), (CX + 10, 176), (CX + 2, 192), (CX + 12, 192), (CX - 6, 212),
                                             (CX - 1, 196), (CX - 10, 196)]), second, lw=2.5, hi=False, shade_amt=0)
    elif o == "frost_plate":
        paint(ctx, lambda c: smooth_closed(c, [(CX - 36, 176), (CX + 36, 176), (CX + 32, 224), (CX, 238), (CX - 32, 224)], 0.4),
              light(second, 0.35), lw=4, hi_size=0.6)
        # frost facets on the breastplate
        for (a, b) in (((CX, 182), (CX, 232)), ((CX - 30, 196), (CX, 210)), ((CX + 30, 196), (CX, 210))):
            stroke(ctx, lambda c, a=a, b=b: (c.move_to(*a), c.line_to(*b)), (1, 1, 1), 3, 0.8)
        flat(ctx, lambda c: rrect_path(c, CX - 60, 234, 120, 12, 5), second)
        stroke(ctx, lambda c: rrect_path(c, CX - 60, 234, 120, 12, 5), INK, 3)
    elif o == "wraps":
        # light cloth wraps crossing the chest
        wrap = second
        for side in (-1, 1):
            flat(ctx, lambda c, side=side: poly_path(c, [(CX + side * 40, 164), (CX + side * 24, 164), (CX - side * 34, 226),
                                                          (CX - side * 18, 226)]), wrap)
            stroke(ctx, lambda c, side=side: (c.move_to(CX + side * 40, 164), c.line_to(CX - side * 18, 226)), INK, 2.5)
            stroke(ctx, lambda c, side=side: (c.move_to(CX + side * 24, 164), c.line_to(CX - side * 34, 226)), INK, 2.5)
    elif o in NAT_OUTFITS:
        nat_torso_detail(ctx, spec, m, lean)
    elif o in W3_OUTFITS:
        w3_torso_detail(ctx, spec, m, lean)
    elif o == "apron":
        # rolled shirt with a button placket
        stroke(ctx, lambda c: (c.move_to(CX, 166), c.line_to(CX, 200)), shade(main, 0.4), 3)


def ext_torso_overlay(ctx, spec, m, lean):
    """Garment parts that hang outside the torso silhouette (drawn over it)."""
    main, second, trim = hex2rgb(spec["main"]), hex2rgb(spec["second"]), hex2rgb(spec["trim"])
    o = spec["outfit"]
    x0 = CX + lean * 0.3
    if o == "tabard":
        tab = hex2rgb(spec.get("tabard", "#fff6dc"))
        paint(ctx, lambda c: smooth_closed(c, [(x0 - 24, 172), (x0 + 24, 172), (x0 + 26, 270), (x0, 280), (x0 - 26, 270)], 0.2),
              tab, lw=LW - 1, hi_size=0.5)
        stroke(ctx, lambda c: smooth_closed(c, [(x0 - 16, 180), (x0 + 16, 180), (x0 + 18, 262), (x0, 270), (x0 - 18, 262)], 0.2), second, 3.5)
        flat(ctx, lambda c: rrect_path(c, x0 - 26, 232, 52, 12, 4), second)
        stroke(ctx, lambda c: rrect_path(c, x0 - 26, 232, 52, 12, 4), INK, 3)
        paint(ctx, lambda c: star_path(c, x0, 204, 15, 9, 8), hex2rgb("#ffd84a"), lw=3, hi=False)
        paint(ctx, lambda c: ellipse_path(c, x0, 204, 7, 7), hex2rgb("#fff7cc"), lw=2.5, hi=False, shade_amt=0)
    elif o == "long_cloak":
        # tall collar points + moon clasp
        for side in (-1, 1):
            paint(ctx, lambda c, side=side: smooth_closed(c, [(CX + side * 8 + lean, 168), (CX + side * 44 + lean, 156),
                                                               (CX + side * 58 + lean, 172), (CX + side * 34 + lean, 184)], 0.4),
                  shade(main, 0.15), lw=4.5, hi=False)
        paint(ctx, lambda c: ellipse_path(c, CX + lean, 174, 10, 10), trim, lw=3.5, hi_size=0.6)
        flat(ctx, lambda c: ellipse_path(c, CX + 4 + lean, 171, 7, 7), shade(main, 0.15))
    elif o == "sea_robe":
        # shell pendant
        paint(ctx, lambda c: smooth_closed(c, [(x0 - 10, 176), (x0 + 10, 176), (x0 + 6, 190), (x0, 194), (x0 - 6, 190)], 0.5),
              hex2rgb("#ffc8c0"), lw=3, hi_size=0.6)
    elif o == "frost_plate":
        # fluffy snow-fur collar
        fur = hex2rgb("#f6fbff")
        for i in range(7):
            t = i / 6.0
            x = CX - 48 + 96 * t + lean
            y = 168 + 6 * math.sin(t * math.pi)
            paint(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 16, 13), fur if i % 2 == 0 else light(hex2rgb("#cfe8ff"), 0.4),
                  lw=4, hi=False, shade_amt=0.15)
        # armoured faulds below the belt
        for side in (-1, 1):
            paint(ctx, lambda c, side=side: smooth_closed(c, [(CX + side * 8, 244), (CX + side * 50, 244), (CX + side * 54, 266),
                                                               (CX + side * 12, 270)], 0.3), light(main, 0.1), lw=4.5, hi=False)
    elif o == "wraps":
        sash = hex2rgb(spec.get("sash", spec["trim"]))
        # neck scarf wrap
        paint(ctx, lambda c: smooth_closed(c, [(CX - 40 + lean, 156), (CX + 40 + lean, 156), (CX + 36 + lean, 176), (CX - 36 + lean, 176)], 0.4),
              sash, lw=4.5)
        # waist sash with a side knot
        paint(ctx, lambda c: smooth_closed(c, [(CX - 40, 222), (CX + 40, 222), (CX + 42, 240), (CX - 42, 240)], 0.3), sash, lw=4.5)
        paint(ctx, lambda c: ellipse_path(c, CX - 30, 232, 9, 9), light(sash, 0.2), lw=3.5, hi=False)
    elif o in NAT_OUTFITS:
        nat_torso_overlay(ctx, spec, m, lean)
    elif o in W3_OUTFITS:
        w3_torso_overlay(ctx, spec, m, lean)
    elif o == "apron":
        leather = second
        for side in (-1, 1):
            outlined_line(ctx, [(x0 + side * 28, 194), (x0 + side * 22, 164)], shade(leather, 0.2), 6, 11, smooth=False)
        paint(ctx, lambda c: rrect_path(c, x0 - 38, 190, 76, 90, 12), leather, lw=LW - 1, hi_size=0.5)
        stroke(ctx, lambda c: rrect_path(c, x0 - 32, 196, 64, 78, 9), trim, 2.2, 0.8)
        paint(ctx, lambda c: rrect_path(c, x0 - 22, 230, 44, 26, 6), shade(leather, 0.25), lw=3.5, hi=False)
        # chisel and pencil poking out of the pocket
        outlined_line(ctx, [(x0 - 10, 232), (x0 - 14, 214)], hex2rgb("#cfd6e6"), 5, 10, smooth=False)
        outlined_line(ctx, [(x0 + 8, 232), (x0 + 12, 218)], hex2rgb("#ffd23a"), 5, 10, smooth=False)
        flat(ctx, lambda c: rrect_path(c, x0 - 56, 222, 18, 12, 4), shade(leather, 0.3))


def ext_shoulders(ctx, spec, m, lean):
    main, second, trim = hex2rgb(spec["main"]), hex2rgb(spec["second"]), hex2rgb(spec["trim"])
    o = spec["outfit"]
    s = m["shoulder"]
    if o in ("tabard", "frost_plate"):
        pad = second if o == "tabard" else light(main, 0.15)
        for side in (-1, 1):
            if o == "frost_plate":
                # ice shard spikes rising off the pauldron
                for k, (dx, h) in enumerate(((-6, 30), (8, 40), (20, 26))):
                    bx = CX + side * (s - 6 + dx) + lean
                    paint(ctx, lambda c, bx=bx, h=h: poly_path(c, [(bx - 7, 172), (bx + side * 4, 172 - h), (bx + 7, 172)]),
                          light(hex2rgb("#7fd8ff"), 0.3 + 0.2 * (k % 2)), lw=3.5, hi=False)
            paint(ctx, lambda c, side=side: smooth_closed(c, [(CX + side * (s - 32) + lean, 160), (CX + side * (s + 16) + lean, 164),
                                                               (CX + side * (s + 20) + lean, 198), (CX + side * (s - 14) + lean, 194)], 0.5),
                  pad, lw=LW, hi_size=0.6)
            if o == "tabard":
                stroke(ctx, lambda c, side=side: smooth_open(c, [(CX + side * (s - 22) + lean, 172), (CX + side * (s + 12) + lean, 178)]),
                       light(pad, 0.5), 3)
    elif o in NAT_OUTFITS:
        nat_shoulders(ctx, spec, m, lean)
    elif o in W3_OUTFITS:
        w3_shoulders(ctx, spec, m, lean)
    elif o == "phoenix_plate":
        ec, ec2 = ELEMENT[spec["element"]]
        for side in (-1, 1):
            ox, oy = CX + side * (s - 8) + lean, 172
            glow(ctx, ox + side * 30, oy - 20, 50, ec2, 0.35)
            # fan of flame feathers sweeping up and out
            for k in range(4):
                a = -math.pi / 2 + side * (0.45 + k * 0.32)
                L = 92 - k * 12
                tip = (ox + math.cos(a) * L, oy + math.sin(a) * L)
                nx, ny = -math.sin(a), math.cos(a)
                mid = (ox + math.cos(a) * L * 0.5, oy + math.sin(a) * L * 0.5)
                pts = [(ox + nx * 7, oy + ny * 7), (mid[0] + nx * 15, mid[1] + ny * 15), tip,
                       (mid[0] - nx * 15, mid[1] - ny * 15), (ox - nx * 7, oy - ny * 7)]
                col = ec if k % 2 == 0 else second
                paint(ctx, lambda c, pts=pts: smooth_closed(c, pts, 0.45), col, lw=4, hi=False)
                flat(ctx, lambda c, mid=mid, tip=tip, nx=nx, ny=ny: poly_path(c, [(mid[0] + nx * 5, mid[1] + ny * 5), tip,
                                                                                   (mid[0] - nx * 5, mid[1] - ny * 5)]), ec2, 0.9)
            paint(ctx, lambda c, side=side: smooth_closed(c, [(CX + side * (s - 30) + lean, 160), (CX + side * (s + 12) + lean, 164),
                                                               (CX + side * (s + 16) + lean, 196), (CX + side * (s - 14) + lean, 192)], 0.5),
                  shade(main, 0.1), lw=LW, hi_size=0.6)
            stroke(ctx, lambda c, side=side: smooth_open(c, [(CX + side * (s - 24) + lean, 174), (CX + side * (s + 10) + lean, 178)]), trim, 4)


def ext_back_items(ctx, spec, pose, lean):
    """Things worn on the back / trailing behind the body (drawn before hair-back and torso)."""
    ec, ec2 = ELEMENT[spec["element"]]
    nat_back_items(ctx, spec, pose, lean)
    w3_back_items(ctx, spec, pose, lean)
    bp = spec.get("backpack")
    if bp == "coils":
        paint(ctx, lambda c: rrect_path(c, CX - 52, 150, 104, 72, 14), hex2rgb("#4a4a58"), lw=LW)
        for side in (-1, 1):
            x = CX + side * 92
            if pose == "cast":
                glow(ctx, x, 70, 46, ec2, 0.7)
            else:
                glow(ctx, x, 70, 30, ec2, 0.45)
            outlined_line(ctx, [(CX + side * 40, 170), (x, 150), (x, 78)], hex2rgb("#5a5a6a"), 10, 17, smooth=False)
            for k in range(5):
                y = 140 - k * 12
                paint(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 13, 5), COPPER, lw=3, hi=False)
            paint(ctx, lambda c, x=x: ellipse_path(c, x, 70, 11, 11), ec2, lw=3.5, hi_size=0.6)
            zig = [(x + side * 4, 60), (x - side * 6, 50), (x + side * 8, 42), (x, 30)]
            stroke(ctx, lambda c, zig=zig: (c.move_to(*zig[0]), [c.line_to(*p) for p in zig[1:]]), ec2, 3.5)
        if pose == "cast":
            # arc jumping between the two coil tips, over the head
            pts = [(CX - 92, 66), (CX - 62, 40), (CX - 30, 54), (CX, 22), (CX + 30, 50), (CX + 62, 34), (CX + 92, 66)]
            stroke(ctx, lambda c: (c.move_to(*pts[0]), [c.line_to(*p) for p in pts[1:]]), ec, 7)
            stroke(ctx, lambda c: (c.move_to(*pts[0]), [c.line_to(*p) for p in pts[1:]]), ec2, 3)
    elif bp == "plans":
        # rolled blueprints in a leather tube, slung diagonally across the back
        a, b = (CX + 40, 222), (CX - 98, 74)
        outlined_line(ctx, [a, b], hex2rgb("#7a5030"), 26, 34, smooth=False)
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        ex, ey = b[0] - math.cos(ang) * 4, b[1] - math.sin(ang) * 4
        paint(ctx, lambda c: ellipse_path(c, ex, ey, 15, 10, ang + math.pi / 2), hex2rgb("#f0e4c4"), lw=4, hi=False)
        # rolled-paper spiral peeking out of the open end
        stroke(ctx, lambda c: ellipse_path(c, ex, ey, 7, 4.5, ang + math.pi / 2), hex2rgb("#4a7ac8"), 2.5)
        for t in (0.72, 0.5):
            px, py = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            outlined_line(ctx, [(px - math.sin(ang) * 15, py + math.cos(ang) * 15), (px + math.sin(ang) * 15, py - math.cos(ang) * 15)],
                          BRASS, 5, 10, smooth=False)
    if spec.get("sash"):
        sash = hex2rgb(spec["sash"])
        fl = 14 if pose == "cast" else 0
        # long scarf tail streaming off the neck in the wind
        paint(ctx, lambda c: smooth_closed(c, [(CX - 20, 158), (CX - 70, 142 - fl), (CX - 112, 112 - fl * 1.5), (CX - 146, 118 - fl * 2),
                                                 (CX - 128, 132 - fl), (CX - 138, 150 - fl), (CX - 96, 148 - fl), (CX - 56, 174),
                                                 (CX - 20, 176)], 0.45), sash, lw=4.5, hi_size=0.6)
        # two sash ends trailing from the waist knot
        for k in range(2):
            dy = k * 18
            paint(ctx, lambda c, dy=dy: smooth_closed(c, [(CX - 40, 226 + dy * 0.3), (CX - 80, 236 + dy - fl * 0.5),
                                                           (CX - 118 + dy, 222 + dy * 1.4 - fl), (CX - 108 + dy, 240 + dy * 1.4 - fl),
                                                           (CX - 76, 252 + dy), (CX - 40, 240 + dy * 0.3)], 0.45),
                  shade(sash, 0.1 * k), lw=4.5, hi=False)


def ext_hair_back(ctx, spec):
    hair = hex2rgb(spec["hair"])
    main, second, trim = hex2rgb(spec["main"]), hex2rgb(spec["second"]), hex2rgb(spec["trim"])
    ec, ec2 = ELEMENT[spec["element"]]
    h = spec["head"]
    if h == "sun_helm":
        # radiant sun disc standing behind the helm
        glow(ctx, CX, 106, 124, ec, 0.45)
        paint(ctx, lambda c: star_path(c, CX, 106, 100, 78, 12, rot=-math.pi / 2), ec, lw=4.5, hi=False)
        paint(ctx, lambda c: star_path(c, CX, 106, 92, 74, 12, rot=-math.pi / 2 + math.pi / 12), light(ec, 0.35), lw=3.5, hi=False)
        paint(ctx, lambda c: ellipse_path(c, CX, 106, 80, 80), ec2, lw=LW, hi_size=0.6)
        stroke(ctx, lambda c: ellipse_path(c, CX, 106, 71, 71), ec, 4)
    elif h == "crescent_hood":
        paint(ctx, lambda c: smooth_closed(c, [(CX - 72, 162), (CX - 78, 100), (CX - 62, 56), (CX, 44), (CX + 62, 56),
                                                 (CX + 78, 100), (CX + 72, 162), (CX, 172)], 0.5), shade(main, 0.25), lw=LW)
    elif h == "pearl_veil":
        veil = light(ec2, 0.55)
        paint(ctx, lambda c: smooth_closed(c, [(CX - 52, 70), (CX + 52, 70), (CX + 84, 150), (CX + 98, 240), (CX + 70, 232),
                                                 (CX + 40, 250), (CX - 40, 250), (CX - 72, 234), (CX - 98, 240), (CX - 84, 150)], 0.5),
              veil, lw=4, alpha=0.6, hi=False)
        paint(ctx, lambda c: smooth_closed(c, [(CX - 60, 96), (CX + 60, 96), (CX + 72, 150), (CX + 80, 206), (CX + 58, 196),
                                                 (CX + 66, 220), (CX + 36, 206), (CX - 36, 206), (CX - 64, 222), (CX - 58, 196),
                                                 (CX - 80, 206), (CX - 72, 150)], 0.5), hair, lw=LW)
    elif h in NAT_HEADS:
        nat_hair_back(ctx, spec)
    elif h in W3_HEADS:
        w3_hair_back(ctx, spec)
    elif h == "topknot":
        # ribbon tails, then the knot itself (its base is hidden by the front hair)
        for k, dy in enumerate((0, 14)):
            paint(ctx, lambda c, dy=dy: smooth_closed(c, [(CX + 8, 46), (CX + 50, 34 + dy), (CX + 86, 46 + dy * 1.6), (CX + 70, 56 + dy * 1.4),
                                                           (CX + 44, 50 + dy), (CX + 10, 58)], 0.5), shade(trim, 0.12 * k), lw=4, hi=False)
        paint(ctx, lambda c: ellipse_path(c, CX, 40, 20, 18), hair, lw=LW)
        paint(ctx, lambda c: smooth_closed(c, [(CX - 8, 26), (CX - 2, 6), (CX + 10, 2), (CX + 8, 24)], 0.5), hair, lw=4.5)


def ext_hair_front(ctx, spec, element_color):
    hair = hex2rgb(spec["hair"])
    main, second, trim = hex2rgb(spec["main"]), hex2rgb(spec["second"]), hex2rgb(spec["trim"])
    ec, ec2 = ELEMENT[spec["element"]]
    h = spec["head"]
    if h == "sun_helm":
        # short hair at the temples, open-faced gilded helm with a sun gem
        for side in (-1, 1):
            paint(ctx, lambda c, side=side: smooth_closed(c, [(CX + side * 64, 124), (CX + side * 58, 92), (CX + side * 40, 96),
                                                               (CX + side * 50, 120)], 0.4), hair, lw=4.5, hi=False)
        helm = hex2rgb(spec["main"])
        paint(ctx, lambda c: smooth_closed(c, [(CX - 64, 112), (CX - 60, 68), (CX - 26, 48), (CX + 26, 48), (CX + 60, 68),
                                                 (CX + 64, 112), (CX + 42, 94), (CX - 42, 94)], 0.5), helm, lw=LW, hi_size=0.7)
        stroke(ctx, lambda c: smooth_open(c, [(CX - 56, 98), (CX - 30, 86), (CX, 82), (CX + 30, 86), (CX + 56, 98)]), second, 6)
        paint(ctx, lambda c: smooth_closed(c, [(CX - 6, 50), (CX + 6, 50), (CX + 8, 30), (CX, 20), (CX - 8, 30)], 0.5), second, lw=4)
        paint(ctx, lambda c: star_path(c, CX, 70, 14, 7, 8), ec, lw=3, hi=False)
        paint(ctx, lambda c: ellipse_path(c, CX, 70, 6, 6), ec2, lw=2.5, hi=False, shade_amt=0)
    elif h == "crescent_hood":
        def hood(c):
            smooth_closed(c, [(CX - 64, 126), (CX - 68, 82), (CX - 72, 46), (CX - 60, 20), (CX - 26, 8), (CX - 42, 24),
                              (CX - 46, 42), (CX - 22, 56), (CX, 58), (CX + 22, 56), (CX + 46, 42), (CX + 42, 20),
                              (CX + 26, 8), (CX + 60, 20), (CX + 72, 46), (CX + 68, 82),
                              (CX + 64, 126), (CX + 46, 94), (CX, 82), (CX - 46, 94)], 0.35)
        paint(ctx, hood, main, lw=LW, hi_pos=(-0.2, -0.25))
        stroke(ctx, lambda c: smooth_open(c, [(CX - 60, 110), (CX - 40, 92), (CX, 84), (CX + 40, 92), (CX + 60, 110)]), second, 5)
        for side in (-1, 1):
            # pale moon-edge along each horn
            stroke(ctx, lambda c, side=side: smooth_open(c, [(CX + side * 62, 70), (CX + side * 62, 34), (CX + side * 48, 18),
                                                              (CX + side * 30, 11)]), trim, 3.5, 0.9)
            glow(ctx, CX + side * 28, 12, 22, ec, 0.85)
        # oath sigil on the brow
        paint(ctx, lambda c: poly_path(c, [(CX, 60), (CX + 8, 70), (CX, 80), (CX - 8, 70)]), ec, lw=3, hi=False)
    elif h == "plume_helm":
        # flame plume crest, then the crimson helm with a nasal guard
        paint(ctx, lambda c: smooth_closed(c, [(CX + 18, 60), (CX + 26, 34), (CX + 14, 6), (CX + 2, 24), (CX - 10, 6),
                                                 (CX - 24, 26), (CX - 46, 16), (CX - 48, 42), (CX - 72, 46), (CX - 54, 62),
                                                 (CX - 20, 62)], 0.45), ec, lw=LW, hi=False)
        flat(ctx, lambda c: smooth_closed(c, [(CX + 10, 58), (CX + 14, 36), (CX + 4, 30), (CX - 8, 38), (CX - 30, 36),
                                                (CX - 40, 54), (CX - 14, 60)], 0.5), ec2, 0.95)
        helm = shade(main, 0.1)
        paint(ctx, lambda c: smooth_closed(c, [(CX - 66, 126), (CX - 64, 72), (CX - 30, 50), (CX + 30, 50), (CX + 64, 72),
                                                 (CX + 66, 126), (CX + 48, 100), (CX + 12, 92), (CX - 12, 92), (CX - 48, 100)], 0.5),
              helm, lw=LW, hi_size=0.7)
        stroke(ctx, lambda c: smooth_open(c, [(CX - 58, 96), (CX, 82), (CX + 58, 96)]), trim, 5)
        paint(ctx, lambda c: rrect_path(c, CX - 5, 80, 10, 30, 5), trim, lw=3.5, hi=False)
    elif h == "pearl_veil":
        pts = [(CX - 62, 126), (CX - 60, 80), (CX - 30, 56), (CX, 60), (CX + 30, 56), (CX + 60, 80), (CX + 62, 126),
               (CX + 50, 100), (CX + 28, 82), (CX, 90), (CX - 28, 82), (CX - 50, 100)]
        paint(ctx, lambda c: smooth_closed(c, pts, 0.45), hair, lw=LW)
        # pearl circlet
        stroke(ctx, lambda c: smooth_open(c, [(CX - 58, 86), (CX - 30, 74), (CX, 70), (CX + 30, 74), (CX + 58, 86)]), INK, 7)
        stroke(ctx, lambda c: smooth_open(c, [(CX - 58, 86), (CX - 30, 74), (CX, 70), (CX + 30, 74), (CX + 58, 86)]), hex2rgb("#e8d3a0"), 3)
        for (x, y) in ((CX - 44, 79), (CX - 22, 72), (CX + 22, 72), (CX + 44, 79)):
            paint(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 5.5, 5.5), hex2rgb("#fffaf4"), lw=2.5, hi_size=0.6, shade_amt=0.2)
        paint(ctx, lambda c: smooth_closed(c, [(CX, 62), (CX + 9, 76), (CX, 88), (CX - 9, 76)], 0.6), hex2rgb("#fffaf4"), lw=3, hi_size=0.7)
        flat(ctx, lambda c: ellipse_path(c, CX, 77, 4, 5), light(ec2, 0.3), 0.8)
        # veil drapes at the sides of the face
        for side in (-1, 1):
            paint(ctx, lambda c, side=side: smooth_closed(c, [(CX + side * 56, 84), (CX + side * 72, 120), (CX + side * 80, 176),
                                                               (CX + side * 62, 168), (CX + side * 58, 120)], 0.5),
                  light(ec2, 0.6), lw=3, alpha=0.55, hi=False)
    elif h == "goggles_messy":
        pts = [(CX - 60, 118), (CX - 74, 98), (CX - 62, 92), (CX - 78, 70), (CX - 52, 66), (CX - 50, 40), (CX - 24, 50),
               (CX - 14, 26), (CX + 6, 46), (CX + 26, 26), (CX + 34, 52), (CX + 62, 44), (CX + 56, 66), (CX + 80, 74),
               (CX + 62, 92), (CX + 72, 110), (CX + 58, 118), (CX + 46, 96), (CX + 24, 104), (CX + 10, 90),
               (CX - 10, 102), (CX - 26, 90), (CX - 44, 100)]
        paint(ctx, lambda c: smooth_closed(c, pts, 0.25), hair, lw=LW, hi_pos=(-0.25, -0.3))
        # goggles pushed up on the forehead
        stroke(ctx, lambda c: smooth_open(c, [(CX - 62, 90), (CX, 80), (CX + 62, 90)]), INK, 12)
        stroke(ctx, lambda c: smooth_open(c, [(CX - 62, 90), (CX, 80), (CX + 62, 90)]), hex2rgb("#4a3a30"), 6)
        for side in (-1, 1):
            paint(ctx, lambda c, side=side: ellipse_path(c, CX + side * 21, 80, 17, 15), BRASS, lw=4.5, hi_size=0.6)
            paint(ctx, lambda c, side=side: ellipse_path(c, CX + side * 21, 80, 10, 9), hex2rgb("#9fe8ff"), lw=3, hi=False, shade_amt=0.2)
            flat(ctx, lambda c, side=side: ellipse_path(c, CX + side * 21 - 3, 77, 3.5, 3), (1, 1, 1))
    elif h == "winged_helm":
        for side in (-1, 1):
            wing = [(CX + side * 54, 100), (CX + side * 64, 64), (CX + side * 90, 20), (CX + side * 102, 40), (CX + side * 92, 58),
                    (CX + side * 108, 64), (CX + side * 94, 82), (CX + side * 104, 94), (CX + side * 70, 108)]
            paint(ctx, lambda c, wing=wing: smooth_closed(c, wing, 0.35), light(ec, 0.45), lw=4.5, hi_size=0.6)
            stroke(ctx, lambda c, side=side: smooth_open(c, [(CX + side * 64, 90), (CX + side * 84, 54)]), ec, 3)
        helm = light(main, 0.05)
        paint(ctx, lambda c: smooth_closed(c, [(CX - 66, 146), (CX - 66, 76), (CX - 30, 48), (CX + 30, 48), (CX + 66, 76),
                                                 (CX + 66, 146), (CX + 50, 138), (CX + 48, 100), (CX, 90), (CX - 48, 100),
                                                 (CX - 50, 138)], 0.4), helm, lw=LW, hi_size=0.7)
        stroke(ctx, lambda c: smooth_open(c, [(CX - 56, 94), (CX, 82), (CX + 56, 94)]), second, 6)
        paint(ctx, lambda c: poly_path(c, [(CX, 54), (CX + 10, 70), (CX, 84), (CX - 10, 70)]), trim, lw=3.5, hi_size=0.6)
    elif h in NAT_HEADS:
        nat_hair_front(ctx, spec)
    elif h in W3_HEADS:
        w3_hair_front(ctx, spec)
    elif h == "topknot":
        pts = [(CX - 60, 112), (CX - 58, 74), (CX - 26, 54), (CX + 20, 54), (CX + 56, 72), (CX + 62, 110), (CX + 48, 90),
               (CX + 30, 98), (CX + 22, 80), (CX - 6, 88), (CX - 26, 80), (CX - 44, 94)]
        paint(ctx, lambda c: smooth_closed(c, pts, 0.45), hair, lw=LW)
        paint(ctx, lambda c: rrect_path(c, CX - 13, 50, 26, 10, 4), trim, lw=3.5, hi=False)
        # headband
        stroke(ctx, lambda c: smooth_open(c, [(CX - 60, 98), (CX, 86), (CX + 60, 98)]), INK, 10)
        stroke(ctx, lambda c: smooth_open(c, [(CX - 60, 98), (CX, 86), (CX + 60, 98)]), trim, 5)
    elif h == "flat_cap":
        cap = hex2rgb(spec.get("cap", "#6e6a5c"))
        # thick beard and moustache (over the mouth), then the flat cap
        paint(ctx, lambda c: smooth_closed(c, [(CX - 58, 110), (CX - 52, 150), (CX - 32, 182), (CX, 196), (CX + 32, 182),
                                                 (CX + 52, 150), (CX + 58, 110), (CX + 44, 128), (CX + 24, 138), (CX, 136),
                                                 (CX - 24, 138), (CX - 44, 128)], 0.45), hair, lw=LW, hi_pos=(-0.2, 0.1))
        for side in (-1, 1):
            paint(ctx, lambda c, side=side: smooth_closed(c, [(CX, 132), (CX + side * 14, 128), (CX + side * 28, 136),
                                                               (CX + side * 20, 144), (CX + side * 4, 140)], 0.5), shade(hair, 0.1), lw=3.5, hi=False)
        stroke(ctx, lambda c: smooth_open(c, [(CX - 8, 152), (CX, 156), (CX + 8, 152)]), INK, 3)
        paint(ctx, lambda c: smooth_closed(c, [(CX - 64, 98), (CX - 70, 74), (CX - 44, 56), (CX + 6, 50), (CX + 54, 56),
                                                 (CX + 74, 74), (CX + 66, 96), (CX, 92)], 0.45), cap, lw=LW, hi_size=0.6)
        stroke(ctx, lambda c: smooth_open(c, [(CX - 40, 60), (CX - 6, 76), (CX + 30, 92)]), shade(cap, 0.3), 3)
        paint(ctx, lambda c: smooth_closed(c, [(CX + 10, 92), (CX + 60, 84), (CX + 94, 90), (CX + 72, 102), (CX + 14, 102)], 0.4),
              shade(cap, 0.2), lw=LW - 1, hi=False)
        paint(ctx, lambda c: ellipse_path(c, CX + 6, 54, 7, 4), shade(cap, 0.25), lw=3, hi=False)


def ext_prop(ctx, spec, hand, pose, element):
    kind = spec["prop"]
    ec, ec2 = ELEMENT[element]
    hx, hy = hand
    lh, rh = hands_for(spec, pose)
    trim = hex2rgb(spec["trim"])
    second = hex2rgb(spec["second"])
    wood = hex2rgb("#8a5a34")
    metal = hex2rgb("#cfd6e6")
    cast = pose == "cast"

    def blade_at(x, y, ang, L, half, col, edge=None):
        tip = (x + math.cos(ang) * L, y + math.sin(ang) * L)
        nx, ny = -math.sin(ang), math.cos(ang)
        b = (x + math.cos(ang) * 16, y + math.sin(ang) * 16)
        pts = [(b[0] + nx * half, b[1] + ny * half), (tip[0] - math.cos(ang) * 16 + nx * half * 0.9, tip[1] - math.sin(ang) * 16 + ny * half * 0.9),
               tip, (tip[0] - math.cos(ang) * 16 - nx * half * 0.9, tip[1] - math.sin(ang) * 16 - ny * half * 0.9),
               (b[0] - nx * half, b[1] - ny * half)]
        paint(ctx, lambda c: poly_path(c, pts), col, lw=4.5, hi_size=0.6)
        if edge:
            stroke(ctx, lambda c: (c.move_to(*b), c.line_to(*tip)), edge, 2.5)
        return b, tip, (nx, ny)

    if kind == "sun_shield_sword":
        # short sword in the right hand (drawn first so the hand grips it)
        ang = -1.3 if not cast else -0.95
        if cast:
            glow(ctx, hx + math.cos(ang) * 60, hy + math.sin(ang) * 60, 56, ec, 0.6)
        b, tip, (nx, ny) = blade_at(hx, hy, ang, 96, 8, metal, light(ec2, 0.2) if not cast else ec)
        outlined_line(ctx, [(b[0] + nx * 18, b[1] + ny * 18), (b[0] - nx * 18, b[1] - ny * 18)], second, 8, 15, smooth=False)
        paint(ctx, lambda c: ellipse_path(c, hx - math.cos(ang) * 16, hy - math.sin(ang) * 16, 6, 6), second, lw=3, hi=False)
        if cast:
            sparkle(ctx, tip[0], tip[1], 12)
        # kite shield on the left arm with a sun emblem
        sx, sy = (lh[0] + 4, lh[1] - 24) if not cast else (lh[0] + 6, lh[1] - 36)
        kite = [(sx - 40, sy - 50), (sx, sy - 60), (sx + 40, sy - 50), (sx + 36, sy + 8), (sx, sy + 68), (sx - 36, sy + 8)]
        inner = [(sx + (x - sx) * 0.78, sy - 3 + (y - sy) * 0.78) for (x, y) in kite]
        paint(ctx, lambda c: smooth_closed(c, kite, 0.3), second, lw=LW, hi_size=0.7)
        paint(ctx, lambda c: smooth_closed(c, inner, 0.3), hex2rgb(spec.get("tabard", "#fff6dc")), lw=3.5, hi_size=0.6)
        if cast:
            glow(ctx, sx, sy - 6, 50, ec2, 0.7)
        paint(ctx, lambda c: star_path(c, sx, sy - 6, 24, 14, 10), ec, lw=3.5, hi=False)
        paint(ctx, lambda c: ellipse_path(c, sx, sy - 6, 11, 11), light(ec, 0.5), lw=3, hi=False, shade_amt=0.1)
        sparkle(ctx, sx - 20, sy - 36, 8)
    elif kind in ("chain_staff", "conch_staff", "wrench_staff"):
        reach = {"chain_staff": 150, "conch_staff": 132, "wrench_staff": 140}[kind]
        if cast:
            reach -= 46 if kind != "chain_staff" else 80
        top = (hx + 10, hy - reach)
        bottom = (hx - 4, hy + 40)
        shaft = {"chain_staff": hex2rgb("#2a1e34"), "conch_staff": hex2rgb("#c8a27a"), "wrench_staff": hex2rgb("#7a8090")}[kind]
        outlined_line(ctx, [bottom, top], shaft, 9, 16, smooth=False)
        tx, ty = top
        if kind == "chain_staff":
            glow(ctx, tx, ty - 18, 60 if cast else 44, ec, 0.8 if cast else 0.55)
            # floating chain links drifting up beside the shaft
            for k in range(4):
                lx = tx - 26 + (k % 2) * 6 - k * 3
                ly = ty + 34 + k * 26 - (10 if cast else 0)
                rot = 0.3 if k % 2 else -0.3
                rx, ry = (10, 5) if k % 2 else (5, 10)
                stroke(ctx, lambda c, lx=lx, ly=ly, rot=rot, rx=rx, ry=ry: ellipse_path(c, lx, ly, rx, ry, rot), INK, 8)
                stroke(ctx, lambda c, lx=lx, ly=ly, rot=rot, rx=rx, ry=ry: ellipse_path(c, lx, ly, rx, ry, rot), hex2rgb("#c9c3d6"), 3.5)
            # oath sigil: crimson ring holding a crescent
            stroke(ctx, lambda c: ellipse_path(c, tx, ty - 18, 22, 22), INK, 12)
            stroke(ctx, lambda c: ellipse_path(c, tx, ty - 18, 22, 22), ec, 6)
            for k in range(4):
                a = k * math.pi / 2 + math.pi / 4
                paint(ctx, lambda c, a=a: poly_path(c, [(tx + math.cos(a) * 20, ty - 18 + math.sin(a) * 20),
                                                        (tx + math.cos(a) * 32, ty - 18 + math.sin(a) * 32),
                                                        (tx + math.cos(a + 0.25) * 22, ty - 18 + math.sin(a + 0.25) * 22)]),
                      ec, lw=2.5, hi=False)
            def crescent(c):
                c.new_sub_path()
                c.arc(tx, ty - 18, 13, math.pi * 0.3, math.pi * 1.7)
                c.arc_negative(tx + 6, ty - 18, 10, math.pi * 1.6, math.pi * 0.4)
                c.close_path()
            paint(ctx, crescent, light(ec, 0.6), lw=3, hi=False)
            if cast:
                sparkle(ctx, tx + 18, ty - 44, 10, light(ec, 0.6))
        elif kind == "conch_staff":
            glow(ctx, tx, ty - 22, 56 if cast else 42, ec2, 0.75 if cast else 0.5)
            conch = [(tx - 18, ty + 4), (tx - 24, ty - 16), (tx - 12, ty - 36), (tx + 4, ty - 56), (tx + 16, ty - 34),
                     (tx + 24, ty - 12), (tx + 14, ty + 6)]
            paint(ctx, lambda c: smooth_closed(c, conch, 0.5), hex2rgb("#ffe0cc"), lw=4.5, hi_size=0.6)
            for k in range(3):
                y = ty - 12 - k * 13
                stroke(ctx, lambda c, y=y, k=k: smooth_open(c, [(tx - 20 + k * 5, y + 4), (tx, y - 4), (tx + 20 - k * 5, y + 2)]), INK, 2.5)
            # spikes on the shell shoulder and the pink opening
            for (px, py) in ((tx - 24, ty - 20), (tx + 22, ty - 22)):
                paint(ctx, lambda c, px=px, py=py: poly_path(c, [(px, py - 6), (px + (8 if px > tx else -8), py - 2), (px, py + 6)]),
                      hex2rgb("#ffe0cc"), lw=3, hi=False)
            paint(ctx, lambda c: ellipse_path(c, tx + 4, ty + 2, 13, 8, -0.2), hex2rgb("#ff9fb4"), lw=3.5, hi=False)
            if cast:
                for (bx, by, r) in ((tx - 30, ty - 50, 7), (tx + 30, ty - 60, 5), (tx - 6, ty - 74, 6), (tx + 22, ty - 84, 4)):
                    stroke(ctx, lambda c, bx=bx, by=by, r=r: ellipse_path(c, bx, by, r, r), (1, 1, 1), 2.5)
                    paint(ctx, lambda c, bx=bx, by=by, r=r: ellipse_path(c, bx, by, r, r), ec2, lw=0, hi=False, alpha=0.5)
        else:
            glow(ctx, tx, ty - 22, 60 if cast else 40, ec2, 0.8 if cast else 0.5)
            # open-ended wrench jaw
            def jaw(c):
                c.new_sub_path()
                c.arc(tx, ty - 20, 24, -math.pi * 0.3, math.pi * 1.3)
                c.arc_negative(tx, ty - 20, 11, math.pi * 1.3, -math.pi * 0.3)
                c.close_path()
            paint(ctx, jaw, metal, lw=LW - 1, hi_size=0.6)
            paint(ctx, lambda c: rrect_path(c, tx - 8, ty - 4, 16, 18, 4), BRASS, lw=3.5, hi=False)
            zig = [(tx - 8, ty - 36), (tx + 4, ty - 26), (tx - 4, ty - 20), (tx + 8, ty - 12)] if not cast else \
                  [(tx - 6, ty - 26), (tx + 8, ty - 44), (tx - 6, ty - 56), (tx + 12, ty - 72), (tx + 2, ty - 84)]
            stroke(ctx, lambda c: (c.move_to(*zig[0]), [c.line_to(*p) for p in zig[1:]]), ec, 7)
            stroke(ctx, lambda c: (c.move_to(*zig[0]), [c.line_to(*p) for p in zig[1:]]), ec2, 3)
            sparkle(ctx, tx + 20, ty - 44, 8, ec2)
    elif kind == "flame_sabre":
        ang = -1.1 if not cast else -1.95
        ctx.save()
        ctx.translate(hx, hy)
        ctx.rotate(ang)
        glow(ctx, 70, -10, 70, ec, 0.45 if not cast else 0.7)
        # flame tongues licking off the curved back edge
        for k, (x, L) in enumerate(((44, 22), (68, 26), (92, 24), (112, 18))):
            paint(ctx, lambda c, x=x, L=L: smooth_closed(c, [(x - 10, -10 - x * 0.12), (x - 4, -18 - L - x * 0.12), (x + 4, -24 - x * 0.12),
                                                               (x + 12, -12 - L * 0.6 - x * 0.12), (x + 10, -6 - x * 0.12)], 0.5),
                  ec if k % 2 == 0 else hex2rgb(spec["second"]), lw=3.5, hi=False)
        blade = [(16, -9), (60, -16), (100, -24), (130, -40), (112, -14), (70, 0), (16, 7)]
        paint(ctx, lambda c: smooth_closed(c, blade, 0.3), metal, lw=4.5, hi_size=0.6)
        stroke(ctx, lambda c: smooth_open(c, [(22, -5), (70, -10), (112, -24)]), ec2, 3)
        outlined_line(ctx, [(14, -20), (14, 20)], trim, 9, 16, smooth=False)
        outlined_line(ctx, [(-20, 0), (12, 0)], hex2rgb("#4a2a1a"), 9, 16, smooth=False)
        paint(ctx, lambda c: ellipse_path(c, -22, 0, 6, 6), trim, lw=3, hi=False)
        ctx.restore()
        if cast:
            sparkle(ctx, hx + math.cos(ang) * 132, hy + math.sin(ang) * 132, 12)
    elif kind == "crystal_shield_mace":
        # flanged mace in the right hand
        ang = -1.25 if not cast else -1.9
        head = (hx + math.cos(ang) * 78, hy + math.sin(ang) * 78)
        outlined_line(ctx, [(hx - math.cos(ang) * 16, hy - math.sin(ang) * 16), head], hex2rgb("#5f6f8a"), 9, 16, smooth=False)
        if cast:
            glow(ctx, head[0], head[1], 52, ec2, 0.75)
        paint(ctx, lambda c: star_path(c, head[0], head[1], 28, 18, 8, rot=ang), metal, lw=4.5, hi_size=0.6)
        paint(ctx, lambda c: ellipse_path(c, head[0], head[1], 11, 11), ec, lw=3.5, hi=False)
        # hexagonal faceted crystal greatshield on the left arm
        sx, sy = (lh[0] + 6, lh[1] - 32) if not cast else (lh[0] + 8, lh[1] - 42)
        hexa = [(sx, sy - 78), (sx + 46, sy - 48), (sx + 46, sy + 42), (sx, sy + 76), (sx - 46, sy + 42), (sx - 46, sy - 48)]
        glow(ctx, sx, sy, 96, ec2, 0.4 if not cast else 0.7)
        paint(ctx, lambda c: poly_path(c, hexa), mix(ec, (1, 1, 1), 0.25), lw=LW, alpha=0.95, hi_size=0.8)
        inner = [(sx + (x - sx) * 0.5, sy + (y - sy) * 0.5) for (x, y) in hexa]
        paint(ctx, lambda c: poly_path(c, inner), ec2, lw=3.5, hi=False, shade_amt=0.15)
        for (ox, oy), (ix, iy) in zip(hexa, inner):
            stroke(ctx, lambda c, ox=ox, oy=oy, ix=ix, iy=iy: (c.move_to(ox, oy), c.line_to(ix, iy)), (1, 1, 1), 2.5, 0.8)
        sparkle(ctx, sx - 18, sy - 44, 10)
        sparkle(ctx, sx + 16, sy + 30, 6)
    elif kind in NAT_PROPS:
        nat_prop(ctx, spec, hand, pose, element)
    elif kind in W3_PROPS:
        w3_prop(ctx, spec, hand, pose, element)
    elif kind == "war_fans":
        for side, (fx, fy) in ((1, rh), (-1, lh)):
            r = 46 if not cast else 54
            if cast:
                a0, a1 = -math.pi / 2 - 1.2, -math.pi / 2 + 1.2
            else:
                a0, a1 = (-1.75, -0.2) if side > 0 else (-math.pi + 0.2, -math.pi + 1.75)
            n = 6
            pts = [(fx, fy)]
            for i in range(n * 2 + 1):
                a = a0 + (a1 - a0) * i / (n * 2)
                rr = r + 8 if i % 2 == 0 else r - 2
                pts.append((fx + math.cos(a) * rr, fy + math.sin(a) * rr))
            if cast:
                glow(ctx, fx, fy - 26, 58, ec2, 0.65)
            paint(ctx, lambda c, pts=pts: poly_path(c, pts), ec, lw=LW - 1, hi_size=0.6)
            flat(ctx, lambda c, fx=fx, fy=fy, a0=a0, a1=a1, r=r: (c.move_to(fx, fy), c.arc(fx, fy, r * 0.45, a0, a1), c.close_path()),
                 hex2rgb("#2c3c4c"), 0.9)
            for i in range(n + 1):
                a = a0 + (a1 - a0) * i / n
                stroke(ctx, lambda c, a=a, fx=fx, fy=fy, r=r: (c.move_to(fx, fy), c.line_to(fx + math.cos(a) * (r + 6), fy + math.sin(a) * (r + 6))),
                       INK, 2.5)
            paint(ctx, lambda c, fx=fx, fy=fy: ellipse_path(c, fx, fy, 6, 6), metal, lw=3, hi=False)
            if cast:
                for k in range(2):
                    rr = r + 18 + k * 12
                    stroke(ctx, lambda c, fx=fx, fy=fy, rr=rr: c.arc(fx, fy - 4, rr, -math.pi / 2 - 0.9, -math.pi / 2 - 0.2), ec2, 4 - k)
    elif kind == "stone_gauntlet":
        ox, oy = (hx + 2, hy - 2) if not cast else (hx + 2, hy - 8)
        glow(ctx, ox, oy, 56, ec2, 0.35 if not cast else 0.75)
        paint(ctx, lambda c: rrect_path(c, ox - 36, oy - 30, 72, 66, 9), STONE, lw=LW, hi_size=0.6)
        for k in range(4):
            paint(ctx, lambda c, k=k: rrect_path(c, ox - 32 + k * 16, oy - 38, 15, 16, 4), light(STONE, 0.15), lw=3.5, hi=False)
        # cracks and a glowing rune square
        stroke(ctx, lambda c: (c.move_to(ox - 30, oy + 20), c.line_to(ox - 20, oy + 14), c.line_to(ox - 22, oy + 4)), INK, 2.5)
        stroke(ctx, lambda c: (c.move_to(ox + 32, oy + 26), c.line_to(ox + 22, oy + 24)), INK, 2.5)
        paint(ctx, lambda c: rrect_path(c, ox - 11, oy - 6, 22, 22, 4), ec2, lw=3, hi=False, shade_amt=0.15)
        stroke(ctx, lambda c: (c.move_to(ox - 5, oy), c.line_to(ox + 5, oy + 10), c.move_to(ox + 5, oy), c.line_to(ox - 5, oy + 10)),
               shade(ec2, 0.5), 2.5)
        if cast:
            for (px, py, r) in ((ox - 42, oy - 44, 7), (ox + 44, oy - 36, 6), (ox + 4, oy - 58, 5)):
                paint(ctx, lambda c, px=px, py=py, r=r: poly_path(c, [(px - r, py), (px, py - r), (px + r, py + 2), (px, py + r)]),
                      STONE, lw=3, hi=False)


# ============================================================================ nature & poison parts
# Heroes liora (Grove Warden), thalen (Thornguard), vesper (Alchemist) and sable (Plague Doctor). Unlike the
# earlier heroes, their evolutions change gear, not only trim/halo/wings: the drawers read spec["_evo"]
# ("A" / "B" / None) and spec["_pose"], which hero_sprite sets after applying the hero's evo_spec overrides.

NAT_HEADS = ("leaf_crown", "antler_helm", "alchemist_goggles", "plague_beak")
NAT_OUTFITS = ("moss_cloak", "bark_armor", "alchemist_coat", "plague_robe")
NAT_TORSO_SHAPES = ("moss_cloak", "alchemist_coat", "plague_robe")
NAT_PROPS = ("blossom_staff", "thorn_shield", "thorn_tower", "thorn_whip", "flask", "censer")

LEAF = hex2rgb("#4fae4a")
LEAF_LIGHT = hex2rgb("#8fd65a")
BLOSSOM_CORE = hex2rgb("#ffe36a")
PALE_WOOD = hex2rgb("#dcc49a")
DARK_WOOD = hex2rgb("#6a4426")
GLASS = hex2rgb("#e4f6ff")
MIASMA = hex2rgb("#8a4ac8")
SMOKE = hex2rgb("#9a9aa4")


def _leaf(ctx, x, y, ang, L, w, col, lw=3.0, vein=True):
    ca, sa = math.cos(ang), math.sin(ang)
    nx, ny = -sa, ca
    tip = (x + ca * L, y + sa * L)
    m1 = (x + ca * L * 0.45 + nx * w, y + sa * L * 0.45 + ny * w)
    m2 = (x + ca * L * 0.45 - nx * w, y + sa * L * 0.45 - ny * w)
    paint(ctx, lambda c: smooth_closed(c, [(x, y), m1, tip, m2], 0.55), col, lw=lw, hi=False, shade_amt=0.2)
    if vein:
        stroke(ctx, lambda c: (c.move_to(x + ca * L * 0.15, y + sa * L * 0.15), c.line_to(x + ca * L * 0.75, y + sa * L * 0.75)),
               shade(col, 0.45), 1.8)


def _blossom(ctx, x, y, r, col, glow_col=None, glow_a=0.0, glow_k=3.2):
    if glow_col:
        glow(ctx, x, y, r * glow_k, glow_col, glow_a)
    for k in range(5):
        a = -math.pi / 2 + k * 2 * math.pi / 5
        paint(ctx, lambda c, a=a: ellipse_path(c, x + math.cos(a) * r * 0.72, y + math.sin(a) * r * 0.72, r * 0.62, r * 0.5, a),
              col, lw=2.5, hi=False, shade_amt=0.15)
    paint(ctx, lambda c: ellipse_path(c, x, y, r * 0.4, r * 0.4), BLOSSOM_CORE, lw=2, hi=False, shade_amt=0)


def _thorn(ctx, x, y, ang, L, col, lw=2.5):
    nx, ny = -math.sin(ang), math.cos(ang)
    w = L * 0.4
    paint(ctx, lambda c: poly_path(c, [(x + nx * w, y + ny * w), (x + math.cos(ang) * L, y + math.sin(ang) * L), (x - nx * w, y - ny * w)]),
          col, lw=lw, hi=False, shade_amt=0)


def _cloud(ctx, blobs, col, alpha=1.0, lw=3.5, hi_col=None):
    """Union of circles with a single ink outline (smoke puffs, miasma, spore clouds)."""
    def path(c):
        for (x, y, r) in blobs:
            ellipse_path(c, x, y, r, r)
    ctx.push_group()
    if lw > 0:
        stroke(ctx, path, INK, lw * 2)
    flat(ctx, path, col)
    if hi_col:
        flat(ctx, lambda c: [ellipse_path(c, x - r * 0.25, y - r * 0.3, r * 0.45, r * 0.35) for (x, y, r) in blobs], hi_col, 0.55)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(alpha)


def _mushroom(ctx, x, y, r, cap, spot=(1, 0.97, 0.88), glow_col=None):
    if glow_col:
        glow(ctx, x, y, r * 2.6, glow_col, 0.55)
    paint(ctx, lambda c: rrect_path(c, x - r * 0.3, y - r * 0.2, r * 0.6, r * 1.1, r * 0.25), hex2rgb("#f4ead2"), lw=2.5, hi=False)
    paint(ctx, lambda c: smooth_closed(c, [(x - r, y), (x - r * 0.7, y - r * 0.75), (x, y - r * 0.95), (x + r * 0.7, y - r * 0.75),
                                         (x + r, y), (x, y + r * 0.1)], 0.5), cap, lw=2.8, hi_size=0.6)
    for (dx, dy, rr) in ((-0.4, -0.45, 0.17), (0.3, -0.6, 0.14), (0.55, -0.2, 0.11)):
        flat(ctx, lambda c, dx=dx, dy=dy, rr=rr: ellipse_path(c, x + dx * r, y + dy * r, rr * r, rr * r), spot)


def _cross(ctx, x, y, r, col, glow_a=0.7):
    glow(ctx, x, y, r * 3.2, col, glow_a)
    t = r * 0.38
    pts = [(x - t, y - r), (x + t, y - r), (x + t, y - t), (x + r, y - t), (x + r, y + t), (x + t, y + t), (x + t, y + r),
           (x - t, y + r), (x - t, y + t), (x - r, y + t), (x - r, y - t), (x - t, y - t)]
    paint(ctx, lambda c: poly_path(c, pts), col, lw=2.5, hi_size=0.7, shade_amt=0.1)


def _flask_vial(ctx, x, y, liquid, scale=1.0, lw=2.5):
    w, h = 9 * scale, 18 * scale
    paint(ctx, lambda c: rrect_path(c, x - w / 2, y - h / 2, w, h, w * 0.45), GLASS, lw=lw, hi=False, shade_amt=0.1)
    flat(ctx, lambda c: rrect_path(c, x - w / 2 + 1.5, y - h * 0.05, w - 3, h * 0.5, w * 0.35), liquid)
    paint(ctx, lambda c: rrect_path(c, x - w * 0.35, y - h / 2 - 5 * scale, w * 0.7, 6 * scale, 2), hex2rgb("#a8743a"), lw=2, hi=False)


# ---------------------------------------------------------------------------- torso

def nat_torso_path(spec, s, w, hp, top, lean):
    o, evo = spec["outfit"], spec.get("_evo")
    if o == "moss_cloak":
        bottom = GROUND - 8
        n = 9
        hem = []
        for i in range(n + 1):
            t = i / float(n)
            x = CX + hp + 26 - (2 * hp + 52) * t
            hem.append((x, bottom - (0 if i % 2 == 0 else 16)))
        pts = [(CX - s * 0.6 + lean, top - 2), (CX + s * 0.6 + lean, top - 2), (CX + s + 8 + lean * 0.6, top + 22),
               (CX + hp + 12, 232)] + hem + [(CX - hp - 12, 232), (CX - s - 8 + lean * 0.6, top + 22)]
        return lambda c: smooth_closed(c, pts, 0.25)
    if o == "alchemist_coat":
        bottom = 280
        pts = [(CX - s * 0.6 + lean, top), (CX + s * 0.6 + lean, top), (CX + s + 4 + lean * 0.6, top + 16), (CX + w + 4, 214),
               (CX + hp + 22, bottom), (CX + 18, bottom - 2), (CX, 246), (CX - 18, bottom - 2), (CX - hp - 22, bottom),
               (CX - w - 4, 214), (CX - s - 4 + lean * 0.6, top + 16)]
        if evo == "A":
            # scorched, ragged tails
            pts[4:10] = [(CX + hp + 22, bottom - 4), (CX + hp + 10, bottom - 14), (CX + hp, bottom), (CX + 18, bottom - 6), (CX, 246),
                         (CX - 18, bottom - 6), (CX - hp + 2, bottom), (CX - hp - 10, bottom - 14), (CX - hp - 22, bottom - 4)]
        return lambda c: smooth_closed(c, pts, 0.32)
    # plague_robe
    bottom = GROUND - 6
    if evo == "A":
        hem = [(CX + hp + 18, bottom - 4), (CX + hp + 4, bottom - 18), (CX + 26, bottom + 2), (CX + 10, bottom - 14), (CX - 8, bottom + 4),
               (CX - 24, bottom - 14), (CX - hp - 4, bottom + 2), (CX - hp - 18, bottom - 6)]
    else:
        hem = [(CX + hp + 16, bottom - 2), (CX, bottom + 4), (CX - hp - 16, bottom - 2)]
    pts = [(CX - s * 0.62 + lean, top), (CX + s * 0.62 + lean, top), (CX + s + lean * 0.6, top + 16), (CX + w + 4, 214)] + hem + \
          [(CX - w - 4, 214), (CX - s + lean * 0.6, top + 16)]
    return lambda c: smooth_closed(c, pts, 0.4 if evo != "A" else 0.25)


def nat_torso_detail(ctx, spec, m, lean):
    main, second, trim = hex2rgb(spec["main"]), hex2rgb(spec["second"]), hex2rgb(spec["trim"])
    o, evo = spec["outfit"], spec.get("_evo")
    ec, ec2 = ELEMENT[spec["element"]]
    x0 = CX + lean * 0.3
    if o == "moss_cloak":
        dress = hex2rgb(spec.get("dress", "#efe6c8"))
        flat(ctx, lambda c: poly_path(c, [(x0 - 6, 168), (x0 + 6, 168), (CX + 30, 300), (CX - 30, 300)]), dress)
        for side in (-1, 1):
            stroke(ctx, lambda c, side=side: (c.move_to(x0 + side * 6, 168), c.line_to(CX + side * 30, 300)), INK, 3)
        # moss texture
        for (dx, dy, r) in ((-44, 190, 6), (-30, 238, 5), (-58, 262, 7), (40, 200, 5), (52, 248, 7), (28, 270, 5), (-48, 222, 4)):
            flat(ctx, lambda c, dx=dx, dy=dy, r=r: ellipse_path(c, CX + dx, dy, r, r * 0.8), shade(main, 0.35), 0.8)
            flat(ctx, lambda c, dx=dx, dy=dy, r=r: ellipse_path(c, CX + dx - 2, dy - 2, r * 0.5, r * 0.4), light(main, 0.3), 0.8)
        # vine belt
        vine = [(CX - 70, 222), (CX - 24, 230), (CX + 20, 226), (CX + 70, 218)]
        outlined_line(ctx, vine, hex2rgb("#3f7a2a"), 5, 10)
        for (x, y, a) in ((CX - 40, 228, 2.2), (CX + 6, 228, 0.9), (CX + 44, 222, 2.4)):
            _leaf(ctx, x, y, a, 16, 6, LEAF_LIGHT, lw=2.5, vein=False)
        if evo == "B":
            # healer's satchel with a leaf cross
            paint(ctx, lambda c: rrect_path(c, CX + 18, 232, 26, 22, 6), hex2rgb("#c89a5a"), lw=3, hi=False)
            _cross(ctx, CX + 31, 243, 6, LEAF, glow_a=0.0)
    elif o == "bark_armor":
        if evo == "B":
            # light leather jerkin crossed with vine straps
            for side in (-1, 1):
                outlined_line(ctx, [(CX + side * 44, 168), (CX - side * 30, 236)], hex2rgb("#3f7a2a"), 7, 13, smooth=False)
                for t in (0.3, 0.65):
                    px, py = CX + side * 44 + (-side * 74) * t, 168 + 68 * t
                    _thorn(ctx, px, py, -math.pi / 2 - side * 0.6, 9, PALE_WOOD, lw=2)
        else:
            plate = light(main, 0.18)
            chest = [(CX - 38, 174), (CX + 38, 174), (CX + 34, 226), (CX, 240), (CX - 34, 226)]
            paint(ctx, lambda c: smooth_closed(c, chest, 0.35), plate, lw=4, hi_size=0.6)
            # bark grain
            for (a, b) in (((CX - 22, 182), (CX - 18, 226)), ((CX - 4, 180), (CX - 2, 236)), ((CX + 16, 182), (CX + 20, 224))):
                stroke(ctx, lambda c, a=a, b=b: smooth_open(c, [a, ((a[0] + b[0]) / 2 + 4, (a[1] + b[1]) / 2), b]), shade(plate, 0.4), 3)
            # moss on the plate
            _cloud(ctx, [(CX - 26, 178, 9), (CX - 12, 176, 8), (CX + 24, 180, 7)], second, lw=2)
            if evo == "A":
                # second, heavier layer of bark plates on the belly
                for i in range(2):
                    y = 222 + i * 12
                    paint(ctx, lambda c, y=y: rrect_path(c, CX - 52, y, 104, 14, 6), shade(main, 0.1), lw=3.5, hi=False)
        flat(ctx, lambda c: rrect_path(c, CX - 60, 236, 120, 12, 5), DARK_WOOD)
        stroke(ctx, lambda c: rrect_path(c, CX - 60, 236, 120, 12, 5), INK, 3)
        _leaf(ctx, CX - 8, 242, -0.3, 18, 7, trim, lw=2.5, vein=False)
    elif o == "alchemist_coat":
        vest = second
        flat(ctx, lambda c: poly_path(c, [(x0 - 18, 166), (x0 + 18, 166), (CX + 14, 248), (CX - 14, 248)]), vest)
        for side in (-1, 1):
            stroke(ctx, lambda c, side=side: smooth_open(c, [(x0 + side * 18, 166), (x0 + side * 26, 196), (CX + side * 14, 248)]), INK, 3)
        for i in range(3):
            paint(ctx, lambda c, i=i: ellipse_path(c, CX + 1, 196 + i * 16, 3.5, 3.5), trim, lw=2, hi=False, shade_amt=0)
        # pockets
        for side in (-1, 1):
            paint(ctx, lambda c, side=side: rrect_path(c, CX + side * 40 - 11, 232, 22, 16, 4), shade(main, 0.2), lw=3, hi=False)
        if evo == "A":
            for (dx, dy, r) in ((-46, 262, 13), (40, 250, 11), (-30, 206, 8), (52, 214, 9), (10, 266, 9)):
                flat(ctx, lambda c, dx=dx, dy=dy, r=r: ellipse_path(c, CX + dx, dy, r, r * 0.8), hex2rgb("#1e1418"), 0.7)
                stroke(ctx, lambda c, dx=dx, dy=dy, r=r: ellipse_path(c, CX + dx, dy, r * 0.75, r * 0.6), hex2rgb("#ff8a2a"), 1.8, 0.75)
        else:
            # old potion stain
            flat(ctx, lambda c: smooth_closed(c, [(CX - 52, 252), (CX - 38, 246), (CX - 30, 258), (CX - 40, 266), (CX - 54, 262)], 0.5), ec, 0.55)
    elif o == "plague_robe":
        stroke(ctx, lambda c: (c.move_to(x0, 170), c.line_to(CX, 300)), shade(main, 0.45), 3)
        belt = hex2rgb("#4a3a2a") if evo != "B" else second
        flat(ctx, lambda c: rrect_path(c, CX - 60, 222, 120, 12, 5), belt)
        stroke(ctx, lambda c: rrect_path(c, CX - 60, 222, 120, 12, 5), INK, 3)
        for x in (CX - 38, CX + 22):
            paint(ctx, lambda c, x=x: rrect_path(c, x, 230, 16, 18, 5), shade(belt, 0.1) if evo != "B" else light(second, 0.2), lw=3, hi=False)
        if evo == "B":
            for side in (-1, 1):
                stroke(ctx, lambda c, side=side: (c.move_to(x0 + side * 12, 236), c.line_to(CX + side * 20, 300)), second, 6)


def nat_torso_overlay(ctx, spec, m, lean):
    o, evo = spec["outfit"], spec.get("_evo")
    ec, ec2 = ELEMENT[spec["element"]]
    trim = hex2rgb(spec["trim"])
    if o == "moss_cloak":
        if evo == "A":
            # wild overhanging leaves along the hem
            for i in range(7):
                x = CX - 70 + i * 23
                _leaf(ctx, x, 262 + (i % 2) * 6, math.pi / 2 + (i - 3) * 0.18, 26, 9, LEAF if i % 2 else LEAF_LIGHT, lw=3)
        elif evo == "B":
            for (x, y, r) in ((CX - 58, 278, 11), (CX + 52, 276, 9), (CX - 36, 284, 7)):
                _mushroom(ctx, x, y, r, hex2rgb("#c8553d"))
    elif o == "alchemist_coat":
        # bandolier of flasks from the left shoulder to the right hip
        a, b = (CX - 44 + lean, 166), (CX + 48, 244)
        outlined_line(ctx, [a, b], hex2rgb("#6a4428"), 9, 15, smooth=False)
        liquids = (ec, MIASMA, ec, hex2rgb("#ff8a2a") if evo == "A" else MIASMA)
        if evo == "B":
            liquids = (MIASMA, ec, MIASMA, MIASMA)
        for k, t in enumerate((0.18, 0.4, 0.62, 0.84)):
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            glow(ctx, x, y, 16, liquids[k], 0.45)
            _flask_vial(ctx, x, y - 2, liquids[k])
            if evo == "A" and k % 2 == 0:
                sparkle(ctx, x + 8, y - 18, 7, hex2rgb("#ffe36a"))
        paint(ctx, lambda c: rrect_path(c, CX + 38, 236, 20, 16, 4), BRASS, lw=3, hi=False)
    elif o == "plague_robe" and evo == "A":
        # a third censer hanging from the belt
        _censer(ctx, CX - 30, 262, 11, spec, chain_from=(CX - 30, 232))


def nat_shoulders(ctx, spec, m, lean):
    main, second, trim = hex2rgb(spec["main"]), hex2rgb(spec["second"]), hex2rgb(spec["trim"])
    o, evo = spec["outfit"], spec.get("_evo")
    s = m["shoulder"]
    if o == "moss_cloak":
        # leaf collar around the neck, blossom clasp
        n = 9 if evo != "A" else 11
        for i in range(n):
            t = i / float(n - 1)
            x = CX - 54 + 108 * t + lean
            y = 166 + 8 * math.sin(t * math.pi)
            ang = math.pi / 2 + (0.5 - t) * 1.9
            _leaf(ctx, x, y - 4, ang, 30 if evo != "A" else 36, 10, LEAF if i % 2 else LEAF_LIGHT, lw=3)
        if evo == "A":
            # twigs sprouting from the shoulders
            for side in (-1, 1):
                outlined_line(ctx, [(CX + side * (s - 6) + lean, 170), (CX + side * (s + 14) + lean, 150), (CX + side * (s + 20) + lean, 132)],
                              DARK_WOOD, 5, 10)
                _leaf(ctx, CX + side * (s + 20) + lean, 132, -math.pi / 2 + side * 0.6, 18, 7, LEAF_LIGHT, lw=2.5, vein=False)
        _blossom(ctx, CX + lean, 176, 9, trim)
    elif o == "bark_armor":
        if evo == "B":
            # light leaf pauldrons
            for side in (-1, 1):
                for k in range(3):
                    _leaf(ctx, CX + side * (s - 22 + k * 10) + lean, 168 + k * 4, math.pi / 2 - side * (0.9 + k * 0.25), 30, 10,
                          second if k % 2 else LEAF_LIGHT, lw=3)
            return
        big = 1.25 if evo == "A" else 1.0
        for side in (-1, 1):
            ox = CX + side * (s - 8) + lean
            pad = [(ox - side * 24, 160 - 6 * big), (ox + side * 22 * big, 160), (ox + side * 26 * big, 196 + 6 * big), (ox - side * 10, 194)]
            for k, (dx, ang) in enumerate(((-10, -1.9), (4, -1.57), (18, -1.2))):
                if side < 0:
                    ang = -math.pi - ang
                _thorn(ctx, ox + side * dx * big, 162 - 2 * big, ang, 16 * big, PALE_WOOD)
            paint(ctx, lambda c, pad=pad: smooth_closed(c, pad, 0.5), main, lw=LW, hi_size=0.6)
            stroke(ctx, lambda c, ox=ox: smooth_open(c, [(ox - side * 12, 172), (ox + side * 6, 178), (ox + side * 16, 190)]), shade(main, 0.4), 3)
            _cloud(ctx, [(ox - side * 10, 162, 9), (ox + side * 6, 160, 9), (ox + side * 18, 164, 7)], second, lw=2)
            if evo == "A":
                paint(ctx, lambda c, ox=ox: smooth_closed(c, [(ox - side * 6, 188), (ox + side * 30, 190), (ox + side * 30, 212), (ox - side * 2, 208)], 0.5),
                      shade(main, 0.15), lw=4.5, hi=False)
    elif o == "alchemist_coat":
        # high stiff collar
        col = shade(main, 0.15)
        for side in (-1, 1):
            paint(ctx, lambda c, side=side: smooth_closed(c, [(CX + side * 12 + lean, 170), (CX + side * 44 + lean, 136),
                                                               (CX + side * 58 + lean, 150), (CX + side * 42 + lean, 180)], 0.4),
                  col, lw=4.5, hi=False)
    elif o == "plague_robe":
        # raven-feather mantle over the shoulders
        fe = hex2rgb(spec.get("feather", "#26222e"))
        sheen = hex2rgb("#7a5aa8") if evo != "B" else hex2rgb("#ffffff")
        rows = ((0, 13, 50, 11), (1, 9, 34, 10)) if evo != "A" else ((0, 15, 60, 12), (1, 11, 40, 10))
        for row, n, L, wdt in rows:
            span = s + 26 - row * 16
            for i in range(n):
                t = i / float(n - 1)
                x = CX - span + 2 * span * t + lean
                y = 160 + row * 2 + 10 * math.sin(t * math.pi)
                ang = math.pi / 2 + (0.5 - t) * 1.6
                col = fe if (i + row) % 2 == 0 else light(fe, 0.12)
                _leaf(ctx, x, y, ang, L, wdt, col, lw=3, vein=False)
                stroke(ctx, lambda c, x=x, y=y, ang=ang, L=L: (c.move_to(x + math.cos(ang) * L * 0.2, y + math.sin(ang) * L * 0.2),
                                                             c.line_to(x + math.cos(ang) * L * 0.7, y + math.sin(ang) * L * 0.7)),
                       sheen, 1.8, 0.6)


def nat_back_items(ctx, spec, pose, lean):
    evo = spec.get("_evo")
    if spec["outfit"] == "alchemist_coat" and evo == "B":
        # swirling purple miasma behind the alchemist
        _cloud(ctx, [(CX - 96, 210, 30), (CX - 70, 168, 26), (CX - 92, 252, 26), (CX + 96, 200, 30), (CX + 74, 160, 24),
                     (CX + 98, 246, 26), (CX - 40, 120, 22), (CX + 46, 112, 22), (CX, 96, 26)], MIASMA, alpha=0.55, lw=2.5,
               hi_col=light(MIASMA, 0.5))
        for k in range(3):
            r = 92 + k * 14
            stroke(ctx, lambda c, r=r, k=k: c.arc(CX, 196, r, math.pi * (0.8 + k * 0.3), math.pi * (1.5 + k * 0.3)), light(MIASMA, 0.4), 4, 0.7)
    elif spec["outfit"] == "plague_robe" and evo == "A":
        _cloud(ctx, [(CX - 90, 150, 30), (CX - 104, 200, 26), (CX + 92, 136, 28), (CX + 102, 186, 24), (CX - 60, 104, 24), (CX + 64, 96, 24)],
               hex2rgb("#5a6a2a"), alpha=0.5, lw=2.5)
    elif spec["outfit"] == "plague_robe" and evo == "B":
        glow(ctx, CX, 150, 140, hex2rgb("#e8ffd0"), 0.45)


def nat_front_fx(ctx, spec, pose):
    if spec["head"] in W3_HEADS:
        return w3_front_fx(ctx, spec, pose)
    if spec["head"] not in NAT_HEADS:
        return
    evo = spec.get("_evo")
    ec, ec2 = ELEMENT[spec["element"]]
    cast = pose == "cast"
    if spec["head"] == "leaf_crown" and evo == "B":
        # glowing spores floating around the healer
        for (x, y, r) in ((58, 116, 7), (40, 182, 5), (70, 250, 6), (272, 158, 5), (286, 236, 7), (96, 54, 5), (258, 262, 4),
                          (34, 226, 4)):
            glow(ctx, x, y, r * 3.6, ec2, 0.6)
            paint(ctx, lambda c, x=x, y=y, r=r: ellipse_path(c, x, y, r, r), light(ec2, 0.4), lw=2.5, hi=False, shade_amt=0)
    elif spec["head"] == "leaf_crown" and evo == "A":
        for (x, y, a) in ((54, 98, 0.6), (40, 200, -0.4), (284, 186, 2.6)):
            _leaf(ctx, x, y, a, 20, 7, LEAF_LIGHT, lw=2.5)
    elif spec["head"] == "alchemist_goggles" and evo == "B":
        _cloud(ctx, [(CX - 70, 284, 18), (CX - 36, 290, 16), (CX + 40, 290, 16), (CX + 74, 282, 18)], MIASMA, alpha=0.5, lw=2)
        for (x, y) in ((CX - 108, 120), (CX + 104, 132), (CX - 112, 214)):
            stroke(ctx, lambda c, x=x, y=y: smooth_open(c, [(x - 10, y + 6), (x, y - 6), (x + 10, y), (x + 4, y + 8), (x - 2, y + 2)]),
                   light(MIASMA, 0.3), 3.5, 0.85)
    elif spec["head"] == "plague_beak" and evo == "B":
        for (x, y, r) in ((60, 110, 8), (264, 100, 6), (48, 196, 6)):
            sparkle(ctx, x, y, r, hex2rgb("#f4ffe0"))


# ---------------------------------------------------------------------------- heads

def nat_hair_back(ctx, spec):
    hair = hex2rgb(spec["hair"])
    h, evo = spec["head"], spec.get("_evo")
    ec, ec2 = ELEMENT[spec["element"]]
    if h == "leaf_crown":
        paint(ctx, lambda c: smooth_closed(c, [(CX - 58, 96), (CX + 58, 96), (CX + 68, 160), (CX + 76, 214), (CX + 50, 204),
                                                 (CX + 28, 184), (CX - 28, 184), (CX - 50, 206), (CX - 78, 214), (CX - 68, 160)], 0.5),
              hair, lw=LW)
        if evo == "A":
            # antler-like branches rising from the crown
            for side in (-1, 1):
                main_b = [(CX + side * 30, 78), (CX + side * 50, 54), (CX + side * 58, 28)]
                outlined_line(ctx, main_b, DARK_WOOD, 9, 16)
                for (a, b) in (((CX + side * 46, 60), (CX + side * 82, 48)), ((CX + side * 54, 40), (CX + side * 80, 24)),
                               ((CX + side * 40, 66), (CX + side * 30, 40))):
                    outlined_line(ctx, [a, b], DARK_WOOD, 6, 12, smooth=False)
                _leaf(ctx, CX + side * 82, 48, -math.pi / 2 + side * 1.1, 20, 7, LEAF_LIGHT, lw=2.5, vein=False)
                _blossom(ctx, CX + side * 80, 24, 9, hex2rgb("#ff9cc6"), ec2, 0.6)
                _blossom(ctx, CX + side * 58, 28, 7, hex2rgb("#ff9cc6"), ec2, 0.5)
    elif h == "antler_helm":
        big = 1.25 if evo == "A" else 1.0
        for side in (-1, 1):
            base = (CX + side * 40, 72)
            tip = (CX + side * 82 * big, 12 if big == 1.0 else 18)
            mid = (CX + side * 64 * big, 46)
            outlined_line(ctx, [base, mid, tip], PALE_WOOD, 11, 18)
            for (a, b) in (((CX + side * 56 * big, 54), (CX + side * 52 * big, 18)),
                           ((CX + side * 72 * big, 32), (CX + side * 104 * min(big, 1.12), 22))):
                outlined_line(ctx, [a, b], PALE_WOOD, 8, 14, smooth=False)
            _leaf(ctx, CX + side * 52 * big, 22, -math.pi / 2 - side * 0.5, 18, 7, LEAF_LIGHT, lw=2.5, vein=False)
            _leaf(ctx, mid[0], mid[1], -math.pi / 2 + side * 1.2, 20, 7, LEAF, lw=2.5, vein=False)
    elif h == "alchemist_goggles":
        paint(ctx, lambda c: smooth_closed(c, [(CX - 62, 92), (CX + 62, 92), (CX + 70, 150), (CX + 52, 160), (CX - 52, 160),
                                                 (CX - 70, 150)], 0.5), shade(hair, 0.15), lw=LW)
    elif h == "plague_beak":
        hood = shade(hex2rgb(spec.get("hat", "#24212c")), 0.1)
        paint(ctx, lambda c: smooth_closed(c, [(CX - 68, 162), (CX - 74, 100), (CX - 54, 64), (CX, 56), (CX + 54, 64),
                                                 (CX + 74, 100), (CX + 68, 162), (CX, 170)], 0.5), hood, lw=LW)


def nat_hair_front(ctx, spec):
    hair = hex2rgb(spec["hair"])
    main, second, trim = hex2rgb(spec["main"]), hex2rgb(spec["second"]), hex2rgb(spec["trim"])
    h, evo, pose = spec["head"], spec.get("_evo"), spec.get("_pose")
    ec, ec2 = ELEMENT[spec["element"]]
    downed = pose == "downed"
    if h == "leaf_crown":
        pts = [(CX - 62, 124), (CX - 60, 80), (CX - 30, 56), (CX + 10, 52), (CX + 48, 62), (CX + 64, 92), (CX + 64, 126),
               (CX + 50, 100), (CX + 34, 84), (CX + 10, 96), (CX - 12, 82), (CX - 40, 96)]
        paint(ctx, lambda c: smooth_closed(c, pts, 0.45), hair, lw=LW)
        if evo == "B":
            # mushroom-cap hat with glowing spots
            cap = hex2rgb("#c8553d")
            glow(ctx, CX, 70, 110, ec2, 0.35)
            paint(ctx, lambda c: smooth_closed(c, [(CX - 88, 86), (CX - 74, 46), (CX - 34, 18), (CX + 34, 18), (CX + 74, 46),
                                                     (CX + 88, 86), (CX + 44, 94), (CX, 96), (CX - 44, 94)], 0.5), cap, lw=LW, hi_size=0.6)
            stroke(ctx, lambda c: smooth_open(c, [(CX - 80, 86), (CX - 40, 92), (CX, 93), (CX + 40, 92), (CX + 80, 86)]), hex2rgb("#f4e6c8"), 4)
            for (x, y, r) in ((CX - 46, 50, 10), (CX + 6, 34, 12), (CX + 52, 56, 9), (CX - 14, 70, 7), (CX + 30, 76, 6), (CX - 66, 74, 6)):
                glow(ctx, x, y, r * 2.4, ec2, 0.5)
                paint(ctx, lambda c, x=x, y=y, r=r: ellipse_path(c, x, y, r, r * 0.85), light(ec2, 0.55), lw=2.5, hi=False, shade_amt=0)
            _leaf(ctx, CX + 70, 82, 0.5, 22, 8, LEAF_LIGHT, lw=2.5)
        else:
            n = 11
            for i in range(n):
                t = i / float(n - 1)
                x = CX - 62 + 124 * t
                y = 92 - 22 * math.sin(math.pi * t)
                ang = -math.pi / 2 + (t - 0.5) * 2.2
                _leaf(ctx, x, y, ang, 28 if i % 2 else 22, 9, LEAF if i % 2 else LEAF_LIGHT, lw=3)
            stroke(ctx, lambda c: smooth_open(c, [(CX - 62, 94), (CX - 30, 76), (CX, 70), (CX + 30, 76), (CX + 62, 94)]), INK, 8)
            stroke(ctx, lambda c: smooth_open(c, [(CX - 62, 94), (CX - 30, 76), (CX, 70), (CX + 30, 76), (CX + 62, 94)]), DARK_WOOD, 4)
            big = evo == "A"
            for (x, y, r) in ((CX - 38, 80, 8), (CX, 70, 11), (CX + 38, 80, 8)):
                _blossom(ctx, x, y, r * (1.3 if big else 1.0), trim if not big else hex2rgb("#ff9cc6"), ec2 if big else None, 0.6)
    elif h == "antler_helm":
        beard = hair
        # mossy beard first (covers mouth), then the bark helm
        paint(ctx, lambda c: smooth_closed(c, [(CX - 50, 126), (CX - 40, 156), (CX - 20, 176), (CX, 184), (CX + 20, 176),
                                                 (CX + 40, 156), (CX + 50, 126), (CX + 30, 138), (CX, 140), (CX - 30, 138)], 0.45),
              beard, lw=LW - 1, hi_pos=(-0.2, 0.1))
        for (x, y) in ((CX - 24, 156), (CX + 8, 166), (CX + 28, 150)):
            _leaf(ctx, x, y, math.pi / 2 + (0.3 if x > CX else -0.3), 14, 5, LEAF_LIGHT, lw=2, vein=False)
        stroke(ctx, lambda c: smooth_open(c, [(CX - 8, 146), (CX, 150), (CX + 8, 146)]), INK, 3)
        helm = hex2rgb(spec["main"])
        paint(ctx, lambda c: smooth_closed(c, [(CX - 68, 134), (CX - 66, 72), (CX - 30, 46), (CX + 30, 46), (CX + 66, 72),
                                                 (CX + 68, 134), (CX + 50, 120), (CX + 46, 96), (CX, 88), (CX - 46, 96),
                                                 (CX - 50, 120)], 0.4), helm, lw=LW, hi_size=0.7)
        for (a, b) in (((CX - 36, 56), (CX - 42, 86)), ((CX - 8, 50), (CX - 6, 84)), ((CX + 24, 52), (CX + 30, 84))):
            stroke(ctx, lambda c, a=a, b=b: smooth_open(c, [a, ((a[0] + b[0]) / 2 + 3, (a[1] + b[1]) / 2), b]), shade(helm, 0.45), 3)
        # moss band on the brim with a glowing seed gem
        _cloud(ctx, [(CX - 50, 96, 9), (CX - 30, 90, 10), (CX - 8, 88, 9), (CX + 14, 88, 10), (CX + 36, 92, 9), (CX + 54, 98, 8)],
               second, lw=2.5, hi_col=light(second, 0.4))
        glow(ctx, CX, 74, 22, ec2, 0.7)
        paint(ctx, lambda c: smooth_closed(c, [(CX, 60), (CX + 9, 74), (CX, 86), (CX - 9, 74)], 0.4), trim, lw=3, hi_size=0.6)
    elif h == "alchemist_goggles":
        # swept silver hair with one long lock, goggles worn over the eyes
        pts = [(CX - 62, 118), (CX - 66, 80), (CX - 40, 54), (CX - 4, 46), (CX + 34, 50), (CX + 62, 70), (CX + 78, 96),
               (CX + 66, 98), (CX + 64, 120), (CX + 50, 92), (CX + 22, 84), (CX - 4, 92), (CX - 26, 82), (CX - 46, 100)]
        paint(ctx, lambda c: smooth_closed(c, pts, 0.4), hair, lw=LW, hi_pos=(-0.25, -0.3))
        stroke(ctx, lambda c: smooth_open(c, [(CX - 44, 64), (CX - 10, 56), (CX + 30, 64)]), hex2rgb("#a8e030"), 4, 0.9)
        stroke(ctx, lambda c: smooth_open(c, [(CX - 62, 118), (CX, 112), (CX + 62, 118)]), INK, 12)
        stroke(ctx, lambda c: smooth_open(c, [(CX - 62, 118), (CX, 112), (CX + 62, 118)]), hex2rgb("#4a3a30"), 6)
        for side in (-1, 1):
            x, y = CX + side * 20, 116
            paint(ctx, lambda c, x=x: ellipse_path(c, x, y, 18, 16), hex2rgb("#5a5866"), lw=4.5, hi_size=0.6)
            lens = ec if not downed else grey(ec, 0.9)
            if not downed:
                glow(ctx, x, y, 22, ec, 0.5)
            paint(ctx, lambda c, x=x, lens=lens: ellipse_path(c, x, y, 11, 10), lens, lw=3, hi=False, shade_amt=0.25)
            if downed:
                stroke(ctx, lambda c, x=x: (c.move_to(x - 5, y - 5), c.line_to(x + 5, y + 5), c.move_to(x + 5, y - 5), c.line_to(x - 5, y + 5)), INK, 3)
            else:
                flat(ctx, lambda c, x=x: ellipse_path(c, x - 4, y - 4, 3.5, 3), (1, 1, 1))
        if evo == "B":
            mask = hex2rgb("#3a3448")
            paint(ctx, lambda c: smooth_closed(c, [(CX - 34, 134), (CX + 34, 134), (CX + 38, 152), (CX + 20, 168), (CX - 20, 168),
                                                     (CX - 38, 152)], 0.45), mask, lw=LW - 1, hi_size=0.5)
            for k in range(3):
                stroke(ctx, lambda c, k=k: (c.move_to(CX - 10, 146 + k * 6), c.line_to(CX + 10, 146 + k * 6)), light(mask, 0.35), 2.5)
            for side in (-1, 1):
                paint(ctx, lambda c, side=side: ellipse_path(c, CX + side * 38, 156, 12, 12), MIASMA, lw=3.5, hi_size=0.6)
                flat(ctx, lambda c, side=side: ellipse_path(c, CX + side * 38, 156, 5, 5), shade(MIASMA, 0.5))
    elif h == "plague_beak":
        mask = hex2rgb(spec.get("mask", "#ece0c4"))
        hat = hex2rgb(spec.get("hat", "#24212c"))
        paint(ctx, lambda c: smooth_closed(c, [(CX - 54, 98), (CX + 54, 98), (CX + 56, 132), (CX + 40, 158), (CX, 166),
                                                 (CX - 40, 158), (CX - 56, 132)], 0.45), mask, lw=LW - 1, hi_size=0.5)
        # beak curving down and to the right
        beak = [(CX - 16, 128), (CX + 16, 124), (CX + 34, 150), (CX + 50, 186), (CX + 44, 190), (CX + 20, 166), (CX - 6, 150)]
        paint(ctx, lambda c: smooth_closed(c, beak, 0.45), mask, lw=LW - 1, hi_pos=(-0.3, -0.3))
        stroke(ctx, lambda c: smooth_open(c, [(CX - 2, 138), (CX + 22, 152), (CX + 40, 180)]), shade(mask, 0.4), 2.5)
        for (x, y) in ((CX + 4, 134), (CX + 12, 132)):
            flat(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 2, 2), INK)
        if evo == "B":
            _cross(ctx, CX + 18, 150, 9, hex2rgb("#5fe05a"))
        for side in (-1, 1):
            x, y = CX + side * 22, 114
            paint(ctx, lambda c, x=x: ellipse_path(c, x, y, 15, 15), hex2rgb("#6a5a3a") if evo != "B" else hex2rgb("#c8d0c0"), lw=4, hi=False)
            if downed:
                paint(ctx, lambda c, x=x: ellipse_path(c, x, y, 9, 9), grey(ec, 0.9), lw=2.5, hi=False)
                stroke(ctx, lambda c, x=x: (c.move_to(x - 5, y - 5), c.line_to(x + 5, y + 5), c.move_to(x + 5, y - 5), c.line_to(x - 5, y + 5)), INK, 3)
            else:
                lens = ec if evo != "B" else hex2rgb("#bff7a0")
                glow(ctx, x, y, 20, lens, 0.55)
                paint(ctx, lambda c, x=x, lens=lens: ellipse_path(c, x, y, 9, 9), lens, lw=2.5, hi=False, shade_amt=0.2)
                flat(ctx, lambda c, x=x: ellipse_path(c, x - 3, y - 3, 3, 2.6), (1, 1, 1))
        # wide-brimmed hat
        paint(ctx, lambda c: smooth_closed(c, [(CX - 92, 88), (CX - 70, 72), (CX, 66), (CX + 70, 72), (CX + 92, 88), (CX + 60, 98),
                                                 (CX, 100), (CX - 60, 98)], 0.5), hat, lw=LW, hi=False)
        paint(ctx, lambda c: smooth_closed(c, [(CX - 46, 86), (CX - 42, 30), (CX - 30, 18), (CX + 30, 18), (CX + 42, 30), (CX + 46, 86),
                                                 (CX, 92)], 0.3), light(hat, 0.06), lw=LW, hi_size=0.5)
        band = trim if evo != "B" else hex2rgb("#6fbf4a")
        paint(ctx, lambda c: smooth_closed(c, [(CX - 45, 68), (CX + 45, 68), (CX + 46, 84), (CX, 90), (CX - 46, 84)], 0.3), band, lw=3.5, hi=False)
        if evo == "A":
            # crow feather tucked in the band
            _leaf(ctx, CX + 34, 74, -1.1, 50, 9, hex2rgb("#3a2a4a"), lw=3, vein=True)


# ---------------------------------------------------------------------------- props

def _censer(ctx, x, y, r, spec, chain_from=None, light_mode=False):
    ec, ec2 = ELEMENT[spec["element"]]
    metal = BRASS if spec.get("_evo") != "A" else hex2rgb("#6a6470")
    if chain_from:
        stroke(ctx, lambda c: (c.move_to(*chain_from), c.line_to(x, y - r - 4)), INK, 5)
        stroke(ctx, lambda c: (c.move_to(*chain_from), c.line_to(x, y - r - 4)), hex2rgb("#c9c3b0"), 2)
    glow(ctx, x, y, r * 2.6, ec if not light_mode else hex2rgb("#f4ffe0"), 0.55)
    paint(ctx, lambda c: ellipse_path(c, x, y, r, r * 0.95), metal, lw=4, hi_size=0.6)
    for dx in (-r * 0.45, 0, r * 0.45):
        flat(ctx, lambda c, dx=dx: rrect_path(c, x + dx - 2, y - r * 0.5, 4, r, 2), ec if not light_mode else hex2rgb("#f4ffe0"))
    paint(ctx, lambda c: smooth_closed(c, [(x - r * 0.8, y - r * 0.55), (x, y - r * 1.4), (x + r * 0.8, y - r * 0.55)], 0.5), metal, lw=3.5, hi=False)
    paint(ctx, lambda c: ellipse_path(c, x, y + r + 2, r * 0.3, r * 0.3), metal, lw=2.5, hi=False)


def _smoke_trail(ctx, pts, col, alpha=0.8, r0=10, grow=2.5):
    blobs = [(x, y, r0 + i * grow) for i, (x, y) in enumerate(pts)]
    _cloud(ctx, blobs, col, alpha=alpha, lw=2.5, hi_col=light(col, 0.45))


def nat_prop(ctx, spec, hand, pose, element):
    kind, evo = spec["prop"], spec.get("_evo")
    ec, ec2 = ELEMENT[element]
    hx, hy = hand
    lh, rh = hands_for(spec, pose)
    trim = hex2rgb(spec["trim"])
    cast = pose == "cast"
    if kind == "blossom_staff":
        reach = 150 if not cast else 62
        tx, ty = hx + 10, hy - reach
        bx, by = hx - 4, hy + 40
        shaft = []
        for i in range(6):
            t = i / 5.0
            wob = (6 if i % 2 else -5) if 0 < i < 5 else 0
            shaft.append((bx + (tx - bx) * t + wob, by + (ty - by) * t))
        outlined_line(ctx, shaft, DARK_WOOD, 10, 17)
        for (a, b) in (((bx + (tx - bx) * 0.55 + 4, by + (ty - by) * 0.55), (bx + (tx - bx) * 0.55 + 18, by + (ty - by) * 0.55 - 14)),):
            outlined_line(ctx, [a, b], DARK_WOOD, 5, 10, smooth=False)
            _leaf(ctx, b[0], b[1], -0.6, 16, 6, LEAF_LIGHT, lw=2.5, vein=False)
        glow(ctx, tx, ty - 14, 46 if cast else 44, ec2, 0.75 if cast else 0.5)
        # curled crook
        outlined_line(ctx, [(tx, ty), (tx - 16, ty - 16), (tx - 10, ty - 34), (tx + 6, ty - 36), (tx + 12, ty - 24)], DARK_WOOD, 8, 15)
        outlined_line(ctx, [(tx, ty), (tx + 16, ty - 8), (tx + 22, ty - 22)], DARK_WOOD, 6, 12)
        for (x, y, a) in ((tx - 20, ty - 4, 2.6), (tx + 22, ty - 4, 0.2)):
            _leaf(ctx, x, y, a, 18, 7, LEAF, lw=2.5)
        r = 9 if evo != "A" else 14
        for (x, y, rr) in ((tx - 2, ty - 28, r + 2), (tx + 22, ty - 24, r), (tx - 20, ty - 18, r - 1)):
            _blossom(ctx, x, y, rr, hex2rgb("#ff9cc6"), ec2 if (cast or evo == "A") else None, 0.7, 2.2 if cast else 3.2)
        if evo == "B":
            _mushroom(ctx, tx - 8, ty + 26, 9, hex2rgb("#c8553d"), glow_col=ec2)
        if cast:
            for (x, y, a) in ((tx - 40, ty - 30, 0.4), (tx + 36, ty - 36, 1.2), (tx - 30, ty - 44, 2.2), (tx + 40, ty - 12, 2.8)):
                paint(ctx, lambda c, x=x, y=y, a=a: ellipse_path(c, x, y, 6, 3.5, a), hex2rgb("#ffc2dc"), lw=2, hi=False, shade_amt=0)
            sparkle(ctx, tx + 32, ty - 18, 10, light(ec2, 0.4))
    elif kind in ("thorn_shield", "thorn_tower"):
        # wooden thorn sword in the right hand
        ang = -1.3 if not cast else -0.95
        L = 92
        tip = (hx + math.cos(ang) * L, hy + math.sin(ang) * L)
        nx, ny = -math.sin(ang), math.cos(ang)
        b = (hx + math.cos(ang) * 16, hy + math.sin(ang) * 16)
        if cast:
            glow(ctx, (b[0] + tip[0]) / 2, (b[1] + tip[1]) / 2, 56, ec2, 0.6)
        for t in (0.35, 0.6, 0.82):
            px, py = b[0] + (tip[0] - b[0]) * t, b[1] + (tip[1] - b[1]) * t
            _thorn(ctx, px + nx * 8, py + ny * 8, ang + 0.9, 12, PALE_WOOD)
        blade = [(b[0] + nx * 9, b[1] + ny * 9), (tip[0] - math.cos(ang) * 18 + nx * 7, tip[1] - math.sin(ang) * 18 + ny * 7), tip,
                 (tip[0] - math.cos(ang) * 18 - nx * 7, tip[1] - math.sin(ang) * 18 - ny * 7), (b[0] - nx * 9, b[1] - ny * 9)]
        paint(ctx, lambda c: poly_path(c, blade), hex2rgb("#c8a070"), lw=4.5, hi_size=0.6)
        stroke(ctx, lambda c: (c.move_to(*b), c.line_to(*tip)), ec, 3)
        outlined_line(ctx, [(b[0] + nx * 18, b[1] + ny * 18), (b[0] - nx * 18, b[1] - ny * 18)], hex2rgb("#3f7a2a"), 8, 15, smooth=False)
        if kind == "thorn_shield":
            sx, sy = (lh[0] + 4, lh[1] - 24) if not cast else (lh[0] + 6, lh[1] - 36)
            rx, ry = 42, 50
            for k in range(12):
                a = k * 2 * math.pi / 12 + 0.26
                _thorn(ctx, sx + math.cos(a) * (rx - 2), sy + math.sin(a) * (ry - 2), a, 14, PALE_WOOD)
            paint(ctx, lambda c: ellipse_path(c, sx, sy, rx, ry), hex2rgb("#8a5a34"), lw=LW, hi_size=0.7)
            ctx.save()
            ctx.new_path()
            ellipse_path(ctx, sx, sy, rx, ry)
            ctx.clip()
            for dx in (-20, 0, 20):
                stroke(ctx, lambda c, dx=dx: (c.move_to(sx + dx, sy - ry), c.line_to(sx + dx, sy + ry)), shade(hex2rgb("#8a5a34"), 0.45), 3)
            ctx.restore()
            stroke(ctx, lambda c: ellipse_path(c, sx, sy, rx - 7, ry - 7), INK, 9)
            stroke(ctx, lambda c: ellipse_path(c, sx, sy, rx - 7, ry - 7), hex2rgb("#3f9a3a"), 5)
            if cast:
                glow(ctx, sx, sy, 56, ec2, 0.7)
            glow(ctx, sx, sy, 26, ec2, 0.6)
            _leaf(ctx, sx, sy + 16, -math.pi / 2, 34, 13, LEAF_LIGHT, lw=3.5)
        else:
            # Bramble Fortress: huge bark tower shield bristling with thorns
            sx, sy = (lh[0] + 6, lh[1] - 40) if not cast else (lh[0] + 30, lh[1] - 4)
            w2, top, bot = 50, sy - 92, sy + 78
            body = [(sx - w2, top + 26), (sx - w2 + 14, top + 4), (sx, top - 6), (sx + w2 - 14, top + 4), (sx + w2, top + 26),
                    (sx + w2, bot - 18), (sx, bot), (sx - w2, bot - 18)]
            for side in (-1, 1):
                for k in range(5):
                    y = top + 30 + k * 30
                    _thorn(ctx, sx + side * (w2 - 2), y, math.pi / 2 - side * math.pi / 2 + side * -0.25, 16, PALE_WOOD)
            glow(ctx, sx, sy, 110, ec2, 0.35 if not cast else 0.65)
            paint(ctx, lambda c: smooth_closed(c, body, 0.25), hex2rgb("#7a5030"), lw=LW, hi_size=0.7)
            ctx.save()
            ctx.new_path()
            smooth_closed(ctx, body, 0.25)
            ctx.clip()
            for dx in (-25, 0, 25):
                stroke(ctx, lambda c, dx=dx: (c.move_to(sx + dx, top), c.line_to(sx + dx + 2, bot)), shade(hex2rgb("#7a5030"), 0.45), 3)
            for y in (top + 30, bot - 34):
                _cloud(ctx, [(sx - 40 + i * 16, y + (i % 2) * 4, 9) for i in range(6)], hex2rgb("#4f8a3a"), lw=2)
            ctx.restore()
            glow(ctx, sx, sy - 6, 34, ec2, 0.7)
            _leaf(ctx, sx, sy + 18, -math.pi / 2, 44, 16, LEAF_LIGHT, lw=3.5)
            for (x, y) in ((sx - 26, top + 54), (sx + 24, top + 60), (sx + 18, bot - 26)):
                _thorn(ctx, x, y, -1.2, 12, PALE_WOOD)
    elif kind == "thorn_whip":
        if not cast:
            pts = [(hx, hy), (hx + 30, hy - 26), (hx + 52, hy - 78), (hx + 36, hy - 130), (hx - 2, hy - 150), (hx + 10, hy - 168)]
        else:
            pts = [(hx, hy), (hx + 30, hy - 26), (hx + 36, hy - 66), (hx + 4, hy - 92), (hx - 44, hy - 90), (hx - 70, hy - 76)]
        glow(ctx, pts[-1][0], pts[-1][1], 36 if cast else 30, ec2, 0.7 if cast else 0.45)
        outlined_line(ctx, pts, hex2rgb("#3f7a2a"), 9, 16)
        # thorns along the lash
        for i in range(1, len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            a = math.atan2(y1 - y0, x1 - x0)
            for t in (0.3, 0.75):
                px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                _thorn(ctx, px, py, a + (1.5 if (i + int(t * 4)) % 2 else -1.5), 11, PALE_WOOD, lw=2)
        _leaf(ctx, pts[-1][0], pts[-1][1], math.atan2(pts[-1][1] - pts[-2][1], pts[-1][0] - pts[-2][0]), 22, 8, LEAF_LIGHT, lw=3)
        outlined_line(ctx, [(hx - 4, hy + 14), (hx + 4, hy - 10)], DARK_WOOD, 9, 16, smooth=False)
        if cast:
            sparkle(ctx, pts[-1][0] - 10, pts[-1][1] - 18, 12, light(ec2, 0.4))
            for k in range(2):
                stroke(ctx, lambda c, k=k: c.arc(hx - 10, hy - 30, 56 + k * 12, -math.pi * 0.95, -math.pi * 0.6), ec2, 4 - k, 0.8)
    elif kind == "flask":
        liquid = {None: ec, "A": hex2rgb("#ff9a2a"), "B": MIASMA}[evo]
        if not cast:
            fx, fy = hx + 4, hy + 16
        else:
            fx, fy = hx + 6, hy - 6
        r = 18
        glow(ctx, fx, fy, 50, liquid, 0.55 if not cast else 0.8)
        neck_top = fy - r - 22
        paint(ctx, lambda c: rrect_path(c, fx - 6, neck_top, 12, 26, 4), GLASS, lw=3.5, hi=False, shade_amt=0.1)
        paint(ctx, lambda c: ellipse_path(c, fx, fy, r, r), GLASS, lw=4, hi=False, shade_amt=0.1)
        ctx.save()
        ctx.new_path()
        ellipse_path(ctx, fx, fy, r - 2, r - 2)
        ctx.clip()
        flat(ctx, lambda c: rrect_path(c, fx - r, fy - 3, 2 * r, r + 4, 2), liquid)
        flat(ctx, lambda c: rrect_path(c, fx - r, fy - 3, 2 * r, 4, 2), light(liquid, 0.4))
        ctx.restore()
        flat(ctx, lambda c: ellipse_path(c, fx - 7, fy - 8, 4, 6, 0.5), (1, 1, 1), 0.85)
        for (bx, by, br) in ((fx + 5, fy + 6, 3), (fx - 4, fy + 10, 2.2)):
            stroke(ctx, lambda c, bx=bx, by=by, br=br: ellipse_path(c, bx, by, br, br), (1, 1, 1), 1.8, 0.9)
        if not cast:
            paint(ctx, lambda c: rrect_path(c, fx - 7, neck_top - 8, 14, 10, 3), hex2rgb("#a8743a"), lw=3, hi=False)
        if cast or evo is not None:
            # bubbling over / splashing out of the neck
            if cast:
                splash = [(fx - 14, neck_top - 12, 8), (fx + 10, neck_top - 20, 9), (fx - 4, neck_top - 34, 10), (fx + 16, neck_top - 44, 7)]
                _cloud(ctx, splash, liquid, lw=2.5, hi_col=light(liquid, 0.5))
                for (bx, by, br) in ((fx - 24, neck_top - 46, 5), (fx + 28, neck_top - 56, 4), (fx - 4, neck_top - 60, 6)):
                    stroke(ctx, lambda c, bx=bx, by=by, br=br: ellipse_path(c, bx, by, br, br), INK, 5)
                    stroke(ctx, lambda c, bx=bx, by=by, br=br: ellipse_path(c, bx, by, br, br), light(liquid, 0.4), 2.5)
        if evo == "A":
            # unstable: smoke and sparks
            if cast:
                trail = [(fx + 26, fy - 4), (fx + 34, fy - 26), (fx + 30, fy - 50)]
            else:
                trail = [(fx + 4, neck_top - 10), (fx + 16, neck_top - 28), (fx + 6, neck_top - 48)]
            _smoke_trail(ctx, trail, SMOKE, alpha=0.75, r0=9, grow=3)
            for (sx_, sy_, sr) in ((fx - 22, fy - 10, 9), (fx + 24, fy - 26, 7), (fx - 12, neck_top - 4, 6)):
                sparkle(ctx, sx_, sy_, sr, hex2rgb("#ffe36a"))
        elif evo == "B" and not cast:
            _smoke_trail(ctx, [(fx + 2, neck_top - 16), (fx + 14, neck_top - 32)], MIASMA, alpha=0.6, r0=8, grow=3)
    elif kind == "censer":
        light_mode = evo == "B"
        smoke = {None: ec, "A": hex2rgb("#6a8a2a"), "B": hex2rgb("#e4ffd0")}[evo]
        hands = [(hx, hy, 1)]
        if evo == "A":
            hands.append((lh[0], lh[1], -1))
        for (px, py, side) in hands:
            if not cast:
                cx_, cy_ = px + side * 4, py + 40
                trail = [(cx_ + side * 14, cy_ - 22), (cx_ + side * 30, cy_ - 52), (cx_ + side * 22, cy_ - 88), (cx_ + side * 38, cy_ - 124)]
            else:
                cx_, cy_ = px + side * 30, py - 22
                trail = [(cx_ + side * 6, cy_ + 26), (cx_ + side * 16, cy_ + 54), (cx_ + side * 8, cy_ + 84), (cx_ + side * 20, cy_ + 114)]
            if evo == "A":
                trail = trail + [(trail[-1][0] - side * 6, trail[-1][1] - 30)] if not cast else trail
            _smoke_trail(ctx, trail, smoke, alpha=0.8 if not light_mode else 0.85, r0=9, grow=3)
            _censer(ctx, cx_, cy_, 15, spec, chain_from=(px, py), light_mode=light_mode)
            if cast:
                sparkle(ctx, cx_ + side * 6, cy_ - 26, 9, light(smoke, 0.4))


# ============================================================================ wave-3 parts
# Heroes caelis (Echo Savant), oriane (Rune Conductor), zerith (Rift Binder), maelis (Void Sentinel), solenne
# (Ember Scribe), mirel (River Shaper), veyra (Arcshot Ranger), isolde (Frostbreaker), aeris (Tempest Oracle),
# doran (Granite Fist), elowen (Sun Cantor) and morven (Gloom Sentinel). Same opt-in scheme as the nature &
# poison parts: the drawers read spec["_evo"] / spec["_pose"] and every evolution swaps gear or silhouette.
# Two more opt-in hooks are read by hero_sprite: "sleeve" ("skin" for bare arms, or a colour) and "fx_glow"
# (a light colour used instead of the element's secondary for the evo-B aura/emblem and the cast-hand glow,
# because the void and shadow secondaries are near-black).

W3_HEADS = ("mirror_circlet", "conductor_hat", "rift_hood", "void_helm", "scribe_beret", "shell_crown", "ranger_visor",
            "ice_braid", "oracle_veil", "stone_brow", "radiant_hair", "gloom_hood")
W3_OUTFITS = ("layered_robe", "tailcoat", "sigil_plate", "star_cloak", "obsidian_plate", "scribe_robe", "river_dress",
              "ranger_jacket", "frost_coat", "oracle_robe", "stone_gi", "cantor_robe", "tattered_mail")
W3_TORSO_SHAPES = ("layered_robe", "tailcoat", "star_cloak", "scribe_robe", "river_dress", "frost_coat", "oracle_robe",
                   "cantor_robe", "tattered_mail")
W3_PROPS = ("rune_book", "arcane_orbs", "baton", "long_baton", "rune_shield", "star_gauntlet", "void_daggers",
            "portal_shield", "null_bastion", "portal_glaive", "burning_quill", "burning_scroll", "ember_lantern",
            "water_ribbon", "flood_trident", "heal_orb", "arc_bow", "heavy_bow", "split_bow", "frost_lance",
            "glacier_gauntlet", "chime_staff", "wind_loom", "chain_talisman", "granite_fists", "boulder_shield",
            "fracture_fists", "songbook", "solar_lance", "gloom_glaive", "dread_shield", "soul_scythe")

SILVER = hex2rgb("#e2e8f4")
GOLD = hex2rgb("#ffd35a")
VOID_GLOW = hex2rgb("#8a7cff")
VOID_DARK = hex2rgb("#140c38")
PARCH = hex2rgb("#f6e9c8")
INKBLOT = hex2rgb("#2a2440")
BONE = hex2rgb("#ece4d0")
EMBER = hex2rgb("#ffc04a")
DARK_SHAFT = hex2rgb("#2a2030")


# ---------------------------------------------------------------------------- small helpers

def _c(spec, key, default):
    return hex2rgb(spec.get(key, default))


def _sc(ctx, pts, col, lw=LW, t=0.4, **kw):
    paint(ctx, lambda c: smooth_closed(c, pts, t), col, lw=lw, **kw)


def _pp(ctx, pts, col, lw=4.0, **kw):
    paint(ctx, lambda c: poly_path(c, pts), col, lw=lw, **kw)


def _el(ctx, x, y, rx, ry, col, lw=3.5, rot=0.0, **kw):
    paint(ctx, lambda c: ellipse_path(c, x, y, rx, ry, rot), col, lw=lw, **kw)


def _open(c, pts):
    c.move_to(*pts[0])
    for p in pts[1:]:
        c.line_to(*p)


def _dag(xr, xl, yb, depth, n):
    """Dagged / ragged hem running from right to left."""
    return [(xr + (xl - xr) * i / float(n), yb - (depth if i % 2 else 0)) for i in range(n + 1)]


def _arc_pts(cx, cy, rx, ry, rot, a0, a1, n=28):
    cr, sr = math.cos(rot), math.sin(rot)
    out = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / float(n)
        x, y = math.cos(a) * rx, math.sin(a) * ry
        out.append((cx + x * cr - y * sr, cy + x * sr + y * cr))
    return out


def _along(pts, u):
    """Point at fraction u along a polyline (by segment index)."""
    f = u * (len(pts) - 1)
    i = min(int(f), len(pts) - 2)
    t = f - i
    return (pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t)


def _glyph(ctx, x, y, r, col, k=0, lw=2.4, alpha=1.0):
    k %= 4
    if k == 0:
        def f(c):
            poly_path(c, [(x, y - r), (x + r * 0.7, y), (x, y + r), (x - r * 0.7, y)])
            c.move_to(x, y - r * 0.45)
            c.line_to(x, y + r * 0.45)
    elif k == 1:
        def f(c):
            poly_path(c, [(x, y - r), (x + r * 0.9, y + r * 0.7), (x - r * 0.9, y + r * 0.7)])
    elif k == 2:
        def f(c):
            c.move_to(x, y + r)
            c.line_to(x, y - r * 0.1)
            c.line_to(x - r * 0.75, y - r)
            c.move_to(x, y - r * 0.1)
            c.line_to(x + r * 0.75, y - r)
    else:
        def f(c):
            ellipse_path(c, x, y, r * 0.8, r * 0.8)
            c.move_to(x - r, y + r)
            c.line_to(x + r, y - r)
    stroke(ctx, f, col, lw, alpha)


def _ring_half(ctx, cx, cy, rx, ry, rot, col, front, w=5.0, glyph_col=None, n_glyph=5):
    a0, a1 = (0.0, math.pi) if front else (math.pi, 2 * math.pi)
    pts = _arc_pts(cx, cy, rx, ry, rot, a0, a1)
    stroke(ctx, lambda c: _open(c, pts), INK, w + 5)
    stroke(ctx, lambda c: _open(c, pts), col, w)
    stroke(ctx, lambda c: _open(c, pts), light(col, 0.55), w * 0.3)
    if glyph_col:
        for i in range(n_glyph):
            a = a0 + (a1 - a0) * (i + 0.5) / n_glyph
            x, y = _arc_pts(cx, cy, rx, ry, rot, a, a, 1)[0]
            _glyph(ctx, x, y, 5.5, INK, i + (0 if front else 2), 5)
            _glyph(ctx, x, y, 5.5, glyph_col, i + (0 if front else 2), 2.4)


def _ribbon(ctx, pts, col, inner, w=11.0):
    outlined_line(ctx, pts, col, w, w + 7)
    stroke(ctx, lambda c: smooth_open(c, pts), inner, w * 0.32, 0.9)


def _orb(ctx, x, y, r, col, core=(1, 1, 1), glow_a=0.7, glow_k=2.6):
    if glow_a:
        glow(ctx, x, y, r * glow_k, col, glow_a)
    _el(ctx, x, y, r, r, col, lw=3.5, hi_size=0.7, shade_amt=0.2)
    flat(ctx, lambda c: ellipse_path(c, x - r * 0.3, y - r * 0.3, r * 0.32, r * 0.32), core, 0.9)


def _drop(ctx, x, y, r, col):
    _sc(ctx, [(x, y - r * 1.7), (x + r * 0.95, y - r * 0.1), (x, y + r), (x - r * 0.95, y - r * 0.1)], col, lw=3, t=0.5, hi_size=0.6)


def _shard(ctx, x, y, ang, L, w, col, lw=3.0, sheen=None):
    ca, sa = math.cos(ang), math.sin(ang)
    nx, ny = -sa, ca
    pts = [(x - ca * L * 0.35, y - sa * L * 0.35), (x + nx * w, y + ny * w), (x + ca * L * 0.65, y + sa * L * 0.65), (x - nx * w, y - ny * w)]
    _pp(ctx, pts, col, lw=lw, hi_size=0.6, shade_amt=0.22)
    if sheen:
        stroke(ctx, lambda c: (c.move_to(x - ca * L * 0.12 + nx * w * 0.35, y - sa * L * 0.12 + ny * w * 0.35),
                               c.line_to(x + ca * L * 0.4 + nx * w * 0.1, y + sa * L * 0.4 + ny * w * 0.1)), sheen, 2.2, 0.9)


def _spike(ctx, bx, by, ang, L, w, col, lw=3.5):
    ca, sa = math.cos(ang), math.sin(ang)
    nx, ny = -sa, ca
    tip = (bx + ca * L, by + sa * L)
    _pp(ctx, [(bx + nx * w, by + ny * w), (bx + ca * L * 0.55 + nx * w * 0.75, by + sa * L * 0.55 + ny * w * 0.75), tip,
              (bx - nx * w, by - ny * w)], col, lw=lw, hi_size=0.6, shade_amt=0.25)
    stroke(ctx, lambda c: (c.move_to(bx + nx * w * 0.1, by + ny * w * 0.1), c.line_to(tip[0] - ca * 6, tip[1] - sa * 6)),
           light(col, 0.6), 2.2, 0.8)


def _portal(ctx, x, y, rx, ry, col, dark=VOID_DARK, rot=0.0, lw=4.0, spin=0.0, glow_a=0.55):
    if glow_a:
        glow(ctx, x, y, max(rx, ry) * 1.6, col, glow_a)
    _el(ctx, x, y, rx, ry, dark, lw=lw, rot=rot, hi=False, shade_amt=0)
    cr, sr = math.cos(rot), math.sin(rot)
    for k in range(3):
        pts = []
        for i in range(14):
            t = i / 13.0
            a = spin + k * 2 * math.pi / 3 + t * 3.4
            rr = 0.9 - 0.78 * t
            px, py = math.cos(a) * rx * rr, math.sin(a) * ry * rr
            pts.append((x + px * cr - py * sr, y + px * sr + py * cr))
        stroke(ctx, lambda c, pts=pts: smooth_open(c, pts), light(col, 0.25 * k), max(1.5, min(rx, ry) * 0.16))
    flat(ctx, lambda c: ellipse_path(c, x, y, rx * 0.2, ry * 0.2, rot), light(col, 0.7))


def _flame(ctx, x, y, h, w, col, core=None, bend=0.0, lw=3.0):
    pts = [(x - w, y - h * 0.05), (x - w * 0.75, y - h * 0.45), (x - w * 0.15 + bend * 0.5, y - h * 0.7), (x + bend, y - h),
           (x + w * 0.45 + bend * 0.4, y - h * 0.55), (x + w, y - h * 0.15), (x + w * 0.55, y + w * 0.35), (x - w * 0.5, y + w * 0.35)]
    _sc(ctx, pts, col, lw=lw, t=0.5, hi=False)
    if core:
        cy_ = y - h * 0.12
        inner = [(x + (px - x) * 0.5, cy_ + (py - cy_) * 0.55) for (px, py) in pts]
        flat(ctx, lambda c: smooth_closed(c, inner, 0.5), core, 0.95)


def _note(ctx, x, y, s, col):
    outlined_line(ctx, [(x + s * 0.5, y - 1), (x + s * 0.5, y - s * 1.7), (x + s * 1.2, y - s * 1.15)], col, 2.6, 6.5, smooth=False)
    _el(ctx, x, y, s * 0.62, s * 0.46, col, lw=2.5, rot=-0.4, hi=False, shade_amt=0.15)


def _gear(ctx, x, y, r, n, col, rot=0.0):
    pts = []
    for i in range(n * 4):
        a = rot + i * 2 * math.pi / (n * 4)
        rr = r if (i % 4) in (1, 2) else r * 0.76
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    _pp(ctx, pts, col, lw=3, hi=False, shade_amt=0.2)
    _el(ctx, x, y, r * 0.45, r * 0.45, shade(col, 0.25), lw=2.5, hi=False, shade_amt=0)
    flat(ctx, lambda c: ellipse_path(c, x, y, r * 0.18, r * 0.18), INK)


def _skull(ctx, x, y, r, col=BONE, eye=None):
    _sc(ctx, [(x - r, y - r * 0.1), (x - r * 0.85, y - r * 0.8), (x, y - r * 1.05), (x + r * 0.85, y - r * 0.8), (x + r, y - r * 0.1),
              (x + r * 0.6, y + r * 0.45), (x + r * 0.5, y + r * 0.9), (x - r * 0.5, y + r * 0.9), (x - r * 0.6, y + r * 0.45)],
        col, lw=3.0, t=0.45, hi=False, shade_amt=0.2)
    for s in (-1, 1):
        flat(ctx, lambda c, s=s: ellipse_path(c, x + s * r * 0.4, y - r * 0.05, r * 0.27, r * 0.3), INK)
        if eye:
            glow(ctx, x + s * r * 0.4, y - r * 0.05, r * 0.8, eye, 0.85)
            flat(ctx, lambda c, s=s: ellipse_path(c, x + s * r * 0.4, y - r * 0.05, r * 0.13, r * 0.15), light(eye, 0.5))
    flat(ctx, lambda c: poly_path(c, [(x, y + r * 0.25), (x + r * 0.12, y + r * 0.45), (x - r * 0.12, y + r * 0.45)]), INK)
    for k in (-1, 0, 1):
        stroke(ctx, lambda c, k=k: (c.move_to(x + k * r * 0.22, y + r * 0.62), c.line_to(x + k * r * 0.22, y + r * 0.88)), INK, 1.8)


def _wisp(ctx, x, y, r, col, ang=math.pi / 2):
    glow(ctx, x, y, r * 3.0, col, 0.55)
    tail = (x + math.cos(ang) * r * 2.8, y + math.sin(ang) * r * 2.8)
    pts = [(x + math.cos(ang + math.pi + d) * r, y + math.sin(ang + math.pi + d) * r) for d in (-1.7, -0.85, 0.0, 0.85, 1.7)]
    _sc(ctx, pts + [tail], light(col, 0.45), lw=2.5, t=0.5, hi=False, shade_amt=0.15)
    nx, ny = -math.sin(ang), math.cos(ang)
    for s in (-1, 1):
        flat(ctx, lambda c, s=s: ellipse_path(c, x + nx * s * r * 0.35 - math.cos(ang) * r * 0.2,
                                              y + ny * s * r * 0.35 - math.sin(ang) * r * 0.2, r * 0.16, r * 0.22), INK)


def _chain(ctx, a, b, col=hex2rgb("#a8a4b4"), r=4.5):
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / (r * 1.7)))
    for i in range(n):
        t = (i + 0.5) / n
        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        rx, ry = (r * 1.25, r * 0.75) if i % 2 == 0 else (r * 0.95, r * 0.32)
        stroke(ctx, lambda c, x=x, y=y, rx=rx, ry=ry: ellipse_path(c, x, y, rx, ry, ang), INK, 5.5)
        stroke(ctx, lambda c, x=x, y=y, rx=rx, ry=ry: ellipse_path(c, x, y, rx, ry, ang), col, 2.4)


def _shell(ctx, x, y, r, rot, col, lw=3.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    pts = [(0, r * 0.2)]
    n = 9
    for i in range(n):
        a = -math.pi + 0.3 + (math.pi - 0.6) * i / (n - 1)
        rr = r if i % 2 == 0 else r * 0.9
        pts.append((math.cos(a) * rr, math.sin(a) * rr * 0.9))
    _sc(ctx, pts, col, lw=lw, t=0.3, hi_size=0.6, shade_amt=0.18)
    for i in range(1, 5):
        a = -math.pi + 0.3 + (math.pi - 0.6) * i / 5.0
        stroke(ctx, lambda c, a=a: (c.move_to(0, r * 0.12), c.line_to(math.cos(a) * r * 0.8, math.sin(a) * r * 0.72)), shade(col, 0.35), 1.8)
    _el(ctx, 0, r * 0.25, r * 0.3, r * 0.16, col, lw=2.5, hi=False)
    ctx.restore()


def _sun(ctx, x, y, r, col, core=None, lw=2.5):
    paint(ctx, lambda c: star_path(c, x, y, r, r * 0.62, 8), col, lw=lw, hi=False, shade_amt=0.15)
    _el(ctx, x, y, r * 0.45, r * 0.45, core or light(col, 0.5), lw=2, hi=False, shade_amt=0)


def _blot(ctx, x, y, r):
    pts = [(x + math.cos(a) * r * (1.0 if i % 2 == 0 else 0.7), y + math.sin(a) * r * (1.0 if i % 2 == 0 else 0.7))
           for i, a in enumerate([k * 2 * math.pi / 8 + 0.3 for k in range(8)])]
    flat(ctx, lambda c: smooth_closed(c, pts, 0.5), INKBLOT, 0.85)
    flat(ctx, lambda c: ellipse_path(c, x + r * 0.5, y + r * 1.5, r * 0.3, r * 0.4), INKBLOT, 0.85)


def _pole(ctx, hx, hy, ang, up, down, col, w=9.0):
    ca, sa = math.cos(ang), math.sin(ang)
    top = (hx + ca * up, hy + sa * up)
    outlined_line(ctx, [(hx - ca * down, hy - sa * down), top], col, w, w + 7, smooth=False)
    return top


def _local(ctx, p, ang):
    """Enter a frame at p where local -y points along ang (for weapon heads)."""
    ctx.save()
    ctx.translate(*p)
    ctx.rotate(ang + math.pi / 2)


def _sword(ctx, hx, hy, ang, L, col, edge, guard, grip=hex2rgb("#3a2a30"), half=9.0):
    ca, sa = math.cos(ang), math.sin(ang)
    nx, ny = -sa, ca
    b = (hx + ca * 16, hy + sa * 16)
    tip = (hx + ca * L, hy + sa * L)
    blade = [(b[0] + nx * half, b[1] + ny * half), (tip[0] - ca * 18 + nx * half * 0.8, tip[1] - sa * 18 + ny * half * 0.8), tip,
             (tip[0] - ca * 18 - nx * half * 0.8, tip[1] - sa * 18 - ny * half * 0.8), (b[0] - nx * half, b[1] - ny * half)]
    _pp(ctx, blade, col, lw=4.5, hi_size=0.6)
    stroke(ctx, lambda c: (c.move_to(*b), c.line_to(tip[0] - ca * 8, tip[1] - sa * 8)), edge, 3)
    outlined_line(ctx, [(b[0] + nx * 18, b[1] + ny * 18), (b[0] - nx * 18, b[1] - ny * 18)], guard, 8, 15, smooth=False)
    outlined_line(ctx, [(hx - ca * 16, hy - sa * 16), b], grip, 8, 15, smooth=False)
    return tip


def _lantern(ctx, x, y, h, flame, metal=BRASS, glow_a=0.6, chain_from=None):
    if chain_from:
        _chain(ctx, chain_from, (x, y - h * 0.62))
    glow(ctx, x, y, h * 1.25, flame, glow_a)
    w = h * 0.66
    _pp(ctx, [(x - w * 0.6, y + h * 0.36), (x + w * 0.6, y + h * 0.36), (x + w * 0.4, y + h * 0.52), (x - w * 0.4, y + h * 0.52)],
        metal, lw=3, hi=False)
    paint(ctx, lambda c: rrect_path(c, x - w / 2, y - h * 0.38, w, h * 0.76, 6), light(flame, 0.55), lw=3.5, hi=False, shade_amt=0.15)
    _flame(ctx, x, y + h * 0.22, h * 0.48, w * 0.22, flame, light(flame, 0.65), lw=2.0)
    for dx in (-w * 0.25, w * 0.25):
        stroke(ctx, lambda c, dx=dx: (c.move_to(x + dx, y - h * 0.36), c.line_to(x + dx, y + h * 0.36)), INK, 2.2)
    _pp(ctx, [(x - w * 0.62, y - h * 0.36), (x + w * 0.62, y - h * 0.36), (x + w * 0.3, y - h * 0.56), (x - w * 0.3, y - h * 0.56)],
        metal, lw=3, hi=False)
    stroke(ctx, lambda c: ellipse_path(c, x, y - h * 0.64, 4.5, 4.5), INK, 5)
    stroke(ctx, lambda c: ellipse_path(c, x, y - h * 0.64, 4.5, 4.5), metal, 2)


def _rock(ctx, x, y, r, col=STONE, glow_cracks=None, moss=True):
    pts = [(x - r * 0.95, y - r * 0.68), (x - r * 0.22, y - r * 0.95), (x + r * 0.72, y - r * 0.85), (x + r, y - r * 0.05),
           (x + r * 0.85, y + r * 0.72), (x - r * 0.05, y + r * 0.95), (x - r * 0.85, y + r * 0.72), (x - r * 1.05, y + r * 0.05)]
    _sc(ctx, pts, col, lw=LW, t=0.3, hi_size=0.6)
    cracks = [[(x - r * 0.6, y + r * 0.5), (x - r * 0.3, y + r * 0.25), (x - r * 0.35, y - r * 0.05)],
              [(x + r * 0.75, y + r * 0.45), (x + r * 0.45, y + r * 0.3), (x + r * 0.5, y + r * 0.05), (x + r * 0.25, y - r * 0.1)]]
    for cr in cracks:
        if glow_cracks:
            glow(ctx, cr[1][0], cr[1][1], r * 0.7, glow_cracks, 0.6)
            stroke(ctx, lambda c, cr=cr: _open(c, cr), INK, 6)
            stroke(ctx, lambda c, cr=cr: _open(c, cr), glow_cracks, 3)
        else:
            stroke(ctx, lambda c, cr=cr: _open(c, cr), INK, 2.5)
    if moss:
        _cloud(ctx, [(x + r * 0.35, y - r * 0.85, r * 0.2), (x + r * 0.6, y - r * 0.75, r * 0.17), (x + r * 0.1, y - r * 0.9, r * 0.15)],
               LEAF, lw=2)


def _fist(ctx, x, y, cast, glow_cracks=None, scale=1.0):
    r = 34 * scale
    if glow_cracks:
        glow(ctx, x, y, r * 2.0, glow_cracks, 0.75 if cast else 0.45)
    _rock(ctx, x, y + 2, r, STONE, glow_cracks, moss=glow_cracks is None)
    for k in range(4):
        _el(ctx, x - r * 0.62 + k * r * 0.42, y - r * 0.72, r * 0.25, r * 0.2, light(STONE, 0.18), lw=3, hi=False, shade_amt=0.2)
    if glow_cracks:
        for k in range(3):
            stroke(ctx, lambda c, k=k: (c.move_to(x - r * 0.45 + k * r * 0.42, y - r * 0.55), c.line_to(x - r * 0.4 + k * r * 0.42, y - r * 0.2)),
                   glow_cracks, 2.5)


# ---------------------------------------------------------------------------- torso

def w3_torso_path(spec, s, w, hp, top, lean):
    o, ev = spec["outfit"], spec.get("_evo")
    sh = [(CX - s * 0.62 + lean, top), (CX + s * 0.62 + lean, top), (CX + s + lean * 0.6, top + 16), (CX + w + 2, 212)]
    sl = [(CX - w - 2, 212), (CX - s + lean * 0.6, top + 16)]
    t = 0.35
    if o == "layered_robe":
        hem = _dag(CX + hp + 16, CX - hp - 16, 262, 12, 6) if ev == "B" else _dag(CX + hp + 26, CX - hp - 26, GROUND - 4, 14, 8)
        t = 0.2
    elif o == "tailcoat":
        hem = [(CX + hp + 18, 272), (CX + hp + 2, 284), (CX + hp - 8, 244), (CX + 14, 238), (CX, 248), (CX - 14, 238),
               (CX - hp + 8, 244), (CX - hp - 2, 284), (CX - hp - 18, 272)]
        t = 0.25
    elif o == "star_cloak":
        sh = [(CX - s * 0.6 + lean, top - 4), (CX + s * 0.6 + lean, top - 4), (CX + s + 12 + lean * 0.6, top + 22), (CX + hp + 20, 236)]
        sl = [(CX - hp - 20, 236), (CX - s - 12 + lean * 0.6, top + 22)]
        if ev == "B":
            hem = _dag(CX + hp + 38, CX - hp - 38, GROUND - 4, 24, 9)
            t = 0.2
        else:
            hem = [(CX + hp + 36, GROUND - 6), (CX, GROUND - 2), (CX - hp - 36, GROUND - 6)]
    elif o == "scribe_robe":
        hem = _dag(CX + hp + 20, CX - hp - 20, GROUND - 6, 10, 7) if ev == "A" else \
            [(CX + hp + 18, GROUND - 8), (CX, GROUND - 2), (CX - hp - 18, GROUND - 8)]
    elif o == "river_dress":
        hem = [(CX + hp + 30 - (2 * hp + 60) * i / 8.0, GROUND - 6 + (7 if i % 2 else -5)) for i in range(9)]
        t = 0.5
    elif o == "frost_coat":
        hem = [(CX + hp + 24, 278), (CX + hp + 8, 266), (CX + 18, 276), (CX + 6, 242), (CX - 6, 242), (CX - 18, 276),
               (CX - hp - 8, 266), (CX - hp - 24, 278)]
        t = 0.15
    elif o == "oracle_robe":
        hem = [(CX + hp + 22, GROUND - 14), (CX + 8, GROUND - 8), (CX - hp - 26, GROUND - 18)]
    elif o == "cantor_robe":
        if ev == "B":
            hem = [(CX + hp + 14, 258), (CX, 264), (CX - hp - 14, 258)]
        elif ev == "A":
            hem = [(CX + hp + 40, GROUND - 6), (CX + hp + 14, GROUND - 14), (CX, GROUND - 2), (CX - hp - 14, GROUND - 14),
                   (CX - hp - 40, GROUND - 6)]
        else:
            hem = [(CX + hp + 26, GROUND - 6), (CX, GROUND), (CX - hp - 26, GROUND - 6)]
    else:  # tattered_mail
        hem = _dag(CX + hp + 8, CX - hp - 8, 256, 12, 7) if ev == "B" else _dag(CX + hp + 18, CX - hp - 18, 272, 16, 8)
        t = 0.2
    pts = sh + hem + sl
    return lambda c: smooth_closed(c, pts, t)


def w3_torso_detail(ctx, spec, m, lean):
    """Detail painted inside the torso clip."""
    main, second, trim = hex2rgb(spec["main"]), hex2rgb(spec["second"]), hex2rgb(spec["trim"])
    o, ev = spec["outfit"], spec.get("_evo")
    ec, ec2 = ELEMENT[spec["element"]]
    x0 = CX + lean * 0.3
    if o == "layered_robe":
        layer = _c(spec, "layer", "#a780e8")
        yb = 250 if ev == "B" else 266
        _pp(ctx, [(CX - 96, 204), (CX + 96, 204)] + _dag(CX + 96, CX - 96, yb, 14, 8), layer, lw=4, hi=False)
        flat(ctx, lambda c: rrect_path(c, x0 - 11, 168, 22, 140, 8), trim)
        for side in (-1, 1):
            stroke(ctx, lambda c, side=side: (c.move_to(x0 + side * 11, 170), c.line_to(x0 + side * 11, 300)), INK, 3)
        for i, y in enumerate((236, 270)):
            _glyph(ctx, x0, y, 6, second, i + 1, 2.8)
        flat(ctx, lambda c: rrect_path(c, CX - 60, 206, 120, 11, 5), second)
        stroke(ctx, lambda c: rrect_path(c, CX - 60, 206, 120, 11, 5), INK, 3)
    elif o == "tailcoat":
        flat(ctx, lambda c: poly_path(c, [(x0 - 16, 166), (x0 + 16, 166), (CX + 13, 240), (CX - 13, 240)]), second)
        for side in (-1, 1):
            _pp(ctx, [(x0 + side * 14, 166), (x0 + side * 32, 172), (CX + side * 22, 202), (CX + side * 13, 230)], shade(main, 0.3),
                lw=3, hi=False, shade_amt=0)
            for y in (210, 226):
                _el(ctx, CX + side * 25, y, 3.5, 3.5, trim, lw=2, hi=False, shade_amt=0)
        hp = m["hip"]
        for i, (x, y) in enumerate(((CX + hp + 4, 256), (CX + hp + 6, 272), (CX - hp - 4, 256), (CX - hp - 6, 272))):
            _glyph(ctx, x, y, 5, trim, i, 2.4)
        flat(ctx, lambda c: rrect_path(c, CX - 3, 186, 6, 40, 2), light(second, 0.0))
        for y in (194, 208, 222):
            _el(ctx, CX, y, 2.5, 2.5, INK, lw=0, hi=False, shade_amt=0)
    elif o == "sigil_plate":
        _sc(ctx, [(CX - 38, 174), (CX + 38, 174), (CX + 34, 228), (CX, 242), (CX - 34, 228)], light(main, 0.3), lw=4, t=0.35, hi_size=0.6)
        glow(ctx, CX, 216, 26, ec, 0.6)
        stroke(ctx, lambda c: ellipse_path(c, CX, 216, 13, 13), INK, 8)
        stroke(ctx, lambda c: ellipse_path(c, CX, 216, 13, 13), ec, 4)
        _glyph(ctx, CX, 216, 6, (1, 1, 1), 1, 2.4)
        flat(ctx, lambda c: rrect_path(c, CX - 60, 236, 120, 12, 5), trim)
        stroke(ctx, lambda c: rrect_path(c, CX - 60, 236, 120, 12, 5), INK, 3)
    elif o == "star_cloak":
        flat(ctx, lambda c: poly_path(c, [(x0 - 8, 168), (x0 + 8, 168), (CX + 46, 300), (CX - 46, 300)]), VOID_DARK)
        for side in (-1, 1):
            stroke(ctx, lambda c, side=side: (c.move_to(x0 + side * 8, 168), c.line_to(CX + side * 46, 300)), second, 4)
        stars = ((-58, 200, 6), (-30, 246, 4), (46, 186, 4), (60, 238, 6), (-66, 270, 5), (26, 272, 4), (-12, 226, 4),
                 (10, 256, 3), (0, 284, 5), (-44, 186, 3))
        for i, (dx, y, r) in enumerate(stars):
            sparkle(ctx, CX + dx, y, r, (1, 1, 1) if i % 3 else light(trim, 0.4))
        stroke(ctx, lambda c: _open(c, [(CX - 58, 200), (CX - 12, 226), (CX - 30, 246), (CX - 66, 270)]), trim, 1.6, 0.55)
        stroke(ctx, lambda c: _open(c, [(CX + 46, 186), (CX + 60, 238), (CX + 26, 272)]), trim, 1.6, 0.55)
        if ev == "A":
            for col, lw in ((INK, 12), (GOLD, 7)):
                stroke(ctx, lambda c: smooth_open(c, [(CX - 130, GROUND - 18), (CX, GROUND - 10), (CX + 130, GROUND - 18)]), col, lw)
        if ev == "B":
            _portal(ctx, CX - 52, 226, 10, 20, VOID_GLOW, rot=0.3, lw=3, glow_a=0.5)
            _portal(ctx, CX + 52, 256, 9, 17, VOID_GLOW, rot=-0.25, lw=3, spin=1.0, glow_a=0.5)
    elif o == "obsidian_plate":
        _sc(ctx, [(CX - 40, 174), (CX + 40, 174), (CX + 36, 226), (CX, 242), (CX - 36, 226)], light(main, 0.14), lw=4, t=0.3, hi_size=0.6)
        for (a, b) in (((CX, 180), (CX, 236)), ((CX - 34, 188), (CX, 204)), ((CX + 34, 188), (CX, 204))):
            stroke(ctx, lambda c, a=a, b=b: (c.move_to(*a), c.line_to(*b)), trim, 2.5, 0.55)
        glow(ctx, CX, 220, 30, VOID_GLOW, 0.7)
        _pp(ctx, [(CX, 208), (CX + 10, 220), (CX, 232), (CX - 10, 220)], light(ec, 0.3), lw=3, hi_size=0.6)
        flat(ctx, lambda c: rrect_path(c, CX - 60, 236, 120, 12, 5), second)
        stroke(ctx, lambda c: rrect_path(c, CX - 60, 236, 120, 12, 5), INK, 3)
    elif o == "scribe_robe":
        panel = light(main, 0.4) if ev != "A" else shade(main, 0.35)
        flat(ctx, lambda c: poly_path(c, [(x0 - 12, 166), (x0 + 12, 166), (CX + 24, 300), (CX - 24, 300)]), panel)
        for side in (-1, 1):
            stroke(ctx, lambda c, side=side: (c.move_to(x0 + side * 12, 166), c.line_to(CX + side * 24, 300)), INK, 3)
        _pp(ctx, [(CX - 46 + lean, 168), (CX - 28 + lean, 166), (CX + 56, 230), (CX + 40, 240)], second, lw=3, hi=False, shade_amt=0.15)
        flat(ctx, lambda c: rrect_path(c, CX - 60, 216, 120, 12, 5), hex2rgb("#7a4a2a"))
        stroke(ctx, lambda c: rrect_path(c, CX - 60, 216, 120, 12, 5), INK, 3)
        if ev == "A":
            for (dx, y, r) in ((-46, 268, 9), (34, 276, 8), (-6, 282, 7), (52, 256, 6)):
                flat(ctx, lambda c, dx=dx, y=y, r=r: ellipse_path(c, CX + dx, y, r, r * 0.8), hex2rgb("#1e1012"), 0.8)
                stroke(ctx, lambda c, dx=dx, y=y, r=r: ellipse_path(c, CX + dx, y, r * 0.8, r * 0.62), EMBER, 2, 0.85)
            for (dx, y) in ((-30, 250), (24, 244), (48, 280)):
                sparkle(ctx, CX + dx, y, 5, EMBER)
        else:
            for (dx, y, r) in ((-42, 266, 6), (30, 276, 5), (8, 256, 3.5)):
                _blot(ctx, CX + dx, y, r)
    elif o == "river_dress":
        flat(ctx, lambda c: poly_path(c, [(x0 - 10, 166), (x0 + 10, 166), (CX + 34, 300), (CX - 34, 300)]), second)
        for k in range(3):
            stroke(ctx, lambda c, k=k: smooth_open(c, [(CX - 20 + k * 12, 222), (CX - 12 + k * 12, 246), (CX - 24 + k * 14, 272),
                                                       (CX - 16 + k * 14, 298)]), ec, 2.5, 0.6)
        for k, y in enumerate((262, 278)):
            pts = [(CX - 96 + i * 16, y + (-5 if (i + k) % 2 else 5)) for i in range(13)]
            stroke(ctx, lambda c, pts=pts: smooth_open(c, pts), light(main, 0.6), 4)
        if ev == "A":
            _sc(ctx, [(CX - 36, 170), (CX + 36, 170), (CX + 32, 212), (CX, 228), (CX - 32, 212)], hex2rgb("#d8ecf8"), lw=4, t=0.35, hi_size=0.6)
            stroke(ctx, lambda c: smooth_open(c, [(CX - 24, 214), (CX - 14, 196), (CX + 2, 190), (CX + 12, 198), (CX + 4, 206), (CX - 2, 200)]),
                   ec, 3.5)
        if ev == "B":
            _cross(ctx, CX, 252, 9, ec, glow_a=0.0)
        for col, lw in ((INK, 8), (hex2rgb("#fff4ea"), 4)):
            stroke(ctx, lambda c: smooth_open(c, [(CX - 60, 214), (CX, 222), (CX + 60, 214)]), col, lw)
        for k in range(5):
            x = CX - 40 + k * 20
            _el(ctx, x, 218 + 3 * math.sin((k / 4.0) * math.pi), 4, 4, hex2rgb("#fffaf4"), lw=2, hi=False, shade_amt=0.15)
    elif o == "ranger_jacket":
        stroke(ctx, lambda c: (c.move_to(x0, 168), c.line_to(CX, 256)), shade(main, 0.45), 3)
        for (y, side) in ((186, -1), (206, -1), (192, 1)):
            stroke(ctx, lambda c, y=y, side=side: _open(c, [(CX + side * 52, y), (CX + side * 42, y + 8), (CX + side * 52, y + 12),
                                                             (CX + side * 42, y + 20)]), trim, 3)
        _pp(ctx, [(CX + 34 + lean, 164), (CX + 50 + lean, 170), (CX - 32, 252), (CX - 48, 244)], second, lw=3, hi=False, shade_amt=0.15)
        paint(ctx, lambda c: rrect_path(c, CX - 3, 202, 14, 12, 3), BRASS, lw=2.5, hi=False)
        flat(ctx, lambda c: rrect_path(c, CX - 58, 226, 116, 12, 5), hex2rgb("#3a2a20"))
        stroke(ctx, lambda c: rrect_path(c, CX - 58, 226, 116, 12, 5), INK, 3)
        for x in (CX - 44, CX + 22):
            paint(ctx, lambda c, x=x: rrect_path(c, x, 234, 20, 18, 4), hex2rgb("#5a4030"), lw=3, hi=False)
    elif o == "frost_coat":
        flat(ctx, lambda c: poly_path(c, [(x0 - 12, 166), (x0 + 12, 166), (CX + 18, 300), (CX - 18, 300)]), second)
        for side in (-1, 1):
            stroke(ctx, lambda c, side=side: (c.move_to(x0 + side * 12, 166), c.line_to(CX + side * 18, 300)), INK, 3)
        for y in (184, 200, 216):
            outlined_line(ctx, [(x0 - 18, y), (x0 + 18, y)], trim if ev != "B" else BRASS, 4, 8, smooth=False)
            _el(ctx, x0, y, 4, 4, light(ec, 0.3) if ev != "B" else BRASS, lw=2, hi=False, shade_amt=0)
        sx, sy = CX - 42, 252
        for k in range(3):
            a = k * math.pi / 3
            stroke(ctx, lambda c, a=a: (c.move_to(sx - math.cos(a) * 10, sy - math.sin(a) * 10), c.line_to(sx + math.cos(a) * 10, sy + math.sin(a) * 10)),
                   trim, 2.5)
        flat(ctx, lambda c: rrect_path(c, CX - 58, 228, 116, 11, 5), shade(main, 0.35))
        stroke(ctx, lambda c: rrect_path(c, CX - 58, 228, 116, 11, 5), INK, 3)
        _pp(ctx, [(CX, 226), (CX + 8, 233), (CX, 240), (CX - 8, 233)], light(ec, 0.3), lw=2.5, hi=False)
        if ev == "A":
            crust = [(CX - 110, 300), (CX + 110, 300)] + [(CX + 110 - i * 20, 262 + (10 if i % 2 else -6)) for i in range(12)]
            _pp(ctx, crust, light(ec, 0.45), lw=3.5, hi=False, shade_amt=0.15)
    elif o == "oracle_robe":
        for k in range(3):
            stroke(ctx, lambda c, k=k: smooth_open(c, [(CX + 22 + k * 16, 232), (CX + 16 + k * 18, 260), (CX + 20 + k * 20, 292)]),
                   shade(main, 0.18), 3)
        _pp(ctx, [(CX - 50 + lean, 166), (CX - 28 + lean, 164), (CX + 64, 246), (CX + 42, 262)], second, lw=3, hi=False, shade_amt=0.15)
        for k in range(2):
            stroke(ctx, lambda c, k=k: (c.move_to(CX - 34 + k * 10 + lean, 172), c.line_to(CX + 46 + k * 4, 248)), shade(second, 0.3), 2)
        for col, lw in ((INK, 7), (trim, 3.5)):
            stroke(ctx, lambda c: smooth_open(c, [(CX - 60, 222), (CX, 226), (CX + 60, 218)]), col, lw)
        for x in (CX - 30, CX - 20):
            outlined_line(ctx, [(x, 226), (x - 2, 246)], trim, 3, 7, smooth=False)
        for col, lw in ((INK, 10), (trim, 5)):
            stroke(ctx, lambda c: smooth_open(c, [(CX - 120, GROUND - 30), (CX, GROUND - 22), (CX + 120, GROUND - 26)]), col, lw)
        swirl = [(CX - 36 + math.cos(a) * (10 - a * 1.2), 256 + math.sin(a) * (10 - a * 1.2)) for a in [i * 0.5 for i in range(12)]]
        stroke(ctx, lambda c: smooth_open(c, swirl), second if ev != "B" else ec, 3)
    elif o == "stone_gi":
        skin = SKIN[spec["skin"]]
        if ev == "B":
            flat(ctx, lambda c: rrect_path(c, CX - 90, 150, 180, 72, 4), skin)
            for side in (-1, 1):
                stroke(ctx, lambda c, side=side: smooth_open(c, [(CX + side * 40, 194), (CX + side * 18, 202), (CX + side * 2, 192)]), INK, 3)
            for y in (210,):
                stroke(ctx, lambda c, y=y: (c.move_to(CX - 10, y), c.line_to(CX + 10, y)), INK, 2.5)
            for cr in ([(CX - 34, 176), (CX - 24, 186), (CX - 28, 198)], [(CX + 30, 204), (CX + 22, 212), (CX + 28, 220)]):
                glow(ctx, cr[1][0], cr[1][1], 22, EMBER, 0.6)
                stroke(ctx, lambda c, cr=cr: _open(c, cr), INK, 6)
                stroke(ctx, lambda c, cr=cr: _open(c, cr), EMBER, 3)
        else:
            flat(ctx, lambda c: poly_path(c, [(x0 - 30, 160), (x0 + 30, 160), (CX + 6, 224), (CX - 6, 224)]), skin)
            for side in (-1, 1):
                stroke(ctx, lambda c, side=side: (c.move_to(x0 + side * 30, 160), c.line_to(CX + side * 6, 224)), INK, 3.5)
            stroke(ctx, lambda c: _open(c, [(CX - 8, 176), (CX - 2, 186), (CX - 6, 196)]), INK, 2.5)
            glow(ctx, CX - 2, 186, 14, ec2, 0.35)
    elif o == "cantor_robe":
        if ev != "B":
            for side in (-1, 1):
                flat(ctx, lambda c, side=side: poly_path(c, [(x0 + side * 6, 166), (x0 + side * 20, 166), (CX + side * 24, 300),
                                                              (CX + side * 8, 300)]), second)
                for e in (6, 20):
                    stroke(ctx, lambda c, side=side, e=e: (c.move_to(x0 + side * e, 166), c.line_to(CX + side * (e + 4 if e > 6 else 8), 300)),
                           INK, 2.5)
            for (dx, y, r) in ((-56, 262, 10), (56, 252, 9), (-50, 212, 7), (50, 204, 7), (-30, 284, 6), (36, 286, 6)):
                _sun(ctx, CX + dx, y, r, second, lw=2)
        else:
            _sc(ctx, [(CX - 38, 172), (CX + 38, 172), (CX + 34, 222), (CX, 238), (CX - 34, 222)], light(second, 0.2), lw=4, t=0.35, hi_size=0.6)
            _sun(ctx, CX, 214, 12, hex2rgb("#fff7cc"), lw=2.5)
        for col, lw in ((INK, 6), (second, 3)):
            stroke(ctx, lambda c: smooth_open(c, [(CX - 56, 228), (CX, 234), (CX + 56, 228)]), col, lw)
        if ev == "A":
            for i in range(12):
                x = CX - 110 + i * 20
                _leaf(ctx, x, GROUND - 30, math.pi / 2 + (i - 5.5) * 0.06, 24, 8, (1, 1, 1) if i % 2 else light(second, 0.6), lw=2.5, vein=False)
    elif o == "tattered_mail":
        mail = light(main, 0.25)
        rows = range(172, 272, 9) if ev != "B" else range(176, 206, 9)
        for j, y in enumerate(rows):
            for i in range(13):
                x = CX - 72 + i * 12 + (6 if j % 2 else 0)
                stroke(ctx, lambda c, x=x, y=y: c.arc(x, y, 5, 0.1, math.pi - 0.1), mail, 1.8)
        if ev == "B":
            for side in (-1, 1):
                outlined_line(ctx, [(CX + side * 46, 166), (CX - side * 34, 236)], hex2rgb("#4a3040"), 8, 14, smooth=False)
            _el(ctx, CX, 201, 6, 6, trim, lw=2.5, hi=False)
        _pp(ctx, [(x0 - 22, 170), (x0 + 22, 170), (CX + 26, 236), (CX + 18, 268), (CX + 8, 250), (CX - 4, 272), (CX - 14, 252), (CX - 26, 266)],
            second, lw=3.5, hi=False, shade_amt=0.15)
        flat(ctx, lambda c: rrect_path(c, CX - 60, 222, 120, 12, 5), hex2rgb("#241c24"))
        stroke(ctx, lambda c: rrect_path(c, CX - 60, 222, 120, 12, 5), INK, 3)
        paint(ctx, lambda c: ellipse_path(c, CX, 228, 8, 8), trim, lw=2.5, hi=False)
        flat(ctx, lambda c: ellipse_path(c, CX + 3, 226, 6, 6), hex2rgb("#241c24"))


def w3_torso_overlay(ctx, spec, m, lean):
    """Garment parts drawn over the torso silhouette."""
    main, second, trim = hex2rgb(spec["main"]), hex2rgb(spec["second"]), hex2rgb(spec["trim"])
    o, ev = spec["outfit"], spec.get("_evo")
    ec, ec2 = ELEMENT[spec["element"]]
    x0 = CX + lean * 0.3
    if o == "layered_robe":
        if ev == "B":
            bx, by = CX - 54, 242
            _chain(ctx, (CX - 42, 214), (bx + 4, by - 16))
            paint(ctx, lambda c: rrect_path(c, bx - 15, by - 17, 30, 36, 5), shade(main, 0.15), lw=3.5, hi_size=0.6)
            flat(ctx, lambda c: rrect_path(c, bx + 10, by - 14, 4, 30, 1.5), hex2rgb("#fff4fb"))
            _glyph(ctx, bx - 2, by, 7, second, 3, 2.6)
        _pp(ctx, [(x0, 166), (x0 + 9, 176), (x0, 186), (x0 - 9, 176)], SILVER, lw=3, hi_size=0.6)
        stroke(ctx, lambda c: (c.move_to(x0 - 3, 172), c.line_to(x0 + 2, 180)), second, 2)
    elif o == "tailcoat":
        for side in (-1, 1):
            _pp(ctx, [(x0, 174), (x0 + side * 15, 165), (x0 + side * 15, 183)], trim, lw=3, hi=False, shade_amt=0.2)
        _el(ctx, x0, 174, 5, 5, light(trim, 0.2), lw=2.5, hi=False)
    elif o == "sigil_plate":
        for side in (-1, 1):
            _sc(ctx, [(CX + side * 8, 244), (CX + side * 50, 244), (CX + side * 56, 268), (CX + side * 12, 272)], light(main, 0.2),
                lw=4.5, t=0.3, hi=False)
            _glyph(ctx, CX + side * 32, 258, 5, trim, side + 1, 2.2)
    elif o == "star_cloak":
        glow(ctx, x0, 174, 22, VOID_GLOW, 0.6)
        paint(ctx, lambda c: star_path(c, x0, 174, 12, 5, 5), trim, lw=3, hi=False)
    elif o == "obsidian_plate":
        if ev == "B":
            _sc(ctx, [(x0 - 24, 238), (x0 + 24, 238), (x0 + 26, 280), (x0, 288), (x0 - 26, 280)], second, lw=LW - 1, t=0.2, hi_size=0.5)
            _portal(ctx, x0, 262, 9, 12, VOID_GLOW, glow_a=0.4, lw=3)
        else:
            rows = ((244, 270),) if ev != "A" else ((262, 290), (244, 270))
            for (ya, yb) in rows:
                for side in (-1, 1):
                    _sc(ctx, [(CX + side * 8, ya), (CX + side * 52, ya), (CX + side * 58, yb - 4), (CX + side * 12, yb)], light(main, 0.1),
                        lw=4.5, t=0.3, hi=False)
                    stroke(ctx, lambda c, side=side, ya=ya: (c.move_to(CX + side * 14, ya + 7), c.line_to(CX + side * 48, ya + 7)), ec, 2.5, 0.8)
    elif o == "scribe_robe":
        for (x, h, r) in ((CX - 40, 30, 0.1), (CX - 20, 24, -0.08), (CX + 28, 28, 0.06)):
            ctx.save()
            ctx.translate(x, 228)
            ctx.rotate(r)
            paint(ctx, lambda c, h=h: rrect_path(c, -6, 0, 12, h, 4), PARCH, lw=3, hi=False, shade_amt=0.2)
            for yy in (0, h):
                _el(ctx, 0, yy, 8, 3.5, hex2rgb("#8a5a34"), lw=2.5, hi=False, shade_amt=0)
            flat(ctx, lambda c, h=h: ellipse_path(c, 0, h * 0.5, 3.5, 3.5), hex2rgb("#c8402a"))
            ctx.restore()
        paint(ctx, lambda c: rrect_path(c, CX + 44, 226, 16, 16, 5), hex2rgb("#3a3a5a"), lw=3, hi_size=0.6)
        paint(ctx, lambda c: rrect_path(c, CX + 48, 219, 8, 8, 2), hex2rgb("#a8743a"), lw=2.5, hi=False)
    elif o == "river_dress":
        if ev != "A":
            _shell(ctx, x0, 186, 10, 0, trim)
    elif o == "ranger_jacket":
        for side in (-1, 1):
            _pp(ctx, [(CX + side * 10 + lean, 172), (CX + side * 36 + lean, 152), (CX + side * 50 + lean, 164), (CX + side * 32 + lean, 182)],
                shade(main, 0.12), lw=4, hi=False)
        if ev == "A":
            outlined_line(ctx, [(CX + 38, 234), (CX + 40, 244)], hex2rgb("#6a4428"), 3, 7, smooth=False)
            _leaf(ctx, CX + 32, 252, math.pi / 2 + 0.35, 32, 7, hex2rgb("#c8402a"), lw=2.5)
            _leaf(ctx, CX + 48, 252, math.pi / 2 - 0.2, 36, 7, hex2rgb("#f4f0e8"), lw=2.5)
            _skull(ctx, CX + 40, 254, 11)
    elif o == "frost_coat":
        for side in (-1, 1):
            _pp(ctx, [(CX + side * 10 + lean, 172), (CX + side * 34 + lean, 148), (CX + side * 48 + lean, 160), (CX + side * 30 + lean, 182)],
                second, lw=4, hi=False, shade_amt=0.15)
    elif o == "oracle_robe":
        _el(ctx, CX - 34 + lean, 174, 10, 10, trim, lw=3, hi_size=0.6)
        stroke(ctx, lambda c: c.arc(CX - 34 + lean, 174, 5, 0.5, 4.8), shade(trim, 0.4), 2)
    elif o == "stone_gi":
        rope = second
        pts = [(CX - 66, 220), (CX - 22, 228), (CX + 22, 228), (CX + 66, 220)]
        outlined_line(ctx, pts, rope, 13, 20)
        for i in range(12):
            x = CX - 60 + i * 11
            y = 220 + 7 * (1 - ((x - CX) / 66.0) ** 2)
            stroke(ctx, lambda c, x=x, y=y: (c.move_to(x - 4, y - 5), c.line_to(x + 3, y + 5)), shade(rope, 0.4), 2.5)
        for pts2 in ([(CX - 14, 232), (CX - 20, 254), (CX - 16, 270)], [(CX - 2, 232), (CX + 4, 256), (CX, 268)]):
            outlined_line(ctx, pts2, rope, 7, 13)
            _el(ctx, pts2[-1][0], pts2[-1][1] + 4, 5, 6, light(rope, 0.2), lw=2.5, hi=False)
        _el(ctx, CX - 8, 230, 11, 9, rope, lw=3.5, hi=False)
    elif o == "cantor_robe":
        if ev == "B":
            _sc(ctx, [(CX - 40 + lean, 162), (CX + 40 + lean, 162), (CX + 34 + lean, 184), (CX - 34 + lean, 184)], second, lw=4.5, t=0.35, hi_size=0.6)
        else:
            for i in range(9):
                t = i / 8.0
                x = CX - 40 + 80 * t + lean
                y = 168 + 6 * math.sin(t * math.pi)
                _el(ctx, x, y, 11, 9, (1, 1, 1) if i % 2 == 0 else hex2rgb("#fff4d6"), lw=3, hi=False, shade_amt=0.15)
        _sun(ctx, x0 + lean * 0.4, 180, 9, second)
    elif o == "tattered_mail":
        _chain(ctx, (CX + 34, 232), (CX + 52, 266))


def w3_shoulders(ctx, spec, m, lean):
    main, second, trim = hex2rgb(spec["main"]), hex2rgb(spec["second"]), hex2rgb(spec["trim"])
    o, ev, pose = spec["outfit"], spec.get("_evo"), spec.get("_pose")
    ec, ec2 = ELEMENT[spec["element"]]
    s = m["shoulder"]
    if o == "layered_robe":
        if ev == "B":
            for side in (-1, 1):
                pts = [(CX + side * (s - 30) + lean, 160), (CX + side * (s + 18) + lean, 162), (CX + side * (s + 24) + lean, 192),
                       (CX + side * (s - 6) + lean, 198)]
                _pp(ctx, pts, light(main, 0.12), lw=LW - 1, hi_size=0.6)
                _glyph(ctx, CX + side * (s + 4) + lean, 180, 6, second, side + 1, 2.6)
        else:
            layer = _c(spec, "layer", "#a780e8")
            if ev == "A":
                for side in (-1, 1):
                    pts = [(CX + side * 14 + lean, 172), (CX + side * 52 + lean, 120), (CX + side * 66 + lean, 134), (CX + side * 38 + lean, 180)]
                    _pp(ctx, pts, SILVER, lw=4, hi_size=0.7)
                    stroke(ctx, lambda c, side=side: (c.move_to(CX + side * 32 + lean, 156), c.line_to(CX + side * 54 + lean, 130)), second, 2.5)
            cap = [(CX - 24 + lean, 158), (CX + 24 + lean, 158), (CX + s + 12 + lean, 178)] + \
                _dag(CX + s + 16 + lean, CX - s - 16 + lean, 204, 10, 6) + [(CX - s - 12 + lean, 178)]
            _sc(ctx, cap, layer, lw=LW - 1, t=0.2, hi_size=0.5)
    elif o == "tailcoat" and ev == "A":
        for side in (-1, 1):
            x = CX + side * (s - 6) + lean
            for k in range(5):
                fx = x - 12 + k * 6
                outlined_line(ctx, [(fx, 174), (fx + side, 192)], GOLD, 3, 7, smooth=False)
            _el(ctx, x, 170, 20, 9, GOLD, lw=4, rot=side * 0.18, hi_size=0.6)
    elif o == "sigil_plate":
        for side in (-1, 1):
            x = CX + side * (s - 2) + lean
            _el(ctx, x, 176, 25, 21, light(main, 0.2), lw=LW - 1, hi_size=0.6)
            stroke(ctx, lambda c, x=x: ellipse_path(c, x, 176, 15, 12), trim, 3)
            _glyph(ctx, x, 176, 6, ec, 0, 2.5)
    elif o == "star_cloak" and ev == "A":
        mantle = hex2rgb("#4a2a8a")
        for side in (-1, 1):
            _pp(ctx, [(CX + side * 10 + lean, 172), (CX + side * 44 + lean, 138), (CX + side * 60 + lean, 152), (CX + side * 36 + lean, 184)],
                shade(mantle, 0.1), lw=4, hi=False)
        edge = [(CX - s - 18 + lean, 204), (CX - 26 + lean, 196), (CX + lean, 212), (CX + 26 + lean, 196), (CX + s + 18 + lean, 204)]
        _sc(ctx, [(CX - s - 24 + lean, 172), (CX - 30 + lean, 160), (CX + 30 + lean, 160), (CX + s + 24 + lean, 172)] + edge[::-1],
            mantle, lw=LW - 1, t=0.35, hi_size=0.6)
        stroke(ctx, lambda c: smooth_open(c, edge), GOLD, 4)
        glow(ctx, CX + lean, 180, 22, VOID_GLOW, 0.6)
        paint(ctx, lambda c: star_path(c, CX + lean, 180, 12, 5, 5), GOLD, lw=3, hi=False)
    elif o == "obsidian_plate":
        big = 1.2 if ev == "A" else (0.75 if ev == "B" else 1.0)
        if ev == "A":
            _sc(ctx, [(CX - 38 + lean, 160), (CX + 38 + lean, 160), (CX + 32 + lean, 182), (CX - 32 + lean, 182)], light(main, 0.15), lw=4.5, t=0.35, hi=False)
        for side in (-1, 1):
            ox = CX + side * (s - 8) + lean
            if ev == "A":
                for (dx, h) in ((-2, 36), (16, 26)):
                    bx = ox + side * dx
                    _pp(ctx, [(bx - 7, 166), (bx + side * 8, 166 - h), (bx + 7, 166)], light(main, 0.3), lw=3.5, hi=False)
            pad = [(ox - side * 24 * big, 160), (ox + side * 24 * big, 158 + (1 - big) * 10), (ox + side * 30 * big, 196), (ox - side * 6, 198)]
            _pp(ctx, pad, light(main, 0.1), lw=LW, hi_size=0.6)
            stroke(ctx, lambda c, ox=ox: smooth_open(c, [(ox - side * 14, 172), (ox + side * 10 * big, 176), (ox + side * 24 * big, 190)]), ec, 3.5)
    elif o == "scribe_robe":
        if ev == "B":
            pts = [(CX - s - 14 + lean, 178), (CX - 24 + lean, 158), (CX + 24 + lean, 158), (CX + s + 14 + lean, 178), (CX + s + 6 + lean, 198),
                   (CX + 24, 216), (CX + lean * 0.3, 238), (CX - 24, 216), (CX - s - 6 + lean, 198)]
            _sc(ctx, pts, second, lw=LW - 1, t=0.3, hi_size=0.5)
            ctx.save()
            ctx.new_path()
            smooth_closed(ctx, pts, 0.3)
            ctx.clip()
            for k in range(3):
                stroke(ctx, lambda c, k=k: smooth_open(c, [(CX - s - 10 + lean, 188 + k * 8), (CX + lean * 0.3, 210 + k * 9),
                                                           (CX + s + 10 + lean, 188 + k * 8)]), light(second, 0.4), 2.5)
            ctx.restore()
            for k in range(4):
                x = CX + lean * 0.3 - 6 + k * 4
                outlined_line(ctx, [(x, 238), (x, 248)], second, 2.5, 6, smooth=False)
        else:
            lsh, rsh = (CX - s + 8 + lean, 182), (CX + s - 8 + lean, 182)
            lh, rh = hands_for(spec, pose)
            for (a, b) in ((lsh, lh), (rsh, rh)):
                for t, r in ((0.62, 6.5), (0.45, 4.0)):
                    _blot(ctx, a[0] + (b[0] - a[0]) * t + 3, a[1] + (b[1] - a[1]) * t - 2, r)
    elif o == "river_dress":
        for side in (-1, 1):
            ox = CX + side * (s - 10) + lean
            if ev == "A":
                pts = [(ox - side * 22, 172), (ox - side * 4, 154), (ox + side * 22, 148), (ox + side * 38, 160), (ox + side * 30, 170),
                       (ox + side * 20, 164), (ox + side * 14, 174), (ox + side * 28, 196), (ox - side * 10, 196)]
                _sc(ctx, pts, light(ec, 0.15), lw=LW - 1, t=0.35, hi_size=0.6)
                stroke(ctx, lambda c, ox=ox: smooth_open(c, [(ox - side * 10, 162), (ox + side * 14, 154), (ox + side * 28, 160)]), (1, 1, 1), 3, 0.85)
            elif ev != "B":
                _shell(ctx, ox, 180, 20, side * 0.55, trim)
    elif o == "ranger_jacket":
        if ev == "A":
            _cloud(ctx, [(CX - 44 + lean + i * 17.6, 164 + (i % 2) * 4, 11) for i in range(6)], hex2rgb("#8a6a4a"), lw=2.5,
                   hi_col=light(hex2rgb("#8a6a4a"), 0.4))
        ox = CX - (s - 8) + lean
        _sc(ctx, [(ox + 22, 160), (ox - 20, 162), (ox - 26, 196), (ox + 10, 194)], light(main, 0.18), lw=LW, t=0.45, hi_size=0.6)
        for dy in (174, 186):
            _el(ctx, ox - 8, dy, 3, 3, second, lw=1.8, hi=False, shade_amt=0)
        if ev == "B":
            ox2 = CX + s - 8 + lean
            glow(ctx, ox2 + 10, 132, 22, ec2, 0.7)
            outlined_line(ctx, [(ox2, 172), (ox2 + 10, 136)], hex2rgb("#5a5f70"), 5, 10, smooth=False)
            for k in range(3):
                _el(ctx, ox2 + 3 + k * 2.6, 162 - k * 9, 8, 3.5, COPPER, lw=2.5, hi=False, shade_amt=0)
            _el(ctx, ox2 + 10, 132, 6, 6, ec2, lw=2.5, hi=False)
    elif o == "frost_coat":
        ox = CX - (s - 8) + lean
        for k, (dx, h, a) in enumerate(((10, 44, -1.9), (-6, 56, -2.15), (-20, 40, -2.45), (22, 28, -1.62))):
            _spike(ctx, ox + dx, 170, a, h, 9, light(ec, 0.35) if k % 2 else light(ec, 0.6))
        _sc(ctx, [(ox + 24, 160), (ox - 22, 162), (ox - 28, 198), (ox + 10, 196)], light(main, 0.2), lw=LW, t=0.45, hi_size=0.6)
        ox2 = CX + s - 8 + lean
        if ev == "B":
            _el(ctx, ox2, 176, 22, 18, BRASS, lw=LW - 1, hi_size=0.6)
            _gear(ctx, ox2, 176, 12, 8, light(BRASS, 0.3))
        else:
            _el(ctx, ox2, 174, 18, 13, light(main, 0.2), lw=4.5, hi=False)
    elif o == "stone_gi":
        if ev == "A":
            for side in (-1, 1):
                ox = CX + side * (s - 4) + lean
                rock = [(ox - side * 30, 166), (ox - side * 6, 144), (ox + side * 24, 146), (ox + side * 44, 166), (ox + side * 42, 198),
                        (ox + side * 14, 210), (ox - side * 16, 196)]
                _sc(ctx, rock, STONE, lw=LW, t=0.25, hi_size=0.6)
                stroke(ctx, lambda c, ox=ox: _open(c, [(ox + side * 4, 152), (ox + side * 10, 168), (ox + side * 4, 180)]), INK, 2.5)
                stroke(ctx, lambda c, ox=ox: _open(c, [(ox + side * 30, 186), (ox + side * 20, 196)]), INK, 2.5)
                _cloud(ctx, [(ox - side * 2, 148, 8), (ox + side * 12, 146, 7)], LEAF, lw=2)
        else:
            lsh, rsh = (CX - s + 8 + lean, 182), (CX + s - 8 + lean, 182)
            lh, rh = hands_for(spec, pose)
            for (a, b) in ((lsh, lh), (rsh, rh)):
                px, py = a[0] + (b[0] - a[0]) * 0.3, a[1] + (b[1] - a[1]) * 0.3
                stroke(ctx, lambda c, px=px, py=py: _open(c, [(px - 7, py - 5), (px, py + 2), (px + 3, py - 3), (px + 9, py + 6)]), INK, 2.5)
    elif o == "cantor_robe" and ev == "B":
        for side in (-1, 1):
            ox = CX + side * (s - 6) + lean
            paint(ctx, lambda c, ox=ox: star_path(c, ox, 176, 30, 22, 10), second, lw=4, hi=False, shade_amt=0.15)
            _el(ctx, ox, 176, 20, 17, light(second, 0.25), lw=4, hi_size=0.6)
    elif o == "tattered_mail":
        if ev == "B":
            ox = CX - (s - 8) + lean
            _sc(ctx, [(ox + 20, 160), (ox - 18, 162), (ox - 24, 192), (ox + 8, 190)], hex2rgb("#4a3040"), lw=LW - 1, t=0.45, hi_size=0.5)
            return
        big = 1.15 if ev == "A" else 1.0
        for side in (-1, 1):
            ox = CX + side * (s - 8) + lean
            cloth = [(ox - side * 18, 182), (ox + side * 28 * big, 182), (ox + side * 30 * big, 218), (ox + side * 22, 206), (ox + side * 14, 224),
                     (ox + side * 4, 208), (ox - side * 6, 222), (ox - side * 14, 204)]
            _pp(ctx, cloth, second, lw=3.5, hi=False, shade_amt=0.15)
            if ev == "A":
                for (dx, h) in ((-4, 34), (14, 24)):
                    bx = ox + side * dx
                    _pp(ctx, [(bx - 7, 166), (bx + side * 6, 166 - h), (bx + 7, 166)], BONE, lw=3.5, hi=False)
            pad = [(ox - side * 24, 160), (ox + side * 22 * big, 158), (ox + side * 28 * big, 196), (ox - side * 8, 196)]
            _sc(ctx, pad, light(main, 0.12), lw=LW, t=0.4, hi_size=0.6)
            stroke(ctx, lambda c, ox=ox: smooth_open(c, [(ox - side * 14, 170), (ox + side * 12, 172), (ox + side * 24 * big, 188)]), trim, 3)


# ---------------------------------------------------------------------------- back items & front effects

def _mirror_orbit(ctx, spec, cast, front):
    cy, rx, ry = (188, 132, 40) if cast else (206, 122, 30)
    rot = -0.12
    a0, a1 = (0.0, math.pi) if front else (math.pi, 2 * math.pi)
    pts = _arc_pts(CX, cy, rx, ry, rot, a0, a1)
    stroke(ctx, lambda c: _open(c, pts), light(hex2rgb("#ff5fd2"), 0.4), 2.5, 0.65)
    angles = (0.3, 1.2, 2.1, 2.95) if front else (3.6, 4.5, 5.4)
    for i, a in enumerate(angles):
        x, y = _arc_pts(CX, cy, rx, ry, rot, a, a, 1)[0]
        _shard(ctx, x, y, a + math.pi / 2 + (0.5 if i % 2 else -0.5), 30 - (i % 2) * 6, 9, SILVER, sheen=hex2rgb("#ff5fd2"))


def _oriane_rings(ev, cast):
    dy = -10 if cast else 0
    if ev == "B":
        return []
    if ev == "A":
        return [(CX, 216 + dy, 120, 28, -0.12), (CX, 150 + dy, 102, 22, 0.16)]
    return [(CX, 210 + dy, 100, 22, -0.12)]


def _wind_band(ctx, spec, front, cast):
    ec, ec2 = ELEMENT[spec["element"]]
    cy, rx, ry = (196, 120, 40) if cast else (214, 112, 34)
    a0, a1 = (0.0, math.pi) if front else (math.pi, 2 * math.pi)
    pts = _arc_pts(CX, cy, rx, ry, -0.2, a0, a1, 20)
    _ribbon(ctx, pts, ec, light(ec2, 0.4), 9)


def w3_back_items(ctx, spec, pose, lean):
    h, ev = spec["head"], spec.get("_evo")
    if h not in W3_HEADS:
        return
    ec, ec2 = ELEMENT[spec["element"]]
    trim = hex2rgb(spec["trim"])
    cast = pose == "cast"
    if h == "mirror_circlet" and ev == "A":
        _mirror_orbit(ctx, spec, cast, front=False)
    elif h == "conductor_hat":
        for ring in _oriane_rings(ev, cast):
            _ring_half(ctx, *ring, col=ec, front=False, glyph_col=trim)
    elif h == "rift_hood" and ev == "A":
        bx, by = CX, 30
        r = 18 if not cast else 21
        glow(ctx, bx, by, 28, VOID_GLOW, 0.75 if cast else 0.6)
        ring_back = _arc_pts(bx, by, 54, 11, 0.12, math.pi, 2 * math.pi)
        ring_front = _arc_pts(bx, by, 54, 11, 0.12, 0.0, math.pi)
        for col, lw in ((INK, 9), (hex2rgb("#5146d9"), 5), (light(VOID_GLOW, 0.5), 1.8)):
            stroke(ctx, lambda c: _open(c, ring_back), col, lw)
        _el(ctx, bx, by, r, r, hex2rgb("#06040e"), lw=4, hi=False, shade_amt=0)
        stroke(ctx, lambda c: ellipse_path(c, bx, by, r - 3, r - 3), VOID_GLOW, 2, 0.9)
        for col, lw in ((INK, 9), (hex2rgb("#5146d9"), 5), (light(VOID_GLOW, 0.5), 1.8)):
            stroke(ctx, lambda c: _open(c, ring_front), col, lw)
        if cast:
            for (x, y) in ((bx - 70, by + 24), (bx + 74, by + 16), (bx - 40, by + 40)):
                sparkle(ctx, x, y, 6, VOID_GLOW)
    elif h == "shell_crown":
        if ev == "A":
            for side in (-1, 1):
                wave = [(CX + side * 44, 292), (CX + side * 126, 292), (CX + side * 134, 240), (CX + side * 124, 196), (CX + side * 100, 166),
                        (CX + side * 70, 158), (CX + side * 54, 172), (CX + side * 72, 178), (CX + side * 90, 190), (CX + side * 96, 216),
                        (CX + side * 84, 246), (CX + side * 66, 270)]
                _sc(ctx, wave, light(ec, 0.12), lw=4.5, t=0.45, hi_size=0.6)
                for k in range(2):
                    stroke(ctx, lambda c, side=side, k=k: smooth_open(c, [(CX + side * (104 + k * 12), 284), (CX + side * (114 + k * 10), 240),
                                                                         (CX + side * (106 + k * 8), 204)]), light(ec2, 0.3), 3, 0.8)
                _cloud(ctx, [(CX + side * 104, 172, 10), (CX + side * 86, 162, 10), (CX + side * 66, 164, 9), (CX + side * 56, 174, 7)],
                       (1, 1, 1), lw=2.5)
        else:
            inner = light(ec2, 0.4) if ev != "B" else (1, 1, 1)
            col = ec if ev != "B" else ec2
            _ribbon(ctx, [(CX - 30, 176), (CX - 86, 148), (CX - 120, 180), (CX - 102, 226), (CX - 124, 262), (CX - 106, 288)], col, inner, 12)
            _ribbon(ctx, [(CX + 30, 176), (CX + 84, 140), (CX + 118, 170), (CX + 100, 214), (CX + 122, 246), (CX + 108, 280)], col, inner, 12)
    elif h == "ranger_visor":
        ctx.save()
        ctx.translate(CX + 40, 162)
        ctx.rotate(0.45)
        big = 1.15 if ev == "A" else 1.0
        for k in range(3):
            x = -9 + k * 9
            outlined_line(ctx, [(x, -60), (x, -92 * big)], COPPER, 3.5, 8, smooth=False)
            fl = hex2rgb("#f4f0e8") if ev == "A" else trim
            _pp(ctx, [(x, -92 * big), (x - 6, -104 * big), (x, -112 * big), (x + 6, -104 * big)], fl, lw=2.5, hi=False)
        paint(ctx, lambda c: rrect_path(c, -16, -72, 32, 100, 8), hex2rgb("#5a3a26"), lw=LW - 1, hi_size=0.5)
        for y in (-58, 6):
            flat(ctx, lambda c, y=y: rrect_path(c, -16, y, 32, 7, 2), COPPER)
        ctx.restore()
    elif h == "ice_braid" and ev == "A":
        for (bx, by, a, L, w) in ((CX - 74, 262, -math.pi / 2 - 0.5, 104, 18), (CX + 78, 258, -math.pi / 2 + 0.45, 116, 20),
                                  (CX - 40, 220, -math.pi / 2 - 0.2, 120, 16), (CX + 44, 214, -math.pi / 2 + 0.18, 112, 15)):
            _spike(ctx, bx, by, a, L, w, light(ec, 0.4))
    elif h == "oracle_veil" and ev == "A":
        _wind_band(ctx, spec, False, cast)
    elif h == "radiant_hair":
        if ev == "A":
            for side in (-1, 1):
                for k in (3, 2, 1, 0):
                    a = -math.pi / 2 + side * (0.75 + k * 0.3)
                    _leaf(ctx, CX + side * 28, 184, a, 112 - k * 14, 17 - k, (1, 1, 1) if k % 2 == 0 else hex2rgb("#fff1b8"), lw=3.5)
        glow(ctx, CX, 104, 96, ec2, 0.55)
        if ev == "A":
            for r in (70, 80):
                stroke(ctx, lambda c, r=r: ellipse_path(c, CX, 100, r, r), INK, 7)
                stroke(ctx, lambda c, r=r: ellipse_path(c, CX, 100, r, r), GOLD, 3)
            for k in range(8):
                a = k * math.pi / 4 + math.pi / 8
                sparkle(ctx, CX + math.cos(a) * 75, 100 + math.sin(a) * 75, 8, hex2rgb("#fff7cc"))


def w3_front_fx(ctx, spec, pose):
    h, ev, kind = spec["head"], spec.get("_evo"), spec["prop"]
    ec, ec2 = ELEMENT[spec["element"]]
    trim = hex2rgb(spec["trim"])
    cast = pose == "cast"
    lh, rh = hands_for(spec, pose)
    if h == "mirror_circlet" and ev == "A":
        _mirror_orbit(ctx, spec, cast, front=True)
    elif h == "conductor_hat":
        for ring in _oriane_rings(ev, cast):
            _ring_half(ctx, *ring, col=ec, front=True, glyph_col=trim)
    elif h == "rift_hood" and ev == "B":
        _portal(ctx, 46, 128, 10, 20, VOID_GLOW, rot=0.4, lw=3, glow_a=0.45)
        _portal(ctx, 276, 246, 9, 16, VOID_GLOW, rot=-0.3, lw=3, spin=1.2, glow_a=0.45)
    elif h == "shell_crown" and ev != "A":
        col = ec if ev != "B" else ec2
        _ribbon(ctx, [(CX - 108, 262), (CX - 50, 274), (CX + 20, 266), (CX + 104, 240)], col, light(ec2, 0.4) if ev != "B" else (1, 1, 1), 10)
        if ev == "B":
            for (x, y, r) in ((56, 150, 6), (270, 160, 5), (60, 220, 4), (264, 214, 5)):
                stroke(ctx, lambda c, x=x, y=y, r=r: ellipse_path(c, x, y, r, r), INK, 4.5)
                stroke(ctx, lambda c, x=x, y=y, r=r: ellipse_path(c, x, y, r, r), (1, 1, 1), 2)
    elif h == "ice_braid" and ev == "A":
        for (bx, a, L, w) in ((CX - 96, -math.pi / 2 - 0.4, 54, 12), (CX - 72, -math.pi / 2 - 0.1, 38, 9), (CX + 88, -math.pi / 2 + 0.3, 50, 11),
                              (CX + 110, -math.pi / 2 + 0.55, 34, 9)):
            _spike(ctx, bx, 290, a, L, w, light(ec, 0.55))
        if cast:
            for (x, y, a) in ((44, 110, -2.2), (40, 170, 2.6), (70, 84, -1.8)):
                _shard(ctx, x, y, a, 22, 6, light(ec, 0.5))
    elif h == "oracle_veil":
        m = build_metrics(spec["build"])
        for side in (-1, 1):
            fx = CX + side * (m["hip"] * 0.45 + 6)
            for k, (dy, a, L) in enumerate(((278, -0.5, 24), (286, -0.15, 20))):
                ang = -math.pi / 2 + side * (math.pi / 2 + a)
                _leaf(ctx, fx + side * 10, dy, ang, L, 7, (1, 1, 1) if k == 0 else light(ec2, 0.3), lw=2.5, vein=False)
        if ev == "A":
            _wind_band(ctx, spec, True, cast)
        elif ev == "B":
            for (x, y, r) in ((54, 150, 20), (266, 196, 18)):
                stroke(ctx, lambda c, x=x, y=y, r=r: c.arc(x, y, r, 0.4, 4.4), INK, 6, 0.8)
                stroke(ctx, lambda c, x=x, y=y, r=r: c.arc(x, y, r, 0.4, 4.4), hex2rgb("#5a7a74"), 3, 0.9)
    elif h == "stone_brow" and kind == "boulder_shield":
        _fist(ctx, rh[0] + 2, rh[1] - (2 if not cast else 8), cast)
    elif h == "gloom_hood" and ev == "B":
        wc = hex2rgb("#ffb8e6")
        for (x, y, r, a) in ((52, 140, 9, 1.2), (272, 214, 8, 2.0), (62, 238, 7, 0.9)):
            _wisp(ctx, x, y, r, wc, a)


# ---------------------------------------------------------------------------- heads

def w3_hair_back(ctx, spec):
    hair = hex2rgb(spec["hair"])
    main, second, trim = hex2rgb(spec["main"]), hex2rgb(spec["second"]), hex2rgb(spec["trim"])
    h, ev = spec["head"], spec.get("_evo")
    ec, ec2 = ELEMENT[spec["element"]]
    if h == "mirror_circlet":
        _sc(ctx, [(CX - 60, 96), (CX + 60, 96), (CX + 68, 150), (CX + 58, 174), (CX + 34, 162), (CX - 34, 162), (CX - 58, 174),
                  (CX - 68, 150)], hair, t=0.5)
    elif h == "conductor_hat":
        _sc(ctx, [(CX - 58, 96), (CX + 58, 96), (CX + 66, 150), (CX + 72, 208), (CX + 46, 198), (CX + 28, 178), (CX - 28, 178),
                  (CX - 46, 198), (CX - 72, 208), (CX - 66, 150)], hair, t=0.5)
    elif h == "rift_hood":
        if ev == "A":
            _sc(ctx, [(CX - 60, 96), (CX + 60, 96), (CX + 66, 142), (CX + 50, 162), (CX - 50, 162), (CX - 66, 142)], hair, t=0.5)
        else:
            _sc(ctx, [(CX - 70, 162), (CX - 74, 100), (CX - 56, 62), (CX, 50), (CX + 56, 62), (CX + 74, 100), (CX + 70, 162), (CX, 172)],
                shade(main, 0.25), t=0.5)
    elif h == "void_helm":
        glow(ctx, CX, 100, 92, VOID_GLOW, 0.3)
        rings = (76,) if ev != "A" else (76, 90)
        for r in rings:
            stroke(ctx, lambda c, r=r: ellipse_path(c, CX, 100, r, r), INK, 13)
            stroke(ctx, lambda c, r=r: ellipse_path(c, CX, 100, r, r), ec, 7)
            stroke(ctx, lambda c, r=r: ellipse_path(c, CX, 100, r, r), VOID_GLOW, 2.5)
        n = 4 if ev != "A" else 6
        for k in range(n):
            a = -math.pi / 2 + (k + 0.5) * 2 * math.pi / n
            _orb(ctx, CX + math.cos(a) * 76, 100 + math.sin(a) * 76, 7, VOID_GLOW, glow_a=0.5)
    elif h == "scribe_beret":
        if ev == "A":
            for (dx, fh, b) in ((-54, 56, -10), (-28, 74, -4), (0, 84, 0), (28, 74, 4), (54, 56, 10)):
                _flame(ctx, CX + dx, 104, fh, 22, ec, ec2, bend=b, lw=4)
        elif ev == "B":
            _sc(ctx, [(CX - 70, 164), (CX - 74, 100), (CX - 54, 62), (CX, 52), (CX + 54, 62), (CX + 74, 100), (CX + 70, 164), (CX, 174)],
                shade(second, 0.2), t=0.5)
        else:
            _sc(ctx, [(CX - 58, 96), (CX + 58, 96), (CX + 64, 148), (CX + 46, 164), (CX - 46, 164), (CX - 64, 148)], hair, t=0.5)
            for side in (-1, 1):
                _sc(ctx, [(CX + side * 52, 138), (CX + side * 68, 148), (CX + side * 74, 194), (CX + side * 64, 214), (CX + side * 52, 196),
                          (CX + side * 50, 160)], hair, lw=4.5, t=0.5)
                paint(ctx, lambda c, side=side: rrect_path(c, CX + side * 62 - 9, 156, 18, 9, 3), second, lw=3, hi=False)
    elif h == "shell_crown":
        _sc(ctx, [(CX - 58, 96), (CX + 58, 96), (CX + 70, 160), (CX + 80, 220), (CX + 60, 212), (CX + 64, 238), (CX + 36, 216),
                  (CX - 36, 216), (CX - 64, 238), (CX - 60, 212), (CX - 80, 220), (CX - 70, 160)], hair, t=0.5)
    elif h == "ranger_visor":
        if ev == "A":
            _sc(ctx, [(CX - 70, 164), (CX - 74, 100), (CX - 56, 62), (CX, 50), (CX + 56, 62), (CX + 74, 100), (CX + 70, 164), (CX, 174)],
                shade(_c(spec, "hood", "#4a3a2a"), 0.2), t=0.5)
        else:
            _sc(ctx, [(CX - 60, 96), (CX + 60, 96), (CX + 64, 140), (CX + 50, 156), (CX - 50, 156), (CX - 64, 140)], hair, t=0.5)
    elif h == "ice_braid":
        _sc(ctx, [(CX - 60, 96), (CX + 60, 96), (CX + 66, 150), (CX + 50, 170), (CX - 50, 170), (CX - 66, 150)], hair, t=0.5)
    elif h == "oracle_veil":
        veil = light(ec2, 0.35) if ev != "B" else hex2rgb("#3a4652")
        _sc(ctx, [(CX - 56, 80), (CX - 40, 44), (CX, 30), (CX + 50, 34), (CX + 96, 22), (CX + 122, 42), (CX + 98, 58), (CX + 82, 92),
                  (CX + 92, 150), (CX + 72, 204), (CX + 56, 172), (CX - 56, 172), (CX - 76, 204), (CX - 92, 150), (CX - 82, 92)],
            veil, lw=4, t=0.45, alpha=0.6 if ev != "B" else 0.85, hi=False)
        _sc(ctx, [(CX - 60, 96), (CX + 60, 96), (CX + 66, 160), (CX + 62, 228), (CX + 40, 216), (CX - 40, 216), (CX - 62, 228),
                  (CX - 66, 160)], hair, t=0.45)
    elif h == "stone_brow":
        band = _c(spec, "headband", "#c8402a")
        fl = 16 if ev == "B" else 0
        for k, dy in enumerate((0, 16)):
            _sc(ctx, [(CX - 50, 86 + dy * 0.3), (CX - 90 - fl, 96 + dy - fl * 0.6), (CX - 116 - fl * 1.4, 114 + dy * 1.4 - fl),
                      (CX - 104 - fl, 124 + dy * 1.4 - fl * 0.5), (CX - 84 - fl * 0.5, 112 + dy), (CX - 52, 104 + dy * 0.3)],
                shade(band, 0.12 * k), lw=4, t=0.45, hi=False)
    elif h == "radiant_hair":
        _sc(ctx, [(CX - 58, 96), (CX + 58, 96), (CX + 70, 150), (CX + 92, 190), (CX + 66, 190), (CX + 74, 222), (CX + 44, 204),
                  (CX + 30, 228), (CX + 10, 202), (CX - 10, 202), (CX - 30, 228), (CX - 44, 204), (CX - 74, 222), (CX - 66, 190),
                  (CX - 92, 190), (CX - 70, 150)], hair, t=0.3)
    elif h == "gloom_hood":
        hood = _c(spec, "hood", "#24202c")
        _sc(ctx, [(CX - 72, 166), (CX - 78, 100), (CX - 60, 58), (CX, 44), (CX + 60, 58), (CX + 78, 100), (CX + 72, 166), (CX, 176)],
            shade(hood, 0.2), t=0.5)


def w3_hair_front(ctx, spec):
    hair = hex2rgb(spec["hair"])
    main, second, trim = hex2rgb(spec["main"]), hex2rgb(spec["second"]), hex2rgb(spec["trim"])
    h, ev, pose = spec["head"], spec.get("_evo"), spec.get("_pose")
    ec, ec2 = ELEMENT[spec["element"]]
    downed = pose == "downed"
    if h == "mirror_circlet":
        _sc(ctx, [(CX - 64, 128), (CX - 62, 82), (CX - 34, 56), (CX + 8, 50), (CX + 46, 60), (CX + 64, 90), (CX + 64, 124), (CX + 50, 98),
                  (CX + 30, 86), (CX + 6, 96), (CX - 14, 84), (CX - 36, 100), (CX - 50, 96)], hair, t=0.45)
        _sc(ctx, [(CX - 62, 100), (CX - 50, 112), (CX - 52, 150), (CX - 62, 170), (CX - 72, 150)], hair, lw=4.5, t=0.5)
        if ev == "A":
            for (x, y, a, L, w) in ((CX - 32, 62, -math.pi / 2 - 0.35, 34, 8), (CX + 32, 62, -math.pi / 2 + 0.35, 34, 8),
                                    (CX, 52, -math.pi / 2, 46, 10)):
                _shard(ctx, x, y, a, L, w, SILVER, sheen=second)
        for col, lw in ((INK, 9), (SILVER, 4.5)):
            stroke(ctx, lambda c: smooth_open(c, [(CX - 62, 92), (CX - 32, 78), (CX, 74), (CX + 32, 78), (CX + 62, 92)]), col, lw)
        for side in (-1, 1):
            _el(ctx, CX + side * 60, 94, 7, 10, SILVER, lw=3, hi_size=0.6)
        if ev == "B":
            _orb(ctx, CX, 74, 9, ec, core=light(ec2, 0.6), glow_a=0.6)
        else:
            glow(ctx, CX, 74, 20, ec, 0.5)
            _pp(ctx, [(CX, 58), (CX + 11, 74), (CX, 90), (CX - 11, 74)], SILVER, lw=3.5, hi_size=0.6)
            stroke(ctx, lambda c: (c.move_to(CX - 4, 66), c.line_to(CX + 3, 80)), second, 2.5)
    elif h == "conductor_hat":
        _sc(ctx, [(CX - 62, 124), (CX - 62, 80), (CX - 34, 54), (CX + 8, 48), (CX + 46, 58), (CX + 64, 88), (CX + 64, 124), (CX + 52, 100),
                  (CX + 30, 84), (CX + 6, 96), (CX - 16, 82), (CX - 40, 98)], hair, t=0.45)
        if ev == "B":
            for side in (-1, 1):
                _pp(ctx, [(CX + side * 56, 80), (CX + side * 86, 54), (CX + side * 66, 96)], light(main, 0.25), lw=3.5, hi=False)
            _sc(ctx, [(CX - 64, 112), (CX - 60, 68), (CX - 26, 48), (CX + 26, 48), (CX + 60, 68), (CX + 64, 112), (CX + 42, 94), (CX - 42, 94)],
                light(main, 0.2), t=0.5, hi_size=0.7)
            stroke(ctx, lambda c: smooth_open(c, [(CX - 56, 98), (CX - 30, 86), (CX, 82), (CX + 30, 86), (CX + 56, 98)]), trim, 5)
            glow(ctx, CX, 46, 30, ec, 0.6)
            _el(ctx, CX, 46, 17, 17, light(main, 0.35), lw=4, hi=False)
            stroke(ctx, lambda c: ellipse_path(c, CX, 46, 11, 11), ec, 3)
            _glyph(ctx, CX, 46, 6, ec, 1, 2.4)
        else:
            hatc = _c(spec, "hat", "#1e1838")
            ctx.save()
            ctx.translate(CX + 18, 62)
            ctx.rotate(0.2)
            if ev == "A":
                _leaf(ctx, -14, -16, -2.1, 40, 9, ec, lw=3)
            paint(ctx, lambda c: rrect_path(c, -24, -46, 48, 48, 7), hatc, lw=LW - 1, hi_size=0.6)
            flat(ctx, lambda c: rrect_path(c, -24, -16, 48, 10, 2), trim)
            stroke(ctx, lambda c: rrect_path(c, -24, -16, 48, 10, 2), INK, 2.5)
            _glyph(ctx, 0, -32, 7, trim, 0, 2.4)
            _el(ctx, 0, 2, 46, 10, hatc, lw=LW - 1, hi=False)
            ctx.restore()
    elif h == "rift_hood":
        if ev == "A":
            _sc(ctx, [(CX - 62, 118), (CX - 64, 80), (CX - 36, 52), (CX, 46), (CX + 36, 52), (CX + 64, 80), (CX + 62, 118), (CX + 50, 92),
                      (CX + 20, 80), (CX - 20, 80), (CX - 50, 92)], hair, t=0.45)
            crown = [(CX - 42, 78), (CX - 46, 50), (CX - 28, 64), (CX - 14, 42), (CX, 60), (CX + 14, 42), (CX + 28, 64), (CX + 46, 50),
                     (CX + 42, 78), (CX, 84)]
            _pp(ctx, crown, hex2rgb("#2a2050"), lw=4.5, hi_size=0.6)
            stroke(ctx, lambda c: smooth_open(c, [(CX - 40, 74), (CX, 80), (CX + 40, 74)]), GOLD, 3)
            glow(ctx, CX, 70, 14, VOID_GLOW, 0.8)
            _pp(ctx, [(CX, 62), (CX + 6, 70), (CX, 78), (CX - 6, 70)], VOID_GLOW, lw=2.5, hi=False)
        else:
            _sc(ctx, [(CX - 50, 104), (CX - 40, 80), (CX, 72), (CX + 40, 80), (CX + 52, 104), (CX + 30, 92), (CX + 12, 100), (CX - 6, 90),
                      (CX - 26, 100)], hair, lw=4.5, t=0.4)
            hood = [(CX - 66, 130), (CX - 66, 82), (CX - 46, 50), (CX - 12, 34), (CX + 24, 24), (CX + 52, 18), (CX + 46, 36), (CX + 62, 62),
                    (CX + 68, 96), (CX + 66, 130), (CX + 50, 100), (CX + 30, 84), (CX, 78), (CX - 30, 84), (CX - 50, 100)]
            _sc(ctx, hood, main, t=0.4, hi_pos=(-0.2, -0.25))
            stroke(ctx, lambda c: smooth_open(c, [(CX - 62, 118), (CX - 46, 92), (CX, 80), (CX + 46, 92), (CX + 62, 118)]), second, 5)
            for (x, y, r) in ((CX - 30, 56, 5), (CX + 18, 44, 4), (CX - 48, 82, 3), (CX + 50, 70, 3)):
                sparkle(ctx, x, y, r, (1, 1, 1))
            if ev == "B":
                _portal(ctx, CX - 34, 66, 6, 11, VOID_GLOW, rot=0.4, lw=2.5, glow_a=0.5)
            glow(ctx, CX + 50, 22, 18, VOID_GLOW, 0.8)
            paint(ctx, lambda c: star_path(c, CX + 50, 22, 9, 4, 5), trim, lw=2.5, hi=False)
    elif h == "void_helm":
        if ev == "A":
            for side in (-1, 1):
                _pp(ctx, [(CX + side * 50, 72), (CX + side * 86, 42), (CX + side * 66, 88)], light(main, 0.2), lw=4, hi=False)
        if ev != "B":
            big = 1.25 if ev == "A" else 1.0
            _pp(ctx, [(CX - 10 * big, 54), (CX, 14 - 6 * (big - 1) * 4), (CX + 10 * big, 54)], ec, lw=4, hi=False)
        _sc(ctx, [(CX - 66, 142), (CX - 66, 76), (CX - 30, 48), (CX + 30, 48), (CX + 66, 76), (CX + 66, 142), (CX + 50, 136), (CX + 48, 100),
                  (CX, 90), (CX - 48, 100), (CX - 50, 136)], light(main, 0.14), t=0.4, hi_size=0.7)
        stroke(ctx, lambda c: smooth_open(c, [(CX - 56, 96), (CX, 84), (CX + 56, 96)]), ec, 6)
        if ev == "A":
            for side in (-1, 1):
                _sc(ctx, [(CX + side * 46, 116), (CX + side * 66, 114), (CX + side * 64, 154), (CX + side * 42, 150)], light(main, 0.2), lw=4, t=0.3, hi=False)
        if ev == "B":
            _portal(ctx, CX, 66, 10, 10, VOID_GLOW, lw=3, glow_a=0.6)
        else:
            glow(ctx, CX, 68, 16, VOID_GLOW, 0.8)
            _pp(ctx, [(CX, 58), (CX + 8, 68), (CX, 78), (CX - 8, 68)], light(VOID_GLOW, 0.3), lw=3, hi=False)
    elif h == "scribe_beret":
        if ev == "A":
            _sc(ctx, [(CX - 62, 120), (CX - 60, 80), (CX - 30, 58), (CX + 12, 54), (CX + 48, 62), (CX + 64, 92), (CX + 64, 122), (CX + 50, 98),
                      (CX + 26, 90), (CX + 4, 98), (CX - 20, 86), (CX - 44, 100)], ec, t=0.45, hi=False)
            flat(ctx, lambda c: smooth_closed(c, [(CX - 40, 74), (CX, 62), (CX + 40, 72), (CX + 20, 82), (CX - 20, 84)], 0.5), ec2, 0.9)
        elif ev == "B":
            _sc(ctx, [(CX - 62, 118), (CX - 60, 82), (CX - 30, 64), (CX + 12, 60), (CX + 48, 68), (CX + 62, 94), (CX + 62, 118), (CX + 48, 98),
                      (CX + 26, 92), (CX + 4, 100), (CX - 20, 90), (CX - 44, 100)], hair, t=0.45)
            _sc(ctx, [(CX - 66, 128), (CX - 64, 76), (CX - 24, 50), (CX + 24, 50), (CX + 64, 76), (CX + 66, 128), (CX + 48, 96), (CX, 84),
                      (CX - 48, 96)], second, t=0.5)
            stroke(ctx, lambda c: smooth_open(c, [(CX - 62, 112), (CX - 44, 92), (CX, 84), (CX + 44, 92), (CX + 62, 112)]), trim, 4)
        else:
            _sc(ctx, [(CX - 62, 120), (CX - 60, 80), (CX - 30, 56), (CX + 12, 52), (CX + 48, 62), (CX + 64, 92), (CX + 64, 122), (CX + 50, 98),
                      (CX + 26, 90), (CX + 4, 98), (CX - 20, 86), (CX - 44, 100)], hair, t=0.45)
            _leaf(ctx, CX + 30, 70, -1.0, 54, 10, PARCH, lw=3)
            _leaf(ctx, CX + 30 + math.cos(-1.0) * 34, 70 + math.sin(-1.0) * 34, -1.0, 20, 7, second, lw=2.5, vein=False)
            ctx.save()
            ctx.translate(CX - 8, 62)
            ctx.rotate(-0.16)
            _el(ctx, 0, 0, 58, 20, second, lw=LW - 1, hi_size=0.6)
            stroke(ctx, lambda c: smooth_open(c, [(-54, 6), (0, 14), (54, 6)]), shade(second, 0.35), 3)
            _el(ctx, 6, -20, 6, 5, shade(second, 0.15), lw=3, hi=False)
            ctx.restore()
        # round reading glasses
        for side in (-1, 1):
            flat(ctx, lambda c, side=side: ellipse_path(c, CX + side * 19, 118, 13, 13), (1, 1, 1), 0.2)
            stroke(ctx, lambda c, side=side: ellipse_path(c, CX + side * 19, 118, 13, 13), INK, 3.5)
        stroke(ctx, lambda c: smooth_open(c, [(CX - 6, 116), (CX, 112), (CX + 6, 116)]), INK, 3)
    elif h == "shell_crown":
        _sc(ctx, [(CX - 62, 124), (CX - 60, 80), (CX - 30, 56), (CX + 10, 52), (CX + 48, 62), (CX + 64, 92), (CX + 64, 126), (CX + 52, 104),
                  (CX + 40, 86), (CX + 22, 98), (CX + 2, 84), (CX - 20, 98), (CX - 40, 86), (CX - 52, 104)], hair, t=0.5)
        for col, lw in ((INK, 7), (hex2rgb("#fff4ea"), 3.5)):
            stroke(ctx, lambda c: smooth_open(c, [(CX - 58, 90), (CX - 30, 76), (CX, 72), (CX + 30, 76), (CX + 58, 90)]), col, lw)
        for side in (-1, 1):
            _shell(ctx, CX + side * 34, 74, 15, side * 0.5, light(trim, 0.15))
        if ev == "A":
            for side in (-1, 1):
                _spike(ctx, CX + side * 16, 62, -math.pi / 2 + side * 0.5, 26, 6, hex2rgb("#ff8a7a"), lw=3)
        _shell(ctx, CX, 64, 26, 0, trim)
        _el(ctx, CX, 70, 5, 5, hex2rgb("#fffaf4"), lw=2.5, hi=False)
    elif h == "ranger_visor":
        _sc(ctx, [(CX - 62, 112), (CX - 64, 78), (CX - 40, 52), (CX, 44), (CX + 40, 48), (CX + 70, 70), (CX + 84, 102), (CX + 70, 98),
                  (CX + 64, 120), (CX + 50, 96), (CX + 20, 88), (CX - 10, 92), (CX - 36, 88), (CX - 52, 100)], hair, t=0.4)
        if ev == "A":
            hood = _c(spec, "hood", "#4a3a2a")
            _sc(ctx, [(CX - 66, 128), (CX - 66, 80), (CX - 40, 48), (CX, 36), (CX + 40, 48), (CX + 66, 80), (CX + 66, 128), (CX + 48, 98),
                      (CX + 20, 86), (CX - 20, 86), (CX - 48, 98)], hood, t=0.4, hi_pos=(-0.2, -0.25))
            stroke(ctx, lambda c: smooth_open(c, [(CX - 62, 116), (CX - 44, 94), (CX, 88), (CX + 44, 94), (CX + 62, 116)]), second, 4)
        if ev == "B":
            for col, lw in ((INK, 12), (hex2rgb("#3a3a4a"), 6)):
                stroke(ctx, lambda c: smooth_open(c, [(CX - 62, 118), (CX, 112), (CX + 62, 118)]), col, lw)
            outlined_line(ctx, [(CX + 60, 104), (CX + 76, 66)], hex2rgb("#5a5f70"), 4, 9, smooth=False)
            glow(ctx, CX + 76, 64, 16, ec2, 0.8)
            _el(ctx, CX + 76, 64, 6, 6, ec2, lw=2.5, hi=False)
            for side in (-1, 1):
                x = CX + side * 21
                _el(ctx, x, 116, 17, 15, hex2rgb("#5a5f70"), lw=4.5, hi_size=0.6)
                lens = ec2 if not downed else grey(ec2, 0.9)
                if not downed:
                    glow(ctx, x, 116, 20, ec2, 0.5)
                _el(ctx, x, 116, 11, 10, lens, lw=3, hi=False, shade_amt=0.2)
                if downed:
                    stroke(ctx, lambda c, x=x: (c.move_to(x - 5, 111), c.line_to(x + 5, 121), c.move_to(x + 5, 111), c.line_to(x - 5, 121)), INK, 3)
                else:
                    stroke(ctx, lambda c, x=x: (c.move_to(x - 7, 116), c.line_to(x + 7, 116), c.move_to(x, 109), c.line_to(x, 123)), shade(ec2, 0.5), 1.8)
        else:
            half = 50 if ev == "A" else 60
            paint(ctx, lambda c: rrect_path(c, CX - half, 104, half * 2, 26, 12), hex2rgb("#1a1a30"), lw=4.5, hi=False, shade_amt=0)
            lens = ec2 if not downed else grey(ec2, 0.9)
            if not downed:
                glow(ctx, CX, 117, 46, ec2, 0.45)
            flat(ctx, lambda c: rrect_path(c, CX - half + 10, 111, half * 2 - 20, 12, 6), lens)
            if downed:
                stroke(ctx, lambda c: _open(c, [(CX - 20, 110), (CX - 8, 120), (CX + 4, 112), (CX + 14, 122)]), INK, 2.5)
            else:
                flat(ctx, lambda c: rrect_path(c, CX - half + 14, 113, 24, 4, 2), (1, 1, 1), 0.85)
            if ev != "A":
                for side in (-1, 1):
                    _el(ctx, CX + side * 60, 118, 9, 11, COPPER, lw=3.5, hi=False)
    elif h == "ice_braid":
        _sc(ctx, [(CX - 62, 122), (CX - 62, 80), (CX - 30, 54), (CX + 14, 50), (CX + 50, 60), (CX + 66, 90), (CX + 64, 126), (CX + 52, 96),
                  (CX + 40, 84), (CX + 20, 94), (CX - 2, 82), (CX - 28, 96), (CX - 48, 94)], hair, t=0.45)
        for i in range(7):
            x, y = CX + 48 + i * 1.8, 138 + i * 14
            _el(ctx, x, y, 13 - i * 0.7, 10, hair, lw=3.5, rot=0.45 if i % 2 else -0.45, hi=False, shade_amt=0.2)
        paint(ctx, lambda c: rrect_path(c, CX + 50, 234, 16, 9, 3), hex2rgb("#4a7fd6"), lw=3, hi=False)
        _sc(ctx, [(CX + 52, 242), (CX + 64, 242), (CX + 66, 258), (CX + 58, 264), (CX + 50, 258)], hair, lw=3, t=0.5, hi=False)
        sx, sy = CX - 40, 76
        for k in range(3):
            a = k * math.pi / 3
            stroke(ctx, lambda c, a=a: (c.move_to(sx - math.cos(a) * 9, sy - math.sin(a) * 9), c.line_to(sx + math.cos(a) * 9, sy + math.sin(a) * 9)), INK, 5)
            stroke(ctx, lambda c, a=a: (c.move_to(sx - math.cos(a) * 9, sy - math.sin(a) * 9), c.line_to(sx + math.cos(a) * 9, sy + math.sin(a) * 9)),
                   light(ec, 0.4), 2.5)
        if ev == "A":
            for (x, y, a, L, w) in ((CX - 38, 66, -math.pi / 2 - 0.4, 36, 9), (CX + 40, 68, -math.pi / 2 + 0.45, 32, 8), (CX - 18, 58, -math.pi / 2 - 0.15, 46, 10),
                                    (CX + 20, 58, -math.pi / 2 + 0.18, 44, 10), (CX, 54, -math.pi / 2, 56, 11)):
                _shard(ctx, x, y, a, L, w, light(ec, 0.45), lw=3.5, sheen=(1, 1, 1))
            for col, lw in ((INK, 8), (light(ec, 0.6), 4)):
                stroke(ctx, lambda c: smooth_open(c, [(CX - 50, 76), (CX, 68), (CX + 50, 76)]), col, lw)
        if ev == "B":
            stroke(ctx, lambda c: ellipse_path(c, CX + 19, 118, 15, 15), INK, 7)
            stroke(ctx, lambda c: ellipse_path(c, CX + 19, 118, 15, 15), BRASS, 3.5)
            flat(ctx, lambda c: ellipse_path(c, CX + 19, 118, 13, 13), light(ec, 0.5), 0.3)
            stroke(ctx, lambda c: smooth_open(c, [(CX + 34, 122), (CX + 48, 140), (CX + 44, 160)]), BRASS, 2, 0.9)
    elif h == "oracle_veil":
        _sc(ctx, [(CX - 62, 124), (CX - 60, 80), (CX - 30, 56), (CX, 66), (CX + 30, 56), (CX + 60, 80), (CX + 62, 124), (CX + 46, 96),
                  (CX + 16, 80), (CX, 90), (CX - 16, 80), (CX - 46, 96)], hair, t=0.45)
        for col, lw in ((INK, 8), (trim, 4)):
            stroke(ctx, lambda c: smooth_open(c, [(CX - 58, 88), (CX, 74), (CX + 58, 88)]), col, lw)
        _pp(ctx, [(CX, 70), (CX + 7, 80), (CX, 92), (CX - 7, 80)], ec, lw=2.5, hi_size=0.6)
        if ev == "B":
            veil = hex2rgb("#3a4652")
            _sc(ctx, [(CX - 66, 108), (CX - 60, 66), (CX - 20, 40), (CX + 20, 40), (CX + 60, 66), (CX + 66, 108), (CX + 44, 100), (CX + 22, 106),
                      (CX, 98), (CX - 22, 106), (CX - 44, 100)], veil, lw=4, t=0.35, alpha=0.88, hi=False)
            stroke(ctx, lambda c: _open(c, [(CX - 20, 52), (CX - 8, 64), (CX - 16, 70), (CX - 2, 86)]), ec, 2.5, 0.9)
        else:
            _sc(ctx, [(CX - 62, 92), (CX - 52, 58), (CX, 42), (CX + 52, 56), (CX + 62, 90), (CX + 40, 70), (CX, 62), (CX - 40, 72)],
                light(ec2, 0.35), lw=3, t=0.45, alpha=0.5, hi=False)
    elif h == "stone_brow":
        band = _c(spec, "headband", "#c8402a")
        _cloud(ctx, [(CX + 2, 64, 9), (CX + 14, 62, 8), (CX - 10, 66, 7)], LEAF, lw=2)
        stroke(ctx, lambda c: _open(c, [(CX + 22, 70), (CX + 30, 80), (CX + 26, 90)]), INK, 2.5)
        stroke(ctx, lambda c: _open(c, [(CX - 30, 70), (CX - 22, 78), (CX - 26, 86)]), INK, 2.5)
        for col, lw in ((INK, 15), (band, 9)):
            stroke(ctx, lambda c: smooth_open(c, [(CX - 64, 94), (CX, 82), (CX + 64, 94)]), col, lw)
        _el(ctx, CX - 58, 92, 9, 8, shade(band, 0.1), lw=3, hi=False)
        if ev == "B":
            glow(ctx, CX + 26, 82, 16, EMBER, 0.6)
        for side in (-1, 1):
            x = CX + side * 19
            _sc(ctx, [(x - side * 14, 106), (x + side * 2, 98), (x + side * 16, 100), (x + side * 14, 108), (x - side * 10, 112)], hair, lw=3, t=0.4, hi=False)
    elif h == "radiant_hair":
        _sc(ctx, [(CX - 62, 126), (CX - 62, 82), (CX - 32, 54), (CX + 10, 48), (CX + 48, 58), (CX + 64, 90), (CX + 64, 126), (CX + 50, 100),
                  (CX + 34, 84), (CX + 14, 98), (CX - 4, 82), (CX - 22, 96), (CX - 44, 92), (CX - 50, 104)], hair, t=0.45, hi_pos=(-0.2, -0.3))
        if ev == "B":
            for col, lw in ((INK, 9), (hex2rgb("#ffc93a"), 4.5)):
                stroke(ctx, lambda c: smooth_open(c, [(CX - 60, 92), (CX, 76), (CX + 60, 92)]), col, lw)
            for side in (-1, 1):
                _pp(ctx, [(CX + side * 56, 90), (CX + side * 82, 70), (CX + side * 64, 100)], hex2rgb("#ffc93a"), lw=3, hi=False)
            _sun(ctx, CX, 76, 11, ec, lw=2.5)
        else:
            _sun(ctx, CX + 40, 70, 10, ec, lw=2.5)
            sparkle(ctx, CX - 34, 66, 7, (1, 1, 1))
    elif h == "gloom_hood":
        hood = _c(spec, "hood", "#24202c")
        eye = hex2rgb(spec["eyes"])
        flat(ctx, lambda c: ellipse_path(c, CX, 118, 54, 40), hex2rgb("#14101a"), 0.94)
        for side in (-1, 1):
            x = CX + side * 20
            if downed:
                stroke(ctx, lambda c, x=x: (c.move_to(x - 7, 111), c.line_to(x + 7, 125), c.move_to(x + 7, 111), c.line_to(x - 7, 125)), grey(eye, 0.6), 3.5)
            else:
                glow(ctx, x, 118, 18, eye, 0.7)
                flat(ctx, lambda c, x=x: smooth_closed(c, [(x - side * 10, 114), (x + side * 9, 116), (x - side * 4, 122)], 0.5), light(eye, 0.3))
        mail = hex2rgb("#4a4652")
        _sc(ctx, [(CX - 52, 130), (CX + 52, 130), (CX + 46, 160), (CX, 170), (CX - 46, 160)], mail, lw=LW - 1, t=0.4, hi=False)
        for j, y in enumerate((140, 150, 160)):
            for i in range(7):
                x = CX - 36 + i * 12 + (6 if j % 2 else 0)
                stroke(ctx, lambda c, x=x, y=y: c.arc(x, y, 4.5, 0.1, math.pi - 0.1), light(mail, 0.3), 1.6)
        if ev == "A":
            for side in (-1, 1):
                _pp(ctx, [(CX + side * 38, 62), (CX + side * 64, 26), (CX + side * 54, 68)], BONE, lw=4, hi=False)
        tip = [(CX - 68, 134), (CX - 70, 84), (CX - 48, 50), (CX, 34), (CX + 48, 50), (CX + 70, 84), (CX + 68, 134), (CX + 52, 106),
               (CX + 26, 94), (CX, 104), (CX - 26, 94), (CX - 52, 106)]
        _sc(ctx, tip, hood, t=0.4, hi_pos=(-0.2, -0.3))
        stroke(ctx, lambda c: smooth_open(c, [(CX - 64, 122), (CX - 50, 104), (CX - 26, 92), (CX, 102), (CX + 26, 92), (CX + 50, 104), (CX + 64, 122)]),
               trim, 3, 0.85)
        if ev == "B":
            for (x, y) in ((CX - 56, 74), (CX + 44, 60)):
                stroke(ctx, lambda c, x=x, y=y: _open(c, [(x, y), (x + 6, y + 8), (x + 1, y + 14)]), INK, 3)


# ---------------------------------------------------------------------------- props

def _baton(ctx, spec, hx, hy, cast, long_):
    ec, ec2 = ELEMENT[spec["element"]]
    L = (128 if not cast else 96) if long_ else (78 if not cast else 70)
    ang = (-1.25 if long_ else -1.0) if not cast else (-1.05 if long_ else -0.75)
    ca, sa = math.cos(ang), math.sin(ang)
    tip = (hx + ca * L, hy + sa * L)
    if cast:
        sweep = (ang - 0.9, ang)
        stroke(ctx, lambda c: c.arc(hx, hy, L, *sweep), light(ec, 0.35), 8, 0.5)
        stroke(ctx, lambda c: c.arc(hx, hy, L, *sweep), ec, 3, 0.9)
        for i, t in enumerate((0.2, 0.55, 0.9)):
            a = sweep[0] + (sweep[1] - sweep[0]) * t
            _glyph(ctx, hx + math.cos(a) * L * 0.72, hy + math.sin(a) * L * 0.72, 6, INK, i, 5)
            _glyph(ctx, hx + math.cos(a) * L * 0.72, hy + math.sin(a) * L * 0.72, 6, light(ec, 0.45), i, 2.6)
    outlined_line(ctx, [(hx - ca * 12, hy - sa * 12), tip], GOLD if long_ else hex2rgb("#fff8f0"), 6 if long_ else 5, 12 if long_ else 11,
                  smooth=False)
    outlined_line(ctx, [(hx - ca * 16, hy - sa * 16), (hx + ca * 12, hy + sa * 12)], hex2rgb("#f4c8e0"), 10, 16, smooth=False)
    glow(ctx, tip[0], tip[1], 26 if cast else 18, ec, 0.8)
    if long_:
        paint(ctx, lambda c: star_path(c, tip[0], tip[1], 11, 5, 5), GOLD, lw=3, hi=False)
    sparkle(ctx, tip[0], tip[1] - (2 if long_ else 0), 9 if not long_ else 7, (1, 1, 1))


def w3_prop(ctx, spec, hand, pose, element):
    kind, ev = spec["prop"], spec.get("_evo")
    ec, ec2 = ELEMENT[element]
    fx = _c(spec, "fx_glow", "#ffffff") if spec.get("fx_glow") else ec2
    hx, hy = hand
    lh, rh = hands_for(spec, pose)
    main, second, trim = hex2rgb(spec["main"]), hex2rgb(spec["second"]), hex2rgb(spec["trim"])
    cast = pose == "cast"
    if kind == "rune_book":
        bx, by = (hx + 26, hy - 66) if not cast else (hx + 22, hy - 30)
        glow(ctx, bx, by - 6, 56 if cast else 42, ec, 0.7 if cast else 0.45)
        cover = [(bx - 36, by - 4), (bx, by + 4), (bx + 36, by - 4), (bx + 36, by + 22), (bx, by + 30), (bx - 36, by + 22)]
        _pp(ctx, cover, shade(main, 0.15), lw=4, hi=False)
        for side in (-1, 1):
            page = [(bx + side * 32, by - 10), (bx, by - 2), (bx, by + 22), (bx + side * 32, by + 14)]
            _pp(ctx, page, hex2rgb("#fff4fb"), lw=3, hi=False, shade_amt=0.12)
            for k in range(3):
                stroke(ctx, lambda c, side=side, k=k: (c.move_to(bx + side * 7, by + 4 + k * 6), c.line_to(bx + side * 26, by - 2 + k * 6)),
                       ec, 2, 0.7)
        stroke(ctx, lambda c: (c.move_to(bx, by - 2), c.line_to(bx, by + 22)), INK, 2.5)
        runes = ((-14, -24, 7), (12, -40, 8), (-4, -60, 6)) if not cast else ((-22, -26, 8), (18, -38, 9), (-6, -58, 8), (30, -62, 6))
        for i, (dx, dy, r) in enumerate(runes):
            glow(ctx, bx + dx, by + dy, r * 2.4, ec, 0.55)
            _glyph(ctx, bx + dx, by + dy, r, INK, i, 5.5)
            _glyph(ctx, bx + dx, by + dy, r, light(ec, 0.45), i, 3)
        if cast:
            sparkle(ctx, bx + 34, by - 30, 10, light(ec, 0.6))
    elif kind == "arcane_orbs":
        if not cast:
            ox, oy = hx + 4, hy - 54
            stroke(ctx, lambda c: ellipse_path(c, ox, oy, 34, 12, -0.3), light(ec, 0.4), 2.5, 0.7)
            for i, a in enumerate((0.3, 2.4, 4.4)):
                x, y = _arc_pts(ox, oy, 34, 12, -0.3, a, a, 1)[0]
                _orb(ctx, x, y, 11 - i, ec, core=light(ec2, 0.5), glow_a=0.55)
        else:
            for i, (dx, dy) in enumerate(((40, 18), (18, -50), (50, -18))):
                x, y = hx + dx, hy + dy
                stroke(ctx, lambda c, x=x, y=y: (c.move_to(hx + 4, hy), c.line_to(x, y)), light(ec, 0.4), 9, 0.5)
                stroke(ctx, lambda c, x=x, y=y: (c.move_to(hx + 4, hy), c.line_to(x, y)), ec2, 3, 0.9)
                _orb(ctx, x, y, 11, ec, core=light(ec2, 0.6), glow_a=0.75)
            sparkle(ctx, hx + 30, hy - 20, 9, (1, 1, 1))
    elif kind in ("baton", "long_baton"):
        _baton(ctx, spec, hx, hy, cast, kind == "long_baton")
    elif kind == "rune_shield":
        _baton(ctx, spec, hx, hy, cast, False)
        sx, sy = (lh[0] + 6, lh[1] - 32) if not cast else (lh[0] + 12, lh[1] - 16)
        glow(ctx, sx, sy, 72, ec, 0.55 if cast else 0.3)
        _el(ctx, sx, sy, 46, 46, light(main, 0.2), lw=LW, hi_size=0.7)
        stroke(ctx, lambda c: ellipse_path(c, sx, sy, 36, 36), INK, 10)
        stroke(ctx, lambda c: ellipse_path(c, sx, sy, 36, 36), trim, 5)
        for k in range(8):
            a = k * math.pi / 4 + math.pi / 8
            _el(ctx, sx + math.cos(a) * 41.5, sy + math.sin(a) * 41.5, 2.8, 2.8, trim, lw=1.8, hi=False, shade_amt=0)
        glow(ctx, sx, sy, 30, ec, 0.6)
        tri = [(sx, sy - 22), (sx + 19, sy + 11), (sx - 19, sy + 11)]
        stroke(ctx, lambda c: poly_path(c, tri), INK, 7)
        stroke(ctx, lambda c: poly_path(c, tri), ec, 3.5)
        stroke(ctx, lambda c: ellipse_path(c, sx, sy, 12, 12), INK, 6)
        stroke(ctx, lambda c: ellipse_path(c, sx, sy, 12, 12), light(ec, 0.45), 2.5)
        if cast:
            sparkle(ctx, sx - 24, sy - 30, 9)
    elif kind == "star_gauntlet":
        ox, oy = (hx + 6, hy - 46) if not cast else (hx + 12, hy - 46)
        r = 15 if not cast else 22
        glow(ctx, ox, oy, r * 2.8, VOID_GLOW, 0.75 if cast else 0.5)
        if cast:
            for k, rot in enumerate((-0.4, 0.5, 1.4)):
                stroke(ctx, lambda c, rot=rot, k=k: ellipse_path(c, ox, oy, r * 1.9 - k * 3, r * 0.55, rot), light(VOID_GLOW, 0.3), 2.5, 0.75)
        paint(ctx, lambda c: star_path(c, ox, oy, r * 1.25, r * 0.4, 4, rot=0.3), hex2rgb("#06040e"), lw=3.5, hi=False, shade_amt=0)
        flat(ctx, lambda c: ellipse_path(c, ox, oy, r * 0.32, r * 0.32), light(VOID_GLOW, 0.4))
        stroke(ctx, lambda c: ellipse_path(c, ox, oy, r * 1.5, r * 0.45, -0.3), VOID_GLOW, 2.5)
        for k in range(3):
            x = hx - 11 + k * 11
            _pp(ctx, [(x - 4, hy - 14), (x, hy - 27), (x + 4, hy - 14)], hex2rgb("#3a2f6a"), lw=3, hi=False)
        _sc(ctx, [(hx - 18, hy - 12), (hx - 2, hy - 20), (hx + 16, hy - 14), (hx + 20, hy + 4), (hx + 12, hy + 18), (hx - 12, hy + 18),
                  (hx - 20, hy + 4)], hex2rgb("#1a1430"), lw=4.5, t=0.4, hi_size=0.6)
        paint(ctx, lambda c: star_path(c, hx, hy + 2, 9, 3.5, 4), VOID_GLOW, lw=2, hi=False, shade_amt=0)
    elif kind == "void_daggers":
        for side, (sx, sy) in ((1, rh), (-1, lh)):
            ang = (math.pi / 2 - side * 0.55) if not cast else (-0.75 if side > 0 else -2.5)
            L = 64
            ca, sa = math.cos(ang), math.sin(ang)
            nx, ny = -sa, ca
            b = (sx + ca * 12, sy + sa * 12)
            tip = (sx + ca * L, sy + sa * L)
            glow(ctx, sx + ca * L * 0.55, sy + sa * L * 0.55, 34, VOID_GLOW, 0.6 if cast else 0.4)
            blade = [(b[0] + nx * 8, b[1] + ny * 8), (sx + ca * L * 0.55 + nx * 13, sy + sa * L * 0.55 + ny * 13), tip,
                     (sx + ca * L * 0.5 - nx * 3, sy + sa * L * 0.5 - ny * 3), (b[0] - nx * 7, b[1] - ny * 7)]
            _sc(ctx, blade, hex2rgb("#6a5ae8"), lw=4, t=0.3, hi_size=0.6)
            stroke(ctx, lambda c, b=b, tip=tip, nx=nx, ny=ny: smooth_open(c, [(b[0] + nx * 6, b[1] + ny * 6),
                                                                            (sx + ca * L * 0.55 + nx * 9, sy + sa * L * 0.55 + ny * 9), tip]),
                   VOID_GLOW, 2.5)
            outlined_line(ctx, [(b[0] + nx * 14, b[1] + ny * 14), (b[0] - nx * 14, b[1] - ny * 14)], ec, 6, 12, smooth=False)
            _el(ctx, sx - ca * 12, sy - sa * 12, 5, 5, VOID_GLOW, lw=2.5, hi=False)
    elif kind in ("portal_shield", "null_bastion"):
        _sword(ctx, hx, hy, -1.3 if not cast else -0.95, 92, hex2rgb("#3a3260"), VOID_GLOW, light(main, 0.3))
        if kind == "portal_shield":
            sx, sy = (lh[0] + 4, lh[1] - 34) if not cast else (lh[0] + 10, lh[1] - 26)
            arch = [(sx - 44, sy - 36)] + _arc_pts(sx, sy - 40, 44, 44, 0, math.pi, 2 * math.pi, 12)[1:-1] + \
                [(sx + 44, sy - 36), (sx + 44, sy + 40), (sx, sy + 70), (sx - 44, sy + 40)]
            glow(ctx, sx, sy, 56 if cast else 80, VOID_GLOW, 0.55 if cast else 0.3)
            _pp(ctx, arch, light(main, 0.12), lw=LW, hi_size=0.7)
            inner = [(sx + (x - sx) * 0.74, sy - 6 + (y - sy) * 0.74) for (x, y) in arch]
            _pp(ctx, inner, VOID_DARK, lw=3.5, hi=False, shade_amt=0)
            _portal(ctx, sx, sy - 8, 24, 40, ec, lw=0, spin=0.6 if cast else 0.0, glow_a=0.6)
            stroke(ctx, lambda c: poly_path(c, [(sx + (x - sx) * 0.87, sy - 3 + (y - sy) * 0.87) for (x, y) in arch]), trim, 2.5)
        else:
            sx, sy = (lh[0] + 14, lh[1] - 40) if not cast else (lh[0] + 30, lh[1] - 6)
            w_, t_, b_ = 56, 96, 86
            body = [(sx - w_, sy - t_ + 14), (sx - w_ + 16, sy - t_), (sx + w_ - 16, sy - t_), (sx + w_, sy - t_ + 14), (sx + w_, sy + b_ - 20),
                    (sx, sy + b_), (sx - w_, sy + b_ - 20)]
            glow(ctx, sx, sy, 76 if cast else 96, VOID_GLOW, 0.55 if cast else 0.3)
            _pp(ctx, body, light(main, 0.12), lw=LW, hi_size=0.7)
            stroke(ctx, lambda c: poly_path(c, [(sx + (x - sx) * 0.84, sy + (y - sy) * 0.84) for (x, y) in body]), ec, 4)
            for (x, y) in ((sx - 44, sy - 72), (sx + 44, sy - 72), (sx - 44, sy + 50), (sx + 44, sy + 50), (sx - 44, sy - 10), (sx + 44, sy - 10)):
                _el(ctx, x, y, 4, 4, trim, lw=2, hi=False, shade_amt=0)
            glow(ctx, sx, sy - 6, 40, VOID_GLOW, 0.7)
            for col, lw in ((INK, 11), (VOID_GLOW, 5)):
                stroke(ctx, lambda c: ellipse_path(c, sx, sy - 6, 24, 24), col, lw)
                stroke(ctx, lambda c: (c.move_to(sx - 18, sy + 12), c.line_to(sx + 18, sy - 24)), col, lw)
    elif kind == "portal_glaive":
        ang = -1.47 if not cast else -1.35
        top = _pole(ctx, hx, hy, ang, 140 if not cast else 64, 52 if not cast else 40, hex2rgb("#2a2440"), 9)
        metal = hex2rgb("#c8c4e0")
        _local(ctx, top, ang)
        glow(ctx, 0, -16, 40, VOID_GLOW, 0.75 if cast else 0.5)
        blade = [(-10, -2), (-24, -12), (-32, -32), (-26, -50), (-16, -38), (-18, -22)]
        _sc(ctx, blade, metal, lw=4, t=0.45, hi_size=0.6)
        stroke(ctx, lambda c: smooth_open(c, [(-24, -12), (-32, -32), (-26, -50)]), VOID_GLOW, 2.5)
        _pp(ctx, [(-5, -28), (0, -46), (5, -28)], metal, lw=3, hi=False)
        stroke(ctx, lambda c: ellipse_path(c, 0, -16, 14, 16), INK, 11)
        stroke(ctx, lambda c: ellipse_path(c, 0, -16, 14, 16), light(main, 0.35), 6)
        _portal(ctx, 0, -16, 10, 12, ec, lw=0, glow_a=0.0, spin=1.0 if cast else 0.0)
        ctx.restore()
    elif kind == "burning_quill":
        ang = -1.15 if not cast else -1.0
        L = 112 if not cast else 92
        ca, sa = math.cos(ang), math.sin(ang)
        nx, ny = -sa, ca
        tip = (hx + ca * L, hy + sa * L)
        if cast:
            trail = [(tip[0] - 6, tip[1] + 14), (tip[0] - 36, tip[1] + 24), (tip[0] - 52, tip[1] + 4), (tip[0] - 32, tip[1] - 8),
                     (tip[0] - 48, tip[1] - 22), (tip[0] - 70, tip[1] - 10)]
            glow(ctx, tip[0] - 36, tip[1] + 4, 44, ec2, 0.5)
            stroke(ctx, lambda c: smooth_open(c, trail), ec, 8, 0.85)
            stroke(ctx, lambda c: smooth_open(c, trail), ec2, 3)
        _leaf(ctx, hx + ca * 12, hy + sa * 12, ang, L - 10, 15, PARCH, lw=3.5, vein=True)
        _leaf(ctx, hx + ca * L * 0.62, hy + sa * L * 0.62, ang, L * 0.36, 10, second, lw=3, vein=False)
        _pp(ctx, [(hx - ca * 10 + nx * 4, hy - sa * 10 + ny * 4), (hx - ca * 28, hy - sa * 28), (hx - ca * 10 - nx * 4, hy - sa * 10 - ny * 4)],
            hex2rgb("#3a3240"), lw=2.5, hi=False)
        glow(ctx, tip[0], tip[1] - 8, 28, ec2, 0.7)
        _flame(ctx, tip[0], tip[1] + 6, 32 if cast else 28, 12, ec, ec2, bend=6)
    elif kind == "burning_scroll":
        if not cast:
            x1, x2 = lh[0] + 6, hx - 6
            ytop, ybot = 210, 256
            glow(ctx, (x1 + x2) / 2, ytop, 70, ec2, 0.5)
            for i in range(6):
                x = x1 + 12 + i * (x2 - x1 - 24) / 5.0
                _flame(ctx, x, ytop + 4, 20 + (i % 2) * 12, 9, ec, ec2, bend=(i - 2.5) * 1.5)
            paper = [(x1, ytop + 4), ((x1 + x2) / 2, ytop - 2), (x2, ytop), (x2, ybot), ((x1 + x2) / 2, ybot + 4), (x1, ybot - 2)]
            _sc(ctx, paper, PARCH, lw=4, t=0.3, hi=False, shade_amt=0.15)
            for k in range(3):
                y = ytop + 14 + k * 11
                pts = [(x1 + 14 + i * 12, y + (-3 if i % 2 else 3)) for i in range(int((x2 - x1 - 28) / 12) + 1)]
                stroke(ctx, lambda c, pts=pts: smooth_open(c, pts), ec, 2.5)
            for x in (x1, x2):
                paint(ctx, lambda c, x=x: rrect_path(c, x - 6, ytop - 8, 12, ybot - ytop + 16, 5), hex2rgb("#8a5a34"), lw=3.5, hi=False)
                for y in (ytop - 10, ybot + 10):
                    _el(ctx, x, y, 5, 4, BRASS, lw=2.5, hi=False)
        else:
            ctx.save()
            ctx.translate(hx, hy)
            ctx.rotate(0.3)
            glow(ctx, 0, -48, 70, ec2, 0.6)
            for i in range(5):
                y = -14 - i * 17
                for side in (-1, 1):
                    _flame(ctx, side * 18, y, 14 + (i % 2) * 6, 7, ec, ec2, bend=side * 4)
            _sc(ctx, [(-18, -6), (18, -6), (20, -46), (16, -88), (-16, -88), (-20, -46)], PARCH, lw=4, t=0.3, hi=False, shade_amt=0.15)
            for k in range(4):
                y = -20 - k * 16
                stroke(ctx, lambda c, y=y: smooth_open(c, [(-10, y), (-4, y - 3), (2, y + 2), (10, y - 2)]), ec, 2.5)
            for y in (-2, -92):
                paint(ctx, lambda c, y=y: rrect_path(c, -26, y - 5, 52, 10, 5), hex2rgb("#8a5a34"), lw=3.5, hi=False)
            ctx.restore()
            sparkle(ctx, hx + 48, hy - 70, 9, ec2)
    elif kind == "ember_lantern":
        if not cast:
            _lantern(ctx, hx + 2, hy + 30, 40, ec, BRASS, 0.55, chain_from=(hx, hy + 4))
        else:
            glow(ctx, hx + 6, hy + 26, 66, ec2, 0.55)
            _lantern(ctx, hx + 6, hy + 28, 44, ec, BRASS, 0.8, chain_from=(hx + 2, hy + 2))
            for (x, y, r) in ((hx - 22, hy - 4, 7), (hx + 36, hy - 10, 6), (hx + 20, hy - 30, 5), (hx - 6, hy - 26, 5)):
                sparkle(ctx, x, y, r, EMBER)
    elif kind == "water_ribbon":
        if not cast:
            pts = [(hx, hy), (hx + 26, hy - 18), (hx + 14, hy - 52), (hx + 38, hy - 76), (hx + 22, hy - 104), (hx + 40, hy - 124)]
        else:
            pts = [(hx, hy), (hx + 30, hy + 8), (hx + 52, hy - 18), (hx + 40, hy - 52), (hx + 58, hy - 78)]
        glow(ctx, pts[-1][0], pts[-1][1], 30, ec2, 0.6)
        _ribbon(ctx, pts, ec, light(ec2, 0.4), 11)
        _drop(ctx, pts[-1][0], pts[-1][1] - 4, 9, ec2)
        if cast:
            for (x, y) in ((hx + 66, hy + 10), (hx + 20, hy - 70)):
                _drop(ctx, x, y, 5, ec2)
    elif kind == "flood_trident":
        ang = -1.45 if not cast else -1.05
        top = _pole(ctx, hx, hy, ang, 150 if not cast else 70, 46, hex2rgb("#d9b46a"), 8)
        metal = hex2rgb("#e4f0ff")
        _local(ctx, top, ang)
        glow(ctx, 0, -18, 36, ec2, 0.8 if cast else 0.5)
        outlined_line(ctx, [(-20, 0), (20, 0)], metal, 8, 14, smooth=False)
        for sx_ in (-18, 18):
            outlined_line(ctx, [(sx_, 2), (sx_ * 1.05, -24)], metal, 6, 12, smooth=False)
            _pp(ctx, [(sx_ - 6, -22), (sx_ * 1.05, -36), (sx_ + 6, -22)], metal, lw=3, hi=False)
        outlined_line(ctx, [(0, 2), (0, -30)], metal, 7, 13, smooth=False)
        _pp(ctx, [(-7, -28), (0, -46), (7, -28)], metal, lw=3, hi=False)
        _el(ctx, 0, 6, 9, 7, ec, lw=3, hi=False)
        ctx.restore()
        if cast:
            for (x, y) in ((top[0] - 30, top[1] + 10), (top[0] + 22, top[1] + 30)):
                _drop(ctx, x, y, 6, ec2)
    elif kind == "heal_orb":
        ox, oy, r = (hx + 6, hy - 46, 22) if not cast else (hx + 12, hy - 40, 27)
        glow(ctx, ox, oy, r * 2.6, ec2, 0.85 if cast else 0.6)
        if cast:
            for k in range(2):
                stroke(ctx, lambda c, k=k: ellipse_path(c, ox, oy, r * (1.4 + k * 0.4), r * (1.4 + k * 0.4)), (1, 1, 1), 2.5 - k, 0.7)
        _el(ctx, ox, oy, r, r, light(ec2, 0.35), lw=4, hi_size=0.7, alpha=0.95)
        stroke(ctx, lambda c: c.arc(ox, oy, r * 0.7, 2.4, 4.4), ec, 2.5, 0.8)
        _cross(ctx, ox - 3, oy + 1, 9, (1, 1, 1), glow_a=0.0)
        _leaf(ctx, ox + 6, oy + 8, -0.6, 15, 5, LEAF_LIGHT, lw=2, vein=False)
        for (x, y, rr) in ((ox - 16, oy + 36, 5), (ox + 14, oy + 42, 4)):
            _drop(ctx, x, y, rr, ec2)
    elif kind in ("arc_bow", "heavy_bow", "split_bow"):
        heavy = kind == "heavy_bow"
        half = 104 if heavy else 92
        cxb, cyb = (lh[0] - 10, lh[1] - 52) if not cast else (lh[0] - 6, lh[1])
        if heavy:
            limb = [(cxb + 10, cyb - half), (cxb - 8, cyb - half * 0.6), (cxb - 22, cyb), (cxb - 8, cyb + half * 0.6), (cxb + 10, cyb + half)]
            nt, nb = limb[0], limb[-1]
        else:
            limb = [(cxb - 4, cyb - half - 10), (cxb + 12, cyb - half + 4), (cxb + 4, cyb - half * 0.72), (cxb - 14, cyb - half * 0.35), (cxb - 18, cyb),
                    (cxb - 14, cyb + half * 0.35), (cxb + 4, cyb + half * 0.72), (cxb + 12, cyb + half - 4), (cxb - 4, cyb + half + 10)]
            nt, nb = limb[1], limb[-2]
        pull = (cxb + 12, cyb) if not cast else (cxb + 56, cyb)

        def zig(a, b, n, amp, phase):
            out = []
            for i in range(n + 1):
                t = i / float(n)
                off = 0 if i in (0, n) else (amp if (i + phase) % 2 else -amp)
                out.append((a[0] + (b[0] - a[0]) * t + off, a[1] + (b[1] - a[1]) * t))
            return out
        if heavy:
            for p in (nt, nb):
                stroke(ctx, lambda c, p=p: (c.move_to(*p), c.line_to(*pull)), hex2rgb("#f0e8d8"), 2.5)
        else:
            offs = (0,) if kind == "arc_bow" else (-6, 6)
            for o_ in offs:
                pp = (pull[0] + o_ * (0.5 if cast else 1), pull[1] + (o_ if cast else 0))
                for (a, b, ph) in ((nt, pp, 0), (pp, nb, 1)):
                    zz = zig((a[0] + o_ * 0.4, a[1]), (b[0], b[1]), 5, 4, ph)
                    stroke(ctx, lambda c, zz=zz: _open(c, zz), ec, 5, 0.8)
                    stroke(ctx, lambda c, zz=zz: _open(c, zz), ec2, 2.2)
            glow(ctx, pull[0], pull[1], 40, ec2, 0.35)
        body = {"arc_bow": hex2rgb("#4a4f6a"), "heavy_bow": hex2rgb("#4a3020"), "split_bow": hex2rgb("#2e3350")}[kind]
        stroke(ctx, lambda c: smooth_open(c, limb), INK, 17 if heavy else 14)
        stroke(ctx, lambda c: smooth_open(c, limb), body, 10 if heavy else 8)
        if not heavy:
            stroke(ctx, lambda c: smooth_open(c, limb[1:-1]), ec2, 2.2, 0.9)
        else:
            for t in (0.2, 0.8):
                p = _along(limb, t)
                outlined_line(ctx, [(p[0] - 9, p[1]), (p[0] + 9, p[1])], BRASS, 5, 10, smooth=False)
            p = _along(limb, 0.25)
            _leaf(ctx, p[0] - 4, p[1], math.pi / 2 + 0.5, 34, 7, hex2rgb("#c8402a"), lw=2.5)
            _leaf(ctx, p[0] + 2, p[1] + 4, math.pi / 2 + 0.2, 30, 6, hex2rgb("#f4f0e8"), lw=2.5)
        grip = second if kind != "split_bow" else hex2rgb("#3a3a4a")
        paint(ctx, lambda c: rrect_path(c, cxb - 26, cyb - 13, 14, 26, 4), grip, lw=3, hi=False)
        if kind == "split_bow":
            glow(ctx, cxb - 19, cyb, 16, ec2, 0.8)
            flat(ctx, lambda c: rrect_path(c, cxb - 23, cyb - 7, 8, 14, 2), ec2)
        if cast:
            tipx = cxb - 34
            outlined_line(ctx, [(pull[0], cyb), (tipx, cyb)], COPPER, 4, 9, smooth=False)
            glow(ctx, tipx, cyb, 30, ec2, 0.8)
            _pp(ctx, [(tipx + 4, cyb - 7), (tipx - 12 - (6 if heavy else 0), cyb), (tipx + 4, cyb + 7)], COPPER, lw=3, hi=False)
            _pp(ctx, [(pull[0] - 2, cyb), (pull[0] + 8, cyb - 8), (pull[0] + 12, cyb), (pull[0] + 8, cyb + 8)], trim, lw=2.5, hi=False)
            if kind == "split_bow":
                for s_ in (-1, 1):
                    zz = [(tipx - 8, cyb), (tipx - 18, cyb + s_ * 10), (tipx - 12, cyb + s_ * 18), (tipx - 24, cyb + s_ * 30)]
                    stroke(ctx, lambda c, zz=zz: _open(c, zz), ec, 6)
                    stroke(ctx, lambda c, zz=zz: _open(c, zz), ec2, 2.5)
            else:
                zz = [(tipx - 2, cyb - 10), (tipx + 8, cyb - 18), (tipx + 2, cyb - 24), (tipx + 14, cyb - 34)]
                stroke(ctx, lambda c: _open(c, zz), ec2, 3)
    elif kind == "frost_lance":
        ang = -1.42 if not cast else -1.0
        top = _pole(ctx, hx, hy, ang, 160 if not cast else 64, 40, hex2rgb("#9fbfe0"), 8)
        ca, sa = math.cos(ang), math.sin(ang)
        nx, ny = -sa, ca
        _pp(ctx, [(hx + ca * 14 + nx * 15, hy + sa * 14 + ny * 15), (hx + ca * 40 + nx * 5, hy + sa * 40 + ny * 5),
                  (hx + ca * 40 - nx * 5, hy + sa * 40 - ny * 5), (hx + ca * 14 - nx * 15, hy + sa * 14 - ny * 15)], light(main, 0.45), lw=3.5, hi_size=0.6)
        glow(ctx, top[0] + ca * 20, top[1] + sa * 20, 40 if cast else 30, ec2, 0.8 if cast else 0.55)
        for s_ in (-1, 1):
            _shard(ctx, top[0] + nx * s_ * 10, top[1] + ny * s_ * 10, ang + s_ * 0.5, 22, 6, light(ec, 0.3))
        _shard(ctx, top[0] + ca * 14, top[1] + sa * 14, ang, 58, 12, light(ec, 0.5), lw=3.5, sheen=(1, 1, 1))
        if cast:
            for (x, y, r) in ((top[0] - 26, top[1] + 4, 7), (top[0] + 14, top[1] + 30, 6), (top[0] - 8, top[1] - 26, 5)):
                sparkle(ctx, x, y, r, (1, 1, 1))
    elif kind == "glacier_gauntlet":
        gx, gy = hx, hy
        glow(ctx, gx, gy, 54, ec, 0.75 if cast else 0.4)
        if cast:
            for k, (dx, dy, a, L) in enumerate(((44, -18, -0.5, 30), (54, 8, 0.0, 34), (40, 30, 0.5, 26), (30, -40, -1.0, 24))):
                _shard(ctx, gx + dx, gy + dy, a, L, 7, light(ec, 0.45 if k % 2 else 0.6))
        _cloud(ctx, [(gx - 32, gy - 34, 8), (gx - 40, gy - 46, 10), (gx - 34, gy - 60, 8)], (1, 1, 1), alpha=0.8, lw=2)
        outlined_line(ctx, [(gx - 22, gy - 10), (gx - 34, gy - 28)], BRASS, 6, 12, smooth=False)
        _sc(ctx, [(gx - 26, gy - 28), (gx + 22, gy - 32), (gx + 32, gy - 6), (gx + 28, gy + 24), (gx - 20, gy + 28), (gx - 32, gy + 2)],
            hex2rgb("#a8d4f0"), lw=LW, t=0.35, hi_size=0.6)
        for k in range(3):
            _spike(ctx, gx - 14 + k * 14, gy - 26, -math.pi / 2 + (k - 1) * 0.25, 18, 6, light(ec, 0.5), lw=2.5)
        paint(ctx, lambda c: rrect_path(c, gx - 30, gy + 4, 60, 10, 4), BRASS, lw=3, hi=False)
        _gear(ctx, gx + 26, gy + 18, 13, 8, BRASS, 0.2)
        _gear(ctx, gx + 6, gy + 30, 9, 6, light(BRASS, 0.25))
        glow(ctx, gx - 4, gy - 8, 16, ec2, 0.9)
        _el(ctx, gx - 4, gy - 8, 7, 7, light(ec, 0.6), lw=2.5, hi=False)
    elif kind == "chime_staff":
        ang = -1.47 if not cast else -1.3
        top = _pole(ctx, hx, hy, ang, 150 if not cast else 76, 44, PALE_WOOD, 9)
        tx, ty = top
        hook = [(tx, ty), (tx + 4, ty - 18), (tx + 22, ty - 28), (tx + 42, ty - 22), (tx + 46, ty - 10)]
        outlined_line(ctx, hook, PALE_WOOD, 8, 15)
        swing = 0.35 if cast else 0.0
        glow(ctx, tx + 24, ty + 10, 40, ec2, 0.6 if cast else 0.35)
        for k, (u, L) in enumerate(((0.32, 30), (0.52, 40), (0.72, 34), (0.92, 24))):
            px, py = _along(hook, u)
            ex, ey = px + math.sin(swing) * 8, py + 8
            stroke(ctx, lambda c, px=px, py=py, ex=ex, ey=ey: (c.move_to(px, py), c.line_to(ex, ey)), INK, 1.8)
            outlined_line(ctx, [(ex, ey), (ex + math.sin(swing) * L, ey + math.cos(swing) * L)], hex2rgb("#d8fff0"), 6, 11, smooth=False)
        _leaf(ctx, tx - 2, ty + 10, math.pi / 2 + 0.4, 30, 7, second, lw=2.5, vein=False)
        if cast:
            for k in range(3):
                r = 24 + k * 9
                stroke(ctx, lambda c, r=r: c.arc(tx + 6, ty + 24, r, -0.3, 1.2), ec, 4 - k, 0.8)
    elif kind == "wind_loom":
        ox, oy = (hx + 10, hy - 52) if not cast else (hx + 18, hy - 30)
        R = 30 if not cast else 34
        glow(ctx, ox, oy, R * 2, ec2, 0.7 if cast else 0.45)
        for k, (dx, col) in enumerate(((-12, ec), (8, light(ec2, 0.2)), (22, second))):
            pts = [(ox + dx, oy - R + 6), (ox + dx - 10, oy - R - 24), (ox + dx + 8, oy - R - 46), (ox + dx - 4 + k * 6, oy - R - 70 + k * 8)]
            if cast:
                pts = [(ox + dx, oy - R + 6), (ox + dx + 14, oy - R - 14), (ox + dx + 4 + k * 4, oy - R - 28), (ox + dx + 18 - k * 6, oy - R - 40)]
            _ribbon(ctx, pts, col, (1, 1, 1), 7)
        ctx.save()
        ctx.new_path()
        ellipse_path(ctx, ox, oy, R - 3, R - 3)
        ctx.clip()
        flat(ctx, lambda c: ellipse_path(c, ox, oy, R, R), light(ec2, 0.5), 0.5)
        for k in range(-2, 3):
            stroke(ctx, lambda c, k=k: (c.move_to(ox - R, oy + k * 10), c.line_to(ox + R, oy + k * 10 - 6)), ec, 2.5)
            stroke(ctx, lambda c, k=k: (c.move_to(ox + k * 10, oy - R), c.line_to(ox + k * 10 + 4, oy + R)), second, 2)
        ctx.restore()
        outlined_line(ctx, [(hx, hy), (ox - 4, oy + R)], PALE_WOOD, 6, 12, smooth=False)
        stroke(ctx, lambda c: ellipse_path(c, ox, oy, R, R), INK, 12)
        stroke(ctx, lambda c: ellipse_path(c, ox, oy, R, R), PALE_WOOD, 7)
    elif kind == "chain_talisman":
        tx_, ty_ = (hx + 22, hy + 30) if not cast else (hx + 34, hy - 46)
        _chain(ctx, (hx + 4, hy + 4) if not cast else (hx + 6, hy - 6), (tx_, ty_ - 18))
        for k in range(2):
            r = 26 + k * 9
            stroke(ctx, lambda c, r=r: c.arc(tx_, ty_, r, 3.6, 5.6), INK, 5, 0.7)
            stroke(ctx, lambda c, r=r: c.arc(tx_, ty_, r, 3.6, 5.6), hex2rgb("#5a7a74"), 2.5, 0.9)
        glow(ctx, tx_, ty_, 40, ec, 0.7 if cast else 0.45)
        hexa = [(tx_ + math.cos(a) * 18, ty_ + math.sin(a) * 18) for a in [k * math.pi / 3 + math.pi / 6 for k in range(6)]]
        _pp(ctx, hexa, hex2rgb("#2a3436"), lw=4, hi_size=0.5)
        stroke(ctx, lambda c: smooth_closed(c, [(tx_ - 11, ty_), (tx_, ty_ - 7), (tx_ + 11, ty_), (tx_, ty_ + 7)], 0.6), ec, 2.5)
        flat(ctx, lambda c: ellipse_path(c, tx_, ty_, 3.5, 3.5), light(ec, 0.4))
        for dx in (-6, 6):
            paint(ctx, lambda c, dx=dx: rrect_path(c, tx_ + dx - 4, ty_ + 16, 8, 18, 1.5), hex2rgb("#e8e2cc"), lw=2.5, hi=False)
            stroke(ctx, lambda c, dx=dx: (c.move_to(tx_ + dx - 2, ty_ + 22), c.line_to(tx_ + dx + 2, ty_ + 28)), hex2rgb("#c8402a"), 2)
    elif kind in ("granite_fists", "fracture_fists"):
        gc = EMBER if kind == "fracture_fists" else None
        sc_ = 0.9 if kind == "fracture_fists" else 1.0
        for (x, y) in (rh, lh):
            _fist(ctx, x + 2, y - (2 if not cast else 8), cast, gc, sc_)
        if cast:
            for (x, y, r) in ((rh[0] - 30, rh[1] - 40, 7), (rh[0] + 36, rh[1] - 30, 6), (rh[0] + 4, rh[1] - 56, 5)):
                _pp(ctx, [(x - r, y), (x, y - r), (x + r, y + 2), (x, y + r)], STONE, lw=3, hi=False)
            if gc:
                for k in range(2):
                    stroke(ctx, lambda c, k=k: c.arc(rh[0], rh[1], 46 + k * 12, -2.6, -0.6), gc, 4 - k, 0.8)
    elif kind == "boulder_shield":
        sx, sy = (lh[0] + 8, lh[1] - 30) if not cast else (lh[0] + 14, lh[1] - 22)
        glow(ctx, sx, sy, 76, ec2, 0.55 if cast else 0.25)
        _rock(ctx, sx, sy, 52, light(STONE, 0.05))
        glow(ctx, sx, sy + 4, 26, ec2, 0.75)
        rune = [(sx - 12, sy - 10), (sx, sy - 20), (sx + 12, sy - 10), (sx + 12, sy + 12), (sx, sy + 22), (sx - 12, sy + 12)]
        for col, lw in ((INK, 8), (ec2, 4)):
            stroke(ctx, lambda c: poly_path(c, rune), col, lw)
            stroke(ctx, lambda c: (c.move_to(sx, sy - 20), c.line_to(sx, sy + 22)), col, lw)
    elif kind == "songbook":
        bx, by = (hx + 2, hy - 20) if not cast else (hx + 8, hy - 2)
        glow(ctx, bx, by - 10, 50, ec2, 0.55)
        notes = ((14, -30, 7), (32, -52, 8), (8, -72, 6)) if not cast else ((22, -30, 8), (46, -42, 7), (32, -72, 9), (56, -80, 6), (10, -98, 7))
        for i, (dx, dy, s_) in enumerate(notes):
            glow(ctx, bx + dx, by + dy, s_ * 2.6, ec, 0.5)
            _note(ctx, bx + dx, by + dy, s_, GOLD if i % 2 == 0 else (1, 1, 1))
        cover = [(bx - 32, by - 2), (bx, by + 6), (bx + 32, by - 2), (bx + 32, by + 20), (bx, by + 28), (bx - 32, by + 20)]
        _pp(ctx, cover, hex2rgb("#e8a830"), lw=4, hi=False)
        for side in (-1, 1):
            page = [(bx + side * 28, by - 8), (bx, by), (bx, by + 22), (bx + side * 28, by + 14)]
            _pp(ctx, page, (1, 1, 1), lw=3, hi=False, shade_amt=0.1)
            for k in range(4):
                stroke(ctx, lambda c, side=side, k=k: (c.move_to(bx + side * 4, by + 4 + k * 4.5), c.line_to(bx + side * 24, by - 2 + k * 4.5)),
                       INK, 1.2, 0.55)
        if cast:
            sparkle(ctx, bx + 40, by - 20, 10, hex2rgb("#fff7cc"))
    elif kind == "solar_lance":
        ang = -1.45 if not cast else -1.05
        top = _pole(ctx, hx, hy, ang, 150 if not cast else 40, 44, light(GOLD, 0.35), 8)
        _local(ctx, top, ang)
        glow(ctx, 0, -24, 40, ec, 0.85 if cast else 0.55)
        if cast:
            for a in (-0.5, 0.0, 0.5):
                stroke(ctx, lambda c, a=a: (c.move_to(0, -30), c.line_to(math.sin(a) * 40, -30 - math.cos(a) * 40)), hex2rgb("#fff7cc"), 3, 0.7)
        _sc(ctx, [(0, -4), (-11, -22), (0, -56), (11, -22)], hex2rgb("#fff7cc"), lw=3.5, t=0.4, hi_size=0.6)
        stroke(ctx, lambda c: (c.move_to(0, -10), c.line_to(0, -46)), ec, 2.5)
        paint(ctx, lambda c: star_path(c, 0, 0, 17, 11, 10), GOLD, lw=3, hi=False)
        _el(ctx, 0, 0, 8, 8, hex2rgb("#fff7cc"), lw=2.5, hi=False)
        ctx.restore()
    elif kind in ("gloom_glaive", "soul_scythe"):
        scythe = kind == "soul_scythe"
        ang = (-1.5 if scythe else -1.47) if not cast else (-1.45 if scythe else -1.3)
        up = (120 if scythe else 140) if not cast else (10 if scythe else 40)
        top = _pole(ctx, hx, hy, ang, up, 56, DARK_SHAFT, 9)
        metal = hex2rgb("#c8c0d8")
        wc = hex2rgb("#ffb8e6")
        _local(ctx, top, ang)
        glow(ctx, 0, -30, 44, fx, 0.6 if cast else 0.35)
        if scythe:
            blade = [(4, 4), (-18, -12), (-36, -40), (-36, -72), (-22, -90), (-20, -64), (-12, -40), (2, -24)]
            _sc(ctx, blade, metal, lw=4.5, t=0.45, hi_size=0.6)
            stroke(ctx, lambda c: smooth_open(c, [(-18, -12), (-36, -40), (-36, -72), (-22, -90)]), fx, 3)
            _pp(ctx, [(2, -2), (22, -10), (6, -16)], metal, lw=3, hi=False)
        else:
            blade = [(2, 6), (22, -2), (34, -22), (30, -46), (16, -62), (20, -40), (14, -18), (2, -10)]
            _sc(ctx, blade, metal, lw=4, t=0.45, hi_size=0.6)
            stroke(ctx, lambda c: smooth_open(c, [(22, -2), (34, -22), (30, -46), (16, -62)]), fx, 2.5)
            _pp(ctx, [(-4, -4), (0, -30), (4, -4)], metal, lw=3, hi=False)
        _el(ctx, 0, 4, 6, 5, trim, lw=2.5, hi=False)
        ctx.restore()
        if scythe:
            for (dx, dy, r, a) in ((-36, -40, 7, 1.0), (28, -18, 6, 2.2), (-10, -86, 6, 1.6)) if not cast else \
                    ((-40, -30, 8, 0.6), (30, -10, 7, 2.4), (-22, -70, 7, 1.2), (34, -54, 6, 2.0)):
                _wisp(ctx, top[0] + dx, top[1] + dy, r, wc, a)
        else:
            lx, ly = (lh[0] - 2, lh[1] + 28) if not cast else (lh[0] - 2, lh[1] + 34)
            _lantern(ctx, lx, ly, 36, fx, hex2rgb("#5a5466"), 0.6 if not cast else 0.85, chain_from=(lh[0], lh[1] + 6))
    elif kind == "dread_shield":
        _chain(ctx, (hx, hy + 6), (hx + 4, hy + 24))
        glow(ctx, hx + 4, hy + 40, 40, fx, 0.75 if cast else 0.5)
        _skull(ctx, hx + 4, hy + 42, 15, BONE, eye=fx)
        _flame(ctx, hx + 4, hy + 24, 16, 6, fx, light(fx, 0.6), lw=2)
        sx, sy = (lh[0] + 10, lh[1] - 40) if not cast else (lh[0] + 26, lh[1] - 10)
        w_, t_, b_ = 48, 92, 84
        body = [(sx - w_, sy - t_ + 16), (sx, sy - t_), (sx + w_, sy - t_ + 16), (sx + w_, sy + b_ - 22), (sx, sy + b_), (sx - w_, sy + b_ - 22)]
        for side in (-1, 1):
            for k in range(4):
                _spike(ctx, sx + side * (w_ - 2), sy - t_ + 36 + k * 36, math.pi / 2 - side * math.pi / 2 - side * 0.2, 16, 6, BONE, lw=3)
        _spike(ctx, sx, sy - t_ + 4, -math.pi / 2, 18, 7, BONE, lw=3)
        glow(ctx, sx, sy, 70 if cast else 96, fx, 0.45 if cast else 0.2)
        _pp(ctx, body, light(main, 0.06), lw=LW, hi_size=0.7)
        stroke(ctx, lambda c: poly_path(c, [(sx + (x - sx) * 0.84, sy + (y - sy) * 0.84) for (x, y) in body]), second, 5)
        _skull(ctx, sx, sy - 10, 20, BONE, eye=fx)
        for (x, y) in ((sx - 36, sy - 60), (sx + 36, sy - 60), (sx - 36, sy + 46), (sx + 36, sy + 46)):
            _el(ctx, x, y, 4, 4, trim, lw=2, hi=False, shade_amt=0)


# ============================================================================ evolution kits (P3 visual identity)
# The Art Quality Validator flagged 20 "A" branches as visually indistinct (silhouette IoU >= 0.97 with the base
# form: only a halo, gold trim and a chest star). Each kit below changes the SILHOUETTE in a way that matches the
# branch's mechanics (Docs/Enhancement/ART_BIBLE.md §Evolution identity):
#   aegis     guardians that hold the line   -> tower shield + spiked pauldrons + crystal crest
#   archmage  big-spell casters              -> tall mantle collar + floating crystal crown + orbiting runes
#   champion  bruisers                       -> horned helm + massive pauldrons + belt plate
#   blade     assassins / archers            -> crossed blades on the back + long streaming scarf + headband tails
#   saint     healers / supports             -> sunburst disk behind the head + long stole
EVO_KITS = {
    "A": {"borun": "aegis", "eirwen": "archmage", "glacius": "aegis", "seren": "aegis", "terra": "aegis",
          "ignis": "archmage", "volt": "archmage", "voltrix": "archmage", "freya": "archmage", "tidal": "archmage",
          "zephyr": "archmage", "ashara": "champion", "cinder": "champion", "magnus": "champion",
          "kael": "blade", "nyxara": "blade", "raiden": "blade", "sylph": "blade",
          "marina": "saint", "nerissa": "saint"},
    "B": {"caelis": "saint", "zerith": "archmage"},
}
METAL = hex2rgb("#c9cfdc")


def evo_kit(hero_id, evo):
    return EVO_KITS.get(evo or "", {}).get(hero_id)


def kit_back(ctx, kit, spec, m, pose, lean, ec, ec2):
    sh = m["shoulder"]
    if kit == "aegis":
        side = -1
        x0 = CX + side * (sh + 30) + lean
        body = lambda c: rrect_path(c, x0 - 34, 168, 68, 112, 22)  # noqa: E731
        paint(ctx, body, shade(ec, 0.15), lw=LW, hi_size=0.6)
        paint(ctx, lambda c: rrect_path(c, x0 - 22, 182, 44, 84, 14), light(ec, 0.25), lw=3.5, hi=False)
        paint(ctx, lambda c: poly_path(c, [(x0, 196), (x0 + 13, 222), (x0, 250), (x0 - 13, 222)]), ec2, lw=3, hi=False)
    elif kit == "archmage":
        dark = shade(ec, 0.45)
        pts = [(CX - sh - 10 + lean, 200), (CX - sh - 44 + lean, 126), (CX - 92 + lean, 52), (CX - 30 + lean, 78), (CX + lean, 64),
               (CX + 30 + lean, 78), (CX + 92 + lean, 52), (CX + sh + 44 + lean, 126), (CX + sh + 10 + lean, 200)]
        paint(ctx, lambda c: smooth_closed(c, pts, 0.35), dark, lw=LW, hi_size=0.5)
        for s in (-1, 1):
            stroke(ctx, lambda c, s=s: smooth_open(c, [(CX + s * (sh + 2) + lean, 188), (CX + s * (sh + 16) + lean, 126), (CX + s * 54 + lean, 82)]), ec2, 3.5, 0.9)
    elif kit == "blade":
        for s in (-1, 1):
            a = -1.05 if s < 0 else -2.09
            bx, by = CX + lean + s * 10, 210
            tip = (bx + math.cos(a) * 175, by + math.sin(a) * 175)
            outlined_line(ctx, [(bx, by), tip], METAL, 12, 19, smooth=False)
            outlined_line(ctx, [(bx + math.cos(a) * 36, by + math.sin(a) * 36), (bx + math.cos(a) * 30 + 12 * s, by + math.sin(a) * 30 + 6)], ec, 7, 13, smooth=False)
        flutter = 12 if pose == "cast" else 0
        scarf = [(CX - 20 + lean, 168), (CX - 70 + lean, 176 - flutter), (CX - 112 + lean, 160 - flutter), (CX - 138 + lean, 178 - flutter * 2),
                 (CX - 116 + lean, 190 - flutter), (CX - 70 + lean, 194), (CX - 16 + lean, 186)]
        paint(ctx, lambda c: smooth_closed(c, scarf, 0.45), ec, lw=4.5, hi_size=0.5)
    elif kit == "saint":
        cx, cy = CX + lean * 0.6, 104
        ctx.save()
        ctx.new_path()
        star_path(ctx, cx, cy, 100, 70, 16, rot=0)
        ctx.set_source_rgba(*light(ec2, 0.35), 0.95)
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(4)
        ctx.stroke()
        ctx.restore()
        paint(ctx, lambda c: ellipse_path(c, cx, cy, 72, 72), light(ec, 0.5), lw=3.5, hi=False)


def kit_body(ctx, kit, spec, m, pose, lean, ec, ec2):
    sh = m["shoulder"]
    if kit in ("aegis", "champion"):
        big = kit == "champion"
        for side in (-1, 1):
            x = CX + side * sh + lean
            w = 40 if big else 32
            pts = [(x - side * 26, 158), (x + side * w, 150 if big else 160), (x + side * (w + 12), 186), (x + side * (w - 4), 206), (x - side * 18, 198)]
            paint(ctx, lambda c, pts=pts: smooth_closed(c, pts, 0.4), METAL if big else light(ec, 0.15), lw=LW, hi_size=0.6)
            spike = [(x + side * (w - 6), 160), (x + side * (w + 22), 128 if big else 138), (x + side * (w + 8), 170)]
            paint(ctx, lambda c, spike=spike: poly_path(c, spike), ec2 if big else METAL, lw=4, hi=False)
        if big:
            paint(ctx, lambda c: ellipse_path(c, CX + lean, 238, 22, 18), METAL, lw=4.5, hi_size=0.6)
            paint(ctx, lambda c: ellipse_path(c, CX + lean, 238, 9, 8), ec, lw=2.5, hi=False)
    elif kit == "saint":
        for side in (-1, 1):
            x = CX + side * 20 + lean
            stole = [(x - 9, 166), (x + 9, 166), (x + 11, 272), (x, 284), (x - 11, 272)]
            paint(ctx, lambda c, stole=stole: poly_path(c, stole), light(ec2, 0.55), lw=3.5, hi=False)
            paint(ctx, lambda c, x=x: star_path(c, x, 250, 8, 3.5, 4, rot=0), ec, lw=2, hi=False)


def kit_head(ctx, kit, spec, m, pose, lean, ec, ec2):
    hx = CX + lean * 0.6
    if kit == "aegis":
        for dx, h in ((-22, 26), (0, 40), (22, 26)):
            paint(ctx, lambda c, dx=dx, h=h: poly_path(c, [(hx + dx - 9, 66), (hx + dx, 66 - h), (hx + dx + 9, 66)]), light(ec2, 0.2), lw=3.5, hi=False)
    elif kit == "archmage":
        for i, (dx, dy, r) in enumerate(((-44, 48, 9), (-22, 30, 11), (0, 22, 14), (22, 30, 11), (44, 48, 9))):
            glow(ctx, hx + dx, dy, r * 2.4, ec2, 0.45)
            paint(ctx, lambda c, dx=dx, dy=dy, r=r: poly_path(c, [(hx + dx, dy - r * 1.6), (hx + dx + r, dy), (hx + dx, dy + r * 1.3), (hx + dx - r, dy)]),
                  light(ec, 0.15) if i % 2 else ec2, lw=3, hi=False)
        for s in (-1, 1):
            ox, oy = hx + s * 86, 128 + (-14 if s > 0 else 8)
            glow(ctx, ox, oy, 26, ec2, 0.55)
            paint(ctx, lambda c, ox=ox, oy=oy: ellipse_path(c, ox, oy, 11, 11), ec, lw=3, hi=False)
            stroke(ctx, lambda c, ox=ox, oy=oy: ellipse_path(c, ox, oy, 18, 7, 0.4), light(ec2, 0.3), 2.5, 0.9)
    elif kit == "champion":
        for s in (-1, 1):
            horn = [(hx + s * 40, 92), (hx + s * 78, 60), (hx + s * 84, 22), (hx + s * 64, 50), (hx + s * 30, 76)]
            paint(ctx, lambda c, horn=horn: smooth_closed(c, horn, 0.4), hex2rgb("#f2e6cc"), lw=4.5, hi_size=0.6)
        paint(ctx, lambda c: smooth_closed(c, [(hx - 50, 84), (hx, 62), (hx + 50, 84), (hx + 40, 96), (hx - 40, 96)], 0.4), METAL, lw=4.5, hi_size=0.6)
        paint(ctx, lambda c: poly_path(c, [(hx, 66), (hx + 9, 78), (hx, 90), (hx - 9, 78)]), ec, lw=2.5, hi=False)
    elif kit == "blade":
        stroke(ctx, lambda c: ellipse_path(c, hx, 96, 52, 10, -0.08), ec, 9)
        for t, dy in ((0, 0), (1, 14)):
            tail = [(hx + 46, 98), (hx + 82, 92 + dy), (hx + 112, 108 + dy), (hx + 128, 100 + dy)]
            outlined_line(ctx, tail, ec, 7, 12)
