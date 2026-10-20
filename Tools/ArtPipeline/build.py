#!/usr/bin/env python3
"""Batch entry point for the art pipeline (wraps ap.py stages with scope, cache and batch records).

  python3 Tools/ArtPipeline/build.py --scope golden --quality release [--import]
  python3 Tools/ArtPipeline/build.py --scope all --quality release --incremental [--import]
  python3 Tools/ArtPipeline/build.py --scope characters --dry-run
  python3 Tools/ArtPipeline/build.py --scope all --force --import

Stages: generate (Tools/AssetGen/art, deterministic) -> scope prune -> validate (blocking = stop) -> diff
(before/after sheets) -> [import: backup + journal + atomic replace + gen_meta --refresh-textures, rollback on
failure]. Each run appends a record to Reports/ArtRegeneration/batches.json and writes a log under
Reports/ArtRegeneration/logs/. The live project is only touched with --import, and only after validation passes.

--quality: "release" (default) or "preview". Only Blender renders use it (48 vs 8 samples); the 2D vector
generator has one quality level (it is resolution-exact), so 2D outputs are identical in both modes.
"""
import argparse
import datetime
import fnmatch
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artlib as A  # noqa: E402

SCOPES = {
    "golden": ["Heroes/ignis_*", "World/crystal_*", "Enemies/nyxhollow_*", "Vfx/telegraph*", "Icons/status_*"],
    "characters": ["Heroes/*", "Enemies/*", "Portraits/*"],
    "environment_items": ["World/*", "Relics/*", "Cards/*"],
    "ui_icons": ["UI/*", "Icons/*"],
    "vfx": ["Vfx/*"],
    "all": ["*"],
}
OUT = os.path.join(A.ROOT, "Reports", "ArtRegeneration")
BATCHES = os.path.join(OUT, "batches.json")
INPUT_GLOBS = ["Tools/AssetGen/art/*.py", "Assets/_Aetherward/Resources/Content/*.json", "Tools/ArtPipeline/art_spec.json"]


def input_hash():
    import glob
    h = hashlib.sha256()
    for g in INPUT_GLOBS:
        for p in sorted(glob.glob(os.path.join(A.ROOT, g))):
            h.update(os.path.relpath(p, A.ROOT).encode())
            with open(p, "rb") as f:
                h.update(f.read())
    h.update(sys.version.split()[0].encode())
    return h.hexdigest()


def in_scope(rel, scope):
    return any(fnmatch.fnmatch(rel, pat) for pat in SCOPES[scope])


def run(cmd, log):
    t = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True)
    log.write(f"$ {' '.join(cmd)}\n{r.stdout}{r.stderr}\n[exit {r.returncode} in {time.time() - t:.1f}s]\n")
    log.flush()
    return r


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--scope", default="all", choices=sorted(SCOPES))
    p.add_argument("--quality", default="release", choices=["release", "preview"])
    p.add_argument("--incremental", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--import", dest="do_import", action="store_true")
    a = p.parse_args(argv)
    stage = os.path.join(A.ROOT, "Temp", "ArtStage", a.scope)
    cache_file = os.path.join(stage, ".cache.json")
    ih = input_hash()
    cached = A.load_json(cache_file) if os.path.exists(cache_file) else {}
    cache_hit = a.incremental and not a.force and cached.get("inputHash") == ih and os.path.isdir(os.path.join(stage, "Art"))
    os.makedirs(os.path.join(OUT, "logs"), exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = os.path.join(OUT, "logs", f"build_{a.scope}_{stamp}.log")
    plan = {"scope": a.scope, "patterns": SCOPES[a.scope], "quality": a.quality, "inputHash": ih[:16], "cacheHit": cache_hit, "import": a.do_import}
    if a.dry_run:
        print("[build] DRY RUN " + json.dumps(plan))
        return 0
    rec = dict(plan, started=stamp, log=os.path.relpath(log_path, A.ROOT), planned=0, generated=0, validatedBlocking=None,
               changed=0, imported=0, usedInGame=0, blocked=[], rolledBack=False, exit=0)
    ap = [sys.executable, os.path.join(A.HERE, "ap.py")]
    with open(log_path, "w", encoding="utf-8") as log:
        log.write(json.dumps(plan) + "\n")
        if cache_hit:
            log.write("[cache] inputs unchanged since the last build of this scope: generation skipped\n")
        else:
            r = run(ap + ["generate", "--stage", stage], log)
            if r.returncode:
                rec.update(exit=2, blocked=["generate failed (see log)"])
                return finish(rec, 2)
            # Prune to scope (generation is all-or-nothing; staging per scope keeps scopes independent).
            art = os.path.join(stage, "Art")
            removed = 0
            for dp, _, fs in os.walk(art):
                for f in fs:
                    rel = os.path.relpath(os.path.join(dp, f), art).replace("\\", "/")
                    if f.endswith(".png") and not in_scope(rel, a.scope):
                        os.remove(os.path.join(dp, f))
                        removed += 1
            for name in ("import_settings.json", "manifest.json"):
                pth = os.path.join(stage, name)
                data = A.load_json(pth)
                live = "Assets/_Aetherward/Resources/Art/"
                if isinstance(data, dict):
                    data = {k: v for k, v in data.items() if in_scope(k[len(live):], a.scope)}
                else:
                    data = [m for m in data if in_scope(m["path"][len(live):], a.scope)]
                A.dump_json(data, pth, indent=1, sort_keys=isinstance(data, dict))
            log.write(f"[scope] pruned {removed} out-of-scope outputs\n")
            A.dump_json(None if a.scope == "all" else SCOPES[a.scope], os.path.join(stage, ".scope.json"))
            A.dump_json({"inputHash": ih, "builtAt": stamp}, cache_file)
        staged = [f for f in _pngs(os.path.join(stage, "Art"))]
        rec["planned"] = len([r for r in _pngs(A.ART) if in_scope(r, a.scope)])
        rec["generated"] = len(staged)
        missing = sorted(set(r for r in _pngs(A.ART) if in_scope(r, a.scope)) - set(staged))
        if missing:
            rec["blocked"] += [f"no generator output for {m} (live file kept)" for m in missing]
        r = run(ap + ["validate", "--stage", stage], log)
        rep = A.load_json(os.path.join(stage, "report", "report.json"))
        rec["validatedBlocking"] = rep["summary"]["blocking"]
        rec["warnings"] = rep["summary"]["warnings"]
        if r.returncode:
            rec.update(exit=1)
            log.write("[validate] blocking defects: nothing imported\n")
            return finish(rec, 1)
        r = run(ap + ["diff", "--stage", stage], log)
        diff_md = os.path.join(stage, "diff", "diff.md")
        changed = [l.split("|")[1].strip() for l in A.read_text(diff_md).splitlines() if l.startswith("| ") and not l.startswith("| Asset")] if os.path.exists(diff_md) else []
        rec["changed"] = len(changed)
        rec["changedAssets"] = changed
        if changed and os.path.isdir(os.path.join(stage, "diff")):
            ev = os.path.join(OUT, "art_evidence", f"diff_{a.scope}")
            shutil.rmtree(ev, ignore_errors=True)
            shutil.copytree(os.path.join(stage, "diff"), ev)
        if a.do_import and changed:
            r = run(ap + ["import", "--stage", stage], log)
            if r.returncode:
                rec.update(exit=r.returncode, rolledBack=r.returncode == 2)
                return finish(rec, r.returncode)
            rec["imported"] = len(changed)
        manifest = A.load_json(os.path.join(OUT, "art_manifest.json")) if os.path.exists(os.path.join(OUT, "art_manifest.json")) else {"assets": []}
        refs = {m["assetId"]: m["references"] for m in manifest["assets"]}
        rec["usedInGame"] = sum(1 for s in staged if refs.get(s[:-4]))
    return finish(rec, 0)


def _pngs(d):
    out = []
    for dp, _, fs in os.walk(d):
        for f in fs:
            if f.endswith(".png"):
                out.append(os.path.relpath(os.path.join(dp, f), d).replace("\\", "/"))
    return sorted(out)


def finish(rec, code):
    rec["exit"] = code
    hist = A.load_json(BATCHES) if os.path.exists(BATCHES) else []
    hist.append(rec)
    A.dump_json(hist, BATCHES, indent=1)
    print(f"[build] scope={rec['scope']} planned={rec['planned']} generated={rec['generated']} blocking={rec['validatedBlocking']} "
          f"changed={rec['changed']} imported={rec['imported']} used={rec['usedInGame']} blocked={len(rec['blocked'])} "
          f"cacheHit={rec['cacheHit']} exit={code} log={rec['log']}")
    return code


if __name__ == "__main__":
    sys.exit(main())
