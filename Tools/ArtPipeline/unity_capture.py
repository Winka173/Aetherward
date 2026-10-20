#!/usr/bin/env python3
"""Real Unity screenshots of a scripted battle (CaptureDirector in the Windows development player).

  python Tools/ArtPipeline/unity_capture.py --spec ArtProduction/manifests/capture_b01.json \
      --out ArtProduction/reviews/B01/unity/baseline --res 1920x1080 [--override ArtHandoff/returns/B01/exports/Art]

Build the player first: Unity -batchmode -quit -executeMethod Aetherward.EditorTools.AetherwardBuild.WindowsDevelopment
(-> Builds/WindowsDev/Aetherward.exe). The player plays a real Battle with the spec's roster and wave, saves
ScreenCapture PNGs (world + HUD) and capture_info.json into --out, then quits. Saves go to a throwaway folder.
Exit codes: 0 ok, 1 capture failed or shots missing, 2 usage error.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PLAYER = os.path.join(ROOT, "Builds", "WindowsDev", "Aetherward.exe")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--spec", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--res", default="1920x1080")
    p.add_argument("--override", default=None, help="Art-root-shaped folder of PNGs that replace live sprites")
    p.add_argument("--timeout", type=int, default=180)
    a = p.parse_args()
    if not os.path.exists(PLAYER):
        print("player not built: " + PLAYER)
        return 2
    w, h = a.res.lower().split("x")
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    spec = json.load(open(a.spec, encoding="utf-8"))
    spec["outDir"] = out
    tmp = os.path.join(tempfile.gettempdir(), "aw_capture_spec.json")
    json.dump(spec, open(tmp, "w", encoding="utf-8"), indent=1)
    cmd = [PLAYER, "-screen-width", w, "-screen-height", h, "-screen-fullscreen", "0", "-logFile", os.path.join(out, "player.log"),
           "-awCapture", tmp]
    if a.override:
        cmd += ["-awArtOverride", os.path.abspath(a.override)]
    print("[capture] " + " ".join(cmd), flush=True)
    try:
        r = subprocess.run(cmd, timeout=a.timeout)
    except subprocess.TimeoutExpired:
        print("[capture] timed out")
        return 1
    missing = [s["name"] for s in spec["shots"] if not os.path.exists(os.path.join(out, s["name"] + ".png"))]
    info = os.path.join(out, "capture_info.json")
    print("[capture] exit %d, missing shots: %s, info: %s" % (r.returncode, missing or "none", os.path.exists(info)))
    return 0 if r.returncode == 0 and not missing and os.path.exists(info) else 1


if __name__ == "__main__":
    sys.exit(main())
