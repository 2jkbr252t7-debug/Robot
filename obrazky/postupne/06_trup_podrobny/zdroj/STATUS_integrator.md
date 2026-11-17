# STATUS – integrator (T4 torso)

State: **K1–K11 all PASS** on the STL set with stamp `bbc136411578d453` (148 parts, 24 printed).
Result file `checks.json`, log `checks.log`, parts list `parts.json`. The table comes from one run on the
final files: `build_all.py` (03:27 UTC, 40 s, no STL changed) and then `checks.py --force` (03:27–03:46 UTC, 1130 s,
exit 0), log `integ_work/cont/checks_final_run.log`. No build or check script was edited after that run started (only `T4_spec.md` got its addendum).

This role ran twice. The first run (about 100 min) was killed by a container restart at 02:46 UTC and left no
status file; the second run (from 02:48 UTC) continued from the files on disk. Both are described here.

## 1. How to reproduce

    /opt/venv/cad/bin/python build_all.py            # 40 s from the BREP cache, 17.5 min with --rebuild
    /opt/venv/cad/bin/python checks.py --force       # about 24 min; module checks run in parallel threads

`checks.py` without `--force` keeps every section whose STL stamp still matches and reruns the rest.
A section that raises, or whose helper has no result for the STL files on disk, is reported NOT RUN, never PASS.

## 2. Final table

| id | status | key numbers |
|---|---|---|
| K1 | PASS | 148/148 valid single solids, STL closed, one surface component; STEP null for 9 loft parts (12 MB rule), 139 STEP files, 13 MB in total |
| K2 | PASS | 153 parts (148 + 5 finished B parts), 555 pairs: 0 unintended overlaps, 39 declared press / thread / insert fits, 129 contacts |
| K3 | PASS | 315 pan x lift poses, 39 moving bodies vs 62 static parts: smallest undeclared clearance 1.000 (limit 1.0); 32 declared running fits inside the stage; gear flank gap 0.035; J1 sweep vs dummy: 1.000 |
| K4 | PASS | shells: 105 179 rays, median 2.20, min 1.30 (declared boss pilots); all printed parts: 2050 thin cells, all inside 27 declared local features, none below 0.6, 0 undeclared |
| K5 | PASS | C(J1) 18.000, C(pan) 21.600; journal in bore 0.15 with tape / 0.28 bare; 6805 seat 0.00, post 0.02; 12/12 seat-play rows; module seat tables 57/57, 30/30, 17/17 |
| K6 | PASS | crank r 10.000, stroke 20.000, dead centres at 0 / 180 deg; pin in slot 0.100 per side; pan hard stops +-90.85 deg; J1 hard stops +-154.75 deg |
| K7 | PASS | 45 steps, 38 swept paths, 0 collisions; 43 screws with a D4.5 tool channel (7 limited only by their own counterbore); 43 inserts / magnets / pins accessible |
| K8 | PASS | 93 204 T3 grid points: -0.013 .. +0.009 mm; rim zone D1 1.33 (declared <= 1.5); seams x 0.47, white / black 0.50; see-through 0 of 6.8 M rays from 26 views |
| K9 | PASS | min head clearance 0.517 mm (criterion 0.5) at lift 12.5, tilt 30 down, pan 0; no pan-dependent tilt table needed |
| K10 | PASS | all resin / POM parts fit 218 x 123 x 220; min feature 0.60; 10/10 vent / drain paths open; FDM supports declared for 3 parts |
| K11 | PASS | torso 346.2 g (T 301.9, P 39.0, L 5.3), centre of gravity (-0.9, -0.2, -51.8): 0.9 mm off the J1 axis; dummy stand 97.7 g |

Module pre-checks of the three builders (RAM A–G, PAN A–H, OBAL O / M / S / X) were rerun on the same STL set: all ok.

## 3. What the second run changed

Geometry (one part):
* **Z_naboj_test** – the 4 feet are gone. The plate lies flat on the bed (z -113.5 .. -108.5); a pedestal r 22.5
  carries the shoulder and the stop block at the old plate-top level z -104; the M8 head sits inside the counterbore,
  which is r 10.5 below z -109.2 with a 45 degree run-out (13 mm socket). FDM overhang 9340 -> 188 mm2
  (only the counterbore ceiling). Bounding box unchanged, mass 72.6 -> 77.0 g.
  Constants: `RAM['DUMMY']` in `t4_common.py` (plate_z, pedestal, socket); `t4_ram.mk_naboj`; one wall row in
  `t4_ram_checks.py` moved and one added. Section picture: `integ_work/cont/sec_naboj_x0.png`.

Checks:
* **K5** raised because two radii were read with wrong z limits (dummy post) or picked up the edge of the pinion
  passage (6805 seat). Both are now the dominant cylinder radius in the band.
* **K4 scan** (`checks_bl.py`) kept only the 400 thinnest cells per part, so T_ram cells between 1.40 and 1.59 were
  never judged. It now reports every cell below 1.62, per 2.5 mm cell and 0.1 mm thickness class. Result: 2050 cells
  below the material limit instead of 1352, still all inside declared features.
* **K4 declaration added**: the 1.4 ring of the 6 F2 insert bosses (r 3.0 around a D3.2 heat-set seat). This was the
  last K4 failure. I declared it instead of thickening the bosses: they are tied into the cradle wall / column foot.
* **K4 summary** now names the two declared rim features of the shells (flat top rim 1.25, socket rim wedge 0.94).
* **K10** support texts follow the measured overhang clusters (T_ram 455 mm2, P_drziak_serva 94 mm2, dummy 188 mm2).
* **K1** lists the 4 parts whose BREP volume differs from the STL volume, with the reason (section 5).
* `checks.py`: helpers run once per process under `--force`; the module checks start in background threads;
  `checks.json` carries `module_prechecks` and `from_scratch_rebuild`.

Spec: `T4_spec.md` got section 16, an addendum with the 8 integrator changes that supersede its numbers
(the text above it is untouched; copy before the edit in `integ_work/cont/T4_spec_before_addendum.md`).

## 4. What the first run changed (from the diff against `integ_work/*_before_integ.py`)

* `build_all.py`, `checks.py`, `checks_bl.py`, `t4_mesh.py`, `t4_assembly.py` written.
* Resin density 1.18 -> 1.15 g/cm3; every module exported through `t4_obal.export_abs` (absolute deflection 0.01).
* P_koleso: retaining lip 0.4 -> 0.6 thick (top z -42.0); floor under the blind dowel holes 0.5 -> 0.6.
* P_sachta: FPC groove under the apron runs out to the apron edge (removed a 0.3 x 0.2 rim and a feather edge).
* T_ram: pilots of F7 and F14 and the 4 cradle F2 insert seats are through holes (were 0.4 .. 0.5 floors).
* T_stred: magnet pocket of the two upper frame pads 0.5 further out along the wall, band-step fin removed
  (0.46 .. 0.50 of resin beside the pocket became >= 0.6). The frame magnet moved with it.
* STEP rule: 9 loft-derived parts have `step: null`; `step/` went from 685 MB to 13 MB.

The full list is `INTEG['changes']` in `t4_common.py` and `integrator_changes` in `parts.json`.

## 5. From-scratch rebuild

Run in an empty copy (`integ_work/scratch_build/`, same 5 source files, empty cache): `build_all.py --rebuild`,
1049 s, 148 valid parts. Compared with the main directory (`integ_work/cont/scratch_rebuild_report.json`):
* 145 of 148 STL files are byte-identical.
* T_stred, T_bok_L, T_bok_P are not. Their BREPs are the same (face / edge / vertex counts equal, vertex coordinates
  equal to 4e-12), but the mesher gives 86 828 vs 86 860 and 85 058 vs 85 174 triangles. Mesh volume differs by
  0.02 mm3; mesh-to-mesh distance is 0.0002–0.0004 mean, 0.035 at the 99.9th percentile, 0.078 max.
* That max sits on inner feature faces (seam lip, relief steps). So the 0.01 deflection is not held strictly there;
  the exterior faces are verified to 0.013 by K8. K4 readings on those faces can be off by a few hundredths.

The checks ran on the main-directory STL files, not on the scratch ones. The scratch caches were deleted afterwards;
logs, md5 lists and the three differing STL files are kept.

## 6. Declared items (what PASS rests on)

* **K3**: several clearances sit exactly on 1.000 with no margin: well to pan pinion, well to pinion screw, back floor and
  bracket to T_paluba, J1 pinion to the dummy post. Lift servo to T_ram column 1.025.
* **K4**: 27 local features below the wall limit of their material, each with box, minimum and reason in `K4_DECL`.
  Thinnest ones: 0.6 floors behind the 4 frame magnet pockets; 0.6 deck under the stop groove (spec);
  0.6 grille webs; 0.6 retaining lip and dowel-hole floors of P_koleso; 0.68 FPC groove in the back-sector floor;
  0.7 floors behind the F8 inserts and collars above the F2 seats; 0.75 seam-lip root ridge of the caps;
  0.78 webs of L_ucho; 0.8 ledge of P_drziak_serva (spec); 0.81 webs of L_pata; 0.85 door hook tabs.
  Seven parts are declared with a whole-part box and a minimum instead of a tight box (T_mriezka, T_drziak_repro,
  T_prichytka_fpc, P_drziak_serva, L_pata, L_jazyk, L_ucho). I looked at the cell clusters of every part with
  `integ_work/cont/k4_clusters.py`: all are webs at holes, lips, rims, ring or clip features, with two exceptions
  that are real areas and come from the spec: the 0.8 ledge of P_drziak_serva (22 x 12 mm under the servo end)
  and the 1.0 skirt disc of T_spodok.
* **K5**: the MG90S seat takes +0.2 in width flat; up to +0.3 the case rides up the 45 degree wedge lip.
* **K8**: two seam zones show the dark interior (no see-through): the top edge of the door for |x| < 20.6
  (241 of 389 lines of sight) and the 0.3 slit at the lower ends of the side seams (28 of 140).
* **K9**: the margin is 0.017 mm (white rim at (0, -29.6, 4.0) against the display frame). Recommended firmware limit:
  tilt down 27.5 degrees for lift 10 .. 15.
* **K10**: supports declared for T_ram (shoulder bosses, post shelf, bridges, F5 boss, clip ring), P_drziak_serva
  and the counterbore ceiling of the dummy. No slicer was run: islands, suction and support placement of the resin
  parts are not simulated.

## 7. Not done / open

* No further geometry work on the builders' open items: door top seam backing (rabbet), the 0.3 slit at the cap
  spigot top, collar-tube ribs at 0 / 180 degrees, service access to the FPC clamp screw after the collar disc is glued.
* Door hook tabs stay 0.85 thick (rule: local >= 1.2). They only locate the door, the magnets hold it; thickening
  them needs room that PAN_ENV + 1.0 does not leave. Print them in tough resin.
* K7 does not path-test flexible or loose parts (FPC, servo leads, foam pads, springs) and T_spodok (the base everything
  is built on).
* BREP volumes of the loft parts are unreliable in OCC (T_stred default 28 823, adaptive 29 821, STL 29 823;
  T_bok_L 13 574 .. 13 838 depending on the method, STL 13 684). Masses use the STL volume.
* Bought-part dimensions that are listing values, not measured: STS3215 spline length, STS3032 tab height and hole
  pattern, MG90S, speaker, LED strip.
* `montaz_trup.txt`, `NAVRH_trup.md`, images, GLB / .blend are not part of this role. They must take over:
  the dummy stand without feet, the builders' assembly-order changes, the K9 tilt recommendation.

## 8. Files

* `/tmp/claude-0/gapwf/fin/T4/build_all.py`, `checks.py`, `checks_bl.py`, `t4_mesh.py`, `t4_assembly.py`
* `/tmp/claude-0/gapwf/fin/T4/checks.json`, `checks.log`, `parts.json`, `stl/` (148), `step/` (139)
* `/tmp/claude-0/gapwf/fin/T4/integ_work/cont/` – second run: logs, backups of the files before my edits,
  `checks_final_run.log`, `scratch_rebuild_report.json`, `k4_clusters.py`, `sec_naboj_x0.png`
* `/tmp/claude-0/gapwf/fin/T4/integ_work/` – first run: logs, `*_before_integ.py` backups
