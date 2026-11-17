# STATUS – CAD builder, module PAN (pan stage + neck lift), continuation run, 2026-11-17

Continuation of an interrupted run (it left `t4_pan.py`, 33 parts, no status, no checks, no previews). Nothing was restarted;
this run fixed the two flagged parts, wrote and ran the module checks, fixed what they found, rendered previews.

## Files (all under /tmp/claude-0/gapwf/fin/T4/)
* `t4_pan.py` – module: `build() -> dict[name] = part(shape, group, mat, printed, label_sk, ...)`; `python t4_pan.py` builds (printed
  parts cached by source hash in `cache/pan_*.brep`, full rebuild 3 s), prints validity / volume / bbox / build time, exports
  `stl/<name>.stl` with `t4_obal.export_abs` (absolute deflection 0.01) and `step/<name>.step`, writes `parts_pan.json`.
  Pose functions for the checks / integrator: `pose_parts(lift)`, `mk_kluka(theta)`, `fpc_lift(lift)`, `fpc_stage()`, `fpc_loop(pan)`.
* `parts_pan.json` – 33 parts (7 printed, 26 bought / fasteners / tapes / FPC), all_ok = True;
  per part: valid, bbox, mesh volume, mass, stl, step, source of the dimension, assembly step, fastener record; plus `deviations`
  (13), `intended_fits` (16), `assembly`, `firmware`, `additions`.
* `t4_pan_checks.py` -> `pan_checks.json`, log `pan_checks.log` – module checks A–H (sections can be run separately: `... t4_pan_checks.py E`).
* `t4_common.py` – ONLY the block "additions by pan" (dict `PAN`) was written (source `pan_work/additions_pan.txt`, applied with
  `pan_work/put_additions_pan.py`).
* Previews (600 px, 16 samples, script `pan_work/prev_pan.py`): `prev_pan_iso.png` (from the back), `_iso_pred`, `_bez_krku`, `_zozadu`,
  `_zdola`, `_rez_x` (section x = 0), `_rez_kluka` (section through the crank, rest), `_rez_kluka_10` (mid stroke), `_zdvih20`,
  `_v_trupe` (section x = 0 inside the OBAL + RAM parts), `_det_fpc_pozy` (pan loop at -85 / 0 / +85 over the deck). All were looked at.
* Pose STLs: `pan_work/poses/lift10/`, `lift20/` (all 33 parts, pan 0), `pan_work/poses/fpc/fpc_zdvih_{0,10,20}.stl`, `fpc_pan_{-85,0,85}.stl`.
* Backups of the state found on disk: `pan_work/bak/`.

## Parts
| part | grp | material | mass g | bbox x / y / z | STEP |
|---|---|---|---|---|---|
| P_sachta | P | resin_black | 16.45 | -28.07…28.07 / -28.07…28.07 / -42.20…-2.00 | yes |
| P_koleso | P | resin_black | 2.55 | -15.18…15.66 / -15.18…16.50 / -45.70…-42.20 | yes |
| P_drziak_serva | P | petg | 3.79 | -6.35…22.90 / 12.60…30.95 / -41.90…-12.30 | yes |
| P_kluka | P | resin_black | 0.25 | -17.00…-12.80 / 19.60…26.80 / -36.40…-20.60 | yes |
| L_pata | L | petg | 4.05 | -22.30…22.30 / -9.80…9.80 / -40.50…-36.50 | yes |
| L_jazyk | L | petg | 0.17 | 21.30…27.90 / -3.50…3.50 / -40.50…-35.50 | yes |
| L_ucho | L | pom | 0.47 | -19.90…-7.50 / 9.80…25.10 / -40.50…-31.90 | yes |
| servo_zdvih | P | bought | 13.4 | -15.50…16.00 / 17.10…29.30 / -41.10…-13.30 | yes |
| cap_kluky | P | steel | 0.13 | -19.90…-14.50 / 22.20…24.20 / -35.20…-33.20 | yes |
| fpc_pan | P | fpc | 0.08 | -4.58…28.20 / -5.20…23.50 / -51.00…-23.41 | yes |
| spoj_zdvih | P | bought | 0.25 | 16.60…22.00 / 12.72…18.30 / -41.00…-36.65 | yes |
| kabel_zdvih | P | bought | 0.4 | 15.70…20.18 / 18.00…24.10 / -38.75…-14.80 | yes |

Also: 8 PTFE strips + journal band, 2 gear dowels D2 x 4, stop pin D2 x 4.5, ear dowel D1.5 x 5, 2 x M2x4 + 2 M2 inserts (F10), M2x6 (F11),
M2.5x6 countersunk (crank), M2x8 (F12), M1.6x10 countersunk (tongue). Mass by group: P 39.5 g, L 5.3 g.
STEP: all 33 files exported, largest 2.08 MB (limit 12 MB) – no part of this module is loft-derived.

## What this run changed (and why)
* **L_jazyk** – STL was non-manifold: the 1.8 mm key was cut by the D1.8 screw hole into two halves touching in a line. Key = two prongs (y ±1.1…2.6, 1.4 high), slot in L_pata widened; skins around the slot 1.05 / 1.15.
* **P_koleso** – the part was fine; only its EXPECTED bbox was wrong (21-tooth sector, lip not all round). Lip shortened 145° → 140° (by calculation its end reached the pinion tip circle at the hard stop +90; now drum / lip ↔ pinion ≥ 0.91 measured).
* **L_ucho slot 2.2 × 12.2 → 2.2 × 12.7** (front end y 12.1 → 11.6): at mid stroke the pin was 0.10 from the slot end, less than the float of the neck in the well. The back end cannot move (sweep radius 32.03 vs 32.2) – firmware must keep the crank at 3…177° (stroke 19.97, pin 0.62 from the closed slot end).
* **Lower bracket pad / F10_1: z −30.0 → −31.7**, lug z −36.55…−29.7, tab at the upper screw up to z −12.3 only. Found by the door check H3 / H2: the frame magnet pad of T_stred at (25, −24) is tilted along the wall normal, its silhouette along Y reaches x 18, z −29.14 – the lug hit it on the way in and the D4.5 tool channel of F10_1 was blocked by 0.37. The micro junction moved down 0.35 for the lug.
* **Bracket slivers removed**: pad pockets open cleanly at the lug / tab top (were 0.12 mm walls); tab post pilot is a through hole (was a 0.5 floor).
* **F10 = 2 × M2×4** (spec M2×6) in inserts with a 3.2 deep hole: 1.2 floor to the well inner face (was 0.9).
* **Glue groove** of the collar-disc seat interrupted at the D4.8 tool hole (0.9 rim).
* **Export** through `t4_obal.export_abs`; no STEP above 12 MB.

## Checks actually run on the final geometry (`pan_checks.json`)
| check | result | status |
|---|---|---|
| A solids / STL | 33 parts: valid single solids, bbox as designed, STL re-read watertight (0 open / non-manifold / flipped edges); not ok: [] | PASS |
| B interference among PAN parts (+ finished neck halves, collar disc) | OCC common volume at lift 0 / 10 / 20: 11 overlapping pairs, all declared press / thread / bonded fits (largest 4.71 mm³); exact mesh distances at lift 0…20: 30 pairs below 1.0, all declared; undeclared: [] | PASS |
| C crank kinematics | stroke 20.000 (r 10.0), d lift / d θ = 0 at θ 0 / 180° (pin at y 23.2, z −34.2 / −14.2), pin ↔ slot flanks 0.1…0.101 over 13 angles, slot end gaps 0.6 (front, mid stroke) / 0.1 (back, dead centres); peak torque 0.0167 N·m for 0.17 kg (MG90S 0.18: ×10.8); pan stop ±90, teeth margin 15° | PASS |
| D swept envelope vs PAN_ENV and the analytic shell (inset 2.2) | every P / L part, lift 0…20, pan −85…85: PAN_ENV violations [] (declared: gear lip r 16.5 = spec 7.2 vs band r 15.9; stop pin in the deck groove); smallest margins: lift servo 0.116, ear 0.168; shell clearance min **1.511** (servo corner, pan 30), ear 1.764; low-zone rule hits 0 | PASS |
| E real meshes of OBAL + RAM (58 static parts incl. golier_prstenec), pan −85…85 × lift 0…20 | smallest undeclared clearances: P_sachta ↔ pastorok_pan 1.0; P_sachta ↔ skr_pastorok_pan 1.0; P_sachta ↔ T_paluba 1.0; P_drziak_serva ↔ T_paluba 1.0; servo_zdvih ↔ T_ram 1.025; fpc_stage ↔ T_paluba 1.08; servo_zdvih ↔ T_stred 1.217; fpc_lift ↔ T_paluba 1.237; L_ucho ↔ T_stred 1.4. Declared running fits: journal ↔ bore 0.14 (tape) / 0.27, collar seam 0.25, pivot 0.025, gear on washer, stop pin in groove 0.2, FPC on its anchors. Gear ↔ ROTATING pinion: flank gap 0.0353…0.0384 at 93 poses; drum / lip ↔ pinion ≥ 0.91 (at the hard stop). Hard stops ±90: P_sachta ↔ pastorok_pan 0.4 | PASS |
| F seats / fits | 30 measurements on the solids and on the OBAL / RAM / B meshes, not ok: [] (bore r 28.342 → journal 0.142 with tape; MG90S: 3 seat faces, wedge 0.20, post 0.30, slots ±1.0) | PASS |
| G walls (ray scan, opposing faces) | P_sachta min 0.7 (median 1.599); P_koleso min 0.4 (median 3.5); P_drziak_serva min 0.8 (median 4.1); P_kluka min 1.178 (median 2.5); L_pata min 0.817 (median 4.0); L_jazyk min 1.1 (median 1.84); L_ucho min 0.775 (median 2.5); undeclared thin zones: [] – every reading below the material limit is a declared local feature (list below) | PASS |
| H assembly (module level) | H1 stage straight −Z through the bore (raised 0…52): only the intended guides / seats below 0.6 (PASS); H2 D4.5 tool channels, clearance to the tool: F10_1 +1.10; F10_2 +0.50; F12 +1.25; skr_jazyka +6.75; skr_fpc (RAM) +0.15 (PASS); H3 lift module −Y through the door (pulled back 0…30): pairs below 0.8 other than its seats: P_drziak_serva ↔ T_stred 0.55 (PASS) | PASS |

Overall: ALL PASS.
Method of every distance: surface samples (all mesh vertices + 0.3 mm grid) of the moving part against the triangles of the other
part (exact point–triangle distance, STL deflection 0.01); penetration would show as a distance → 0. Not a swept-volume boolean.

## Declared thin / close features inside the module
* P_sachta (resin_black, limit 1.2): back-sector floor 0.9 (spec 7.1, z -41.9..-41.0); 0.7 in the 0.2 FPC groove – measured min 0.7
* P_sachta (resin_black, limit 1.2): guide lands 0.7 high on the 1.6 wall (ray from a land flank) – measured min 1.033
* P_sachta (resin_black, limit 1.2): glue groove 0.3 deep in the 1.5 top plate; rim 1.1 x 0.3 outside the groove – measured min 1.098
* P_koleso (resin_black, limit 1.2): floor 0.5 under the two blind dowel holes D2 (dowels D2 x 4: 2.85 in the gear, 1.15 in the hub disc) – measured min 0.5
* P_koleso (resin_black, limit 1.2): retaining lip 0.4 x 0.8 (spec 7.2) – measured min 0.4
* P_drziak_serva (petg, limit 1.6): lands 0.85 / 1.05 above the two F10 slots (lug must pass under the frame magnet pad, tab under the door edge) – measured min 0.85
* P_drziak_serva (petg, limit 1.6): web 1.25 between the +X end of the lower slot and the lug end (x 22.9) – measured min 1.252
* P_drziak_serva (petg, limit 1.6): web 1.3 under the F11 pilot hole (post bottom 0.3 above the servo end) – measured min 1.3
* P_drziak_serva (petg, limit 1.6): ledge 0.8 under the servo end (spec 7.3, z -41.9..-41.1) – measured min 0.8
* P_kluka (resin_black, limit 1.2): hub wall 1.2 around the serration – measured min 1.178
* L_pata (petg, limit 1.6): skins 1.05 / 1.15 above and below the tongue key slot, 0.85 around the D1.3 pilot – measured min 0.85
* L_pata (petg, limit 1.6): webs 0.81 under the ear dowel hole D1.48, 1.15 at the ear pilot D1.7, countersinks of the optional screws – measured min 0.817
* L_jazyk (petg, limit 1.6): key prongs 1.5, recess floor 2.2, countersink rim – measured min 1.1
* L_ucho (pom, limit 1.2): webs 0.78 above / below the D1.5 locating dowel hole (flange only 3.1 high under the crank sweep) – measured min 0.775
* L_ucho (pom, limit 1.2): slot closing web 0.8 at the far end (sweep limit r 32.03) – measured min 0.8
* L_ucho (pom, limit 1.2): webs 0.85 above / below the M2 clearance hole in the 4.0 flange; front web 1.4 – measured min 0.85
* Running gaps below 1.0 by design: crank pin in the slot 0.10 per side; crank arm ↔ ear 0.40; foot 0.5 above the hub disc and tongue / ear 0.5
  above the floor at rest; tongue block 0.5 under the window top at lift 20; neck on the lands 0.30 bare / 0.17 with tape.
* Lift servo ↔ T_ram columns 1.02 and ↔ frame magnet pad of T_stred 1.22: above the 1.0 rule, but with little margin for print tolerance.

## Foot ↔ finished neck
* epoxy on the bottom face z -36.5 of the FRONT neck half only (the halves must still separate).
* Optional: 2 x M2x8 countersunk, from below, heads flush at z -40.5 at (x, y) [[-10.0, -5.0], [7.5, -5.0]] into krk_predna_polovica, D1.6 pilots 4 mm deep to be drilled through the foot holes (change of a finished part, spec open point 4). Checked: B mesh sections z -36.3 .. -34: solid material at both positions; the neck's cross screws sit at x -15 and x +5, z -31 (hole z -32 .. -30): the foot screws end at z -32.5 and are 0.7 / 3.2 mm beside them in plan.
* Wires: neck wire channels at x 11.75 .. 14.5, y -6.5 .. -3.5 and y -2 .. +2 (B mesh) inside the foot slot x 11.6 .. 15.0, y -7.2 .. 2.6; FPC paddle 3.4 × 10.4 in a 1.0 deep pocket under the foot (solder side down), tail in a 0.3 channel to the tongue.

## Deviations from T4_spec.md (details in parts_pan.json["deviations"])
* **P1 L_jazyk (new part)** – spec: 7.3: tab x 22.3..27.0 as part of L_pata; built: separate tongue, keyed (2 prongs) + 1 x M1.6x10 countersunk along -X, mounted after the neck is in the well. Reason: a tab that is part of the foot cannot be lowered through the well (inner half length 23.5, end window only below z -15).
* **P2 guide lands in the well** – spec: 7.1: 4 PTFE strips on flat long faces, neck gap 0.87; built: 8 lands 0.70 high (2 front, 1 back + 1 short above the ear window, 4 on the end walls) as strip seats; neck gap 0.30 bare / 0.17 with 0.13 tape. Reason: the neck must be guided: 0.87 per side would let the head rock by 2.8 deg; lands keep the tape off the window edges.
* **P3 ear slot** – spec: 7.3 / EAR: slot 2.2 x 12.2, y 12.1..24.3; built: 2.2 x 12.7, y 11.6..24.3 (front end +0.5). Reason: at mid stroke the pin was 0.10 from the slot end, less than the 0.17..0.30 float of the neck in the well -> binding. Back end unchanged (sweep limit r 32.03): firmware keeps theta 3..177 deg.
* **P4 ear dowel** – spec: dowel D2 at x -15.5, zrel -4.3; built: D1.5 x 5 at zrel -4.75. Reason: the flange is only 3.1 high under the crank sweep (notch); D2 would leave 0.55 webs, D1.5 centred leaves 0.78.
* **P5 ear flange y** – spec: flange y 10.2..12.4; built: 9.8..12.4. Reason: the foot back face is at y 9.8 (foot 19.6 deep); 10.2 would leave a 0.4 gap under the screw.
* **P6 bracket pads / F10** – spec: BRACKET_PADS (19.5, -30.0), (8.0, -14.5), face y 15.6, F10 = M2x6; built: lower pad z -31.7, pad face y 15.4, insert hole 3.2 deep, F10 = 2 x M2x4 ISO 4762 (2.3 mm in the insert). Reason: the lug of the bracket and the F10_1 tool channel must pass under the frame magnet pad of T_stred at (25, -24) (the tilted pad and its riser reach x 18, z -29.14 seen along Y); 1.7 of PETG under the screw heads; 1.2 floor behind the insert hole.
* **P7 bracket outline** – spec: BRACKET x -5.3..17.6, z -41.9..-13.0; ledge y 17.1..26.2; built: lug to x 22.9 (z -36.55..-29.7) around the lower pad, tab to z -12.3 around the upper screw, wedge lip y 29.45..30.95 behind the servo end, rest block y 12.6..13.0. Reason: pad r 3.0 + slot +-1.0 needs the lug; the lip holds the far end of the servo (one tab only). All inside PAN_ENV (margin 1.48).
* **P8 pan gear sectors** – spec: 7.2: teeth 154.3..354.3 (200 deg), lip r 16.5; built: 21 teeth centred 154.3..354.3 (root sector 149.3..359.3), drum r 15.7 over 4..145, lip over 22..140. Reason: whole teeth; at the hard stops +-90 the drum / lip stay 1.0 / 5.5 deg outside the pinion zone. The lip r 16.5 (spec 7.2) is outside the r 15.9 band of PAN_ENV (spec table) - back sector only, 2.3 from the FPC clamp.
* **P9 rotating FPC anchor** – spec: 7.2 / 9: anchor on the drum at gear azimuth 30; built: the FPC comes down onto the drum at gear azimuth 14 (riser), free inner run from 23.4. Reason: shortest run from the lift loop at the +X end wall. U-turn at 92 + 0.402 x pan (57.8..126.2), inside the 56..128 of RAM; free length 47.3 (RAM 45.6).
* **P10 FPC lift loop** – spec: 9 / FPC_LIFT: legs y +-3.5, R 3.5, x 25.3..28.4, z -40.5..-15.5; built: moving leg y -3.5 on the tongue, fixed leg y +4.5 on a fin of the well, R 4.0, envelope x 25.2..28.2, y -3.62..4.56, z -41.9..-13.4 (PAN['LIFT_LOOP_ENV']). Reason: fixed leg needs a backing (fin) and a path under the floor (apron, groove 0.2); U top at lift 20 = z -13.4, r max 28.57 <= 28.7.
* **P11 tool hole in the stage top** – spec: -; built: D4.8 through the top plate at stage (0, 21.1). Reason: driver access to the clamp screw of T_prichytka_fpc (RAM, B frame (18.0, 11.0), axis Z) at pan -58.5 before the lift module / collar disc are mounted.
* **P12 micro junction** – spec: 9: 2 x 3 pins on the bracket; built: 1 x 3 pin header 1.27 on an FR4 stiffener bonded to the FPC branch on the well back wall (x 16.6..22, z -41..-36.65), socket on the shortened servo lead. Reason: the branch is part of the FPC outline; the bracket stays removable without unsoldering.
* **P13 STL export** – spec: t4_common.export_part; built: t4_obal.export_abs (absolute deflection 0.01). Reason: instruction of the lead / OBAL finding.

## NOT done / NOT verified (do not treat as passed)
* K1–K11 (global) were not run by me. E / H are module pre-checks on the STL files of OBAL (16:5x) and RAM (16:07) found on disk; if either module is re-exported, re-run `t4_pan_checks.py E H`.
* K9 (real head vs torso top) is not part of this module. The neck halves above z 4 and the head were not checked against anything here.
* K7 for the whole torso: only the three module steps above were simulated (straight translations, sampled every 1…4 mm). Dropping the neck with the bonded foot into the well, hooking the ear onto the pin and mounting the tongue were NOT simulated – they rest on the static gaps (foot 0.37 to the tapes, ear ±1.0 in its window, tongue ±1.0).
* The FPC is modelled as an ideal strip (constant radii, creased folds); its real shape between the anchors, fatigue life (R 4.0 lift loop = 33 t, R 3.84 pan U-turn = 32 t) and the developed outline for ordering are not verified. The outline has 3 folds and 2 T-branches – it needs a drawing of its own.
* Soldering 7 neck wires to the FPC paddle under the foot is described, not modelled wire by wire.
* MG90S dimensions are the E2 model (user drawing); the spline is modelled as a D4.8 cylinder, the crank serration (21T, 4.44 / 4.84) must be test-printed. Servo torque margin uses an assumed 0.17 kg for head + neck + foot.
* K10 printability: no slicer run. P_sachta (tough resin) has the 0.9 back floor of the spec (0.7 in the FPC groove) and a 14 × 30 window in the back wall; orientation top-down is assumed. P_drziak_serva (PETG) has a 0.8 ledge (spec) and 0.85 / 1.05 lands above the F10 slots.
* K11: masses are in parts_pan.json; the centre of gravity of the module was not combined.
* Bought-part sizes (MG90S, dowels, screws, junction header / socket) are datasheet / standard values, not measured parts.
* The design choices inherited from the first run (fin + apron, FPC routing under the floor, junction on the back wall, tongue) were not re-derived; they were only tested by the checks above and looked at in the previews.
* Service access to the FPC clamp screw of RAM (axis Z) AFTER the collar disc is glued on: the D4.8 tool hole is then covered. It is reachable only with the lift module removed and an L-key through the door – not simulated.

## How to re-run
```
/opt/venv/cad/bin/python t4_pan.py                     # 7 s from the cache (--rebuild: 10 s)
/opt/venv/cad/bin/python t4_pan_checks.py E            # 3 min  real meshes (needs stl/ of OBAL + RAM)
/opt/venv/cad/bin/python t4_pan_checks.py A B C D F G H  # about 15 min
/opt/venv/cad/bin/python pan_work/export_poses.py && /opt/venv/bl/bin/python pan_work/prev_pan.py iso rez_x v_trupe
```
