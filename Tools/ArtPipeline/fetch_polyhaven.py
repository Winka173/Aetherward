#!/usr/bin/env python3
"""Fetch the CC0 Poly Haven textures/models the environment renders use (cached, md5-checked).

  python Tools/ArtPipeline/fetch_polyhaven.py [--res 2k]

Files go to ArtCache/polyhaven/<id>/ (git-ignored, re-downloadable). Every asset is recorded with its
source URL, author and licence in ArtProduction/REFERENCE_MANIFEST.json. Poly Haven publishes all assets as CC0.
"""
import argparse
import hashlib
import json
import os
import sys
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CACHE = os.path.join(ROOT, "ArtCache", "polyhaven")   # not Temp/: Unity deletes Temp/ when the Editor quits
MANIFEST = os.path.join(ROOT, "ArtProduction", "REFERENCE_MANIFEST.json")
TEXTURES = ["burned_ground_01", "aerial_ground_rock", "cobblestone_large_01", "castle_wall_slates", "broken_wall",
            "mossy_rock", "cliff_side", "dark_rock"]
TEX_MAPS = {"Diffuse": "diff", "nor_gl": "nor_gl", "Rough": "rough", "Displacement": "disp"}
MODELS = ["gothic_statue", "rock_moss_set_01", "rock_moss_set_02", "namaqualand_boulder_02", "namaqualand_boulder_05",
          "dead_tree_trunk_02", "dead_quiver_trunk", "root_cluster_01", "stone_fire_pit", "tree_stump_01"]
API = "https://api.polyhaven.com"


def get_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "aetherward-art-pipeline"}), timeout=60) as r:
        return json.load(r)


def download(url, dst, md5=None):
    if os.path.exists(dst) and (md5 is None or hashlib.md5(open(dst, "rb").read()).hexdigest() == md5):
        return False
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "aetherward-art-pipeline"}), timeout=300) as r:
        data = r.read()
    if md5 and hashlib.md5(data).hexdigest() != md5:
        raise RuntimeError("md5 mismatch for " + url)
    open(dst, "wb").write(data)
    return True


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--res", default="2k")
    a = p.parse_args()
    records = []
    for tid in TEXTURES:
        files = get_json("%s/files/%s" % (API, tid))
        info = get_json("%s/info/%s" % (API, tid))
        out = {}
        for key, short in TEX_MAPS.items():
            fmt = "jpg" if "jpg" in files[key][a.res] else "png"
            f = files[key][a.res][fmt]
            dst = os.path.join(CACHE, tid, "%s_%s.%s" % (tid, short, fmt))
            fresh = download(f["url"], dst, f.get("md5"))
            out[short] = os.path.relpath(dst, ROOT).replace("\\", "/")
            print(("got  " if fresh else "have ") + out[short], flush=True)
        records.append({"id": tid, "type": "texture", "files": out, "url": "https://polyhaven.com/a/" + tid,
                        "authors": sorted(info.get("authors", {})), "license": "CC0 1.0 (Poly Haven)"})
    for mid in MODELS:
        files = get_json("%s/files/%s" % (API, mid))
        info = get_json("%s/info/%s" % (API, mid))
        b = files["blend"][a.res]["blend"]
        base = os.path.join(CACHE, mid)
        dst = os.path.join(base, os.path.basename(b["url"]))
        download(b["url"], dst, b.get("md5"))
        for rel, inc in b.get("include", {}).items():
            download(inc["url"], os.path.join(base, rel), inc.get("md5"))
        print("have " + os.path.relpath(dst, ROOT), flush=True)
        records.append({"id": mid, "type": "model", "files": {"blend": os.path.relpath(dst, ROOT).replace("\\", "/")},
                        "url": "https://polyhaven.com/a/" + mid, "authors": sorted(info.get("authors", {})), "license": "CC0 1.0 (Poly Haven)"})
    json.dump({"_doc": "Third-party inputs used by the art pipeline. Only CC0 sources; files are cached under ArtCache/ and re-fetched by "
                       "Tools/ArtPipeline/fetch_polyhaven.py.", "assets": records}, open(MANIFEST, "w", encoding="utf-8"), indent=1)
    print("manifest -> " + os.path.relpath(MANIFEST, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
