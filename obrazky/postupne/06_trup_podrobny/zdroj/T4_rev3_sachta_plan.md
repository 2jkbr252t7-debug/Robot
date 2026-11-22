# T4 rev. 3 – strengthening of the rotating well and its bottom (lead decisions, binding)

Trigger: the user asked "is the well strong enough for resin printing at the bottom, where the gear is – won't it break off?".
Two independent reviews ran on rev. 2 (K1–K13 all pass there):
* `sachta_a/` – own 3-D voxel FE on the real STL (results_v4.json, fe_cases_v4.py, fe3d.py, collect_v4.py, hand calcs h02 / h03,
  geometry g10; structured result in /home/user/Robot/obrazky/postupne/06_trup_podrobny/kontrola_sachty/a/vysledok.json): NOT OK –
  the 1.25 hub disc itself is fine, its CONNECTIONS are weak (findings S1–S7 major, S8–S11, S16 minor).
* `sachta_b/` – real-life failure modes (m04, m05; …/kontrola_sachty/b/vysledok.json): buildable after two fixes (B1 = S1, B2 shroud)
  plus notes B3–B13.
Rules stay: T4_zivica.md (Elegoo Tough; allowables 8.5 normal / 4.3 sustained or unfilleted notch / 12.9 abuse incl. stress
concentration; epoxy design 2.7 MPa), approved exterior, finished head / neck (B), slim stage r ≤ 26.5 (must pass the glued ring),
moving ↔ static clearance ≥ 1.0, no torque screwdriver, as few parts as possible.

## Decisions (what must change)
R3-1 **F15 thread** (S1 / B1): ISO 7380 M3 × 8 with 2 × DIN 125 M3 stacked on the DIN 9021 (no screw cutting) – or an equally simple
  variant if the stack check fails. Engagement in T_most ≥ 1.5 mm at worst-case screw length and thread run-in; strip margin ≥ 2 on
  (0.10 N·m fingertip preload + 2 × L1). Correct spec and K12 A7d with real numbers.
R3-2 **Axial retention must not depend on the epoxy bond alone** (S3): today well → bond → gear → washer → F15. Preferred: make the
  retention positive on the WELL (e.g. the retention washer overlapping the hub ring with T_cap raised accordingly, or another
  mechanical stop) so that with the bond completely failed the stage still cannot lift more than 0.3 mm and the pan stop stays
  engaged. If no positive variant fits, prove the bond with FE peel ≤ 2.7 MPa in the positive-location model AND add the bench pull
  test – but try the positive variant first and say exactly why it does not fit before falling back.
R3-3 **Hub ring ↔ walls** (S2): remove the weak "lens". Options to evaluate with FE, cheapest first: (a) lower front wall ≥ 2.3 thick
  for z −40.9…−36.8 with blended lens ends (R ≥ 0.5–1.0); (b) a real front floor: lower the pan pinion / reduce the mesh width to 3.0
  (pinion top z −42.9) so the well gets a ≥ 1.2 floor over the full front sector (re-check tooth stress of the bought gears and the
  buy list); (c) ribs. Choose what passes L3 (0.6 N·m hand twist, both directions, abuse 12.9) and L1 at lift 20 (8.5) with margin.
R3-4 **Window and sill corners** (S4, S6, B11): R ≥ 1.5 on every window corner (+X end window, back window, sill / jamb), R ≥ 1.0 at the
  corner / floor joints; wall around the +X window top ≥ 2.0 where space allows; +X PTFE land ≥ 3 mm from the window edge if the
  FFC / DPS_krk allow.
R3-5 **Lift-module load path** (S3, S6, B8): the module's vertical (L1 up, L2 down at lift > 0) and stop (L8, L3) forces must enter the
  back wall positively and spread – full-width rail / ledge with R ≥ 1 roots, away from the sill corner; no reliance on friction
  (Z3.7) and no reamed fitted screws (precision a hobby builder cannot hold) unless nothing else works.
R3-6 **Slim corners / journal band** (S5): re-check after R3-3…R3-5; keep ≥ 1.34 in the band zone where the r 26.365 envelope allows
  (turn only what must be turned), +X pillar stiffened if still over 8.5.
R3-7 **Drum shroud** (B2 / S10): no free-hanging arch – web joining the shroud to the back-wall bottom (with the matching relief in
  P_drziak_serva if needed) and filleted roots; printable without supports on it.
R3-8 **Rest gap vs MG90S toggle** (S7): the foot must never be clamped onto the hub ring by the servo near bottom dead centre. Design the
  gap and the firmware rule together (nominal gap with print tolerance, calibration step that finds the landing angle and stores a
  margin) and keep the L2-at-lift-0 load path valid (K12 row for the deflection needed to land).
R3-9 **Minor** (S8, S9, S11, S16, B3–B7, B10, B12, B13): T_cap root R1.0 and initial axial play ≥ 0.12; retention washer overlap with a
  chamfered bought-gear bore; thin skins < 1.2 declared or thickened; K12 corrected (H2 bond area 387.8 not 442, H3, A7d, S06b Kt, TQ
  F15 creep direction) and NEW K12 rows for every FE-critical spot (lens / floor junction, window corners, slim corners, rail, bond
  peel, shroud root) fed from a reproducible FE script; documents: supports allowed on the hub-disc landing face then sanded flat,
  T_cap hole drilled Ø3.1, toughened 2K epoxy on abraded surfaces, Loctite 222 on F10, PTFE-compatible grease on the pivot tape,
  towel under the bare stage, no long holds at mid lift.

## Acceptance
* FE on the NEW STL (reuse and extend sachta_a's harness; positive-location module joint, gap journal, collar-disc upper guide) for
  L1 at lift 0 and 20, L2 at lift 0 / 10 / 20, L3 both directions, L8 into both stops (converged, no non-physical tension): every
  resin stress within the allowable of its class at the stated averaging distance; bond within 2.7 or not needed for retention.
* K1–K13 all PASS on the new geometry (K3 sweep, K7 stage up through the glued ring, K10 print cups, K12 incl. the new rows).
* Exterior untouched (K8), part count not increased except the two M3 washers.
