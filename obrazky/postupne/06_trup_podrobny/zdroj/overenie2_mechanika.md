# T4 rev. 2 – adversarial verification, lens GEOMETRY / KINEMATICS / STRENGTH (overenie2_mechanika)

Verifier run of 2026-11-17 (22:00–23:40 UTC) on the STL set `bb776d9f640e8354` (165 parts). Nothing in the design files was
changed. Scripts, logs and JSON results are in `/tmp/claude-0/gapwf/fin/T4/overenie2_mechanika/`. All tests are my own code:
numpy / scipy point-to-triangle distances, a vertical-ray inside test, a 2-D plane-stress FE solver, mesh slicing, and
Blender BVH. No code from checks.py, checks_bl.py or the module checks was reused. The only design functions called are
the pose and cable-shape generators of `t4_pan.py`, used to pose the geometry for my sweeps.

**Re-runs.** `build_all.py` exits 0 and gives 165 parts. All 165 STLs are byte-identical to the integrator's (md5 lists
`stl_md5_before/after.txt`). `checks.py --force` took 2372 s, log `checks_verifier.log`, and reproduces the integrator's
table exactly: K1–K6, K8–K11 and K13 PASS; K7 and K12 FAIL.

**Verdict: not ready to print. No blocker in this lens, but 8 majors.**
- Three of them are real strength or fit defects that the K-checks pass because of how they measure:
  - the journal land / PTFE tape conflict (G1);
  - sharp loaded corners on the arm column, which K12 rates with Kt 1.3 (S1);
  - an R0 tongue rated against the normal-use allowable (S2).
- One K-check claim is false. K9 says no pose is below the criterion, but my run finds 0.489 mm at lift 18 / tilt 40 (K1).
- The other majors:
  - the pan-servo centre distance is held only by friction (S3);
  - one of the two documented ear materials fails (S4);
  - the specified resin-joint torques cannot be set with ordinary tools (S5);
  - the head tilt margin is about 1 degree everywhere in the firmware table (K2).

The kinematic envelope itself holds up. A finer sweep (pan step 1 degree / 2 degrees × lift step 1 mm, 2109 poses) confirms
K3's minimum undeclared clearance of 1.0. Exterior, seams, see-through, crank, gear geometry and watertightness pass.

## 1. Tests run (all on the final STLs)

| script | what | result |
|---|---|---|
| t01_stl_integrity.py | own manifold check: open / non-manifold / flipped edges, components, signed volume, bbox vs parts.json | 165 / 165 closed, 1 component each, volume within 0.2 % of parts.json, 0 orphan or missing STL |
| t02_rest_interference.py + t02b_recheck.py | every bbox-overlapping pair (722, incl. 8 B neck / collar parts): edge samples of A inside B (ray parity) → exact depth | only declared fits (threads, ZIF, crimp, tape) + **P_sachta ↔ P_drziak_serva 0.050** + **P_sachta ↔ ffc_par 0.635** (§3 m1, m2); all other contacts ≤ 0.01 |
| t03_sweep.py | pan −90.3…90.3 step 1° (stage, pan loop) / step 2° (lift bodies) × lift 0…20 step 1 (2109 poses); exact distance field of the static parts (0.25 mm grid) + exact point-triangle refinement both directions | no undeclared pair below 1.0; minima 1.0 (P_drziak_serva ↔ T_spodok, P_sachta ↔ pastorok_pan), 1.017 (MG90S corner ↔ column web, pan −61), 1.11 (lift FFC ↔ T_drziak_repro, pan −85, lift 0), 1.117 (foot ↔ F15 washer). K3 confirmed |
| t03b_stage_internal.py | lift group / crank / lift cables vs stage parts and each other, lift 0…20 step 0.25 | §4: only designed contacts below 1.0, plus the F12 head 0.40 and the pigtail 0.32 |
| t03c_j1_sweep.py + t03d_j1_stop.py | torso below z −83.5 vs base dummy, J1 −155…155 step 1° (0.25° near the stops) | stop contact at ±153.3–153.5°, 1.105 at ±150, pinion 1.0 |
| t04_sensitivity.py | ±0.15 per printed surface, ±0.10 hand-made metal, ±0.05 bought, ±0.5 cable shape, on every clearance < 1.3 | §3 m5 |
| t05_gears_loads.py | gear C from the STL axes, backlash / contact ratio vs C, Lewis + Hertz, F4 friction, L1 / L2 numbers measured on the STLs | §2 S3, §5 |
| t06_crank_ear.py | Scotch yoke on the real arm / pin / ear STL over θ 0…180, tolerance, rest gap, ear 2-D FE | §2 S4, §5 |
| t08a_column_fe.py + o2rsec.py | own raster sections of the column (z −9…−78) + 2.5-D plane-stress FE of the whole T_spodok tower under L5 | §2 S1 |
| t09_sharp_corners.py | concave mesh edges with one-edge turn > 50° (unfilleted) on every printed part, clustered | §2 S1, S2 |
| t10_walls_bl.py | wall thickness by inward ray (opposing faces only) on 10 structural parts | §3 m3 |
| t11_head_torso_bl.py, t11b_tilt_limits_bl.py | real B head (14 STLs) vs torso top, Blender BVH both directions, B-table rule / firmware 27.5 cap / linear, lifts 0…20, pan −90…90; max tilt for 0.5 / 1.0 mm per 0.5 mm lift | §2 K1, K2 |
| t12_exterior_bl.py, t12a_… | shells vs analytic T3 surface, 561 600 grid points (0.25 mm × 1440 per section); 2 M random see-through rays | §5 |
| t13_render_bl.py | T4 STLs rendered in the reference scene / hero camera of NOVA_celok.png | `t13_compare.png`, `t13_crop_front.png` |

## 2. Majors

### G1 (major) – P_sachta journal: the PTFE tape lies over resin lands at r 26.50, so the radial play is 0.02, not 0.15
* **Evidence.** In the tape band z −10…−3, P_sachta is not the r 26.37 cylinder that A2 / 17.3 specify.
  * Eight arcs reach r 26.50 (own slice, z −9.8 / −6.5 / −3.2): stage az 18.1–29.5, 59.2–64.3, 115.7–120.8, 151.5–161.9,
    198.1–208.5, 239.2–244.3, 295.7–300.8 and 331.5–341.9. Together they cover **63° of the circumference**: the four well
    corners plus four 5° bumps on the ring.
  * The tape `ptfe_pas_capu` (r 26.37–26.50) sits 0.135 inside P_sachta at these lands (t02b exact depth).
  * Wrapped over the lands, the tape's outer face is at r 26.63. The bore measures r 26.645–26.650 (own slice). That leaves
    **0.02 mm radial play on 63° of the circumference**. Any print error of a 53 mm resin journal, or of the bore, gives
    interference.
* **Why the checks pass.**
  * K2 declares the overlap as "film on its land, 37.4 mm³".
  * K5 / PAN A report "bore 0.150". That value is measured to the bare resin at r 26.50 and ignores the tape on top.
* **Reproduce.** `t02b_recheck.json` (pair P_sachta / ptfe_pas_capu). Slice P_sachta at z −6.5 and look at r > 26.40.
* **Fix.** Turn the journal band of P_sachta to r ≤ 26.37 at every azimuth for z −10.5…−2.5, cutting the 8 lands 0.13 deep.
  The remaining corner wall is 1.37 at az 24 / 156 (inner face r 25.0), so ≥ 1.2 still holds. The tape then gives r 26.50
  and 0.15 play, as designed.

### S1 (major) – arm column: the corners on the column's outer bending fibres are sharp, so K12's Kt 1.3 does not apply there
* **Evidence (t09, probes and own sections).** L5 is 10 N along X at the arm tip with the arm up, so M = 10 × (72 + (−17 − z))
  N·mm.
  1. **Corner z −48.2, x ±34.4, y 12.55…15.05.** This is where the bridge-wall top meets the column inner face. Probed at
     y 12.7 / 13.8 / 14.9 on both columns: no material at 0.05…0.8 mm along the bisector, so the corner is sharp.
     - The Ø4.5 arm-wire hole lies 0.85 below it (z −49.05…−53.55). K4 declares the 0.6 ring around it "unloaded".
     - The column-alone section just above the corner is 135.1 mm², Zy 209.6 mm³, with the extreme fibre at x 34.4.
     - M = 1029 N·mm gives **4.91 MPa nominal** at a sharp corner. That exceeds the 4.3 MPa Z2 limit for unfilleted notches,
       and with Kt ≈ 2.5 it is about 12 MPa against 8.5.
     - My 2.5-D FE (t08a, the whole tower with in-plane walls coupled, so a lower bound) puts the global maximum exactly
       there: **σ1 9.09 MPa at (34.38, −48.62)**, with 11.7 MPa compression on the other side.
  2. **Corner z −38, x ±42.0, y −9…15.** The column head overhangs the box closure plate by 1 mm at the outer extreme fibre.
     The edge is sharp (t09 cluster, 24 mm long). At z −38.5, Zy is 209.6 and M = 935 N·mm, giving **4.46 MPa nominal**,
     again above 4.3.
  3. The plate / box-top step at x 38.39, z −33.84 is also sharp (probe at y 0 / 8). There the nominal is only 2.4–2.9 MPa
     (Zy 300–370), so with Kt 3 it is about 8–9 MPa, borderline.
* **Integrator rows.**
  * At z −42, z −28 and z −30 the integrator passes the column as 6.02, 6.87 and 5.24 MPa with Kt 1.3. RAM row 42c passes it
    as "column + full-height bridge walls 2.9–3.2 MPa". Neither rates the junction corners.
  * The FAIL rows at z −26…−9 are consistent with my own sections: 6.7–8.9 MPa nominal, so Kt 1.3 gives 8.7–11.5. The 2.5-D
    FE lower bound there is 5.6–6.0 MPa.
* **Reproduce.** Run `t08a_column_fe.py`, `t09_sharp_corners.json` (T_spodok clusters at (34.4, 5, −48.2) and (42, 3, −38)),
  and the probe code in the log above (o2inside).
* **Fix.**
  * Add an R ≥ 1.5 fillet along the bridge-wall-top / column-inner-face edge on both columns. The fillet volume
    x 32.9–34.4, z −48.2…−46.7 at |y| 12.5–15 is r ≥ 35.2 from the axis, outside PAN_ENV2 + 1.0 (34.4), 1.3 from the deck edge (r ≤ 34.2) and away from the lug sweep
    r ≤ 31.6.
  * Move the arm-wire hole ≥ 4 mm lower (z ≤ −55), or into the rib.
  * Give the head overhang at z −38 / x 42 an R ≥ 1 cove, or make the closure plate flush with the head at x 43.
  * Re-rate these corners in K12 with the notch allowable 4.3 MPa, or with an R-based Kt. This comes in addition to the open
    column FE item of the integrator.

### S2 (major) – K12 row PAN H13 (pocket tongue, R0 declared) is rated against 8.5 MPa; Z2 caps unfilleted notches at 4.3 MPa
* **Evidence.**
  * K12 row: "pocket tongue 2.9 × 1.5 (cantilever from the plate, **R0 declared**), L2 30 N lift 20: 5.22 / 8.5".
  * Z2 says "unfilleted notches ≤ 4.3 MPa". The PAN H10 turret-wall root (also R0) is correctly rated against 4.3.
  * t09 finds the 42.6 mm sharp concave edge along the tongue root at y 15.1, x −4.2…14.2, z −39.35…−36.45.
  * So **5.22 > 4.3 is a hidden FAIL**.
* **Fix.** Either put an R0.5 at the tongue root, or make the tongue 2.0 thick instead of 1.5:
  5.22 × (1.5 / 2.0)² = 2.9 MPa, which passes. Then re-run K12.

### S3 (major) – the pan-servo centre distance is held only by friction of resin (Z3.7). At stall the margin is 1.05–1.6 before any creep
* **Evidence (t05 + own gap measurement).**
  * Measured gaps between the STS3032 case and T_spodok:
    - +Y face to the cradle front wall: 0.30;
    - −Y face: 0.543;
    - ±X ends: **0.10**.
  * So the X component of the gear reaction is taken positively, after 0.1 mm. The Y component is held only by the two F4
    screws through holes slotted ±0.3 along C. The tab is clamped on the resin post at the RAM torque of 0.02 N·m, which is
    50 N preload per screw.
  * Friction capacity, with 2 screws and 2 faces: **40 N at µ 0.2, 60 N at µ 0.3**.
  * Reaction at L8 (STS3032 stall 4.5 kg·cm @ 6 V, confirmed in retailer listings): Ft 61.3 N, Fr 22.3 N, C unit
    (−0.271, −0.963). The worst **Y component is 21.5 + 16.6 = 38.1 N** away from the gear; under L3 it is 25.9 N.
  * The margin is 1.05 (µ 0.2) to 1.6 at full preload, and Z3.7 expects the clamp preload on resin to relax. Once it slips,
    the servo walks to the slot end at ΔC = +0.3:
    - backlash 0.236 mm at the pitch circle, which is **0.9° of head play**;
    - contact ratio 1.61 → 1.26.
* **Fix.** Make the C setting positive in Y. After setting the backlash (C 21.655–21.71 gives 0.04–0.08), either:
  * bed both F4 shanks on the −C side of their slots with epoxy, or a pressed 0.3 shim;
  * or add a printed abutment with 0.1 PET shims behind the case's −Y face. There is 0.543 of room, so a shim pack works.

### S4 (major) – metal ear: own 2-D FE gives 137 MPa at the plate root. The spec's first-named material, 5754-H22 2.0, fails
* **Evidence.**
  * Model: t06, plane-stress Q4 FE of the real L_ucho slice (pixel 0.05). The flange / bend zone (y ≤ 11.4, z ≤ −36.5) is
    fixed. Load is 30 N on the slot edge at y 23.2, the TDC pin position.
  * **Von Mises 137.7 MPa (L2) / 136.9 MPa (L1 × 2) at (y 13.07, z −37.73).** This is the plate root next to the 0.3 relief
    kerf, where the whole moment passes through the 4 mm-high bend zone. The 231 MPa at the fixed corner is a fixity
    artefact and is not used.
  * PAN H19 uses 100 MPa, scaled from the rev. 1 FE.
  * 304 1.5: 137.7 / 143 (215 / 1.5), so 0.96, passes with almost no margin.
  * Spec A9 / 17.5 name **"5754-H22 aluminium 2.0"** first. In-plane bending scales with 1 / t: 137.7 × 1.5 / 2.0 = 103 MPa
    against 130 / 1.5 = 87, so **FAIL**.
  * 6061-T6 2.0: 103 / 160, passes.
* **Fix.**
  * Delete 5754 from the ear options in A9 / 17.5 / 17.8, leaving 304 1.5 or 6061-T6 2.0.
  * Drill Ø1.0 at the end of the relief kerf, so the root is a round instead of a saw-cut slit.
  * Correct row H19.

### S5 (major) – the resin-joint torques that make K12 pass (0.015–0.045 N·m) cannot be controlled. At 0.1 N·m the joints are over the limit
* **Evidence.** The K12 tightest rows are:

  | joint | stress / limit | torque |
  |---|---|---|
  | F1 / F3a washer on the pad | 3.99 / 4.3 | 0.045 |
  | F16 | 3.95 / 4.3 | 0.025 |
  | F4 nut | 3.89 / 4.3 | 0.02 |
  | F8 washer | 3.87 / 4.3 | 0.015 |
  | F7 / F8 inserts | 2.49 / 2.7 | 0.03 |

  These are 1.5–4.5 N·cm, below the range of ordinary torque screwdrivers. A small hand driver easily reaches 0.1 N·m.
  At 0.1 N·m (own calculation, K 0.2):
  - M2.5 + DIN 125: 200 N on 22.6 mm², **8.9 MPa**;
  - M2 + ISO 7092: 250 N on 12.1 mm², **20.7 MPa**;
  - insert bond on M2: about 8 MPa against 2.7.
* **Fix.** Make the joints tolerant of 0.1 N·m:
  * DIN 9021 / DIN 433 large washers where there is room (M2.5 9021: 44.5 mm² gives 4.5 MPa);
  * or brass compression sleeves that put the head load on metal;
  * or prescribe a preset cN·m torque driver (2–15 cN·m class) and say so in the build list.

### K1 (major) – K9 PASS is false: the B tilt table allows 40° at lift 18 and the head comes within 0.489 mm of the torso top
* **Evidence (t11, Blender BVH, pans −90…90).**
  * B-table row −2 (= T4 lift 18) allows a 40° nod down. The clearance is **0.489 mm at (0, −29.6, 4) between T_stred and
    ram_displeja**, below the 0.5 criterion. The result is the same at every pan.
  * K9 sampled only lifts 20 / 12.5 / 7.5 / 0 and missed rows 2.5, 5, 10, 15, 16–18.
  * The same rule gives 0.666 at lift 10 (tilt 25) and 0.517 at lift 12.5 (tilt 30).
  * The spec's firmware sentence "lift 10…15 → tilt down ≤ 27.5°" is dangerous if read as an allowance: **at lift 10 and
    tilt 27°/28° the clearance is 0.001 / 0.0** (contact). Sensitivity at pan 0: lift 10, tilt 25 → 0.666, 26° → 0.151,
    27° → 0.001.
* **Fix.** One continuous firmware rule, shown in the t11b table to keep ≥ 1.0 mm at every lift 0…20:
  **tilt_down_max = min(40°, 4° + 1.9°/mm × lift)**. Tilt-up rows of the B table keep ≥ 1.0 already. Write it into the
  firmware limits instead of the B table + 27.5 row.

### K2 (major, same root) – the tilt table has only 0.0–0.7° of margin at every row
* t11b gives the maximum nod-down for 0.5 mm at each B row lift: 5.5 / 10.7 / 15.6 / 20.5 / 25.3 / 30.0 / 39.9 at lifts
  0 / 2.5 / 5 / 7.5 / 10 / 12.5 / 18. The B rule allows 5 / 10 / 15 / 20 / 25 / 30 / 40.
* An MG90S tilt servo's dead band and horn backlash are about 1°. The crank error at mid-lift is 0.17 mm/° (t06), and the
  clearance grows about 1 mm per mm of lift.
* So the as-built head will touch the painted torso top at the rows unless the table is derated. Same fix as K1.

## 3. Minors

| id | part | problem | evidence | fix |
|---|---|---|---|---|
| m1 | P_sachta ↔ P_drziak_serva | 0.050 mm interference between two resin parts, not flagged by K2, whose depth criterion is ≤ 0.02 | t02b, at (−8.19, 15.26, −41.85), back-floor edge vs pocket bottom | trim the pocket bottom 0.1 locally, or chamfer the back-floor edge |
| m2 | ffc_par ↔ P_sachta | the FFC riser "under" run starts at x 14.96, so 0.635 mm of strip lies inside the drum shroud (r 15.95–16.7). K2's half_depth 0.052 hides this | t02b, at (15.05, 5.6, −41.6) | start the under-run at r 16.7 and add an R0.3 edge to the groove entry. The groove must cover the real crease |
| m3 | T_spodok black cap rim | knife edge all round the perimeter at z −81.5…−82.5: 0 → 0.6 mm thick inside the outer 0.6 mm (~300 mm long). The horizontal mating face cuts the tuck-under surface at a shallow angle. K4 claims nothing below 0.6 except declared run-outs | t10_walls_opposing.json cluster n 7222, min 0.000; section y 0, x 42.6–43.1 at z −81.55…−81.6 | give the rim a 0.8 vertical land by lowering the mating face locally, or declare it and add a handling note (it chips at support removal) |
| m4 | J1 stop lug (RAM 49) | the clutch does not limit a hand turning the torso into the ±153° stop; abuse is rated at 0.6 N·m only | own check: 5.0 × 2.35 root, lever 2.65, Kt 1.4: 25.8 MPa at **1.35 N·m** torso torque (easily done by hand on a 105 mm body) | the documented alternative: Ø3 steel pin bonded 6 deep at r 19 |
| m5 | tolerance stack (t04) | clearances that drop below 0.7 or to ≤ 0 with the per-surface errors: TOWER_CLEAR 0.249 → **−0.05** (stop post 1, plus shell warp); spigot 0.206 → −0.09 (locating fit, sandable); golier ring 0.248 → −0.05 (stage passing the glued ring); P_drziak_serva ↔ cradle wall top 1.0 → 0.70; drum ↔ pinion top 1.0 → 0.80; MG90S corner ↔ column 1.017 → 0.82; lift FFC ↔ speaker holder 1.11 → about 0.5 (free FFC loop shape) | t04_sensitivity.json | file-to-fit notes for post 1 and the ring; keep ≥ 1.3 where free (Z3.12) |
| m6 | MG90S | under L2 at mid lift the crank back-drives the servo at 30 N × 10 mm = 0.30 N·m, which is 1.4 × its stall torque (0.177 / 0.216 N·m at 4.8 / 6 V). Gear-train strength is UNVERIFIED | t05 L2 | firmware: park at lift 0 whenever idle; document the risk |

## 4. Stage-internal and J1 sweeps (t03b, t03c, t03d) and the tolerance study (t04)

**Inside the stage (t03b, lift 0…20 step 0.25, own exact distances).** Every pair below 1.0 is a designed contact or fit,
except the cable item below.
* Designed contacts: arm hub on the spline 0; FFC continuity 0; pin in slot 0.10; arm screw head 0.121; rest gap foot / ear
  0.15; neck halves on the PTFE lands 0.17; neck in the collar-disc opening 0.25 (B); neck to the well 0.30; foot to the
  lands 0.37; ear to arm 0.40.
* **F12 screw head ↔ P_sachta 0.40** at lift 0, in the back window.
* **Pigtail ↔ P_drziak_serva 0.32** at lift 4.25. The pigtail is a free wire bundle whose shape PAN calls "guessed", so it
  will rub the pocket. Fix: a tie point on the foot so the bundle cannot swing toward the pocket.

**J1 (t03c / t03d).**
* The lug reaches the base stop block at **±153.3…153.5°**, the same as RAM's ±153.37.
* At the firmware ±150° the lug is 1.105 from the block, which is 3.4° of margin.
* The J1 pinion stays 1.0 from the dummy hub at every angle.
* Nothing else of the torso comes within 3 mm of the base dummy.
* K3's J1 row is confirmed.

**Tolerance (t04).** Worst case = nominal − (per-surface errors of both parts). The items that matter physically:

| pair | nominal | worst | consequence |
|---|---|---|---|
| T_stred lowering over stop post 1 (TOWER_CLEAR) | 0.249 | −0.05 (+ shell warp) | T5 can bind → file-to-fit note on post 1, or move pin 1 inward 0.25 |
| spigot locating fit | 0.206 | −0.09 | sand the spigot (declared fit) |
| P_sachta lands + tape ↔ bore (G1) | 0.02 | −0.28 | **no running play** → G1 fix |
| journal ring (after the G1 fix) ↔ bore | 0.15 | −0.15 | sand to fit (already in the drill table) |
| stage / collar disc ↔ glued ring | 0.248 | −0.05 | the stage may not pass the ring upward (D1 service path) → sand note |
| neck halves ↔ PTFE land strips | 0.17 | −0.03 | lift can bind → sand / second tape layer note |
| koleso_pan bore ↔ taped T_cap | 0.02–0.06 | −0.08…−0.14 | tape wraps adjust it (declared) |
| P_drziak_serva lug ↔ cradle wall top | 1.00 | 0.70 | ok, below the preferred 1.3 |
| drum ↔ pan pinion top | 1.00 | 0.80 | ok |
| MG90S corner ↔ column web (pan −61) | 1.017 | 0.82 | ok |
| lift FFC loop ↔ T_drziak_repro (pan −85, lift 0) | 1.11 | ≈0.5 | a free FFC loop varies by more than its 0.15 tolerance → rubbing at pan < −80 possible; keep firmware ±85 |
| F12 head ↔ P_sachta window | 0.40 | 0.20 | ok |


## 5. Claims verified (no finding)

**Watertightness, interference, envelope.**
* STL watertight, 165 / 165.
* No undeclared rest interference other than m1 / m2.
* Pan × lift sweep at a finer grid than K3: undeclared minimum 1.0. The OBAL front stack is cleared at 1.11 (pan −85,
  lift 0), matching K3's 1.109.

**Gears.**
* C(pan) 21.6003 and C(J1) 18.000 from the STL axes.
* Contact ratio 1.61 (pan) and 1.53 (J1).
* Backlash with standard gears: 0.04 / 0.08 needs ΔC +0.055 / +0.110. Each 0.1 J1 shim gives 0.073.
* Lewis, pan (L8): 62.0 MPa on the 18T, 50.8 on the 36T. Hertz steel on brass: 485 MPa at stall, 280 at rated torque.
* J1 Lewis at the 0.40 N·m clutch: 36.0 MPa.
* Spline bonds at 10 MPa: 1.18 / 1.16 N·m.

**Crank.**
* r 10.000 and pin Ø2.000 (measured); stroke 20.000; dead centres at 0 / 180.
* Pin-to-slot clearance 0.10 everywhere, 0.62 at the firmware ends of 3° / 177°.
* The slot end tolerates an ear error of −0.62…+0.6 mm in the firmware range.
* Metal around the slot end is 0.83.

**L1 retention (30 N).**
* DIN 9021 overlaps the gear by 0.50, or 0.43 at the worst bore offset: 2.25 MPa on brass.
* Washer bending 22 MPa.
* Hub-disc bond 519.5 mm², 0.058 MPa.

**L2.**
* Lift 0: the foot lands on 305.5 mm² of hub disc, 0.098 MPa. Rest gap is 0.15 nominal, 0.05 with the head weight on the
  pin (slot play 0.20).
* PTFE washer 0.08 MPa.
* Lift 20: pin shear 9.5 MPa and bending 36 MPa (steel); the MG90S side load of 30 N remains UNVERIFIED.

**Exterior and seams.**
* Exterior against T3 below drop 1.5: −0.30…+0.056. The negative values are the seam edges at x ±33.2 and the door seam.
  The plateau r ≤ 30 at z 4 deviates by up to +0.44, which is the declared collar-plateau zone.
* See-through: 0 of 1 775 132 random rays that cross the T3 hull.

**Head clearance at the B table's own points.**
* K9's 0.517 at lift 12.5 / tilt 30 reproduces exactly.

**Render.**
* The T4 STLs in the reference scene match NOVA_celok.png in silhouette, seams, light bar and grille position
  (`t13_compare.png`).
* Visible differences: the grille pill shows 5 sound slots where the reference is plain grey, and the light-guide edge is
  slightly brighter. Both are approved details. The background difference comes from compositing.

## 6. Not done / limits (do not treat as passed)
* No 3-D FE. The column and ear numbers come from my 2-D / 2.5-D FE and sections:
  - the column lower bound couples all y-layers;
  - the ear fixity at the bend is idealised.
* The T_bok share of the column load is not modelled, as for the integrator.
* TOWER_CLEAR / spigot lowering was not re-measured independently. The numbers in m5 are the integrator's 0.249 / 0.206.
* The stop-bridge / lug junction of P_drziak_serva has a sharp edge at (−16.8, 20…26.8, −41.9) (t09). I did not FE it.
  K12 H5 (7.89 / 8.5, Kt 1.3) may be optimistic there.
* Bought-part data:
  - STS3032 4.5 kg·cm @ 6 V, STS3215 19.5 kg·cm @ 7.4 V and MG90S 22.8 × 12.2 × 28.5 mm (matches the model) come from
    retailer listings and servodatabase (search snippets). No manufacturer PDF was reached.
  - The MG90S output side-load rating is not published anywhere I could find.
* The large intermediate files `t03_static_df*.npy` were deleted; `t03_sweep.py` rebuilds them in about 6 min.
