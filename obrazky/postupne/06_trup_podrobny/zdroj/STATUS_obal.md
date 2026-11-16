# STATUS – OBAL builder (shells), continuation run, 2026-11-16

Files (all under /tmp/claude-0/gapwf/fin/T4/):
* `t4_obal.py` – module, `build()` registry + `main()` (build, export, `parts_obal.json`); 50 parts
* `parts_obal.json` – dict: module / parts[] / deviations[] / intended_fits[] / bought{} / step_null[]
* `checks_obal.py` → `checks_obal.json` (O1, O3, O4, O5 + merged mesh and slide checks)
* `obal_work/mesh_checks.py` (Blender BVH) → `obal_work/mesh_checks.json`: M1, M2, M3, O2, S1, F1, X1
* `obal_work/slide_checks.py` → `obal_work/slide_checks.json`: X2, X3 (straight-line assembly against the RAM meshes)
* `obal_work/prev_obal.py` → `prev_obal_iso.png`, `_back.png`, `_sec_x.png`, `_sec_y.png`, `_inside_back.png`
  (+ context renders with the RAM module in `obal_work/pv_*_ram.png`)
* `stl/<name>.stl` for all 50 parts; `step/<name>.step` for 42 of them (8 are `step: null`, see below)
* `t4_common.py`: block "additions by obal" appended at the end (dict `OBAL`, 24 keys; nothing above it was touched)

## What the first run left and what this run changed
The first run (cut off) had 48 valid solids, no status file, an unfinished OCC interference test and had never run its
O3–O5 checks. Found and fixed in this run:

| # | finding | fix |
|---|---|---|
| 1 | T_stred × T_dvere overlap 14.6 mm³: the risers of the 4 frame-magnet pads crossed the door edge and the door bosses | `_pad` rev 3: riser 0.3 outside the opening down to inset 4.4, arm behind the door boss. Overlap now 0 |
| 2 | STL exported with a deflection RELATIVE to the edge size (build123d `export_stl`, also `t4_common.export_part`): chord errors up to 0.28 mm, exterior check failed with 48 164 of 127 345 grid points over 0.05 | `export_abs`: absolute deflection 0.01 mm. Exterior deviation now −0.013 … +0.004 mm |
| 3 | STEP 17–320 MB for loft-derived parts | STEP only below 12 MB; 8 parts `step: null`, oversized files deleted |
| 4 | door hook tabs 0.07 mm from the curved wall (flat tab, curved shell) | tab inset 2.5 → 2.75: 0.32 measured |
| 5 | floor behind the frame magnet pocket 0.4 mm | pad 4.5…7.2 (was 4.7…7.2), door boss face 4.3 (was 4.5): floor 0.6, air gap 0.2 kept |
| 6 | grille webs above / below the slots 0.5 mm; grille flange 0.09 into the speaker gasket | slots 1.6 high (webs 0.6); flange 23.0 → 22.4 wide |
| 7 | wire groove of T_klb left two 0.1 mm notches (neck, Ø22 journal) | groove opens through the shoulder face, ramps out inside the step chamfer |
| 8 | no cable exits on the bought parts of the front wall | reserved-space solids `vyvod_repro`, `vyvod_led`; wire notch in `T_drziak_repro` |
| 9 | OCC `common()` test: 30–110 s per pair against T_stred | BVH overlap + parity sampling: 101 pairs in 30 s, reproduces the OCC value (14.71 vs 14.60 mm³) |

## Check results (final geometry, from checks_obal.json)

| check | result | status |
|---|---|---|
| O1 / M1 solids | 50 parts: all valid single solids, volume > 0, bounding boxes as expected, all STL watertight (0 open / non-manifold / flipped edges) | PASS |
| O2 interference | 101 bbox-overlapping pairs, BVH overlap + parity sampling: 0 unintended; intended: 5 thread-forming screws in their pilots (3.3–3.8 mm³ each) | PASS |
| O3 zones | static vs RAM envelopes: min 0.7 (not declared); pan −85…85 × lift 0…20 vs PAN / LIFT envelopes: min 1.212; lowering of T_stred over the tower envelopes: min 0.5 (= TOWER_CLEAR); PAN_ENV + 1.0: 1 formal exception(s) (skrutka_led_2), ≥ 1.0 by the direct sweep | PASS |
| O4 seats | 17 seats listed with part / seat / clearance / tolerance; measured: bore r 28.342, speaker seat r 14.146, socket gap 0.496, neck gap 0.247, lip relief wall 1.477 normal / 2.547 horizontal | PASS |
| O5 inside | every internal part ≥ 0 from the inner surface (2 declared: LED screw tips in their boss pilots); shells ≤ 0.004 outside the exterior | PASS |
| M2 walls | 105179 through-wall rays: median 2.2, 1st percentile 2.192, min 1.302 (LED boss pilots, declared); below 2.0 outside declared spots: 0; below 1.2: 0; socket rim wedge min 0.944 (declared, not counted) | PASS |
| M3 exterior | 127345 grid points (0.45 mm): deviation -0.0128 … 0.0038 mm, 0 over 0.05; 5743 uncovered points, all in declared gaps (5702 in the sockets); seam widths measured: x seams [0.466, 0.476], door [0.225, 0.231] | PASS |
| S1 seam backing | lines of sight inside the gap planes: see-through 0; open to the interior only in the 2 declared zones: door_top_centre 241/389 rays; seam_x_lower_end 28/140 rays | PASS |
| F1 fits measured | door hooks 0.319; frame magnets <-> door magnets 0.2; door boss <-> magnet pad of the frame 0.1; cap seam lip <-> centre band 0.156; cap edge <-> band edge 0.5; joint body <-> socket bore 0.5; joint neck <-> seat-flange hole 0.249; light guide plug <-> bar opening 0.199; grille plug <-> slot 0.2; speaker <-> its 3 boss scallops 0.149; bush <-> joint bore 0.025 | info |
| X1 vs RAM meshes | 27 touching pairs, none with volume (contacts only); cap socket tube ↔ column rib 0.651 mm | info |
| X2 lowering vs RAM meshes | 43 tower parts, 989 pairs: min plan gap 0.5 (required 0.5) | info, ok |
| X3 cap slide vs meshes | 86 pairs, 0 closer than required + 0.6 | info, ok |

## Printed parts

| part | material | mass g | bbox x / y / z | STEP |
|---|---|---|---|---|
| T_stred | resin_white | 35.19 | -33.05…33.05 / -40.01…37.38 / -81.00…4.00 | null |
| T_bok_L | resin_white | 16.15 | 31.05…52.50 / -33.40…33.40 / -81.00…2.66 | null |
| T_bok_P | resin_white | 16.15 | -52.50…-31.05 / -33.40…33.40 / -81.00…2.66 | null |
| T_dvere | resin_white | 9.13 | -28.00…28.00 / 28.89…40.01 / -72.00…-9.51 | null |
| T_klb_L | resin_black | 9.15 | 37.00…58.76 / -10.50…16.50 / -30.48…-3.50 | yes |
| T_klb_P | resin_black | 9.15 | -58.76…-37.00 / -10.50…16.50 / -30.48…-3.50 | yes |
| T_puzdro_L | pom | 1.16 | 42.00…58.75 / -2.00…8.00 / -22.00…-12.00 | yes |
| T_puzdro_P | pom | 1.16 | -58.75…-42.00 / -2.00…8.00 / -22.00…-12.00 | yes |
| T_svetlovod | resin_clear | 0.68 | -16.80…16.80 / -39.33…-34.03 / -36.50…-28.50 | null |
| T_mriezka | resin_grey | 0.25 | -11.20…11.20 / -40.01…-36.70 / -50.60…-45.40 | null |
| T_drziak_led | resin_black | 0.92 | -22.30…22.30 / -35.94…-29.40 / -36.00…-29.00 | null |
| T_drziak_repro | petg | 0.57 | -16.89…16.89 / -31.60…-30.00 / -70.10…-36.30 | yes |

Printed mass 99.66 g, bought parts of the module 15.47 g.

## Declared, not fixed (inside the OBAL module)
* **Door top edge is not backed.** No ledge for |x| < 20.6 (pan sweep, spec 4.3): the 0.25 mm seam along the top edge of
  the door is open to the interior between and beside the hook tabs (S1: 241 of 389 lines of sight meet nothing within
  9 mm; none leaves the torso again). PAN_ENV + 1.0 leaves 0.29 mm behind the wall there, so no shadow lip fits; a rabbet
  inside the 2.2 wall (frame lip 1.2 + door tongue 0.8) would close it but was not built.
* **Lower ends of the two side seams.** The seam lip of the caps ends at z −77.7, the cap spigot top is at −78.0: through
  that 0.3 mm slit, and for lines rising from below the lower edge, 28 of 140 lines of sight pass into the shell (they end
  on the frame, none is a see-through). Everywhere else the seams are backed (3 870 lines, 0 open).
* **Socket rim on top of the shoulders.** The exterior meets the socket bore r 14 at 51° (minimum, azimuth 90°); the wall
  between bore and exterior is below 1.2 mm within about 1.5 mm of that rim (0.94 at 0.6 mm from the edge). This is the
  approved T3 look (cylinder emerging from the shelf); it is the thinnest white feature.
* **Door depth stop.** The door rim is 0.2 in front of the ledge (spec) and 0.1 in front of the 4 pad risers; pulled in by
  the magnets it sits 0.1 below flush on four small crescents next to the magnet bosses (magnet air gap then 0.1).
  Shim the ledge with 0.1 tape if a flush door is wanted.
* **LED-holder screws vs PAN_ENV.** `skrutka_led_2` (and its mirror image within 0.01) stands just outside the formal front
  sector (azimuth 232…236 at r 33.0, limit there r 35.0); direct sweep against every PAN / LIFT envelope: 4.5 mm.
  Proposal for the lead: PAN_FRONT = (230, 336), and the front rule down to z −41.9 instead of −40.5 (used in O3).
* **Collar tube:** gusset cones in ±Y instead of the 6 ribs; ribs at 0° / 180° omitted.
* **Lip relief wall** 1.48 mm normal (2.55 horizontal) at |x| 16.75, z −81 – spec estimate was ≥ 1.5; local limit 1.2.

## NOT done / NOT verified
* K7 for the door (hook in, swing shut) and for the front stack was not simulated – only static gaps were measured.
* K9 (real head vs torso top) and K8 from 26 viewpoints are integrator checks; S1 here is a ray test of the seam gaps only.
* K10: orientation and supports are the spec's (4.7); no slicer run. Minimum features are listed below.
* The PAN module (`t4_pan.py`) did not exist when the checks ran: O3 uses the PAN / LIFT ENVELOPES of
  `t4_common.envelopes()`, not real pan-stage geometry.
* X1 / X2 / X3 / S1 used the RAM STLs on disk at 16:10–16:40 (parts_ram.json and stl/T_ram.stl dated 16:07); the RAM
  builder was still working, so these cross-module numbers are a snapshot, not the final K2 / K7.
* Bought-part sizes (speaker Ø28 × 5, LED strip 30 × 4 × 0.8) are catalogue / spec values, not measured parts.

## Minimum features and drains (input for K10)
* T_dvere hook tabs 0.85 thick (8 × 4.8); T_stred floor behind the frame magnet pockets 0.6; T_mriezka webs 0.6, slots 0.8 wide;
  T_svetlovod flange 1.2; T_drziak_led walls ≥ 1.4; seam lip of the caps 1.6; door ledge 1.6 × 2.0; T_klb walls ≥ 1.03
  (magnet pockets to the end chamfer); T_drziak_repro ring 1.6 (PETG).
* Sharpest white edge: socket rim 51°; all seam edges are 90° cuts of the 2.2 wall.
* Drain / vent: T_stred 2 × Ø1.6 through the collar tube at z 0.4 (trough between tube and shelf) + the bore; caps and door
  are open shells; no closed pocket in any part.
* Largest part T_stred 66.1 × 77.4 × 85.0 mm (build volume 218 × 123 × 220).

## How to re-run
```
/opt/venv/cad/bin/python t4_obal.py                      # 40 s from the cache (full rebuild about 20 min: add --rebuild)
/opt/venv/bl/bin/python  obal_work/mesh_checks.py        # 40 s  -> obal_work/mesh_checks.json
/opt/venv/cad/bin/python obal_work/slide_checks.py       # 4 min -> obal_work/slide_checks.json (needs the RAM STLs)
/opt/venv/cad/bin/python checks_obal.py                  # 6 min (3 min with the sweep cache) -> checks_obal.json
/opt/venv/bl/bin/python  obal_work/prev_obal.py -- --views iso,back,sec_x --res 600 --samples 12
```
