# T4 addendum Z – resin-only printing, strength, simplicity (user requirement of 2026-11-17, binding)

The user (Slovak hobby builder), in their words: *"I will print it on a resin 3D printer, so it must be strong and must not
break; you have to pay attention to the hardness of the resin / material, function etc.; as little complicated as possible but
fully functional."* Earlier (2026-11-05): *"I can only print from resin."*

This overrides the brief (§4 "Chassis: PETG FDM" was the lead's mistake) and every "PETG / POM" entry in T4_spec.md.

## Z0. The user's printer (stated 2026-11-17)
Elegoo Saturn 4 Ultra (user wrote "Saturn 4k ultra"): 10" mono LCD MSLA. Build volume of the 12K version 218.88 x 122.88 x 220 mm
(XY pixel about 19 x 24 um); if it is the 16K version, 211.68 x 118.37 x 220 mm (14 x 19 um). Design to the SMALLER volume
(211 x 118 x 220) so either fits. Tilting vat release. Fine detail is not the limit - strength, warp and support marks are.
Resin advice must name resins that work on this printer (405 nm MSLA, standard vat), e.g. Elegoo ABS-Like 3.0, Siraya Tech
Blu / Tenacious blends, Anycubic ABS-Like Pro 2, Phrozen Aqua-Gray 8K / TR250LV class - verify datasheet numbers before quoting.

## Z1. Everything printed is MSLA resin
* No FDM / PETG part and no machined POM part. Currently wrong in parts.json: T_ram, T_paluba, T_prichytka_fpc,
  T_drziak_repro, P_drziak_serva, L_pata, L_jazyk, Z_naboj_test (petg) and T_puzdro_L/P, L_ucho (pom).
* Nothing may rely on FDM / thermoplastic behaviour: no heat-set inserts, no flexing snap hooks, no living hinges, no
  press fits that need a yielding plastic, no FDM overhang rules (resin prints any overhang on supports – but supports leave
  marks, so keep them off visible and fit faces).
* Bought standard parts (screws, brass inserts, pins, bearings, gears, magnets, servo horns) are fine and preferred wherever
  a printed resin feature would be the weak point.

## Z2. Material
* Design for ONE structural resin class: tough "ABS-like" engineering resin (not standard / water-washable resin, which is
  glass-brittle). Properties to design with (conservative, cured): tensile strength 35 MPa, flexural strength 50 MPa,
  E ≈ 1.8 GPa, elongation at break ≥ 15 %, HDT ≈ 55–60 °C, Shore D ≈ 80. Allowable working stress: 12 MPa static (safety
  factor 3 on tensile), 6 MPa for sustained load (creep) and for features with a notch that cannot be filleted.
* The documents must tell the user the required PROPERTIES (so any brand can be checked against its datasheet), give 2–4
  example products, and say which parts may use ordinary white resin if they want (none that carries a screw, tab or pin).
  Visible parts are painted (as on the finished head: 2K satin white / black), so resin colour is not a constraint except the
  clear light guide. Simplest plan to recommend: one tough resin for every part + paint.
* Post-processing rules belong to the documents: wash, cure per datasheet (over-curing embrittles), drill / ream fit holes
  after curing, epoxy for inserts / pins / bearings / magnets (as in B/montaz.txt), keep parts out of sunlight.

## Z3. Design rules for resin (brittle, notch-sensitive, creeps under sustained load, wears, softens at ~55 °C)
1. Walls: structural ≥ 2.0 (columns, brackets, bosses, pads ≥ 2.5 where space allows); ribs ≥ 1.5; local skin ≥ 1.2.
   A feature thinner than 1.2 is allowed only if it carries no load AND is not handled during assembly.
2. Nothing flexes: no hook / tab / clip that must bend in assembly or service. Cantilever tabs that carry load: root
   thickness ≥ 2.0 and length ≤ 2 × thickness, or replace by magnets / pins / screws.
3. Fillet every inside corner of a loaded feature: R ≥ 1.0 (≥ 0.5 where space forbids – then say where). Sharp inside
   corners at column / boss / pad / tab / ear / crank roots are defects.
4. Threads: (a) joints opened in service → brass knurled insert BONDED with epoxy (hole = OD + 0.1, wall around the
   insert ≥ 1.6, engagement ≥ 3.0); (b) one-time small joints (PCB mounts, clamps) → thread-forming screw for plastics,
   pilot Ø = d − 0.35 (M2: 1.65–1.7), boss OD ≥ 2.5 d, engagement ≥ 2 d, ≥ 1.5 material to any free edge; (c) captive nut
   if that is simpler. No screw may be driven into a boss thinner than that.
5. Screw heads on resin: countersunk heads wedge and split thin resin – allowed only with ≥ 1.5 material under and
   around the cone and a hard stop; otherwise pan / button head in a flat counterbore (or washer).
6. No interference fits: pins, bearings, magnets, bushes are slide fits (+0.05…0.10) bonded with epoxy; fit holes are
   drilled / reamed to size after printing (state the drill size). A pin that must rotate runs in a bought metal sleeve or
   has a declared wear allowance.
7. Sustained preload relaxes in resin: springs and clamped stacks need steel washers on both faces and positive location
   (keys, shoulders, pins) – never rely on friction of clamped resin for position or torque.
8. Sliding: resin on resin only with PTFE tape / grease and low pressure; steel pin in a resin slot needs a contact
   pressure check (≤ 5 MPa projected) or a liner.
9. Printed gear teeth: check the tooth-root stress (Lewis) at SERVO STALL and at manual abuse (someone turns the head /
   torso by hand) with the resin allowable. If it fails: wider face, bigger module, bought gear (brass / POM) bonded to a
   printed hub, a torque limit that is real (slip element; firmware limits do not protect against a hand), or stops that
   take the load instead of the teeth. Never print servo splines: use the horn supplied with the servo, screwed into a
   printed pocket.
10. Heat: ≥ 1 mm air or a vent path around the buck converter and the servo cases; no loaded thin resin feature touching
    them.
11. Print strategy per part: orientation, where supports go (never on visible or fit faces), drain / vent holes, no
    suction cups, no islands, hole compensation (+0.10…0.15 on Ø), expected warp of thin large shells and how the design
    tolerates it (locating lips, screws pulling the part into shape).
12. Robustness against print tolerance (± 0.15 typical): running clearances between moving and static parts ≥ 1.0 nominal
    are fine, but a clearance of exactly 1.000 with zero margin on several parts is fragile – prefer ≥ 1.3 where it costs
    nothing; fits that only work within ± 0.05 need an adjustment (shim, slot, file-to-fit instruction).

## Z4. Load cases every loaded feature must survive (with numbers, safety factor ≥ 2 on the Z2 allowables for abuse cases)
* L1 robot lifted by the head: 15 N pull up (≈ 1 kg robot × 1.5) through head → neck → lift mechanism → pan stage →
  torso → J1 bearing → base. What takes the axial load at each interface?
* L2 head pushed down / leaned on: 30 N down on the head at any lift position (0, mid, 20).
* L3 head turned by hand against the pan servo: 0.6 N·m about the pan axis (and into the ± 90° hard stops).
* L4 torso turned by hand: the J1 slip clutch must slip (≈ 0.25 N·m) before anything is overloaded; hard stops ± 155°.
* L5 arm load: 10 N at the arm tip (72 mm from the shoulder axis) in any direction, and arm forced by hand against its
  servo (friction collar ≈ 0.25 N·m must slip first); robot lifted by one arm (15 N).
* L6 knock / topple from standing height onto a desk: side cap, shoulder joint, door (must stay on or pop off undamaged).
* L7 assembly loads: screw tightening torque (M2: 0.15 N·m, M2.5: 0.3 N·m), pressing the bearing, pulling the door 100×.
* L8 servo stall: STS3215 (J1) 1.9 N·m class (datasheet!), STS3032 (pan) and MG90S (lift) at their stall torque.

## Z5. Simplicity ("as little complicated as possible but fully functional")
For every printed part, fastener group, special bought part and assembly step ask: can it be removed, merged with its
neighbour or replaced by a simpler standard solution WITHOUT losing a function the user asked for (J1 torso rotation
± 150°, head pan ± 80°, neck lift 20 mm, head tilt, 2 arms later, light bar, speaker), the approved exterior, or
the ability to replace a servo? Resin has no FDM constraints, so parts that were split only for FDM printing can merge.
Prefer: fewer printed parts, few screw types (M2 and M2.5, one or two lengths each), off-the-shelf parts over custom ones
(the two CUSTOM FPCs are the hardest items for a hobby builder to obtain – is there an off-the-shelf alternative that still
works?), adjustments by shim / slot instead of tight tolerances, assembly without special jigs.
Not negotiable: exterior shape and visible seams (approved), head + neck parts (finished), the function list above.
