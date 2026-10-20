"""Validator self-tests: intentionally broken sheets/manifests must trigger the expected checks.
Run: python3 -m unittest discover -s Tools/ArtPipeline/tests -v
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import artlib as A  # noqa: E402
import validate as V  # noqa: E402


def figure(size=320, top=40, bottom=292, left=110, right=210, colour=(200, 60, 40), ink=(28, 23, 48)):
    """A simple unit-like figure: ink outline + flat body, light upper-left."""
    a = np.zeros((size, size, 4), np.uint8)
    a[top:bottom + 1, left:right + 1] = (*ink, 255)
    a[top + 4:bottom - 3, left + 4:right - 3] = (*colour, 255)
    a[top + 4:(top + bottom) // 2, left + 4:(left + right) // 2] = tuple(min(255, c + 40) for c in colour) + (255,)
    return a


class Fixture:
    def __init__(self):
        self.root = tempfile.mkdtemp(prefix="artval_")
        self.art = os.path.join(self.root, "Art")
        self.content = os.path.join(self.root, "Content")
        self.scripts = os.path.join(self.root, "Scripts")
        for d in (self.art, self.content, self.scripts):
            os.makedirs(d)
        self.settings, self.manifest = {}, []
        self.guid = 0
        A.dump_json({"heroes": [{"id": "testo", "element": "fire"}]}, os.path.join(self.content, "heroes.json"))
        A.dump_json({"enemies": []}, os.path.join(self.content, "enemies.json"))

    def rel_root(self, rel):
        return os.path.relpath(os.path.join(self.art, rel), A.ROOT).replace("\\", "/")

    def put(self, rel, arr, pivot=(0.5, 0.0875), manifest=True, meta=True, guid=None, license="original"):
        p = os.path.join(self.art, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        Image.fromarray(arr, "RGBA" if arr.shape[-1] == 4 else "RGB").save(p)
        self.settings[self.rel_root(rel)] = {"ppu": 200, "pivot": list(pivot)}
        if manifest:
            self.manifest.append({"path": self.rel_root(rel), "license": license})
        if meta:
            self.guid += 1
            A.write_text(p + ".meta", "fileFormatVersion: 2\nguid: %s\n" % (guid or "%032x" % self.guid))

    def hero_set(self, hid="testo", evo_same=False):
        base = figure()
        for f in ("idle", "cast", "downed", "evoA", "evoA_cast", "evoB", "evoB_cast"):
            arr = base
            if f.startswith("evo") and not evo_same:
                arr = figure(top=24, left=90, right=230, colour=(240, 200, 40) if f.startswith("evoA") else (60, 120, 230))
            self.put(f"Heroes/{hid}_{f}.png", arr)

    def run(self, waivers=None, today="2026-10-20"):
        sp = os.path.join(self.root, "settings.json")
        mp = os.path.join(self.root, "manifest.json")
        wp = os.path.join(self.root, "waivers.json")
        A.dump_json(self.settings, sp)
        A.dump_json(self.manifest, mp)
        A.dump_json({"waivers": waivers or []}, wp)
        out = os.path.join(self.root, "out")
        args = V.parser().parse_args(["--art", self.art, "--settings", sp, "--manifest", mp, "--content", self.content,
                                      "--scripts", self.scripts, "--waivers", wp, "--out", out, "--today", today])
        rep = V.run(args)
        blocking = V.write(rep, out)
        return rep, blocking

    def close(self):
        shutil.rmtree(self.root, ignore_errors=True)


def checks(rep, asset=None, waived=None):
    return {i["check"] for i in rep.issues if (asset is None or i["asset"] == asset) and (waived is None or i["waived"] == waived)}


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.f = Fixture()

    def tearDown(self):
        self.f.close()

    def test_clean_set_passes(self):
        self.f.hero_set()
        rep, blocking = self.f.run()
        self.assertEqual(0, blocking, [i for i in rep.issues if i["severity"] == "error"])
        self.assertNotIn("weak_evolution", checks(rep))
        self.assertEqual("KEEP", rep.assets["Heroes/testo_idle.png"]["decision"])

    def test_cropped_empty_and_missing_frame_are_blocking(self):
        self.f.hero_set()
        self.f.put("Heroes/testo_cast.png", figure(top=0))               # touches the top edge
        os.remove(os.path.join(self.f.art, "Heroes/testo_evoB_cast.png"))
        self.f.manifest = [m for m in self.f.manifest if not m["path"].endswith("testo_evoB_cast.png")]
        self.f.put("Icons/blank.png", np.zeros((96, 96, 4), np.uint8), pivot=(0.5, 0.5))
        rep, blocking = self.f.run()
        self.assertIn("cropped_silhouette", checks(rep, "Heroes/testo_cast.png"))
        self.assertIn("missing_frame", checks(rep, "Heroes/testo_evoB_cast.png"))
        self.assertIn("empty_image", checks(rep, "Icons/blank.png"))
        self.assertGreaterEqual(blocking, 3)
        self.assertEqual("REMAKE", rep.assets["Heroes/testo_cast.png"]["decision"])

    def test_manifest_meta_guid_license_and_size_defects(self):
        self.f.hero_set()
        self.f.put("Relics/no_manifest.png", figure(128, 10, 110, 20, 100), pivot=(0.5, 0.5), manifest=False)
        self.f.put("Relics/no_license.png", figure(128, 10, 110, 20, 100), pivot=(0.5, 0.5), license="")
        self.f.put("Relics/dup1.png", figure(128, 10, 110, 20, 100), pivot=(0.5, 0.5), guid="ab" * 16)
        self.f.put("Relics/dup2.png", figure(128, 10, 110, 20, 100), pivot=(0.5, 0.5), guid="ab" * 16)
        self.f.put("Relics/no_meta.png", figure(128, 10, 110, 20, 100), pivot=(0.5, 0.5), meta=False)
        self.f.put("Relics/wrong_size.png", figure(100, 10, 90, 20, 80), pivot=(0.5, 0.5))
        self.f.manifest.append({"path": self.f.rel_root("Relics/ghost.png"), "license": "original"})
        rep, _ = self.f.run()
        self.assertIn("manifest_missing", checks(rep, "Relics/no_manifest.png"))
        self.assertIn("license_missing", checks(rep, "Relics/no_license.png"))
        self.assertIn("duplicate_guid", checks(rep, "Relics/dup1.png"))
        self.assertIn("meta_missing", checks(rep, "Relics/no_meta.png"))
        self.assertIn("size_mismatch", checks(rep, "Relics/wrong_size.png"))
        self.assertIn("manifest_orphan", checks(rep, "Relics/ghost.png"))

    def test_case_collision_and_missing_script_reference(self):
        self.f.hero_set()
        self.f.put("Icons/Glyph.png", figure(96, 10, 80, 10, 80), pivot=(0.5, 0.5))
        self.f.put("Icons/glyph.png", figure(96, 10, 80, 10, 80), pivot=(0.5, 0.5))
        A.write_text(os.path.join(self.f.scripts, "X.cs"), 'var t = Art.Tex("Icons/nowhere");\n')
        rep, _ = self.f.run()
        if os.path.exists(os.path.join(self.f.art, "Icons/Glyph.png")) and os.path.exists(os.path.join(self.f.art, "Icons/glyph.png")):
            self.assertIn("duplicate_path", checks(rep, "Icons/glyph.png"))   # case-sensitive file systems only
        self.assertIn("missing_reference", checks(rep, "Icons/nowhere.png"))

    def test_weak_evolution_foot_slide_frame_jump_and_halo(self):
        self.f.hero_set(evo_same=True)
        self.f.put("Heroes/testo_cast.png", figure(top=60, bottom=250, left=40, right=100))   # floats + pops
        halo = figure()
        halo[34:40, 100:220] = (255, 255, 255, 90)                                            # bright translucent rim
        halo[296:300, 100:220] = (255, 255, 255, 90)
        self.f.put("Heroes/testo_evoB_cast.png", halo)
        rep, _ = self.f.run()
        self.assertIn("weak_evolution", checks(rep, "Heroes/testo_evoA.png"))
        self.assertIn("foot_pivot_mismatch", checks(rep, "Heroes/testo_cast.png"))
        self.assertIn("frame_jump", checks(rep, "Heroes/testo_cast.png"))
        self.assertIn("white_halo", checks(rep, "Heroes/testo_evoB_cast.png"))
        self.assertEqual("REFINE", rep.assets["Heroes/testo_evoA.png"]["decision"])

    def test_waivers_suppress_until_expiry(self):
        self.f.hero_set()
        self.f.put("Heroes/testo_cast.png", figure(top=0))
        w = [{"asset": "Heroes/testo_cast.png", "check": "cropped_silhouette", "reason": "test", "expires": "2026-12-31"}]
        rep, blocking = self.f.run(waivers=w)
        self.assertEqual(0, blocking)
        self.assertIn("cropped_silhouette", checks(rep, "Heroes/testo_cast.png", waived=True))
        rep, blocking = self.f.run(waivers=w, today="2027-01-02")
        self.assertIn("waiver_expired", checks(rep))
        self.assertGreaterEqual(blocking, 2)

    def test_no_alpha_is_blocking_for_sprites(self):
        self.f.hero_set()
        self.f.put("Relics/opaque.png", figure(128, 10, 110, 20, 100)[..., :3].copy(), pivot=(0.5, 0.5))
        rep, _ = self.f.run()
        self.assertIn("no_alpha_channel", checks(rep, "Relics/opaque.png"))


if __name__ == "__main__":
    unittest.main()
