# REV. 2 – task list for the OBAL builder (t4_obal.py). Read T4_spec.md §17 first; numbers = t4_common.R2 (rev2 block).
0. Backup t4_obal.py and checks_obal.py to rev2_backup/<name>.obal.bak. Work on the cached rev. 1 BREPs (cache/obal_v1_*);
   only small planar / cylindrical booleans; keep faces 0.3–0.4 off loft faces; never one boolean > 5 min; check volume
   (mesh_volume) and is_valid after each step; export with export_abs. Deviations: block "additions by obal rev2" at the
   end of t4_common + parts_obal.json["deviations"].
1. T_stred: add tube_z(28.40, 26.65, −10.50, −2.00) (overlaps the old bore by 0.05 – never coincident) → journal bore
   r 26.65 for z −10.50…−2.00 + shoulder face at z −2.00; ring seat r 28.35 for z −2.00…4.00 untouched; 0.5 × 45° lead-in
   chamfer at the bore bottom (z −10.5). F1 bosses r 3.2 → 3.4 (z −81…−75, webs to the wall as rev. 1), insert holes
   Ø3.6 × 4.3 + Ø2.8 pilot (bonded M2.5 OD 3.5 × 4.0; replace vlozka_stred_* solids). Door top-seam tongue: for
   |x| ≤ 20.6 keep the wall between inset 1.1 and 2.2 from the opening top edge (z −11.75) down to z −12.75 (cut it out of
   the door instead); verify it stays inside inset 2.2 everywhere. Nothing else of the exterior changes.
2. T_dvere: delete both hook tabs + roots; top edge stepped for |x| ≤ 20.6: outer half (inset 0…1.1) to z −12.00, inner half
   (inset 1.1…2.2) to z −13.00 (0.25 under the tongue); keep ledge contact, 4 magnet bosses, finger notch 12 × 1.2 × 0.85;
   print orientation: inner face to the plate is NOT allowed if supports would touch the outer face – state it.
3. T_klb_L / T_klb_P: neck x ±(38.6…40.6) (was 38.4…40.6); R0.5 at the neck / body step (x 40.6) and at the body / end step
   (x 50.956), R1.0 where the 0.5 socket seam allows; F8 counterbores (Ø4.2 to |x| 45.0) + Ø2.3 clearance at r 7.5,
   az 60/180/300; magnet pockets Ø3.1 × 2.1 at r 7.5, az 0/120/240; key 2.9 × 1.4 at az 0 (unchanged); bush bore Ø8.05
   (end face → |x| 44.0) + recess Ø10.2 (→ |x| 38.6) + wire groove = frozen arm interface. Delete T_puzdro_L/P and the
   disc-spring parts (pruziny_klb_*).
4. T_drziak_repro ring 1.6 → 2.0 (OBAL SPK_RING t), DIN 125 M2 washers under the 3 heads (model them). T_bok, T_svetlovod,
   T_mriezka, T_drziak_led unchanged (re-export only if their inputs changed).
5. Checks (checks_obal.py): K8 exterior fidelity + seams + see-through from the 26 viewpoints WITHOUT the door hooks
   (the tongue must close the door top seam; report any ray that passes the seam ends x ±33.3 near the spigot – RAM's
   spigot has no notch within |x| 31.0…35.6); bore r 26.65 ± 0.01 on the STL for z −10.4…−2.1; tube wall ≥ 3.9; F1 insert
   walls ≥ 1.6; T_klb step radii measured; K10 / K13 table per part (orientation by "which face to the build plate",
   support faces, drains ≥ Ø2.5). Write STATUS_rev2_obal.md and parts_obal.json.
