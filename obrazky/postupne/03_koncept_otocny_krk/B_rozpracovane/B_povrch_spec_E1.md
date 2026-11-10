# NOVA mini – variant B – EXTERIOR SURFACE SPEC (head + neck), rev. E1

World mm, Z up, front −Y, robot right −X. Head-local frame as head_common.py (bottom z=0, centre y=0, front y=−33).
HZ=27 extended / 7 rest, hinge axis AXZ=16.5, torso top z=4. Target look = referencie/R01_celok_zadanie.png.
Every function of round 5 stays (display fit, MG90S direct drive, MR85 + hollow pin, pan disc, 20 mm lift, dust-tight
neck, serviceability). Only the EXTERIOR and the display/visor stack change. Decision on the mechanism: KEEP B
(pop-up + tilt). It is fully engineered and checked; the ugliness is 100 % surfacing. (If the lift drive ever gets
dropped, the same neck fixed at mid-lift −10 needs no change to this spec except the collar height.)

## 0. Defects seen (renders closeB/01–08 + geometry)
D1  Visor stands 5 mm PROUD of the white rim (SH.VISOR_T) and is 1 mm SMALLER than the shell (VIS_IN) → a 1 mm step
    + a 5 mm grey side band around the whole face (01, 02, 07). R01 has black flush with white, one continuous round.
D2  Visor is smoked clear through its full 5.9 mm → the display seats, ribs, corner pads, inserts and the inner floor
    are visible as grey rectangles/triangles through the glass (01, 04, 05); double/ghost eyes (decal + reflection).
D3  Front rounding is elliptical 9 (depth) × 7.6 (x) but only × 4 (z): the top/bottom front edges look tight and
    pinched compared with the sides (01); R01 has equal soft radii all around.
D4  Ear = flat puck R13×6, 1.5 proud, sharp cylindrical edge, LED ring 0.35 proud with its own step; shell hole edge
    sharp (02, 03, 06). Reads as a washer, not a pod.
D5  Under the head at rest and at ±40°: black BLOCKY aprons (36 × 5 mm triangular fillers), lug web box 45 × 20 with
    chamfers, a visible apron/lug seam and the 0.1 apron–floor gap (05, 08); lug barrel + web read as blocks (05).
D6  Neck saddle land: planar 35° facet where the y=±10 face meets the R10.5 saddle under each lug → visible kink
    when extended (04, 07).
D7  Neck parting line y=0 runs over the knuckle top and down both narrow faces; halves meet with a raw butt → visible
    line + any 0.05 mismatch becomes a step (04).
D8  Hinge seam knuckle/lug 0.5 wide (KN 17.5 / LUG0 18.0) → dark ring that reads as a gap (04, 07).
D9  Blade corners R2 look boxy next to the R10 knuckle and the big head radii (04, 07). R01 neck has soft corners.
D10 Collar: disc + ring + torso show 2 concentric lines with unequal widths; slot edge sharp; the slot shows a dark
    rectangle around the neck (04, 07, 08).
D11 Shell/visor seam zone: white rim face 1 mm wide lit from the side → bright halo around the black face (01, 02).
D12 Render-only: eyes drawn as decals IN FRONT of the glass → must be LCD content behind the window (keep for
    visualisation but move them to the LCD plane).

## 1. Head body (white shell, hlava_skrupina) – form
1.1 Envelope unchanged: W108 × H77 × D66, softhead sections N=3.6, y −33..+33.
1.2 FRONT ROUND (softhead.factor, front zone R_FRONT=9): make the inset EQUAL in x and z: at the flat front (y=−33)
    a = 54−7.5 = 46.5 and b = 38.5−7.5 = 31.0 (flat front 93 × 62). Implement sec(y) in the front zone as
    a = W/2 − 7.5·(1−q), b = H/2 − 7.5·(1−q), q = sqrt(1−s²), s = (−24−y)/9. Back zone (R_BACK 30) unchanged.
    Result: elliptical round 9 deep × 7.5 inset, G1 to the flat front, G2 to the sides (q is a quarter ellipse).
1.3 Shell front face (Y_SEAM) moves from −28.0 to −26.0: the BLACK FRONT PIECE owns the whole front round
    (y −33..−26), the white starts where the round is 11° from flat (s=0.22). This is the R01 colour break.
1.4 All other white surfaces: no feature, no hole, no seam except: visor seam (§2), 2 ear pods (§3), bottom tenon
    slots (§4), which are hidden by the lugs. Print surface: sand P400→P1000, primer, 2K satin white (gloss 30–40 %).
1.5 Wall 2.5 nominal unchanged; inner loft start INNER_Y0 = −30.5 stays (it is now inside the visor pocket zone, cut
    away by the rabbet/front opening → check volume, no sliver thinner than 0.5 anywhere in front of y=−24).

## 2. Front piece (sklo → "celo", glossy black face) – flush, one piece, no visible fasteners
2.1 Outline = the SAME loft as the head (shrink 0) for y −33..−26.0 → step 0 (nominal) to the white shell. Tolerance
    goal ±0.05; if a step remains, black must be LOW, never proud (sand the flange face, not the shell).
2.2 Seam: V-shadow line 0.25 wide × 0.12 deep = chamfer 0.12 × 45° on the visor edge AND on the shell rim edge at
    y=−26. No other gap: visor flange face y=−26 bears directly on the shell rim face y=−26 (metal-to-metal style hard
    stop, 0 glue gap). Spigot sec(−26, shrink 1.6), length 0.9 (rabbet 1.0 deep, floor y=−25.0) → 0.1 axial
    clearance at the spigot end, 0.1 radial clearance in the rabbet (rabbet shrink 1.5).
2.3 Material: clear MSLA resin (water-clear type, e.g. Siraya Tech Blu Clear / Anycubic High Clear), printed front face
    up at 20–25° tilt, supports only on the back/pocket side; front sanded P1000→P3000, polished, then 2K UV-stable
    clear coat (gloss ≥ 85 GU). Thickness at the window 3.0 (see 2.5); elsewhere solid, may be cored from the back
    with walls ≥ 2.5 behind the mask (no cavity may reach within 2.5 of any exterior surface).
2.4 BLACK MASK: 2 × opaque black paint (satin/matt, 2K or acrylic) on EVERY non-exterior face of the piece: pocket
    floor outside the window, pocket walls, back face, spigot faces, the flange face y=−26 and its 0.12 chamfer
    (otherwise the clear edge light-pipes and shows a bright line at the seam). Window = display ACTIVE AREA
    73.44 × 48.96 + 0.3 per side → 74.0 × 49.6, R1.0, positioned on the module's real AA (measure; the AA is not
    centred on the 85.5 × 55.5 board). Window itself: light smoke tint 40–50 % T (tinted clear coat on the pocket
    floor, 1 coat) so the off display reads as black glass like R01; eyes remain clearly visible.
2.5 DISPLAY POCKET in the back of the piece (the module sits INSIDE the black piece, so no shell part can ever be seen
    through the glass): outline 86.4 × 56.4 R2.2 (LCD glass 86 × 56 + 0.2 per side), floor at y=−30.0 → glass 3.0 at
    the window, pocket depth 4.9 to the back face y=−25.1. Stack (y): pads −30.0..−29.8 | LCD −29.8..−26.8 |
    PCB gap 0.2 | PCB −26.6..−25.2 | back face −25.1 (PCB back 0.1 inside the pocket) | shell seats from −25.2
    to −19.2 (SEAT_T 6) | component keep-out 9.0 to −16.2. The 4 corner seats are clipped to the pocket outline −0.3.
    Pocket walls locate the LCD (0.2); the shell ribs now only locate the PCB (keep, FIT 0.25).
2.6 RETENTION (no visible fasteners, long-term preload, serviceable): 6 magnet pairs N35 Ø4 × 2 (≈3.5–4.5 N each
    at contact, ≥18 N total; no creep, no tape). Visor side: Ø4.2 × 2.1 pockets from the back face inside the
    spigot ring (ring is 8.2 wide there → ≥1.9 wall to the pocket, ≥2.1 to the spigot outline), epoxied, faces 0.05
    below the back face. Shell side: Ø4.2 × 2.1 pockets in Ø6.5 × 3.0 bosses hanging from the inner skin just behind
    the front opening, magnet face flush with the rabbet-floor plane y=−25.0 (like the display seats). Positions (head-local
    x, z): (±20, 70.7), (±20, 6.3), (±47.4, 38.5). Polarity marked on both parts before gluing. Display preload path:
    pads 0.3/0.4 compressed to 0.2 → ≤0.72 N (R5 numbers) against ≥18 N magnet hold → ratio 25:1.
    Removal for service: suction cup on the flat front, pull straight −Y (0.9 spigot slides out); no tools.
2.7 Dust/light seal: the 0.9 lap (spigot in rabbet) behind the 0.25 V-line; mask paint on the spigot → no light leak,
    no view inside from any angle.

## 3. Ear pods (usi + led_kruzky) – smooth domed buttons
3.1 Pod Ø26 (R13), axis x, centre (y −1, z 38.5 local) unchanged; shell through-hole R13.15 unchanged (seam 0.15 radial).
3.2 Shape outside the shell: cylinder R13 rising 1.5 above the local shell surface, then a spherical dome R38
    (sag 2.3 → centre 3.8 proud), blended by a fillet R1.5 (G1 cylinder→dome). Inside the shell: as now (6 mm body,
    lip/boss/groove, 4 light holes). Pod top edge nowhere sharper than R1.5.
3.3 Light ring r 8.6..10.5: FLUSH with the dome: its front face is the same sphere R38 (0 ± 0.05, never proud); it sits
    in the 1.65 groove with 0.1 radial seams; ring edges R0.2. Centre disc (r < 8.6) = same sphere → one continuous
    dome with a 1.9 wide cyan band. Pod black = satin (gloss 20 %); ring = clear/cyan, sanded matte on the front for
    even glow (no hot spots from the 4 LEDs).
3.4 Shell hole edge: round R0.8 on the white edge around the pod (G1 to the shell surface). The pod cylinder stands
    1.5 proud so the R0.8 never shows the hole wall.

## 4. Head underside – lug interface (usko_kryt, usko_lozisko), nothing blocky
4.1 DELETE the two aprons and their pegs (APEG, apron_pegs, apron head holes). They were cosmetic fillers and are
    exactly what looks like broken blocks (D5). The head is retained by the 4 cross screws as before.
4.2 Lug exterior (each side, |x| 17.8..22.5): barrel R10 concentric with the axis + a web |y| ≤ 8.0 rising from the
    barrel to the head floor; web→barrel blend = concave fillet R3 (removes the 37° kink at z AXZ+6); outer end face
    x=±22.5 flat with R2 rounds all around (barrel→face and web→face, G1); web top enters the floor slot (tenon,
    unchanged 4 × 16). Web = tenon width (±8.0) → the floor slot (±8.1) shows only a 0.1 black-on-black line.
4.3 Hinge seam knuckle/lug: 0.3 (KN 17.5, LUG0 17.8; LUG1 22.5). Lip ring / cap groove / sleeve / counterbore move
    with LUG0 (−0.2 in |x|); all hide the horn, MR85 and wires as before (re-run the seam ray-casts at 0°, ±40°).
4.4 Visible result: ONE black cylinder Ø20 × 45 (knuckle + 2 lugs) under the white head with two 0.3 hairlines, the
    two 4.7 × 16 black webs entering the head, and the blade below. No surface of the lug set may be planar except
    the two end faces x=±22.5.
4.5 Head floor around the slots: as now (soft superellipse bottom); the slot mouths get a 0.3 × 45° break so no white
    sliver chips. Cross-screw clearance holes stay inside the pads (never reach the exterior – verify).

## 5. Neck (krk_predna/zadna_polovica) – one clean black body
5.1 Blade 45 × 20, vertical corners R3.0 (was R2; interior unaffected: nearest void is the +X counterbore, wall 4.1).
    Knuckle R10, axis AXZ, |x| ≤ 17.5: tangent (G1) to both y=±10 faces by construction. Knuckle end faces flat.
5.2 Saddle under each lug (|x| 17.8..22.5 incl. the 0.3 seam zone from 17.5): concave R10.5 concentric for |y| ≤ 7.5,
    blended to the y=±10 faces by a CONVEX fillet R3 tangent to both (meets the face at z ≈ AXZ−5.6); replaces the
    planar 35° SADDLE_LAND. Wall to the internal voids ≥ 1.2 (same role the land had; re-check with the ray-cast rule).
    The blade's R3 vertical corner continues into this fillet (G1 corner blend, use a rolling-ball fillet).
5.3 Parting line stays at y=0 (only plane that clamps the servo symmetrically), executed as a V-shadow line 0.3 wide ×
    0.15 deep: chamfer 0.15 × 45° on BOTH halves along the whole exterior outline (sides, knuckle top, saddles).
    Halves are dowelled, assembled and sanded TOGETHER (P400→P800) before paint so the two surfaces are coplanar
    (≤0.03 mismatch), then painted separately. Dowel fit as R5 (press in the back half, slip in the front).
5.4 No other feature on the visible part (z ≥ 3.5 extended): screw counterbores (4), dowels, lead channel and the
    oblique head all stay below z 3.0 → inside the torso at full extension (R5 already satisfies this; keep the
    oblique head top at z ≤ 2.7).
5.5 Knuckle −X end: the static lip ring r 6.8..8.0 stays inside the cap groove; the only visible thing at the end is
    the 0.3 seam. +X end: sleeve OD 11.08 inside the counterbore r5.9; nothing shows.
5.6 Edges: bottom edge of the blade (hidden) chamfer 0.5; all exterior edges of the neck otherwise ≥ R3 or tangent.
    Finish: 2K satin black (gloss 20 %), same paint as lugs and collar so the three parts read as one.

## 6. Collar (golier_kotuc, golier_prstenec) and torso top
6.1 Disc R26.5, top flush with the torso top z=4.0 (±0.1); slot 45.5 × 20.5 with corners R3.25 (blade R3 + 0.25);
    slot edge round R0.6 (the neck slides through a soft edge; no dark sharp rectangle). Disc outer edge R0.3.
6.2 Ring: inner r 26.75 (0.25 running seam to the pan disc), outer r 28.25, top flush z=4.0, outer edge R0.3; glued
    seam ring→torso 0.1 (R3 had 0.25 → reduce: the torso recess r 28.35). Torso rim edge R1.0 (G1 to the dome).
6.3 Both parts same satin black as the neck. The 3 visible lines are therefore: 0.25 (disc/ring), 0.1 (ring/torso),
    and the slot clearance 0.25 around the neck – all ≤ 0.25, concentric, no steps.

## 7. Continuity, radii and seams – summary table
| surface / edge                              | requirement                                  |
|---------------------------------------------|----------------------------------------------|
| head shell ↔ front piece outer surface      | SAME loft, step 0, G2 across the seam         |
| front flat ↔ front round                    | G1 (q→0 slope), round 9 deep × 7.5 inset      |
| front round ↔ sides/top/bottom              | G2 (elliptical blend), ends at y=−24          |
| head back dome                              | unchanged (G1 to the back flat)               |
| visor/shell seam                            | V 0.25 w × 0.12 d at y=−26, on the 11° slope   |
| ear pod: cylinder ↔ dome                    | fillet R1.5 (G1); dome R38; ring flush ±0.05  |
| ear pod ↔ shell                             | seam 0.15; shell edge R0.8                     |
| lug web ↔ barrel                            | concave R3 (G1); end-face rounds R2 (G1)      |
| knuckle ↔ lug                               | seam 0.3, coaxial, zero radial step            |
| neck faces ↔ knuckle                        | tangent (G1) by construction                   |
| neck saddle ↔ faces                         | convex R3 (G1), no planar land                 |
| blade vertical corners                      | R3.0; collar slot R3.25                        |
| neck parting line                           | V 0.3 w × 0.15 d, mismatch ≤ 0.03              |
| collar slot edge / disc edge / torso rim    | R0.6 / R0.3 / R1.0                             |
| any exterior edge not listed                | ≥ R0.3 break; nothing sharp                    |

## 8. Colour / finish
White: 2K satin white, gloss 30–40 % (shell). Black satin, gloss 20 %: neck halves, lugs, pods, collar disc + ring.
Black GLOSS (clear part with black mask behind): front piece only, gloss ≥ 85 GU. Cyan: ring clear resin, matte
front. Visualisation: eyes as LCD content at y=−29.8 (not decals in front of the glass).

## 9. What the builder must verify after implementing (numbers)
V1 Mesh volume of every shell/visor loft (OCC GProp is wrong for the periodic lofts – use HC.mesh_volume).
V2 No resin wall < 1.2 anywhere (visor pocket walls ≥ 8 at the sides; window 3.0; mask zones irrelevant).
V3 Visor ↔ shell: max radial step along the seam ≤ 0.02 in CAD (same loft) – sample 72 points.
V4 Magnet pockets: ≥ 1.5 to any exterior or cavity surface; 6 pairs aligned ≤ 0.1.
V5 Lugs/webs ↔ neck and ↔ collar at tilt 0°, ±40° and lift 0..−20: clearance ≥ 0.25 (as R5), seams 0.3 uniform.
V6 Ray-cast from 24 viewpoints (eye height, ±60° azimuth, 3/4 above and from below at 20°) at rest and ±40°
    extended: no internal part (servo, horn, MR85, pin, screw, insert, wire, seat, rib) visible; no hole/slot visible.
V7 Display AA (74.0 × 49.6 window) fully inside the pocket floor; LCD glass 0.2 clear to the pocket walls.
V8 Pop-up rest pose (axis at z −3.5): head bottom z=7, knuckle/lug barrel top z=6.5, collar top 4 → the 3 mm black
    band under the head is the Ø20 cylinder + the two webs only; the blade saddle tops out at AXZ−5.6 = −9.1 (deep in
    the torso) and the parting V-line is below z 4 except on the knuckle top (over the cylinder, 0.3 wide) → verify
    that nothing else of the neck is above z 4 at rest and that the slot clearance 0.25 is uniform around the cylinder.
