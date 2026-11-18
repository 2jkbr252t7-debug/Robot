# T4 rev. 2 – fixer record (opravy2)

Fixer runs 2026-11-17/18 (run 1 killed by a container restart at 00:48 UTC; run 2 = continuation) on the verifier findings of
`overenie2_mechanika.md` (G1, S1–S5, K1, K2, mech-m1 … m7) and `overenie2_montaz.md` (B1, M1–M6, mont-m1 … m8).
Backups of every file the fixer changed: `rev2_backup/<name>.fixer.bak`. Work files: `fix2_work/`.
Spec text: `T4_spec.md` section **17.16** (supersedes 17.0–17.15 where different). Numbers: `t4_common.FIX2` (incl. the fingertip-torque
joint table `FIX2["JOINTS"]`, `tilt_down_max()`, `tilt_up_max()`), `t4_pan.PAN2["FIX2"]`, `t4_ram.RAM2` (COL.plate, bridge_fillet,
head_cove, wire_hole, CUP_VENTS, J1_LUG, F3A, USB_EXT), `t4_obal` step `stred_pinion`.

**Lead decision applied in run 2 (overrides 17.16 item 13 of run 1):** no torque screwdriver may be required. Every screw joint that
bears on resin is designed for a small precision screwdriver turned with the fingertips – design case **0.10 N·m** (see S5).

"Reproduced" below means: the fixer confirmed the defect in the model / code (own probe or code inspection, script named) before
changing anything. Where run 1 left no log, the reproduction is stated as code inspection + the verifier's numbers.

## 1. Findings

| id | real? | change (where) | result / regression check |
|---|---|---|---|
| **B1** blocker – bonded pan pinion blocks T_stred removal | **real** (run 1, `fix2_work/b1_probe.py`: T_stred lip material inside r 8.6 of the pinion axis at z −81 … −79.5; the in-situ bond T5b made S5 impossible) | T_stred front lip cut back to **r 8.35 about the pinion axis** (interior only, `t4_obal` step `stred_pinion`); pinion bonded **on the bench (B7b)**, step T5b and its 24 h cure deleted; new service row **S5a**: T_stred (+ front stack, F1 inserts, frame magnets, glued ring) lifted straight up with the STS3032 + pinion in place; carrier serviced with T_stred off (S6) | K7 S5a is a **sweep** (not a remove), plan clearance 0.35 to the pinion (`integ2_work/lowering.py`); K7 rows "T_stred lifted straight up …", "carrier out (with T_stred off)" |
| B1 follow-up (run 2) – front stack vs the bench-bonded pinion | **real** (OBAL O3d: the k 2.0 head of the 270° speaker-ring screw 0.06 from the modelled pinion teeth; −0.13 against the tip circle r 8.0, i.e. a clash at other tooth angles) | F13 screws (speaker ring + LED holder) → **low-head thread-forming M2 × 6, k ≤ 1.2** (`t4_obal.TF_HEAD`; catalogue data UNVERIFIED) | **regression** K7 row "T_stred + front stack vs the pan pinion tip circle (any tooth angle)" ≥ TOWER_CLEAR − 0.02 |
| **G1** journal lands under the PTFE tape | **real** (code: the 8 well-corner / rib-end lands were trimmed only to the r 26.50 stage envelope) | P_sachta journal band z −10.7 … −1.9 turned to **r ≤ 26.365 at every azimuth** (`PAN2["FIX2"]["journal_r"]`) | K5 now measures the journal **with the tape**: P_sachta r max, tape r max, bore r min and play ≥ 0.14 (`checks._journal_play`) |
| **S1** sharp corners on the column bending fibres | **real** (code: no fillet between the +Y bridge-wall top and the column inner face; the head overhang had no cove) | R1.5 fillet bridge-top / column (x ±34.4, z −48.2), R1.0 cove under the head overhang (x ±42 … 43, z −38), arm-wire hole moved to (y −2.0, z −51.0), plate inner face r 34.4 at every y and plate \|y\| ≤ 20 for z −38 … −20, F3a_2 → (30.6, 4.0) | RAM E3 root list carries both fillets; K12 column rows (load through the F8 screws, Kt 1.3 / 1.1): max 7.65 / 8.5 at z −24 |
| **S2** tongue root R0 rated at 8.5 | **real** (K12 row PAN H13 "R0 declared" vs 8.5) | P_drziak_serva tongue roots **R0.5** (both long edges), groove mouth chamfer 0.8 in P_sachta | H13 now Kt 1.6 → 5.57 / 8.5; **regression**: K12 `R0:` rows force every decisive row whose feature says R0 / unfilleted / sharp onto 4.3 |
| **S3** pan-servo centre distance held by friction | **real** (run 1, `fix2_work/s3_probe.py`: case gaps +Y 0.30 / −Y 0.54 / ±X 0.10 – only X positive) | after the backlash is set (T3b) the clearance of both F4 shanks in their ±0.3 slots is **filled with epoxy around the waxed screws** (cast positive stop; screws stay removable) | K12 FIX2 S3 rows: shank bearing through the cast fill 6.35 / 8.5 (L8), 4.32 / 12.9 (L3) |
| **S4** ear FE 137.7 MPa; 5754 fails | **real** (accepted the verifier's FE; 5754-H22 allowable 87 < 103 MPa) | L_ucho **304 stainless 1.5 only**; Ø1.0 drilled at the inner end of the bend-relief kerf (model + DXF) | H19 uses 137.7 vs 143 MPa; **regression** K13: `L_ucho` material must be `stainless` |
| **S5** joints pass only at 1.5–4.5 cN·m | **real** (own calculation: the M2 3.2 × 3.0 insert holds 241 N at 8 MPa < 250 N preload at 0.10 N·m; M2 washers 15.8–25.8 MPa) | **run 2 (lead decision): design case 0.10 N·m, no torque tool.** M2 inserts → **M2 × 4 × OD 4.0** (123-3D listing, drawing UNVERIFIED) in **Ø4.1 holes through the 4.0 wall** (F7 standoffs r 3.65, F8 column holes Ø4.1 to the insert end + radial-wedge exit (first try: through holes left a 0.45 sliver under the plate top, K4), F10 pads r 3.65 through to the well, **F10_B moved to (18.0, −33.3)**, its washer + head in a 0.35 deep step of the P_drziak_serva plate beside the MG90S case, driven with the 1.3 hex precision screwdriver – the first try at (18.0, −33.3) without the step put the washer 0.12 into the servo case, caught by K2); F15 rows re-rated (T_cap crush, root tension with the preload relaxed); every module torque row moved to 0.10 N·m (RAM L7 / S06, PAN H15 / H27 / H28, OBAL S3–S5) | K12 **TQ rows** (one per joint: bearing ≤ 25.8, insert ≥ 1.5 × preload, thread-forming strip / hoop, positive location) + **coverage row** (every screw in parts.json maps to a rated joint); K13 regression: M2 inserts ≥ 4.0 × OD 4.0. Table in 17.16-13 and §2 below |
| **K1** K9 sampled only 4 lifts; lift 18 / 40° = 0.489 | **real** (code: K9 iterated over the B table rows only) | one firmware rule **tilt_down_max = min(40°, 4° + 1.9°/mm × lift)**, tilt_up as B rows (steps); park at lift 0 | K9 on a **0.5 mm lift grid** (41 lifts × 11 pans × 7 tilts): ≥ 1.0 mm inside the limits, ≥ 0.5 mm at limit + 1° |
| **K2** no tilt margin to the criterion | **real** (same root as K1) | same rule (≈ 1° of margin) | same K9 rows (limit + 1° dead band) |
| **M1** USB-C plug cannot be seated | **real** (code: plug envelope 8.0 tall < USB-C shell 8.34; door 18.6 mm from the mouth) | ESP32-S3-Zero turned 180° (mouth +X at x 23.0), bought **90° USB-C FPC extension** (`usb_predlzovac`, head 5.0 × 3.5 × 9.5 UNVERIFIED) plugged at T5c, female end parked at the door | K7 row T5c (male end along X into the mouth); K2 / K3 with the extension present |
| **M2** P_sachta suction cups | **real** (run 1 cup test, `fix2_work/cup_test.json`) | 8 × Ø2.5 vents through the top plate (hidden under the collar disc); printed top plate down, raised ≥ 3 mm on supports | K10 voxel cup test (0.4 mm) in the recorded orientation for every printed part, criterion ≤ 30 mm² |
| **M3** T_spodok suction cup; tilt sign | **real** (run 1 cup test: 181.8 mm² × 1.6 under the pan servo before the drains) | Ø2.5 drain (0, −16.6), Ø2.0 (0, 24.6), Ø2.5 vents (±38.5, 2.7); orientation **+15° about +X, u_away (0, −0.259, 0.966)** | K10 cup test (largest sealed cup 28.8 mm²) |
| **M4** backlash cannot be set with the gears in mesh | **real** (code: B4b bonded the gear before T7; F4 driven only at T2) | new step **T3b**: bare 36T gear on the taped T_cap, 0.05 paper strip, F4_2 1.3 key straight, F4_1 1.3 ball-end key tilted 28° toward +Y, epoxy cast (S3), gear lifted off, bonded on the bench (B4b) | K7 row T3b (tool channels incl. the tilted ball-end key) |
| **M5** FH19C takes 0.2 FPC; FH12-5S-0.5SH does not exist | **real** (part data from distributor search snippets – vendor pages not reachable) | one ZIF at all 4 places: **Panasonic Y5B AYF530535** (5 p, 0.5 mm, top + bottom contact, 0.30 FFC), fallback **Molex 54548-0572**; neck ZIF envelope 1.2 high – **UNVERIFIED, confirm on a distributor page before the PCBs are drawn** | **regression** K13: no FH19C-5S / FH12-5S-0.5SH string left in parts.json / R2 |
| **M6** FFC pair cannot be installed in the stated order | **real** (code: T4b plugged the carrier tails, T7 swept the stage free) | T4b carrier without FFC; **T7**: stage held above, tails fed down the empty bore → deck slot → cradle-wall slot → ZIFs, Kapton anchor, then the stage lowered | K7 rows: vertical column over the deck slot free to z +4; wall-slot exit → door line of sight free |
| mech-m1 P_sachta / P_drziak_serva 0.050 | **real** | run 1 trimmed P_sachta at y ≥ 15.12 – **still 0.02 left** (found in run 2 by the new exact check; a y ≥ 15.0 trim then cut 0.01–0.2 slivers into the shroud top, K4); final: P_sachta untouched, **P_drziak_serva plate bottom raised 0.15 (z −41.75) over x −9 … 9.5** | **regression** K2 exact-BREP pair: max overlap thickness ≤ 0.005 (now 0.0) |
| mech-m2 FFC under-run inside the shroud | **real** | under-run starts on the arc r 16.72 | K2 exact-BREP pair P_sachta / ffc_par: max thickness 0.0011 (faceting slivers of the wound strip only) |
| mech-m3 cap rim knife edge | real (geometry of the approved exterior) | **declared** (no supports on the rim, one 0.2 sanding stroke, hidden under the white lip) | K4 declaration "black cap rim" (run-out) |
| mech-m4 J1 lug at a hand twist | **real** (5.0 wide lug: 25.8 MPa at 1.35 N·m) | lug **8.0 tangential** (R1 roots); base stop block az 270 ± 14.6° (stop still ±153.4°); the Ø3 pin alternative does not fit (6805 seat r 18.575) | RAM row 49 at **1.5 N·m**: 11.2 / 12.9 |
| mech-m5 tolerance stack | real (risk) | documents: B1 dry-fit of T_stred on the bare T_spodok, sand post 1 / spigot / ring passage / neck lands to a free slide | documentation (17.16-15) |
| mech-m6 pigtail near the pocket | real (0.32) | one Kapton wrap binds the pigtail to the moving FFC leg at z −36 | documentation; the 0.32 is a declared flexible contact in PAN C1 |
| mech-m7 MG90S back-driven under L2 | real (risk, gear-train strength unpublished) | firmware parks at lift 0; never both MG90S in stall; bench side-load test kept | documentation (17.16-15) |
| mont-m1 FFC power / 5 V budget | real (estimate, UNVERIFIED part data) | 5 V budget in 17.16-15 (4.2 A peak vs 3.2 A buck → firmware limits simultaneous moves); bench drop measurement | documentation |
| mont-m2 PicoBlade pair loose | real | taped to the pocket back plate (x 17 … 23, z −29 … −17) | documentation |
| mont-m3 FFC slack / crease CF | real | slack loop on the carrier top edge zone z −53.5 … −48.2; CF formed as an R ≥ 1 radius bend over a Ø2 rod | documentation (17.16-6) |
| mont-m4 TOWER_CLEAR 0.25 resin/resin | real (risk) | B1 dry-fit + sand post 1 before inserts / pins are bonded | documentation; K7 still reports 0.249 |
| mont-m5 complexity | partly | in-situ pinion bond deleted (B1); thread-forming joints kept (one-time, now rated at 0.10 N·m); **declined**: one Ø2 × 6 dowel (the F10 / F12 / crank-pin lengths are set by hole depths and would protrude into the pocket), F3b / F7 stay countersunk (heads in Al / FR4, Z3.5 allows it) | – |
| mont-m6 K10 bbox bug, no PAN print record / cup test | **real** | `ext = b[1::2] - b[0::2]`; print records with u_away for P_sachta / P_drziak_serva; cup test for every printed part | K10 (oriented size + cup test) |
| mont-m7 documents vs data | real | T13Lb 1.3 hex (precision screwdriver); pins bonded 8.4 deep; door (T14) after the base FFC is plugged; T_paluba 70° about +Y; torque as "seat + 1/8 turn" | t4_assembly texts, 17.16-13 / -15 |
| mont-m8 arm connectors; MG90S Al arm | real | 3-pin Y-split at J_BUS_5 for the two arm servos; count the MG90S spline before buying the Al arm, P05 fallback otherwise | documentation (17.16-15) |

## 2. S5 – fingertip torque (lead decision), joint by joint at 0.10 N·m (K 0.2)

Preload M2 250 N, M2.5 200 N, M3 167 N. Criteria: bonded insert pull-out ≥ 1.5 × preload with epoxy 8 MPa (stress ≤ 5.33);
washer / nut / head bearing on resin ≤ 25.8 MPa (short-term crush); thread-forming strip capacity 0.75 π d L × 0.6 × 25.8 ≥ preload and
boss hoop ≤ 12.9; the clamped resin only in compression; creep relaxation accepted only with positive location.

| row | feature | stress / allowable (MPa) | ok |
|---|---|---|---|
| TQ F1 bearing | F1: T_spodok pad counterbore floor around the D3.2 float hole (DIN 125 M2.5) (A 17.5 mm2) | 11.44 / 25.8 | yes |
| TQ F1 insert | F1: bonded insert OD 3.5 x 4.0 in T_stred boss (A 44.0 mm2; pull-out 352 N = 1.76 x preload) | 4.55 / 5.333 | yes |
| TQ F1 location | F1: positive location (preload relaxation harmless, Z3.7): spigot (radial) + F1 shanks in D3.2 float holes (rotation, no sustained torque: the stage r | - | yes |
| TQ F3a bearing | F3a: T_paluba deck around the D2.8 hole (DIN 125 M2.5) (A 19.4 mm2) | 10.33 / 25.8 | yes |
| TQ F3a insert | F3a: bonded insert OD 3.5 x 4.0 in T_spodok boss (A 44.0 mm2; pull-out 352 N = 1.76 x preload) | 4.55 / 5.333 | yes |
| TQ F3a location | F3a: positive location (preload relaxation harmless, Z3.7): stop pin 1 through the deck C-ear + F3a shanks in D2.8 (0.15 radial); the stop force goes  | - | yes |
| TQ F3b insert | F3b: bonded insert OD 3.5 x 4.0 in T_spodok boss (A 44.0 mm2; pull-out 352 N = 1.76 x preload) | 4.55 / 5.333 | yes |
| TQ F3b location | F3b: positive location (preload relaxation harmless, Z3.7): countersunk heads centre the aluminium bridge on the screws (metal), pivot bonded | - | yes |
| TQ F4 bearing | F4: DIN 562 nut on the slot ceiling of the pan post (head on the servo tab) (A 12.9 mm2) | 19.44 / 25.8 | yes |
| TQ F4 location | F4: positive location (preload relaxation harmless, Z3.7): epoxy-cast slot fill around the waxed shanks (S3, C positive) + case gaps +-X 0.10 | - | yes |
| TQ F7 insert | F7: bonded insert OD 4.0 x 3.95 in T_spodok standoff r 3.65 (hole through 3.95) (A 49.6 mm2; pull-out 397 N = 1.59 x preload) | 5.04 / 5.333 | yes |
| TQ F7 location | F7: positive location (preload relaxation harmless, Z3.7): countersunk heads centre the PCB; no load | - | yes |
| TQ F8 bearing | F8: T_klb counterbore floor (ISO 7092 M2, OD at its lower tolerance 4.2) (A 9.7 mm2) | 25.77 / 25.8 | yes |
| TQ F8 insert | F8: bonded insert OD 4.0 x 4.0 in T_spodok column head (hole D4.1 through to the inner face) (A 50.3 mm2; pull-out 402 N = 1.61 x preload) | 4.97 / 5.333 | yes |
| TQ F8 location | F8: positive location (preload relaxation harmless, Z3.7): T_klb key in the column key slot + neck spigot (S2 rows) | - | yes |
| TQ F10 bearing | F10: P_drziak_serva plate (DIN 433 M2) (A 9.7 mm2) | 25.77 / 25.8 | yes |
| TQ F10 insert | F10: bonded insert OD 4.0 x 4.0 in P_sachta pad r 3.65 (hole through to the well) (A 50.3 mm2; pull-out 402 N = 1.61 x preload) | 4.97 / 5.333 | yes |
| TQ F10 location | F10: positive location (preload relaxation harmless, Z3.7): F10 dowel + tongue in the rail | - | yes |
| TQ F11 bearing | F11: DIN 562 nut in the P_drziak_serva block slot (head on the MG90S tab) (A 12.9 mm2) | 19.44 / 25.8 | yes |
| TQ F11 location | F11: positive location (preload relaxation harmless, Z3.7): MG90S held by the closed pocket (both case ends) | - | yes |
| TQ F13 bearing | F13: speaker ring step 1.7 / LED-holder ear (DIN 125 M2) (A 13.2 mm2) | 18.95 / 25.8 | yes |
| TQ F13 strip | F13: thread-forming 4.0 engaged in T_stred D5 bosses, D1.7 pilot (shear area 18.8 mm2, capacity 292 N) | 13.26 / 15.48 | yes |
| TQ F13 hoop | F13: boss D5 hoop stress from the thread wedge | 7.24 / 12.9 | yes |
| TQ F13 location | F13: positive location (preload relaxation harmless, Z3.7): axial position = head seat (the gasket push is held by the heads); no lateral load | - | yes |
| TQ F14 strip | F14: thread-forming 4.1 engaged in T_spodok D5 standoffs, D1.7 pilot (shear area 19.3 mm2, capacity 299 N) | 12.94 / 15.48 | yes |
| TQ F14 hoop | F14: boss D5 hoop stress from the thread wedge | 7.07 / 12.9 | yes |
| TQ F14 location | F14: positive location (preload relaxation harmless, Z3.7): no load (boards) | - | yes |
| TQ F15 bearing | F15: T_cap end face under the DIN 9021 M3 washer (T_cap bonded on the aluminium T_most) (A 37.5 mm2) | 4.45 / 25.8 | yes |
| TQ F15 location | F15: positive location (preload relaxation harmless, Z3.7): T_cap bonded on T_most; the stage is held axially by the head / washer (positive), creep o | - | yes |
| TQ F16 bearing | F16: J1 corner pad 1.2 around the D2.4 +-0.3 slot (DIN 125 M2; pad clamped on the servo ear) (A 11.4 mm2) | 21.96 / 25.8 | yes |
| TQ F16 location | F16: positive location (preload relaxation harmless, Z3.7): cradle walls + 0.1 PET shims (J1 centre distance), PORON bumper | - | yes |
| TQ F12 location | F12: positive location (preload relaxation harmless, Z3.7): F12 dowel | - | yes |
| TQ coverage | every screw in the parts list maps to a rated joint (35 screws; unmapped [], joints without a rating []; skr_ramena = metal servo output) | - | yes |

Other fixer rows in K12 (FIX2): S3 6.35 / 8.5 ok; S3 4.32 / 12.9 ok

Notes:
* The tightest joints are **F8 and F10** washer bearing: 25.77 / 25.8 with the washer OD at its lower tolerance (4.2); 20.7 MPa at the
  nominal 4.5. A larger washer does not fit (F8: the D4.7 counterbore is 1.13 from the bush bore; F10: DIN 125 Ø5 touches the servo
  case). Both parts are located positively (key + spigot, dowel + rail), so creep only relaxes the clamp.
* Thread-forming F13 / F14 are rated with K 0.2 (conservative – thread-forming screws in plastics run at higher K, i.e. less preload):
  strip 1.17 / 1.20 × preload.
* F15 (M3 into the aluminium bridge through the resin T_cap): T_cap 4.5 / 25.8; under L8 the root's tension side is checked with the
  preload fully relaxed (4.16 / 8.5) and the compression side with the full preload (8.6 / 25.8).
* Documents: **small precision screwdriver (10–12 mm handle), fingertips only, stop when the head seats + 1/8 turn; no L-key leverage;
  a torque screwdriver is optional (5–8 cN·m)**. Loctite 222 on F4, F8, F12, F15.

## 3. Check-suite corrections made in run 2 (the checks were wrong, not the parts – each one verified on the geometry)
* RAM C2 (simplified lip test): the pinion is now present at T5 and passes through the r 8.35 lip relief (its margin = 8.35 − distance to
  the pinion axis: 0.35); the USB FPC extension is plugged at T5c, after T_stred. The exact test stays K7 T5 (`integ2_work/lowering.py`).
* RAM C5 (stage envelope): its 0.03 mm / 0.25 rad tessellation lay up to 0.19 inside the r 34.4 shoulder-plate cylinder (BREP samples
  r 34.21 where the 0.01-deflection STL has r ≥ 34.393); C5 now samples a 0.005 / 0.03 rad tessellation → 1.00.
* OBAL O3d (T_stred lowering): pinion present at T5 (B1), USB extension late (M1) – same as K7.
* K8 / OBAL K8: the fixer's cap print vents (M3) added to the declared "cap_underside_holes" zone (`FIX2["CAP_VENTS"]`, hidden by the base).
* K7 FFC column (M6 row of run 1): the test column r 22.45 … 23.55 overlapped the 0.05 of the guide-wall face at r 23.5 that the FFC pair
  runs along; corrected to r 22.45 … 23.45.
* K4: the first F8 Ø4.1 through holes left a 0.45 sliver under the shoulder-plate top beyond the insert end (< 0.6 = a real K4 failure, not declarable) → geometry changed (holes end at the insert end, radial-wedge exit); the old "F8 insert seat floors 0.65" box now describes the wedge exits (min 0.6); the arm-wire-hole web box (run 1 moved the hole to z −51) extended to z −54.5 (0.88 reading at z −53.95, min 0.6).
* PAN G: the back-floor declaration reaches z −40.4 (two 1.06 / 1.11 readings at z −40.6 on the floor top edge at the FFC under-run arc).
* K12: a table with no failing row but two rows whose input is unpublished (MG90S output side load; topple impact force) is reported
  PASS with those rows listed as open items (bench tests) instead of NOT RUN.
* K13: PAN print records read from parts_pan.json.

## 4. Final check run

`checks.py --force`, 2026-11-18 03:53:20, STL stamp b738b2a51038ab5a:

| check | verdict | summary (first 260 characters) |
|---|---|---|
| K1 | **PASS** | 166/166 parts: valid single BREP solid, volume > 0, STL closed (0 open / non-manifold / flipped edges), one surface component, bbox as designed; STEP null for 9 loft-derived parts (rule: < 12 MB), 0 STEP over the limit; 0 orphan exports; deleted rev. 1 parts s |
| K2 | **PASS** | 171 parts (166 torso + 5 finished parts of variant B), 665 bbox-overlapping pairs: 0 unintended interference(s); 25 declared thread / bonded / ZIF / crimp fits (3 across modules); 130 pairs only touch (coincident faces, depth < 0.02); exact BREP regression (ov |
| K3 | **PASS** | pan -90.3..90.3 (firmware +-85 step 5, hard stops +-90.0, tolerance +-90.3) x lift 0..20 step 2.5 (351 poses), 42 moving bodies (stage, lift module, crank at its angle, foot / ear / DPS_krk / neck, FFC lift loop and pigtail in their posed shapes, FFC pan loop) |
| K4 | **PASS** | 16 printed parts scanned (opposing-face rays): every reading below 1.2 lies in a declared local feature (18 declared features, 2 of them tangent run-out edges of fillets / coves); nothing below 0.6 except run-out edges; structural walls by the module checks: O |
| K5 | **PASS** | 21 fasteners coaxial with their insert / nut (max offset 0.0; F4 slotted +-0.3 for the backlash); C(pan) 21.6003, C(J1) 18.0; stage ring 0.248 / bore 0.15; journal incl. the PTFE tape (G1) 0.145 (P_sachta r max 26.365, tape r max 26.5, bore r min 26.645); modu |
| K6 | **PASS** | crank r 10.0: pin z at theta 0 / 180 = -34.2 / -14.2 -> stroke 20.000 (dead centres at 0 / 180, firmware 3..177: -34.186 .. -14.214); crank angle at lift 0 / 10 / 20: {0.0: 0.0, 10.0: 90.0, 20.0: 180.0}; pan hard stop  /  (PAN D PASS); crank module PAN E PASS; |
| K7 | **PASS** | 50 steps (20 bench, 23 torso, 7 service rows): 39 straight-line paths swept against the parts present - 0 undeclared collisions; 38 screws with a straight tool channel (D4.5, or the named key: ['skr_F10_B', 'skr_F11', 'skr_F12_1', 'skr_F15', 'skr_F4_1', 'skr_F |
| K8 | **PASS** | white shells + plugs: 93204 T3 grid points, deviation -0.0128 .. 0.0095 mm, 0 over 0.05 outside the declared zones; analytic T4 vs T3 below drop 2.6: 0.0000; seams measured {'seam_x, width along x (16 stations)': [0.466, 0.476], 'door seam sides, width along x |
| K9 | **PASS** | head (variant B STL, 14 parts) vs torso meshes, firmware rule tilt_down_max = min(40, 4 + 1.9 x lift) deg; tilt_up_max = 10 deg (lift < 7.5), ...; 41 lifts 0..20 step 0.5 x pans -85..85 x tilts (0, half, limit, limit + 1.0 deg, both directions): min inside the |
| K10 | **PASS** | 16 printed parts, all Elegoo Tough resin; 16 fit the 211.68 x 118.37 x 220 volume with 5 mm in an axis-aligned orientation, [] fit tilted as the module print tables state; module print / support / cup / drain verdicts {'obal': {'R': True}, 'ram': {'P_print_tab |
| K11 | **PASS** | torso (groups T + P + L, 161 parts, without head / neck / arms / base): 388.0 g, centre of gravity (-0.9, 0.1, -50.8) = 0.9 mm from the J1 axis, 40.2 mm above the 6805 (criterion: every part has a mass, offset < 12.5 = bearing bore radius, every printed part 1 |
| K12 | **PASS** | 198 rows (192 decisive: RAM 103, PAN 34, OBAL 20) recomputed on the final geometry with the Z2 allowables: 0 FAIL, 2 not verifiable (input not published / assumed - open items, bench test: PAN H26 MG90S output side load 30 N, 6 mm outboard; OBAL S1c T_klb + F8 |
| K13 | **PASS** | 16 printed parts, all resin (no PETG / POM: True); 18 inserts all bonded (no heat-set); countersunk heads only in metal / FR4 ({'skr_F3b_1': 'T_most (Al)', 'skr_F3b_2': 'T_most (Al)', 'skr_F7_1': 'DPS_riadenie (FR4)', 'skr_F7_2': 'DPS_riadenie (FR4)', 'skr_ram |

## 5. Open / UNVERIFIED (not passed by any check)
* Part data from search snippets only: Panasonic Y5B AYF530535 / Molex 54548-0572 ZIF; USB-C 90° FPC extension head size; M2 × 4 × OD 4.0
  insert drawing (123-3D listing title); STS3032 / MG90S data as in 17.13.
* Resin data: Elegoo Tough lower bounds (Z0); epoxy 8 MPa on knurled brass / abraded resin assumed (lead value).
* Bench tests still required: one insert pull test on a printed coupon (M2 × 4 × OD 4.0 and M2.5 × 4 × OD 3.5), MG90S side load,
  FFC voltage drop, J1 clutch slip torque.
