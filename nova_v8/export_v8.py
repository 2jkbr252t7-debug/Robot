"""
Package the NOVA mini v8 CAD export for the modelling team (all three head variants).

    /opt/venv/cad/bin/python -m nova_v8.export_v8 [--build]

--build first rebuilds every v8 module (base, torso, head A, internals, head A+, head B).
Writes
  export/NOVA_mini_<ver>_STEP.zip   – telo/ (base + torso + arms + neck), hlava_A/, hlava_A_plus/, hlava_B/,
                                      each split into vonkajsie/ (visible) and vnutro/ (internal), plus sklo/
                                      (flat blanks + bending-mould ribs as DXF/SVG)
  export/NOVA_mini_<ver>_kusovnik.csv – one row per part with the variant column
"""
from __future__ import annotations

import csv
import glob
import json
import os
import subprocess
import sys
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from nova import spec as v7spec  # noqa: E402  (materials)
from nova_v8 import spec  # noqa: E402

MODULES = ["cad_base", "cad_torso", "cad_head", "cad_internals", "cad_head_aplus", "cad_head_b"]
RENDER_ONLY = ("H04C", "H04E", "HP04C", "HP04E", "HB03C", "HB03E", "HP04F", "HB03F", "B-UG", "T06")


def load(build_dir, name):
    p = os.path.join(ROOT, build_dir, "manifest", f"{name}.json")
    with open(p) as f:
        return json.load(f)


def main():
    if "--build" in sys.argv:
        for m in MODULES:
            print("build", m, flush=True)
            subprocess.run([sys.executable, "-m", f"nova_v8.{m}"], cwd=ROOT, check=True)

    head_a = load("build_v8", "head")
    groups = []   # (zip folder, build dir, records)
    body = []
    for n in ("base", "torso", "internals"):
        body.extend(load("build_v8", n))
    groups.append(("telo", "build_v8", body))
    groups.append(("hlava_A", "build_v8", head_a))
    groups.append(("hlava_A_plus", "build_v8_var_aplus", load("build_v8_var_aplus", "head_aplus")))
    groups.append(("hlava_B", "build_v8_var_b", load("build_v8_var_b", "head_b")))

    out = os.path.join(ROOT, "export")
    os.makedirs(out, exist_ok=True)
    ver = spec.VERSION
    zp = os.path.join(out, f"NOVA_mini_{ver}_STEP.zip")
    readme = (
        f"NOVA mini {ver} – STEP export (mm, AP214). Každý diel je už v polohe ZOSTAVY:\n"
        "Z hore, počiatok na podlahe v strede základne, predok robota = −Y, pravá strana robota = −X.\n"
        "Naimportuj telo/ + JEDNU z hláv (hlava_A, hlava_A_plus alebo hlava_B) a všetko sedí na mieste.\n"
        "vonkajsie/ = viditeľné kryty, vnutro/ = mechanika a elektronika (zjednodušené obálky).\n"
        "sklo/ = rozvinuté prírezy zakriveného skla (DXF/SVG 1:1) a rebrá ohýbacej formy.\n"
        "Iba renderovacie objekty (podsvietenie, oči, okno kamery, plochý prírez) nie sú v STEP.\n")
    n = 0
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("CITAJ_MA.txt", readme)
        seen = set()
        for folder, bdir, recs in groups:
            for r in recs:
                if r["id"] in RENDER_ONLY:
                    continue
                key = (folder, r["id"])
                if key in seen:
                    continue
                seen.add(key)
                stp = os.path.join(ROOT, bdir, "step", f"{r['id']}.step")
                if not os.path.exists(stp):
                    print("  missing STEP", stp)
                    continue
                sub = "vnutro" if r.get("internal") else "vonkajsie"
                z.write(stp, f"{folder}/{sub}/{r['id']}.step")
                n += 1
        for f in sorted(glob.glob(os.path.join(ROOT, "nova_v8", "sklo", "*"))):
            if os.path.isfile(f):
                z.write(f, f"sklo/{os.path.basename(f)}")
        bom = os.path.join(ROOT, "nova_v8", "BOM_v8.md")
        if os.path.exists(bom):
            z.write(bom, "BOM_v8.md")
    with open(os.path.join(out, f"NOVA_mini_{ver}_kusovnik.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Balík", "ID", "Názov", "Materiál", "Podzostava", "Kĺb", "Vnútorný", "Rozmer X", "Rozmer Y",
                    "Rozmer Z", "Objem mm3", "Poznámka"])
        for folder, _bdir, recs in groups:
            for r in recs:
                if r["id"] in RENDER_ONLY:
                    continue
                sz = r["bbox"]["size"]
                mat = v7spec.MATERIALS.get(r["mat"], {}).get("desc", r["mat"])
                w.writerow([folder, r["id"], r["name"], mat, r["sub"], r.get("joint", ""),
                            "áno" if r.get("internal") else "nie", f"{sz[0]:.1f}", f"{sz[1]:.1f}", f"{sz[2]:.1f}",
                            f"{r.get('volume_mm3', 0):.0f}", r.get("note", "")])
    print(f"wrote {zp} ({n} STEP files, {os.path.getsize(zp) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
