# STATUS – docs / visualisation rev. 2 (2026-11-18)

Deliverables in `out/` (all user-facing text in Slovak):
* renders + labelled sheets: `T4_hero.png`, `T4_rozlozeny.png`, `T4_rez_spredu.png`, `T4_rez_zboku.png`, `T4_dvere.png`, `T4_zospodu.png`,
  `T4_tlac.png`;
* drawings of the 3 custom metal parts: `T4_ucho_vykres.png` + `ucho.dxf` (304 stainless 1.5, flat pattern from
  `t4_pan.ear_flat_pattern()`), `T4_most_vykres.png` + `most.dxf` (T_most, Al 2.0), `T4_pata_vykres.png` + `pata.dxf` (L_pata, Al 20 x 4);
  DXF R2000, mm, ezdxf audit 0 errors;
* `NOVA_trup.glb` (11.8 MB, 173 meshes, metres, torso bottom at z 0, head at lift 12.5, every mesh decimated to <= 16 000 faces)
  and `NOVA_trup.blend` (compressed, mm, hero camera + studio rig);
* `montaz_trup.txt` (buy, print, drill, epoxy, torque, 29 assembly steps, wiring / pin table, firmware, service of every servo) and
  `NAVRH_trup.md` (architecture, material, interfaces base / arms, deviations, check results, fixed findings, open items, 5 questions).

Scripts (re-runnable): `out/work/t4_scene.py` (Blender scene, shots, anchors, GLB), `out/work/sheet_t4.py` (labelled sheets),
`out/work/tlac_orient.py` + `tlac_scene.py` + `sheet_tlac.py` (print plates), `out/work/vykresy.py` (drawings + DXF),
`out/work/pose_lift.py` (posed STLs of the lift group at lift 12.5 from `t4_pan.pose_parts`).

Runs: `build_all.py` (exit 0, 53 s, cached) at 03:55 -> new STL stamp 938a05322f21426f; `checks.py` first run killed by the 30 min
background limit while in K8 (K1, K2, K3, K4, K5, K7, K9, K11 had passed), re-run started 04:31 with a 2 h limit (log
`out/work/checks_docs2.log`). That run finished 04:40:21 (exit 0, 840 s): checks.json stamp 938a05322f21426f, **K1-K13 all PASS** (K12: 198 rows, 0 FAIL, 2 not verifiable = MG90S side load and topple force, bench tests). The documents quote these numbers.

Not changed: no CAD module, no check script, no spec text. build_all.py / checks.py rewrote only their own outputs (stl/, step/,
parts*.json, checks.json, checks.log, module check logs) as the task asked; everything else written is in `out/` plus this file.

Honesty notes:
* The labels and numbers come from parts.json / t4_* modules / T4_spec.md 17.16 / opravy2.md; the pin assignment of the ESP32-S3-Zero
  and the FFC conductor order are a PROPOSAL for the (not yet drawn) carrier PCB, marked as such.
* Elegoo Tough numbers are retailer numbers (elegoo.com not reachable: DNS refused in this session) - marked NEOVERENÉ.
* Print-plate support rods are a visual density estimate (1 per 9 mm2 of faces within 45 deg of the plate), not slicer output.
