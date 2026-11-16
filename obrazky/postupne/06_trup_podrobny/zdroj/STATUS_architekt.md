# STATUS – lead mechanical architect (T4 torso), 2026-11-16

## Delivered (all under /tmp/claude-0/gapwf/fin/T4/)
* `T4_spec.md` – specification (fit study, architecture, part list, interfaces, fasteners, assembly order, space
  reservation table, fits, notes for K1–K11, open points).
* `t4_common.py` – constants, exterior (numeric + CAD), cached BREP in `cache/`, helpers, envelopes, registry / export,
  self-test (`python t4_common.py`, log `cache/selftest.log`, numbers `cache/selftest.json`).
* `fit/fit2.py` → `fit/fit_report.json` (pack vs new shell, T4 envelopes vs shell / static parts / lip / tub / PAN_ENV),
  `fit/head_check.py` → `fit/head_check.json` (real head vs torso top), `fit/gen_tables.py` → `fit/spec_tables.md`,
  `fit/smoke.py`, `fit/smoke2.py` (boolean smoke tests on the cached blanks, logs next to them).

## What was actually run (and passed)
* Self-test: outer / inner(2.2) lofts, shell_white, stred_blank, bok_L/P_blank, cap_blank – valid single solids;
  outer loft vs analytic surface ≤ 0.006 mm (white) / 0.024 mm (cap); wall of the lofted shell 2.192…2.225;
  profile identical to T3 outside the rim zone (drop ≥ 2.6); spigot ↔ white lip gap 0.21…0.28.
* Fit study on ENVELOPES (boxes / cylinders, not final part geometry): results in T4_spec.md §1.4.
* Head check: VERTEX based (280 k head vertices vs a 0.16 mm surface cloud), pan −85…85 step 5, lifts 0 / 7.5 / 12.5 / 20,
  tilt in 5° steps inside the B table.
* Smoke booleans listed in T4_spec.md §4.1 (see fit/smoke.log, fit/smoke2.log for the door-ledge recipe).

## NOT done / NOT verified by me (do not treat as passed)
* No final part geometry exists yet – t4_obal.py / t4_ram.py / t4_pan.py, build_all.py, checks.py are the builders' /
  checkers' work. K1–K11 have NOT been run. In particular:
  - K9 (Blender BVH head check) not run; my vertex check gives 0.53 mm at lift 12.5 / tilt +30° (criterion 0.5).
  - K8 see-through from 26 viewpoints not evaluated (seam backing strips may be needed, spec §14).
  - K7: lowering of T_stred was checked as a 2-D lip-outline test of the tower envelopes plus hand calculation for the
    shell-mounted add-ons (door ledge, magnet pads, speaker, bosses); no 3-D path simulation.
  - K4: remaining wall at the front lip relief (≥ 1.5 estimated) and the 1.25 walls in T_klb are calculated, not measured.
  - K11 mass / CoG not computed (only shell_white 71.4 g).
* Bought-part dimensions are taken from pack.md / electronics_dims.md. STS3032 (tabs, hole pattern) and STS3215
  (boss diameter, plug zone) are listing values of medium confidence – seats are slotted ±0.3, verify on purchase.
* Details left to the builders inside their zones (described but not modelled): collar-tube ribs, crevice filling
  between tube and shell, door ledge / pads, seam tabs, T_ram bridges, bracket shape, FPC geometry, wiring.
* OCC `shape.volume` is unreliable on the thin loft shells (up to 4 % off) – use `t4_common.mesh_volume()`.

## Addendum (end of the session)
* `fit/smoke2.log`: `inner_solid(2.0 / 2.4 / 4.0)` build (8–9 s each, valid); door-ledge recipe of spec §4.3 gives one
  valid solid (parts 38 s each, fusing to the opened band 128 s).
* `fit/fit2.log` (final run): tower parts inside the T_stred boss prisms: none; all other minima as in spec §1.4.
* Files to read first: T4_spec.md, then t4_common.py section 1 (constants) and `envelopes()` / `PAN_ENV`.
