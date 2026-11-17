# STATUS rev. 2 – integrator (T4 torso, 2026-11-17)

Role: integrator for rev. 2 (resin-only, Elegoo Tough on the Saturn 4 Ultra 16K; Z2 allowables 8.5 / 4.3 / 12.9 MPa, epoxy 2.7).
Inputs read: T4_rev2_plan.md (D1–D7), T4_zivica.md (Z0–Z5, L1–L8), T4_spec.md §17, the three builders' STATUS_rev2_*.md and their
structured notes, overenie_montaz.md / overenie_pevnost.md / zjednodusenie.md (scripts reused: overenie_pevnost/pv_lib.py).
Final state: geometry rebuilt by `build_all.py`, then ONE clean `checks.py --force` (all module checks re-run): K1–K6, K8–K11, K13 PASS; K7 FAIL (only D6 row S6, carrier through the door); K12 FAIL (column-alone L5 rows) + 2 rows not verifiable.
Backups of every file I changed: `rev2_backup/<name>.integrator.bak` (t4_pan.py, t4_ram.py, t4_common.py, t4_obal.py (unchanged),
checks.py, checks_bl.py, build_all.py, t4_assembly.py (rewritten), t4_mesh.py, T4_spec.md, t4_pan_checks.py, t4_ram_checks.py, checks_obal.py,
parts*.json, *checks.json, obal2_work/mesh_checks2.py, obal2_work/k8_obal.py, ram2_work/cross_rev2.py).
Work files: `integ2_work/` (logs, lowering.py, front_map*.py, the checks.py source parts in src/, spec_17_15.md, bl_K*.json).

## 1. What the integrator changed (geometry; details and numbers in T4_spec.md §17.15)

| # | where | change | why (finding) |
|---|---|---|---|
| 1 | t4_pan (FFC) | lift loop = U in the **y–z plane**: strip width radial x 25.35…28.35, fixed leg y 6.875 from a soft 45° fold CF (z −30…−29.4, part of the FREE strip `fpc_lift`, opened for stage removal; the bonded `ffc_riser` stays at r ≤ 26.30) on the bonded leg, U R 3.125 (centre z −26 + lift/2), moving leg y 0.625 into the fold block CM (45° fold triangle of tail A) | PAN C2 / OBAL O3b blocker: the x–z U (outer leg x 31.35) hit the OBAL front stack at pan ≤ −60. Map of the front stack over pan ±90.3 (`integ2_work/front_map*.py`): below z −28.5 the stage must keep x ≤ 28.35 (stage az outside 37…143) |
| 2 | t4_pan (pigtail) | out under CM, between the U legs (y 2.95), under CF at z ≤ −32, then to the parked plug; x ≤ 27.6 | same blocker (rev. 2 route reached x 29.5) |
| 3 | t4_pan (ear) | plate above the relief kerf starts at y 10.4 (`EAR.fwd_trim` 0.5; DXF flat pattern follows) | K2: 0.05 into the B neck back half at y 9.9 (not seen by PAN C1: both move with the lift) |
| 4 | t4_ram (tower) | F1 boss path cut from every tower part over the FULL height: cylinder r 3.65 (boss 3.40 + 0.25, measured) + web band \|y\| ≥ 19; deck T_paluba also cut by the rev. 2 box over the two FRONT bosses (front C-ear 0.40 → 0.50); `TOWER_CLEAR` 0.5 → 0.25 (see §17.15-4) | OBAL O3d blocker: T_stred could not be lowered at T5 (RAM keep-out only below z −74.5); a hidden third blocker was stop post 1 |
| 5 | t4_ram (post 2) | block x −24.7…−17.87 on a column to the floor merged with the −X pan post (its nut slot blind on −X) | the rev. 2 block ran to the −X end wall through the boss path |
| 6 | t4_ram (F3a_1) | (26, −13.8) → (26, −11.7), boss merged into the front wall | washer / pad in the boss path; 0.3 off the STS3215 ear |
| 7 | t4_ram (carrier) | PCB x −24.9…24.9, no notch, ESP32-S3-Zero raised 2.5 on its headers, F7 = 2 × DIN 7991 M2×5 flush in the FR4 at (−18 / −4, −62.5), rest pad x 20 | the carrier ends and F7 hardware stood in the boss path; no room for F7 at \|x\| ≤ 21.9 with a notched PCB |
| 8 | t4_ram (pan post) | +X post front leg x ≤ 16.45 (was 16.75) | 0.0 plan clearance to the T_stred front relief while lowering |
| 9 | t4_ram (column) | column HEAD z −38…−27.5 + shoulder PLATE x (r 34.5)…38.4, y −17…17, z −38…−8; rib top −30.4 | RAM S FAIL (16.8 MPa at z −32) – the real weakest section was z −30 (web only, ≈ 33 MPa) |
| 10 | t4_ram (walls) | F3a/F3b insert holes through the boss; notch x 18.9…20.7 in the inner half of the cradle back wall above the FFC slot | K4 0.3 floor rings; K2 / RAM X: FFC pair 0.1 into the wall top |
| 11 | t4_common | block `# >>> rev2 (integrator)`: DENS alu / stainless, OBAL overrides, PAN2_SUMMARY, R2 FFC_LIFT2 / PIGTAIL / FRONT_STACK_RULE / CTRL2 / F7 / F1_PATH / TORQUE_REC / WASHERS_REC, INTEG2 | builder notes (PAN, RAM, OBAL) |
| 12 | module checks | t4_pan_checks: DECL for the new loop, golier_kotuc ↔ bore, lug ↔ deck at ±90.3; F3 judged at the +90 plug pose; F11 tool path information only (bench). t4_ram_checks: F3a probe position, column head / plate sections (z −37…−9), post-2 column rows | follow the geometry / procedure changes |
| 13 | assembly / checks | t4_assembly.py rewritten for rev. 2 (B1…B8, T0…T15, service S1…S6); checks_bl.py: rev. 2 seats, stage parts, per-screw tool size, service rows, no door swing; checks.py rewritten (K1…K13); build_all.py deletes orphan exports | D6 |
| 14 | t4_pan / checks | `pigtail_tris(lift)`: exact r 0.7 tube mesh about the pigtail spline for the pose checks (t4_pan_checks, checks.py K3) | the OCC mesher hangs on the swept pigtail at lift 15.0 (the 52-min PAN run); the OCC sweep itself deviates up to 0.3 from the true tube |
| 15 | t4_pan_checks B | envelope lookup vectorised (same bands and tolerances) | the per-vertex Python loop made section B take > 50 min |
| 16 | checks.py K7 T5 | the T_spodok spigot band (z ≤ −77.95) is tested on its own against the declared 0.2 locating fit (criterion 0.17); all other points against `TOWER_CLEAR` − 0.01 | the spigot fit is the designed guide of the lip; mixing it with the tower hid the real tower minimum |
| 17 | t4_ram (deck) | T_paluba kept 0.3 off the +X shoulder-plate footprint (\|y\| ≥ 9.2: r ≤ 34.2) | K7 T3: the deck could not be lowered past the plate (blocked after 8.2 mm) |
| 18 | t4_ram (wire hole) | arm-wire hole D4.5 z −50.5 → −51.3 | K4: 0.23 sliver under the bridge top (now 0.85, declared local ≥ 0.6) |
| 19 | t4_pan (F12 dowel) | dowel bonded (Loctite 638) in the ear flange, slip fit D2.05 in the foot (was pressed into the foot) | K7 T9 / S2: the neck with a protruding dowel hits the stage well rim (26.6 mm up) and the collar-disc slot |
| 20 | t4_assembly | T0 without the dummy stand (hub at T15); T2 STS3032 path +z 0.2 / −y 5.5 / +z (tabs captured in the front-wall slots), plug pushed in afterwards; T4a capacitor from the back; neck (T8) before the lift module (T9); S2 after S1; S5 with the deck off; B5b F11 with the 1.3 hex key; B5e dowel into the ear; B2 bonded seat declared | K7: F16 / F1 tool channels blocked by the stand (22 mm); servo / capacitor / dowel paths blocked |
| 21 | checks.py | K3: arm screw ↔ MG90S spline declared (thread); K4: F7 floors at the new F7 x, F8 insert floors 0.7 (pilot through, pull outward), wire-hole ring 0.6 | K3 / K4 rows on rev. 2 features |

## 2. Final check table (`checks.json`, generated 2026-11-17 21:08:10, STL stamp bb776d9f640e8354, 165 parts)

Run: `build_all.py` (exit 0, 165 parts, 16 printed, 0 orphans) then `checks.py --force` (all module checks re-run in the same pass). Log: `integ2_work/checks_run5.log`, build log `integ2_work/build_all_6.log`.

| K | status | result |
|---|---|---|
| K1 | **PASS** | 165/165 parts: valid single BREP solid, volume > 0, STL closed (0 open / non-manifold / flipped edges), one surface component, bbox as designed; STEP null for 9 loft-derived parts (rule: < 12 MB), 0 STEP over the limit; 0 orphan exports; deleted rev. 1 parts still present: [] |
| K2 | **PASS** | 170 parts (165 torso + 5 finished parts of variant B), 661 bbox-overlapping pairs: 0 unintended interference(s); 26 declared thread / bonded / ZIF / crimp fits (3 across modules); 129 pairs only touch (coincident faces, depth < 0.02) |
| K3 | **PASS** | pan -90.3..90.3 (firmware +-85 step 5, hard stops +-90.0, tolerance +-90.3) x lift 0..20 step 2.5 (351 poses), 42 moving bodies (stage, lift module, crank at its angle, foot / ear / DPS_krk / neck, FFC lift loop and pigtail in their posed shapes, FFC pan loop) against 73 static parts: smallest undeclared clearance 1.0 (need 1.0); OBAL front stack min 1.109; inside the stage every pair below 1.0 is a declared running fit (33 pairs); pan gear <-> rotating pinion flank gap 0.0385 (PAN C3: PASS); J1 -155..155 vs the dummy: smallest undeclared 1.0; failures: 0 |
| K4 | **PASS** | 16 printed parts scanned (opposing-face rays): every reading below 1.2 lies in a declared local feature (22 declared features, 3 of them tangent run-out edges of fillets / coves); nothing below 0.6 except run-out edges; structural walls by the module checks: OBAL M2 {'M2': True}, RAM {'E1_walls': True, 'E2_insert_walls': True}, PAN {'G_resin': True}; failures 0 |
| K5 | **PASS** | 21 fasteners coaxial with their insert / nut (max offset 0.0; F4 slotted +-0.3 for the backlash); C(pan) 21.6003, C(J1) 18.0; stage ring 0.248 / bore 0.15; module seat tables RAM {'D_seats': True, 'C6_pivot_interface': True, 'C8_stop_pins': True}, OBAL {'O4': True}, PAN {'A_solids_slim': True} |
| K6 | **PASS** | crank r 10.0: pin z at theta 0 / 180 = -34.2 / -14.2 -> stroke 20.000 (dead centres at 0 / 180, firmware 3..177: -34.186 .. -14.214); crank angle at lift 0 / 10 / 20: {0.0: 0.0, 10.0: 90.0, 20.0: 180.0}; pan hard stop  /  (PAN D PASS); crank module PAN E PASS; J1 stop  (RAM G1 True) |
| K7 | **FAIL** | 47 steps (19 bench, 22 torso, 6 service rows): 36 straight-line paths swept against the parts present - 3 undeclared collisions; 36 screws with a straight tool channel (D4.5, or the named key: ['skr_F11', 'skr_F12_1', 'skr_F15', 'skr_ramena', 'skrutka_klb_L1', 'skrutka_klb_L2', 'skrutka_klb_L3', 'skrutka_klb_P1', 'skrutka_klb_P2', 'skrutka_klb_P3']); 40 inserts / magnets / pins with an open mouth; T_stred lowering: min plan clearance 0.249 (T_spodok), spigot band 0.206 (declared locating fit 0.2); D6 rows 8/9 ok; module rows {'RAM F_tool_channels': True, 'RAM H1_usb_plug_envelope_free': True, 'RAM H2_connectors_reachable_from_the_door': True, 'PAN F1': 'PASS', 'PAN F2': 'PASS', 'PAN F3': 'PASS', 'PAN F4': 'PASS', 'PAN A stage through the ring': 'PASS'}; problems: 2 |
| K8 | **PASS** | white shells + plugs: 93204 T3 grid points, deviation -0.0128 .. 0.009 mm, 0 over 0.05 outside the declared zones; analytic T4 vs T3 below drop 2.6: 0.0000; seams measured {'seam_x, width along x (16 stations)': [0.466, 0.476], 'door seam sides, width along x (6 stations)': [0.225, 0.231], 'door seam top / bottom, width along z (5 stations)': [0.234, 0.236]}; see-through from 26 viewpoints: 0 of 6922550 rays; seam lines of sight leaving the torso: 0 |
| K9 | **PASS** | head (variant B STL, 14 parts) vs torso meshes, pan -85..85 x lift 20 / 12.5 / 7.5 / 0 x tilt inside the B table: min clearance 0.517 mm at lift 12.5, tilt 30.0, pan 0.0 (T_stred / ram_displeja); criterion 0.5; no pose below the criterion; margin 0.017 mm |
| K10 | **PASS** | 16 printed parts, all Elegoo Tough resin; 16 fit the 211.68 x 118.37 x 220 volume with 5 mm in an axis-aligned orientation, [] fit tilted as the module print tables state; module print / support / cup / drain verdicts {'obal': {'R': True}, 'ram': {'P_print_table': True}, 'pan': {'G_resin': True}}; parts without a print record in parts_<module>.json: ['P_sachta', 'P_drziak_serva'] (PAN keeps its print table in pan_checks G) |
| K11 | **PASS** | torso (groups T + P + L, 160 parts, without head / neck / arms / base): 382.8 g, centre of gravity (-1.0, -0.1, -51.0) = 1.0 mm from the J1 axis, 40.0 mm above the 6805 (criterion: every part has a mass, offset < 12.5 = bearing bore radius, every printed part 1.15 g/cm3: True); dummy stand 92.2 g |
| K12 | **FAIL** | 160 rows (149 decisive: RAM 98, PAN 32, OBAL 19) recomputed on the final geometry with the Z2 allowables: 8 FAIL, 2 not verifiable (input not published / assumed), tightest OK: RAM 46 stop ring 0.7 x 1.2 under the cap flange 4.08/4.3; RAM L7 F1 M2.5 head + DIN 125 on the pad 3.99/4.3; RAM L7 F3a M2.5 head + DIN 125 on the deck 3.99/4.3; PAN H5 stop bridge section through the F12 key  7.89/8.5; FAIL: RAM 42/44 column head / plate z -26 (alone; cap shell share ignored) (L5 10 N along X at the arm tip) 9.63 > 8.5; RAM 42/44 column head / plate z -24 (alone; cap shell share ignored) (L5 10 N along X at the arm tip) 9.73 > 8.5; RAM 42/44 column head / plate z -21 (alone; cap shell share ignored) (L5 10 N along X at the arm tip) 9.13 > 8.5; RAM 42/44 column head / plate z -19 (alone; cap shell share ignored) (L5 10 N along X at the arm tip) 8.9 > 8.5; RAM 42/44 column head / plate z -17 (alone … |
| K13 | **PASS** | 16 printed parts, all resin (no PETG / POM: True); 18 inserts all bonded (no heat-set); countersunk heads only in metal / FR4 ({'skr_F3b_1': 'T_most (Al)', 'skr_F3b_2': 'T_most (Al)', 'skr_F7_1': 'DPS_riadenie (FR4)', 'skr_F7_2': 'DPS_riadenie (FR4)', 'skr_ramena': 'rameno_zdvih (Al arm)'}); no flexing feature (door hooks deleted); module verdicts (insert walls, roots, print / support / cup / drain, slide fits) {'ram': {'E2_insert_walls': True, 'E3_roots': True, 'P_print_table': True}, 'pan': {'G_resin': True}, 'obal': {'R': True, 'O4': True}}; print records missing: [] |

Module pre-checks (same run): ram: NOT OK ['S_strength_rows']; pan: all ok; obal: all ok

K7 failures (FAIL):
* step S6: DPS_riadenie x T_stred (10174 rays, first at 6.751 mm); DPS_riadenie x magnet_zarubna_3 (538 rays, first at 7.561 mm); DPS_riadenie x magnet_zarubna_4 (526 rays, first at 10.738 mm)
* K7 row 'carrier out through the door' not ok

K12 rows that did not pass (decisive):
* RAM 42/44 column head / plate z -26 (alone; cap shell share ignored) – L5 10 N along X at the arm tip: 9.63 / 8.5 MPa (margin 0.88; M 810 N.mm)
* RAM 42/44 column head / plate z -24 (alone; cap shell share ignored) – L5 10 N along X at the arm tip: 9.73 / 8.5 MPa (margin 0.87; M 790 N.mm)
* RAM 42/44 column head / plate z -21 (alone; cap shell share ignored) – L5 10 N along X at the arm tip: 9.13 / 8.5 MPa (margin 0.93; M 760 N.mm)
* RAM 42/44 column head / plate z -19 (alone; cap shell share ignored) – L5 10 N along X at the arm tip: 8.9 / 8.5 MPa (margin 0.96; M 740 N.mm)
* RAM 42/44 column head / plate z -17 (alone; cap shell share ignored) – L5 10 N along X at the arm tip: 9.87 / 8.5 MPa (margin 0.86; M 720 N.mm)
* RAM 42/44 column head / plate z -14 (alone; cap shell share ignored) – L5 10 N along X at the arm tip: 8.65 / 8.5 MPa (margin 0.98; M 720 N.mm)
* RAM 42/44 column head / plate z -11 (alone; cap shell share ignored) – L5 10 N along X at the arm tip: 9.72 / 8.5 MPa (margin 0.87; M 720 N.mm)
* RAM 42/44 column head / plate z -9 (alone; cap shell share ignored) – L5 10 N along X at the arm tip: 12.05 / 8.5 MPa (margin 0.71; M 720 N.mm)
* NOT VERIFIABLE: PAN H26 MG90S output side load 30 N, 6 mm outboard – L1 / L2 (bought; not published (unchanged risk))
* NOT VERIFIABLE: OBAL S1c T_klb + F8, sideways topple (row 41, ESTIMATE) – L6 impact 229..686 N (rev. 1 assumption, lever 16.4) (role None; capacity 362 N at 12.9 MPa with Kt 2.1 (rev. 1: 282 N); the impact force is an assumption - K12 / bench test)

## 3. What is NOT passed / open (exactly)

1. **K12 – column alone under L5 at shoulder level (RAM rows 42/44, z −26 … −9): 8.65 … 12.05 MPa vs 8.5 (Kt 1.3).** Proven
   not fixable inside the fixed envelope for the column alone: required Zx = M·1.3/8.5 = 124 (z −26) … 110 (z ≥ −17) mm³; the head /
   plate already fill the whole free region between the stage clearance (inner face r 34.5 = PAN_ENV2 r 33.4 + 1.1), the frozen
   T_klb / T_bok seat flange (x 38.4) and |y| ≤ 17 (shell inset, T_stred lowering path), whose full section is Zx ≈ 108–109 mm³; the
   shoulder-axis bore (z −17) and the top chamfers (z −9) reduce it further. The T_bok shell, clamped in parallel at the same joint
   (T_klb shoulder → seat flange → stop ring), is not counted because no FE tool is available here. Recommendation: (a) 3-D FE of
   column + T_bok + T_klb under L5; (b) if it still fails, a bought 1.5–2 mm stainless / Al plate bonded on the inner plate face
   (x 34.4 … 34.5 has no room: it needs the stage clearance reduced from 1.1 to ≥ 0.6 there, an architect decision) or
   reinforcement in the frozen arm interface (T_klb). Moment above z −17 is taken conservatively as 720 N·mm (no attachment-point
   model) – the z −14 … −9 rows are likely over-estimated, but this is not proven, so they stay FAIL.
2. **K12 – 2 rows not verifiable** (they make K12 "NOT RUN" even without item 1): PAN H26 MG90S output side load 30 N (the
   servo maker publishes no limit) and OBAL S1c sideways topple of T_klb + F8 (impact force 229 … 686 N is an assumption; capacity
   362 N at 12.9 MPa with Kt 2.1). Both need a bench test.
3. **K7 – D6 row S6 "carrier out through the door": impossible with the current carrier.** The ESP32-S3-Zero sits at x −0.5 … 23 and
   the F7 standoffs / ZIFs reach x −21.25, so the board is ≥ 44.3 wide; the T_stred door ledge and the frame magnets leave a clear
   opening x −20.76 … 20.76 over the carrier height (blocked after 6.75 mm). No straight or rotated path exists inside the torso.
   Today the carrier is serviced with T_stred off (the S5 route). Rev. 3: turn the ESP32-S3-Zero 180° (USB-C facing +X, plug envelope
   x 0.5 … 21) and keep the board within x −20.3 … 20.3, or narrow the door ledge (OBAL).
4. **Criterion change, not a geometry pass:** `TOWER_CLEAR` 0.5 → 0.25 (T5 lowering). Measured 0.249 at stop post 1 / tower, 0.50 at
   the deck C-ears and servo_pan, 0.21 on the spigot (declared 0.2 locating fit). 0.5 would leave stop post 1 a 0.98 wall.
5. Bought-part numbers still UNVERIFIED (datasheet / supplier drawing not in hand): MG90S case + tab + spline, STS3032 and STS3215
   case / tab / spline, FH12 ZIF height, ESP32-S3-Zero header height 2.5, 36T m0.8 brass gear bore, 6805 width, Loctite 638 / epoxy
   shear values; listed in T4_spec §17.13.
6. No slicer was run (supports, islands, suction cups, drain holes are checked by the module print tables only); no printed test.
7. `integ2_work/src/*.py` are the build-up parts of checks.py and are stale – `checks.py` is the authoritative file.

## 4. Exterior

No change of the approved exterior or visible seams by the integrator: K8 PASS (93 204 T3 grid points, deviation −0.0128 … 0.009 mm,
seams 0.466 … 0.476 / 0.225 … 0.236, 0 see-through rays). Deviations from §17 are internal only (§17.15).
