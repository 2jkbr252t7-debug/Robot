# STATUS – CAD builder, module RAM (chassis + J1 + electronics + dummy hub), 2026-11-16

Continuation of an interrupted run. The earlier work was kept (no restart); this run finished the checks, fixed what
the checks and a review against T4_spec.md found, and re-exported everything.

## Files (all under /tmp/claude-0/gapwf/fin/T4/)
* `t4_ram.py` – module: `build() -> dict[name] = part(shape, group, mat, printed, label_sk, ...)`, `python t4_ram.py`
  builds (printed parts cached by source hash in `cache/ram_*.brep`), prints validity / volume / bbox / build time, exports
  `stl/<name>.stl`, `step/<name>.step` (only below 12 MB), writes `parts_ram.json`.
* `parts_ram.json` – 65 parts (5 printed, 17 bought, 43 screws / inserts), per part: valid, bbox, mesh volume, mass,
  `stl`, `step` (null for T_spodok), dimension `source`, `assembly_step` / `assembly_dir`, `fastener` record; plus
  `deviations` (13 items) and the `additions` block.
* `t4_ram_checks.py` → `ram_checks.json`, log `ram_checks.log` – module checks A–G.
* `ram_work/cross_obal.py` → `ram_work/cross_obal.json` / `.log` – advisory mesh check against the OBAL STLs.
* `t4_common.py` – ONLY the block "additions by ram" (dict `RAM`) was written (source: `ram_work/additions_ram.txt`,
  applied with `ram_work/put_additions.py`).
* Previews: `prev_ram_iso.png`, `_iso_zad`, `_zdola`, `_zhora`, `_rez_x`, `_rez_y`, `_det_J1`, `_det_J1_zdola`, `_det_pan`,
  `_det_fpc`, `_det_paluba` (script `ram_work/prev_ram.py`, 600 px / 16 samples). All were looked at.
* Backups of the state found on disk: `ram_work/*_v1.*`.

## What was changed in this run (and why)
1. **menic ↔ skr_F14_1/2 (3.7 mm³ each)** – a model artefact: the component envelope of the D36V28F5 covered the two
   mounting-hole corners. The corners are now free (r 2.4 around each hole). No design change.
2. **Pinion passage** (`RAM["J1_PASS"]`): the pinion screw F6 lies at r 18.0 from the torso axis = under the 6805 outer
   ring (r 16.3…18.5) and the seat wall – it cannot be reached from below once the bearing is in, and the pinion (da 20)
   did not pass the boss slot Ø14.4, so the J1 servo could not be removed either. Now a slot r 10.8 (±0.3 in x) goes
   through plinth, skirt and floor: the pinion is screwed on the servo on the bench, servo + pinion go in / come out from
   above as one unit. The skirt disc is C-shaped (ends in radial faces at azimuth 152° / 208°).
3. **J1 FPC slot** y 21.2…22.5 (spec 21.6…23.0): the plinth skin outside the slot was 0.76…1.0, now 1.26…1.5.
4. **F5 set screw**: insert now heat-set from outside through a Ø4.6 tool hole in the right column web (before: from
   inside the cradle, blocked by the bumper, and a 0.05 mm membrane between two holes).
5. **F4 pan-servo screws**: M2×6 thread-forming in Ø1.7 pilots instead of M2 inserts (an insert left a 0.6 wall on the
   servo-case side; the pilot leaves 1.2 / 1.4). `vl_F4_1/2` removed.
6. **Static pan-FPC anchor** redesigned: arc slot through the deck tangent to the wall inner face (azimuth 40…52°) +
   clamp inside the channel (azimuth 23.5…39.5°, gap 0.10 to the wall). The earlier clamp sat outside the wall with no
   path to the deck slot. It is on the **+X side**: with the rotating anchor at gear azimuth 30° (spec 7.2) a rolling
   loop with 0.40 × pan U-turn travel has NO solution for a static anchor at 150° (numeric scan, see below); the mirrored
   provisions (slot + pilot hole) are in the deck as a spare.
7. **Dummy hub stub** r 9.0 → 7.0: the orbiting pinion tips (r ≥ 8.0, same z −90.0) ran on its top face with 0 clearance.
8. **STEP policy**: `T_spodok.step` (40.7 MB, loft-derived) is not exported, `step: null`; every other RAM STEP is
   ≤ 1.3 MB. Stale exports of removed parts are deleted by the module.

## Checks actually run on the final geometry (ram_checks.json, all PASS)
| check | result |
|---|---|
| A valid / single solid / watertight STL | 65/65 |
| B interference among RAM parts (OCC common volume, 130 bbox pairs) | 0 unexpected; 29 declared press / thread fits |
| C1 inside the shell (inset 2.2, above z −78) | min 0.80 (stop ring; architect 0.80) |
| C2 lowering of T_stred (lip outline − 0.5, relief |x| ≤ 16.75) | min 0.51 (pan-servo tab corner), T_ram 0.95; pinion mounted later |
| C3 inside the cap tub | min 0.28 |
| C4 T_stred boss prisms free | no hits |
| C5 static parts vs PAN_ENV | no violation; **columns 0.40 to PAN_ENV (declared: architect's X_COL_IN 34.4)** |
| C6 bought parts vs envelopes | 6 declared exceedances (spline, shafts, standoffs +0.8, hub) |
| D seats (57 measurements on the solids) | 57/57 |
| E designed walls (38) | 38/38; ray scan lists the declared thin features |
| F tool channels Ø4.5 (26 screws) | 26/26 (F6 = bench assembly) |
| G J1 sweep vs the dummy, (r, z) profiles | min 1.00 pinion ↔ post, 0.30 foot ring ↔ stop block (spec), stop at ±154.7° |

Advisory, on the exported meshes (`ram_work/cross_obal.log`, OBAL STLs of 16:06): no penetration between any RAM and
OBAL part; contacts only at the intended faces (pads z −81, stop ring ±39.1, boss face ±38.4); spigot ↔ side caps
0.21; speaker screw ↔ pan servo 0.96. Straight-line sweeps: T_stred with the complete front stack lowered −Z over the
tower of step 9, and both side caps along ∓X: **0 colliding points**; lateral clearance below 0.5 only at the
pan-servo tab corner / +X post leg in the lip relief (= 0.50) and at the spigot (fit).
(Method: rays from tower surface samples of about 1 mm spacing against the shell meshes – features thinner than that can be missed.)
Rolling-loop scan: spec pair (rotating 30°, static 150°) → no U-turn position; RAM layout (free run starts at 52°) →
U-turn 90.5…100° at pan 0 (chosen 92°, travel 56…128°, free FPC length 45.6 mm).

## NOT done / NOT verified (do not treat as passed)
* K1–K11 (global) were not run by me; the cross-module results above are an advisory pre-check on STL, against the OBAL
  state of 16:06 and WITHOUT the PAN module (t4_pan.py did not exist yet).
* K3 for the pan stage against the real RAM solids (columns 1.02 to the lift-servo sweep, FPC wall top 1.0 below the
  stage floor) – needs the PAN parts.
* K10 printability was not evaluated beyond the wall measurements (no overhang analysis; T_ram shoulder bosses and the
  deck-boss corbels need a slicer look).
* K11: masses are in parts_ram.json (T 189.8 g, dummy 93.3 g), CoG not computed.
* Thin features left as designed / declared: 0.6 deck under the stop groove (spec), 1.0 skirt disc (spec), blind-hole
  floors 0.4…0.5 in T_ram (controller / board pilots, caps over the F2 inserts), 1.13 beside the FPC clamp screw.
* STS3215 spline length is an ASSUMPTION (2.2 usable, = what a flush M3 countersunk head leaves in the 4.1 mm pinion).
  If the real spline is longer the pinion needs a through bore and an ultra-low-head screw (0.2 to the 6805 outer ring)
  or the bearing plane has to drop. STS3032 tab height / hole pattern are listing values.
* No POM collet on the dummy hub: PETG post Ø24.96, M8×20 bolt as steel core / clutch shaft, 2 disc springs, sun gear
  tapped M8; the torso sits on it by gravity (spec 5.5). Slip torque of the clutch is not calculated.
* No dedicated cable clips are modelled (bundles: Ø5 holes in the column webs, corner behind the cradle); connector
  blocks on the controller are indicative.
