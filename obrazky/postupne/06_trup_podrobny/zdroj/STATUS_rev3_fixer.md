# STATUS rev3 fixer (round 1) – WORK IN PROGRESS (interim save 2026-11-22 13:05 UTC)

Backups of every changed file: `rev3_backup/<name>.bak` (+ `rev3_backup/stl/` = the rev. 2 STL set).

## Done so far
* `fe_sachta/` harness: `femodel.py` (model from the current STL, contact solver), `cases.py` (loads / supports / joint), `post.py`
  (spots, 0.4 mm averaging x 1.04, bond), `fe_design.py` + `design.json` (joint description written by t4_pan / build_all),
  `run_fe.py` (entry: acceptance cases + fail-safe cases -> `results.json`; `--validate` -> `validation.json`).
* `t4_common.py`: block `rev3 (sachta)` (dict `R3`, R2 re-bindings, PAN_ENV2 floor band).
* `t4_pan.py`: `mk_sachta` rev. 3 (floor over the whole well, hub lip, R1 roots, R1.5 window corners, lintel, R3.0 inner corners, rail block
  high on the back wall with a stadium groove, pad C, shroud roof, spline relief), `mk_drziak` (stadium tongue, plate relief, keyhole
  relief), `mk_ucho` (flange end chamfer), `mk_koleso` (lower bore chamfer), 8th PTFE strip (lintel), `fe_design()`.
* `t4_ram.py`: T_cap root R1.0 + hole D3.1, F15 = M3x8 + 2 x DIN 125 + DIN 9021 (parts pd_F15_d1 / pd_F15_d2), pan pinion face 3.0.
* `t4_assembly.py`: B2, B2b (F15 calibration), B4b, B7b, T7, T11 (rest-gap calibration), S3, S4.
* `t4_ram_checks.py`, `t4_pan_checks.py`: pivot rows / strength rows updated (not yet re-run to the end).
* FE evidence for R3-3 at h 0.6 (res/var_lens_h06, res/var_floor_h06): option (a) "lens + 2.3 wall" fails L3 (lens 39.6-40.6 MPa vs 12.9),
  option (b) "real floor" passes L3 (lens 4.7, max spot 10.6) -> (b) chosen.

## Still to do (this list is replaced by the final status at the end of the round)
* FE: validation run on the rev. 2 STL (h 0.4) - running; coarse runs of geometry v2; final h 0.4 acceptance run -> results.json.
* checks.py: K12 FE rows; module checks re-run; build_all + checks.py --force.
* T4_spec.md 17.17, opravy3.md, final STATUS, 3 previews.

---
# CONTINUATION (round 1b, started 2026-11-23 09:30 UTC) - running notes, replaced by the final status at the end
* 09:50 read state. Sources = geometry v6 (t4_pan.py 14:06), stl/ = older build. LD1-LD6 of the lead are binding.
* FOUND (harness, inherited): every L2_lift20c run of rev. 3 (v3..v6) was NOT in equilibrium - the guide-force NNLS in
  cases.lift_case_collar had no feasible solution (one back land at x 12.8 + centred collar patterns cannot balance the yaw), the
  residual (38 / 99 N sideways + 47 N.mm) was applied as a net load -> journal reaction 94 N.  The LD5 "open spots of L2 at lift 20"
  (top plate / ring 20.7, back-window top corner 15.8 ...) come from that non-physical load.  Fix: collar contact may sit anywhere
  along the opening edge (patterns at x 0 / +-15 and y 0 / +-6), residual must vanish (case is flagged otherwise).
* TODO order: harness (LD1 filter + contact rows, LD2 classes, equilibrium) -> rebuild v6 -> FE v6 governing cases -> v7.. -> freeze.
* (round 1c, 09:55 UTC 11-23, third start after a server error) harness edits of 1b verified by diff vs rev3_backup/*.r1:
  cases.py (classes, collar patterns x 3 per edge, contact npz, 'equilibrated'), post.py (LD1 filter, contact rows need design.json
  'bearing' - NOT yet written by t4_pan.fe_design), run_fe.py (capacity_N, kind).  Next: fe_design 'bearing', FE v6 governing cases.
* 11:40 FE v6b (geometry v6, new harness, res/v6b_h06): well OK except L1 lift 20 +X lintel 13.7 / +X window corner 13.6 (abuse 12.9).
  POCKET field (rev3_work/pocket_field.py): NOT contact artefacts - the 2.0 plate bends under the stop moment about z (50 .. 180 MPa),
  sharp sole / fin / notch corners; the conservative servo lever (keyhole 110 N, tab 80 N) loads the F11 block.  FOUND: the round-1
  dowel boss (x 16 .. 20.8, y 17.6 .. 20.2) blocks the MG90S insertion (-X travel 9.2).
* v7 (in the sources, backups rev3_backup/*.v6): ROOF beam on P_drziak_serva, sole / notch / lug fillets, no dowel boss (dowel D2 x 6 at
  x 17.4 = servo end stop), ledge rib x -8 .. -2.9, shelf x -6 .. 4, pads D / E.  Harness: servo x-couple loads, load patches in cz.
* 11:05 FE v7 (res/v7_h06): roof beam worked for the stop moment (pad A / pad E carry it) but K7 is BLOCKED (door lintel of T_stred at
  z -12.75) -> roof removed.  L8 still 130 .. 166 MPa at the notch corner / plate fin (bottom chord cut by the shelf notch); L1 at lift 0
  (normal 8.5) on the WELL: +X pillar foot / thin floor 16 .. 17, slim corner 12.1, back-window -X top corner 9.3 (same in v4 - was not
  looked at in round 1); L1 lift 20: +X lintel edge 13.6, window top corner 14.2 (abuse 12.9).
* v8 (sources + stl of 11:04; backups *.v6): no roof; shelf = ledge in a closed WINDOW of the plate (bottom chord kept), pad C on the
  bottom chord, turret wall 4.0, F11 nut slot closed at +Y, R0.3 under the block, +X end-window sill raised to -39.2, end-window top
  corners R2.0, back-window -X top corner R2.5, plateau-top / ledge fillet.  femodel: anti-chatter (node frozen open after 6 flips).
  FE v8 running (res/v8_h06), pan checks A-G running (rev3_pan_checks_run.log).  NEXT: freeze, final FE set h 0.5, K12, build_all, docs.
* 11:50 FE v8 (res/v8_h06): L8 cw stop 83 MPa (plate bottom chord at the turret), ccw 27.5; L1 lift 0 (normal): plate chord 20.4, +X
  pillar foot 19.3 (the v8 "raised sill" was not built: first window cut removes the wall), corner arcs 14.7 (R2.5 filler made it worse),
  ledge root 11.8; L1 lift 20: lintel 13.8; L2 lift 20: plate top strip 20.9, shelf root 15.9 (contact edge).
* v9 = FROZEN geometry (sources backed up as rev3_backup/*.v9): curb at the +X pillar foot (sill -39.5 for y >= 0.3) really added,
  back-window R2.5 filler removed, end-window R2.0 fillers clipped to the wall profile, block chamfer 1.6, turret-wall face recessed
  0.2 except a corner pad at the plate, F10_A moved to x 4.2, lug inner root clipped to the PAN_ENV2 sector.  Harness: true patch
  rectangles of the vertical stops in the LD1 filter.  NEXT: build_all -> final FE set h 0.5 on stl/ -> K12 -> checks.py --force -> docs.
* (round 1d, 16:35 UTC 11-23, fourth start) v9 final set at h 0.5 finished (12 cases) -> archived as fe_sachta/results_v9_h05.json + res/v9_h05
  (NOT the final results: LD7 asks for v10).  v9: 24 failing rows; fail-safe hub lip 32.7 > 25.8 (L1_lift20c_nobond) still to judge.
* 16:50 v10 (LD7) in the sources + stl/ (build_all --only pan, rev3_build_pan_v10.log): R3["CURB"] = floor-level curb under the back
  window x -14.5 .. -6.5, y to 15.1, z -41.9 .. -40.65 (NOT higher: the ear flange z -40.5 / F12 head pass 0.15 over the sill on the way
  in, K7) + sole front face of P_drziak_serva down to -41.9 (plate relief only x > -7.3) = bearing 9.0 mm2; SOLE_ROOT_R 1.0 -> 2.0;
  design.json face curb_y, post.py contact row.  FE v10 h 0.6 running: fe_sachta/res/v10_h06 (.out) - L8 both stops, L1_lift0, L2_lift0_chain.
  Pan-check FAIL rows reproduced: C1 FFC tails 0.82 / 0.89 to the R2.0 top corners of the +X end window at lift 20 (real, declare);
  C2 two pairs designed at exactly 1.00 (declared by 1c, re-run needed); F3 ZIF sight criterion changed by 1c (closed floor), re-run needed;
  H rows 29 / 4 = stop path (LD7).  RAM C5 0.73 = annular-sector model of the lug vs deck trim (real mesh: 0.95 at -90.3, >= 1.0 at -90.0,
  pan C2) -> criterion to be corrected; C6: T_cap r 4.85 = its R1.0 root fillet (criterion 4.501 outdated).
* 17:05 FE v10a (curb only, res/v10_h06): +90: plate 29.1 (F10_A hole edge = clamped washer zone, added to the LD1 contact zone in cases.py),
  turret 18.3, sole 14.7; -90: plate / sole corner 74 / 68 at (-6.3, 17.1, -40.2) (v8 at the same h: 83), F11 block 32.9, turret 30.8;
  pairs at -90: curb 11.2, pad D 19.8, F10_A -24.5, F10_B -8.8, dowel_x 33.  NOT enough (capacity 0.15 N.m).
  Test (no geometry): same model with the cw pin force turned 45 deg (design_x45test.json, res/x45test_h06): F10_A -14.9, pad D 9.1,
  curb 31.4, corner 51, F11 block 20.4, turret 18.9 -> the direction of the pin force is the lever that matters.
* 17:10 v10b = THE ONE CORRECTION of LD7 (sources + stl/, rev3_build_pan_v10b.log; v10a kept in rev3_backup/*.v10a + fe_sachta/snap/v10a):
  (1) R3["STOP"]["cw_face"]: cw face of the lug = plane tangent to pin 1 at -90.0, normal 38 deg from +x (pin force 30.1 N = 23.7 along -x
  + 18.5 along -y onto the curb; nose tip 1.05 from the deck trim wall at -90.0; contact line 1.9 from both face ends; pin 1 / deck unchanged);
  (2) sole (R3["SOLE_EXT"]) + curb continued to x -16.9 (seat 8.9 x 1.25 = 11.1 mm2); (3) plate relief cut obliquely (PLATE_RELIEF_CUT):
  the plate root keeps its back 1.4 mm down to -41.9 at the sole.  FE v10b h 0.6 running (res/v10b_h06).  After it: FREEZE whatever the
  number (LD7), build_all, final set h 0.5.  Checks updated for the new face: t4_ram_checks (env_lug plane, C8), t4_pan_checks H rows 4 / 6 / 29.
* 17:25 FE v10b h 0.6 (res/v10b_h06): -90: every row <= 23.5 (sole 23.5, turret 14.3, F11 block 13.7; curb 26.9 N, pad D 5.4, F10_A -10.4)
  EXCEPT 44.6 at (-3.1, 16.9, -40.35) = the feather end of the new plate-root fin; +90: 28.9 at the same feather, turret 16.2, sole 12.8;
  L1_lift0 / L2_lift0_chain: unchanged class of rows (fin feather 15.2 in L1).
* 17:29 v10c = detail of the same correction: fin ends bluntly at x -5.0 with an R1.5 run-out (R3["PLATE_RELIEF_CUT"/"PLATE_RELIEF_RUNOUT"]).
  GEOMETRY FROZEN = v10c: build_all.py ran (rev3_build_all.log, 169 parts ok), FE stamp 95c09f9277bd, snapshot fe_sachta/snap/v10c,
  sources rev3_backup/*.v10c.  FINAL FE SET h 0.5 started 17:31 (nohup, --jobs 2, 12 cases, stops first): log fe_sachta/res/main_h05_v10c.out,
  results -> fe_sachta/res/main + fe_sachta/results.json.  If interrupted: re-run "run_fe.py --h 0.5 --jobs 2" (finished cases are kept by stamp).
  NEXT: checks.py --force (module checks), K12 after results.json, mk_docs.py (new tail in the scratchpad -> rev3_work/mk_docs.py), previews.
* 17:40 checks.py --force on v10c (rev3_checks_force.log) found K2 FAIL - three rows: (1) P_sachta <-> P_drziak_serva 0.085 mm3 / 0.044 thick at
  x -8.8 .. -5, y 15.1 .. 16.8, z -41.9 .. -41.85: the new fin stands on the FFC retaining lip (r 16.7 .. 17.5, modelled 0.05 above -41.9) = the rev. 2
  finding m1 again -> R3["LIP_RELIEF"] (module bottom -41.75 inside r 17.6) IN THE SOURCES, NOT YET BUILT; (2) ptfe_pasik_7 <-> ptfe_pasik_8 overlap
  (round-1 lintel tape y to 6.0 over the +X land strip) -> lintel tape y (-6.0, 4.9) in R3 (sources); (3) skr_F15 <-> T_most 3.75 mm3 > declared 3.0:
  the declaration was for M3x6 (0.8 engaged) -> 4.6 for M3x8 / 1.80 (checks.py K2_FITS, reason recorded).
  The final FE set was STOPPED (stamp will change): only L8_stop_p90 finished on v10c at h 0.5 (plate 25.3, turret 19.1, lug 15.8, sole 13.0 ->
  capacity 449 N.mm); L8_stop_m90 still running as information.  NEXT: wait for the rest of checks --force (pan C / E / F / G), fix what it shows,
  build_all (= v10d, FREEZE), final FE set h 0.5 again + checks.py --force again in parallel, then K12, mk_docs.py, STATUS.
  Previews prev3_sachta_*.png re-rendered 17:36 (v10c; the v10d changes are not visible in them) and looked at: OK.
* 18:15 v10c at h 0.5 (information, res/v10c_h05): -90: sole / plate corner 41.8 / 38.6 at (-6.5, 17.1, -39.9), F11 block 24.5, turret 15.1
  (capacity 272 N.mm; v9: 110.5 -> 103 N.mm); +90: 25.3 (449 N.mm).  LD7 target (<= 30) NOT met at -90; per LD7 no further stop-path iteration.
  checks --force on v10c: K1 K3 K5 K6 K7 K9 K11 PASS; K2 FAIL (3 rows, above); K4 FAIL (K4_DECL still had the rev. 2 table: rev. 3 run-outs /
  declared thin features added with reasons; two real items fixed in the geometry: 0.2 skin at the F10_A insert hole -> hole through, fillet
  slivers past the lug nose -> clipped); pan G: fin + sill fillet declared; pan A-F PASS (F3 with the above-floor criterion 0.845).
* 18:17 v10d = FROZEN (v10c + lip relief + F10_A hole through + fillet clips + lintel tape y 4.9): build_all ran (rev3_build_all.log, 169 ok),
  snapshot fe_sachta/snap/v10d, sources rev3_backup/*.v10d.  STARTED: final FE set h 0.5 (fe_sachta/res/main_h05_v10d.out -> results.json)
  and checks.py --force (rev3_checks_force.log).  NEXT: when both are done: checks.py K12 (no --force), rev3_work/mk_docs.py, final STATUS.
* 18:40 OOM: the kernel killed the FE case L1_lift0 (6.7 GB rss) while two FE cases + checks.py --force ran together (15 GB limit).  The other
  cases continue; L1_lift0 must be re-run: "cd fe_sachta && python run_fe.py --h 0.5 --jobs 1 --cases <the same list>" keeps the finished cases by
  stamp (d57319eb33aa) and runs only the missing ones.  Until checks.py --force has finished only ONE FE case runs (the second is paused with SIGSTOP).

# FINAL STATE of rev. 3 (lead, 2026-11-23 20:40 UTC, after the fourth interruption of the fixer at 19:31)
* Geometry FROZEN = v10d (stl/ of 18:10, checks stamp b9361c2258e96717, FE stamp d57319eb33aa; sources rev3_backup/*.v10d, snapshot fe_sachta/snap/v10d).
* Final FE set at h 0.5 COMPLETE on v10d: 10 acceptance + 2 fail-safe cases, all converged and in equilibrium -> fe_sachta/results.json
  (442 rows, 26 rows = 14 spots above their allowable at the plan loads).  The two cases lost at the OOM / interruption (L1_lift0, L1_lift0_nobond)
  were re-run alone (fe_sachta/res/main_h05_v10d_b.out).
* checks.py on v10d: K1 K2 K3 K4 K5 K6 K7 K8 K9 K10 K11 K13 PASS; K12 FAIL = by design of LD5 / LD7: rows above their allowable are NOT declared away,
  they stay FAIL and carry the load at which the spot reaches its allowable (634 rows, 38 FAIL: 26 FE rows + pan H29 / H4 hand rows of the stop path and
  their FIX2 notch rows; 2 not verifiable = bought-part data).  Module checks: ram all ok, obal all ok, pan A - G ok, H_strength = the stop path rows.
* Usage limits (capacity = plan load x allowable / stress of the governing row; rev3_work/mk_docs.py -> opravy3.md, out/zmeny_rev3.txt):
  lift by the head, neck parked 14.8 N (back-window corner 17.27 vs 8.5); pull up, neck extended 22.9 N; push down parked (chain) 24.4 N; push down at
  mid lift 21.9 N; twist cw by hand 455 N.mm; stop +90: 451 N.mm; stop -90: 278 N.mm (sole / plate corner of P_drziak_serva 40.9 vs 12.9 at 880 N.mm).
  LD7 target (<= 30 MPa at 880 N.mm at both stops) NOT met at -90 (v9: 110.5 -> v10d: 40.9; +90: 30.5 -> 25.2).  Per LD7 no further iteration:
  stated limit + servo EEPROM (angle limits +-85 deg, Max Torque 15 %) + "never force the head against an end stop".
* Fail-safe (gear bond failed completely): hub ring / lip 30.54 > 25.8 in L1_lift20c_nobond at the 30 N plan load (v9: 32.7).  Judgement of the lead:
  a double fault outside the stated limit - at the usage limit of that situation (22.9 N, pull on the EXTENDED neck) the row is 30.54 x 22.9 / 30 = 23.3
  < 25.8, and with the neck parked (L1_lift0_nobond) the worst fail-safe row is 20.45 at 30 N (10.1 at the 14.8 N limit).  So inside the stated usage
  limits the stage stays captive on the washer even with the bond gone; above them (30 N on the extended neck AND a failed bond) the lip may crack.
  Rise of the stage in the fail-safe cases: see opravy3.md (axial play + elastic part, limit 0.3).
* Documents regenerated from the computed results at 20:38: opravy3.md, T4_spec.md 17.17 (40 lines), out/zmeny_rev3.txt, rev3_work/summary.json.
  Previews prev3_sachta_zad / zdola / zhora.png (v10d, 19:05).
* NOT done (scope decision of the user: only the fix + printable models): images, video, animation, the full assembly guide (out/montaz_trup.txt,
  out/NAVRH_trup.md and out/T4_*.png are still rev. 2 - out/zmeny_rev3.txt lists what differs).
* Independent check: overenie3/ (one verifier, started 20:25 UTC); its result and a possible fix-back are appended below.

# FIX-BACK after overenie3 (fixer of the one allowed fix-back round, 2026-11-23 21:56 UTC) - dated block
Input: 11 findings of the verifier (overenie3/: V1, V2 major; V3 - V7 minor; V8 - V11 notes).  My scripts and results: fixback3_work/.
GEOMETRY NOT CHANGED: stl/ + step/ = frozen v10d (checks stamp b9361c2258e96717, FE stamp d57319eb33aa); the final FE set (fe_sachta/results.json) is untouched.
Note on the task's "stale before 20:40" rule: results.json (20:38:05), checks.json, opravy3.md, T4_spec.md 17.17 and out/zmeny_rev3.txt (20:38) were the lead's FINAL
files (12 of 12 cases, all converged / equilibrated, cases_missing empty) - they were read as final and have now been regenerated by this round.

* V1 (major) - measured by FE, not by hand: fixback3_work/fe_gap.py = case L8_stop_m90 of the final set (same STL, design.json, h 0.5; harness files not
  modified, the pair list is patched after Stage construction) with a clearance at the pair curb_y:
  - gap010_h05 (clearance 0.1 mm, h 0.5, stamp d57319eb33aa, converged True, equilibrated True, 1625 s): governing row 39.73 / 12.9 MPa (P_drziak_serva sole + high bridge (z <= -36) at [-6.5, 17.22, -39.85]); curb 25.99 N on 12 of 54 nodes, pad A -10.74, pad C 0.0, pad D 6.35, dowel x 23.63; relative y travel of the sole at the seat -0.103 (x -16.8) .. 0.089 (x -8.3) mm
  - gap030_h05 (clearance 0.3 mm, h 0.5, stamp d57319eb33aa, converged True, equilibrated True, 1148 s): governing row 38.14 / 12.9 MPa (P_drziak_serva sole + high bridge (z <= -36) at [-6.5, 17.22, -39.85]); curb 24.17 N on 10 of 54 nodes, pad A -12.61, pad C 0.0, pad D 8.2, dowel x 23.62; relative y travel of the sole at the seat -0.303 (x -16.8) .. -0.061 (x -8.3) mm
  - gap0667_h05 (clearance 0.6667 mm, h 0.5, stamp d57319eb33aa, converged True, equilibrated True, 849 s): governing row 65.86 / 12.9 MPa (P_drziak_serva F11 block + nut slot at [-2.5, 17.2, -16.5]); curb 13.26 N on 6 of 54 nodes, pad A -23.14, pad C 12.36, pad D 14.94, dowel x 23.68; relative y travel of the sole at the seat -0.669 (x -16.8) .. -0.173 (x -8.3) mm
  - open_h05 (clearance 5.0 mm, h 0.5, stamp d57319eb33aa, converged True, equilibrated True, 684 s): governing row 105.19 / 12.9 MPa (P_drziak_serva F11 block + nut slot at [-2.5, 17.2, -16.5]); curb 0.0 N on 0 of 54 nodes, pad A -36.69, pad C 28.7, pad D 24.31, dowel x 23.74; relative y travel of the sole at the seat -1.165 (x -16.8) .. -0.291 (x -8.3) mm
  PARTLY REAL: the seat is needed and cannot be checked in the assembled torso, but the claim 'holds only with zero gap' is NOT confirmed - a clearance up to 0.10 does not lower the capacity; the cliff is at the critical clearance below.
  Seat open: capacity 108 N.mm (governing 105.19 MPa at 880 N.mm, P_drziak_serva F11 block + nut slot at [-2.5, 17.2, -16.5]) against 278 N.mm with the closed seat of the final set.
  The sole travels 1.165 mm toward the curb at 880 N.mm with the seat open -> a clearance of 0.05 / 0.10 mm closes at 38 / 76 N.mm, where the governing stress of the open model is 4.5 / 9.0 MPa (< 12.9).
  CRITICAL clearance 0.143 mm: from there the allowable is reached before the seat closes (capacity = open-seat value).
  Capacity at the allowable 12.9 with a residual clearance 0.05 / 0.10: 289 / 297 N.mm; stress at the 15 % torque limit (132 N.mm) / at twice it: closed 6.1 / 12.3, 0.05: 6.1 / 11.8, 0.10: 9.9 / 12.2, open: 15.8 / 31.6 MPa (lower bound 25.8).
  (State at torque T with clearance g = T / 880 x the state at 880 N.mm with clearance g x 880 / T; governing utilisation interpolated linearly between the computed
  clearances [0.1, 0.3, 0.6667] + closed + open.)  Torque limit if the seat is not there: 5 % (44 N.mm).
  Fix (text only, LD7 untouched): bench step B4c (new, before T7): bare P_drziak_serva on the stage with F10 tight, lamp inside the well, the sole / curb line is
  looked at from BELOW the stage (fixback3_work/v1_view.py: no module / gear material below the line, x -16.9 .. -10.5) - the 0.05 feeler must not enter (no light =
  closed; 0.05 keeps a factor of about 3 to the critical clearance); otherwise the sole is bedded on the curb face with toughened 2K epoxy (release agent on the
  sole).  The T9 instruction "0.10 feeler / one layer of 0.13 PTFE tape" is removed: a feeler blade can enter the 1.25 mm high slit only from below, and in the torso the
  deck is 1.1 mm under it (overenie3 s5_insert.out: P_drziak_serva <-> T_paluba 1.100); 0.10 leaves 0.04 to the cliff, and a 0.13 tape neither fits a 0.10 .. 0.13 gap nor stays (PTFE creeps).
  The condition and the open-seat numbers are in zmeny_rev3.txt 3 (B4c) / 4 / 5, opravy3.md (usage limits + fix-back section), T4_spec.md 17.17 item 6 and in
  checks.json K12 (usage_limit_conditions + summary clause; status and rows of K12 unchanged).
* V2 (major) - reproduced on the STEP solids (fixback3_work/v2_f12b.py): skr_F12_1 moved along +y overlaps P_drziak_serva from 2.4 to 19.9 mm (head D3.5 / key hole D2.4,
  6.63 mm3 = the head annulus); 3.7 mm behind the ear flange for a 7.3 long screw.  REAL (and in rev. 2 already).  Fix (text only): t4_assembly.py B5e / T9 / T11 / S1
  + zmeny_rev3.txt 3 (B5e, T9, T11, S1): F12 pre-loaded in the ear flange before the ear is hung on the crank pin (captive, play 2.4); started through the
  key hole about 3 mm before the seat (tip meets the foot between 4.4 and 2.0 mm; the last 2.0 mm are screwed while the module is pushed home);
  tightened at T11; S1 in reverse.  The step DATA of t4_assembly.py (move / legs / screws) are unchanged, only the texts.
* V3 - reproduced (STEP: no well material inside r 1.95 on the F10_A axis, y 10.3 .. 15.1).  Builder note B4a.  Geometry kept (changing P_sachta = new FE stamp).
* V4 - not re-measured (K4 lists the scallop feather, 30 cells).  Print note in zmeny 6.
* V5 - reproduced (STEP: L_ucho <-> P_sachta 0.140).  Print note in zmeny 6, straight-edge check in B4c, note in T9.
* V6 - reproduced (STL: ptfe_cap 3.5 -> 3.1 high, 1.0 above the T_cap base).  Line in zmeny 2 and spec 17.17 item 12.
* V7 - reproduced (fixback3_work/v7_spline.py: floor underside over the pinion axis at -41.70 for pan -90 .. +90; modelled tip -42.70, clearance 1.0).
  Line in zmeny 2 (measure the STS3032 before P_sachta is printed), spec 17.17 item 13 c.
* V8 - note, not re-measured; recorded in opravy3.md (fix-back table).
* V9 - (a) the unused rev. 2 declaration 'F10 A insert seat floor 0.8' removed from K4_DECL of checks.py; "checks.py K4" re-run on the cached mesh data: PASS, the
  same 28 declared features in use.  (b) T_cap print string 'through hole D3.4' -> 'D3.1' in t4_ram.py, parts.json, parts_ram.json (text field only: no rebuild,
  STL md5 fields untouched).
* V10 - note, nothing to do.
* V11 - reproduced from results.json: 2 fail-safe rows above 25.8 (L1_lift20c_nobond 30.54; L1_lift0_nobond 27.98, both hub ring / lip at
  (0.54, -4.11, -41.89)).  mk_docs.py now lists every fail-safe row above the lower bound with its load.  CORRECTION of the lead's block above: "with the neck parked
  (L1_lift0_nobond) the worst fail-safe row is 20.45 at 30 N" is wrong - it is 27.98 (hub ring / lip); at the 14.8 N usage limit of that situation it scales to
  13.8 MPa, so the lead's conclusion (captive inside the stated limits) stands.
* Found on the way (not in the findings): the sole / curb seat also carries 5.5 N in L2_lift0_chain and 7.1 N in L2_lift20c of the final set (0.3 N in L2_lift10).
  Open-seat variants of other cases, where computed:
  - open_L2_h05 / L2_lift20c (clearance 5.0, converged True, equilibrated True): governing row 11.38 / 12.9 (back-window corners (top + sill / jamb)); final set, seat closed: 12.35 / 12.9 (back-window corners (top + sill / jamb)); worst P_drziak_serva row open: 9.16 (P_drziak_serva plate (incl. fin, notch, low plate, dowel hole))
* Changed files: rev3_work/mk_docs.py (generator), t4_assembly.py (texts of B5e / T9 / T11 / S1), checks.py (K4_DECL entry removed; K12 condition clause), t4_ram.py +
  parts.json + parts_ram.json (one string), regenerated: opravy3.md, T4_spec.md 17.17, out/zmeny_rev3.txt, rev3_work/summary.json, checks.json (K4, K7, K12).
  Backups: rev3_backup/*.v10d (mk_docs.py, t4_ram.py, parts.json, parts_ram.json; t4_assembly.py.v10d existed and was identical) and rev3_backup/*.pre_fixback3
  (checks.py - its .v10d backup was older than the lead's last edit -, checks.json, opravy3.md, zmeny_rev3.txt, T4_spec.md, STATUS, bl_K7.json).
* Checks after the round: K1:PASS  K2:PASS  K3:PASS  K4:PASS  K5:PASS  K6:PASS  K7:PASS  K8:PASS  K9:PASS  K10:PASS  K11:PASS  K12:FAIL  K13:PASS (K12 FAIL = the stated usage limits, as before).  K7 was re-run (--force --no-modules) with the edited step texts.
* NOT re-run (not needed, geometry unchanged): build_all.py, the final FE set, K1 K2 K3 K5 K6 K8 K9 K10 K11 K13, the module checks.
* Open: out/montaz_trup.txt (rev. 2 guide, steps 5 / 21 / 23 and service 1) still describes F12 as inserted after the module - zmeny_rev3.txt section 3 overrides it
  (stated there); the bench test of the pan-servo torque limit stays UNVERIFIED.
