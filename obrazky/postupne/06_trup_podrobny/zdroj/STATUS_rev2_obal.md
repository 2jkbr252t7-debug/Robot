# STATUS rev. 2 – CAD builder, module OBAL (shells + front stack + shoulder joints), 2026-11-17

Rework of `t4_obal.py` / `checks_obal.py` to T4_spec.md §17, `t4_common.R2`, `rev2_arch/ULOHA_obal.md` and the resin rules
(T4_zivica.md Z0–Z5; Z2 allowables normal 8.5 / sustained 4.3 / abuse 12.9 / epoxy 2.7 MPa). Backups (rev. 1):
`rev2_backup/t4_obal.py.obal.bak`, `checks_obal.py.obal.bak`, `parts_obal.json.obal.bak`, `checks_obal.json.obal.bak`,
`STATUS_obal.md.obal.bak`. `t4_common.py`, the RAM / PAN modules and /fin/B were NOT edited. Module-local numbers are in the block
`# >>> additions by obal rev2` of `t4_obal.py` (also `parts_obal.json["additions_obal_rev2"]`); keys of `t4_common.OBAL` that rev. 2
supersedes are in `OBAL2_OVERRIDES` (`parts_obal.json["overrides_of_common_OBAL"]`) for the integrator.

## Files (all in /tmp/claude-0/gapwf/fin/T4/)
* `t4_obal.py` – `build()` registry (55 parts), `python t4_obal.py` builds from the cached BREPs (rev. 1 `cache/obal_v1_*` reused where a
  step did not change, rev. 2 steps `cache/obal_v2_*`), prints validity / volume / bbox / time, exports STL (`export_abs`, absolute
  deflection 0.01) to `stl/`, STEP (< 12 MB) to `step/`, writes `parts_obal.json` (per printed part a `print` record), deletes the
  exports of removed parts. Full T_stred rebuild ≈ 7–9 min (longest single boolean 151–187 s, the ledge fuse); from cache ≈ 45 s.
* `checks_obal.py` → `checks_obal.json` (O1, O3a–d, O4, O5, R, S + merged mesh / K8 results), log `obal2_work/checks4.log` (≈ 15 min).
* `obal2_work/mesh_checks2.py` (Blender BVH) → `obal2_work/mesh_checks2.json`: M1, M2, M3, O2, S1, F1, X1 (≈ 30 s).
* `obal2_work/k8_obal.py` (Blender) → `obal2_work/k8_obal.json`: K8 exterior vs the approved T3 surface + see-through from 26 views
  (pitch 0.25, scene = OBAL + RAM group T + PAN groups P / L / T + B collar ring / disc / neck halves) (≈ 3 min).
* `obal2_work/meshlib.py` (sampling, exact distances, pan × lift sweep, lowering, print bbox, support faces, voxel cup finder),
  `obal2_work/ffc_front.py` (FFC / pigtail vs front stack, brute force), `obal2_work/prev2_obal.py` (previews).
* Previews (600 px, 12 samples, all looked at): `prev2_obal_iso.png`, `_zad` (back, door), `_rez_x0` (section x 0), `_det_lozisko`
  (bore + shoulder + collar ring + stage journal), `_det_jazyk` (door top seam section), `_det_jazyk_zvnutra` (tongue from inside),
  `_rez_klb` (T_klb section with T_bok, screws, washers, column), `_klb_krk`, `_klb_koniec`, `_predna_zostava` (front stack from
  inside), `_f1_stlpik` (F1 boss + insert), `_kontext_rez_x0` (section with RAM + PAN + B).

## What changed (rev. 1 → rev. 2)
| part | change |
|---|---|
| T_stred | journal bore **r 26.65 for z −10.5…−2.0** (measured 26.645…26.650) with 0.5 × 45° lead-in (r 27.145 at −10.5), **shoulder z −2.00**, ring seat r 28.35 above unchanged, tube wall **3.945**; F1 bosses **r 3.4** (insert wall 1.598–1.599; bonded M2.5 OD 3.5 × 4.0 in Ø3.6 × 4.3 + Ø2.8 pilot); **door top-seam tongue** inset 1.35…2.2, z −12.75…−11.75, \|x\| ≤ 20.6; vents **Ø2.5** at z 0.0 through the collar tube only; built with the rev. 1 recipe from the cached blank (cavity add-ons → shell → cuts → pads → ledge). 37.33 g |
| T_dvere | hook tabs **and roots deleted** (cavity has only the 4 magnet bosses); top edge stepped for \|x\| ≤ 20.85: lip inset 0…1.25 up to z −12.0, inner half stops at z −13.0; ledge, 4 magnet bosses, finger notch unchanged. 8.73 g |
| T_klb_L / _P | neck **x 38.6…40.6**; **R0.5 undercut** at the shoulder x 40.6 (measured 0.49–0.503); **R0.5 fillet** at the step x 50.956 (0.488–0.503); key tip x 37.0, width 2.9, **r 5.6…10.6**, root **R0.2**; **F8 at az 60/180/300**: Ø2.3 + counterbore **Ø4.7** to x 45.0 for an ISO 7092 M2 washer; **magnets Ø3.1 × 2.1 at az 0/120/240**; bush bore Ø8.05 / recess Ø10.2 / wire groove unchanged (frozen). 8.65 g each |
| T_drziak_repro | resin (was PETG); **ring 2.0**, **closed** (rev. 1 wire notch removed), ro 16.5, ears r 3.2; 0.3 open steps (radial slots 6.6 wide) under the 3 DIN 125 washers. 0.75 g |
| T_drziak_led | rev. 1 + 0.3 open steps under the 2 DIN 125 washers (F13 engagement 4.0) |
| bought | F8 = ISO 7380 M2 × 10 + ISO 7092 M2 (2.2 × 4.5 × 0.3); F13 = M2 × 6 thread-forming + DIN 125 M2 (5 washers modelled); magnets at new azimuths; `vyvod_repro` moved into the ring hole |
| deleted | T_puzdro_L / T_puzdro_P (POM), pruzina_klb_* (exports removed), door hooks |
Unchanged (re-exported): T_bok_L / T_bok_P, T_svetlovod, T_mriezka. Printed mass 97.37 g (rev. 1 99.66 g), bought 14.69 g.

## Deviations from §17 / ULOHA (each with its reason; full text `parts_obal.json["deviations"]`, first 13 entries "REV2 …")
1. **Door top seam split** – door lip inset 0…**1.25** (spec 1.1), 0.1 gap, tongue **1.35…2.2 = 0.85** (spec 1.1…2.2): the spec makes
   the two faces touch (a second depth stop) and leaves the HANDLED lip 1.1 < 1.2 (Z3.1); 1.2 measured 1.15 on the mesh (the inset loft
   deviates ≤ 0.05), hence 1.25. The tongue is unloaded and not handled (Z3.1 allows < 1.2).
2. Door inner half removed to **\|x\| ≤ 20.85** (spec 20.6) → 0.25 beside the tongue ends instead of a touching patch.
3. F1 bosses keep the rev. 1 cone top (z −75…−72.2) and blind pilot to −74.7 (spec "pilot 1.0").
4. Vents Ø2.5 at **z 0.0**, \|x\| ≤ 30.75 (the Ø2.5 hole at z 0.4 notched the inner top corner: skin 1.84).
5. Door-frame magnet pads keep the rev. 1 trim (PAN_ENV_REV1, r 35.0 at z −24) – 1.6 outside PAN_ENV2.
6. **Shoulder R0.5 as an undercut** (relief groove) – a plain fillet would stand 0.25 into the T_bok seat-flange hole (T_bok unchanged);
   clamp face r 12.0…13.5 still overlaps the column stop ring through the flange. R1.0 used nowhere (flange at 40.6, arm-hub interface at
   50.956).
7. **Key r 5.6…10.6** (rev. 1 7.0…10.9): the old outer corners were 0.004 inside the neck rim (no root fillet possible); RAM's slot is
   r 5.3…14.0. Key root R0.2 only (the 0.2 gap to the boss face is all the room outside the slot).
8. **F8 counterbore Ø4.7** (spec Ø4.2) + **ISO 7092 / DIN 433 M2 washer Ø4.5** (spec DIN 125 M2 Ø5.0 does not fit: Ø5.2 would leave
   0.88 to the bush bore). Walls 1.126 to the bush bore, 1.151 to the D22 journal (declared local, not in the screw load path).
9. **F13 spot steps** 0.3 under the washers (ring + LED-holder ears): ring 2.0 + washer 0.3 would leave 3.7 < 2 d of thread; the 270°
   speaker boss cannot take a deeper pilot (skin 0.76). Round spot faces left 0.1–0.5 rims → open steps. Engagement measured 4.0 on all 5.
10. **Speaker ring closed** (rev. 1 notch removed), ro 16.5: the notch left a 20 mm cantilever (7 MPa sustained); wires leave backward
    through the ring hole.
11. T_stred print orientation changed to "lower edge to the plate, 40° about Y" (searched: 20° about X put 335 mm² of exterior on
    supports; 40° about Y 68 mm², no supports on the bore).
12. Recommended torques (row S): F8 **0.015 N·m + Loctite 222**, F13 **0.03**, F1 **0.045** (spec 0.05 / 0.04 / 0.09 exceed Z2 – see S).

## Checks actually run (final geometry; `checks_obal.json`, `obal2_work/mesh_checks2.json`, `obal2_work/k8_obal.json`)
| check | result | verdict |
|---|---|---|
| O1 solids | 55/55 valid single solids, watertight STL, bbox as expected; deleted parts gone (STL + STEP removed) | PASS |
| M1 / O2 | watertight; 106 bbox pairs, 0 unintended interference (thread-forming screws in pilots, washer contacts declared) | PASS |
| M2 walls | 105 201 through-wall rays: min 1.201, p01 2.191, median 2.199; < 2.0 undeclared 0, < 1.2 0; declared: door lip 1.201+, LED pilots 1.302, speaker pilots 1.779; socket-rim wedge 0.944 (rev. 1, approved look) | PASS |
| M3 exterior | 127 345 grid points: −0.0128…+0.0038 mm, 0 over 0.05 outside declared gaps; seams x 0.466–0.476, door 0.225–0.236 | PASS |
| **K8** | exterior vs T3: 0 bad points in the strict zones; **see-through 0** of ≈ 6.8 M rays from the **26 views** (no hooks; rev. 2 scene) | PASS |
| S1 seams | **door top centre (tongue): 0 / 389 open**; door sides / bottom / corners 0; seam x 0 / 3 140; seam x top 0 / 730; **seam lower ends x ±33.3**: in-plane rays 28 / 140 enter the shell below the lip (rev. 1 declared, none see-through), **x-tilted rays ±6 / ±12° toward the spigot notch 0 / 112 open** (RAM spigot present at \|x\| ≥ 32.9) | PASS |
| O4 seats / rev. 2 dims | bore 26.645–26.650 (± 0.01 ✓; measured z −9.9…−2.1 – the ULOHA window −10.4 lies inside the required 0.5 lead-in, r 27.05 at −10.4), shoulder flat at −2.00, ring seat 28.345, chamfer 27.145, tube wall 3.945 (≥ 3.9 ✓), F1 walls 1.598–1.599 (≥ 1.6 within 0.002 mesh), tongue inset 1.35–2.21 / z −12.75 / to \|x\| 20.6, door lip 1.256 / −12.0 / −13.0 / 0 hooks, T_klb neck 38.6 / key tip 37.0 / undercut 0.49–0.503 / fillet 0.488–0.503 / key root 1.477 at 0.15 from the face, F8 Ø4.7 / Ø2.3, magnets Ø3.1, frozen bores, ring 2.0 / steps, F13 engagement 4.0 × 5 | PASS |
| O5 inside | every internal part inside inset 2.2 (declared: LED screw tips 0.68 into the pilot / skin 1.5); shells ≤ 0.004 outside the exterior | PASS |
| R / K10–K13 | all printed parts resin, fit the Saturn 4 Ultra 16K with 5 mm margin + 5 mm supports (largest T_stred 104.5 × 77.4 × 106.7); supports on visible faces: T_stred 68 mm² (lowest −X band, sand), T_klb 0 after excluding the hidden shoulder / undercut (see json), all others 0; no supports on fit faces; max sealed layer (cup) area: T_stred 31.5 mm² (blind insert / magnet pockets), T_klb 22.5 (3 magnet pockets × 7.5), all others 0; vents Ø2.5; no heat-set, no countersunk head on resin, washers under every head, inserts wall 1.6 / engagement 4.0, thread-forming engagement 4.0, no flexing feature | PASS |
| S strength (Z2) | all check rows and recommended-torque rows pass: T_klb shoulder 1.57 (L5) / 0.54; key root 7.13 / 8.5 (L5 0.25 N·m, Kt 1.8), flank 4.41; F8 washer bearing 3.87 / 4.3 at 0.015 N·m; F13 3.23 at 0.03; F1 bond 2.05 / 2.7, boss 3.45 / 4.3 at 0.045; journal 0.04 / 0.27 MPa; tube 0.18; door notch 2.33; magnet bonds; ring 3.34 / 2.48 (closed, soft gasket). **Spec torques fail Z2** (documentation finding): F8 0.05 → 12.9, 0.03 → 7.7 MPa; F13 0.04 → 4.31; F1 0.09 → 4.09 (epoxy) / 6.89. S1c topple capacity ≈ 361 N vs assumed 229–686 N impact = ESTIMATE (K12 / drop test) | PASS (see notes) |
| O3a static vs RAM / PAN-T meshes | 49 pairs < 2 mm, all contacts declared (lip/spigot fit, F1 boss on pad, flange on stop ring, inserts / screws); undeclared min 0.557 (speaker-ring screw ↔ STS3032 case); **RAM rib top ↔ T_bok socket tube 0.10** (X1, static, both modules unchanged there – see notes) | PASS |
| **O3b pan × lift sweep (real PAN meshes)** | journal fit zone 0.145 (designed 0.15, declared: bore, lead-in, tube bottom and shoulder up to r 28.4); T_stred elsewhere 1.40 (L_ucho at lift 20); T_dvere 1.505 (servo); speaker-ring screws 1.37 (pigtail, swept without lift as a hanging loop); **FAIL: PAN FFC lift loop `ffc_par` meets the front stack at pan −70…−88: DPS_led 0.001, T_drziak_repro 0.001, T_drziak_led 0.002, reproduktor 0.022, skrutka_led_1 0.45** | **FAIL (cross-module, blocking)** |
| O3c PAN_ENV2 formal | front stack is inside PAN_ENV2 (r 33.4 at every azimuth for z −40.9…−17): margins −3.8…−1.2 – the table ignores the front stack (information) | info |
| **O3d lowering of T_stred (T5)** | **FAIL at all 4 F1 bosses** (plan clearance 0.001–0.008): the boss footprints (x ±25.6…32.4, \|y\| ≥ 15.6) must pass straight down through RAM parts above them – boss (−29, −19): T_spodok stop-pin post-2 block (e.g. (−27.42, −15.99, −58.9), top −48.2); boss (+29, −19): T_paluba corner (31.6, −16.81, −46.2) + F3a_1 washer / screw (27.8, −15.8, −45.4); bosses (±29, +19): DPS_riadenie ends (28.23 / −27.0, y 16.5…18.1, z −57.5) + F7 screws, washers, inserts; everything else of T_stred / front stack ≥ 0.557 (speaker-ring screw vs STS3032) | **FAIL (cross-module, blocking)** |

## Blocking cross-module findings (OBAL cannot fix them inside its zone)
1. **FFC lift loop vs front stack (same finding as PAN's STATUS).** `ffc_par` (lift-loop leg at stage az ≈ 0, x 25.1…31.35, z −42…−24)
   swings to B az 255…285 at pan −70…−90 and meets the LED holder / LED PCB / speaker ring / speaker (their inner faces at r 29.6–31.6).
   OBAL cannot reach ≥ 1.0: the speaker back face (y −31.6) is fixed by speaker 5.0 + gasket 0.85 + wall 2.2 behind the approved grille;
   the LED box could move outward only by shortening the 5.6 mm light-mixing depth to ≈ 3. **Recommended: PAN option 1** (lift-loop U in
   the y–z plane, x 25.35…28.35 → ≥ 1.25 from the ring) or keep everything below z −28 at r ≤ 28.4 outside stage az 37…143; PAN_ENV2 must
   become azimuth dependent there.
2. **T_stred cannot be lowered over the tower (T5).** R2 limits the OBAL F1 zone to z −81…−75; rev. 1 had a vertical keep-out prism for
   all z (BOSS_KEEPOUT). RAM parts now stand above all four bosses (numbers per boss in `checks_obal.json["O3_zones"]["lowering"]`). Fix
   (RAM / integrator): keep x ±(25.1…32.9) × \|y\| ≥ 15.1 free for every z above −81 (trim the post-2 block, the deck corner and the
   F3a_1 washer position, the carrier ends + F7), or change the assembly order (carrier through the door after T5) **and** still trim the
   block / deck / F3a. OBAL cannot move the
   bosses without moving F1 (RAM pads).

## Notes for the integrator (also in the structured summary)
* Mirror `OBAL2_OVERRIDES` into `t4_common.OBAL` (TUBE_VENT Ø2.5 z 0.0; DOOR_HOOK deleted; SPK_RING closed, t 2.0, ro 16.5, steps;
  EXIT_SPK; door tongue / lip; KLB built; LED step).
* §17.9: F8 washer = ISO 7092 / DIN 433 M2 (2.2 × 4.5 × 0.3), counterbore Ø4.7; torques F8 0.015 + Loctite 222, F13 0.03, F1 0.045.
* X1: T_spodok column rib top (y 12.5…15, z −30) is **0.10** from the T_bok socket tube r 16 (static) – below print tolerance; RAM should
  drop the rib top to z −30.4 or chamfer it (T_bok is unchanged since rev. 1).
* T_klb neck face is 0.2 in front of the column boss face (m18) – measured 0.200.
* Speaker-ring screw head ↔ STS3032 case 0.557 static / 0.557 plan during lowering (tight; screw head modelled Ø3.8 × 2.0).
* The pan pinion and the F1 screws / washers are excluded from the lowering (installed after T5).

## NOT done / NOT verified
* No FE. S rows are hand calculations (stated Kt); S1c (topple) is an estimate with an assumed impact force.
* Bought-part numbers: ISO 7380 M2 head (dk 3.5, k 1.3) catalogue nominal – UNVERIFIED; ISO 7092 M2 washer OD 4.5 (4.2–4.5) from
  McMaster / Aspen / JC Fasteners listings (search snippets); thread-forming screw head modelled Ø3.8 × 2.0 (conservative); speaker gasket
  force (PORON 4701-40 class) UNVERIFIED; speaker solder-lug position (r < 13) to be checked on the purchased speaker.
* Cup finder is a 0.5 mm (0.25 for small parts) voxel model; no slicer / support generation was run.
* Cross-module numbers use the RAM / PAN STLs on disk at the time of the run (RAM 13:35, PAN 13:52).
* The two blocking findings above are not resolved; K7 for the door (straight in, no hooks) was not simulated beyond the static gaps.

## How to re-run
```
/opt/venv/cad/bin/python t4_obal.py                      # ≈ 45 s from the cache (--rebuild: rev. 2 steps, ≈ 9 min; --rebuild-v1: everything)
/opt/venv/bl/bin/python  obal2_work/mesh_checks2.py      # ≈ 30 s  -> obal2_work/mesh_checks2.json
/opt/venv/bl/bin/python  obal2_work/k8_obal.py -- --pitch 0.25    # ≈ 3 min -> obal2_work/k8_obal.json
/opt/venv/cad/bin/python checks_obal.py                  # ≈ 15 min -> checks_obal.json (merges the two above)
/opt/venv/bl/bin/python  obal2_work/prev2_obal.py -- --name iso --dir 0.55,-1,0.45   # previews
```
