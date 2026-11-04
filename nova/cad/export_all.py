"""
Rebuild every subassembly and package the CAD export for the modelling team.

    /opt/venv/cad/bin/python -m nova.cad.export_all [--no-build]

Writes export/NOVA_<version>_STEP.zip (all parts, STEP AP214, assembly coordinates, mm) and
export/NOVA_<version>_kusovnik.csv (part list with material and bounding box).
"""
from __future__ import annotations

import csv
import glob
import json
import os
import subprocess
import sys
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from nova import spec  # noqa: E402

SUBS = ["base", "torso", "neck", "head", "arms", "internals"]


def main():
    if "--no-build" not in sys.argv:
        for s in SUBS:
            print("build", s, flush=True)
            subprocess.run([sys.executable, "-m", f"nova.cad.{s}"], cwd=ROOT, check=True)
    recs = []
    for s in SUBS:
        with open(os.path.join(ROOT, "build", "manifest", f"{s}.json")) as f:
            recs.extend(json.load(f))
    out = os.path.join(ROOT, "export")
    os.makedirs(out, exist_ok=True)
    ver = spec.VERSION
    zp = os.path.join(out, f"NOVA_{ver}_STEP.zip")
    readme = (
        f"NOVA {ver} – STEP export (mm, AP214). Every part is already placed in ASSEMBLY coordinates:\n"
        "Z up, origin on the floor at the centre of the base, robot front = -Y, robot right = -X.\n"
        "Import all files into one assembly and they sit in place (default pose: all joints 0).\n"
        "vonkajsie/ = visible covers, vnutro/ = internal mechanics & electronics (simplified envelopes).\n"
        "H04C/H04E (camera window, eyes) are render-only objects and are not included.\n")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("CITAJ_MA.txt", readme)
        for r in recs:
            if r["id"] in ("H04C", "H04E"):
                continue
            folder = "vnutro" if r.get("internal") else "vonkajsie"
            z.write(os.path.join(ROOT, "build", "step", f"{r['id']}.step"), f"{folder}/{r['id']}.step")
    with open(os.path.join(out, f"NOVA_{ver}_kusovnik.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["ID", "Názov", "Materiál", "Podzostava", "Kĺb", "Vnútorný", "Rozmer X", "Rozmer Y", "Rozmer Z",
                    "Objem mm3", "Poznámka"])
        for r in recs:
            if r["id"] in ("H04C", "H04E"):
                continue
            sz = r["bbox"]["size"]
            w.writerow([r["id"], r["name"], spec.MATERIALS[r["mat"]]["desc"], r["sub"], r.get("joint", ""),
                        "áno" if r.get("internal") else "nie", f"{sz[0]:.1f}", f"{sz[1]:.1f}", f"{sz[2]:.1f}",
                        f"{r.get('volume_mm3', 0):.0f}", r.get("note", "")])
    print("wrote", zp, os.path.getsize(zp) / 1e6, "MB")


if __name__ == "__main__":
    main()
