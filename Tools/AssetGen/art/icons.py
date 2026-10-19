"""Icon sets built from glyphs on inked badges: elements, statuses, reactions, roles, relics, cards, UI."""
import math
import cairo
from toolkit import INK, Canvas, hex2rgb, mix, shade, light, paint, flat, stroke, glow, sparkle, ellipse_path, rrect_path, poly_path, star_path
from glyphs import glyph, FIRE, FIRE2, WATER, WATER2, BOLT, BOLT2, ICE, ICE2, WIND, WIND2, EARTH, EARTH2, GOLD, STEEL, RED, PURPLE

ELEMENT_COLORS = {
    "fire": (FIRE, FIRE2), "water": (WATER, WATER2), "lightning": (BOLT, BOLT2), "ice": (ICE, ICE2), "wind": (WIND, WIND2), "earth": (EARTH, EARTH2),
}
ELEMENT_GLYPH = {"fire": "flame", "water": "drop", "lightning": "bolt", "ice": "snowflake", "wind": "swirl", "earth": "rock"}


def badge(ctx, s, color, shape="circle"):
    m = 6
    if shape == "circle":
        path = lambda c: ellipse_path(c, s / 2, s / 2, s / 2 - m, s / 2 - m)
    elif shape == "diamond":
        path = lambda c: poly_path(c, [(s / 2, m), (s - m, s / 2), (s / 2, s - m), (m, s / 2)])
    elif shape == "hex":
        path = lambda c: poly_path(c, [(s / 2 + math.cos(a) * (s / 2 - m), s / 2 + math.sin(a) * (s / 2 - m)) for a in [k * math.pi / 3 + math.pi / 6 for k in range(6)]])
    else:
        path = lambda c: rrect_path(c, m, m, s - 2 * m, s - 2 * m, s * 0.18)
    grad = cairo.RadialGradient(s * 0.4, s * 0.3, 2, s / 2, s / 2, s * 0.6)
    grad.add_color_stop_rgb(0, *light(color, 0.25))
    grad.add_color_stop_rgb(1, *shade(color, 0.45))
    ctx.save()
    ctx.new_path()
    path(ctx)
    ctx.set_source(grad)
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(7)
    ctx.stroke()
    ctx.new_path()
    path(ctx)
    ctx.clip()
    ctx.new_path()
    path(ctx)
    ctx.set_source_rgba(*light(color, 0.5), 0.6)
    ctx.set_line_width(5)
    ctx.translate(0, 3)
    ctx.stroke()
    ctx.restore()


def element_icon(el, s=128):
    cv = Canvas(s, s)
    a, b = ELEMENT_COLORS[el]
    badge(cv.ctx, s, shade(a, 0.35), "circle")
    glyph(cv.ctx, ELEMENT_GLYPH[el], s / 2, s / 2, s * 0.68, *( (a, b) if el not in ("lightning",) else (b, None)))
    return cv


STATUS = {
    # id: (glyph, colour, glyph colour)
    "burn": ("flame", FIRE, None), "wet": ("drop", WATER, None), "charged": ("bolt", BOLT, BOLT2), "chill": ("snowflake", ICE, None),
    "windmark": ("swirl", WIND, None), "armor_crack": ("crack_shield", EARTH, STEEL), "frozen": ("snowflake", hex2rgb("#4a7fd6"), ICE2),
    "stun": ("star", hex2rgb("#8a6a2a"), GOLD), "exposed": ("target", hex2rgb("#7a2a3a"), RED), "shield": ("shield", hex2rgb("#4a7fd6"), STEEL),
    "taunt": ("eye", hex2rgb("#a0402a"), (1, 1, 1)), "slow": ("hourglass", hex2rgb("#3a6a8a"), None), "adapt": ("gem", hex2rgb("#2a8a80"), hex2rgb("#40c0b0")),
}


def status_icon(sid, s=96):
    cv = Canvas(s, s)
    g, col, gcol = STATUS[sid]
    badge(cv.ctx, s, col, "diamond" if sid in ("frozen", "stun", "exposed") else "circle")
    glyph(cv.ctx, g, s / 2, s / 2, s * 0.6, gcol)
    return cv


REACTIONS = {
    "vaporize": ("fire", "water", "cloud"), "overload": ("fire", "lightning", "burst"), "melt": ("fire", "ice", "drop"),
    "firestorm": ("fire", "wind", "swirl"), "magma": ("fire", "earth", "mountain"), "electrocharge": ("water", "lightning", "bolt"),
    "freeze": ("water", "ice", "snowflake"), "rainstorm": ("water", "wind", "cloud"), "mudfield": ("water", "earth", "hourglass"),
    "superconduct": ("lightning", "ice", "crack_shield"), "thunderstorm": ("lightning", "wind", "tower"), "magnetize": ("lightning", "earth", "magnet"),
    "blizzard": ("ice", "wind", "swirl"), "ice_spikes": ("ice", "earth", "spikes"), "sandstorm": ("wind", "earth", "hourglass"),
}
REACTION_GLYPH_COL = {
    "vaporize": (0.95, 0.95, 1.0), "overload": None, "melt": FIRE2, "firestorm": FIRE, "magma": hex2rgb("#ff7a3a"), "electrocharge": BOLT2,
    "freeze": ICE2, "rainstorm": WATER2, "mudfield": hex2rgb("#8a6a3a"), "superconduct": ICE2, "thunderstorm": STEEL, "magnetize": RED,
    "blizzard": ICE2, "ice_spikes": ICE2, "sandstorm": hex2rgb("#e0c080"),
}


def reaction_icon(rid, s=128):
    """Split badge: left/right halves in the two element colours, glyph shows the reaction's effect."""
    cv = Canvas(s, s)
    ctx = cv.ctx
    a, b, g = REACTIONS[rid]
    ca, cb = ELEMENT_COLORS[a][0], ELEMENT_COLORS[b][0]
    m = 6
    hexpath = lambda c: poly_path(c, [(s / 2 + math.cos(t) * (s / 2 - m), s / 2 + math.sin(t) * (s / 2 - m)) for t in [k * math.pi / 3 for k in range(6)]])
    ctx.save()
    ctx.new_path()
    hexpath(ctx)
    ctx.clip()
    flat(ctx, lambda c: poly_path(c, [(0, 0), (s * 0.62, 0), (s * 0.38, s), (0, s)]), shade(ca, 0.2))
    flat(ctx, lambda c: poly_path(c, [(s * 0.62, 0), (s, 0), (s, s), (s * 0.38, s)]), shade(cb, 0.2))
    glow(ctx, s / 2, s / 2, s * 0.45, (1, 1, 1), 0.25)
    ctx.restore()
    stroke(ctx, hexpath, INK, 7)
    glyph(ctx, g, s / 2, s / 2, s * 0.62, REACTION_GLYPH_COL[rid])
    return cv


ROLES = {
    "guardian": ("shield", hex2rgb("#4a6aa0"), STEEL), "mage": ("hat", hex2rgb("#5a3aa0"), PURPLE), "bruiser": ("fist", hex2rgb("#a0503a"), None),
    "assassin": ("dagger", hex2rgb("#3a3a5a"), STEEL), "support": ("dots", hex2rgb("#3a8a6a"), GOLD), "healer": ("cross", hex2rgb("#2a7a5a"), None),
    "ranger": ("bow", hex2rgb("#4a7a3a"), None), "controller": ("swirl", hex2rgb("#2a6a8a"), ICE2),
}


def role_icon(role, s=96):
    cv = Canvas(s, s)
    g, col, gcol = ROLES[role]
    badge(cv.ctx, s, col, "hex")
    glyph(cv.ctx, g, s / 2, s / 2, s * 0.6, gcol)
    return cv


FAMILY = {"combat": hex2rgb("#b04a3a"), "element": hex2rgb("#4a5ab0"), "defense": hex2rgb("#3a8a6a"), "chaos": hex2rgb("#7a3a9a")}
RARITY = {"common": hex2rgb("#a8b0c0"), "rare": hex2rgb("#4aa0ff"), "epic": hex2rgb("#b07aff"), "legendary": hex2rgb("#ffc23a"), "cursed": hex2rgb("#ff3a5a")}

RELIC_ART = {
    "arcane_echo": ("echo", PURPLE, None), "chain_conductor": ("chain", STEEL, None), "phoenix_feather": ("feather", FIRE, FIRE2),
    "frozen_crown": ("crown", ICE, (1, 1, 1)), "mana_battery": ("battery", STEEL, BOLT2), "glass_cannon": ("cannon", hex2rgb("#7a86a0"), FIRE2),
    "elemental_mirror": ("mirror", hex2rgb("#bfe8ff"), GOLD), "blood_contract": ("scroll", hex2rgb("#f4e4c4"), RED),
    "stoneheart": ("heart", hex2rgb("#9a8f86"), None), "overgrowth": ("sprout", EARTH2, None), "storm_caller": ("cloud", hex2rgb("#c8d0f0"), None),
    "last_stand": ("sword", STEEL, RED), "steam_reactor": ("gear", hex2rgb("#d0d8e8"), None), "frozen_heart": ("heart", ICE, None),
    "thunder_relay": ("tower", STEEL, BOLT2), "eternal_ember": ("flame", GOLD, FIRE), "crystal_growth": ("gem", hex2rgb("#7fe8ff"), None),
    "war_drum": ("drum", RED, STEEL), "executioners_lens": ("lens", hex2rgb("#bfe8ff"), RED), "quiver_of_gales": ("quiver", hex2rgb("#a0703f"), WIND),
    "iron_bulwark": ("shield", hex2rgb("#9aa6bc"), hex2rgb("#5a6a8a")), "alchemists_purse": ("purse", hex2rgb("#a0703f"), GOLD),
    "scholars_lens": ("book", hex2rgb("#5a7ad0"), GOLD), "spark_of_genesis": ("burst", hex2rgb("#fff0a0"), hex2rgb("#ff9a3a")),
    "sanctuary_bell": ("bell", GOLD, None), "tempest_engine": ("gear", BOLT2, None), "absolute_zero": ("snowflake", ICE, None),
    "living_monolith": ("mountain", hex2rgb("#9a8f86"), hex2rgb("#7fe8ff")),
}
RELIC_EXTRA = {"chain_conductor": "bolt", "storm_caller": "bolt", "steam_reactor": "cloud", "tempest_engine": "bolt", "absolute_zero": "crown",
               "living_monolith": "gem", "stoneheart": "rock"}


def relic_icon(rid, family, rarity, s=128):
    cv = Canvas(s, s)
    ctx = cv.ctx
    badge(ctx, s, FAMILY[family], "square")
    rc = RARITY[rarity]
    stroke(ctx, lambda c: rrect_path(c, 10, 10, s - 20, s - 20, s * 0.16), rc, 4, 0.9)
    if rarity in ("legendary", "epic"):
        glow(ctx, s / 2, s / 2, s * 0.42, rc, 0.4)
    g, col, col2 = RELIC_ART[rid]
    glyph(ctx, g, s / 2, s / 2 + 2, s * 0.62, col, col2)
    extra = RELIC_EXTRA.get(rid)
    if extra:
        glyph(ctx, extra, s * 0.74, s * 0.74, s * 0.32, BOLT2 if extra == "bolt" else None)
    return cv


CARD_TYPE = {
    "stat": ("arrow_up", hex2rgb("#3a7a5a")), "ability_modifier": ("staff", hex2rgb("#4a4aa0")), "hero_specialization": ("star", hex2rgb("#8a6a2a")),
    "team_synergy": ("dots", hex2rgb("#2a6a7a")), "element_reaction": ("burst", hex2rgb("#5a3a9a")), "mutation": ("gear", hex2rgb("#6a3a7a")),
    "cursed_pact": ("skull", hex2rgb("#7a1a2a")),
}

CARD_ART = {
    "sharpened_focus": ("sword", None), "reinforced_plate": ("shield", None), "swift_hands": ("hourglass", None), "keen_edge": ("dagger", None),
    "arcane_attunement": ("gem", None), "crystal_lattice": ("gem", hex2rgb("#7fe8ff")), "mender_training": ("cross", None), "long_reach": ("bow", None),
    "quick_cast": ("hourglass", PURPLE), "empowered_spells": ("staff", FIRE2), "echoing_chant": ("echo", None), "lingering_elements": ("swirl", PURPLE),
    "heavy_impact": ("fist", None), "overcharge": ("battery", None), "pyre_covenant": ("flame", None), "tidebound": ("drop", None),
    "storm_choir": ("bolt", None), "glacial_vow": ("snowflake", None), "gale_banner": ("swirl", None), "bedrock_oath": ("rock", None),
    "steam_engine": ("cloud", None), "static_field": ("bolt", BOLT2), "permafrost": ("spikes", None), "magma_core": ("mountain", hex2rgb("#ff7a3a")),
    "storm_front": ("cloud", hex2rgb("#a0b0d0")), "catalyst_surge": ("burst", None), "elemental_overflow": ("echo", GOLD), "overheal_barrier": ("shield", hex2rgb("#7cff9a")),
    "bounty_hunter": ("coin", None), "fortress_doctrine": ("tower", STEEL), "pact_of_cinders": ("flame", RED), "pact_of_hunger": ("skull", None),
    "pact_of_haste": ("hourglass", RED), "pact_of_glass": ("gem", RED),
}


def card_icon(cid, ctype, rarity, s=160):
    cv = Canvas(s, s)
    ctx = cv.ctx
    g0, bg = CARD_TYPE[ctype]
    badge(ctx, s, bg, "circle")
    stroke(ctx, lambda c: ellipse_path(c, s / 2, s / 2, s / 2 - 14, s / 2 - 14), RARITY[rarity], 4, 0.85)
    art = CARD_ART.get(cid)
    if art:
        glyph(ctx, art[0], s / 2, s / 2, s * 0.58, art[1])
    else:
        glyph(ctx, g0, s / 2, s / 2, s * 0.58)
    return cv


UI_ICONS = {
    "gold": ("coin", None, None), "essence": ("gem", PURPLE, None), "crystal": ("gem", hex2rgb("#7fe8ff"), None), "wave": ("skull", None, None),
    "reroll": None, "pause": None, "play": None, "speed": None, "settings": ("gear", None, None), "codex": ("book", None, None),
    "history": ("scroll", None, None), "lock": None, "close": None, "check": None, "star": ("star", None, None), "trophy": ("crown", None, None),
    "heart": ("heart", None, None), "xp": ("star", hex2rgb("#7cff9a"), None), "sword": ("sword", None, None), "shield": ("shield", None, None),
    "leak": ("target", None, None), "evolve": ("burst", GOLD, PURPLE), "auto": ("gear", hex2rgb("#7cff9a"), None),
}


def ui_icon(name, s=96):
    cv = Canvas(s, s)
    ctx = cv.ctx
    spec = UI_ICONS[name]
    if spec is not None:
        glyph(ctx, spec[0], s / 2, s / 2, s * 0.86, spec[1], spec[2])
        return cv
    white = (0.97, 0.97, 1.0)
    if name == "pause":
        for x in (s * 0.3, s * 0.58):
            paint(ctx, lambda c, x=x: rrect_path(c, x, s * 0.2, s * 0.14, s * 0.6, 5), white, lw=5, hi=False)
    elif name == "play":
        paint(ctx, lambda c: poly_path(c, [(s * 0.3, s * 0.2), (s * 0.78, s * 0.5), (s * 0.3, s * 0.8)]), white, lw=5, hi=False)
    elif name == "speed":
        for x in (s * 0.18, s * 0.48):
            paint(ctx, lambda c, x=x: poly_path(c, [(x, s * 0.22), (x + s * 0.34, s * 0.5), (x, s * 0.78)]), white, lw=5, hi=False)
    elif name == "reroll":
        for k, a0 in enumerate((0.2, 3.34)):
            stroke(ctx, lambda c, a0=a0: c.arc(s / 2, s / 2, s * 0.28, a0, a0 + 2.4), INK, 15)
            stroke(ctx, lambda c, a0=a0: c.arc(s / 2, s / 2, s * 0.28, a0, a0 + 2.4), white, 8)
            ax, ay = s / 2 + math.cos(a0 + 2.4) * s * 0.28, s / 2 + math.sin(a0 + 2.4) * s * 0.28
            d = a0 + 2.4 + math.pi / 2
            paint(ctx, lambda c, ax=ax, ay=ay, d=d: poly_path(c, [(ax + math.cos(d) * 16, ay + math.sin(d) * 16), (ax + math.cos(d - 2.1) * 13, ay + math.sin(d - 2.1) * 13),
                                                                   (ax + math.cos(d + 2.1) * 13, ay + math.sin(d + 2.1) * 13)]), white, lw=4, hi=False)
    elif name == "lock":
        stroke(ctx, lambda c: c.arc(s / 2, s * 0.42, s * 0.18, math.pi, 0), INK, 16)
        stroke(ctx, lambda c: c.arc(s / 2, s * 0.42, s * 0.18, math.pi, 0), STEEL, 9)
        paint(ctx, lambda c: rrect_path(c, s * 0.24, s * 0.42, s * 0.52, s * 0.38, 8), GOLD, lw=5)
    elif name == "close":
        for a in (0.785, -0.785):
            ctx.save()
            ctx.translate(s / 2, s / 2)
            ctx.rotate(a)
            paint(ctx, lambda c: rrect_path(c, -s * 0.36, -s * 0.08, s * 0.72, s * 0.16, 6), white, lw=5, hi=False)
            ctx.restore()
    elif name == "check":
        stroke(ctx, lambda c: (c.move_to(s * 0.2, s * 0.52), c.line_to(s * 0.42, s * 0.74), c.line_to(s * 0.8, s * 0.28)), INK, 20)
        stroke(ctx, lambda c: (c.move_to(s * 0.2, s * 0.52), c.line_to(s * 0.42, s * 0.74), c.line_to(s * 0.8, s * 0.28)), hex2rgb("#7cff9a"), 11)
    return cv
