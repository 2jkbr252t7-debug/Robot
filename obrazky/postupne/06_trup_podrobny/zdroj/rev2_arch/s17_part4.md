
### 17.7 Shells and front (OBAL)
* **T_stred:** journal bore **r 26.65 for z −10.50…−2.00** (add the ring r 26.65…28.35 to the existing tube, then the
  shoulder face at z −2.00; ring seat r 28.35 for z −2.00…4.00 unchanged; tube outer r 30.6 unchanged → wall 3.95);
  lower edge chamfer 0.5 × 45°; bore tolerance r 26.65 +0.05/0 (sand to fit: the taped stage turns freely, no shake).
  Recipe: add `tube_z(28.40, 26.65, −10.50, −2.00)` overlapping the old bore face by 0.05 (never coincident), on the cached
  rev. 1 part; the extra resin is ≈ 2.9 g. F1 bosses r 3.2 → **3.4**, bonded M2.5 inserts (hole Ø3.6 × 4.3). Front-stack
  bosses unchanged (thread-forming, one-time). **Door top-seam tongue:** along the door-opening top edge for |x| ≤ 20.6
  (where the ledge is omitted) T_stred keeps the inner half of its wall (inset 1.1…2.2) 1.0 below the opening edge
  (tongue z −12.75…−11.75); the door loses the same volume (17.7 door) – the seam line of sight ends on the tongue,
  nothing enters PAN_ENV. Everything else of T_stred unchanged (approved exterior, seams, K8).
* **T_dvere:** delete both hook tabs and their roots (P07, S15); top edge: the outer half (inset 0…1.1) runs to z −12.00
  (seam 0.25), the inner half (inset 1.1…2.2) stops at z −13.00 (0.25 under the tongue) for |x| ≤ 20.6; ledge + 4 magnet
  pairs locate it (unchanged); finger notch 12 × 1.2 × 0.85 in the bottom edge (OBAL DOOR_NOTCH) + suction cup Ø30 to open.
* **T_bok_L / T_bok_P:** unchanged (one continuous seam lip, seat flange, notch r 14.0).
* **T_klb_L / T_klb_P:** neck **x 38.6…40.6** (−0.2, m18: the cap flange 39.1…40.6 is always clamped); R0.5 at the
  neck / body step (x 40.6) and at the body / end step (x 50.956), R1.0 where the 0.5 socket seam allows (m16); **F8 pattern
  az 60°, 180°, 300°** (counterbores Ø4.2 to x 45.0, clearance Ø2.3); **magnets az 0°, 120°, 240°**; key 2.9 × 1.4 at
  az 0°; bush bore Ø8.05 from the end face to x 44.0 + recess Ø10.2 to x 38.6 and the wire groove = **frozen arm
  interface** (P08; T_puzdro + disc springs deleted, arm round).
* **T_drziak_repro:** ring 1.6 → 2.0 thick, DIN 125 M2 washers under the 3 heads (m19). Front-bracket merge P10: **not done**
  (keeps two small prints; the merged part would need a thin strap across the light box – no screw saved).
* T_svetlovod, T_mriezka, T_drziak_led: unchanged (resin; T_svetlovod clear).

### 17.8 Part list rev. 2 (owner = module that models it)
| name | owner | grp | material | note |
|---|---|---|---|---|
| T_stred | obal | T | tough resin, painted white | bore step + shoulder, F1 r 3.4, door tongue |
| T_bok_L, T_bok_P | obal | T | tough resin, white | unchanged |
| T_dvere | obal | T | tough resin, white | hooks deleted, stepped top edge |
| T_klb_L, T_klb_P | obal | T | tough resin, black | neck −0.2, R0.5, F8 / magnets turned |
| T_svetlovod | obal | T | clear resin (standard allowed) | unchanged |
| T_mriezka, T_drziak_led | obal | T | tough resin | unchanged |
| T_drziak_repro | obal | T | tough resin | ring 2.0 |
| **T_spodok** | ram | T | tough resin, black | merged with T_ram (17.4) |
| T_paluba | ram | T | tough resin | deck lid 2.0, C-shape, FFC wall + slot |
| **T_cap** | ram | T | tough resin | pivot boss Ø7.70 × 4.40 (new) |
| **T_most** | ram | T | Al 5754-H22 / 6061-T6 sheet 2.0 (custom, hand cut) | pivot bridge 18 × 36, tapped M3 (new) |
| Z_naboj_test | ram | Z | tough resin | bench stand; sun-gear stub to the new plane −90…−86; stop block az 270 ± 19.0 |
| P_sachta | pan | P | tough resin, black | slim (17.3) |
| P_drziak_serva | pan | P | tough resin | pocket + stop lug (17.5) |
| **L_pata** | pan | L | Al flat bar 20 × 4 (custom, hand cut) | was resin |
| **L_ucho** | pan | L | 304 stainless 1.5 (preferred) or 6061-T6 2.0 (custom, bent) | was POM |
| koleso_pan | pan | P | bought: brass 36T m0.8 face 4 bore 8 H7 | was printed P_koleso |
| pastorok_pan | ram | T | bought: steel / brass 18T m0.8 bore 5 | Loctite 638 on the spline |
| pastorok_J1 | ram | T | bought: brass 18T m1 bore 6 | Loctite 638 on the spline |
| rameno_zdvih | pan | P | bought: Al servo arm for the MG90S | replaces P_kluka |
| cap_kluky | pan | P | steel dowel ISO 8734 2 m6 × 8 | pressed + 638 in the arm |
| koliky_dorazu (2) | ram | T | steel dowel ISO 8734 3 m6 × 12 | bonded in T_spodok posts |
| kolik_F10 | pan | P | steel dowel ISO 8734 2 m6 × 6 | bonded in the pad |
| ffc_A, ffc_B | pan | P/L | 0.5 mm 5 p 203 mm Type A FFC | replaces fpc_pan |
| DPS_krk | pan | L | FR4 0.8 + 2 × FH19SC-5S-0.5SH | new |
| pigtail_zdvih | pan | L | 3 × AWG30 + Dupont 1 × 3 | new |
| DPS_riadenie | ram | T | carrier (17.6) | new layout |
| servo_J1, servo_pan, servo_zdvih, menic, zosilnovac, kondenzator, reproduktor, DPS_led, magnets, 6805 | as rev. 1 | | | positions per 17.2 / 17.4 / 17.6 |
| ptfe_podlozka | ram | T | PTFE 24 × 10 × 0.3 | ID 12.4 → 10.0 |
| ptfe_pas_capu, ptfe_cap | pan / ram | | PTFE tape 0.13 | journal band 7 × 167; boss wrap 4.4 × 25 |
| podlozky_J1 | ram | T | PET 0.1 strips 4 × 30 (2–6) | J1 top shim + C shims |
| **deleted** | – | – | – | T_ram (merged), T_prichytka_fpc, T_puzdro_L/P, P_koleso, P_kluka, L_jazyk, fpc_pan, spoj_zdvih, cap_pan, kolik_dorazu (old), koliky_kolesa, kolik_ucha, F2, F5, F6, F9, skr_fpc, skr_jazyka, skr_kluky, disc springs, all heat-set inserts |

### 17.9 Fasteners, inserts, drill, torque (S03, Z3.4–Z3.6)
**Screws (all ISO 7380-1 button head, steel 10.9 / A2 – M2 / M2.5 sizes are catalogue nominal, UNVERIFIED: M2 dk 3.5 k 1.3,
M2.5 dk 4.7 k 1.375, M3 dk 5.7 k 1.65).**
| # | joint | qty | screw | washer | into | direction / position |
|---|---|---|---|---|---|---|
| F1 | T_spodok → T_stred | 4 | M2.5 × 8 | DIN 125 M2.5 | bonded M2.5 insert, T_stred boss r 3.4 | +Z from below at (±29.0, ±19.0); Ø3.2 holes (float, M11), counterbore Ø6.5 × 1.9 in the pad |
| F3a | T_paluba → T_spodok | 4 | M2.5 × 6 | DIN 125 M2.5 | bonded M2.5 insert, boss r 3.4 | −Z at (20.0, ±13.8), (−33.5, ±10.0) |
| F3b | T_most → T_spodok | 2 | M2.5 × 6 | DIN 125 M2.5 | bonded M2.5 insert, boss r 3.4 | −Z at (6.0, ±15.95) |
| F4 | pan servo tabs | 2 | M2 × 10 | DIN 125 M2 | DIN 562 M2 nut in the post | −Z at (±14.0, −20.79), slotted ±0.3 |
| F7 | carrier | 2 | M2 × 6 | DIN 125 M2 | bonded M2 insert, boss r 3.25 | −Y (door) at (±19.0, z −62.5) |
| F8 | T_klb → column | 3 + 3 | M2 × 10 | DIN 125 M2 | bonded M2 insert, column boss | ∓X, r 7.5 at az 60/180/300 |
| F10 | lift module → well | 2 + dowel | M2 × 6 | DIN 125 M2 | bonded M2 insert, pad r 3.5 | −Y at (19.5, −31.7), (8.0, −14.5); dowel at (19.5, −27.7) |
| F11 | MG90S upper tab | 1 | M2 × 10 | DIN 125 M2 | DIN 562 M2 nut in the post | +X at (y 23.2, z −15.85) |
| F12 | ear → foot | 2 | M2 × 6 | DIN 125 M2 | tapped M2 in the Al foot (metal) | −Y at (−15.0, −38.5), (−9.0, −38.5) |
| F13 | LED holder, speaker ring | 2 + 3 | M2 × 6 thread-forming for plastics (e.g. EJOT PT K20 class, one-time) | DIN 125 M2 | pilot Ø1.7, boss Ø5, engagement ≥ 4 | as rev. 1 |
| F14 | buck, amplifier | 2 + 2 | M2 × 6 thread-forming, one-time | DIN 125 M2 | pilot Ø1.7, boss Ø5 × 1.5 standoff + web | ±X |
| F15 | pivot | 1 | **M3 × 6** | DIN 9021 M3 (Ø9 × 0.8) | tapped M3 in T_most (metal) | −Z on the axis, through T_cap |
| F16 | J1 servo | 4 | M2 × 6 (thread of the servo case UNVERIFIED) | DIN 125 M2 | servo case holes | +Z from below through the pads |
Kinds: M2 × 6, M2 × 10, M2.5 × 6, M2.5 × 8, M3 × 6 + one thread-forming M2 × 6. No countersunk head anywhere in resin, no
heat-set insert, no thread cut in resin that is opened in service.
**Inserts / nuts:** brass knurled inserts bonded with epoxy – M2: OD 3.2 × 3.0, hole Ø3.3 × 3.3 (+ Ø2.3 pilot 1.0), boss
r ≥ 3.25; M2.5: OD 3.5 × 4.0, hole Ø3.6 × 4.3 (+ Ø2.8 pilot 1.0), boss r ≥ 3.4; engagement ≥ 3.0. Square nuts DIN 562 M2
(4.0 × 4.0 × 1.2): slot 4.1 × 1.35, ≥ 1.5 resin to every free edge.
**Drill / ream after curing** (sharp HSS, low speed, pecking; holes are modelled at FINAL size): Ø1.6 M2 tap drill (Al
foot); Ø1.7 thread-forming pilots; Ø2.0 crank-pin hole in the Al arm (metal press); Ø2.05 F10 dowel; Ø2.3 M2 clearance;
Ø2.4 F16 (file the ±0.3 slot); Ø2.5 M3 tap drill (T_most); Ø2.8 M2.5 clearance; Ø3.05–3.10 stop pins (6.0 deep); Ø3.2
F1 float holes; Ø3.3 / Ø3.6 inserts; Ø3.4 T_cap; Ø5.1 / Ø3.1 magnets; Ø11.0 Al foot (step drill); 8.00 H7 36T gear bore
only if bought smaller (lathe); 26.65 bore / 26.50 journal / 7.96 boss: sand to fit with the PTFE tape; Ø37.15 6805
seat: sand to a slide fit, then epoxy.
**Torque (L7, S03):** M2 into a bonded insert ≤ 0.05 N·m; M2.5 into a bonded insert ≤ 0.09 N·m; M2 into a DIN 562 nut with
the head on resin ≤ 0.05 N·m; M2 thread-forming one-time: seat + 1/8 turn (≤ 0.04 N·m); M2 metal–metal (F12) 0.15 N·m
+ Loctite 222; M3 into T_most through T_cap (F15) ≤ 0.12 N·m + Loctite 222 (T_cap compression ≤ 5 MPa); F16 ≤ 0.05 N·m.
Retaining compound Loctite 638 (or equivalent) only metal–metal: both pinions on their splines, crank pin in the arm.
**Washers:** DIN 125 M2 (2.2 × 5 × 0.3) × 26; DIN 125 M2.5 (2.7 × 6 × 0.5) × 10; DIN 9021 M3 (3.2 × 9 × 0.8) × 1; PET
shim 0.1 strips; PTFE 24 × 10 × 0.3 thrust washer.
