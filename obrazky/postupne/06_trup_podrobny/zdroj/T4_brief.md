# T4 – NOVA mini: TORSO, detailed printable CAD (phase 2, torso only)

The user approved the LOOK of the torso (visual model T3) and asked for the detailed, buildable torso. Arms and base come
later (separate rounds) – here only their INTERFACES are defined. Head + neck (variant B rev. E2) are finished and must not
change. User language: Slovak (all user-facing texts and image labels in Slovak with diacritics).

## 1. Inputs (read them)
* Approved exterior: `/tmp/claude-0/gapwf/fin/T3/shape.py` (profile table CP = drop below the top / half-width a / half-depth
  b / superellipse exponent n; `section(s, inset)`, `stations()`, seam planes XS = ±33.3) and `T3/build_scene.py` (the visual
  model: 3 panels – centre band front-top-back + two side caps, black bottom cap, light bar BAR 31 × 4.2 at drop 36.5, grille
  slot SLOT 21 × 3.2 at drop 52, back door DOOR 56 × 60 r10 at drop 46, shoulder joints: axis X at drop 21, y +3, black stepped
  cylinder Ø27 flange / Ø22 step protruding 12 mm). Renders: `/home/user/Robot/obrazky/postupne/05_trup_podla_R05/*.png`.
* Internal packaging (the agreed mechanism): `/tmp/claude-0/gapwf/fin/T1/pack/pack.md` (read ALL of it), `layout.json`,
  `envelope.json`, previews `prev_*.png`. Pack frame: world z from the floor, collar top Z_TT = 133 → **z_B = z_world − 129**.
* Finished neck/head: STL `/tmp/claude-0/gapwf/fin/B/stl/*.stl` (rest pose, B frame), builder `B/build.py` (interface block at
  lines ~75–130 and 760–800: TOP 4, COLLAR (26.5, 26.75, 28.25, 28.35), neck blade 45 × 20 in a well 47 × 22 R1.5, lift 20,
  neck bottom z −36.5 at rest, wires leave the neck bottom at x ≈ 13.2…14.6: 4 head wires y 0…2.4 + 3 tilt-servo wires
  y −6.7…−3.7), `B/montaz.txt` (assembly + the tilt-vs-lift table), `B_mechanism_review.md` §5a (lift crank).
* Modelling rules: CLAUDE.md (build123d recipes; fillet before booleans; check volumes; ≤ 144 points per lofted section,
  never booleans against faces coincident with a B-spline loft face – keep internal features 0.3–0.4 mm inside).
* Tools: build123d 0.13 `/opt/venv/cad/bin/python`; Blender 5.2 `/opt/venv/bl/bin/python` (Cycles CPU). 4 CPU cores shared.

## 2. Frame
B frame: mm, Z up, x = robot left(+)/right(−), FRONT = −Y, torso axis (J1 and PAN) = Z axis, **torso top = collar top z = 4**.
White shell: z 4 … −81; black bottom cap to z −84.5. Everything in the STL/STEP exports is in this frame, rest pose
(neck retracted, pan 0, J1 0), so the torso parts drop into place next to the existing head/neck STLs.

## 3. Fixed by the user's approval (do not redesign)
* Outer surface = T3 shape (105 wide × 80 deep × 85 high + 3.5 black cap; top section hugs the collar ring).
  Local deviations ≤ 1.5 mm are allowed ONLY where the mechanism forces them (list each one); everything visible stays smooth.
* Visible seams: exactly two seams x = ±33.3 over front, top and back (0.5 ± 0.1 wide), the white/black seam at the bottom,
  the back-door seam, the shoulder joints, light bar + grille slot on the front. No other visible seams, no visible screws on
  the top, front, sides or back (underside is free).
* Collar: finished parts `golier_kotuc` (turns with pan) + `golier_prstenec` (glued in the torso recess r 28.35, z −2…4).
  Give the white top a printable rim: ≥ 1.2 mm of white around the ring (top section r ≥ 29.6 instead of 28.4 is fine).

## 4. Design decisions already taken (lead designer) – refine, don't overturn without a hard reason
* **Structure.** An internal chassis carries everything; the white shells only cover it:
  - `T_spodok` black bottom cap = structural base plate (J1 foot ring with the 6805 seat, STS3215 cradle, columns);
  - `T_ram_*` chassis (deck, columns, top journal ring for the pan stage, electronics mounts) – PETG FDM or resin;
  - `T_stred` centre band (front + top + back in ONE arch part, with the collar recess, light-bar and grille openings and the
    back-door opening) – lowered over the chassis from above, fixed by screws from below (through the bottom cap rim);
  - `T_dvere` back door (magnets + locating lip) = service access to the lift servo, controller, FPC;
  - `T_bok_L`, `T_bok_P` side caps – pushed on from ±X, each fixed through its shoulder socket (screw / magnets hidden under
    the black shoulder joint) + locating lips on the seam;
  - `T_klb_L/P` black shoulder joints (static, part of the torso): hold the arm interface defined in pack.md (static spline
    socket for the arm servo, friction collar ≈ 0.25 N·m, pull-off magnets, 3-wire cable spiral). The ARM itself is later.
  - light guide + LED strip, grille insert, speaker Ø28 behind the grille.
* **Mechanism** = pack.md: J1 STS3215 18 mm off-axis (shaft down) + brass m1 18T/18T + slip clutch + 6805-2RS in a rotating
  foot ring under the bottom cap; PAN STS3032 at the front, m0.8 18T → 36T sector gear, Ø6 pin + PTFE washer at the bottom and
  the Ø56.4 journal at the top, ±90° stop; LIFT MG90S + crank r 10 + POM neck foot with ear (dead centres at 0 and 20 mm);
  pan/lift FPC (3.0 × 0.12 on edge) with lift loop and pan rolling loop; controller ESP32-S3-Zero, 5 V buck D36V28F5, MAX98357A,
  470 µF, torso LED bar. Keep pack's z stack unless the new shell forces a change (z_B = z_world − 129).
* **Base interface (base is designed later).** Everything below the bottom cap (foot ring, bearing seat, pinion zone, J1 FPC
  entry, dark plinth skirt) is part of the torso and must be fully defined; model the static hub + sun gear + bearing inner seat
  as a DUMMY `Z_naboj_test` (a printable test stand) so the torso can be assembled and tested on the bench.
* **Materials / printing.** White shells + black parts: resin MSLA (walls 2.2 nominal, ≥ 2.0; local ≥ 1.2), build volume
  218 × 123 × 220. Chassis: PETG FDM (walls ≥ 1.6, no supports where possible) or resin. M2 / M2.5 screws into brass inserts
  (glued in resin, heat-set in PETG). Seams 0.5. Bought parts modelled at real size with tolerance-aware seats.

## 5. Known conflicts to solve first (found by the lead)
1. **Depth in the back.** Pack's pan-stage sweep reaches r 35.9 (lift servo + crank behind the well) at world z ≈ 95–115
   (z_B −34…−14). New shell half-depth there: b = 37.1 (drop 22) … 38.7 (drop 32) → inner ≈ 34.9–36.5: about 1–2 mm short for
   |pan| ≈ 15–35°. Solve by tightening the lift module (crank/servo corner radius), a local inner relief, and/or ≤ 1.5 mm
   more depth there – and prove it with the sweep check.
2. **Narrow top.** The shell is a bell: b = 30.0 at drop 1, 31.9 at drop 4.4, 33.0 at 7, 34.2 at 10.5, 35.5 at 15. The journal
   ring (pan journal Ø56.4 at world z 118.5–124.5 = drop 8.5–14.5) and its seat must fit inside the white wall there.
3. **Shoulder shelf vs head.** Pack required the torso top beyond r 30 to stay ≥ 1 mm below the collar plateau in every
   direction; the approved shape does that in ±Y but in ±X the shelf is higher (drop 0.85 at x 32, 1.9 at x 35, 4.4 at x 39.4).
   The look stays; verify the REAL head (STL, Blender BVH) against the new torso top over pan −85…85 × lift 0/7.5/12.5/20 ×
   tilt per the B table and, where it collides or gets < 0.5 mm, add a pan-dependent tilt limit table (firmware) – do not
   reshape the shoulders unless a pose inside the B tilt table at pan 0 collides.
4. **Wider body.** The shell is now 105 wide (pack placeholder 89): the side columns / shoulder sockets sit further out
   (shoulder axis: drop 21, y +3; side surface x ≈ 46.8 there). Use the extra width for electronics, not for looseness.
5. **Top rim / collar seat**: seat ring for `golier_prstenec` and the knife-edge of white around it (see §3).

## 6. Deliverables (all under `/tmp/claude-0/gapwf/fin/T4/`)
* `t4_common.py` – constants (every interface number), exterior solids (outer / inner, cached to BREP), helpers, part registry.
* `t4_obal.py`, `t4_ram.py`, `t4_pan.py` – modules; each `build() -> dict[name] = dict(shape, group ('T' static torso, 'P' pan
  stage, 'L' lift, 'Z' base dummy), mat, printed: bool, label_sk)`; `build_all.py` exports `stl/<name>.stl`, `step/<name>.step`,
  `parts.json`. Part names Slovak without diacritics (as in the head/neck set).
* `checks.py` → `checks.json`, all PASS: K1 valid closed solids / watertight STL; K2 no interference at rest (intended fits
  listed); K3 moving clearances ≥ 1.0 over pan −85…85 (5° steps) × lift 0…20 (pan stage, lift servo, crank, foot, FPC loops) and
  J1 −155…155 vs the dummy hub; K4 wall thickness (shells ≥ 2.0, local ≥ 1.2, chassis ≥ 1.6); K5 bought-part seats with
  tolerance ranges (STS3215, STS3032, MG90S ±0.3, 6805, gears: centre distances C 18.0 / 21.6); K6 crank kinematics (stroke
  20.0, dead centres) and pan stop ±90; K7 assembly: every part reaches its place along a stated direction in the stated order
  without collision, every screw has a tool path (Ø4.5 cylinder), inserts accessible; K8 exterior fidelity (outer surface vs T3
  shape ≤ 0.05 mm outside declared zones, seam widths, no see-through holes from 26 viewpoints); K9 real head/neck vs torso
  (Blender BVH) incl. the pan-dependent tilt table of §5.3; K10 printability (size, min feature 0.6, drain holes for resin
  shells, FDM overhangs ≤ 50° or declared supports); K11 mass + CoG of the torso.
* `montaz_trup.txt` (Slovak: buy list, print list with material/colour/orientation, step-by-step assembly, wiring, service) and
  `NAVRH_trup.md` (Slovak: what is what and why, deviations from the approved shape, open questions ≤ 5).
* Images (Slovak labels, helpers `nova.render.sheet` font(), INK, MUTED, ACCENT; label-anchor technique in
  `/tmp/claude-0/-home-user-Robot/e2af8646-c6f1-5ece-963d-7005cfdf5589/scratchpad/detail_E2.py` + `sheet_E2.py`):
  hero with the real head (same camera as `T3/build_scene.py` hero_r01, torso + head + neck only), exploded view with labels,
  labelled sections (front section y = 0 and side section x = 0), back door open, underside. GLB + .blend of the torso with head.
