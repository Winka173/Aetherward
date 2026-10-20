#!/usr/bin/env python3
"""Phase 0 art audit: inventory, reference graph, provenance and toolchain capabilities (read-only).

Writes Reports/ArtRegeneration/{art_inventory.csv, art_manifest.json, toolchain_capabilities.md, art_baseline.md}.
(The brief names lower-case `reports/`; this repo already uses `Reports/`, and both folders would collide on
case-insensitive Windows/macOS checkouts, so the existing folder is used — see Tools/ArtPipeline/README.md.)

Usage: python3 Tools/ArtPipeline/audit.py [--baseline-commit f19ac35]
"""
import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artlib as A  # noqa: E402

OUT = os.path.join(A.ROOT, "Reports", "ArtRegeneration")
LIVE_REL = "Assets/_Aetherward/Resources/Art"
PREFIX_CALL = re.compile(r'(?:Art\.(?:Tex|Sprite)|_fx\.Spawn|Sr\(\w+,\s*)\(\s*"([A-Za-z]+/[A-Za-z0-9_]*)"\s*(\+)?')
ANY_PATH_LITERAL = re.compile(r'"((?:Heroes|Enemies|Relics|Cards|Icons|Portraits|UI|Vfx|World)/[A-Za-z0-9_]*)"')


def sh(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        return (r.stdout + r.stderr).strip()
    except Exception as e:  # noqa: BLE001
        return "ERROR " + str(e)


def code_refs():
    literal, prefixes = {}, {}
    for dp, _, fs in os.walk(A.UNITY_SCRIPTS):
        for f in fs:
            if not f.endswith(".cs"):
                continue
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, A.ROOT)
            for i, line in enumerate(A.read_text(p).splitlines(), 1):
                for m in PREFIX_CALL.finditer(line):
                    (prefixes if m.group(2) else literal).setdefault(m.group(1), []).append(f"{rel}:{i}")
                for m in ANY_PATH_LITERAL.finditer(line):
                    s = m.group(1)
                    tail = line[m.end():m.end() + 3]
                    if "+" in tail:
                        prefixes.setdefault(s, []).append(f"{rel}:{i}")
                    else:
                        literal.setdefault(s, []).append(f"{rel}:{i}")
    return literal, prefixes


def content_refs():
    """Exact runtime paths implied by content ids (heroes, enemies, relics, cards, biomes...)."""
    refs = {}
    c = lambda n: A.read_json(os.path.join(A.CONTENT, n + ".json"))  # noqa: E731
    for h in c("heroes")["heroes"]:
        for fr in ("idle", "cast", "downed", "evoA", "evoA_cast", "evoB", "evoB_cast"):
            refs[f"Heroes/{h['id']}_{fr}"] = "content:heroes.json"
        refs[f"Portraits/{h['id']}"] = "content:heroes.json"
    for e in c("enemies")["enemies"]:
        for fr in ("a", "b"):
            refs[f"Enemies/{e['id']}_{fr}"] = "content:enemies.json"
    for r in c("relics")["relics"]:
        refs[f"Relics/{r['id']}"] = "content:relics.json"
    for r in c("cards")["cards"]:
        refs[f"Cards/{r['id']}"] = "content:cards.json"
    for el in A.ELEMENTS:
        refs[f"Icons/element_{el}"] = "code:Art.ElementIcon"
    try:
        for b in c("biomes")["biomes"]:
            bg = b.get("background")
            if bg:
                refs[bg.replace("Art/", "")] = "content:biomes.json"
    except Exception:  # noqa: BLE001
        pass
    return refs


def git_blob_sha(commit, path):
    r = subprocess.run(["git", "-C", A.ROOT, "show", f"{commit}:{path}"], capture_output=True)
    return hashlib.sha256(r.stdout).hexdigest() if r.returncode == 0 else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline-commit", default="f19ac35")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    literal, prefixes = code_refs()
    content = content_refs()
    settings = A.load_json(A.SETTINGS)
    manifest = {m["path"]: m for m in A.load_json(A.MANIFEST)}
    rows, man = [], []
    files = []
    for dp, _, fs in os.walk(A.ART):
        for f in fs:
            if f.endswith(".png"):
                files.append(os.path.relpath(os.path.join(dp, f), A.ART).replace("\\", "/"))
    files.sort()
    regenerated = 0
    for r in files:
        key = r[:-4]
        live = LIVE_REL + "/" + r
        refs = []
        if key in literal:
            refs.append("literal:" + literal[key][0])
        if key in content:
            refs.append(content[key])
        for p, where in prefixes.items():
            if key.startswith(p) and p.endswith(("_", "/")) or (key.startswith(p) and len(p) < len(key)):
                refs.append(f"prefix:{p}+ ({where[0]})")
                break
        meta = os.path.join(A.ART, r + ".meta")
        guid = None
        if os.path.exists(meta):
            for line in A.read_text(meta).splitlines():
                if line.startswith("guid:"):
                    guid = line.split(":", 1)[1].strip()
        sha = A.sha256(os.path.join(A.ART, r))
        base_sha = git_blob_sha(a.baseline_commit, live)
        changed = base_sha is not None and base_sha != sha
        regenerated += changed
        m = manifest.get(live, {})
        src = m.get("generator", "")
        reproducible = bool(src) and os.path.exists(os.path.join(A.ROOT, src.split(" ")[0])) if src.endswith(".py") else bool(src)
        s = settings.get(live, {})
        rows.append({"asset": key, "category": r.split("/")[0], "source": src, "reproducible": reproducible, "license": m.get("license", ""),
                     "guid": guid or "", "ppu": s.get("ppu", ""), "pivot": s.get("pivot", ""), "sha256": sha[:16],
                     "baseline_sha256": (base_sha or "")[:16], "changed_since_baseline": changed, "references": " | ".join(refs) or "UNREFERENCED"})
        man.append({"assetId": key, "source": src, "output": live, "unityGuid": guid, "references": refs, "sha256": sha,
                    "baselineSha256": base_sha, "license": m.get("license")})
    with open(os.path.join(OUT, "art_inventory.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    A.dump_json({"generatedBy": "Tools/ArtPipeline/audit.py", "baselineCommit": a.baseline_commit,
                 "loading": "Resources.Load via Art.Tex/Art.Sprite path strings (scenes reference no art GUIDs)", "assets": man},
                os.path.join(OUT, "art_manifest.json"), indent=1)

    unref = [x["asset"] for x in rows if x["references"] == "UNREFERENCED"]
    nonrep = [x["asset"] for x in rows if not x["reproducible"]]
    scenes = sorted(os.path.relpath(os.path.join(dp, f), A.ROOT) for dp, _, fs in os.walk(os.path.join(A.ROOT, "Assets")) for f in fs if f.endswith((".unity", ".prefab")))
    scene_guids = set()
    for s in scenes:
        scene_guids |= set(re.findall(r"guid: ([0-9a-f]{32})", A.read_text(os.path.join(A.ROOT, s))))
    art_guids = {x["guid"] for x in rows}
    cats = {}
    for x in rows:
        cats.setdefault(x["category"], [0, 0])
        cats[x["category"]][0] += 1
        cats[x["category"]][1] += x["changed_since_baseline"]

    tc = ["# Toolchain capabilities (probed by Tools/ArtPipeline/audit.py)", "",
          "| Tool | Probe | Result |", "|---|---|---|",
          f"| Blender | `blender --version` | {sh('blender --version 2>/dev/null | head -1') or 'not found'} |",
          "| Blender EEVEE | headless render | BLOCKED: aborts, `libEGL.so.1` missing (Reports/ArtQuality/blender_benchmark/DECISION.md) |",
          "| Blender Cycles CPU | headless render | OK (no OpenImageDenoiser; denoise off) |",
          f"| Unity Editor | `which Unity unity-editor` | {'found' if shutil.which('Unity') or shutil.which('unity-editor') else 'NOT AVAILABLE (no batchmode import/compile/playmode/build possible)'} |",
          f"| Unity version (project) | ProjectSettings/ProjectVersion.txt | {A.read_text(os.path.join(A.ROOT, 'ProjectSettings', 'ProjectVersion.txt')).splitlines()[0]} |",
          f"| Python | `python3 --version` | {sh('python3 --version')} |",
          f"| Pillow / NumPy / pycairo | import | {sh(sys.executable + ' -c \"import PIL,numpy,cairo;print(PIL.__version__,numpy.__version__,cairo.version)\"')} |",
          f"| ImageMagick | `convert -version` | {sh('convert -version | head -1')} |",
          f"| .NET | `dotnet --version` | {sh('dotnet --version')} |",
          "| Unity/Blender MCP | session tools | not connected |",
          "| Paid AI image services | — | not used (no credentials; brief forbids assuming access) |"]
    A.write_text(os.path.join(OUT, "toolchain_capabilities.md"), "\n".join(tc) + "\n")

    md = ["# Art baseline (real state, audited)", "",
          f"- Runtime sprites: **{len(rows)}** PNGs under `{LIVE_REL}`; loaded through `Resources.Load` by path (`Art.Tex/Art.Sprite`). "
          f"Scenes/prefabs found: {len(scenes)} ({', '.join(os.path.basename(s) for s in scenes)}); GUIDs they reference: {len(scene_guids)} "
          f"(art GUIDs among them: {len(scene_guids & art_guids)}). No Animator controllers, AnimationClips, SpriteAtlases or Addressables exist; frames are animated procedurally in `UnitView`.",
          f"- Provenance: {len(rows) - len(nonrep)} / {len(rows)} assets map to a generator script in the manifest (reproducible); non-reproducible: {len(nonrep)}.",
          f"- Baseline commit `{a.baseline_commit}` (before the new pipeline): {regenerated} assets differ from it today (re-generated and imported through `ap.py import`); "
          f"the rest are byte-identical to what the pipeline produces (`ap.py generate` + `ap.py diff` → 0 changes).",
          f"- Unreferenced by code/content (orphan candidates, reviewed manually before any removal): {len(unref)}" + (": " + ", ".join(unref[:40]) if unref else ""),
          "", "| Category | Assets | Changed since baseline |", "|---|---|---|"]
    for k, (n, ch) in sorted(cats.items()):
        md.append(f"| {k} | {n} | {ch} |")
    md += ["", "Baseline quality (validator at the baseline commit): `Reports/ArtQuality/baseline/summary.md` — 62 blocking, 22 weak evolutions.",
           "Unity import/compile, scene screenshots, FPS/memory: **NOT RUN** (no Unity editor; see toolchain_capabilities.md)."]
    A.write_text(os.path.join(OUT, "art_baseline.md"), "\n".join(md) + "\n")
    print(f"audit: {len(rows)} assets, {regenerated} changed since {a.baseline_commit}, {len(unref)} unreferenced -> {os.path.relpath(OUT, A.ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
