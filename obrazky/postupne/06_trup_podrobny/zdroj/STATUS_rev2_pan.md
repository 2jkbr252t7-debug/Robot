# STATUS rev. 2 – CAD builder, module PAN (slim pan stage + neck lift), 2026-11-17

Role: PAN builder, rev. 2 (resin-only Elegoo Tough on the Saturn 4 Ultra 16K, allowables 8.5 / 4.3 / 12.9 MPa). Inputs read: T4_rev2_plan.md,
T4_zivica.md, T4_spec.md §17, t4_common.py block "rev2 (architect)", rev2_arch/ULOHA_pan.md, STATUS_pan.md, overenie_pevnost.md (rows).
Backups (identical to rev. 1): rev2_backup/t4_pan.py.pan.bak, rev2_backup/t4_pan_checks.py.pan.bak.
**t4_common.py was NOT edited** (two builders work in parallel). The block that the integrator may paste is
`pan2_work/additions_pan_rev2.txt`; the module constants are `t4_pan.PAN2` (+ `parts_pan.json["pan2"]`).

## Files (all under /tmp/claude-0/gapwf/fin/T4/)
* `t4_pan.py` – rev. 2 module. `build()` -> registry (38 parts, rest pose, pan 0); `python t4_pan.py` builds (printed + metal parts cached
  as `cache/pan2_*.brep`, about 10 s), prints validity / volume / bbox, exports `stl/` (t4_obal.export_abs, deflection 0.01) + `step/`
  (all 38 STEP < 12 MB), writes `parts_pan.json` (with `deviations` PD1–PD17, `intended_fits`, `ffc_lengths`, `ear_flat_pattern`, `pan2`)
  and the ear flat pattern `stl/L_ucho_rozvin.dxf` (DXF R12, layers CUT / BEND, k-factor 0.4). Removed the STL / STEP of every deleted part.
  Pose functions: `pose_parts(lift)`, `fpc_loop(pan)` (B frame), `fpc_lift(lift)`, `ffc_tails_krk(lift)`, `pigtail(lift)`, `mk_rameno(theta)`,
  `crank_angle(lift)`, `ffc_lengths()`, `ear_flat_pattern()`.
* `t4_pan_checks.py` – rev. 2 module checks A–H -> `pan_checks.json` (only rev. 2 entries) + `pan_checks.log`.
* `pan2_work/` – fix scripts, `prev2_pan.py` (Blender previews), `export_poses.py` (pose STLs lift 10 / 20, pan loop -90..90 in
  `pan2_work/poses/*/stl/`), `parts_pan_extra.json` (deviations merged into parts_pan.json), `additions_pan_rev2.txt`, `front_stack.py`.
* Previews (600 px, 16 samples, looked at): `prev2_pan_iso.png`, `_iso_pred` (+X end, FFC lift loop), `_iso_bez_krku`, `_modul` (lift module
  alone), `_zdola`, `_rez_x0`, `_rez_kluka` (section x -14.4), `_rez_ffc` / `_rez_ffc20` (section y 5.6 through the lift loop, lift 0 / 20),
  `_v_trupe` (section x 0 with the RAM rev. 2 parts), `_det_kanal`, `_det_kanal_m90`, `_det_kanal_p90` (duct at z -42.9, pan 0 / -90 / +90),
  `_zdvih20`.

## Parts (rev. 2) – masses from the STL volume
| part | grp | material | mass g | notes |
|---|---|---|---|---|
| P_sachta | P | tough resin | 15.5 | slim well, r max 26.50 (STL), journal ring r 26.37 + tape, hub disc, back floor, drum shroud + lip, pads A / B, rail |
| P_drziak_serva | P | tough resin | 3.2 | lift-servo pocket: closed keyhole, F11 block, tongue, stop bridge + lug |
| koleso_pan | P | brass (bought) | 20.1 | 36T m0.8, face 4, bore 8 H7, plain; phased to the RAM pinion |
| L_ucho | L | 304 stainless 1.5 | 1.5 | bent L (R1.5), relief kerf, arm notch, slot 2.2; DXF flat pattern |
| L_pata | L | Al flat bar 20 x 4 | 6.4 | Ø11 hole, DPS slot, 1 x M2 tap + Ø2 dowel hole |
| rameno_zdvih + cap_kluky + skr_ramena | P | Al / steel (bought) | 0.6 + 0.15 + 0.3 | Al arm, pin ISO 8734 2 x 6 at r 10.00 |
| servo_zdvih | P | MG90S | 13.4 | unchanged position, lead exit stub |
| DPS_krk | L | FR4 + 2 x FH19C-5S | 0.45 | ZIFs under the board |
| ffc_par (+ ffc_A/B_krk, ffc_A/B_nosic) | P / L / T | FFC 0.5 mm 5 p | 0.21 + tails | stacked pair, rolling pan loop, riser, lift loop with Z-fold |
| pigtail_zdvih, konektor_zdvih, kabel_zdvih | L / P | wires, PicoBlade | – | lift-servo connection |
| PTFE: ptfe_pas_capu + 7 guide strips | P | PTFE 0.13 | – | journal tape (r 26.50) and land tapes |
| F10: skr / podl (DIN 433) / vl A, B + kolik_F10 (2 x 5) | P | steel / brass | – | pocket -> stage |
| F11: skr (M2 x 6) + podl + matica (DIN 562) | P | steel | – | servo tab -> F11 block |
| F12: skr_F12_1 (M2 x 6) + kolik_F12 (2 x 4.5) | L | steel | – | ear -> foot (metal–metal) |
Deleted: P_koleso, P_kluka, L_jazyk, fpc_pan, spoj_zdvih, kolik_kolesa_1/2, kolik_dorazu, kolik_ucha, skr_kluky, skr_jazyka, skr_F12 (old),
skr/vl_F10_1/2 (old names), ptfe_pasik_8; fin, apron, FPC groove, Ø4.8 tool hole, glue groove, r 28.07 drum and the lightening pockets of P_sachta.

## Checks run on the final geometry (`t4_pan_checks.py`, `pan_checks.json`, log `pan_checks.log`)
Final runs: A B D E F G H at 14:15–14:31 on the final STLs; **C (C1/C2/C3) ran at 13:55 on the geometry before the last two edits**
(pad-B flare clipped at z -41.9, riser groove limited to r >= 16.7). Both edits only remove material or restore the shroud ring that
was checked in the earlier C runs, so they cannot reduce a clearance. C was not repeated because it takes 5 min.
| check | result | status |
|---|---|---|
| A solids / slim stage | 38 parts, all valid single solids, STL watertight, all 38 STEP < 12 MB. Permanent stage r max **26.50** (P_sachta corners and journal tape; FFC fixed leg 26.30). Clearance to the glued ring is 0.248 and to the rev. 2 bore 0.150. The tails are tucked into the empty well before the stage goes up. | PASS |
| B PAN_ENV2 + sectors (lift 0..20) | no violation. Smallest margins: servo corner 0.016, FFC riser 0.05, lift loop at lift 20 0.08 (r 32.12 vs 32.2) | PASS |
| C1 inside the module, lift 0..20 | no undeclared pair below 1.0. Declared fits: rest gap 0.15, pin in the slot 0.10, ear to arm 0.40, neck to tapes 0.17, lands 0.30, etc. | PASS |
| C2 vs RAM rev. 2 STLs + OBAL (rev. 1 STLs; T_stred replaced by the analytic rev. 2 bore) over pan -90.3..90.3 x lift 0..20 | **FAIL (front stack)**: FFC lift loop and pigtail to T_drziak_repro / DPS_led / T_drziak_led / reproduktor 0.00–0.62 at pan -85..-90.3. P_drziak_serva to T_paluba 0.87 at the 0.3° overtravel pose only (1.0 at ±90.0). Every other pair is declared: gear 0.3 above the deck, bridge and flush F3b heads (stack 17.1); FFC 0.1 above the deck; shroud 0.6; journal 0.142; stop contact. | FAIL |
| C3 36T gear vs rotating RAM pinion (73 poses) | min flank gap 0.0385, no penetration (pinion z -45.9..-41.9 = gear plane) | PASS |
| D hard stop | contact at -89.988 / +90.016 (R2 pin positions = RAM STL). Engagement 2.6 (2.5 with the L1 rise). Bridge 1.0 above the pins. | PASS |
| E crank | stroke 20.000, dead centres at 0 / 180, pin-to-slot flank 0.100, slot ends 0.60 / 0.62, ear-to-arm gap 0.40. The arm / pin sweep has 1.0 to the pocket and the stage. | PASS |
| F1 lift module (+ ear on the pin) out +Y at pan 0 | not blocked; nothing below 0.8 after dy 0.3 (door-magnet pad silhouette respected: plate x <= 17 above z -30.5) | PASS |
| F2 neck + foot + DPS_krk up through the collar-disc opening (45.5 x 20.5) | footprint 100 % inside | PASS |
| F3 line of sight door -> ZIF mouths | **0.775 at pan +85** (needs 0.80), 0.806 at pan +90. Most rays are blocked by the FFC fixed-leg pillar beside ZIF B. | FAIL at 85 / PASS at 90 |
| F4 tool paths | F10 A / B with Ø4.5: 0.25 / 0.15. F12 with a 1.3 hex key through the Ø2.4 bridge hole: 0.55 (Ø4.5 not possible). **F11 with Ø4.5: -0.73** against the T_stred door frame (rev. 1 STL); a **Ø3 driver clears by 0.02**. | FAIL (Ø4.5 rule) |
| G resin rules (K13) | Wall scan of both printed parts: every reading below 2.0 is a declared feature (min 0.65 lip, 0.80 insert floors, 1.00 nut-slot wall). Both parts are 1 shell (no void). Root list, print table, no PETG / POM, no heat-set inserts, no countersunk head in resin. | PASS (declared exceptions listed in `pan_checks.json`) |
| H strength (Z2 allowables) | 30 rows, all OK. Tightest: stop bridge at the key hole 7.67 / 8.5 at L8; F10 dowel 6.47 / 8.5 at L8; rail lips 6.9 / 8.5; F10 insert bond at 0.04 N·m 3.3 / 4.0. Metal: ear 100 / 143 MPa (304, in-plane scaling of the rev. 1 FE); F12 screw 97 / 427. The MG90S side load is UNVERIFIED. | PASS (hand calc) |

## BLOCKING finding for the lead / architect: the +X-end cables collide with the OBAL front stack
* Measured (`pan2_work/front_stack.py` and C2): the FFC lift loop (outer leg x 31.1..31.35, Z-fold x 27.2..30.2) and the pigtail at the
  stage +X end reach r 30.2..32.1 at z -42..-24. At pan <= -60 deg (lift 0..10) they meet the front stack of OBAL, whose inner faces are at
  r 29.4..30.0 for z -42..-29 (T_drziak_led y -29.4, T_drziak_repro -30.0, DPS_led -30.1, reproduktor -31.6).
  Clearance >= 1.0 holds only for pan >= -55 (lift 0..5) / -60 (lift 10). It is 0.45 at lift 10, pan -90, and the parts touch at lift 0..5.
* The cause is in the architecture. PAN_ENV2 (r 33.4 / 32.2 at every azimuth for z -40.9..-11.5) and FFC_LIFT2 (r 31.7) ignore the front
  stack. Over pan ±90.3, only stage az 37..143 never faces it. Everywhere else, anything below z -28 must stay at r <= ~28.4.
  The rev. 1 lift loop (r 28.57) passed by a small margin.
* Fix options (none applied – they change the cable architecture):
  1. Turn the lift-loop U into the y–z plane: the strip width runs radially (x 25.35..28.35), with two static 90° twists in the bonded and
     foot-carried parts.
  2. Use a smaller U (R <= 1.5, R/t 15). The bend life is unproven.
  3. Couple pan and lift in firmware: pan < -55° only at lift >= 15. This does not protect against L3 (a hand turning the head at lift 0).
  4. Move the neck connection into the back sector. That needs another place for the lift module.
  The rows in PAN_ENV2 for z -42..-29 must become azimuth dependent: r <= 28.4 outside stage az 37..143.

## Deviations from §17 / ULOHA (details and reasons: `parts_pan.json["deviations"]` PD1–PD17)
PD1 F10 joint: pads A (7.0, -15.8) r 3.5 and B (18.4, -34/-38) r 3.25. Dowel at (18.4, -38.0). New bottom rail with a 3.0 tongue groove. Washers
DIN 433. Pocket plate x <= 17 above z -30.5. – PD2 pocket: closed keyhole, NO end wall / PORON, F11 block on the -X side of the tab,
F11 = M2x6 driven from +X. – PD3 stop bridge r 26.25..31.6, z to -36.2, Ø2.4 F12 key hole. – PD4 ear: 304 1.5, R1.5, relief kerf, arm notch,
F12 = 1 screw (x -10.0) + dowel (x -13.2). – PD5 crank pin 2 x 6. – PD6 back floor y >= 3.3 and az <= 135, centre r < 6.5 open; drum
az 8.4..140, lip from 27. – PD7 journal ring 24.37..26.37 to z -2, ribs, back wall 2.0 to x 23.2. – PD8 end window y -7.0..3.4, riser
groove along +X (y 3.3..7.2, r >= 16.7). – PD9 lift loop band y 4..7 with a Z-fold. – PD10 ZIF = FH19C-5S under the board, foot slot
y -7.1..6.7. – PD11 pigtail pads underneath, PicoBlade inline pair parked loose (no clip). – PD12 F10 torque 0.04. – PD13 k 0.4185.
– PD14 carrier route approximate. – PD15 densities set at runtime. – PD16 F12 key 1.3. – PD17 lug r 27.8, roots R1.0 / R0.8.

## Cables (developed length per FFC, rest pose; 203 mm stock)
FFC-A 190.8 (slack 12.2), FFC-B 178.7 (slack 24.3). This includes my carrier route of 65 / 58 mm (approximate, RAM zone; the spec
estimated ~40). Bend radii: pan U-turn centreline R 3.275 (pair 0.25, R/t ≈ 33 per FFC), lift U R 3.0, static bends R 0.6–1.0, two 45°
creases at each end (static). k = 0.4185, U-turn at B az 84 + 0.4185 pan (46.3..121.7), inner run >= 7.3° at pan +90.

## NOT done / NOT verified (do not treat as passed)
* The front-stack conflict above is unresolved. C2 is a FAIL.
* OBAL rev. 2 STLs did not exist (parts_obal.json is rev. 1, 16 Nov). C2 / F used the rev. 1 shell, front stack and door, with an
  analytic rev. 2 bore stand-in. F3 and F4 (F11) were measured against the rev. 1 T_stred. **Re-run `t4_pan_checks.py C F` once OBAL rev. 2
  is exported.**
* No FE in this run. All strength rows are hand calculations with stated Kt. K12 must check by FE: the lug + bridge (7.7 / 8.5 at L8),
  the rail lips, the turret-wall root (R0, declared) and the T_cap root (RAM).
* Bought-part data is UNVERIFIED: the FH19C-5S body 4.5 x 3.85 (catalogue A/D values), PicoBlade mated length 12, the MG90S spline count and
  arm product, the 36T gear bore / hub, ISO 7380 head sizes, and the MG90S side-load rating.
* The FFC is modelled as ideal strips with crease blocks; twists in the riser bend (19°) and the Z-folds are idealised. The carrier run
  is approximate and its clearance to the RAM bosses is only checked as declared contact. The pigtail hanging loop is a guessed shape.
* The servo-lead exit is the E2 model position. The F11 tool path assumes the soft lead is pushed aside.
* No slicer run. The print orientation and support faces are stated, not simulated.
* F10 torque is reduced to 0.04 N·m (R2 had 0.05). This must go into the torque table (docs / integrator).

