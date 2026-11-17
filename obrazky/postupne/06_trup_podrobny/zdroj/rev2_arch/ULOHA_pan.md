# REV. 2 – task list for the PAN builder (t4_pan.py). Read T4_spec.md §17 first; numbers = t4_common.R2 (rev2 block).
0. Backup t4_pan.py and t4_pan_checks.py to rev2_backup/<name>.pan.bak. Import R2 / PAN_ENV2 / PAN_ENV2_SECTORS / envelopes_rev2
   from t4_common; do not edit t4_common above or inside the rev2 block (put your deviations in a block "additions by pan rev2"
   at the end + parts_pan.json["deviations"]). Export every part with t4_obal.export_abs (abs. deflection 0.01); masses from STL volume.
   Reuse cache/pan_*.brep where possible; never run one boolean > 5 min; keep internal faces 0.3–0.4 off loft faces.
1. DELETE parts: P_koleso, P_kluka, L_jazyk, fpc_pan, spoj_zdvih, kabel_zdvih, kolik_dorazu, kolik_kolesa_1/2, kolik_ucha,
   skr_kluky, skr_jazyka, the old single skr_F12, the FIN / APRON / FPC groove / Ø4.8 tool hole / glue groove / journal drum
   r 28.07 / lightening pockets of P_sachta.
2. P_sachta (resin, slim, group P): every surface r ≤ 26.50 (verify on the STL, report max r). Well inner 47.0 × 22.0 with
   inner vertical corners R2.5; end + front walls 1.6, back wall 2.0 (y 11.0…13.0, x −6…20); corners trimmed to r 26.50 full
   height. Wall lower edges z −40.90 for stage az 140…368, z −41.90 in az 5…140. Top plate z −3.50…−2.00 (flat glue land
   r 24…26.5 for golier_kotuc). Journal band r 26.37, z −10.00…−3.00, lead-in chamfer 0.5 at −10.0 (+ ptfe_pas_capu tape
   0.13 × 7 → r 26.50). Hub disc ring r 6.50…12.60 and back floor (stage az 5…140, out to the walls) at z −41.90…−40.65,
   R1 roots to the walls. Drum shroud r 15.50…16.70, stage az 8.0…140.0, z −45.60…−41.90, ends R0.6, retaining lip
   r 16.70…17.50 at z −42.50…−41.90 on the same sector (shroud hangs from the back floor). Back window x −20.9…−6.5,
   y 11.0…13.0, z −40.9…−10.9; end window (+X wall) y −6.5…6.5, z −40.9…−15.0. F10 pads on the back wall outer face:
   face y 15.10, boss r 3.5, R1.0 roots, at (19.5, −31.7) and (8.0, −14.5); bonded M2 insert holes Ø3.3 × 3.3 (+Ø2.3
   pilot 1.0); dowel hole Ø2.05 × 3.5 at (19.5, −27.7). FFC riser groove 0.3 deep × 3.4 wide on the outside of the back
   floor at stage az 14 (r 16.7…25.0) and a flat bonding land on the +X end wall outer face (y 0…3.4, z −41.0…−27.0).
   No closed pocket; state print orientation (top plate to the build plate, supports only on the inside / underside,
   never on the journal band or the drum) and vents.
3. koleso_pan (bought, group P, mat brass): plain 36T m0.8 involute gear, face 4.0, d 28.8, da 30.4, df 26.8, bore Ø8.00,
   z −45.90…−41.90, full 360° teeth, phased to mesh with pastorok_pan at PAN_AX (RAM models the pinion; agree the phase
   with the rev. 1 generator, backlash 0.04…0.08). Bonded under the hub disc (intended fit, no dowels).
4. Lift module (all removable through the door):
   a. servo_zdvih (MG90S) unchanged position (shaft ‖X at y 23.2, z −24.2; case x −6.5…16.0, y 17.1…29.3, z −41.1…−18.3;
      turret r 5.9 + lobe r 2.9 at z −29.8; upper tab x −2.5…0, z −18.3…−13.45, hole z −15.85; lower tab removed).
   b. P_drziak_serva (resin): turret end wall x −8.5…−6.5, y 15.1…29.3, z −41.9…−16.3 with the keyhole hole (r 6.05 about
      (y 23.2, z −24.2) + r 3.05 about (23.2, −29.8)); bottom-cover end wall x 16.0…18.0, y 15.1…26.5, z −41.9…−18.3 with a
      0.5 PORON pad (model as a part 'pena_zdvih'); back plate x −8.5…18.0, y 15.1…17.1, z −41.9…−13.0 with Ø2.3 holes at
      the 2 pads + Ø2.05 dowel hole; tab post x 0…8.0, y 17.1…26.2, z −18.0…−12.3 with a DIN 562 M2 slot (x 5.0…6.3, open
      to +Z) and Ø2.3 hole on the tab axis; stop lug r 27.60…31.60, stage az 118.3…131.7, z −47.20…−41.90 + bridge
      r 27.60…31.60, az 106.5…118.3, z −43.60…−39.90 merged with the turret end wall; roots R1.5 at the lug, R1.0
      elsewhere; NO floor under the case. Everything inside PAN_ENV2 + the lug sector. Report the lug root stress inputs.
   c. rameno_zdvih (bought Al arm, simplified): hub Ø7 × 3.0 (x −15.5…−12.5) + arm 2.0 thick (x −17.5…−15.5), 5 wide,
      to r 12.2, hole Ø2.0 at r 10.00 (pin at BDC y 23.2, z −34.2 at rest); cap_kluky Ø2 × 8 steel, x −20.4…−12.4. Keep
      mk_kluka(theta)-style pose function (crank angle θ, lift = 10(1 − cos θ)).
   d. L_ucho (metal, mat steel or Al – use 'steel' density for 304): plate x −19.9…−17.9, y 9.9…25.1, z −40.5…−31.9 with
      far top corner chamfer 1.5, slot 2.20 (z −35.30…−33.10) for y 11.6…24.3 with full round ends; flange x −19.9…−7.5,
      y 9.9…11.9, z −40.5…−36.5 with 2 × Ø2.3 holes at (−15.0, −38.5), (−9.0, −38.5); bend inner R 2.0 at the corner
      (x −19.9, y 9.9) – model the bend radius. Export also a DXF of the flat pattern (k-factor 0.4) to stl/L_ucho_rozvin.dxf
      for the drawing; if build123d cannot unfold, export the two flat faces with the bend allowance written in parts_pan.json.
   e. L_pata (Al flat bar, mat 'alu' – add density 2.70e-3 in your additions block): x ±22.3, y ±9.8, z −40.5…−36.5, vertical
      corners R0.8; Ø11.0 through hole at (0,0); slot x 9.0…22.3, y −7.4…6.4 (through, open at +X); 2 × M2 tapped holes
      along Y in the back face at (−15.0, −38.5) and (−9.0, −38.5): model Ø1.6 × 7.
   f. F12: 2 × ISO 7380 M2 × 6 + DIN 125 M2 along −Y (heads on the flange back face y 11.9). F10: 2 × M2 × 6 + DIN 125
      + bonded inserts (OD 3.2 × 3.0) + kolik_F10 Ø2 × 6. F11: M2 × 10 + DIN 125 + DIN 562 nut.
5. Cables: ffc_A / ffc_B (5 p, 3.0 × 0.10 each; model the stacked pair as ONE strip 3.0 × 0.25 'ffc_par' plus separate
   tails): static part from the deck slot (RAM provides the slot B az 26…34, r 22.4…23.6) along the static wall inner face
   r 23.5 from B az 30 → U-turn R 3.2 → inner run on the drum r 16.70 → rotating anchor stage az 14 → riser → fixed leg on
   the +X end wall (x 25.1, y 0…3, z −41.0…−27.0) → flat U R 3.0 in the x–z plane (outer leg x ≤ 31.3, envelope R2.FFC_LIFT2)
   → moving leg through the end window into the DPS_krk ZIF mouths (x 22.2, z −38.0…−37.0). z band of the pan loop
   −46.10…−43.10. Pose functions fpc_loop(pan) (U-turn at B az 84.0 + 0.415·pan) and fpc_lift(lift). Report the developed
   length per FFC (must fit 203 mm with the carrier run ≈ 40 mm) and the min bend radius per pose. pigtail_zdvih (3 × AWG30
   as a Ø1.4 tube, envelope R2.PIGTAIL) + Dupont 1 × 3 plug pair parked in the post clip.
6. DPS_krk (group L): FR4 13.0 × 13.4 × 0.8, x 9.2…22.2, y −6.9…6.5, top face z −37.00; 2 ZIF blocks FH19SC-5S (model
   5.4 × 3.0 × 1.0 each, y −6.4…−1.2 and 0.2…5.4, z −38.0…−37.0, mouth x 22.2); 10 solder-pad keep-outs on the top face.
7. PTFE: ptfe_pas_capu (journal), 4 guide strips as rev. 1 on the lands (keep the 0.17 neck float).
8. Checks (t4_pan_checks.py, new sections): (A) every P part r ≤ 26.50 and stage up through the glued ring (r_in 26.748)
   and the bore r 26.65 with neck / lift module / ear out and the lift-loop leg folded to r ≤ 26.3; (B) PAN_ENV2 incl. sectors
   over pan −90…90 × lift 0…20; (C) K3 vs RAM / OBAL rev. 2 STLs (≥ 1.0; declared: gear ↔ pinion flanks, gear ↔ PTFE
   0.0, boss ↔ gear bore 0.02, washer ↔ gear 0.10, foot ↔ hub disc 0.15, lug ↔ pins at ±90 (contact), shroud ↔ deck 0.6);
   (D) stop: lug faces meet the pins at pan −90.0 / +90.0 ± 0.3, engagement ≥ 2.5 incl. the 0.1 rise; (E) crank kinematics
   (stroke 20.00, dead centres, pin in slot 0.1 per side, ear ↔ arm side gap 0.4); (F) K7 rows: lift module out through
   the door with the ear off, neck up with DPS_krk through the disc slot (20.5 wide), FFC tails into the DPS_krk ZIFs at
   pan +85 (line of sight from the door ≥ 80 %), F12 / F10 / F11 tool paths (Ø4.5, ball-end allowed for F4 is RAM's);
   (G) resin rules K13 for P_sachta / P_drziak_serva: walls ≥ 2.0 except the declared 1.6 guide walls and 1.35 corners,
   roots R ≥ 1 (list), no closed pocket, print orientation + support faces + drain per part.
9. Write STATUS_rev2_pan.md (what was built / run / NOT verified) and parts_pan.json (with deviations).
