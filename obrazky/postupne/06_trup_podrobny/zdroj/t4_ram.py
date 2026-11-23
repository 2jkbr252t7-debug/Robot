#!/opt/venv/cad/bin/python
"""NOVA mini - T4 torso REV. 2, module RAM: merged chassis (T_spodok), deck lid, pivot bridge + boss, J1 drive,
pan-servo seat, electronics carrier, stop pins, dummy base hub.   (rev. 1 backup: rev2_backup/t4_ram.py.ram.bak)

    /opt/venv/cad/bin/python t4_ram.py            build (printed parts cached by source hash), export, parts_ram.json
    /opt/venv/cad/bin/python t4_ram.py --rebuild  ignore the cache
    /opt/venv/cad/bin/python t4_ram.py --noexport build + table only

Frame: B frame, mm, Z up, FRONT = -Y, rest pose, torso top z 4.  Numbers: t4_common.R2 (rev. 2, architect) and the
block "additions by ram rev2" below (module-local; deviations from T4_spec.md section 17 with their reasons).
Registry: build() -> dict[name] = t4_common.part(shape, group, mat, printed, label_sk, ...)
Everything printed is ONE tough resin (Elegoo Tough, T4_zivica Z0/Z2): T_spodok, T_paluba, T_cap, Z_naboj_test.
Metal custom part: T_most (aluminium 2.0 sheet).  Everything else is bought (datasheet solids, sources in SOURCES).
"""
from __future__ import annotations
import os, sys, math, time, json, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import numpy as np                                    # noqa: E402
import t4_common as C                                 # noqa: E402
import build123d as bd                                # noqa: E402
from build123d import Vector                          # noqa: E402

C.DENS.setdefault("alu", 2.70e-3)                     # aluminium 5754 / 6061 (T_most); integrator: add to DENS
R2 = C.R2
R3 = C.R3                                             # rev3 (sachta): pivot stack, T_cap root R1.0 / hole D3.1, pan pinion face 3.0
ZF, ZB = C.Z_FLOOR, C.Z_BOT                           # -82.3 floor top, -84.5 cap underside
ZD0, ZD1 = R2["STACK"]["deck"]                        # -48.2 / -46.2  deck (and T_most) plate
CR = R2["CRADLE"]
YI, YO = CR["y_in"], CR["y_out"]                      # 12.55 / 15.05
X0, X1 = CR["x"]                                      # -32.2 / 25.8
XE = CR["end_wall_x"][1]                              # -29.7 inner face of the -X end wall
SHY, SHZ = C.SH_Y, C.SH_Z                             # shoulder axis (y 3, z -17)
J1X, J1Y = C.J1_AX
PAX = R2["GEAR_PAN"]["ax"]
S15, S32 = C.STS3215, C.STS3032
TIMES = {}
ROOTS = []        # loaded inside corners that carry a fillet: dict(part, name, p (edge point), u (bisector), R)

# =====================================================================================================================
# >>> additions by ram rev2   (module-local numbers; nothing of t4_common.py was edited - integrator: copy if needed)
# =====================================================================================================================
RAM2 = dict(
    # ---- J1 support (S10, air option) --------------------------------------------------------------------------------
    J1_POCKET=dict(x=(XE, 16.7), y=(-YI, YI), z=(-83.3, ZF)),          # clearance pocket of the case in the floor
    J1_PADS=dict(x=((-29.7, -24.5), (10.7, 16.7)), y=(7.35, YI), top=-83.3),   # 4 corner pads = floor remnants
    J1_WINDOW=dict(x=(XE, 16.7), y=(-12.45, 12.45)),                  # through the floor except the pads (air 1.2)
    F16=dict(at=[(-27.0, 9.85), (-27.0, -9.85)], hole_d=2.4, slot=0.3, screw="ISO 7380 M2x6 + DIN 125 M2"),
    #   only the 2 -X pads carry F16: the +X pads lie over the plinth ring / 6805 seat (r 13..20) - no tool path once the
    #   bearing is bonded.  The +X end is located by the bumper + PORON and clamped from above (T_most / deck / shims).
    BUMPER=dict(x=(16.7, 18.3), y=(-4.0, 4.0), z=(-83.3, -70.0)), PORON_END=dict(x=(15.7, 16.7), y=(-4.0, 4.0), z=(-80.0, -71.0)),
    FRONT_RECESS=dict(x=(-12.05, 12.05), y_face=-14.243, z=(-73.0, ZD0), tab_x=16.55, tab_z=(-56.8, -53.7)),
    #   front cradle wall 1.69 between the servos (+ over the tab ends x +-16.55, z -56.8..-53.7)
    J1_LUG=dict(r=(18.65, 21.0), w=8.0, z=(-102.0, -98.0), az=90.0, root_r=1.0),
    #   fixer rev2 (overenie2 m4): tangential 5.0 -> 8.0 so the lug survives a realistic hand twist of the torso into the stop
    #   (1.5 N.m: 11.2 MPa incl. Kt 1.4 <= 12.9); the base stop block half-span shrinks 19.0 -> 14.6 deg (R2 J1 base_stop) so the
    #   stop angle stays +-153.4.  The "D3 steel pin at r 19" alternative of 17.4 does not fit (the 6805 seat is r 18.575).
    #   r 18.65..21.0 (spec 17.0..21.0): inside r 18.575 the lug would block the 6805, which goes in from below; not beyond
    #   the foot ring r 21 (the base FFC wraps on it at z -98..-91).  Tangential 5.0 (spec 4.0) restores the root section.
    SEAT_R=R2["SEAT_6805_D"] / 2,                                       # 18.575
    BASE_FFC_SLOT=dict(r=(21.1, 22.4), az=(74.5, 105.5), z=(-91.0, ZF)),
    #   annular sector (spec flat x -6..6, y 21.2..22.5 -> plinth skin 0.71 at x +-6): skin 1.6 everywhere, 0.1 off the foot ring
    #   r 21; arc 11.8 at r 21.75 for the 11.0 FFC (sagitta of the 11 chord 0.70 < 1.3 - 0.1)
    F1=dict(at=C.SCR_STRED, pad_r=R2["F1_BOSS_R"], hole_d=3.2, cb_d=6.5, cb_z=ZB + 1.9, screw="ISO 7380 M2.5x6 + DIN 125 M2.5",
            keepout=dict(x=(25.1, 32.9), y_min=15.1), keepout_z=(C.Z_WHITE, 0.0)),
    #   integrator rev2: the keep-out prism is cut from the tower over its FULL height (was z < -74.5): T_stred is lowered
    #   straight down at T5 and its 4 boss columns pass through x +-(25.6..32.4), |y| >= 15.6 at every z
    #   keep-out / spigot notch = OBAL F1 zone (x +-(25.6..32.4), |y| >= 15.6, z -81..-75) + 0.5: 7.8 wide (the boss webs of
    #   T_stred reach beyond a r 3.9 cylinder); the notch ends at |x| 32.9 (spec "none within 31.0..35.6" cannot hold: the
    #   boss itself reaches |x| 32.4) - the seam band edge |x| 33.05 is still backed by the spigot
    # ---- columns ---------------------------------------------------------------------------------------------------------
    COL=dict(web=R2["COLUMN"]["web_x"], y=R2["COLUMN"]["y"], ribs=R2["COLUMN"]["ribs_y"], rib_x=42.0, rib_top=-30.4,
             box_x=(40.0, 42.0), box_z=(-51.0, -34.0), foot_x=(33.0, 37.6), boss_r=C.R_COL_STOP[0], flange_r=C.R_COL_STOP[1],
             flange_x=(37.4, C.X_COL_STOP), wire_hole=dict(d=4.5, y=-2.0, z=-51.0),
             #   fixer rev2 (S1): wire hole y 11.7 -> -2.0 (was 0.85 under the sharp bridge-top corner; now 12.3 from it, clear of
             #   the F3a corbel at y >= 1.6 and under the deck bottom -48.2 by 0.55); the wire goes up the open bay into the box
             bridge_fillet=1.5, head_cove=1.0,
             head=dict(z=(-38.0, -27.5), y=(-14.0, 17.0), xy_out=[(43.0, -14.0), (43.0, 12.0), (42.3, 16.0), (41.8, 17.0)],
                       x_cut=38.4, r_cut=17.1, chan=dict(x=(38.4, 40.0), y=(5.0, 12.0), z=(-40.0, -27.0)),
                       plate=dict(x_out=38.4, x_in_min=26.0, r_in=34.4, flat_y=None, y=(-17.0, 17.0), z=(-38.0, -8.0), top_y=14.0,
                                  wide=dict(y=20.0, z=(-38.0, -20.0), z_back=-16.0),
                                  top_z_end=-12.0))),
    #   + shoulder PLATE x (r 34.4)..38.4, y -20..24, z -38..-8 (45 deg run-outs into the head): around the shoulder axis the column
    #   depth in x is fixed at 4.0 (PAN_ENV2 + 1.0 inside, the T_klb neck face 38.6 outside), so the L5 moment about y needs width
    #   in y: Zw = w t^2 / 6 -> w >= 46 for 8.5 MPa (Kt 1.3) at the axis level
    #   integrator rev2: column HEAD z -38..-27.5 (L5 fix): rev. 2 had only the 3.0 web between the rib tops (-30) and the boss
    #   (-28.6) - Zw 33 mm3 at z -30 (33 MPa under L5; RAM checked z -32 only).  The head thickens the web to x 38.4 (T_klb
    #   neck face 38.6 = the m18 0.2 gap) over y -14..17 and widens the flanges to x 43 / 41.8 wherever they stay >= 0.5 off the
    #   T_bok seat flange / socket (r 17.1 about the shoulder axis for x > 38.4, measured flange r 16.6) and >= 1.0 off the
    #   T_bok shell; a channel x 38.4..40 / y 5..12 keeps the arm-wire path from the column box to the socket open
    #   box closure z -51 (spec -52): 1.2 above the boards (amp / buck top -52.2)
    BRIDGES_Z=(ZF - 0.3, ZD0),     # full-height walls cradle <-> columns (spec: bridges z -60..-50 of rev. 1): L5 path
    # ---- pan servo posts / stop pins -------------------------------------------------------------------------------------
    PAN_POST=dict(x=(12.05, 17.25), y=(-25.1, -15.05), top=R2["PAN_SERVO"]["post_top"], leg=dict(x=(12.05, 16.45), y=(-26.5, -25.0)),
                  window=dict(y=(-25.0, -16.4), z=(-72.2, -62.2)), nut_slot=dict(y_half=2.35, z=(-59.35, -58.0)), hole_d=2.3, slot=0.3),
    #   x 12.05 (spec 11.25: overlaps the STS3032 case x +-11.75); nut slot through the post in x (a 0.7 wall to the case
    #   cannot be made); slot 4.7 in y for the +-0.3 C adjustment
    STOP_POSTS=dict(r=3.5, top=ZD0, p2_z=(-58.6, ZD0), pin_hole_d=3.05, pin_bond=8.4,
                    p2_block=dict(x=(-24.7, -17.87), y=(-21.06, -YO)),
                    p2_column=dict(x=(-24.7, -17.2), y=(-23.6, -YO), z_top=-58.6)),
    #   integrator rev2: the rev. 2 block ran to the -X end wall through the F1 boss path (x -32.2..-21.37, y -19..-15):
    #   T_stred could not be lowered (OBAL O3d).  Now the block stays at x >= -24.7 and a column (x -24.7..-17.2, y -23.6..-15.05)
    #   carries it down to the floor, merged with the -X pan-servo post (its DIN 562 slot is then entered from +X, servo out)
    #   post tops -48.2 (spec -50.6): pins bonded 8.4 deep, stub 3.6, the deck C-ear braces pin 1 at the contact height
    # ---- bosses (bonded M2.5 inserts from the top) -----------------------------------------------------------------------
    F3A=[(26.0, -11.7), (30.6, 4.0)],
    #   fixer rev2: F3a_2 (31, 5) -> (30.6, 4.0): its DIN 125 washer (r 3.0) stays inside r 34.1, so the deck can keep 0.3 off the
    #   thickened shoulder plate (inner face r 34.4) while it is lowered at T3
    #   integrator rev2: F3a_1 (26, -13.8) -> (26, -11.7): its washer / deck pad reached y -17.8, inside the F1 boss path; boss 0.3 off
    #   the STS3215 mounting ear (y -8)
    #   spec (20, +13.8) sits under the static FFC wall (r 24.2, az 34.6) and in the cradle FFC slot; (-33.5, +-10) heads
    #   (washer r 3.0) are 0.36 from the lug sweep r 31.6 and no deck may cross the lug sweep r 27.6..31.6 to reach them
    F3B=[(6.0, 15.95), (18.5, -15.95)],
    #   spec (6, -15.95): the boss collides with the STS3032 case (y <= -14.54, top -49.7); 2 screws + T_most resting on the
    #   +Y wall top / J1 servo top carry L1 (pivot outside the screw line -> compression on the wall top)
    BOSS=dict(r=3.4, z=(-52.8, ZD0), ins_hole=3.6, ins_depth=4.9, pilot=2.8),       # bottom 0.7 above the carrier top -53.5
    #   integrator rev2: insert hole through the boss (was 4.3 deep: a 0.3 x 0.4 floor ring around the pilot, K4)
    F3B_SCREW="DIN 7991 M2.5x6 countersunk, flush in the aluminium T_most (no head in the FFC duct / under the gear)",
    # ---- carrier ---------------------------------------------------------------------------------------------------------
    CTRL=dict(pcb_x=(-24.9, 24.9), y=R2["CTRL2"]["y"], z=R2["CTRL2"]["z"], f7=[(-18.0, -62.5), (-4.0, -62.5)], f7_face=16.5,
              screw="DIN 7991 M2x5 countersunk flush in the FR4 (no washer: head on the PCB, not on resin)", raise_module=2.5,
              rest_pad=(20.0, -62.5, 2.5)),
    #   integrator rev2: the rev. 2 carrier (x -27..28.6, F7 at x -25 / 25.8) stood in the path of the T_stred F1 boss columns
    #   (|x| >= 25.1, y >= 15.1): T_stred could not be lowered at T5.  Now the PCB is x -24.9..24.9; the ESP32-S3-Zero sits on
    #   its 2.5 mm pin-header spacer (USB-C mouth y 22.7), so the straight plug clears the PCB and no notch is needed; both F7
    #   screws are flush countersunk under the plug envelope (x -18 / -4, reached from the door when no plug is in); the +X end
    #   rests on a pad (x 20) without a screw
    #   spec PCB x -23..23 with F7 at x +-19: x +19 is under the ESP32-S3-Zero (x -0.5..23, full PCB height) -> PCB widened
    #   to x -27..28.6, F7 at x -25 / 25.8 (washer clear of the module); M2x5 (x6 would reach y 12.4, 0.05 from the STS3215)
    # ---- capacitor -----------------------------------------------------------------------------------------------------------
    CAP=dict(d=8.0, l=11.5, x=(6.0, 17.5), y=20.2, z=-76.8, pedestal_x=(8.0, 15.5), half_w=3.0, trough_r=4.1, groove=(2.8, 1.2)),
    #   spec D10 x 13 at x 6..19: collides with the tub wall (y 24.07 at x 19) -> 470 uF 10 V D8 x 11.5
    TIE_SADDLES=[dict(face=(-10.0, YO, -50.5), n="+y", along="x", h=4.6, tun=(1.2, 2.2))],     # 2.0 mm cable tie
    #   column-web saddles (spec y 12, z -45) dropped: the web inner face is 1.0 from PAN_ENV2 and the deck reaches x 34.2;
    #   arm wires enter the closed column box through a D4.5 hole (y 10.7, z -50.5) and run up inside it
    WALL_FFC_SLOT=dict(x=R2["FFC"]["cradle_slot"]["x"], z=(-51.3, -49.7)),   # spec z -51..-50: PAN FFC pair touched the edge
    DRAINS=[(31.0, -9.0), (-31.0, -9.0)], BOARD_STANDOFF=1.5, VENT_D=4.0,      # rev. 1 (+-33, -8) would cut the column feet
    #   fixer rev2 (overenie2 M3): print vents against suction cups (cap underside toward the plate, +15 deg about X, ON SUPPORTS):
    #   D3 drain through the cap floor under the pan-servo pocket, D2.5 vent into each column-foot bay (hidden by the base)
    CUP_VENTS=[(2.5, 0.0, -16.6, -80.0), (2.0, 0.0, 24.6, -81.0), (2.5, 38.5, 2.7, -79.5), (2.5, -38.5, 2.7, -79.5)],
    #   (d, x, y, z_top): +15 deg about +X puts the +Y end of every floor lowest -> each vent sits at the +Y end of its cup
    # ---- deck / bridge / boss ------------------------------------------------------------------------------------------------
    DECK_TRIM=dict(r=R2["DECK_TRIM"]["r"], az=R3["STOP"]["deck_trim_az"]),
    #   rev3 (R3-5): the stop faces of the lug are planes normal to x - the lug now sweeps B az 26.9..224.9 below the pin tops; the trim
    #   starts on the radial line through pin 1 (25.4: the C-ear still backs the pin on its loaded half), >= 1.0 to the lug face at -90
    #   spec az 16..232: the lug block (stage az 118.3..131.7) sweeps B az 28.3..221.7 below the pin tops; 1.0 at r 27.6 =
    #   2.08 deg -> 26.2..223.8 lets the deck embrace pin 1 from its back side (C-ear, > 180 deg)
    MOST=dict(circles=[(0.0, 0.0, 12.5), (6.0, 15.95, 3.0), (11.0, 15.5, 2.5), (18.5, -15.95, 3.0)], tap_d=2.5,
              csk=dict(d=2.8, dk=5.2, depth=1.2)),
    CAP_BOSS=dict(r=R2["PIVOT"]["boss_d"] / 2, z=R2["PIVOT"]["boss_z"], hole_d=R2["PIVOT"]["boss_hole"], edge_r=0.3, flare_r=R3["PIVOT"]["cap_root_r"]),
    #   rev3 (R3-9 / S8): root flare R1.0 (was R0.6) - it reaches r 4.14 at the gear bottom -45.9, so the LOWER bore edge of the 36T gear is
    #   chamfered 0.4 x 45 deg (t4_pan.mk_koleso; by hand with a countersink if the bought gear has none); hole D3.1 (was 3.4; B4)
    SHIMS=dict(strips=[((-14.3, 15.7), (4.0, 8.0)), ((-14.3, 15.7), (-8.0, -4.0))], z=R2["STACK"]["shim"],
               c_shim=dict(x=(XE, S15["x"][0]), y=(-10.0, 10.0), z=(-80.0, -52.0))),
    #   rev3 (R3-1 / R3-2): ISO 7380 M3x8; stack on T_cap = 2 x DIN 125 M3 (spacers) + DIN 9021 M3 (retention washer over the hub lip
    #   of P_sachta) + head; tip -48.0 (1.8 of the 2.0 T_most, 0.2 above its underside, 0.3 above the STS3215)
    F15=dict(screw=R3["PIVOT"]["screw"], length=R3["PIVOT"]["screw_len"], head=R2["PIVOT"]["head_z"], tip=R3["PIVOT"]["tip_z"],
             washer=(1.6, R3["PIVOT"]["washer_r"], R2["PIVOT"]["washer_z"]), spacer=(1.6, R3["PIVOT"]["spacer_r"], R3["PIVOT"]["spacer_t"]),
             spacer_z=R3["PIVOT"]["spacer_z"]),
)
DEVIATIONS = [
    "T_spodok J1 stop lug r 18.65..21.0 x 5.0 tangential x 4.0 (spec r 17..21 x 4.0): inside r 18.575 it would block the 6805, "
    "which goes in from below; tangential 5.0 restores the root section (hand 0.6 N.m: 9.2 MPa <= 12.9).  Stop at +-153.4 deg "
    "with the base block az 270 +- 19 (spec 155); base block r 17..21 engages 2.35 radial.",
    "Base FFC slot = annular sector r 21.1..22.4, B az 74.5..105.5 (spec flat x -6..6, y 21.2..22.5 left 0.71 of plinth skin).",
    "Bridges cradle <-> columns are full-height walls (z -82.6..-48.2, rev. 1 / spec z -60..-50): the column U below the box "
    "closure alone is 16..24 MPa under L5; with the bridge walls the connected section carries it (S rows 42c).",
    "Carrier PCB notched under the USB-C plug envelope (x -21..-0.5, z -66.5..-58.5): a straight plug overmold (about 6.5 thick, "
    "centred on y 20.2) reaches y 16.95, inside the PCB (y 16.5..18.1); behind the notch the cradle wall is 1.9 away.",
    "F16: 2 screws at the -X pads only (spec 4): the +X pads lie over the plinth ring and the 6805 seat (r 13..20) - no tool path "
    "from below once the bearing is bonded.  +X end: bumper + PORON in x, clamped in z by T_most / deck + shims.  F16 heads "
    "(ISO 7380 + washer) protrude to z -86.1 at r 26.7..30.5: base top must be <= -86.3 there.",
    "Cradle front wall 1.69 thick (y -14.243..-12.55) for |x| <= 12.05, z -73..-48.2: the STS3032 case (y <= -14.543) and the "
    "STS3215 (y >= -12.35) leave 2.19 between them; spec wall 2.5 would cut 0.51 into the pan servo.",
    "F4: no washer (the ISO 7380 head bears on the servo's own tab; a DIN 125 D5 washer would overlap the case by 0.25).",
    "Pan-servo posts x +-(12.05..17.25), y -25.1..-15.05 (spec 11.25..17.25, -24.6..-17.1): 0.3 off the STS3032 case; DIN 562 "
    "slot runs through the post in x, 4.7 wide in y (+-0.3 C slot); +X post: window for the servo plug + front leg 1.5.",
    "Stop-pin posts: tops -48.2 (spec -50.6), pins bonded 8.4 deep (spec 6.0), same pin position / top -44.6.  Post 2 is a block "
    "x -32.2..-21.37, y -19..-15.05, z -58.6..-48.2 tied to the -X end wall (a bracket on the free front wall alone: 28 MPa).",
    "Deck (T_paluba) trim r <= 26.6 for B az 26.2..223.8 (spec 16..232) with a C-ear around pin 1 (from its back side): "
    "the lug block sweeps B az 28.3..221.7 below the pin tops, 1.0 clearance = 2.08 deg at r 27.6.",
    "F3a deck screws at (26, -13.8) and (31, 5) only (spec 4 at (20, +-13.8), (-33.5, +-10)): (20, 13.8) is under the static "
    "FFC wall and in the cradle FFC slot; the -X positions are behind the lug sweep (no deck may cross r 27.6..31.6, washers "
    "0.36 from the lug).  The -X end of the deck's back lobe is unscrewed (rests on the +Y wall and the servo top).",
    "F3b: DIN 7991 M2.5x6 countersunk, flush in the ALUMINIUM T_most (no countersunk head in resin anywhere): ISO 7380 heads "
    "on top of T_most would sit in the FFC duct / under the gear tips (r 14..20, z -46.2..-44.3).  Positions (6, 15.95) and "
    "(18.5, -15.95) (spec (6, -15.95) collides with the STS3032 case).  T_most outline = hull of circles (not 18 x 36).",
    "F1 = ISO 7380 M2.5x6 (spec x8: the tip would reach z -75.1, 0.6 into the T_stred boss beyond its insert pilot).",
    "Carrier PCB x -27..28.6 (spec -23..23), F7 at x -25 / 25.8 (spec +-19: x +19 is under the ESP32-S3-Zero); F7 = M2x5 "
    "(x6 tip 0.05 from the STS3215 case).  Bosses fused with the cradle wall / stop post 1.",
    "Capacitor 470 uF 10 V D8 x 11.5 at x 6..17.5, y 20.2, z -76.8 (spec D10 x 13 at x 6..19 collides with the tub wall); "
    "pedestal trough r 4.1 + tie groove 2.8 x 1.2 under the can.",
    "Base FFC floor slot y 20.6..21.9 (spec 21.2..22.5): plinth skin at x +-6 1.29 (spec gives 0.71).",
    "Box closure z -51..-34 (spec -52): 1.2 above the amplifier / buck tops (-52.2).",
    "rev3: T_cap root flare R1.0 as specified (the 36T gear gets a 0.4 x 45 deg chamfer on its LOWER bore edge); hole D3.1.",
    "rev3: F15 = ISO 7380 M3x8 on a stack of 2 x DIN 125 M3 + DIN 9021 M3 (head seat -40.0, tip -48.0): 1.8 of the 2.0 T_most engaged "
    "(1.51 at the shortest screw 7.71); a dry-fitted screw whose tip stands proud of the T_most underside gets one more DIN 125 under "
    "its head (K7 calibration row).  The DIN 9021 overlaps the hub lip of P_sachta: positive axial retention of the WELL.",
    "rev3: pan pinion face 3.0 (z -45.9 .. -42.9; a bought 4.0 pinion is shortened by 1.0 at its TOP face): 1.0 under the stage floor.",
    "Tie saddle on the cradle back wall: tunnel 2.2 x 1.2 for a 2.0 mm cable tie (spec 2.8 x 1.2 for 2.5 mm): bars 1.2 and 0.7 above the carrier top within the 4.6 between the carrier (-53.5) and the deck seat (-48.2).  Column-web saddles dropped (see TIE_SADDLES).",
    "Static FFC wall: root fillet R1 on the outer side only; the inner face is the FFC running face (no fillet).",
    "Spigot notches / tower keep-out = OBAL F1 zone + 0.5 (x +-(25.1..32.9), |y| >= 15.1, z -81..-74.5): the rev. 1 T_stred "
    "boss webs reach beyond a r 3.9 cylinder (0.8 mm collision on the real meshes); stop post 1 loses its y > 15.1 part below -74.5.",
    "Cradle wall FFC slot z -51.3..-49.7 (spec -51..-50) + 0.8 x 45 deg chamfer on the inner top edge: the PAN FFC pair touched "
    "the slot edge (0.06 on the meshes) where it turns up to the deck slot.",
    "Z_naboj_test stop block top -99.3 (rev. 1 -98.3): the lug's R1 root fillets (z -99..-98) must not touch it; the base round's "
    "stop block needs the same (top -99.3 .. -100, r 17..21).",
]

# =====================================================================================================================
# helpers
# =====================================================================================================================
def one(s):
    sol = list(s.solids()) if hasattr(s, "solids") else [q for x in s for q in x.solids()]
    return sol[0] if len(sol) == 1 else max(sol, key=lambda q: q.volume)


def fuse(shapes):
    shapes = [s for s in shapes if s is not None]
    return shapes[0] if len(shapes) == 1 else shapes[0].fuse(*shapes[1:])


def cut(base, cutters):
    cutters = [c for c in cutters if c is not None]
    return base.cut(*cutters) if cutters else base


def prism_x(pts_yz, x0, x1):
    w = bd.Wire.make_polygon([Vector(x0, y, z) for y, z in pts_yz], close=True)
    return bd.extrude(bd.Face(w), amount=x1 - x0, dir=(1, 0, 0))


def prism_y(pts_xz, y0, y1):
    w = bd.Wire.make_polygon([Vector(x, y0, z) for x, z in pts_xz], close=True)
    return bd.extrude(bd.Face(w), amount=y1 - y0, dir=(0, 1, 0))


def prism_z(pts_xy, z0, z1):
    w = bd.Wire.make_polygon([Vector(x, y, z0) for x, y in pts_xy], close=True)
    return bd.extrude(bd.Face(w), amount=z1 - z0, dir=(0, 0, 1))


def pol(r, az_deg, cx=0.0, cy=0.0):
    a = math.radians(az_deg)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def wedge_z(r, a0, a1, z0, z1, cx=0.0, cy=0.0):
    n = max(2, int(math.ceil((a1 - a0) / 15.0)) + 1)
    step = (a1 - a0) / (n - 1)
    rr = r / math.cos(math.radians(step / 2)) * 1.02
    return prism_z([(cx, cy)] + [pol(rr, a0 + i * step, cx, cy) for i in range(n)], z0, z1)


def tube_sector(ro, ri, a0, a1, z0, z1, cx=0.0, cy=0.0):
    t = C.cyl_z(ro, z0, z1, cx, cy) - C.cyl_z(ri, z0 - 0.5, z1 + 0.5, cx, cy)
    return one(t & wedge_z(ro, a0, a1, z0 - 1, z1 + 1, cx, cy))


def bx(x0, x1, y0, y1, z0, z1):
    return C.box(min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), min(z0, z1), max(z0, z1))


def cyl(axis, r, a, b, p, q):
    """cylinder along `axis` from a to b; (p, q) = the other two coordinates in xyz order"""
    return {"x": C.cyl_x, "y": C.cyl_y, "z": C.cyl_z}[axis](r, min(a, b), max(a, b), p, q)


def hole(d, at, axis, sign, depth, lead=0.15):
    k = "xyz".index(axis)
    a, b = at[k] - sign * lead, at[k] + sign * depth
    o = [at[i] for i in range(3) if i != k]
    return cyl(axis, d / 2, a, b, o[0], o[1])


def slot_hole(d, at, axis, sign, depth, dirv, half):
    """hole of diameter d elongated +-half along the unit vector dirv (perpendicular to axis)"""
    a = np.array(at, float); dv = np.array(dirv, float)
    hs = [hole(d, tuple(a + s * half * dv), axis, sign, depth) for s in (-1, 1)]
    k = "xyz".index(axis)
    n = np.cross(np.eye(3)[k], dv)
    corners = [a + s1 * half * dv + s2 * d / 2 * n for s1, s2 in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    a0, a1 = sorted((at[k] - sign * 0.15, at[k] + sign * depth))
    if axis == "z":
        mid = prism_z([(c[0], c[1]) for c in corners], a0, a1)
    elif axis == "x":
        mid = prism_x([(c[1], c[2]) for c in corners], a0, a1)
    else:
        mid = prism_y([(c[0], c[2]) for c in corners], a0, a1)
    return fuse(hs + [mid])


AX = {"+x": (0, 1), "-x": (0, -1), "+y": (1, 1), "-y": (1, -1), "+z": (2, 1), "-z": (2, -1)}


def fil(part, name, t, lo, hi, p, a, b, r):
    """straight concave fillet strip along the axis t ('x'|'y'|'z') from lo to hi; p = the edge point (x, y, z) (its t
    coordinate is ignored); a, b = the free directions of the two faces ('+y', '-z', ...).  Recorded in ROOTS."""
    ka, sa = AX[a]; kb, sb = AX[b]; kt = "xyz".index(t)
    lo_, hi_ = [0, 0, 0], [0, 0, 0]
    lo_[kt], hi_[kt] = lo, hi
    lo_[ka], hi_[ka] = sorted((p[ka], p[ka] + sa * r))
    lo_[kb], hi_[kb] = sorted((p[kb], p[kb] + sb * r))
    blk = C.box(lo_[0], hi_[0], lo_[1], hi_[1], lo_[2], hi_[2])
    c = list(p); c[ka] += sa * r; c[kb] += sb * r
    o = [c[i] for i in range(3) if i != kt]
    cutter = cyl(t, r, lo - 0.5, hi + 0.5, o[0], o[1])
    u = [0.0, 0.0, 0.0]; u[ka] = sa / math.sqrt(2); u[kb] = sb / math.sqrt(2)
    q = list(p); q[kt] = 0.5 * (lo + hi)
    ROOTS.append(dict(part=part, name=name, p=[round(v, 3) for v in q], u=[round(v, 4) for v in u], R=r))
    return one(blk - cutter)


def cove(part, name, axis, ctr, r0, R, plane, sgn, record_at=None):
    """concave fillet ring around a cylinder (radius r0, axis `axis` through ctr = the other two coords) standing on the
    plane axis = plane, free side sgn (+1 / -1).  record_at: (azimuth deg in the ctr plane) for the ROOTS probe."""
    ring = bd.Pos(0, 0, sgn * R / 2) * (bd.Cylinder(r0 + R, R) - bd.Cylinder(r0 - 0.01, R + 0.2))
    tor = bd.Pos(0, 0, sgn * R) * bd.Torus(r0 + R, R)
    s = ring - tor
    rot = {"z": bd.Rot(0, 0, 0), "x": bd.Rot(0, 90, 0), "y": bd.Rot(-90, 0, 0)}[axis]
    k = "xyz".index(axis)
    pos = [0.0, 0.0, 0.0]; pos[k] = plane
    o = [i for i in range(3) if i != k]
    pos[o[0]], pos[o[1]] = ctr
    s = one(bd.Pos(*pos) * (rot * s))
    if record_at is not None:
        a = math.radians(record_at)
        q = list(pos); q[o[0]] += r0 * math.cos(a); q[o[1]] += r0 * math.sin(a)
        u = [0.0, 0.0, 0.0]; u[k] = sgn / math.sqrt(2); u[o[0]] = math.cos(a) / math.sqrt(2); u[o[1]] = math.sin(a) / math.sqrt(2)
        ROOTS.append(dict(part=part, name=name, p=[round(v, 3) for v in q], u=[round(v, 4) for v in u], R=R))
    return s


def hull2d(P):
    P = sorted(set((round(x, 6), round(y, 6)) for x, y in P))
    def cr(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in P:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(P):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def hull_circles(circles, grow=0.0, n=96):
    P = []
    for cx, cy, r in circles:
        P += [pol(r + grow, 360.0 * i / n, cx, cy) for i in range(n)]
    return hull2d(P)


def gear_profile(m, z, phase_deg=0.0, backlash=0.04, n_inv=7):
    """2-D involute spur gear outline (20 deg), tooth k centred at phase + k * 360 / z"""
    rp = m * z / 2; rb = rp * math.cos(math.radians(20.0)); ra = rp + m; rf = rp - 1.25 * m
    s = math.pi * m / 2 - backlash
    ap = math.radians(20.0)

    def inv(a):
        return math.tan(a) - a

    def half(r):
        return s / (2 * rp) + inv(ap) - inv(math.acos(min(1.0, rb / r)))
    r0 = max(rb, rf)
    rs = [r0 + (ra - r0) * i / (n_inv - 1) for i in range(n_inv)]
    pitch = 2 * math.pi / z
    out = []
    for k in range(z):
        c = math.radians(phase_deg) + k * pitch
        if rf < rb:
            out.append((rf, c - half(r0)))
        out += [(r, c - half(r)) for r in rs] + [(r, c + half(r)) for r in reversed(rs)]
        if rf < rb:
            out.append((rf, c + half(r0)))
        out.append((rf, c + pitch / 2))
    return [(r * math.cos(a), r * math.sin(a)) for r, a in out]


def gear_solid(m, z, z0, z1, cx, cy, phase_deg, backlash=0.04):
    return prism_z([(cx + x, cy + y) for x, y in gear_profile(m, z, phase_deg, backlash)], z0, z1)


# ---- fasteners (ISO 7380 sizes are catalogue nominal, UNVERIFIED: M2 dk 3.5 k 1.3, M2.5 dk 4.7 k 1.375, M3 dk 5.7 k 1.65)
BTN = {"M2": (2.0, 3.5, 1.3), "M2.5": (2.5, 4.7, 1.375), "M3": (3.0, 5.7, 1.65), "M2tf": (2.0, 3.5, 1.3)}
WASH = {"M2": (2.2, 5.0, 0.3), "M2.5": (2.7, 6.0, 0.5), "M3L": (3.2, 9.0, 0.8)}      # DIN 125 / DIN 9021 (M3L)


def _along(s, axis, sign):
    return C._along(s, axis, sign)


def screw_btn(size, length, at, axis, sign):
    """button-head screw: head bearing face at `at`, shank along axis*sign"""
    d, dk, k = BTN[size]
    s = bd.Pos(0, 0, -k / 2) * bd.Cylinder(dk / 2, k) + bd.Pos(0, 0, length / 2) * bd.Cylinder(d / 2, length)
    return one(bd.Pos(*at) * _along(s, axis, sign))


def washer(size, at, axis, sign):
    """washer lying on the surface point `at`, extending against axis*sign (toward the head)"""
    di, do, t = WASH[size]
    s = bd.Pos(0, 0, -t / 2) * (bd.Cylinder(do / 2, t) - bd.Cylinder(di / 2, t + 0.2))
    return one(bd.Pos(*at) * _along(s, axis, sign))


def screw_csk90(d, dk, length, at, axis, sign):
    """countersunk 90 deg screw (DIN 7991), head top flush at `at`, length = overall"""
    k = (dk - d) / 2
    s = bd.Pos(0, 0, k / 2) * bd.Cone(dk / 2, d / 2, k) + bd.Pos(0, 0, (k + length) / 2) * bd.Cylinder(d / 2, length - k)
    return one(bd.Pos(*at) * _along(s, axis, sign))


def nut562(at, half=2.0, t=1.2, d=2.0):
    """DIN 562 M2 square nut 4.0 x 4.0 x 1.2 (top face at `at`, body below)"""
    x, y, z = at
    return one(C.box(x - half, x + half, y - half, y + half, z - t, z) - C.cyl_z(d / 2, z - t - 0.2, z + 0.2, x, y))


def timed(name):
    def deco(fn):
        def wrap(*a, **k):
            t = time.time(); r = fn(*a, **k); TIMES[name] = round(time.time() - t, 1)
            return r
        wrap.__wrapped__ = fn
        return wrap
    return deco


# =====================================================================================================================
# BOUGHT PARTS (datasheet solids at real size; seats carry the tolerance)
# =====================================================================================================================
F16_Z = (ZB, -78.8)


def mk_servo_J1():
    """Feetech STS3215: case 45.2 x 24.7 x 35.0 (+-0.3), boss D12 x 2.6, 25T spline D5.9 x 2.2 (UNVERIFIED); shaft DOWN at
    J1_AX; +X block = reserved bend space of the two 5264 plugs.  2 case holes (M2, positions UNVERIFIED) at the -X pads."""
    case = C.box(*S15["x"], *S15["y"], *R2["STACK"]["j1_case"])
    boss = C.cyl_z(S15["boss_r"], C.Z_J1_BOSS[0], C.Z_J1_BOSS[1] + 0.5, J1X, J1Y)
    shaft = C.cyl_z(S15["spline_d"] / 2, -88.1, C.Z_J1_BOSS[0] + 0.5, J1X, J1Y)
    P = S15["plug"]
    plug = C.box(P["x"][0] - 0.5, P["x"][1], P["y"][0], P["y"][1], R2["STACK"]["j1_case"][1] - P["dz"], R2["STACK"]["j1_case"][1])
    s = one(fuse([case, boss, shaft, plug]))
    return one(cut(s, [C.cyl_z(0.8, -83.4, -78.3, x, y) for x, y in RAM2["F16"]["at"]]))


def mk_pastorok_J1():
    """brass spur gear m1 18T (da 20, d 18), plain, face 4.0 (z -90..-86), bore D6.00 H7 on the STS3215 spline
    (Loctite 638, no screw).  A tooth GAP faces the torso axis (+X)."""
    z0, z1 = R2["J1"]["gear_plane"]
    g = gear_solid(C.M_J1, C.T_J1, z0, z1, J1X, J1Y, 10.0)
    return one(g - C.cyl_z(R2["J1"]["pinion_bore"] / 2, z0 - 0.5, z1 + 0.5, J1X, J1Y))


def mk_koleso_J1():
    """sun gear of the dummy hub: brass m1 18T, face 4.0 (z -90..-86), tapped M8 (screwed + bonded on the M8 core)"""
    z0, z1 = R2["J1"]["gear_plane"]
    g = gear_solid(C.M_J1, C.T_J1, z0, z1, 0.0, 0.0, 0.0)
    return one(g - C.cyl_z(4.0, z0 - 0.5, z1 + 0.5))


def mk_lozisko():
    d, D, B = C.BRG_6805
    return one(C.cyl_z(D / 2, *C.Z_BRG) - C.cyl_z(d / 2, C.Z_BRG[0] - 0.5, C.Z_BRG[1] + 0.5))


PAN_TAB_Z = R2["PAN_SERVO"]["tab_z"]
PAN_CASE_Z = R2["PAN_SERVO"]["case_z"]
PAN_DZ = PAN_CASE_Z[0] - S32["z"][0]          # +1.5 relative to rev. 1
C_DIR = (-PAX[0] / math.hypot(*PAX), -PAX[1] / math.hypot(*PAX))     # unit vector PAN_AX -> torso axis


def mk_servo_pan():
    """Feetech STS3032: case 23.5 x 12.5 x 23.0 at z -72.7..-49.7, tabs 32.5 x 12.5 x 2.5 (z -56.5..-54.0, holes D2.2 at
    x +-14.0), boss D12.4 to z -46.2, 25T spline D4.95 x 3.5 (to -42.7, UNVERIFIED); plug block = reserved bend space."""
    case = C.box(*S32["x"], *S32["y"], *PAN_CASE_Z)
    T = S32["tab"]
    tabs = C.box(T["x"][0], T["x"][1], S32["y"][0], S32["y"][1], *PAN_TAB_Z)
    boss = C.cyl_z(S32["boss_r"], PAN_CASE_Z[1] - 0.5, R2["PAN_SERVO"]["boss_top"], *PAX)
    shaft = C.cyl_z(4.95 / 2, R2["PAN_SERVO"]["boss_top"] - 0.5, -42.7, *PAX)
    P = S32["plug"]
    plug = C.box(P["x"][0] - 0.5, P["x"][1], *P["y"], P["z"][0] + PAN_DZ, P["z"][1] + PAN_DZ - 1.0)   # top -64.2 (F4 tip -64.0)
    s = one(fuse([case, tabs, boss, shaft, plug]))
    return one(cut(s, [C.cyl_z(T["hole_d"] / 2, PAN_TAB_Z[0] - 0.5, PAN_TAB_Z[1] + 0.5, hx, PAX[1]) for hx in T["hole_x"]]))


def mk_pastorok_pan():
    """plain spur gear m0.8 18T (da 16.0, d 14.4), face 4.0 (z -45.9..-41.9), bore D5.00 H7 on the STS3032 spline (Loctite
    638).  A tooth GAP faces the pan axis (the 36T of PAN has a tooth at B az 254.3 at pan 0: PAN phase 4.3 + 10 k)."""
    z0, z1 = R2["GEAR_PAN"].get("pinion_plane", R2["GEAR_PAN"]["plane"])     # rev3 (R3-3 b): pinion top -42.9 (mesh width 3.0)
    to_axis = math.degrees(math.atan2(-PAX[1], -PAX[0]))
    g = gear_solid(C.M_PAN, C.T_PAN[0], z0, z1, PAX[0], PAX[1], to_axis + 10.0)
    return one(g - C.cyl_z(R2["GEAR_PAN"]["pinion"]["bore"] / 2, z0 - 0.5, z1 + 0.5, *PAX))


def mk_ptfe():
    W = R2["PTFE_WASHER"]; z0, z1 = R2["STACK"]["ptfe"]
    return one(C.cyl_z(W["od"] / 2, z0, z1) - C.cyl_z(W["id"] / 2, z0 - 0.2, z1 + 0.2))


def mk_ptfe_cap():
    """PTFE tape 0.13 wrapped once on T_cap (above its root flare) -> journal D7.96 in the 36T bore 8.00"""
    B = RAM2["CAP_BOSS"]
    return one(C.cyl_z(B["r"] + 0.13, B["z"][0] + B["flare_r"], B["z"][1] - B["edge_r"])
               - C.cyl_z(B["r"], B["z"][0], B["z"][1]))


def mk_kolik(i):
    """steel dowel ISO 8734 3 m6 x 12, bonded 8.4 deep (hole D3.05 drilled after curing), top z -44.6"""
    St = R2["STOP"]; x, y = St["pin_xy"][i]
    return C.cyl_z(St["pin_d"] / 2, St["pin_top"] - St["pin_len"], St["pin_top"], x, y)


CT = RAM2["CTRL"]
YPCB0, YPCB1 = CT["y"]                     # 16.5 / 18.1
ZC0, ZC1 = CT["z"]                         # -71.5 / -53.5
_RM = 2.5                                  # integrator rev2: ESP32-S3-Zero raised on its 2.54 pin headers (plastic spacer 2.5)
CTRL_BLOCKS = {   # connector / module blocks on the +Y face (x0, x1, y1, z0, z1); y0 = 18.1 (FFC / header bodies)
    "ESP32-S3-Zero PCB": (-0.5, 23.0, 19.1 + _RM, ZC0, ZC1),
    "ESP32-S3-Zero shield + parts": (1.5, 17.5, 21.0 + _RM, ZC0 + 2.0, ZC1 - 2.0),
    "USB-C receptacle (mouth +X)": (15.65, 23.0, 21.83 + _RM, -66.97, -58.03),
    #   fixer rev2 (overenie2 M1): module turned 180 deg - USB-C mouth faces +X at x 23.0 (a straight plug cannot be seated or
    #   inserted from the door: shell 8.34 + overmold 12.35 x 6.5 + strain relief >= 25 against 18.6 mm to the door edge); the port
    #   is brought to the door by a bought 90 deg USB-C FPC extension (usb_predlzovac)
    "J_PAN_A Y5B AYF530535": (-22.5, -16.4, 20.1, -57.5, -53.5),      # fixer rev2 M5: FH12-5S-0.5SH does not exist (FH12 0.5 mm starts at 6 p)
    "J_PAN_B Y5B AYF530535": (-15.4, -9.3, 20.1, -57.5, -53.5),
    "J_BUS_V 3p 2.5 header": (-8.5, -1.0, 23.5, -58.0, -53.5),
    "J_J1 FH12-10S-1SH": (-22.5, -8.0, 20.1, -71.5, -67.0),
    "J_BUS_5 3p 2.5 header": (-7.5, -0.5, 23.5, -71.5, -67.0),
}


USB_EXT = dict(head=dict(x=(23.0, 28.0), y=(20.95, 24.45), z=(-67.25, -57.75)), fpc=dict(x=(25.0, 25.3), y=(24.45, 26.2), z=(-67.0, -58.0)),
               part="90 deg USB-C FPC extension, slim male (USB-C plug, FPC exit 90 deg toward +Y) to USB-C female on a small PCB, "
                    "about 10 cm (ADT-Link class 'USB-C FPC flat cable 90 degree'; head size UNVERIFIED: modelled 5.0 x 3.5 x 9.5)")
#   fixer rev2 (M1): the male head sits in the free space x 23..28 beside the module (after T5: the T_stred F1 boss passes there
#   while it is lowered); the FPC leaves +Y toward the door; its female end is parked in the door zone and pulled out through
#   the door for flashing (any straight USB-C cable then plugs in outside the torso)


def mk_usb_predlzovac():
    H, F = USB_EXT["head"], USB_EXT["fpc"]
    return one(fuse([C.box(*H["x"], *H["y"], *H["z"]), C.box(*F["x"], H["y"][1] - 0.05, F["y"][1], *F["z"])]))


def mk_riadenie():
    """carrier DPS_riadenie: FR4 55.6 x 18 x 1.6 (x -27..28.6, y 16.5..18.1, z -71.5..-53.5) + Waveshare ESP32-S3-Zero
    (23.5 x 18, USB-C mouth at (-0.5, 20.2, -62.5) facing -X) + connector blocks of spec 17.6; all parts y <= 23.5."""
    P = [C.box(*CT["pcb_x"], YPCB0, YPCB1, ZC0, ZC1)]
    for nm, (x0, x1, y1, z0, z1) in CTRL_BLOCKS.items():
        if nm.startswith("ESP32-S3-Zero PCB"):                   # module PCB on the header spacer + the 2 header rows
            P += [C.box(x0, x1, YPCB1 + _RM, y1, z0, z1), C.box(x0 + 0.5, x1 - 0.5, YPCB1 - 0.05, YPCB1 + _RM + 0.05, z0, z0 + 2.5),
                  C.box(x0 + 0.5, x1 - 0.5, YPCB1 - 0.05, YPCB1 + _RM + 0.05, z1 - 2.5, z1)]
        elif nm.startswith("ESP32-S3-Zero shield"):
            P.append(C.box(x0, x1, YPCB1 + _RM + 0.95, y1, z0, z1))
        elif nm.startswith("USB-C"):
            P.append(C.box(x0, x1, 18.57 + _RM, 21.83 + _RM, -66.97, -58.03))       # mid-mount, centred on y 22.7, mouth +X
        else:
            P.append(C.box(x0, x1, YPCB1 - 0.05, y1, z0, z1))
    s = one(fuse(P))
    N = []
    for x, z in CT["f7"]:                                      # D2.3 hole + 90 deg countersink D4.1 for the flush DIN 7991 head
        N.append(C.cyl_y(1.15, YPCB0 - 0.5, YPCB1 + 0.5, x, z))
        N.append(bd.Pos(x, YPCB1 + 0.01, z) * C._along(bd.Pos(0, 0, 1.0) * bd.Cone(2.05 + 0.01, 1.15 - 0.99, 2.0), "y", -1))
    return one(cut(s, N))


BUCK_C = ((C.BUCK["y"][0] + C.BUCK["y"][1]) / 2, (C.BUCK["z"][0] + C.BUCK["z"][1]) / 2)
BUCK_HOLES = [(BUCK_C[0] - 6.73, BUCK_C[1] + 6.73), (BUCK_C[0] + 6.73, BUCK_C[1] - 6.73)]     # 0.53 in diagonal
AMP_C = ((C.AMP["y"][0] + C.AMP["y"][1]) / 2, (C.AMP["z"][0] + C.AMP["z"][1]) / 2)
AMP_HOLES = [(AMP_C[0] - 6.35, C.AMP["z"][1] - 2.54), (AMP_C[0] + 6.35, C.AMP["z"][1] - 2.54)]


def mk_menic():
    """Pololu D36V28F5 17.8 x 17.8 (PCB 1.6, components outward -X to 8.8 total), on 1.5 standoffs of the right web"""
    xa, xb = R2["BUCK_X"]; (ya, yb), (za, zb) = C.BUCK["y"], C.BUCK["z"]
    s = one(fuse([C.box(xb - 1.6, xb, ya, yb, za, zb), C.box(xa, xb - 1.5, ya + 2.0, yb - 2.0, za + 2.0, zb - 2.0)]))
    N = [C.cyl_x(1.1, xb - 2.5, xb + 0.5, y, z) for y, z in BUCK_HOLES] + [C.cyl_x(2.6, xa - 0.5, xb - 1.6, y, z) for y, z in BUCK_HOLES]
    return one(cut(s, N))


def mk_zosilnovac():
    """Adafruit 3006 MAX98357A 19.3 x 17.8 x 3.0 (PCB 1.6 + parts), on 1.5 standoffs of the left web"""
    xa, xb = R2["AMP_X"]; (ya, yb), (za, zb) = C.AMP["y"], C.AMP["z"]
    s = one(fuse([C.box(xa, xa + 1.6, ya, yb, za, zb), C.box(xa + 1.5, xb, ya + 3.0, yb - 3.0, za + 3.0, zb - 5.5)]))
    return one(cut(s, [C.cyl_x(1.25, xa - 0.5, xa + 2.5, y, z) for y, z in AMP_HOLES]))


def mk_kondenzator():
    K = RAM2["CAP"]
    return C.cyl_x(K["d"] / 2, K["x"][0], K["x"][1], K["y"], K["z"])


# =====================================================================================================================
# T_spodok - merged chassis (rev. 1 T_spodok + T_ram): cap, plinth, 6805 seat, cradle, columns, posts, bosses
# =====================================================================================================================
def _cap_stage_A():
    """slow part (loft cap): cap_blank + spigot ring with 0.6 lead-in - tub.  Cached separately."""
    a, b, n = C.SPIGOT_SE
    zs0, zs1 = C.SPIGOT["z"]
    th = C.azimuths(96)
    ring_lo = C.se_prism(a, b, n, zs0 - 0.6, zs1 - 0.6)
    r1 = C.se_r(a, b, n, th); r2 = r1 - 0.6
    w1 = C._wire(np.stack([r1 * np.cos(th), r1 * np.sin(th), np.full(96, zs1 - 0.6)], 1))
    w2 = C._wire(np.stack([r2 * np.cos(th), r2 * np.sin(th), np.full(96, zs1)], 1))
    lead = bd.Solid.make_loft([w1, w2], True)
    cap = one(C.cap_blank().fuse(ring_lo, lead))
    tub = C.se_prism(*C.TUB_SE, ZF, zs1 + 0.5)
    return one(cap.cut(tub))


def cap_stage_A():
    import inspect
    h = hashlib.md5((inspect.getsource(_cap_stage_A) + _base_text()).encode()).hexdigest()[:10]
    p = os.path.join(C.CACHE, f"ram2_capA_{h}.brep")
    if os.path.exists(p):
        return one(bd.import_brep(p))
    s = _cap_stage_A()
    for old in os.listdir(C.CACHE):
        if old.startswith("ram2_capA_"):
            os.remove(os.path.join(C.CACHE, old))
    bd.export_brep(s, p)
    return s


def _pads_J1():
    P = RAM2["J1_PADS"]
    return [C.box(x0, x1, y0, y1, ZB - 0.1, P["top"]) for x0, x1 in P["x"] for y0, y1 in (P["y"], (-P["y"][1], -P["y"][0]))]


def _j1_pass(r, z0, z1):
    a = C.J1_ADJ
    return fuse([C.cyl_z(r, z0, z1, J1X - a, J1Y), C.cyl_z(r, z0, z1, J1X + a, J1Y), C.box(J1X - a, J1X + a, J1Y - r, J1Y + r, z0, z1)])


def _under():
    """plinth, 6805 foot ring (seat D37.15), J1 stop lug + buttress (with R1 roots); no skirt"""
    zb0, zb1 = C.Z_BRG
    W = RAM2["J1_WINDOW"]
    plinth = C.cyl_z(C.R_PLINTH, zb1, ZB + 0.3) - C.cyl_z(C.R_FOOT_SHOULDER, zb1 - 0.5, ZB + 0.5)
    plinth = plinth - C.box(W["x"][0], W["x"][1], W["y"][0], W["y"][1], ZB, ZB + 1.0)          # 1.2 air under the case
    rs = RAM2["SEAT_R"]
    ring = C.cyl_z(C.R_FOOT_LOW, zb0, zb1 + 0.3) - C.cyl_z(rs, zb0 - 0.5, zb1 + 0.5)
    ring = ring - bd.Pos(0, 0, zb0 + 0.2) * bd.Cone(rs + 0.4, rs, 0.4)                          # entry chamfer 0.4
    L = RAM2["J1_LUG"]; w = L["w"] / 2
    lug = C.box(-w, w, L["r"][0], L["r"][1] + 0.5, L["z"][0], L["z"][1] + 0.2) & C.cyl_z(L["r"][1], L["z"][0] - 1, L["z"][1] + 1)
    r = L["root_r"]
    F = [fil("T_spodok", f"J1 lug side {s:+d} / foot ring bottom", "y", L["r"][0], L["r"][1] - 0.05, (s * w, 0, zb0),
             "+x" if s > 0 else "-x", "-z", r) for s in (1, -1)]
    return [plinth, ring, lug] + F


def _f1_pads():
    a, b, n = C.SPIGOT_SE
    lim = C.se_prism(a - 0.05, b - 0.05, n, ZF - 0.3, C.Z_WHITE)
    return [one(C.cyl_z(RAM2["F1"]["pad_r"], ZF - 0.3, C.Z_WHITE, x, y) & lim) for x, y in RAM2["F1"]["at"]]


def _column(s):
    """shoulder column on side s (+1 = left, +X): (positive solids, cutters)"""
    K = RAM2["COL"]
    xi, xw = K["web"]
    (wy0, wy1) = K["y"]
    fx0, fx1 = K["foot_x"]
    P, N = [], []
    # web from the tub top to the shoulder axis; foot = tub outline - 0.3 inside x 33..37.6 (the web overhang is minimal)
    P.append(bx(s * xi, s * xw, wy0, wy1, -78.2, SHZ))
    a, b, n = C.TUB_SE
    foot = C.se_prism(a - 0.3, b - 0.3, n, ZF - 0.3, -78.0) & bx(s * fx0, s * fx1, wy0, wy1, ZF - 0.5, -77.9)
    P.append(one(foot))
    # ribs with 45 deg run-out at the bottom
    xr = K["rib_x"]
    for ya, yb in K["ribs"]:
        P.append(prism_y([(s * (xw - 0.2), -78.0), (s * fx1, -78.0), (s * xr, -78.0 + (xr - fx1)), (s * xr, K["rib_top"]),
                          (s * (xw - 0.2), K["rib_top"])], ya, yb))
    # box closure
    P.append(bx(s * K["box_x"][0], s * K["box_x"][1], wy0, wy1, *K["box_z"]))
    # integrator rev2: column head (see RAM2["COL"]["head"])
    Hd = K["head"]; hz0, hz1 = Hd["z"]; hy0, hy1 = Hd["y"]
    xy = [(xi, hy0)] + list(Hd["xy_out"]) + [(xi, hy1)]
    head = prism_z([(s * x, y) for x, y in xy], hz0, hz1)
    yz = [(wy0, hz0), (wy1, hz0), (hy1, hz0 + (hy1 - wy1)), (hy1, hz1), (hy0, hz1), (hy0, hz0 + (wy0 - hy0))]
    head = head & prism_x(yz, -50.0, 50.0)
    head = head - cyl("x", Hd["r_cut"], s * Hd["x_cut"], s * 50.0, SHY, SHZ)
    Ch = Hd["chan"]
    head = head - bx(s * Ch["x"][0], s * Ch["x"][1], *Ch["y"], *Ch["z"])
    P.append(one(head))
    Pl = Hd["plate"]; py0, py1 = Pl["y"]; pz0, pz1 = Pl["z"]
    ty, tz = Pl["top_y"], Pl["top_z_end"]                  # top corners chamfered: >= 0.45 inside the shell inset 2.2 (C1)
    yzp = [(max(hy0, py0), pz0), (min(hy1, py1), pz0)] + ([(py1, pz0 + (py1 - hy1))] if py1 > hy1 else []) + \
        [(py1, tz), (ty, pz1), (-ty, pz1), (py0, tz)] + ([(py0, pz0 + (hy0 - py0))] if py0 < hy0 else [])
    Wp = Pl.get("wide")                                    # fixer rev2 (K12 column L5): plate |y| <= 20 for z -38 .. -20, back to 17 at -16
    if Wp:
        yw, zw0, zw1 = Wp["y"], Wp["z"][1], Wp["z_back"]
        yzp = [(max(hy0, py0), pz0), (min(hy1, py1), pz0), (yw, pz0 + (yw - hy1)), (yw, zw0), (py1, zw1), (py1, tz), (ty, pz1), (-ty, pz1),
               (py0, tz), (py0, zw1), (-yw, zw0), (-yw, pz0 + (yw + hy0))]
    plate = prism_x(yzp, *sorted((s * Pl["x_in_min"], s * Pl["x_out"]))) - C.cyl_z(Pl["r_in"], pz0 - 1.0, pz1 + 1.0)
    if Pl["flat_y"]:
        plate = plate - bx(0.0, s * Pl["r_in"], -Pl["flat_y"], Pl["flat_y"], pz0 - 1.0, pz1 + 1.0)   # flat x 34.5 at |y| <= 9.5
    #   fixer rev2 (K12 column L5): inner face r 34.4 = PAN_ENV2 r 33.4 + 1.0 at EVERY y (was r 34.5 with a flat x 34.5 for |y| <= 9.5):
    #   the plate is 0.1 .. 1.4 deeper at |y| <= 9.5; the deck now stays inside r 34.1 (F3a_2 moved to (30.6, 4.0))
    P.append(one(plate))                                   # inner face = r 34.4 (PAN_ENV2 r 33.4 + 1.0): deeper toward |y|
    # shoulder boss disc + backing flange (stop ring after the recess cut)
    P.append(one(fuse([cyl("x", K["boss_r"], s * xi, s * C.X_COL_BOSS, SHY, SHZ),
                       cyl("x", K["flange_r"], s * K["flange_x"][0], s * K["flange_x"][1], SHY, SHZ)])))
    P.append(prism_y([(s * (xw - 0.1), -31.9), (s * C.X_COL_BOSS, -29.8), (s * C.X_COL_BOSS, -27.0), (s * (xw - 0.1), -27.0)],
                     SHY - 3.0, SHY + 3.0))                                                  # gusset under the flange
    # ---- fillets: ribs / web (R2, full height), ribs / box closure inside the box (R1), flange / web (R1.5 cove, lower half)
    sx = "+x" if s > 0 else "-x"
    for ya, yb in K["ribs"]:
        for yy, d in ((ya, "-y"), (yb, "+y")):
            if (d == "-y" and ya == wy0) or (d == "+y" and yb == wy1):
                continue                                   # outer faces of the ribs = flush with the web ends
            P.append(fil("T_spodok", f"col {s:+d} rib / web y {yy}", "z", -73.6, K["rib_top"], (s * xw, yy, 0), sx, d, 2.0))
            P.append(fil("T_spodok", f"col {s:+d} rib / box closure y {yy}", "z", K["box_z"][0], K["box_z"][1],
                          (s * K["box_x"][0], yy, 0), "-x" if s > 0 else "+x", d, 1.0))
    cv = cove("T_spodok", f"col {s:+d} flange / web", "x", (SHY, SHZ), K["flange_r"], 1.5, s * K["flange_x"][0], s, record_at=-90.0)
    P.append(one(cv & bx(s * (xw - 0.1), s * (xw + 2.0), wy0, wy1, -40.0, SHZ - 4.0)))
    # foot roots (R2) on the floor: inner face x 33.0 and the two y faces
    P.append(fil("T_spodok", f"col {s:+d} foot inner / floor", "y", wy0, wy1, (s * fx0, 0, ZF), "-x" if s > 0 else "+x", "+z", 2.0))
    # ---- fixer rev2 (overenie2 S1): R1.5 along the +Y bridge-wall top / column inner face (x 34.4, z -48.2, y 12.55..15.05) and
    #      an R1.0 cove under the head overhang (x 42 .. 43 over the box closure face x 42 at z -38), clipped to the head outline
    P.append(fil("T_spodok", f"col {s:+d} +Y bridge top / column inner face (S1)", "y", YI, YO, (s * xi, 0, ZD0), "-x" if s > 0 else "+x", "+z",
                 K["bridge_fillet"]))
    hc = K["head_cove"]
    cov = fil("T_spodok", f"col {s:+d} head overhang / box closure face (S1)", "y", wy0, wy1, (s * K["box_x"][1], 0, hz0),
              "+x" if s > 0 else "-x", "-z", hc)
    P.append(one(cov & prism_z([(s * x, y) for x, y in xy], hz0 - hc - 0.1, hz0 + 0.1)))
    # ---- cutters: recess inside the stop ring, key slot az 0, F8 inserts az 60/180/300, wire hole, board pilots / vents
    N.append(cyl("x", K["boss_r"], s * C.X_COL_BOSS, s * (C.X_COL_STOP + 0.5), SHY, SHZ))
    N.append(bx(s * (C.X_COL_BOSS - 1.5), s * (C.X_COL_STOP + 0.5), SHY + 5.3, SHY + 14.0, SHZ - 1.5, SHZ + 1.5))
    for az in R2["COLUMN"]["f8_az"]:
        dy, dz = pol(7.5, az)
        at = (s * C.X_COL_BOSS, SHY + dy, SHZ + dz)
        xe = RAM2["COL"]["head"]["plate"]["r_in"]           # 34.4 = insert end plane |x| and the plate inner cylinder radius
        N += [hole(R2["INSERT_HOLES"]["M2"]["hole"], at, "x", -s, C.X_COL_BOSS - xe + 0.02)]   # fixer rev2 (S5): D4.1 to the insert end
        #   (M2 x 4 x OD 4.0 insert, x 38.4 .. 34.4).  Beyond it the lens between the inner cylinder r 34.4 and the plane |x| = 34.4 is cut
        #   away inside a RADIAL wedge over the hole (+ up past the plate top where it is < 1.0 above the hole): no floor, no sliver and no
        #   knife edge (the wedge faces are radial, i.e. normal to the cylinder) - the insert end face is exposed there
        hr = R2["INSERT_HOLES"]["M2"]["hole"] / 2 + 0.15
        yc, zc = SHY + dy, SHZ + dz; ztop = RAM2["COL"]["head"]["plate"]["z"][1]
        zw1 = zc + hr if ztop - (zc + hr) > 1.0 else ztop + 1.0
        N.append(prism_z([(0.0, 0.0), (s * xe, yc - hr), (s * xe, yc + hr)], zc - hr, zw1))
    Wh = K["wire_hole"]
    N.append(cyl("x", Wh["d"] / 2, s * (xi - 0.3), s * (xw + 0.3), Wh["y"], Wh["z"]))
    so = RAM2["BOARD_STANDOFF"]
    holes = AMP_HOLES if s > 0 else BUCK_HOLES
    for (y, z) in holes:
        P.append(cyl("x", 2.5, s * (xw - 0.2), s * (xw + so), y, z))
        N.append(cyl("x", 0.85, s * (xi - 0.3), s * (xw + so + 0.3), y, z))      # thread-forming pilot D1.7, through
    vc = AMP_C if s > 0 else BUCK_C
    N.append(cyl("x", RAM2["VENT_D"] / 2, s * (xi - 0.3), s * (xw + 0.3), vc[0], vc[1]))
    return P, N


def _boss(name, x, y, wall_face_y=None, wall_face_x=None, corbel=False):
    """M2.5 insert boss r 3.4 (z -52.8..-48.2) merged into the neighbouring wall face by a box that runs from the wall face
    to 1.0 past the boss centre (its side faces meet the wall at 90 deg -> R1 strips along z); optional 45 deg corbel
    under it.  Returns (solids, cutters)."""
    B = RAM2["BOSS"]; r = B["r"]; z0, z1 = B["z"]
    P = [C.cyl_z(r, z0, z1, x, y)]
    if wall_face_y is not None:
        sg = 1 if wall_face_y < y else -1                     # free side of the wall face
        P.append(bx(x - r, x + r, wall_face_y, y + sg * 1.0, z0, z1))
        d = "+y" if sg > 0 else "-y"
        for sx in (-1, 1):
            P.append(fil("T_spodok", f"{name} side {sx:+d} / wall", "z", z0, z1, (x + sx * r, wall_face_y, 0),
                         "+x" if sx > 0 else "-x", d, 1.0))
        if corbel:
            w = abs(y - wall_face_y) + r
            P.append(prism_x([(wall_face_y, z0 + 0.01), (wall_face_y + sg * w, z0 + 0.01), (wall_face_y, z0 - w)], x - r, x + r))
    if wall_face_x is not None:
        sg = 1 if wall_face_x < x else -1
        P.append(bx(wall_face_x, x + sg * 1.0, y - r, y + r, z0, z1))
        d = "+x" if sg > 0 else "-x"
        for sy in (-1, 1):
            P.append(fil("T_spodok", f"{name} side {sy:+d} / wall", "z", z0, z1, (wall_face_x, y + sy * r, 0), d,
                         "+y" if sy > 0 else "-y", 1.0))
        if corbel:
            w = abs(x - wall_face_x) + r
            P.append(prism_y([(wall_face_x, z0 + 0.01), (wall_face_x + sg * w, z0 + 0.01), (wall_face_x, z0 - w)], y - r, y + r))
    N = [hole(B["ins_hole"], (x, y, z1), "z", -1, B["ins_depth"]), hole(B["pilot"], (x, y, z1), "z", -1, z1 - z0 + 0.5, lead=0.0)]
    return P, N


def _tie_saddle(face, n, along, w=4.0, h=5.0, prot=2.6, tun=(1.2, 2.6)):
    """cable-tie saddle on a wall face: block (w along `along`, prot along n, h along z) with a tunnel along `along`"""
    x, y, z = face
    kn, sn = AX[n]; ka = "xyz".index(along)
    lo, hi = [x, y, z], [x, y, z]
    lo[ka] -= w / 2; hi[ka] += w / 2
    lo[2] -= h / 2; hi[2] += h / 2
    lo[kn], hi[kn] = sorted((face[kn] - sn * 0.2, face[kn] + sn * prot))
    blk = C.box(lo[0], hi[0], lo[1], hi[1], lo[2], hi[2])
    tl, th = list(lo), list(hi)
    tl[ka] -= 0.5; th[ka] += 0.5
    tl[kn], th[kn] = sorted((face[kn] + sn * 0.2, face[kn] + sn * (0.2 + tun[0])))
    tl[2], th[2] = z - tun[1] / 2, z + tun[1] / 2
    return one(blk - C.box(tl[0], th[0], tl[1], th[1], tl[2], th[2]))


def _tower():
    """analytic part of T_spodok above the floor: (positive solids, local cutters applied before the fuse, global cutters)"""
    P, N = [], []
    zw0 = ZF - 0.3
    # ---- cradle walls: +Y (back), -Y (front, recessed between the two servos), -X end wall; bumper
    P.append(C.box(X0, X1, YI, YO, zw0, ZD0))
    Rc = RAM2["FRONT_RECESS"]
    front = C.box(X0, X1, -YO, -YI, zw0, ZD0) - C.box(Rc["x"][0], Rc["x"][1], -YO - 0.5, Rc["y_face"], Rc["z"][0], ZD0 + 0.5)
    front = front - C.box(-Rc["tab_x"], Rc["tab_x"], -YO - 0.5, Rc["y_face"], *Rc["tab_z"])     # STS3032 tabs (x +-16.25)
    P.append(one(front))
    P.append(C.box(X0, XE, -YO, YO, zw0, ZD0))
    Bu = RAM2["BUMPER"]
    P.append(C.box(*Bu["x"], *Bu["y"], *Bu["z"]))
    # roots of the cradle walls on the floor (R2 outside; inside = pocket / window, no floor)
    P.append(fil("T_spodok", "+Y wall / floor", "x", X0, X1, (0, YO, ZF), "+y", "+z", 2.0))
    P.append(fil("T_spodok", "-Y wall / floor", "x", X0, X1, (0, -YO, ZF), "-y", "+z", 2.0))
    P.append(fil("T_spodok", "-X end wall / floor", "y", -YO, YO, (X0, 0, ZF), "-x", "+z", 2.0))
    for sy in (1, -1):                                   # inner vertical corners end wall / long walls (servo corner R1)
        P.append(fil("T_spodok", f"end wall / long wall {sy:+d} (inside, R0.5: servo case corner 0.2 away)", "z", -83.3, ZD0,
                     (XE, sy * YI, 0), "+x", "-y" if sy > 0 else "+y", 0.5))
    # ---- bridges cradle <-> columns at both long walls
    zb0, zb1 = RAM2["BRIDGES_Z"]
    for sy in (1, -1):
        ya, yb = (YI, YO) if sy > 0 else (-YO, -YI)
        P += [C.box(X1 - 0.2, C.X_COL_IN + 0.1, ya, yb, zb0, zb1), C.box(-C.X_COL_IN - 0.1, X0 + 0.2, ya, yb, zb0, zb1)]
    # ---- columns
    Ng = []
    for s in (1, -1):
        p, n = _column(s); P += p; Ng += n
    # ---- pan-servo posts (6 x 10 under the tabs), DIN 562 slots through in x, +X post with plug window + front leg
    Pp = RAM2["PAN_POST"]
    yt = PAX[1]
    for s in (1, -1):
        post = C.box(s * Pp["x"][0], s * Pp["x"][1], Pp["y"][0], Pp["y"][1] + 0.1, zw0, Pp["top"]) if s > 0 else \
            C.box(-Pp["x"][1], -Pp["x"][0], Pp["y"][0], Pp["y"][1] + 0.1, zw0, Pp["top"])
        if s > 0:
            W = Pp["window"]; Lg = Pp["leg"]
            post = one(post - C.box(Pp["x"][0] - 0.5, Pp["x"][1] + 0.5, W["y"][0] - 0.2, W["y"][1], *W["z"]))
            post = one(post.fuse(C.box(Lg["x"][0], Lg["x"][1], Lg["y"][0], Lg["y"][1] + 0.1, zw0, Pp["top"])))
        P.append(post)
        xin, xout = s * Pp["x"][0], s * Pp["x"][1]
        P.append(fil("T_spodok", f"pan post {s:+d} outer / front wall", "z", ZF, Pp["top"], (xout, -YO, 0),
                     "+x" if s > 0 else "-x", "-y", 1.0))
        P.append(fil("T_spodok", f"pan post {s:+d} inner / front wall", "z", ZF, Rc["z"][0], (xin, -YO, 0),
                     "-x" if s > 0 else "+x", "-y", 1.0))
        P.append(fil("T_spodok", f"pan post {s:+d} outer / floor", "y", Pp["y"][0], -YO,
                     (xout, 0, ZF), "+x" if s > 0 else "-x", "+z", 1.0))
        hx = s * 14.0
        Ns = Pp["nut_slot"]
        # integrator rev2: the -X post is merged with the post-2 column -> its slot ends at the post face (nut entered from +X)
        Ng.append(C.box(min(xin, xout) - (0.5 if s > 0 else 0.0), max(xin, xout) + 0.5, yt - Ns["y_half"], yt + Ns["y_half"], *Ns["z"]))
        Ng.append(slot_hole(Pp["hole_d"], (hx, yt, Pp["top"]), "z", -1, 8.5, (C_DIR[0], C_DIR[1], 0.0), Pp["slot"]))
    # ---- stop-pin posts (Ø7) + pin holes; post 2 = block tied to the -X end wall
    Sp = RAM2["STOP_POSTS"]; St = R2["STOP"]
    (p1x, p1y), (p2x, p2y) = St["pin_xy"]
    P.append(C.cyl_z(Sp["r"], zw0, Sp["top"], p1x, p1y))
    P.append(C.box(X1 - 0.2, p1x, YI, YO, zw0, ZD0))                              # long wall carried on into post 1
    P.append(cove("T_spodok", "stop post 1 / floor", "z", (p1x, p1y), Sp["r"], 2.0, ZF, 1, record_at=-30.0))
    z20, z21 = Sp["p2_z"]
    Bk = Sp["p2_block"]
    Kc = Sp["p2_column"]
    P += [C.cyl_z(Sp["r"], z20, z21, p2x, p2y), C.box(Bk["x"][0], Bk["x"][1], Bk["y"][0], Bk["y"][1] + 0.1, z20, z21),
          C.box(Kc["x"][0], Kc["x"][1], Kc["y"][0], Kc["y"][1] + 0.1, zw0, Kc["z_top"] + 0.1)]
    P.append(fil("T_spodok", "post-2 column / floor (front face)", "x", Kc["x"][0], Kc["x"][1], (0, Kc["y"][0], ZF), "-y", "+z", 1.0))
    P.append(fil("T_spodok", "post-2 column / floor (-X face)", "y", Kc["y"][0], -YO, (Kc["x"][0], 0, ZF), "-x", "+z", 1.0))
    P.append(fil("T_spodok", "post-2 column / front wall (-X side)", "z", ZF, z21, (Kc["x"][0], -YO, 0), "-x", "-y", 1.0))
    for x, y in St["pin_xy"]:
        Ng.append(hole(Sp["pin_hole_d"], (x, y, Sp["top"]), "z", -1, Sp["pin_bond"] + 0.3))
    # ---- insert bosses F3a / F3b (stadium into the wall / web)
    bosses = [("F3a (26,-11.7)", 26.0, -11.7, dict(wall_face_y=-YI)), ("F3a (30.6,4)", RAM2["F3A"][1][0], RAM2["F3A"][1][1],
                                                                       dict(wall_face_x=C.X_COL_IN + 0.05, corbel=True)),
              ("F3b (6,15.95)", 6.0, 15.95, dict(wall_face_y=YO)), ("F3b (18.5,-15.95)", 18.5, -15.95, dict(wall_face_y=-YO))]
    for nm, x, y, kw in bosses:
        p, n = _boss(nm, x, y, **kw); P += p; Ng += n
    # ---- carrier standoffs (F7, bonded M2 inserts along -Y)
    xr, zr, rr = CT["rest_pad"]
    P.append(C.cyl_y(rr, YO - 0.2, CT["f7_face"], xr, zr))                     # +X end of the carrier rests here (no screw)
    P.append(cove("T_spodok", "carrier rest pad / wall", "y", (xr, zr), rr, 1.0, YO, 1, record_at=-90.0))
    rb7 = R2["INSERT_HOLES"]["M2"]["boss_r"]      # fixer rev2 (S5): standoff r 3.25 -> 3.65 (wall 1.6 around the D4.1 hole of the 4 x 4 insert)
    for x, z in CT["f7"]:
        P.append(C.cyl_y(rb7, YO - 0.2, CT["f7_face"], x, z))
        P.append(cove("T_spodok", f"F7 standoff x {x} / wall", "y", (x, z), rb7, 1.0, YO, 1, record_at=-90.0))
        Ng += [hole(R2["INSERT_HOLES"]["M2"]["hole"], (x, CT["f7_face"], z), "y", -1, CT["f7_face"] - YI + 0.3)]   # D4.1 through (3.95)
    # ---- capacitor pedestal (trough r 4.1, 180 deg) + tie groove 2.8 x 1.2 under the can
    K = RAM2["CAP"]
    ped = C.box(K["pedestal_x"][0], K["pedestal_x"][1], K["y"] - K["half_w"], K["y"] + K["half_w"], zw0, K["z"])
    ped = one(ped - C.cyl_x(K["trough_r"], K["pedestal_x"][0] - 1, K["pedestal_x"][1] + 1, K["y"], K["z"]))
    gx = 0.5 * (K["pedestal_x"][0] + K["pedestal_x"][1])
    ped = one(ped - C.box(gx - K["groove"][0] / 2, gx + K["groove"][0] / 2, K["y"] - 5, K["y"] + 5, ZF, K["z"] - K["trough_r"] + 0.4))
    P.append(ped)
    # ---- tie saddles
    for T in RAM2["TIE_SADDLES"]:
        P.append(_tie_saddle(T["face"], T["n"], T["along"], h=T["h"], tun=T["tun"]))
    # ---- local cutters (keep-outs) applied to the tower before the fuse
    F1 = RAM2["F1"]
    Nl = _f1_keepouts_tower(F1["keepout_z"][0], F1["keepout_z"][1])
    return P, Nl, Ng


def _f1_keepouts_tower(z0, z1):
    """integrator rev2: the path of the T_stred F1 boss columns for the tower above the spigot: the boss cylinder r 3.4 + 0.25
    toward the tower (measured on T_stred: the footprint toward the tower is the r 3.40 cylinder) + the outward web band
    |y| >= 19 (the webs run from the boss toward the shell).  Lowering step T5 (K7: exact plan clearance >= 0.25)."""
    K = RAM2["F1"]["keepout"]; out = []
    for sx in (1, -1):
        for sy in (1, -1):
            out.append(C.cyl_z(3.65, z0, z1, sx * 29.0, sy * 19.0))
            out.append(C.box(min(sx * K["x"][0], sx * K["x"][1]), max(sx * K["x"][0], sx * K["x"][1]),
                             min(sy * 19.0, sy * 40.0), max(sy * 19.0, sy * 40.0), z0, z1))
    return out


def _f1_keepouts(z0, z1):
    K = RAM2["F1"]["keepout"]
    return [C.box(min(sx * K["x"][0], sx * K["x"][1]), max(sx * K["x"][0], sx * K["x"][1]),
                  min(sy * K["y_min"], sy * 40.0), max(sy * K["y_min"], sy * 40.0), z0, z1) for sx in (1, -1) for sy in (1, -1)]


@timed("T_spodok")
def mk_spodok(verbose=True):
    def step(msg, t0):
        if verbose:
            print(f"    spodok: {msg} {time.time() - t0:.1f} s", flush=True)
    t = time.time()
    cap = cap_stage_A()
    step("cap stage A (cached loft)", t)
    # ---- pocket + window under the J1 servo (4 corner pads stay)
    t = time.time()
    Pk, W = RAM2["J1_POCKET"], RAM2["J1_WINDOW"]
    pocket = C.box(*Pk["x"], *Pk["y"], Pk["z"][0], Pk["z"][1] + 0.3)
    window = one(C.box(W["x"][0], W["x"][1], W["y"][0], W["y"][1], ZB - 2.0, Pk["z"][0] + 0.01).cut(*_pads_J1()))
    cap = one(cap.cut(pocket, window))
    step("- pocket - window", t)
    # ---- tower + plinth / foot ring / lug + F1 pads, one fuse
    t = time.time()
    P, Nl, Ng = _tower()
    tower = fuse(P).cut(*Nl)                     # NOT one(): the bumper / capacitor pedestal touch only the cap floor
    tsol = list(tower.solids())
    step(f"tower fused ({len(P)} solids -> {len(tsol)} bodies)", t)
    t = time.time()
    cap = cap.fuse(*tsol, *_under(), *_f1_pads())
    assert len(cap.solids()) == 1, f"T_spodok: {len(cap.solids())} bodies after the fuse {[round(q.volume, 1) for q in cap.solids()]}"
    cap = one(cap)
    step("+ tower, plinth, ring, lug, F1 pads", t)
    # ---- global cutters
    t = time.time()
    Pa = R2["J1"]
    N = list(Ng)
    N.append(_j1_pass(C.RAM["J1_PASS"]["r"], -91.0, -83.1))
    F1 = RAM2["F1"]
    for x, y in F1["at"]:
        N += [C.cyl_z(F1["hole_d"] / 2, ZB - 1.0, C.Z_WHITE + 0.5, x, y), C.cyl_z(F1["cb_d"] / 2, ZB - 3.0, F1["cb_z"], x, y)]
    N += _f1_keepouts(C.Z_WHITE, -77.0)                                              # spigot notches 7.8 wide
    S = RAM2["BASE_FFC_SLOT"]
    N.append(tube_sector(S["r"][1], S["r"][0], S["az"][0], S["az"][1], S["z"][0] - 0.5, S["z"][1] + 0.5))
    N += [C.cyl_z(1.5, ZB - 1.0, ZF + 0.5, x, y) for x, y in RAM2["DRAINS"]]
    N += [C.cyl_z(d / 2, ZB - 1.0, ztop, x, y) for d, x, y, ztop in RAM2["CUP_VENTS"]]           # fixer rev2 M3
    F16 = RAM2["F16"]
    N += [slot_hole(F16["hole_d"], (x, y, ZB), "z", 1, 1.3, (1.0, 0.0, 0.0), F16["slot"]) for x, y in F16["at"]]
    Ws = RAM2["WALL_FFC_SLOT"]
    N.append(C.box(Ws["x"][0], Ws["x"][1], YI - 0.3, YO + 0.3, *Ws["z"]))
    N.append(prism_x([(YI - 0.3, Ws["z"][1] - 0.01), (YI + 0.8, Ws["z"][1] - 0.01), (YI - 0.3, Ws["z"][1] + 1.1)], Ws["x"][0], Ws["x"][1]))
    N.append(C.box(18.9, 20.7, YI - 0.3, YI + 1.05, Ws["z"][1] - 0.1, ZD0 + 0.3))
    #   integrator rev2: notch in the inner half of the wall above the slot where the FFC pair rises to the deck slot (B az 32..34:
    #   the strip reached y 12.96, 0.1 into the wall; RAM X / K2)
    #   0.8 x 45 deg chamfer on the inner top edge: the FFC pair turns up toward the deck slot there
    cap = cap.cut(*N)
    assert len(cap.solids()) == 1, f"T_spodok: {len(cap.solids())} bodies after the cuts {[round(q.volume, 1) for q in cap.solids()]}"
    cap = one(cap)
    step(f"- {len(N)} global cutters", t)
    return cap.clean()


# =====================================================================================================================
# T_paluba (deck lid), T_most (Al pivot bridge), T_cap (pivot boss)
# =====================================================================================================================
def most_outline(grow=0.0):
    return hull_circles(RAM2["MOST"]["circles"], grow)


@timed("T_paluba")
def mk_paluba():
    z0, z1 = ZD0, ZD1
    F = R2["FFC"]
    lobe = one(C.cyl_z(F["wall"][1], z0, z1) & C.box(-26.0, 26.0, 0.0, 26.0, z0 - 1, z1 + 1))
    right = C.box(10.0, 34.2, -17.8, YO, z0, z1)
    P = [lobe, right, C.cyl_z(3.2, z0, z1, *RAM2["F3A"][1]), C.cyl_z(4.0, z0, z1, *RAM2["F3A"][0]), C.cyl_z(4.5, z0, z1, *R2["STOP"]["pin_xy"][0])]
    body = fuse(P)
    assert len(body.solids()) == 1, f"T_paluba: {len(body.solids())} bodies before the cuts"
    body = one(body)
    T = RAM2["DECK_TRIM"]
    N = [tube_sector(45.0, T["r"], T["az"][0], T["az"][1], z0 - 0.5, z1 + 0.5),
         prism_z(most_outline(0.1), z0 - 0.5, z1 + 0.5),
         C.box(34.2, 50.0, -30, 30, z0 - 0.5, z1 + 0.5),                       # 0.2 to the left column web
         C.box(9.0, 15.6, -18.5, -14.0, z0 - 0.5, z1 + 0.5)]                   # sliver left of the T_most front lobe
    # integrator rev2 (K7 T3): the deck goes in from above past the +X shoulder plate (inner face r 34.5 for |y| > 9.5, flat 34.5
    # inside): keep 0.3 off its footprint over the whole lowering
    N.append(C.box(20.0, 40.0, -30.0, 30.0, z0 - 0.5, z1 + 0.5) - C.cyl_z(34.1, z0 - 1.0, z1 + 1.0))   # fixer rev2: r 34.1 at every y
    N += _f1_keepouts_tower(z0 - 0.5, z1 + 0.5)                               # integrator rev2: F1 boss path (T_stred lowering)
    N += [b for b in _f1_keepouts(z0 - 0.5, z1 + 0.5) if b.bounding_box().max.Y < 0]   # front bosses: the 0.5 box (no C-ear there)
    N.append(tube_sector(F["deck_slot"]["r"][1], F["deck_slot"]["r"][0], *F["deck_slot"]["az"], z0 - 0.5, z1 + 0.5))
    N += [hole(2.8, (x, y, z1), "z", -1, 2.5) for x, y in RAM2["F3A"]]
    N.append(C.cyl_z(R2["STOP"]["pin_d"] / 2 + 0.05, z0 - 0.5, z1 + 0.5, *R2["STOP"]["pin_xy"][0]))
    body = cut(body, N)
    assert len(body.solids()) == 1, f"T_paluba: {len(body.solids())} bodies"
    body = one(body)
    wall = tube_sector(F["wall"][1], F["wall"][0], F["wall_az"][0], F["wall_az"][1], z1 - 0.2, F["wall_top"])
    rootc = cove("T_paluba", "FFC wall outer / deck (az 15..40, where the deck reaches beyond r 26.1)", "z", (0.0, 0.0),
                 F["wall"][1], 1.0, z1, 1, record_at=22.0)
    rootc = one(rootc & wedge_z(F["wall"][1] + 1.2, F["wall_az"][0], 40.0, z1 - 1, z1 + 2))
    return one(body.fuse(wall, rootc)).clean()


def mk_most():
    """T_most: aluminium 5754-H22 / 6061-T6 sheet 2.0, outline = hull of circles (R >= 2.5 everywhere), M3 tapped at (0, 0)
    (drill 2.5), 2 x D2.8 with 90 deg countersink D5.2 for DIN 7991 M2.5 (F3b)"""
    M = RAM2["MOST"]
    s = prism_z(most_outline(), ZD0, ZD1)
    N = [C.cyl_z(M["tap_d"] / 2, ZD0 - 0.5, ZD1 + 0.5)]
    cs = M["csk"]
    for x, y in RAM2["F3B"]:
        k = (cs["dk"] - cs["d"]) / 2
        N += [C.cyl_z(cs["d"] / 2, ZD0 - 0.5, ZD1 + 0.5, x, y),
              bd.Pos(x, y, ZD1 - k / 2 + 0.001) * bd.Cone(cs["d"] / 2, cs["dk"] / 2, k)]
    return one(cut(s, N))


def mk_cap():
    """T_cap: resin boss D7.70 x 4.40 (z -46.2..-41.8), D3.1 hole (drilled after curing), top edges R0.3, root flare R1.0 (rev3);
    bonded on T_most"""
    B = RAM2["CAP_BOSS"]
    z0, z1 = B["z"]
    c = C.cyl_z(B["r"], z0, z1)
    c = bd.fillet(c.edges().filter_by(bd.GeomType.CIRCLE).group_by(bd.Axis.Z)[-1], B["edge_r"])
    fl = cove("T_cap", "T_cap root flare", "z", (0.0, 0.0), B["r"], B["flare_r"], z0, 1, record_at=0.0)
    s = one(c.fuse(fl))
    return one(s - C.cyl_z(B["hole_d"] / 2, z0 - 0.5, z1 + 0.5))


# =====================================================================================================================
# Z_naboj_test - dummy base hub (bench stand), rev. 1 + rev. 2 sun-gear plane / stop block
# =====================================================================================================================
DUMMY = dict(C.RAM["DUMMY"])
DUMMY["stop"] = dict(az=R2["J1"]["base_stop"]["az"], half=R2["J1"]["base_stop"]["half"], r=(17.0, 23.0), z_top=-99.3)
#   block top -99.3 (rev. 1 -98.3): the R1 root fillets of the lug occupy z -99..-98; engagement -102..-99.3 = 2.7


@timed("Z_naboj_test")
def mk_naboj():
    D = DUMMY
    w, d = D["plate"]; z0, z1 = D["plate_z"]; Pd = D["pedestal"]; zp = Pd["z_top"]
    P = [C.rbox(-w / 2, w / 2, -d / 2, d / 2, z0, z1, 8.0, "z"), C.cyl_z(Pd["r"], z1 - 0.2, zp)]
    P += [C.cyl_z(D["shoulder_r"], zp - 0.2, C.Z_BRG[0]), C.cyl_z(D["post_r"], C.Z_BRG[0] - 0.2, C.Z_BRG[1]),
          C.cyl_z(D["stub"][0], C.Z_BRG[1] - 0.2, R2["J1"]["gear_plane"][0])]
    St = D["stop"]
    P.append(tube_sector(St["r"][1], St["r"][0], St["az"] - St["half"], St["az"] + St["half"], zp - 0.2, St["z_top"]))
    body = one(fuse(P))
    Sk = D["socket"]; dr = Sk["r"] - D["cbore_r"]
    zc = Sk["z_top"] + dr; h = zc - (z0 - 1.0)
    relief = one(C.cyl_z(Sk["r"], z0 - 1.0, zc) & (bd.Pos(0, 0, z0 - 1.0 + h / 2) * bd.Cone(D["cbore_r"] + h, D["cbore_r"], h)))
    N = [C.cyl_z(4.1, z0 - 5, R2["J1"]["gear_plane"][0] + 1), C.cyl_z(D["cbore_r"], z0 - 1, D["seat_z"]), relief]
    return one(cut(body, N)).clean()


def mk_skrutka_M8():
    D = DUMMY; zh = D["bolt_head_z"]
    hexa = prism_z([pol(13.0 / 2 / math.cos(math.radians(30)), 60 * i) for i in range(6)], zh - 5.3, zh)
    return one(fuse([hexa, C.cyl_z(4.0, zh - 0.2, R2["J1"]["gear_plane"][1])]))


def mk_pruzina(i):
    D = DUMMY; z = D["bolt_head_z"] + 0.6 * i
    return one(C.cyl_z(8.0, z, z + 0.6) - C.cyl_z(4.1, z - 0.2, z + 0.8))


# =====================================================================================================================
# fasteners (screws, washers, bonded inserts, nuts)
# =====================================================================================================================
def fasteners():
    F = {}

    def add(name, solid, mat, label, **rec):
        F[name] = (solid, mat, label, rec)
    # F1 T_spodok -> T_stred (from below): washer on the counterbore floor, ISO 7380 M2.5x6
    zc = RAM2["F1"]["cb_z"]; t = WASH["M2.5"][2]
    for i, (x, y) in enumerate(RAM2["F1"]["at"], 1):
        add(f"skr_F1_{i}", screw_btn("M2.5", 6, (x, y, zc - t), "z", 1), "steel", "skrutka ISO 7380 M2,5x6 (spodok -> stred)",
            joint="F1", size="ISO 7380 M2.5x6", head=(x, y, zc - t), dir="+Z", tool_from="-Z", torque=R2["TORQUE"]["M25_insert"])
        add(f"pd_F1_{i}", washer("M2.5", (x, y, zc), "z", 1), "steel", "podložka DIN 125 M2,5", joint="F1")
    # F3a deck -> T_spodok
    for i, (x, y) in enumerate(RAM2["F3A"], 1):
        add(f"skr_F3a_{i}", screw_btn("M2.5", 6, (x, y, ZD1 + 0.5), "z", -1), "steel", "skrutka ISO 7380 M2,5x6 (paluba -> spodok)",
            joint="F3a", size="ISO 7380 M2.5x6", head=(x, y, ZD1 + 0.5), dir="-Z", tool_from="+Z", torque=R2["TORQUE"]["M25_insert"])
        add(f"pd_F3a_{i}", washer("M2.5", (x, y, ZD1), "z", -1), "steel", "podložka DIN 125 M2,5", joint="F3a")
        add(f"vl_F3a_{i}", C.insert("M2.5", (x, y, ZD0), "z", -1), "brass", "závitová vložka M2,5 lepená (spodok)", joint="F3a", at=(x, y, ZD0))
    # F3b T_most -> T_spodok: countersunk flush in the aluminium
    for i, (x, y) in enumerate(RAM2["F3B"], 1):
        add(f"skr_F3b_{i}", screw_csk90(2.5, 5.0, 6.0, (x, y, ZD1), "z", -1), "steel", "skrutka DIN 7991 M2,5x6 zápustná (do hliníka T_most)",
            joint="F3b", size="DIN 7991 M2.5x6", head=(x, y, ZD1), dir="-Z", tool_from="+Z", torque=R2["TORQUE"]["M25_insert"])
        add(f"vl_F3b_{i}", C.insert("M2.5", (x, y, ZD0), "z", -1), "brass", "závitová vložka M2,5 lepená (spodok)", joint="F3b", at=(x, y, ZD0))
    # F4 pan servo: ISO 7380 M2x10 + DIN 125 on the tab, DIN 562 nut in the post
    zt = PAN_TAB_Z[1]; tw = WASH["M2"][2]
    for i, sx in enumerate((-1, 1), 1):
        x = sx * 14.0; y = PAX[1]
        add(f"skr_F4_{i}", screw_btn("M2", 10, (x, y, zt), "z", -1), "steel", "skrutka ISO 7380 M2x10 (servo pan, hlava na úchytke serva)",
            joint="F4", size="ISO 7380 M2x10, no washer (head on the servo's own tab; a D5 washer would overlap the case 0.25)",
            head=(x, y, zt), dir="-Z", tool_from="+Z through the T_stred bore, before the stage", torque=C.FIX2["TQ_DESIGN"])
        add(f"mat_F4_{i}", nut562((x, y, RAM2["PAN_POST"]["nut_slot"]["z"][1])), "steel", "matica DIN 562 M2 štvorhranná", joint="F4")
    # F7 carrier
    for i, (x, z) in enumerate(CT["f7"], 1):
        add(f"skr_F7_{i}", screw_csk90(2.0, 3.8, 5.0, (x, YPCB1, z), "y", -1), "steel", "skrutka DIN 7991 M2x5 zápustná (v DPS, riadiaca doska)",
            joint="F7", size="DIN 7991 M2x5 (flush in the FR4 countersink)", head=(x, YPCB1, z), dir="-Y", tool_from="+Y (door, no USB plug in)",
            torque=R2["TORQUE"]["M2_insert"])
        add(f"vl_F7_{i}", C.insert("M2", (x, CT["f7_face"], z), "y", -1), "brass", "závitová vložka M2x4 OD4,0 lepená (spodok)", joint="F7",
            at=(x, CT["f7_face"], z))
    # F8 inserts in the column bosses (the screws belong to T_klb, OBAL)
    for s, tag in ((1, "L"), (-1, "P")):
        for i, az in enumerate(R2["COLUMN"]["f8_az"], 1):
            dy, dz = pol(7.5, az)
            at = (s * C.X_COL_BOSS, SHY + dy, SHZ + dz)
            add(f"vl_F8_{tag}{i}", C.insert("M2", at, "x", -s), "brass", "závitová vložka M2x4 OD4,0 lepená (náboj ramena)", joint="F8", at=at)
    # F14 buck / amplifier: M2x6 thread-forming one-time + DIN 125
    xb = R2["BUCK_X"][1] - 1.6
    for i, (y, z) in enumerate(BUCK_HOLES, 1):
        add(f"skr_F14_{i}", screw_btn("M2tf", 6, (xb - 0.3, y, z), "x", 1), "steel", "skrutka M2x6 do plastu (menič), jednorazová",
            joint="F14", size="M2x6 thread-forming", head=(xb - 0.3, y, z), dir="+X", tool_from="-X (side cap off)", torque=R2["TORQUE"]["M2_thread_forming"])
        add(f"pd_F14_{i}", washer("M2", (xb, y, z), "x", 1), "steel", "podložka DIN 125 M2", joint="F14")
    xa = R2["AMP_X"][0] + 1.6
    for i, (y, z) in enumerate(AMP_HOLES, 3):
        add(f"skr_F14_{i}", screw_btn("M2tf", 6, (xa + 0.3, y, z), "x", -1), "steel", "skrutka M2x6 do plastu (zosilňovač), jednorazová",
            joint="F14", size="M2x6 thread-forming", head=(xa + 0.3, y, z), dir="-X", tool_from="+X (side cap off)", torque=R2["TORQUE"]["M2_thread_forming"])
        add(f"pd_F14_{i}", washer("M2", (xa, y, z), "x", -1), "steel", "podložka DIN 125 M2", joint="F14")
    # F15 pivot (rev3): 2 x DIN 125 M3 (spacers) + DIN 9021 M3 (retention washer over the hub lip of the well) on T_cap,
    # ISO 7380 M3x8 into the tapped T_most
    F5 = RAM2["F15"]; hz = F5["head"][0]; wz = F5["washer"][2]; L15 = int(F5["length"])
    add("skr_F15", screw_btn("M3", L15, (0.0, 0.0, hz), "z", -1), "steel", f"skrutka ISO 7380 M3x{L15} (čap pan, do T_most)",
        joint="F15", size=f"ISO 7380 M3x{L15}", head=(0.0, 0.0, hz), dir="-Z", tool_from="+Z (through the empty well)", torque=C.FIX2["TQ_DESIGN"])
    add("pd_F15", one(C.cyl_z(F5["washer"][1], *wz) - C.cyl_z(1.6, wz[0] - 0.2, wz[1] + 0.2)), "steel",
        "podložka DIN 9021 M3 (3,2 x 9 x 0,8) – drží šachtu za golier náboja", joint="F15")
    ri_, ro_, ts_ = F5["spacer"]
    for i in (1, 2):
        za = F5["spacer_z"][0] + (i - 1) * ts_
        add(f"pd_F15_d{i}", one(C.cyl_z(ro_, za, za + ts_) - C.cyl_z(ri_, za - 0.2, za + ts_ + 0.2)), "steel",
            "podložka DIN 125 M3 (3,2 x 7 x 0,5) – dištančná pod DIN 9021", joint="F15")
    # F16 J1 servo (from below, the 2 -X pads)
    for i, (x, y) in enumerate(RAM2["F16"]["at"], 1):
        add(f"skr_F16_{i}", screw_btn("M2", 6, (x, y, ZB - 0.3), "z", 1), "steel", "skrutka ISO 7380 M2x6 (servo J1, zospodu)",
            joint="F16", size="ISO 7380 M2x6", head=(x, y, ZB - 0.3), dir="+Z", tool_from="-Z (torso off the base)", torque=R2["TORQUE"]["J1_pads"])
        add(f"pd_F16_{i}", washer("M2", (x, y, ZB), "z", 1), "steel", "podložka DIN 125 M2", joint="F16")
    return F


# =====================================================================================================================
# registry
# =====================================================================================================================
PRINTED = {   # name: (builder, group, material, Slovak label)
    "T_spodok": (lambda: mk_spodok(), "T", "resin_black", "spodok: kryt, pätka J1, kolíska serva J1, stĺpy ramien, stĺpiky (živica Tough)"),
    "T_paluba": (lambda: mk_paluba(), "T", "resin_black", "paluba (servisné veko J1): stena a štrbina FFC, ucho kolíka 1"),
    "T_cap": (lambda: mk_cap(), "T", "resin_black", "čap pan (živica) - lepený na T_most, s PTFE páskou"),
    "Z_naboj_test": (lambda: mk_naboj(), "Z", "resin_black", "skúšobný náboj podstavca (stojan)"),
}


def _base_text():
    return open(os.path.join(HERE, "t4_common.py")).read().split("# >>> additions by ram")[0]


def _src_hash():
    src = open(os.path.abspath(__file__)).read() + json.dumps(R2, sort_keys=True, default=str) + _base_text()
    return hashlib.md5(src.encode()).hexdigest()[:10]


def printed_part(name, rebuild=False):
    fn = PRINTED[name][0]
    p = os.path.join(C.CACHE, f"ram2_{name}_{_src_hash()}.brep")
    if os.path.exists(p) and not rebuild:
        TIMES[name] = 0.0
        return one(bd.import_brep(p))
    t = time.time(); s = fn(); TIMES[name] = round(time.time() - t, 1)
    for old in os.listdir(C.CACHE):
        if old.startswith(f"ram2_{name}_") and old.endswith(".brep"):
            os.remove(os.path.join(C.CACHE, old))
    bd.export_brep(s, p)
    return s


def build(rebuild=False, verbose=False):
    """registry of the RAM module (rev. 2): dict[name] = t4_common.part(...)"""
    ROOTS.clear()
    parts = {}
    for name, (fn, grp, mat, label) in PRINTED.items():
        s = printed_part(name, rebuild)
        parts[name] = C.part(s, grp, mat, True, label, **({"print": PRINT[name]} if name in PRINT else {}))
        if verbose:
            print(f"  built {name} ({TIMES.get(name, 0)} s)", flush=True)
    rp = os.path.join(C.CACHE, f"ram2_roots_{_src_hash()}.json")
    if ROOTS:
        json.dump(ROOTS, open(rp, "w"))
    elif os.path.exists(rp):
        ROOTS.extend(json.load(open(rp)))
    else:                               # all printed parts came from an older cache: record the fillet list again
        _tower(); _under(); mk_paluba(); mk_cap(); json.dump(ROOTS, open(rp, "w"))
    K = RAM2["SHIMS"]
    B = [  # name, builder, group, material, mass g (None = volume x density), label
        ("T_most", mk_most, "T", "alu", None, "most čapu T_most, hliník 2,0 (5754-H22 / 6061-T6), závit M3"),
        ("servo_J1", mk_servo_J1, "T", "bought", 55.0, "servo J1 Feetech STS3215 (hriadeľ dole)"),
        ("pastorok_J1", mk_pastorok_J1, "T", "brass", None, "pastorok J1 m1 z18 mosadz, otvor 6 H7, Loctite 638"),
        ("lozisko_6805", mk_lozisko, "T", "bought", 22.0, "ložisko 6805-2RS 25x37x7 (lepené)"),
        ("servo_pan", mk_servo_pan, "T", "bought", 21.0, "servo pan Feetech STS3032 (hriadeľ hore)"),
        ("pastorok_pan", mk_pastorok_pan, "T", "steel", None, "pastorok pan m0,8 z18 oceľ/mosadz, otvor 5 H7, Loctite 638"),
        ("ptfe_podlozka", mk_ptfe, "T", "ptfe", None, "PTFE podložka 24 x 10 x 0,3"),
        ("ptfe_cap", mk_ptfe_cap, "T", "ptfe", None, "PTFE páska 0,13 na čape (Ø7,96)"),
        ("kolik_dorazu_1", lambda: mk_kolik(0), "T", "steel", None, "kolík dorazu pan ISO 8734 3 m6 x 12 (lepený)"),
        ("kolik_dorazu_2", lambda: mk_kolik(1), "T", "steel", None, "kolík dorazu pan ISO 8734 3 m6 x 12 (lepený)"),
        ("podlozka_J1_1", lambda: C.box(*K["strips"][0][0], *K["strips"][0][1], *K["z"]), "T", "bought", 0.02, "PET podložka 0,1 (výška J1)"),
        ("podlozka_J1_2", lambda: C.box(*K["strips"][1][0], *K["strips"][1][1], *K["z"]), "T", "bought", 0.02, "PET podložka 0,1 (výška J1)"),
        ("podlozka_C_J1", lambda: C.box(*K["c_shim"]["x"], *K["c_shim"]["y"], *K["c_shim"]["z"]), "T", "bought", 0.1,
         "PET podložky 2 x 0,1 (osová vzdialenosť J1 = 18,00)"),
        ("pena_J1_celo", lambda: C.box(*RAM2["PORON_END"]["x"], *RAM2["PORON_END"]["y"], *RAM2["PORON_END"]["z"]), "T", "bought", 0.05,
         "penová podložka PORON 1,0 (čelo serva J1)"),
        ("DPS_riadenie", mk_riadenie, "T", "bought", 9.0, "riadiaca doska s ESP32-S3-Zero (USB-C k +X), ZIF Y5B, konektory zbernice"),
        ("usb_predlzovac", mk_usb_predlzovac, "T", "bought", 2.0, "USB-C predlžovací FPC kábel 90° (samec do ESP32, samica zaparkovaná pri dvierkach)"),
        ("menic", mk_menic, "T", "bought", 2.5, "menič 5 V Pololu D36V28F5"),
        ("zosilnovac", mk_zosilnovac, "T", "bought", 1.5, "zosilňovač Adafruit MAX98357A"),
        ("kondenzator", mk_kondenzator, "T", "bought", 1.5, "kondenzátor 470 µF / 10 V Ø8 x 11,5 (sedlo + sťahovačka)"),
        ("Z_koleso_J1", mk_koleso_J1, "Z", "brass", None, "centrálne koleso J1 m1 z18, mosadz (závit M8)"),
        ("Z_skrutka_M8", mk_skrutka_M8, "Z", "steel", None, "skrutka M8x20 - oceľové jadro náboja a hriadeľ spojky"),
        ("Z_pruzina_1", lambda: mk_pruzina(0), "Z", "steel", None, "tanierová pružina 16x8,2x0,4"),
        ("Z_pruzina_2", lambda: mk_pruzina(1), "Z", "steel", None, "tanierová pružina 16x8,2x0,4"),
    ]
    for name, fn, grp, mat, mass, label in B:
        t = time.time(); s = fn(); TIMES[name] = round(time.time() - t, 2)
        extra = dict(mass=mass) if mass is not None else {}
        parts[name] = C.part(s, grp, mat, False, label, **extra)
    for name, (s, mat, label, rec) in fasteners().items():
        parts[name] = C.part(s, "T", mat, False, label, fastener=rec)
    return parts


def expected_bbox():
    a, b, _ = C.prof(C.TOP - C.Z_CAP_TOP)
    D = DUMMY
    return {
        "T_spodok": (-a, a, -b, b, RAM2["J1_LUG"]["z"][0], SHZ + C.R_COL_STOP[1]),
        "T_cap": (-RAM2["CAP_BOSS"]["r"] - RAM2["CAP_BOSS"]["flare_r"], RAM2["CAP_BOSS"]["r"] + RAM2["CAP_BOSS"]["flare_r"],
                  -RAM2["CAP_BOSS"]["r"] - RAM2["CAP_BOSS"]["flare_r"], RAM2["CAP_BOSS"]["r"] + RAM2["CAP_BOSS"]["flare_r"],
                  *RAM2["CAP_BOSS"]["z"]),
        "Z_naboj_test": (-D["plate"][0] / 2, D["plate"][0] / 2, -D["plate"][1] / 2, D["plate"][1] / 2, D["feet_z"], R2["J1"]["gear_plane"][0]),
    }


SOURCES = {
    "T_most": "custom: aluminium sheet 2.0 EN AW-5754-H22 or 6061-T6 (same sheet as L_ucho), hand cut to the hull outline, "
              "drill 2.5 + tap M3 at (0,0), 2 x D2.8 + 90 deg countersink D5.2",
    "servo_J1": "Feetech STS3215 (listings DFRobot / robotshop / openelab): case 45.2 x 24.7 x 35.0 +-0.3, boss D12 x 2.6, 25T spline "
                "D5.9; spline length 2.2 and case-hole positions / thread UNVERIFIED - measure the purchased servo",
    "pastorok_J1": "brass spur gear m1 18T plain, bore 6 H7, face >= 4 (KHK BSS1-18B or Maedler 263 018 00 - UNVERIFIED shape)",
    "Z_koleso_J1": "brass spur gear m1 18T, face 4, tapped M8 (dummy only)",
    "lozisko_6805": "6805-2RS ISO 15: 25 x 37 x 7; seat D37.15 slide fit + epoxy",
    "servo_pan": "Feetech STS3032 (listings): case 23.5 x 12.5 x 23.0, tabs 32.5 x 2.5, holes D2.2 at 28.0, boss D12.4; spline 25T "
                 "tip D4.95 (UNVERIFIED, check that it is metal)",
    "pastorok_pan": "m0.8 18T plain (no hub), face 4, bore 5 H7, steel (RS PRO 878-7862) or brass (KHK BSS0.8-18) - UNVERIFIED",
    "kolik_dorazu_1": "ISO 8734 3 m6 x 12 hardened dowel", "kolik_dorazu_2": "ISO 8734 3 m6 x 12 hardened dowel",
    "ptfe_podlozka": "PTFE sheet 0.3, washer 24 x 10 cut", "ptfe_cap": "PTFE thread-seal / glide tape 0.13",
    "DPS_riadenie": "custom carrier FR4 55.6 x 18 x 1.6 + Waveshare ESP32-S3-Zero (23.5 x 18, Waveshare drawing) + Hirose "
                    "Panasonic Y5B AYF530535 (5 p 0.5 mm, 0.30 FFC) x2, FH12-10S-1SH(55), 2 x 3-pin 2.50 vertical headers (part numbers UNVERIFIED)",
    "menic": "Pololu D36V28F5 17.8 x 17.8 (Pololu drawing)", "zosilnovac": "Adafruit 3006 MAX98357A 19.3 x 17.8 (Adafruit drawing)",
    "kondenzator": "470 uF 10 V radial D8 x 11.5 (e.g. Panasonic EEU-FR1A471 / Nichicon UPW1A471MPD - size UNVERIFIED)",
    "pena_J1_celo": "PORON 1.0", "podlozka_J1_1": "PET film 0.1", "podlozka_J1_2": "PET film 0.1", "podlozka_C_J1": "PET film 0.1 x 2",
    "Z_skrutka_M8": "ISO 4017 M8 x 20", "Z_pruzina_1": "DIN 2093 16 x 8.2 x 0.4", "Z_pruzina_2": "DIN 2093 16 x 8.2 x 0.4",
}
ASSEMBLY = {   # spec 17.11 (B = bench group, T = torso step)
    "T_spodok": ("B1", "drill / ream, bond inserts, pins, 6805"), "lozisko_6805": ("B1", "+Z from below into the D37.15 seat, epoxy"),
    "kolik_dorazu_1": ("B1", "-Z into the post, epoxy, 24 h"), "kolik_dorazu_2": ("B1", "-Z into the post, epoxy, 24 h"),
    "T_most": ("B2", "cut, drill, tap"), "T_cap": ("B2", "bonded on T_most, centred by a temporary M3"), "ptfe_cap": ("B2", "wrapped on T_cap"),
    "pastorok_J1": ("B7", "on the STS3215 spline, Loctite 638"), "pastorok_pan": ("B7", "on the STS3032 spline, Loctite 638"),
    "servo_J1": ("T1", "-Z into the cradle (pinion through J1_PASS); F16 x2 from below; C 18.00 with podlozka_C_J1"),
    "pena_J1_celo": ("T1", "with the servo"), "podlozka_C_J1": ("T1", "between case -X end and the end wall"),
    "servo_pan": ("T2", "-Z onto the posts, F4 loose"), "podlozka_J1_1": ("T3", "on the STS3215 top"), "podlozka_J1_2": ("T3", "on the STS3215 top"),
    "T_paluba": ("T3", "-Z, F3a x2 (C-ear over pin 1)"), "ptfe_podlozka": ("T3", "on T_most around T_cap"),
    "DPS_riadenie": ("T4", "-Y through the door, F7 x2"), "menic": ("T4", "+X onto the right web, F14"), "zosilnovac": ("T4", "-X onto the left web, F14"),
    "kondenzator": ("T4", "into the saddle, cable tie"), "Z_naboj_test": ("bench", "torso lowered onto it -Z"),
}
STEP_MAX_MB = 12.0


def _export(name, p):
    """STL with ABSOLUTE deflection 0.01 (t4_obal.export_abs); STEP only below 12 MB"""
    try:
        import t4_obal as O
        return O.export_abs(name, p, HERE, do_step=True)
    except AssertionError as ex:         # t4_obal self-sync failed (OBAL edits in progress) -> same routine, local copy
        print("   t4_obal import failed:", ex, "-> local export", flush=True)
        raise


def main(argv):
    rebuild = "--rebuild" in argv
    T0 = time.time()
    print("== t4_ram rev. 2: build ==", flush=True)
    parts = build(rebuild, verbose=True)
    print(f"build {time.time() - T0:.1f} s, {len(parts)} parts", flush=True)
    exp = expected_bbox()
    recs, bad = [], []
    print(f"{'part':22s} {'grp':3s} {'mat':11s} valid sol {'volume':>10s}  bbox x / y / z{'':38s} build s")
    for name, p in parts.items():
        r = C.check_part(name, p)
        if name in exp:
            r["bbox_expected"] = [round(v, 3) for v in exp[name]]
            r["bbox_ok"] = all(abs(u - v) <= 0.06 for u, v in zip(r["bbox"], exp[name]))
            r["ok"] = r["ok"] and r["bbox_ok"]
        r["build_s"] = TIMES.get(name, 0.0)
        b = r["bbox"]
        print(f"{name:22s} {p['group']:3s} {p['mat']:11s} {str(r['valid'])[0]}     {r['n_solids']}  {r['volume']:10.1f}  "
              f"{b[0]:7.2f}..{b[1]:7.2f} / {b[2]:7.2f}..{b[3]:7.2f} / {b[4]:8.2f}..{b[5]:7.2f}  {r['build_s']:5.1f}"
              + ("" if r["ok"] else "   <-- NOT OK"), flush=True)
        if not r["ok"]:
            bad.append(name)
        recs.append((name, p, r))
    if "--noexport" in argv:
        print("not exported; NOT OK:", bad)
        return 1 if bad else 0
    t = time.time()
    pj = os.path.join(HERE, "parts_ram.json")
    old_names = [e["name"] for e in json.load(open(pj))["parts"]] if os.path.exists(pj) else []
    out = []
    for name, p, r in recs:
        e = _export(name, p)
        e["build_s"] = r["build_s"]
        for k in ("bbox_expected", "bbox_ok"):
            if k in r:
                e[k] = r[k]
        e["ok"] = bool(e["ok"] and r["ok"])
        if "fastener" in p:
            e["fastener"] = p["fastener"]
        if name in SOURCES:
            e["source"] = SOURCES[name]
        if name in ASSEMBLY:
            e["assembly_step"], e["assembly_dir"] = ASSEMBLY[name]
        if name in PRINT:
            e["print"] = PRINT[name]
        out.append(e)
        if not e["ok"]:
            bad.append(name)
    stale = [n for n in old_names if n not in parts]
    for n in stale:
        for sub, ext in (("stl", ".stl"), ("step", ".step")):
            f = os.path.join(HERE, sub, n + ext)
            if os.path.exists(f):
                os.remove(f)
    doc = dict(module="ram", revision=2, generated=time.strftime("%Y-%m-%d %H:%M:%S"), frame="B frame, mm, rest pose",
               n_parts=len(out), all_ok=not bad, not_ok=sorted(set(bad)), removed_parts=stale, deviations=DEVIATIONS,
               additions_ram_rev2=json.loads(json.dumps(RAM2, default=str)), roots=ROOTS, parts=out,
               exported_by="t4_obal.export_abs (absolute deflection 0.01 mm, STEP only below 12 MB)")
    json.dump(doc, open(pj, "w"), indent=1, ensure_ascii=False)
    mass = {}
    for e in out:
        if e.get("mass_g") is not None:
            mass[e["group"]] = mass.get(e["group"], 0.0) + e["mass_g"]
    print(f"exported {len(out)} STL in {time.time() - t:.1f} s -> parts_ram.json; removed stale exports {stale}; mass by group (g): "
          + ", ".join(f"{g} {m:.1f}" for g, m in mass.items()))
    print("NOT OK:", sorted(set(bad)) if bad else "none", f"| total {time.time() - T0:.1f} s")
    return 1 if bad else 0


# print strategy of the printed parts (K10 / K13; Saturn 4 Ultra 16K, 211.68 x 118.37 x 220, Elegoo Tough)
PRINT = {
    "T_spodok": dict(orientation="cap underside toward the build plate, tilted +15 deg about +X (right-hand: the +Y / back edge rises, "
                                 "u_away = (0, -0.259, 0.966)), RAISED >= 3 mm ON SUPPORTS (the drains must open into the gap)",
                     u_away=(0.0, -0.2588, 0.9659), on_plate=False,
                     supports="cap underside, plinth / foot-ring bottom, J1 lug; never on the 6805 seat D37.15, the spigot outer "
                              "face, the cradle inner faces or the column boss faces (fit faces)",
                     drains="servo window + 2 x D3 floor drains + floor slots vent the tub; fixer rev2 (M3): D2.5 drain at the +Y end of the pan-servo pocket floor "
                            "(0, -16.6), D2.0 at the back tub floor (0, 24.6), D2.5 vents into both column-foot bays at (+-38.5, 2.7); the blind D3.05 x 8.7 stop-pin holes are "
                            "flushed with IPA and blown out before bonding; cup test in K10", hole_comp="fit holes modelled at final size, drill / ream after curing",
                     warp="thin cradle walls are tied by the end wall, bridges and columns; deck screws pull the tops flat"),
    "T_paluba": dict(orientation="on edge, plate tilted 70 deg about +Y (right-hand; u_away = (0.940, 0, 0.342)), FFC wall up", u_away=(0.9397, 0.0, 0.3420),
                     on_plate=False, supports="straight front / right edges only "
                     "(never on the top = FFC / PTFE running face)", drains="open plate, none needed",
                     warp="2.0 plate may bow <= 0.2: pulled flat by F3a, sits on the shims"),
    "T_cap": dict(orientation="axis vertical, bottom (bond face) toward the build plate", u_away=(0.0, 0.0, 1.0), on_plate=False,
                  supports="bottom face only (bond face, sanded)",
                  drains="through hole D3.1 (rev3: printed D3.1, re-drilled D3.1 after curing)", warp="none"),      # fix-back after overenie3 (V9): the string still said D3.4 (rev. 2)
    "Z_naboj_test": dict(orientation="plate flat on the build plate", u_away=(0.0, 0.0, 1.0), on_plate=True, supports="none (plate on the plate); counterbore ceiling bridged",
                         drains="through bore D8.2", warp="110 x 90 plate: raft recommended"),
}


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
