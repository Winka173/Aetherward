#!/usr/bin/env python3
"""Fetch the CC0 ambientCG materials the environment renders use (cached), and record them.

  python Tools/ArtPipeline/fetch_ambientcg.py [--res 2K]

Files go to ArtCache/ambientcg/<AssetId>/ (git-ignored; Unity deletes Temp/ on quit, so never there). Each material is
appended to ArtProduction/REFERENCE_MANIFEST.json with its URL and the CC0 licence (ambientCG publishes everything CC0).
"""
import argparse
import io
import json
import os
import sys
import urllib.request
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CACHE = os.path.join(ROOT, "ArtCache", "ambientcg")
MANIFEST = os.path.join(ROOT, "ArtProduction", "REFERENCE_MANIFEST.json")
MATERIALS = ["Snow015", "Snow010A", "Ice002", "Ice003", "Lava004", "Lava001", "Rock064", "Rock058", "Ground068",
             "Bricks097", "Marble012", "Moss002", "PavingStones138"]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--res", default="2K")
    a = p.parse_args()
    man = json.load(open(MANIFEST, encoding="utf-8")) if os.path.exists(MANIFEST) else {"assets": []}
    known = {r["id"] for r in man["assets"]}
    for mid in MATERIALS:
        out = os.path.join(CACHE, mid)
        if not (os.path.isdir(out) and os.listdir(out)):
            url = "https://ambientcg.com/get?file=%s_%s-JPG.zip" % (mid, a.res)
            req = urllib.request.Request(url, headers={"User-Agent": "aetherward-art-pipeline"})
            data = urllib.request.urlopen(req, timeout=300).read()
            os.makedirs(out, exist_ok=True)
            zipfile.ZipFile(io.BytesIO(data)).extractall(out)
            print("got  " + mid, flush=True)
        else:
            print("have " + mid, flush=True)
        if mid not in known:
            files = sorted(f for f in os.listdir(out) if f.lower().endswith((".jpg", ".png")))
            man["assets"].append({"id": mid, "type": "texture", "source": "ambientCG", "url": "https://ambientcg.com/view?id=" + mid,
                                  "files": {f: os.path.relpath(os.path.join(out, f), ROOT).replace("\\", "/") for f in files},
                                  "license": "CC0 1.0 (ambientCG)"})
    json.dump(man, open(MANIFEST, "w", encoding="utf-8"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
