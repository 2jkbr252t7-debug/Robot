# STATUS – fixer rev. 2 (runs 1 + 2, 2026-11-17/18)

Record of the fixes: `opravy2.md` (finding → real? → change → result) and `T4_spec.md` 17.16.
Backups: `rev2_backup/*.fixer.bak`. Work files / logs: `fix2_work/` (build_all_8.log, checks_run3.log, ram_S3.log, ram_DE.log,
tq_probe.py, f8_probe.py, fill_opravy.py).

Run 2 (continuation after the container restart at 00:48 UTC):
* audited run 1 against the .fixer.bak files (B1, G1, S1–S4, K1/K2, M1–M6 and the minors were already in the modules / spec);
* applied the LEAD DECISION on torque (no torque screwdriver, design case 0.10 N·m): new M2 insert 4 × OD 4.0 in Ø4.1 through holes
  (F7, F8, F10), F7 standoffs and F10 pads r 3.65, F10_B moved to (18.0, −33.3), F15 rows re-rated, all module torque rows at 0.10,
  K12 TQ rows + coverage, spec 17.16-13 rewritten;
* found that run 1's mech-m1 trim left 0.02 of overlap (new exact-BREP K2 regression) and fixed it;
* added regression checks: K2 exact-BREP pairs (m1 / m2), K12 TQ rows + coverage (S5), K13 ZIF / ear material / M2 insert size
  (M5 / S4 / S5).

Final check table: see `opravy2.md` §4 (filled from `checks.json`). Note: the F8 holes ended up as Ø4.1 to the insert end + radial-wedge exit (not through holes).

## Final state (2026-11-18 03:53 UTC)
`checks.py --force` (fix2_work/checks_run7.log, checks.json, STL stamp b738b2a51038ab5a): **K1–K13 all PASS**, module pre-checks RAM / PAN /
OBAL all ok. Run 2 additionally found and fixed: F10_B washer vs MG90S case (0.35 step), speaker-ring screw head vs the bench-bonded pan
pinion (low-head F13 screws, new K7 tip-circle row), mech-m1 residue (pocket plate bottom raised 0.15), F8 through-hole sliver (radial-wedge
exit). Check-suite corrections are listed in opravy2.md §3.
Open (UNVERIFIED, not covered by any check): ZIF Y5B / Molex 54548, USB-C FPC extension head, M2 × 4 × OD 4.0 insert drawing, low-head
M2 thread-forming screw, MG90S side load, topple impact force; bench tests listed in opravy2.md §5.
