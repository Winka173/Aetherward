#!/usr/bin/env python3
"""Rewrites waves.json applying density multipliers per wave band (keeps hand-authored structure).
Usage: tune_waves.py <count_mult_mid> <count_mult_late> <interval_mult>
Only used during balance passes; the resulting file is the source of truth."""
import json, re, sys, math
path = "Assets/_Aetherward/Resources/Content/waves.json"
src = open(path).read()
header = "".join(l for l in src.splitlines(True) if l.strip().startswith("//"))
data = json.loads("\n".join(l for l in src.splitlines() if not l.strip().startswith("//")))
mid, late, imult = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
for w in data["waves"]:
    n = w["wave"]
    m = 1.0 if n < 5 else (mid if n < 13 else late)
    for g in w["groups"]:
        if g["enemy"] in ("siegebreaker_golem", "rift_warden", "ravager"): continue
        g["count"] = max(1, int(math.ceil(g["count"] * m)))
        if n >= 5 and "interval" in g: g["interval"] = round(g["interval"] * imult, 2)
def fmt(v): return json.dumps(v, separators=(", ", ": "))
out = ["{"] + ["  " + l.strip() for l in header.splitlines()] + ['  "waves": [']
for i, w in enumerate(data["waves"]):
    groups = w.pop("groups")
    head = fmt(w)[1:-1]
    out.append("    { " + head + ",")
    out.append('      "groups": [')
    for j, g in enumerate(groups):
        out.append("        " + fmt(g) + ("," if j < len(groups) - 1 else ""))
    out.append("      ] }" + ("," if i < len(data["waves"]) - 1 else ""))
out += ["  ]", "}"]
open(path, "w").write("\n".join(out) + "\n")
print("rewrote", path)
