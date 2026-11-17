# STATUS rev. 2 – CAD builder, module RAM (2026-11-17)

Rework of `t4_ram.py` / `t4_ram_checks.py` to T4_spec.md section 17 + `t4_common.R2`, resin rules (T4_zivica Z0–Z5, Z2
allowables 8.5 / 4.3 / 12.9 MPa, epoxy 2.7). Backups (rev. 1): `rev2_backup/t4_ram.py.ram.bak`, `t4_ram_checks.py.ram.bak`,
`parts_ram.json.ram.bak`, `STATUS_ram.md.ram.bak`. `t4_common.py` and the other modules were NOT edited; module-local numbers
and every deviation are in the block `# >>> additions by ram rev2` (dict `RAM2`, list `DEVIATIONS`) of `t4_ram.py` and in
`parts_ram.json` (`additions_ram_rev2`, `deviations`, `roots`, per-part `print`).

## Files (all in /tmp/claude-0/gapwf/fin/T4/)
* `t4_ram.py` – build() registry (74 parts), `python t4_ram.py` builds (printed parts cached by source hash in
  `cache/ram2_*.brep`, loft stage of the cap in `cache/ram2_capA_*.brep`), prints validity / volume / bbox / time, exports STL via
  `t4_obal.export_abs` (absolute deflection 0.01) to `stl/`, STEP to `step/` (< 12 MB; T_spodok has none: BREP 34 MB, loft
  faces), writes `parts_ram.json`, deletes the exports of removed parts.
* `t4_ram_checks.py` → `ram_checks.json`, `ram_checks.log` (sections A B C D E F G H S P X).
* `ram2_work/cross_rev2.py` (Blender BVH) → `ram2_work/cross_rev2.json` – advisory real-mesh check against the CURRENT OBAL
  (rev. 1 STLs of 03:26) and PAN (rev. 2 STLs of 13:20) exports.
* `ram2_work/prev2_ram.py` → previews `prev2_ram_*.png` (600 px, 16 samples): iso, iso_zad, spodok_iso, spodok_zad, zdola,
  det_zhora, det_deck, rez_y0, rez_x0, rez_y21, rez_col, det_J1, det_post2, det_carrier, det_pivot. All were looked at. They show
  the geometry of export 7; the final export only changed the dummy stop-block top (-99.3) and the 0.8 chamfer of the cradle FFC slot.

## Parts (rev. 2)
Printed (Elegoo Tough, mat resin_black): **T_spodok** 55.3 g (merged T_spodok + T_ram), **T_paluba** 2.6 g, **T_cap** 0.19 g,
**Z_naboj_test** 69.9 g (bench dummy). Custom metal: **T_most** Al 2.0, 4.4 g (C.DENS["alu"] = 2.70e-3 set at runtime –
integrator: add to DENS). Bought: STS3215 + brass m1 18T (bore 6, Loctite 638), STS3032 + m0.8 18T (bore 5, 638), 6805,
2 × ISO 8734 3 m6 × 12 stop pins, PTFE washer 24 × 10 × 0.3, PTFE tape on T_cap, PET shims, PORON, carrier + ESP32-S3-Zero,
buck, amp, 470 µF Ø8 × 11.5, screws / washers / bonded inserts / DIN 562 nuts (F1, F3a, F3b, F4, F7, F8 inserts, F14, F15, F16).
Deleted (exports removed): T_ram, T_prichytka_fpc, skr_fpc, all F2, F5, F6, cap_pan, pena_J1, the skirt, every heat-set hole.
Group masses: T 198.0 g, Z 92.2 g.

## What was built (main features)
* **T_spodok**: rev. 1 cap (cached loft) + spigot with 4 notches 7.8 wide (= OBAL F1 zone + 0.5), Ø37.15 6805 seat, plinth,
  NO skirt, J1 stop lug r 18.65..21.0 × 5.0 × 4.0 (z -102..-98, R1 roots), J1_PASS slot, base-FFC slot (annular sector r
  21.1..22.4, az 74.5..105.5, plinth skin 1.6), J1 clearance pocket + 4 corner pads 5 × 5 (top -83.3) + WINDOW (1.2 air over the
  plinth, open elsewhere), 2 × F16 at the -X pads, bumper + PORON; cradle walls 2.5 (front wall 1.69 between the two servos),
  -X end wall 2.5, R2 wall/floor roots, R0.5 inner end-wall corners; columns: web 3.0, ribs to x 42, box closure z -51..-34,
  foot = tub outline - 0.3, boss disc r 11.6, stop ring + backing flange, R1.5 flange cove, key slot az 0, F8 bonded M2 insert
  holes at az 60/180/300 (Ø3.3 × 3.3 + Ø2.3 through), board standoffs Ø5 × 1.5 + Ø1.7 pilots, Ø4 vents, Ø4.5 wire hole into the
  box; **full-height bridge walls** cradle ↔ columns; pan-servo posts (DIN 562 slots, Ø2.3 holes slotted ±0.3 along C, +X post
  plug window + leg); stop-pin posts (tops -48.2, pin holes Ø3.05 × 8.7; post 2 = block tied to the -X end wall); insert bosses
  r 3.4 (bonded M2.5, Ø3.6 × 4.3 + Ø2.8) for F3a (26, -13.8), (31, 5) and F3b (6, 15.95), (18.5, -15.95); carrier standoffs
  r 3.25 (bonded M2, face y 16.5) at x -25 / 25.8; capacitor pedestal (trough r 4.1 + tie groove 2.8 × 1.2); tie saddle on
  the cradle back wall; cradle FFC slot x 17..24, z -51.3..-49.7 + 0.8 chamfer; F1 pads r 3.4 with Ø3.2 holes and Ø6.5 × 1.9
  counterbores; 2 drains Ø3 at (±31, -9).
* **T_paluba**: deck 2.0 (z -48.2..-46.2) = back lobe r 25.1 + right part + C-ear embracing pin 1, trimmed r ≤ 26.6 in
  B az 26.2..223.8, slot for T_most (+0.1), FFC wall r 23.5..25.1 to -43.0 (az 15..165, outer R1 root), FFC slot r 22.4..23.6
  az 26..34, F3a Ø2.8 at (26, -13.8), (31, 5).
* **T_most**: Al 2.0, outline = hull of circles (0,0) r 12.5, (6, 15.95) r 3, (11, 15.5) r 2.5, (18.5, -15.95) r 3; M3 tap at
  (0,0); 2 × Ø2.8 + 90° countersink Ø5.2 (DIN 7991 M2.5 × 6, flush).  **T_cap**: Ø7.70 × 4.40, Ø3.4, top edges R0.3, root
  flare R0.6.  F15 ISO 7380 M3 × 6 + DIN 9021 (head top -39.35).
* **Carrier** DPS_riadenie: FR4 55.6 × 18 (x -27..28.6) with a notch under the USB plug envelope; ESP32-S3-Zero x -0.5..23,
  USB-C mouth (-0.5, 20.2, -62.5) facing -X; J_PAN_A/B (FH12-5S), J_BUS_V, J_J1 (FH12-10S-1SH), J_BUS_5 per §17.6; y ≤ 23.5.
* **Z_naboj_test**: sun-gear stub to -90, stop block az 270 ± 19 r 17..23, top -99.3.

## Deviations from §17 (each with its reason; full text in DEVIATIONS / parts_ram.json)
1. J1 stop lug r 18.65..21.0 × 5.0 (spec r 17..21 × 4): inside r 18.575 it blocks the 6805 (inserted from below); beyond r 21 it
   would block the base FFC wrap. Stop at ±153.4° (block ±19). Base stop block: top -99.3 (the lug's R1 roots occupy -99..-98).
2. F16: 2 screws at the -X pads only (+X pads lie over the plinth / 6805 seat – no tool path). Heads protrude to -86.1 (base ≤ -86.3 there).
3. Cradle front wall 1.69 for |x| ≤ 12.05 (+ tab ends |x| ≤ 16.55, z -56.8..-53.7): 2.19 between the STS3215 and STS3032.
4. Pan posts x ±(12.05..17.25) (spec 11.25 overlaps the STS3032 case); nut slot through the post, 4.7 wide (±0.3 C slot).
5. Stop-pin posts top -48.2, pins bonded 8.4 (same pin position / top -44.6); post 2 = block to the -X end wall.
6. Deck trim B az 26.2..223.8 (spec 16..232) with a C-ear behind pin 1 (the lug block sweeps 28.3..221.7 below the pin tops).
7. F3a only 2 screws at (26, -13.8), (31, 5) (spec (20, +13.8) sits under the FFC wall + in the cradle FFC slot; (-33.5, ±10)
   lie behind the lug sweep – no deck may cross r 27.6..31.6). The deck's -X lobe is unscrewed (rests on the wall / servo).
8. F3b: DIN 7991 countersunk flush in the ALUMINIUM T_most (ISO 7380 heads would stand in the FFC duct / under the gear tips);
   positions (6, 15.95), (18.5, -15.95) (spec (6, -15.95) collides with the STS3032 case). T_most = hull, not 18 × 36.
   L1 path: pivot 11.4 off the screw line → compression on the +Y wall top (row A7).
9. F1 = M2.5 × 6 (× 8 would bottom 0.6 in the T_stred boss). 10. F7 at x -25 / 25.8 on a 55.6 PCB, M2 × 5 (spec ±19 is under
   the ESP32 module; × 6 would touch the STS3215). 11. Capacitor Ø8 × 11.5 (Ø10 × 13 collides with the tub wall).
12. Base FFC slot = arc (skin 1.6 instead of 0.71). 13. Box closure z -51..-34 (1.2 above the boards). 14. T_cap flare R0.6.
15. F15 M3 × 6 engages 0.8 of T_most (1.6 threads; × 8 hits the servo) – torque 0.08 N·m. 16. Tie saddle 2.2 × 1.2 (2.0 mm tie);
   column-web saddles dropped (web inner face is 1.0 from PAN_ENV2), arm wires through a Ø4.5 hole into the column box.
17. Static FFC wall: outer R1 root only (inner face = FFC running face). 18. Spigot notches = OBAL F1 zone + 0.5 (x ±(25.1..32.9),
   |y| ≥ 15.1): the rev. 1 boss webs reach beyond r 3.9 (0.8 mm collision on the meshes); notch ends at |x| 32.9 (spec "none in
   |x| 31..35.6" is impossible: the boss itself reaches 32.4). 19. Cradle FFC slot 1.6 tall + chamfer. 20. Bridges full height.
21. Carrier notch under the USB plug. 22. F4 without washer (a Ø5 washer overlaps the servo case 0.25). 23. Plug envelope of the
   STS3032 model lowered 1.0 (F4 tip). 24. Box closure / foot / rib numbers as RAM2.

## Checks actually run (final geometry, `ram_checks.json`)
Run `/opt/venv/cad/bin/python t4_ram_checks.py` (all sections, 661 s, log `ram_checks.log`). **24/25 verdicts PASS, 1 FAIL (S\_strength\_rows).**
| check | result |
|---|---|
| A valid / single solid / watertight STL; deleted parts gone | 74/74; no T_ram / F2 / F5 / F6 / cap_pan / skr_fpc / pena_J1 exports left |
| B interference among RAM parts (OCC common volume, 179 bbox pairs) | 0 unexpected; 7 declared (threads, gear mesh, countersink) |
| C1 shell inset 2.2 above z -78 | min 0.80 (stop ring) |
| C2 T_stred lowering (lip outline - 0.5, front relief) | min 0.51 (pan-servo case corner); pan pinion -1.22 → must be bonded AFTER T_stred (see below) |
| C3 tub - 0.3 | min 0.38 (capacitor) |
| C4 OBAL F1 boss zone x ±(25.6..32.4), \|y\| ≥ 15.6, z -81..-75 | free |
| C5 static parts vs PAN_ENV2 swept pan ±90 (lug annulus r 27.6..31.6 handled as a sector) | min 1.00 (column web, deck vs lug) – hard limit met, not the 1.3 preferred |
| C6 pivot interface | T_cap r 4.45 / top -41.80, washer r 4.50 / -41.00, F15 head r 2.85 / top -39.35; washer → hub disc 2.00 |
| C7 pinion vs drum shroud | 3.39° = 1.04 mm |
| C8 stop pins | r 30.00, B az 25.45 / 224.58, top -44.60; stops at pan -89.99 / +90.02 |
| D seats (54 measurements on the solids) | 54/54 (6805 seat r 18.575 at 12 points, pocket, pads -83.3, 1.2 air, posts, pin holes 1.525 × 8.7, insert holes, standoff faces 38.9 / 16.5, boss / ring faces, deck / T_most 2.0, FFC wall, C 18.00 / 21.600, gear planes, stack 48.00) |
| E1 walls (25) | 25/25 (cradle 2.5; front wall 1.69 declared; web 3.0; closure 2.0; floor 2.2; pads 1.2; post walls 1.975; plinth skin 1.6; lug 5.0 × 2.35; deck 2.0; FFC wall 1.6; T_cap 2.15; T_most 2.0) |
| E2 insert walls ≥ 1.6 (9 inserts, 12 directions each) | min 1.60 |
| E3 roots (37 listed fillets probed at 0.3 R on the bisector) | 37/37 |
| E4 board air | buck 1.50, amp 1.50 + Ø4 vents |
| E5 deck trim r ≤ 26.6 in B az 26.2..223.8 | no violation |
| F tool channels (Ø4.5; F4 Ø1.3 ball-end through the bore) | 19/19 (F4: straight key, r 26.0 at the bore, only before the stage) |
| G1 J1 stop | ±153.37° (block az 270 ± 19) |
| G2 J1 sweep vs the dummy, swept (r, z) | min 0.316 (lug root fillet vs block top -99.3); pinion orbit r 27.93 (base opening ≥ 29) |
| H1 USB-C plug envelope | free (carrier notched) |
| H2 connectors reachable along +Y from the door at pan 0 | 5/5 |
| S strength rows (Z2) | 54/55 decisive rows PASS; FAIL: column above the box closure z -32, column alone, L5 10 N along X: 16.8 MPa (see NOT done) |
| P print table (Saturn 4 Ultra 16K, 5 mm margin) | T_spodok 89.6 × 83.9 × 110.2 (tilted 15°), T_paluba 59.3 × 19.6 × 42.1 (70°), T_cap, Z_naboj_test 110 × 90 × 23.5 – all fit; all resin, no PETG/POM, no heat-set, no countersunk head in resin |
| X cross-module (advisory) | see below |

Key strength numbers (Z2 allowables, Kt included where marked in ram_checks.json["S"]): column + full-height bridge walls
2.9–3.2 MPa (L5, normal 8.5; column alone below the box 16–22 → informational); box torsion 0.7; stop ring under 3 × F8 at
0.05 N·m 4.08 (sustained 4.3); J1 stop lug 7.6 (clutch 0.4 N·m, normal 8.5) / 11.5 (hand 0.6 N·m, abuse 12.9); corner pads
5.1; cradle walls 3.7 / 10.1 (638 releases at 1.1 N·m, abuse); T_cap compression 3.56 (sustained, F15 0.08 N·m) and root
7.7 (L8); F3b inserts 1.15 (epoxy 2.7, L1 × 2); wall top under T_most 4.75; pin-1 C-ear bearing 4.8 (L8); pin 2 post 3.0;
pan posts 4.3; T_most 20.5 MPa (Al). Torque rows evaluated at the RAM torques below.

## Assembly-order findings (for the integrator / K7, not geometry I can fix)
* **Pan pinion after T_stred.** The bonded m0.8 18T (tip y -28.79) cannot pass the T_stred lip (relief 27.55 - 0.5): bond it on
  the STS3032 spline IN SITU after T5 (through the bore / door, Loctite 638, 24 h), not on the bench (B7).
* **F4 / backlash:** F4 heads (r 25.06) are covered by the stage top plate once the stage is in. Sequence: T5 T_stred → pinion
  bonded → bare 36T gear on the taped T_cap → set C / backlash on the slotted F4 holes → tighten F4 with a Ø1.3 ball-end key
  through the bore (checked: straight path, r 26.0 at the bore) → epoxy on the gear top → lower the stage (PAN) → cure.
* F3a / F3b are reached from above only with T_stred off (T3, and the J1 service route already removes T_stred).

## Torque table under the Z2 allowables (spec 17.9 values FAIL – docs / architect must change them)
| joint | limiting element | spec N·m → MPa | RAM recommendation |
|---|---|---|---|
| F1 M2.5 (washer on the resin pad) | bearing 4.3 sustained | 0.09 → 8.0 | **0.045** |
| F3a M2.5 (washer on the deck) / F3a, F3b bonded inserts | bearing 4.3 / epoxy 2.7 | 0.09 → 8.0 / 4.1 | **0.045** |
| F4 M2 into DIN 562 nut (nut on the slot ceiling) | bearing 4.3 sustained | 0.05 → 9.7 | **0.02 + Loctite 222** |
| F7 / F8 M2 bonded inserts | epoxy 2.7 | 0.05 → 4.1 | **0.03** |
| F16 M2 (washer on the 1.2 pad) | bearing 4.3 sustained | 0.05 → 7.9 | **0.025** |
| F15 M3 into T_most through T_cap | T_cap compression 4.3 | 0.12 → 5.3 | **0.08 + Loctite 222** |
(K = 0.2; preload T/(K·d).)

## Cross-module (advisory, real meshes; OBAL STLs are still rev. 1)
`ram2_work/cross_rev2.json` (OBAL STLs 03:26, PAN STLs 13:27):
* DPS_riadenie ↔ ffc_A_nosic / ffc_B_nosic 1.15 – PAN's FFC ends inside the J_PAN ZIF mouths (intended).
* T_spodok ↔ skrutka_klb_L1..3 / P1..3 0.67–0.77 – OBAL rev. 1 F8 screws still at az 90/210/330; rev. 2 pattern is
  60/180/300 (§17.7) – clears when OBAL exports rev. 2.
* T_spodok ↔ ffc_par 0.037 at (19.8, 12.65, -48.24) – PAN's FFC pair grazes the cradle wall top where it rises from the wall
  slot to the deck slot (I already enlarged the slot to 1.6 + 0.8 chamfer); PAN should keep the pair ≥ 0.1 off the wall.
* Contacts (by design): PTFE washer / T_cap / pinion ↔ koleso_pan 0.02–0.06, deck / T_most ↔ koleso_pan 0.30, ↔ P_sachta 0.60.
* T_paluba ↔ P_drziak_serva 0.992 (FFC wall top -43.0 vs the lift module) – 0.008 below the 1.0 hard limit, PAN side.

## NOT done / NOT verified (do not treat as passed)
* K1–K13 (global) not run by me. No FE: rows 42c (column + bridge walls, plane-section estimate), 48 (cradle walls), 50 (corner
  pads, plate estimate), S06b (T_cap root), A7 (T_most lever) are hand / section estimates → K12 FE must confirm.
* Column above the box closure (z -34..-28.6, under the shoulder boss): column ALONE 16.8 MPa under L5 (10 N along X at the
  arm tip) > 8.5. The section there is limited by the T_bok seat flange (x 39.1..40.8 down to z -33, measured on the rev. 1
  T_bok mesh). The side-cap shell clamped at the same joint is a parallel path that is not counted. K12 must run FE with T_bok
  + T_klb; if it fails, the fix needs OBAL (a rib slot in the seat flange) or a steel insert plate.
* All bought-part numbers marked UNVERIFIED in §17.13 stay UNVERIFIED (STS3215 hole pattern / thread for F16, spline lengths,
  STS3032 spline, gear part numbers, FH12 5-pole stock, ISO 7380 head sizes, 470 µF Ø8 × 11.5 size). No web check was made in
  this run; the models use the §17 numbers.
* Print orientation / supports are stated per part (parts_ram.json["parts"][...]["print"]); no slicer / support simulation and
  no closed-cavity flood fill was run (cavities are open by construction: window, drains, through pilots, open column box).
* Real-mesh checks against OBAL are against rev. 1 OBAL STLs (F8 screws still at az 90/210/330) – rerun after OBAL rev. 2.
