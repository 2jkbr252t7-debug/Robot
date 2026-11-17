# STATUS rev. 2 – lead mechanical architect (2026-11-17) – DONE (documents + constants; no CAD)
Delivered (all in /tmp/claude-0/gapwf/fin/T4/):
* T4_spec.md §17 (lines ~826–1330): decisions A1–A14, stack, pan drive (gears, fixing, drum, hard stop), slim stage, PAN_ENV2,
  J1 / merged T_spodok / deck / bridge, base interface, lift module (metal ear + Al foot), cables / ZIFs / DPS_krk / carrier,
  shells, part list, fastener / insert / drill / torque / washer tables, load paths L1–L8 with numbers, assembly + service
  order (every servo), zones / ownership, open items.
* t4_common.py block "rev2 (architect)" at the end: dict R2, PAN_ENV2 (+ PAN_ENV re-bound, PAN_ENV_REV1 kept),
  PAN_ENV2_SECTORS, aliases (R_BORE_JOURNAL, R_JOURNAL_R2, FOOT_GAP_R2, Z_*_R2, ...), envelopes_rev2(), rev2_check().
* rev2_arch/: a01_measure.py/.json (measurements on the rev. 1 / B STLs), s17_part*.md (source of §17),
  ULOHA_pan.md / ULOHA_ram.md / ULOHA_obal.md (builder task lists), t4_common_selftest.log.
* Backups: rev2_backup/T4_spec.md.architekt.bak, rev2_backup/t4_common.py.architekt.bak.
Run: rev2_check() numbers (see §17.14) and `python t4_common.py` (exit 0). Nothing else was run: no rev. 2 geometry exists.
NOT verified / open: §17.13 (bought-part numbers from search snippets – most vendor sites unreachable from this session:
rs-online.com, ameco.cz; STS3215 hole pattern; MG90S spline count; gear part numbers / bores; 5-pole FH12 / FH19SC stock;
MG90S side-load rating; lug root, T_cap root and column stresses need K12 FE).
