"""NOVA mini - T4 torso: SINGLE SOURCE OF TRUTH for the three builders (t4_obal.py / t4_ram.py / t4_pan.py).

Frame = B frame of the finished neck/head: mm, Z up, x = robot LEFT (+) / RIGHT (-), FRONT = -Y, J1 and PAN axis = Z axis,
torso top = collar top z = +4.  z_B = z_world(pack) - 129.  Everything is modelled in the REST pose (lift 0, pan 0, J1 0).

Contents
  1. constants (every interface number of T4_spec.md)
  2. exterior, numeric: profile (T3 shape + printable rim), outer sections, TRUE inner offsets (distance field)
  3. exterior, CAD: outer / inner lofts and part blanks, cached as BREP in ./cache
  4. helper primitives (cylinders along axes, rounded boxes, pill / rounded-rect prisms, screws, inserts, magnets)
  5. space reservation (ENV = envelope list in the B frame, PAN_ENV = swept radius table) used by the fit study
  6. part registry convention + export helpers
  7. self-test:  /opt/venv/cad/bin/python t4_common.py [--rebuild]
Importing this module is cheap (numpy only); build123d is imported lazily by the CAD functions.
"""
from __future__ import annotations
import os, sys, json, math, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
T3_DIR = "/tmp/claude-0/gapwf/fin/T3"
B_STL = "/tmp/claude-0/gapwf/fin/B/stl"
CACHE = os.path.join(HERE, "cache")
sys.path.insert(0, T3_DIR)
import shape as S3                                                # approved exterior (T3), pure numpy   # noqa: E402

# =====================================================================================================================
# 1. CONSTANTS  (B frame, mm).  Naming: Z_* heights, R_* radii, X_/Y_ positions, (lo, hi) tuples are ranges.
# =====================================================================================================================
# ---- 1.1 exterior (approved T3 shape) -------------------------------------------------------------------------------
TOP = 4.0                       # torso top = collar top
DROP_WHITE = 85.0
Z_WHITE = TOP - DROP_WHITE      # -81.0  lower edge of the white shells
SEAM = 0.5                      # every visible seam (nominal, +-0.1)
Z_CAP_TOP = Z_WHITE - SEAM      # -81.5  upper visible edge of the black bottom cap
Z_BOT = TOP - 88.5              # -84.5  flat underside of the black cap
XS = 33.3                       # seam planes x = +-XS;  centre band |x| <= XS - SEAM/2, side caps |x| >= XS + SEAM/2
X_BAND = XS - SEAM / 2          # 33.05
X_CAP = XS + SEAM / 2           # 33.55
WALL = 2.2                      # nominal shell wall (true normal offset)
WALL_MIN, WALL_LOCAL = 2.0, 1.2
R_RIM = 29.6                    # flat white rim around the collar ring (T3 top section r 28.4 -> 29.6, brief par. 3)
RIM_BLEND = (33.3, 31.0)        # radius where the rim blend rejoins the T3 profile: X direction (a), Y direction (b)
BAR = (31.0, 4.2)               # light-bar opening: pill w x h (front, -Y)
Z_BAR = TOP - 36.5              # -32.5
SLOT = (21.0, 3.2)              # grille slot: pill w x h
Z_SLOT = TOP - 52.0             # -48.0
DOOR = (56.0, 60.0, 10.0)       # back door w x h x corner r (the DOOR part; opening = + SEAM/2 per side)
Z_DOOR = TOP - 46.0             # -42.0 door centre  -> door z -72 .. -12, x +-28
SH_Y, SH_Z = 3.0, TOP - 21.0    # shoulder axis (along X) at y +3, z -17
R_SOCKET = 14.0                 # socket hole in the side cap around the shoulder axis
KLB_PROFILE = [(-6.15, 13.5), (3.4, 13.5), (4.2, 12.7), (4.2, 11.4), (4.8, 11.0), (11.2, 11.0), (12.0, 10.2)]
#                 ^ visible black joint: (x - X_SH, r) about the shoulder axis (T3 build_scene, flange D27 / step D22)

# ---- 1.2 collar / top (finished parts of variant B, must not change) -------------------------------------------------
COLLAR = (26.5, 26.75, 28.25, 28.35)   # disc r (turns with pan), ring inner r, ring outer r, torso bore r
Z_COLLAR = (-2.0, 4.0)
R_BORE = 28.35                  # ONE bore in T_stred: collar-ring seat (z -2..4) + pan journal bearing (z -10.5..-4.5)
Z_BORE_BOT = -10.5
R_TUBE = 30.6                   # outer radius of the collar tube hanging from the top wall (wall 2.25)
R_JOURNAL = 28.20               # pan journal on the stage (resin 28.07 + PTFE tape 0.13)
Z_JOURNAL = (-10.5, -4.5)
JOURNAL_FIT = 0.15              # radial running clearance journal / bore
R_STAGE_TOP = 26.5              # stage top (collar-disc seat) radius for z -3.0 .. -2 (1.0 under the static collar ring)
NECK = (45.0, 20.0)             # neck blade section; neck bottom z -36.5 at rest
Z_NECK_BOT = -36.5
LIFT = 20.0
WELL_IN = (47.0, 22.0, 1.5)     # well inner section + corner r
WELL_WALL = 1.6
WELL_OUT = (WELL_IN[0] + 2 * WELL_WALL, WELL_IN[1] + 2 * WELL_WALL)      # 50.2 x 25.2 (corner r 28.09 from the axis)

# ---- 1.3 vertical stack on the axis (bottom -> top) ------------------------------------------------------------------
Z_FLOOR = -82.3                 # top of the cap floor (2.2 thick)
POCKET_J1 = 1.0                 # servo pocket depth in the floor (floor 1.2 under the servo)
Z_J1 = (-83.3, -48.3)           # STS3215 case (shaft DOWN)
FOAM_J1 = 0.5                   # PORON pad between servo top and deck
Z_DECK = (-47.8, -46.0)         # deck plate over the servo (1.8)
Z_PTFE = (-46.0, -45.7)         # PTFE thrust washer 24 x 12.4 x 0.3 (inside the stop groove r 12.3 .. 14.7)
Z_GEAR_PAN = (-45.7, -42.2)     # pan gear / drum (face 3.5)
Z_WELL_FLOOR = (-42.2, -41.0)   # well floor (1.2) = hub disc r <= R_HUB on the gear; back sector floor z -41.9 .. -41.0
R_HUB = 12.6                    # below Z_WALL_BOT the stage may only occupy r <= R_HUB or the BACK sector STAGE_BACK_AZ
Z_WALL_BOT = -41.3              # lower edge of the well walls (1.0 above the static pan pinion, top -42.3)
Z_BACK_FLOOR = (-41.9, -41.0)   # well floor outside the hub: only in the back sector (1.0 above the FPC channel wall)
STAGE_BACK_AZ = (5.0, 140.0)    # stage-frame azimuth sector that never passes over the pan pinion (pan +-85)
FOOT_GAP = 0.5                  # foot <-> well floor at rest
Z_FOOT = (-40.5, -36.5)         # neck foot at rest (4.0)
Z_WELL = (-41.0, -2.0)          # well interior
#   2.2 - 1.0 + 35.0 + 0.5 + 1.8 + 0.3 + 3.5 + 1.2 + 0.5 + 4.0 = 48.0 = Z_NECK_BOT - Z_BOT   (no vertical slack)

# ---- 1.4 J1 (torso yaw) ---------------------------------------------------------------------------------------------
J1_AX = (-18.0, 0.0)            # STS3215 output axis (C = 18.0 from the torso axis)
C_J1, M_J1, T_J1 = 18.0, 1.0, 18                      # centre distance, module, teeth (pinion = sun = 18T brass)
STS3215 = dict(L=45.2, W=24.7, H=35.0, x=(-29.5, 15.7), y=(-12.35, 12.35), boss_r=6.0, boss_h=2.6, spline_d=5.9,
               plug=dict(x=(15.7, 27.0), y=(-8.0, 8.0), dz=18.0), tol=0.3, mass=55.0)
J1_ADJ = 0.3                    # +- x adjustment of the servo in its pocket (set screw M2.5 at the -X end)
Z_J1_BOSS = (-85.9, -83.3)
Z_J1_HUB = (-86.8, -85.9)       # pinion hub r 5.0
Z_J1_GEAR = (-90.0, -86.8)      # gear plane (face 3.2), tip r 10.0, pitch r 9.0
BRG_6805 = (25.0, 37.0, 7.0)    # d, D, B
Z_BRG = (-98.0, -91.0)
R_FOOT_SEAT = 18.5              # bearing seat radius (bore D37.00 +0.05)
R_FOOT_LOW = 21.0               # foot ring OD around the bearing (z -98 .. -91); the J1 FPC inner run wraps on it
R_PLINTH = 24.0                 # visible plinth (z -91 .. -84.5), as T3
R_FOOT_SHOULDER = 17.0          # shoulder above the bearing outer ring (r 17.0 .. 18.5 at z -91)
R_J1_NOTCH = 10.8               # clearance around the pinion teeth in the plinth wall (cylinder about J1_AX)
Z_J1_NOTCH = (-90.6, -86.3)     # ... only below the skirt; above it only the boss slot r 7.2 (x +-0.3) goes through
SKIRT = dict(r=28.5, z=(-86.2, -85.2), hole_r=7.2)     # dust skirt over the pinion orbit (hole about J1_AX); 0.6 above the teeth
Z_BASE_TOP = -86.0              # top plane of the future base (T3: 1.5 mm gap)
R_BASE_OPEN = 29.0              # opening the base must provide (pinion orbit r 28.0)
J1_RANGE = (150.0, 155.0)       # firmware / hard stop (deg)
J1_STOP_LUG = dict(r=(18.5, 21.0), az=90.0, w=2.5, z=(-100.0, -98.0))     # lug under the foot ring (rotates)
J1_FPC = dict(w=6.0, t=0.15, r_inner=21.0, floor_slot=dict(x=(-3.4, 3.4), y=(21.6, 23.0)))   # slot through the floor

# ---- 1.5 PAN (head yaw) ---------------------------------------------------------------------------------------------
C_PAN, M_PAN, T_PAN = 21.6, 0.8, (18, 36)
PAN_AX = (-5.85, -20.793)       # pinion axis (C 21.6; azimuth 254.3 deg) -> the servo case is centred on x = 0
STS3032 = dict(L=23.5, W=12.5, H=23.0, x=(-11.75, 11.75), y=(-27.043, -14.543), z=(-74.2, -51.2),
               tab=dict(x=(-16.25, 16.25), z=(-58.0, -55.5), hole_x=(-14.0, 14.0), hole_d=2.2),
               boss_r=6.2, boss_z=(-51.2, -47.7), hub_r=4.0, hub_z=(-47.7, -45.5),
               plug=dict(x=(11.75, 18.75), y=(-24.8, -16.8), z=(-72.7, -64.7)), tol=0.3, mass=21.0)
Z_PAN_PINION = (-45.5, -42.3)   # m0.8 18T, tip r 8.0, pitch r 7.2
R_PAN_GEAR = (14.4, 15.2)       # 36T pitch r, tip r
R_DRUM = 15.7                   # smooth drum sector for the FPC inner run
PAN_SECTOR = (154.3, 354.3)     # toothed sector of the gear (gear-frame azimuth, 200 deg centred on the pinion)
PAN_RANGE = (85.0, 90.0)        # firmware / hard stop
PAN_STOP = dict(r=13.5, pin_d=2.0, groove_w=2.4, groove_depth=1.2, az=(0.0, 180.0))   # pin in the gear, groove in deck
PIVOT = dict(pin_d=6.0, pin_z=(-47.7, -41.2), boss_r=5.5, boss_z=(-46.0, -44.2))      # steel pin pressed in the deck
FPC_PAN = dict(w=3.0, t=0.12, r_in=R_DRUM, r_out=23.5, z=(-45.9, -42.9), wall=(23.5, 25.1), az=(15.0, 165.0),
               deck_slot=dict(x=(-18.0, -14.0), y=(15.0, 16.2)))

# ---- 1.6 LIFT (neck 0..20) ------------------------------------------------------------------------------------------
MG90S = dict(H=22.5, W=12.2, L=22.8, shaft_from_end=5.9, turret=6.0, boss_r=5.9, lobe=(2.9, 5.6), spline=(4.8, 3.0),
             tab=dict(t=2.5, from_bottom=(16.0, 18.5), ext=4.85, hole=2.45, hole_d=2.2), tol=0.3, mass=13.4)
Y_LIFT, Z_LIFT = 23.2, -24.2    # lift servo shaft axis (along X), pan-stage frame
R_CRANK = 10.0                  # stroke 20.0 = 2 r, dead centres at lift 0 and 20; the pin sweeps the FRONT half
LIFT_X = (-6.5, 16.0)           # servo case: gear face (x_t) .. bottom cover (x_b); turret / spline / crank on -X
LIFT_CASE = dict(x=LIFT_X, y=(Y_LIFT - 6.1, Y_LIFT + 6.1), z=(Z_LIFT - 16.9, Z_LIFT + 5.9))
CRANK = dict(hub_x=(-17.0, -12.8), hub_r=3.6, arm_x=(-17.0, -14.5), tip_r=2.2, pin_d=2.0, pin_x=(-19.9, -14.5))
EAR = dict(x=(-19.9, -17.4), y=(10.2, 25.1), zrel=(-6.3, 2.3), slot_w=2.2, slot_y=(12.1, 24.3), chamfer=1.5,
           flange=dict(x=(-19.9, -7.5), y=(10.2, 12.4), zrel=(-6.3, -2.3), notch=dict(x=(-17.6, -13.5), zrel=-3.2)),
           screw=dict(x=-10.0, zrel=-4.3, size="M2x8 thread-forming, along -Y"),
           dowel=dict(x=-15.5, zrel=-4.3, d=2.0, length=5.0))        # dowel pressed 3.0 into the foot back face
Z_SLOT_REST = Z_LIFT - R_CRANK  # -34.2 = slot centre line of the ear at rest (zrel = 0)
FOOT = dict(size=(44.6, 19.6, 4.0), z=Z_FOOT, tab=dict(x=(22.3, 27.0), y=(-3.5, 3.5), z=(-40.5, -38.0)),
            wire_slot=dict(x=(11.6, 15.0), y=(-7.2, 2.6)))
WIN_BACK = dict(x=(-20.9, -6.5), y=(10.9, 12.7), z=(-41.3, -10.9))        # window in the well back wall (ear + 1.0)
WIN_END = dict(x=(23.4, 25.2), y=(-4.5, 4.5), z=(-41.3, -15.0))           # window in the well +X end wall (FPC tab)
BRACKET = dict(x=(-5.3, 17.6), y=(12.6, 17.1), z=(-41.9, -13.0))          # reserved for P_drziak_serva (+ under the servo)
FPC_LIFT = dict(x=(25.3, 28.4), y=(-4.0, 4.0), z=(-40.5, -15.5), bend_r=3.5)
BRACKET_PADS = [dict(x=19.5, z=-30.0), dict(x=8.0, z=-14.5)]              # M2 inserts in the well back wall, face y 15.6
GEAR_JOINT = dict(dowels=[(9.0, 0.0), (9.0, 180.0)], d=2.0, length=4.0)   # P_koleso bonded to the hub disc + 2 dowels (r, az)

# ---- 1.7 shoulder joints (left = +X; mirror for the right) ----------------------------------------------------------
X_COL_IN = 34.4                 # inner face of the frame column (1.0 to the pan-stage sweep r 33.4)
X_COL_BOSS = 38.4               # boss face = seat of the joint neck (keyed)
X_COL_STOP = 39.1               # stop ring face on the column (r 11.6 .. 12.8): the side cap seat flange rests on it
R_COL_STOP = (11.6, 12.8)
X_SEAT = 40.6                   # outer face of the cap seat flange = shoulder of T_klb (flange 1.5: 39.1 .. 40.6)
R_KLB_NECK = 11.0               # joint neck (38.4 .. 40.6) through the seat hole r 11.25
R_SEAT_HOLE = 11.25
KLB_SCREWS = dict(n=3, pcd_r=7.5, az=(90.0, 210.0, 330.0), size="M2x10 socket head", head_seat_x=45.0, cbore_d=4.2)
#   azimuth in the y-z plane about the shoulder axis: (dy, dz) = r (cos az, sin az); same (dy, dz) on both sides
KLB_MAGNETS = dict(n=3, pcd_r=7.5, az=(30.0, 150.0, 270.0), size=(3.0, 2.0))       # in the outer end face
KLB_BUSH = dict(bore_d=8.05, bore_x_in=44.0, recess_d=10.2, flange=(10.0, 2.0), spring="2x DIN 2093 10x5.2x0.4",
                spigot_d=10.0, spigot_x=41.0, slip_torque=0.25)      # spigot of the column boss 38.4 .. 41.0
KLB_WIRE = dict(az=270.0, groove=(1.6, 2.6), notch_r=13.2, notch_w=3.0)            # 3 x AWG30: groove on the r 13.5 body (underside)
R_KLB_STEP = 11.0                                                                  # D22 step = journal of the arm hub
COL_WEB = dict(y=(-9.0, 15.0), t=2.0, rib_x=42.0, z=(-78.0, -30.0))                # column U-channel (PETG)
COL_FOOT = dict(x=(X_COL_IN, 37.6), y=(-5.0, 11.0), z=(Z_FLOOR, -78.0))            # column foot inside the cap tub

# ---- 1.8 door ---------------------------------------------------------------------------------------------------------
DOOR_LEDGE = dict(inside=2.0, outside=2.0, inset=(2.4, 4.0), top_gap_x=18.0)       # frame ledge on T_stred
DOOR_HOOK = dict(x=(12.0, 20.0), inset=(2.4, 3.6), z=(-12.0, -9.5))                # 2 hook tabs on the door (+-x)
DOOR_MAGNETS = dict(size=(5.0, 2.0), xz=[(25.0, -24.0), (-25.0, -24.0), (25.0, -60.0), (-25.0, -60.0)],
                    door_boss=(8.0, 2.3), pad_inset=(4.7, 7.2))

# ---- 1.9 front stack ------------------------------------------------------------------------------------------------
GUIDE = dict(plug=(30.6, 3.8), flange=(35.0, 8.0, 1.2))
LED_PCB = dict(size=(30.0, 4.0, 0.8), n=6, pitch=5.0, led=(2.0, 2.0, 0.84), gap=4.7, y_front=-30.9)
GRILLE = dict(plug=(20.6, 2.8), flange=(25.0, 7.0, 1.2))
SPEAKER = dict(d=28.0, t=5.0, y=(-36.6, -31.6), z=-51.0)     # centre 3.0 below the slot (clears the light box)
LED_BOX = dict(x=(-17.5, 17.5), y=(-36.6, -30.1), z=(Z_BAR - 3.5, Z_BAR + 3.5))     # guide flange + light box + PCB
LED_BOSS = [(19.5, Z_BAR), (-19.5, Z_BAR)]                   # 2 x M2 thread-forming bosses (r 2.5) on the front wall
SPK_BOSS = dict(n=3, pcd_r=16.5, az=(90.0, 210.0, 330.0))    # 3 x M2 bosses around the speaker axis (x-z plane angles)

# ---- 1.10 bottom cap, fixings -----------------------------------------------------------------------------------------
SPIGOT = dict(z=(Z_CAP_TOP, -78.0), t=1.6, fit=0.2)       # locating spigot of the cap inside the white lip (outline: SPIGOT_SE)
SPIGOT_SE = (41.15, 27.09, 2.66)                           # superellipse a, b, n of the spigot OUTER face (verified in the self-test)
TUB_SE = (SPIGOT_SE[0] - 1.6, SPIGOT_SE[1] - 1.6, 2.66)    # inner face of the spigot = wall of the cap tub above Z_FLOOR
SCR_STRED = [(29.0, 19.0), (-29.0, 19.0), (29.0, -19.0), (-29.0, -19.0)]           # M2.5x8 countersunk, from below
SCR_RAM = [(-22.0, 17.5), (-22.0, -17.5), (18.0, 17.5), (18.0, -17.5), (35.5, 3.0), (-35.5, 3.0)]   # M2.5x8, from below
SCR_DECK = [(-22.0, -15.0), (20.0, -15.0), (-22.0, 15.0), (20.0, 15.0)]            # M2.5x6, from above
CRADLE = dict(x=(-31.6, 23.0), y=(-14.15, 14.15), wall=1.6, z=(Z_FLOOR, Z_DECK[0]))      # walls around the J1 servo
BOSS_STRED = dict(r=3.2, z=(Z_WHITE, -75.0), insert="M2.5 x 4.0, OD 3.5, glued")
BOSS_KEEPOUT = dict(x=(25.8, 32.2), y_min=15.8)            # 4 vertical prisms (+-x, +-y, all z > Z_WHITE) the tower must avoid
LIP_RELIEF = dict(x=(-16.75, 16.75), y_min=27.55)          # front lip of T_stred: inner half depth >= 27.55 (pan servo)
DRAIN = [(33.0, -8.0), (-33.0, -8.0)]                      # D3 drain / vent holes in the cap floor
TOWER_CLEAR = 0.5                                          # tower <-> white lip while T_stred is lowered

# ---- 1.11 electronics (bought, datasheet sizes) -----------------------------------------------------------------------
CTRL = dict(pcb=(48.0, 22.0, 1.6), x=(-24.0, 24.0), y=(15.5, 22.5), z=(-77.0, -55.0),       # carrier + ESP32-S3-Zero
            screws=[(18.0, -68.0), (-18.0, -68.0)])                                          # M2 from +Y (door), (x, z)
BUCK = dict(size=(17.8, 17.8, 8.8), x=(-45.4, -36.6), y=(-5.9, 11.9), z=(-70.0, -52.2))      # Pololu D36V28F5
AMP = dict(size=(19.3, 17.8, 3.0), x=(36.6, 39.6), y=(-5.9, 11.9), z=(-71.5, -52.2))         # MAX98357A breakout
CAP470 = dict(d=10.0, h=13.0, at=(41.0, 3.0, -45.0))                                        # 470 uF / 10 V, axis Z

# ---- 1.12 materials -----------------------------------------------------------------------------------------------------
DENS = dict(resin_white=1.18e-3, resin_black=1.18e-3, resin_clear=1.18e-3, resin_grey=1.18e-3, petg=1.27e-3,
            pom=1.41e-3, brass=8.5e-3, steel=7.85e-3, pcb=1.9e-3, ptfe=2.2e-3, fpc=1.4e-3, magnet=7.5e-3, bought=None)
GROUPS = ("T", "P", "L", "Z")           # static torso, pan stage, lift (on P), base dummy


# =====================================================================================================================
# 2. EXTERIOR - numeric (profile, sections, true inner offsets)
# =====================================================================================================================
def _build_profile():
    """T3 profile (drop, a, b, n) with the printable rim: the top section is a circle r R_RIM at drop 0; the blend
    d_new(x) = d_T3(x) - c (x_m - x)^2 (x < x_m) keeps the profile convex and is IDENTICAL to T3 beyond x_m
    (a >= 33.3 <-> drop >= 1.26, b >= 31.0 <-> drop >= 2.59)."""
    ss = np.linspace(0, S3.S_END, 12001)
    D0, A0, B0, N0 = (S3._SP[k](ss) for k in range(4))
    out = {}
    for key, X0, xm in (("a", A0, RIM_BLEND[0]), ("b", B0, RIM_BLEND[1])):
        k = int(np.argmax(X0))                                 # widest point: only the rising branch is modified
        g0 = float(np.interp(R_RIM, X0[:k], D0[:k]))
        c = g0 / (xm - R_RIM) ** 2
        Dn = D0.copy()
        Dn[:k] = D0[:k] - np.where(X0[:k] < xm, c * (xm - X0[:k]) ** 2, 0.0)
        m = (np.arange(len(X0)) >= k) | (X0 >= R_RIM)
        d, x = Dn[m], X0[m]
        d[0], x[0] = 0.0, R_RIM
        out[key] = (d, x, g0, c)
    dg = np.concatenate([np.linspace(0, 6, 1201)[:-1], np.linspace(6, 76, 3501)[:-1], np.linspace(76, 88.5, 2501)])
    a = np.interp(dg, out["a"][0], out["a"][1]); b = np.interp(dg, out["b"][0], out["b"][1])
    n = np.interp(dg, D0, N0)
    return dg, a, b, n, dict(a=out["a"][2:], b=out["b"][2:])


PD, PA, PB, PN, RIM_INFO = _build_profile()          # dense table by drop
DROP_END = float(PD[-1])                              # 88.5


def prof(drop):
    """(a, b, n) of the T4 exterior at `drop` below TOP (0 .. 88.5)"""
    return (float(np.interp(drop, PD, PA)), float(np.interp(drop, PD, PB)), float(np.interp(drop, PD, PN)))


def prof_t3(drop):
    """(a, b, n) of the approved T3 exterior at `drop` (for fidelity checks)"""
    s = S3.s_of_drop(drop)
    _, a, b, n = S3.prof(s)
    return a, b, n


def se_r(a, b, n, th):
    c, s = np.abs(np.cos(th)), np.abs(np.sin(th))
    return ((c / a) ** n + (s / b) ** n) ** (-1.0 / n)


def azimuths(count):
    """section point azimuths: start at the FRONT centre (-Y), counter-clockwise seen from above"""
    return np.linspace(0, 2 * np.pi, count, endpoint=False) - np.pi / 2


def outer_section(drop, count=120):
    """(count, 3) points of the outer surface at height TOP - drop"""
    a, b, n = prof(drop)
    th = azimuths(count)
    r = se_r(a, b, n, th)
    return np.stack([r * np.cos(th), r * np.sin(th), np.full(count, TOP - drop)], 1)


def outer_r(z, th):
    """outer radius at height z and azimuth th (arrays ok)"""
    z = np.asarray(z, float)
    a = np.interp(TOP - z, PD, PA); b = np.interp(TOP - z, PD, PB); n = np.interp(TOP - z, PD, PN)
    return se_r(a, b, n, np.asarray(th, float))


def y_surface(x, z, side=-1):
    """y of the outer surface at lateral position x and height z; side -1 = front, +1 = back"""
    a, b, n = prof(TOP - z)
    return side * b * (1 - min(1.0, abs(x) / a) ** n) ** (1 / n)


def x_surface(y, z, side=1):
    a, b, n = prof(TOP - z)
    return side * a * (1 - min(1.0, abs(y) / b) ** n) ** (1 / n)


X_SH = x_surface(SH_Y, SH_Z)        # outer surface |x| on the shoulder axis (46.75)
X_KLB_END = X_SH + 12.0             # outer end face of the black joint (arm interface plane)

_CLOUD = {}


def outer_cloud(h=0.16):
    """dense point cloud of the complete outer surface (side + flat top + flat bottom) with a KD-tree"""
    if "tree" in _CLOUD:
        return _CLOUD["P"], _CLOUD["tree"]
    from scipy.spatial import cKDTree
    arc = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(PD), np.maximum(np.abs(np.diff(PA)), np.abs(np.diff(PB)))))])
    t = np.linspace(0, arc[-1], int(arc[-1] / h) + 1)
    d = np.interp(t, arc, PD)
    a, b, n = np.interp(d, PD, PA), np.interp(d, PD, PB), np.interp(d, PD, PN)
    N = int(2 * np.pi * 52.5 / h)
    th = azimuths(N)
    r = se_r(a[:, None], b[:, None], n[:, None], th[None, :])
    P = np.stack([r * np.cos(th), r * np.sin(th), np.broadcast_to((TOP - d)[:, None], r.shape)], 2).reshape(-1, 3)
    caps = []
    for z, (ca, cb, cn) in ((TOP, prof(0.0)), (Z_BOT, prof(DROP_END))):
        g = np.arange(-ca, ca + h, h * 1.25)
        X, Y = np.meshgrid(g, g)
        m = (np.abs(X) / ca) ** cn + (np.abs(Y) / cb) ** cn <= 1.0
        caps.append(np.stack([X[m], Y[m], np.full(m.sum(), z)], 1))
    P = np.concatenate([P] + caps)
    _CLOUD["P"], _CLOUD["tree"] = P, cKDTree(P)
    return P, _CLOUD["tree"]


def dist_outer(Q):
    """distance of points Q (n, 3) to the outer surface (unsigned)"""
    _, tree = outer_cloud()
    d, _ = tree.query(np.asarray(Q, float))
    return d


def inside_outer(Q):
    Q = np.asarray(Q, float)
    r = np.hypot(Q[:, 0], Q[:, 1]); th = np.arctan2(Q[:, 1], Q[:, 0])
    zc = np.clip(Q[:, 2], Z_BOT, TOP)
    return (r < outer_r(zc, th)) & (Q[:, 2] < TOP) & (Q[:, 2] > Z_BOT)


def clearance_to_shell(Q, wall=WALL, far=6.0):
    """signed clearance of points to the INNER surface of a shell of thickness `wall` (+ = free space inside).
    Points whose radial gap exceeds wall + far in the near-vertical zone (-72 < z < -6) get 0.9 x the radial value
    (a lower bound there) instead of the exact distance - they are far from the wall anyway."""
    Q = np.asarray(Q, float)
    r = np.hypot(Q[:, 0], Q[:, 1]); th = np.arctan2(Q[:, 1], Q[:, 0])
    g = outer_r(np.clip(Q[:, 2], Z_BOT, TOP), th) - r
    skip = (g > wall + far) & (Q[:, 2] > -72.0) & (Q[:, 2] < -6.0)
    out = 0.9 * (g - wall)
    if (~skip).any():
        q = Q[~skip]
        d = dist_outer(q)
        out[~skip] = np.where(inside_outer(q), d - wall, -d - wall)
    return out


Z_IN_TOP, Z_IN_BOT = 1.75, -82.25       # z range of the inner solid (cavity); the caps there give 2.25 walls


def inner_section(z, wall=WALL, count=120, _iters=26):
    """(count, 3) points of the TRUE inner offset surface (distance `wall` to the outer surface) in the plane z.
    Solved per azimuth by bisection on the radius (outermost point with distance = wall)."""
    th = azimuths(count)
    ro = outer_r(np.full(count, z), th)
    c, s = np.cos(th), np.sin(th)

    def f(rho):
        return dist_outer(np.stack([rho * c, rho * s, np.full(count, z)], 1)) - wall
    hi = ro.copy(); lo = np.maximum(ro - 0.4, 0.0)
    for _ in range(200):                                     # march inward until the distance exceeds the wall
        m = f(lo) < 0
        if not m.any():
            break
        hi = np.where(m, lo, hi); lo = np.where(m, np.maximum(lo - 0.4, 0.0), lo)
    for _ in range(_iters):
        mid = 0.5 * (lo + hi); m = f(mid) > 0
        lo = np.where(m, mid, lo); hi = np.where(m, hi, mid)
    rho = 0.5 * (lo + hi)
    return np.stack([rho * c, rho * s, np.full(count, z)], 1)


def inner_half(z, wall=WALL):
    """(a_i, b_i): inner half width (y = 0) and half depth (x = 0) at height z"""
    P = inner_section(z, wall, 8)
    return float(np.abs(P[:, 0]).max()), float(np.abs(P[:, 1]).max())


OUTER_DROPS = [0, 0.12, 0.3, 0.55, 0.85, 1.2, 1.6, 2.1, 2.7, 3.4, 4.3, 5.4, 6.8, 8.5, 10.5, 12.5, 15, 18, 21.5, 25, 29,
               33, 37, 41, 45, 49, 53, 57, 61, 65, 68.5, 71.5, 74, 76, 77.75, 79.25, 80.5, 81.6, 82.6, 83.5, 84.3, 85.0,
               85.6, 86.2, 86.7, 87.15, 87.55, 87.9, 88.2, 88.5]
INNER_Z = [1.75, 1.3, 0.8, 0.2, -0.5, -1.3, -2.2, -3.2, -4.4, -5.8, -7.4, -9.2, -11.2, -13.5, -16, -19, -22.5, -26, -30,
           -34, -38, -42, -46, -50, -54, -58, -62, -65.5, -68.5, -71, -73, -74.75, -76.2, -77.4, -78.4, -79.2, -79.9,
           -80.5, -81.0, -81.45, -81.85, -82.25]


# =====================================================================================================================
# 3. EXTERIOR - CAD (lazy build123d), cached BREP
# =====================================================================================================================
def _bd():
    import build123d as bd
    return bd


def _wire(P):
    bd = _bd()
    return bd.Wire([bd.Edge.make_spline([bd.Vector(*p) for p in P], periodic=True)])


def _one(shape):
    """largest solid of a boolean result"""
    sol = shape.solids()
    return max(sol, key=lambda s: s.volume) if len(sol) != 1 else sol[0]


def cached(name, fn, rebuild=False, verbose=True):
    """load ./cache/<name>.brep or build it with fn() and save it; returns a Solid / Compound"""
    bd = _bd()
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, name + ".brep")
    if os.path.exists(p) and not rebuild:
        return bd.import_brep(p)
    t = time.time()
    s = fn()
    bd.export_brep(s, p)
    if verbose:
        print(f"[cache] built {name}: {time.time() - t:.1f} s, volume {s.volume:.1f}, valid {s.is_valid}", flush=True)
    return bd.import_brep(p)


def outer_solid(rebuild=False):
    """full exterior solid, z Z_BOT .. TOP (white part + black cap), loft through OUTER_DROPS"""
    return cached("outer", lambda: _bd().Solid.make_loft([_wire(outer_section(d)) for d in OUTER_DROPS]), rebuild)


def inner_z_range(wall=WALL):
    """(z_bot, z_top) of the cavity solid for a given inset: 0.05 inside the flat top / bottom offsets"""
    return Z_BOT + wall + 0.05, TOP - wall - 0.05


def inner_solid(wall=WALL, rebuild=False):
    """cavity solid: true offset `wall` inside the exterior, z range inner_z_range(wall) (2.2 -> -82.25 .. 1.75).
    Built and cached per inset (name inner_<100*wall>), e.g. inner_solid(2.4), inner_solid(4.0) for the door ledge."""
    nm = f"inner_{int(round(wall * 100)):03d}"
    zb, zt = inner_z_range(wall)
    zs = [zt] + [z for z in INNER_Z if zb + 0.2 < z < zt - 0.2] + [zb]
    return cached(nm, lambda: _bd().Solid.make_loft([_wire(inner_section(z, wall)) for z in zs]), rebuild)


def box(x0, x1, y0, y1, z0, z1):
    bd = _bd()
    return bd.Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * bd.Box(x1 - x0, y1 - y0, z1 - z0)


def shell_white(rebuild=False):
    """white shell before splitting: exterior above Z_WHITE minus the cavity (wall 2.2, top wall >= 2.25)"""
    def mk():
        o = outer_solid() & box(-80, 80, -80, 80, Z_WHITE, TOP + 5)
        return _one(o - inner_solid())
    return cached("shell_white", mk, rebuild)


def stred_blank(rebuild=False):
    """centre band |x| <= X_BAND of the white shell (no bore, no openings)"""
    return cached("stred_blank", lambda: _one(shell_white() & box(-X_BAND, X_BAND, -80, 80, -90, 10)), rebuild)


def bok_blank(side=1, rebuild=False):
    """side cap blank; side +1 = left (+X) = T_bok_L, -1 = right = T_bok_P"""
    nm = "bok_L_blank" if side > 0 else "bok_P_blank"
    x0, x1 = (X_CAP, 80) if side > 0 else (-80, -X_CAP)
    return cached(nm, lambda: _one(shell_white() & box(x0, x1, -80, 80, -90, 10)), rebuild)


def cap_blank(rebuild=False):
    """SOLID black bottom cap body: exterior below Z_CAP_TOP (tub, spigot, foot ring are added by the builder)"""
    return cached("cap_blank", lambda: _one(outer_solid() & box(-80, 80, -80, 80, Z_BOT - 5, Z_CAP_TOP)), rebuild)


def se_prism(a, b, n, z0, z1, count=96):
    """superellipse prism (vertical walls) - spigot / tub / lip outlines"""
    bd = _bd()
    th = azimuths(count); r = se_r(a, b, n, th)
    w = _wire(np.stack([r * np.cos(th), r * np.sin(th), np.full(count, z0)], 1))
    return bd.extrude(bd.Face(w), amount=z1 - z0)


# =====================================================================================================================
# 4. HELPER PRIMITIVES
# =====================================================================================================================
def cyl_z(r, z0, z1, x=0.0, y=0.0):
    bd = _bd()
    return bd.Pos(x, y, (z0 + z1) / 2) * bd.Cylinder(r, z1 - z0)


def cyl_x(r, x0, x1, y=0.0, z=0.0):
    bd = _bd()
    return bd.Pos((x0 + x1) / 2, y, z) * (bd.Rot(0, 90, 0) * bd.Cylinder(r, x1 - x0))


def cyl_y(r, y0, y1, x=0.0, z=0.0):
    bd = _bd()
    return bd.Pos(x, (y0 + y1) / 2, z) * (bd.Rot(90, 0, 0) * bd.Cylinder(r, y1 - y0))


def tube_z(ro, ri, z0, z1, x=0.0, y=0.0):
    return cyl_z(ro, z0, z1, x, y) - cyl_z(ri, z0 - 0.1, z1 + 0.1, x, y)


def rbox(x0, x1, y0, y1, z0, z1, r=0.0, axis="z"):
    """box with the 4 edges parallel to `axis` rounded with r"""
    bd = _bd()
    b = box(x0, x1, y0, y1, z0, z1)
    if r > 0:
        ax = {"x": bd.Axis.X, "y": bd.Axis.Y, "z": bd.Axis.Z}[axis]
        b = bd.fillet(b.edges().filter_by(ax), r)
    return b


def pill_prism_y(w, h, x, z, y0, y1):
    """stadium (pill) w x h in the x-z plane, extruded from y0 to y1 (light bar, grille slot)"""
    r = h / 2
    return box(x - w / 2 + r, x + w / 2 - r, y0, y1, z - r, z + r) + cyl_y(r, y0, y1, x - w / 2 + r, z) + \
        cyl_y(r, y0, y1, x + w / 2 - r, z)


def rrect_prism_y(w, h, r, x, z, y0, y1):
    """rounded rectangle w x h (corner r) in the x-z plane, extruded from y0 to y1 (door, door opening, ledge bands)"""
    return rbox(x - w / 2, x + w / 2, y0, y1, z - h / 2, z + h / 2, r, "y")


def door_prism(grow=0.0, y0=5.0, y1=60.0):
    """door outline prism through the BACK wall; grow = SEAM/2 for the opening, negative for inner bands"""
    return rrect_prism_y(DOOR[0] + 2 * grow, DOOR[1] + 2 * grow, max(0.5, DOOR[2] + grow), 0.0, Z_DOOR, y0, y1)


SCREWS = {   # name: (thread d, clearance hole d, head d, head k, countersunk?)
    "M2": (2.0, 2.3, 3.8, 2.0, False), "M2.5": (2.5, 2.8, 4.5, 2.5, False), "M3": (3.0, 3.3, 5.5, 3.0, False),
    "M2c": (2.0, 2.3, 3.8, 1.2, True), "M2.5c": (2.5, 2.8, 4.7, 1.5, True), "M3c": (3.0, 3.3, 5.6, 1.65, True)}
INSERTS = {  # name: (outer d, length, hole d in resin (glued), hole d in PETG (heat-set))
    "M2": (3.2, 3.0, 3.3, 2.9), "M2.5": (3.5, 4.0, 3.6, 3.2), "M3": (4.2, 4.0, 4.3, 3.9)}


def _along(shape, axis, sign=1):
    """helper: a shape built along +Z from the origin re-oriented so that it points along `axis` * sign"""
    bd = _bd()
    rot = {("z", 1): bd.Rot(0, 0, 0), ("z", -1): bd.Rot(180, 0, 0), ("x", 1): bd.Rot(0, 90, 0),
           ("x", -1): bd.Rot(0, -90, 0), ("y", 1): bd.Rot(-90, 0, 0), ("y", -1): bd.Rot(90, 0, 0)}[(axis, sign)]
    return rot * shape


def screw(size, length, at, axis="z", sign=1):
    """screw solid: head seat at `at`, shank running along axis*sign for `length` (head on the other side).
    Countersunk sizes ("M2.5c") have the head top flush at `at`."""
    bd = _bd()
    d, _, dk, k, csk = SCREWS[size]
    if csk:
        head = bd.Pos(0, 0, k / 2) * bd.Cone(dk / 2, d / 2, k)
        s = head + bd.Pos(0, 0, (k + length) / 2) * bd.Cylinder(d / 2, length - k)
    else:
        s = bd.Pos(0, 0, -k / 2) * bd.Cylinder(dk / 2, k) + bd.Pos(0, 0, length / 2) * bd.Cylinder(d / 2, length)
    return bd.Pos(*at) * _along(s, axis, sign)


def screw_hole(size, length, at, axis="z", sign=1, head_len=30.0, extra=0.2):
    """cutter for a screw: clearance hole along axis*sign from the head seat `at` + head / tool channel behind it"""
    bd = _bd()
    _, dh, dk, k, csk = SCREWS[size]
    if csk:
        s = bd.Pos(0, 0, k / 2) * bd.Cone(dk / 2 + extra, dh / 2, k) + bd.Pos(0, 0, length / 2) * bd.Cylinder(dh / 2, length) \
            + bd.Pos(0, 0, -head_len / 2) * bd.Cylinder(dk / 2 + extra, head_len)
    else:
        s = bd.Pos(0, 0, length / 2) * bd.Cylinder(dh / 2, length) + \
            bd.Pos(0, 0, -head_len / 2) * bd.Cylinder(dk / 2 + extra, head_len)
    return bd.Pos(*at) * _along(s, axis, sign)


def insert(size, at, axis="z", sign=1):
    """brass insert solid: open end at `at`, body along axis*sign"""
    bd = _bd()
    do, ln, _, _ = INSERTS[size]
    d = SCREWS[size][0]
    s = bd.Pos(0, 0, ln / 2) * (bd.Cylinder(do / 2, ln) - bd.Cylinder(d / 2, ln + 0.2))
    return bd.Pos(*at) * _along(s, axis, sign)


def insert_hole(size, at, axis="z", sign=1, mat="resin", pilot=2.0):
    """cutter for an insert seat (+ pilot for the screw tip behind it)"""
    bd = _bd()
    do, ln, dr, dp = INSERTS[size]
    dh = dr if mat == "resin" else dp
    d = SCREWS[size][1]
    s = bd.Pos(0, 0, (ln + 0.3) / 2) * bd.Cylinder(dh / 2, ln + 0.3) + \
        bd.Pos(0, 0, ln + pilot / 2) * bd.Cylinder(d / 2, pilot + 0.6)
    return bd.Pos(*at) * _along(s, axis, sign)


def magnet(d, t, at, axis="y", sign=1):
    bd = _bd()
    return bd.Pos(*at) * _along(bd.Pos(0, 0, t / 2) * bd.Cylinder(d / 2, t), axis, sign)


def magnet_hole(d, t, at, axis="y", sign=1, fit=0.05, depth_extra=0.1):
    bd = _bd()
    return bd.Pos(*at) * _along(bd.Pos(0, 0, (t + depth_extra) / 2) * bd.Cylinder(d / 2 + fit, t + depth_extra), axis, sign)


def rot_z(shape, deg):
    bd = _bd()
    return bd.Rot(0, 0, deg) * shape


def lift_z(shape, mm):
    bd = _bd()
    return bd.Pos(0, 0, mm) * shape


# =====================================================================================================================
# 5. SPACE RESERVATION  (B frame; kinds: box (x, y, z ranges), cyl (axis, c, r, range), tube (+ ri))
#    owner: obal / ram / pan;  group: T static, P pan stage (swept pan -85..85), L lift (P + lift 0..20), Z base dummy
# =====================================================================================================================
def _b(name, owner, group, x, y, z, note=""):
    return dict(name=name, owner=owner, group=group, kind="box", x=tuple(x), y=tuple(y), z=tuple(z), note=note)


def _c(name, owner, group, axis, c, r, rng, ri=0.0, note=""):
    return dict(name=name, owner=owner, group=group, kind="cyl", axis=axis, c=tuple(c), r=r, ri=ri, rng=tuple(rng), note=note)


def envelopes():
    xb, xt = LIFT_X[1], LIFT_X[0]
    E = [
        # ------------------------------------------------------------------ ram (static tower, |x| <= 33 inside the lip)
        _b("servo_J1", "ram", "T", STS3215["x"], STS3215["y"], Z_J1, "STS3215, shaft down at J1_AX"),
        _c("servo_J1_boss", "ram", "T", "z", J1_AX, 6.0, Z_J1_BOSS),
        _b("servo_J1_plug", "ram", "T", STS3215["plug"]["x"], STS3215["plug"]["y"], (Z_J1[1] - 18.0, Z_J1[1]),
           "2 x 5264 plugs + cable bend"),
        _b("ram_koliska", "ram", "T", CRADLE["x"], CRADLE["y"], CRADLE["z"], "cradle walls 1.6 around the servo"),
        _b("paluba", "ram", "T", (-31.6, 31.6), (-14.3, 15.3), Z_DECK, "deck plate on the cradle walls"),
        _c("paluba_zad", "ram", "T", "z", (0, 0), FPC_PAN["wall"][1], Z_DECK, note="deck under the FPC channel (y > 0 half)"),
        _c("cap_pan", "ram", "T", "z", (0, 0), 3.0, PIVOT["pin_z"]),
        _c("ptfe", "ram", "T", "z", (0, 0), 12.0, Z_PTFE, 6.2),
        _c("kanal_fpc_pan", "ram", "T", "z", (0, 0), FPC_PAN["wall"][1], (Z_DECK[1], FPC_PAN["z"][1]), FPC_PAN["wall"][0],
           "static wall of the pan rolling loop (y > 0 half)"),
        _c("fpc_pan", "ram", "T", "z", (0, 0), FPC_PAN["r_out"], FPC_PAN["z"], R_DRUM, "pan rolling loop (y > 0 half)"),
        _b("servo_pan", "ram", "T", STS3032["x"], STS3032["y"], STS3032["z"], "STS3032, shaft up at PAN_AX"),
        _b("servo_pan_tabs", "ram", "T", STS3032["tab"]["x"], STS3032["y"], STS3032["tab"]["z"]),
        _c("servo_pan_boss", "ram", "T", "z", PAN_AX, STS3032["boss_r"], STS3032["boss_z"]),
        _b("servo_pan_plug", "ram", "T", STS3032["plug"]["x"], STS3032["plug"]["y"], STS3032["plug"]["z"]),
        _c("pastorok_pan", "ram", "T", "z", PAN_AX, 8.0, Z_PAN_PINION, note="mounted from above AFTER T_stred"),
        _c("pastorok_pan_naboj", "ram", "T", "z", PAN_AX, 4.0, STS3032["hub_z"]),
        _b("DPS_riadenie", "ram", "T", CTRL["x"], CTRL["y"], CTRL["z"], "carrier + ESP32-S3-Zero, service through the door"),
        _b("stlp_L", "ram", "T", (X_COL_IN, COL_WEB["rib_x"]), COL_WEB["y"], COL_WEB["z"], "left column (U channel)"),
        _b("stlp_P", "ram", "T", (-COL_WEB["rib_x"], -X_COL_IN), COL_WEB["y"], COL_WEB["z"]),
        _c("stlp_L_naboj", "ram", "T", "x", (SH_Y, SH_Z), R_COL_STOP[0], (X_COL_IN, X_COL_BOSS), note="shoulder boss"),
        _c("stlp_P_naboj", "ram", "T", "x", (SH_Y, SH_Z), R_COL_STOP[0], (-X_COL_BOSS, -X_COL_IN)),
        _c("stlp_L_doraz", "ram", "T", "x", (SH_Y, SH_Z), R_COL_STOP[1], (X_COL_BOSS, X_COL_STOP), R_COL_STOP[0], "stop ring"),
        _c("stlp_P_doraz", "ram", "T", "x", (SH_Y, SH_Z), R_COL_STOP[1], (-X_COL_STOP, -X_COL_BOSS), R_COL_STOP[0]),
        _b("stlp_L_pata", "ram", "T", COL_FOOT["x"], COL_FOOT["y"], COL_FOOT["z"]),
        _b("stlp_P_pata", "ram", "T", (-COL_FOOT["x"][1], -COL_FOOT["x"][0]), COL_FOOT["y"], COL_FOOT["z"]),
        _b("menic", "ram", "T", BUCK["x"], BUCK["y"], BUCK["z"], "D36V28F5 on the right column"),
        _b("zosilnovac", "ram", "T", AMP["x"], AMP["y"], AMP["z"], "MAX98357A on the left column"),
        _c("kondenzator", "ram", "T", "z", CAP470["at"][:2], CAP470["d"] / 2, (CAP470["at"][2] - 6.5, CAP470["at"][2] + 6.5)),
        # ------------------------------------------------------------------ ram (below the cap + dummy)
        _c("pastorok_J1", "ram", "T", "z", J1_AX, 10.0, Z_J1_GEAR),
        _c("lozisko_6805", "ram", "T", "z", (0, 0), 18.5, Z_BRG, 12.5),
        _c("pata_J1", "ram", "T", "z", (0, 0), R_PLINTH, (Z_BRG[1], Z_BOT), R_FOOT_SHOULDER, "plinth / gear housing (notched)"),
        _c("pata_J1_dole", "ram", "T", "z", (0, 0), R_FOOT_LOW, Z_BRG, R_FOOT_SEAT),
        _c("sukna", "ram", "T", "z", (0, 0), SKIRT["r"], SKIRT["z"], R_PLINTH),
        _c("Z_koleso_J1", "ram", "Z", "z", (0, 0), 10.0, Z_J1_GEAR),
        _c("Z_naboj", "ram", "Z", "z", (0, 0), 12.5, (Z_BRG[0] - 2.0, Z_BRG[1])),
        # ------------------------------------------------------------------ obal (shell mounted)
        _c("reproduktor", "obal", "T", "y", (0.0, SPEAKER["z"]), SPEAKER["d"] / 2, SPEAKER["y"], note="behind the grille"),
        _b("led_box", "obal", "T", LED_BOX["x"], LED_BOX["y"], LED_BOX["z"], "light guide flange + LED PCB + holder"),
        _c("rura_goliera", "obal", "T", "z", (0, 0), R_TUBE, (Z_BORE_BOT, Z_IN_TOP), R_BORE, "collar tube = ring seat + journal bearing"),
        _c("klb_L", "obal", "T", "x", (SH_Y, SH_Z), 13.5, (X_SEAT, X_SH + 4.2)),
        _c("klb_L_krk", "obal", "T", "x", (SH_Y, SH_Z), R_KLB_NECK, (X_COL_BOSS, X_SEAT)),
        _c("klb_L_cap", "obal", "T", "x", (SH_Y, SH_Z), 11.0, (X_SH + 4.2, X_KLB_END)),
        _c("klb_P", "obal", "T", "x", (SH_Y, SH_Z), 13.5, (-(X_SH + 4.2), -X_SEAT)),
        _c("klb_P_krk", "obal", "T", "x", (SH_Y, SH_Z), R_KLB_NECK, (-X_SEAT, -X_COL_BOSS)),
        _c("klb_P_cap", "obal", "T", "x", (SH_Y, SH_Z), 11.0, (-X_KLB_END, -(X_SH + 4.2))),
        # ------------------------------------------------------------------ pan (P = turns with pan)
        _b("sachta", "pan", "P", (-WELL_OUT[0] / 2, WELL_OUT[0] / 2), (-WELL_OUT[1] / 2, WELL_OUT[1] / 2),
           (Z_WALL_BOT, -3.0), "well 47 x 22, walls 1.6 (lower edge -41.3; corners trimmed to r 26.5 above z -3.0)"),
        _c("sachta_naboj", "pan", "P", "z", (0, 0), R_HUB, Z_WELL_FLOOR, note="hub disc joining well and gear"),
        _b("sachta_dno_zad", "pan", "P", (-8.0, WELL_OUT[0] / 2), (2.0, WELL_OUT[1] / 2), (Z_BACK_FLOOR[0], Z_WALL_BOT),
           "well floor, back sector only"),
        _c("cap_otocny", "pan", "P", "z", (0, 0), R_JOURNAL, Z_JOURNAL, 24.0, "journal D56.4"),
        _c("vrch_stola", "pan", "P", "z", (0, 0), R_STAGE_TOP, (Z_JOURNAL[1], Z_COLLAR[0]), 0.0),
        _c("golier_kotuc", "pan", "P", "z", (0, 0), COLLAR[0], Z_COLLAR, note="finished part (B)"),
        _c("koleso_pan", "pan", "P", "z", (0, 0), R_DRUM, Z_GEAR_PAN, 3.0),
        _b("servo_zdvih", "pan", "P", LIFT_CASE["x"], LIFT_CASE["y"], LIFT_CASE["z"], "MG90S, shaft along -X"),
        _c("servo_zdvih_veza", "pan", "P", "x", (Y_LIFT, Z_LIFT), MG90S["boss_r"], (xt - 6.0, xt)),
        _c("servo_zdvih_lalok", "pan", "P", "x", (Y_LIFT, Z_LIFT - 5.6), 2.9, (xt - 6.0, xt)),
        _b("servo_zdvih_ucho", "pan", "P", (xb - 18.5, xb - 16.0), LIFT_CASE["y"], (LIFT_CASE["z"][1], LIFT_CASE["z"][1] + 4.85)),
        _b("servo_zdvih_kabel", "pan", "P", (xb - 4.6, xb - 0.1), (Y_LIFT - 2.5, Y_LIFT + 2.5), (LIFT_CASE["z"][1], LIFT_CASE["z"][1] + 5.0)),
        _c("kluka_naboj", "pan", "P", "x", (Y_LIFT, Z_LIFT), CRANK["hub_r"], CRANK["hub_x"]),
        _c("kluka_obalka", "pan", "P", "x", (Y_LIFT, Z_LIFT), R_CRANK + CRANK["tip_r"], CRANK["arm_x"],
           note="crank sweep; only the FRONT half disc (y <= Y_LIFT + 2.2) is used", ),
        _b("drziak_serva", "pan", "P", BRACKET["x"], BRACKET["y"], BRACKET["z"],
           "bracket between the well back wall and the servo"),
        _b("drziak_serva_dno", "pan", "P", (LIFT_X[0], LIFT_X[1]), (BRACKET["y"][1], Y_LIFT + 3.0), (-41.9, LIFT_CASE["z"][0]),
           "ledge under the servo end"),
        _b("fpc_zdvih", "pan", "P", FPC_LIFT["x"], FPC_LIFT["y"], FPC_LIFT["z"], "flexible loop (may be folded during insertion)"),
        # ------------------------------------------------------------------ pan (L = P + lift)
        _b("pata", "pan", "L", (-22.3, 22.3), (-9.8, 9.8), Z_FOOT, "foot under the neck"),
        _b("pata_jazyk", "pan", "L", FOOT["tab"]["x"], FOOT["tab"]["y"], FOOT["tab"]["z"]),
        _b("ucho", "pan", "L", EAR["x"], (EAR["flange"]["y"][1], EAR["y"][1] - EAR["chamfer"]),
           (Z_SLOT_REST + EAR["zrel"][0], Z_SLOT_REST + EAR["zrel"][1])),
        _b("ucho_koniec", "pan", "L", EAR["x"], (EAR["y"][1] - EAR["chamfer"], EAR["y"][1]),
           (Z_SLOT_REST + EAR["zrel"][0], Z_SLOT_REST + EAR["zrel"][1] - EAR["chamfer"])),
        _b("ucho_priruba", "pan", "L", (EAR["flange"]["notch"]["x"][1], EAR["flange"]["x"][1]), EAR["flange"]["y"],
           (Z_SLOT_REST + EAR["flange"]["zrel"][0], Z_SLOT_REST + EAR["flange"]["zrel"][1])),
        _b("ucho_priruba_nizka", "pan", "L", (EAR["flange"]["x"][0], EAR["flange"]["notch"]["x"][1]), EAR["flange"]["y"],
           (Z_SLOT_REST + EAR["flange"]["zrel"][0], Z_SLOT_REST + EAR["flange"]["notch"]["zrel"])),
        _b("krk", "pan", "L", (-22.5, 22.5), (-10.0, 10.0), (Z_NECK_BOT, 6.5), "finished neck (B), envelope"),
    ]
    return E


# swept radius limit of everything on the pan stage (pan frame, any azimuth in the BACK 260 deg): (z0, z1, r_max)
#   below Z_WALL_BOT (-41.3) additionally: r <= R_HUB or stage azimuth inside STAGE_BACK_AZ (see 1.3)
PAN_ENV = [(-45.7, -41.9, 15.9), (-41.9, -22.0, 34.0), (-22.0, -18.0, 33.5), (-18.0, -11.5, 32.2), (-11.5, -10.5, 28.3),
           (-10.5, -4.5, 28.2), (-4.5, -3.0, 28.2), (-3.0, 4.0, 26.5)]
PAN_FRONT = (236.0, 336.0)      # azimuth sector never swept by the lift module (only r <= 28.7: well + FPC loop)
PAN_FRONT_R = 28.7


def env_points(e, h=0.8):
    """surface sample points (n, 3) of an envelope"""
    if e["kind"] == "box":
        (x0, x1), (y0, y1), (z0, z1) = e["x"], e["y"], e["z"]

        def lin(a, b):
            return np.linspace(a, b, max(2, int(math.ceil((b - a) / h)) + 1))
        X, Y, Z = lin(x0, x1), lin(y0, y1), lin(z0, z1)
        P = []
        for x in (x0, x1):
            a, b = np.meshgrid(Y, Z); P.append(np.stack([np.full(a.size, x), a.ravel(), b.ravel()], 1))
        for y in (y0, y1):
            a, b = np.meshgrid(X, Z); P.append(np.stack([a.ravel(), np.full(a.size, y), b.ravel()], 1))
        for z in (z0, z1):
            a, b = np.meshgrid(X, Y); P.append(np.stack([a.ravel(), b.ravel(), np.full(a.size, z)], 1))
        return np.concatenate(P)
    r, ri, (u0, u1) = e["r"], e.get("ri", 0.0), e["rng"]
    n = max(24, int(2 * math.pi * r / h)); th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    us = np.linspace(u0, u1, max(2, int(math.ceil((u1 - u0) / h)) + 1))
    rs = np.linspace(ri, r, max(2, int(math.ceil((r - ri) / h)) + 1))
    P = [np.stack([r * np.cos(th), r * np.sin(th), np.full(n, u)], 1) for u in us]
    P += [np.stack([rr * np.cos(th), rr * np.sin(th), np.full(n, u)], 1) for u in (u0, u1) for rr in rs]
    P = np.concatenate(P)
    c = e["c"]
    if e["axis"] == "z":
        P = P + np.array([c[0], c[1], 0.0])
    elif e["axis"] == "x":
        P = np.stack([P[:, 2], P[:, 0] + c[0], P[:, 1] + c[1]], 1)
    else:
        P = np.stack([P[:, 0] + c[0], P[:, 2], P[:, 1] + c[1]], 1)          # axis y: c = (x, z)
    if e["name"] in ("kanal_fpc_pan", "fpc_pan", "paluba_zad"):               # only the back half exists
        P = P[P[:, 1] >= 0.0]
    if e["name"] == "kluka_obalka":                                           # the crank only sweeps the front half
        P = P[P[:, 1] <= Y_LIFT + CRANK["tip_r"] + 1e-6]
    return P


def np_rot_z(P, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    Q = P.copy(); Q[:, 0] = c * P[:, 0] - s * P[:, 1]; Q[:, 1] = s * P[:, 0] + c * P[:, 1]
    return Q


# =====================================================================================================================
# 6. PART REGISTRY + EXPORT
#    each module:  build() -> dict[name] = dict(shape=<Solid>, group='T'|'P'|'L'|'Z', mat=<key of DENS>, printed=bool,
#                                               label_sk='...')      names: Slovak without diacritics
# =====================================================================================================================
def part(shape, group, mat, printed, label_sk, **extra):
    assert group in GROUPS and mat in DENS, (group, mat)
    d = dict(shape=shape, group=group, mat=mat, printed=bool(printed), label_sk=label_sk)
    d.update(extra)
    return d


def check_part(name, p, bbox=None, tol=0.05):
    """K1-type quick check of one registry entry; returns a dict (valid, n_solids, volume, bbox, ok)"""
    s = p["shape"]
    bb = s.bounding_box()
    r = dict(name=name, valid=bool(s.is_valid), n_solids=len(s.solids()), volume=round(s.volume, 2),
             bbox=[round(v, 3) for v in (bb.min.X, bb.max.X, bb.min.Y, bb.max.Y, bb.min.Z, bb.max.Z)])
    r["ok"] = r["valid"] and r["n_solids"] == 1 and r["volume"] > 0
    if bbox is not None:
        r["bbox_ok"] = all(abs(a - b) <= tol for a, b in zip(r["bbox"], bbox)); r["ok"] = r["ok"] and r["bbox_ok"]
    return r


def export_part(name, p, out=HERE, stl_tol=0.02, ang_tol=0.1, step=True):
    """writes stl/<name>.stl (tolerance 0.02 mm / 0.1 rad) and step/<name>.step; returns the parts.json record"""
    bd = _bd()
    os.makedirs(os.path.join(out, "stl"), exist_ok=True); os.makedirs(os.path.join(out, "step"), exist_ok=True)
    bd.export_stl(p["shape"], os.path.join(out, "stl", name + ".stl"), tolerance=stl_tol, angular_tolerance=ang_tol)
    if step:
        bd.export_step(p["shape"], os.path.join(out, "step", name + ".step"))
    rec = check_part(name, p)
    dens = DENS.get(p["mat"])
    rec["volume_mesh"] = round(mesh_volume(p["shape"]), 2)
    rec.update(group=p["group"], mat=p["mat"], printed=p["printed"], label_sk=p["label_sk"],
               mass_g=p.get("mass", round(rec["volume_mesh"] * dens, 2) if dens else None))
    return rec


def export_all(parts, out=HERE):
    recs = [export_part(n, p, out) for n, p in parts.items()]
    json.dump(recs, open(os.path.join(out, "parts.json"), "w"), indent=1, ensure_ascii=False)
    return recs


def mesh_of(shape, tol=0.05, ang=0.2):
    """(vertices (n, 3), triangles (m, 3)) numpy arrays of a shape"""
    v, t = shape.tessellate(tol, ang)
    return np.array([(p.X, p.Y, p.Z) for p in v]), np.array(t)


def mesh_volume(shape, tol=0.01, ang=0.05):
    """volume from a fine tessellation.  USE THIS for masses: OCC's GProp (shape.volume) is off by up to 4 % on the
    thin B-spline shells (bok_L_blank: GProp 12526 vs mesh 12966 mm3)."""
    V, T = mesh_of(shape, tol, ang)
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)


# =====================================================================================================================
# 7. SELF-TEST
# =====================================================================================================================
def lip_outline(z=Z_WHITE, wall=WALL, count=240):
    """inner outline of the white shell at height z (true offset) as (count, 2)"""
    return inner_section(z, wall, count)[:, :2]


def _selftest(rebuild=False):
    T0 = time.time()
    rep = {}
    print("== T4 common self-test ==")
    print(f"frame: B, TOP {TOP}, white {Z_WHITE}..{TOP}, cap {Z_BOT}..{Z_CAP_TOP}, seams x = +-{XS} ({SEAM})")
    print(f"shoulder axis y {SH_Y} z {SH_Z}: X_SH {X_SH:.3f}, joint end {X_KLB_END:.3f}")
    print(f"rim blend: a g0 {RIM_INFO['a'][0]:.3f} c {RIM_INFO['a'][1]:.4f} | b g0 {RIM_INFO['b'][0]:.3f} c {RIM_INFO['b'][1]:.4f}")
    # ---- exterior fidelity vs T3 (numeric)
    dev = []
    for d in np.linspace(0, 88.5, 1771):
        a, b, n = prof(d); a3, b3, n3 = prof_t3(d)
        dev.append((d, a - a3, b - b3))
    dev = np.array(dev)
    far = dev[dev[:, 0] >= 2.6]
    print(f"profile vs T3: max |da| {np.abs(dev[:, 1]).max():.3f}, max |db| {np.abs(dev[:, 2]).max():.3f} (rim zone drop < 2.6); "
          f"outside the rim zone max {np.abs(far[:, 1:]).max():.4f}")
    rep["profile_dev_outside_rim"] = float(np.abs(far[:, 1:]).max())
    t = time.time(); P, tree = outer_cloud(); print(f"outer cloud {len(P)} pts, {time.time() - t:.1f} s")
    print(" z     outer a      b    | inner(2.2) a_i    b_i")
    for z in (1.75, 0, -2, -4.5, -7.5, -10.5, -12, -14, -17, -20, -25, -30, -38, -46, -55, -65, -75, -78, -80, -81):
        a, b, n = prof(TOP - z); ai, bi = inner_half(z)
        print(f"{z:6.2f}  {a:7.2f} {b:7.2f} |  {ai:7.2f} {bi:7.2f}")
    # ---- wall thickness of the numeric shell
    t = time.time(); worst = 9.0
    for z in INNER_Z:
        Q = inner_section(z, WALL, 240); worst = min(worst, float(dist_outer(Q).min()))
    print(f"inner sections: min distance to the exterior {worst:.3f} (target {WALL}), {time.time() - t:.1f} s")
    rep["inner_min_dist"] = worst
    # ---- spigot / lip
    L = lip_outline(); th = np.arctan2(L[:, 1], L[:, 0])
    rs = se_r(*SPIGOT_SE, th); gap = np.hypot(L[:, 0], L[:, 1]) - rs
    print(f"white lip inner outline at z {Z_WHITE}: a_i {np.abs(L[:, 0]).max():.2f}, b_i {np.abs(L[:, 1]).max():.2f}; "
          f"spigot {SPIGOT_SE}: radial gap {gap.min():.2f} .. {gap.max():.2f}")
    rep["spigot_gap"] = [float(gap.min()), float(gap.max())]
    # ---- CAD cache
    bd = _bd()
    t = time.time(); o = outer_solid(rebuild); print(f"outer: vol {o.volume:.0f} valid {o.is_valid} ({time.time() - t:.1f} s)")
    t = time.time(); i = inner_solid(WALL, rebuild); print(f"inner 2.2: vol {i.volume:.0f} valid {i.is_valid} ({time.time() - t:.1f} s)")
    t = time.time(); sw = shell_white(rebuild); print(f"shell_white: vol {sw.volume:.0f} valid {sw.is_valid} solids {len(sw.solids())} ({time.time() - t:.1f} s)")
    names = [("stred_blank", stred_blank), ("bok_L_blank", lambda r=False: bok_blank(1, r)),
             ("bok_P_blank", lambda r=False: bok_blank(-1, r)), ("cap_blank", cap_blank)]
    for nm, fn in names:
        t = time.time(); s = fn(rebuild); bb = s.bounding_box()
        print(f"{nm}: vol {s.volume:.0f} valid {s.is_valid} solids {len(s.solids())} bbox x {bb.min.X:.2f}..{bb.max.X:.2f} "
              f"y {bb.min.Y:.2f}..{bb.max.Y:.2f} z {bb.min.Z:.2f}..{bb.max.Z:.2f} ({time.time() - t:.1f} s)")
        rep[nm] = dict(volume=s.volume, valid=bool(s.is_valid), solids=len(s.solids()))
    # ---- loft fidelity: mesh vertices of the outer solid vs the analytic surface
    t = time.time(); V, _ = mesh_of(o, 0.01, 0.05)
    m = (V[:, 2] > Z_BOT + 0.02) & (V[:, 2] < TOP - 0.02); V = V[m]
    dev = np.hypot(V[:, 0], V[:, 1]) - outer_r(V[:, 2], np.arctan2(V[:, 1], V[:, 0]))      # radial = upper bound of normal
    mw = V[:, 2] > Z_WHITE
    print(f"outer loft vs analytic surface (radial, {len(V)} mesh vertices): white {dev[mw].min():+.4f} .. {dev[mw].max():+.4f}, "
          f"cap {dev[~mw].min():+.4f} .. {dev[~mw].max():+.4f} ({time.time() - t:.1f} s)")
    rep["outer_loft_dev_white"] = float(np.abs(dev[mw]).max()); rep["outer_loft_dev_cap"] = float(np.abs(dev[~mw]).max())
    t = time.time(); V, _ = mesh_of(i, 0.02, 0.1); d = dist_outer(V)
    m = (V[:, 2] > Z_IN_BOT + 0.01) & (V[:, 2] < Z_IN_TOP - 0.01)
    print(f"inner loft: wall thickness min {d[m].min():.3f} max {d[m].max():.3f} over {m.sum()} side vertices ({time.time() - t:.1f} s)")
    rep["wall_min"], rep["wall_max"] = float(d[m].min()), float(d[m].max())
    vm = mesh_volume(sw)
    print(f"shell_white mesh volume {vm:.0f} mm3 = {vm * DENS['resin_white']:.1f} g (GProp {sw.volume:.0f})")
    for nm, fn in names:
        rep[nm]["volume_mesh"] = mesh_volume(fn())
    print("blank mesh volumes:", {nm: round(rep[nm]["volume_mesh"]) for nm, _ in names})
    rep["shell_white"] = dict(volume=sw.volume, volume_mesh=vm, valid=bool(sw.is_valid), solids=len(sw.solids()),
                              mass_g=vm * DENS["resin_white"])
    rep["outer_volume"], rep["inner_volume"] = o.volume, i.volume
    rep["time_s"] = time.time() - T0
    json.dump(rep, open(os.path.join(HERE, "cache", "selftest.json"), "w"), indent=1)
    print(f"total {time.time() - T0:.1f} s")
    return rep


if __name__ == "__main__":
    _selftest("--rebuild" in sys.argv)


# =====================================================================================================================
# >>> additions by ram   (builder of t4_ram.py) - numbers that were MISSING or had to CHANGE inside the RAM module.
#     Nothing above this block was edited.  Reasons: parts_ram.json["deviations"] / report of the RAM builder.
# =====================================================================================================================
RAM = dict(
    # ---- fasteners (positions in the B frame)
    SCR_DECK=[(-22.9, -15.8), (22.9, -15.8), (-22.9, 15.8), (22.9, 15.8)],   # F3, replaces SCR_DECK: insert hole clear
    #          of the 1.6 cradle wall (was 0.85 left), pan heads clear of the FPC channel wall r 25.1 (was overlapping)
    F3=dict(screw="M2.5x6 pan head ISO 7045 (dk 5.0, k 2.1)", head=(5.0, 2.1)),
    SCR_RAM=[(-22.0, 17.5), (-22.0, -17.5), (20.5, 17.5), (20.5, -17.5), (35.5, 3.0), (-35.5, 3.0)],   # F2, replaces
    #          SCR_RAM: x 18.0 -> 20.5, at 18.0 the countersunk head sat under the plinth wall r 24
    F2=dict(screw="M2.5x6 countersunk ISO 10642", length=6.0),   # x8 would leave the 5.0 boss (tip z -76.5 > -77.3)
    F1=dict(screw="M2.5x8 countersunk ISO 10642", head_z=-84.0),  # head sunk 0.5: the underside curves up at r > 34.7
    F4=dict(screw="M2x6 thread-forming (pan head dk 3.8, k 1.6)", pilot_d=1.7, pilot_depth=4.0),
    #          replaces the M2 inserts of spec F4: the STS3032 tab holes are 2.25 from the case, an insert (OD 3.2,
    #          hole 2.9) would leave a 0.6 wall on the case side; the D1.7 pilot leaves 1.2 / 1.4
    F5=dict(at=(-30.0, 0.0, -74.0), insert_x=-35.2, tool_d=4.6, screw="M2.5x6 set screw ISO 4026", z_was=-65.0),
    #          z -74: below the buck -> reachable later; the insert is heat-set from OUTSIDE (-X) through the tool hole
    F6=dict(screw="M3x6 countersunk ISO 10642", length=6.0),      # x8 would bottom in the servo shaft
    F7=dict(xz=[(18.0, -57.0), (-18.0, -57.0)], rests=[(18.0, -74.0), (-18.0, -74.0)], screw="M2x4 thread-forming"),
    #          controller screws: z -68 was under the ESP32 module; x5 would break into the servo pocket
    F14=dict(screw="M2x4 thread-forming"),                         # buck / amplifier boards on 1.0 standoffs
    # ---- cradle / J1
    CRADLE_X1=25.8,                 # long cradle walls end at x 25.8 (CRADLE x 23.0): roots of the +X deck bosses
    POCKET_J1=dict(x=(-30.3, 16.5), y=(-12.95, 12.95)),   # cap pocket = clearance only; the T_ram walls locate the servo
    J1_BUMPER=dict(x=(16.7, 18.3), z_top=-70.0),          # end stop behind the 1.0 foam pad at the +X servo end
    J1_SPLINE_Z=(-88.1, -85.9),     # servo spline inside the pinion (2.2 engaged; spec 3.5 collides with the M3 head)
    J1_PASS=dict(r=10.8, z=(-91.0, -83.1), skirt_gap_az=(152.0, 208.0)),   # PINION PASSAGE: slot r 10.8 about J1_AX (+-J1_ADJ in x) through plinth,
    #          skirt and floor.  Replaces the boss slot D14.4 + the notch Z_J1_NOTCH: the pinion screw F6 lies at r 18.0,
    #          i.e. under the 6805 outer ring (r 16.3 .. 18.5) and the seat wall - it cannot be reached from below once
    #          the bearing is in.  The pinion is therefore screwed on the servo ON THE BENCH and servo + pinion drop in
    #          from above as one unit (and come out the same way for service).
    SKIRT_TOOL_NOTCH_R=2.6,         # tool channels of the 4 inner F2 screws cut scallops into the skirt disc
    J1_FPC_SLOT=dict(x=(-3.4, 3.4), y=(21.2, 22.5)),      # replaces J1_FPC["floor_slot"] y 21.6 .. 23.0: the plinth
    #          skin outside the slot was 0.76 .. 1.0 (r 24); now 1.26 .. 1.5.  Entry point (0, 21.85) instead of (0, 22.3)
    # ---- deck / pan
    PAN_POST=dict(x=(11.95, 16.25), y_front=-25.0, y_leg=(-26.6, -25.0), top=-58.0, shelf=3.6,
                  window=dict(y=(-25.0, -16.4), z=(-73.2, -61.6))),   # +X post = C-frame around the STS3032 plug zone
    FPC_ANCHOR=dict(   # static end of the pan rolling loop.  Primary side +X (azimuths below); the deck also carries the
        #          MIRRORED provisions (az -> 180 - az) as a spare.  Replaces "anchor at azimuth 150" + the rectangular
        #          deck slot x -18 .. -14 of the spec: with the rotating anchor at gear azimuth 30 (spec 7.2) a rolling
        #          loop (U-turn travel 0.40 x pan) only closes with the static anchor on the SAME side (+X).
        slot_r=(22.5, 23.5), slot_az=(40.0, 52.0),      # arc slot through the deck, tangent to the wall inner face
        clamp_r=(18.8, 23.4), clamp_az=(23.5, 39.5), clamp_z=(-46.0, -43.8), screw_r=21.1, screw_az=31.5,
        screw="M2x4 countersunk thread-forming", pilot_d=1.6,
        loop=dict(rot_anchor_gear_az=30.0, u_turn_az_pan0=92.0, u_turn_travel=(56.0, 128.0), free_length=45.6)),
    PAN_PINION=dict(bore_d=4.0, shaft_z=(-47.7, -44.2), screw="M2x5 countersunk, flush at z -42.3"),
    # ---- columns / electronics
    COL_FLANGE=dict(r=12.8, x=(37.4, 39.1)),    # backing of the stop ring (the ring alone would hang on an edge)
    COL_FOOT_X=(33.0, 37.6),                    # column foot widened inward (F2 insert at x 35.5)
    BOARD_STANDOFF=1.0,                         # buck / amplifier stand 1.0 off the column web (thread depth)
    BUCK_X=(-46.2, -37.4), AMP_X=(37.4, 40.4),  # replaces BUCK["x"] / AMP["x"] (+0.8 outward)
    CAP470_AT=(41.1, 3.0, -45.0),               # +0.1 in x: saddle in the web keeps 1.65 of wall
    CTRL_MODULE=dict(x=(-22.8, 0.7), z=(-77.0, -59.0), usb=(-24.0, 19.7, -68.0)),   # ESP32-S3-Zero on the carrier
    # ---- dummy base hub (Z_naboj_test)
    # integrator (K10): the plate lies FLAT on the bed (z -113.5 .. -108.5, no feet - they put the whole 93 cm2 underside on
    # supports); a pedestal r 22.5 carries the old plate-top level z -104 under the shoulder / stop block; the bolt head stays
    # inside the counterbore (1.4 above the table), which is widened to r 10.5 below z -109.2 for a 13 mm socket
    DUMMY=dict(plate=(110.0, 90.0), plate_z=(-113.5, -108.5), feet_z=-113.5, pedestal=dict(r=22.5, z_top=-104.0),
               post_r=12.48, shoulder_r=14.0,
               stub=(7.0, -90.0),   # r 7.0: 1.0 inside the orbit of the pinion tips (r >= 8.0 from the axis, same z -90.0)
               bolt="ISO 4017 M8x20 from below = steel core + clutch shaft", bolt_head_z=-106.8,
               springs="2x DIN 2093 16x8.2x0.4 in series", seat_z=-105.6, cbore_r=8.75, socket=dict(r=10.5, z_top=-109.2),
               stop=dict(az=270.0, half=21.4, r=(18.2, 21.3), z_top=-98.3)),
)
# <<< end of additions by ram


# =====================================================================================================================
# >>> additions by obal   (builder of t4_obal.py) - numbers that were MISSING or had to CHANGE inside the OBAL module.
#     Nothing above this block was edited.  Reasons: parts_obal.json["deviations"] / STATUS_obal.md.  t4_obal.py keeps
#     the same numbers as its local constants and asserts at import that both copies agree.
# =====================================================================================================================
OBAL = dict(
    # ---- door (supersedes parts of DOOR_LEDGE / DOOR_HOOK / DOOR_MAGNETS)
    DOOR_LEDGE_TOP_GAP=dict(x=20.6, z_above=-16.5),   # ledge omitted along the top edge (top_gap_x 18.0: the hooks reach 20.25)
    DOOR_HOOK=dict(x=16.0, half_u=4.0, inset=(2.75, 3.6), v=(-1.5, 3.3)),   # inset 2.4 left 0.07 to the curved wall -> 0.3
    DOOR_BOSS_FACE_INSET=4.3,                         # door magnet boss D8 x 2.1 (door_boss (8.0, 2.3), face at inset 4.5)
    PAD_INSET=(4.5, 7.2),                             # frame magnet pad (pad_inset (4.7, 7.2)): floor 0.6 behind the pocket
    PAD_RISER=dict(u=(3.6, 7.2), door_clear=0.3),     # pad carrier stays 0.3 outside the door opening down to inset 4.4
    DOOR_NOTCH=dict(w=12.0, h=1.2, depth=0.85),       # finger-nail notch in the bottom edge of the door
    # ---- collar tube
    TUBE_GUSSET=dict(z_start=-6.6, az=((50.0, 130.0), (230.0, 310.0))),   # 45 deg cones in +-Y instead of the 6 ribs
    TUBE_VENT=dict(d=1.6, z=0.4),                     # 2 drain holes along X through the tube
    # ---- front stack
    LED_BOSS_FACE_Y=-31.4, LED_PILOT=4.3,             # spec -33.0 / 5.0 (pilot would leave < 1.2 of skin)
    SPK_BOSS_AZ=(30.0, 150.0, 270.0),                 # supersedes SPK_BOSS["az"] (90 deg boss inside the LED box)
    SPK_SEAT_D=28.3, SPK_GASKET=dict(ri=11.9, ro=14.0),
    SPK_RING=dict(ri=13.0, ro=16.0, t=1.6, notch=dict(x=(-17.5, -12.0), z=(-53.0, -49.0))),   # T_drziak_repro, wire notch at -X
    GUIDE_FLANGE=(33.6, 8.0, 1.2),                    # supersedes GUIDE["flange"] (35 wide hits the LED bosses)
    GRILLE_FLANGE=(22.4, 5.2), GRILLE_BACK_Y=-36.7,   # supersedes GRILLE["flange"]: pill inside the gasket ID 23.8
    GRILLE_SLOTS=dict(n=5, w=0.8, h=1.6, pitch=3.6),
    EXIT_SPK=dict(x=(-16.5, -8.0), y=(-31.6, -30.0), z=(-52.5, -49.5)),   # speaker lugs + first cable bend (reserved space)
    EXIT_LED=dict(x=(-15.0, -9.0), y=(-30.1, -28.9), z=(-34.3, -30.7)),   # LED solder pads + first cable bend
    # ---- side caps / joints
    SEAM_LIP=dict(clear=0.15, t=1.6, x_tip=31.05, z_bot=-77.7),   # ONE continuous lip per cap instead of 8 tabs
    SEAT_NOTCH_R=14.0,                                # supersedes KLB_WIRE["notch_r"] 13.2 (wires pass outside the ring r 12.8)
    KLB_KEY=dict(w=2.9, r=(7.0, 10.9), h=1.4),        # key of T_klb in the column slot 3.0 x 1.5 at azimuth 0
    # ---- export
    STL=dict(deflection_mm=0.01, angular_rad=0.1, relative=False),   # export_part() above meshes RELATIVE to the edge size
)
# <<< end of additions by obal


# =====================================================================================================================
# >>> additions by pan   (builder of t4_pan.py) - numbers that were MISSING or had to CHANGE inside the PAN module.
#     Nothing above this block was edited.  Reasons: parts_pan.json["deviations"] / STATUS_pan.md.
#     All positions in the pan-stage frame (= B frame at pan 0), rest pose (lift 0).
# =====================================================================================================================
PAN = dict(
    # ---- P_sachta: well, journal, guide lands
    WELL_CORNER_OUT=3.1,                               # outer corner radius of the well (inner 1.5 + wall 1.6) -> max r 27.06
    JOURNAL=dict(r_resin=28.07, r_in=25.57, chamfer=0.5, fill_x=20.0, ribs_x=(10.0, -10.0), rib_t=1.6,
                 plate_z=(-3.5, -2.0), cone_z=(-4.5, -3.0), tape=dict(t=0.13, z=(-10.0, -5.0))),
    GLUE_GROOVE=dict(r=(24.4, 25.4), depth=0.3, az=((40.0, 82.0), (98.0, 140.0), (220.0, 320.0))),   # collar-disc bond (B: glue at r > 24)
    TOOL_HOLE=dict(at=(0.0, 21.1), d=4.8, pan=-58.5),  # through the stage top plate: driver for the static FPC clamp screw of
    #          T_prichytka_fpc (B frame (18.0, 11.0)) when the neck is already in the well; covered by the collar disc
    LAND=dict(h=0.70, tape=0.13, z=(-38.0, -4.0), lead=0.7,    # PTFE strip seats = guide lands (neck gap 0.17 with tape)
              front_x=((13.0, 17.0), (-17.0, -13.0)), back_x=((13.0, 17.0),),
              back_up=dict(x=(-17.0, -13.0), z=(-10.4, -4.0)), end_y=((4.9, 8.4), (-8.4, -4.9))),
    FLOOR=dict(z=(-41.9, -41.0), az=(5.0, 140.0)),     # back-sector floor = whole well footprint inside STAGE_BACK_AZ
    WIN_END_Y=(-4.5, 4.5),
    FIN=dict(x=(25.0, 27.6), y=(4.56, 5.76), z=(-41.9, -17.0), edge_r=0.5, r_max=28.15),   # backing of the fixed FPC leg
    APRON=dict(x=(24.0, 27.6), y=(4.56, 8.2)),         # floor continued outside the +X end wall (FPC wraps under it)
    FPC_GROOVE=dict(depth=0.2, grow=0.3),              # groove in the floor underside for the bonded FPC run
    PADS=[dict(x=19.5, z=-31.7), dict(x=8.0, z=-14.5)],   # replaces BRACKET_PADS: lower pad z -30.0 -> -31.7 (the lug and the F10_1
    #          tool channel must pass under the frame magnet pad of T_stred at (25, -24): its silhouette along Y reaches x 18, z -29.14)
    PAD=dict(face_y=15.4, r=3.0, seat_depth=3.2),      # bracket pads (BRACKET_PADS face y 15.6 -> 15.4: bracket 1.7 thick there);
    #          insert hole 3.2 deep leaves 1.2 to the well inner face -> F10 screws M2x4 (2.3 in the insert)
    # ---- P_koleso
    GEAR=dict(phase=4.3, teeth_az=(149.3, 359.3), n_teeth=21, drum_az=(4.0, 145.0), r_root=13.4,
              lip=dict(r=16.5, z=(-42.6, -42.0), az=(22.0, 140.0)), recess=(6.0, -44.0), backlash=0.04,
              stop_pin=dict(r=13.5, az=90.0, d=2.0, length=4.5, z=(-46.7, -42.2)),
              dowel_z=(-45.05, -41.05)),
    # ---- lift servo bracket
    BRKT=dict(plate_x=(-5.3, 16.0), plate_y=(13.0, 17.1), plate_z=(-41.9, -13.0), slot=1.0,
              lug=dict(x=(16.0, 22.9), z=(-36.55, -29.7)), tab2=dict(half=6.0, z_top=-12.3), rest=dict(x=(-5.3, -1.3), z=(-40.0, -34.0), y=12.6),
              ledge=dict(x=(-6.35, 16.0), y=(17.1, 26.2), z=(-41.9, -41.1), lip_x=(-5.0, 10.0), lip_y=(29.45, 30.95), lip_h=1.5),
              post=dict(x=(0.0, 5.0), y=(17.1, 26.2), z=(-18.0, -13.4), pilot_d=1.7, pilot_depth=5.2),
              screw_F10="M2x4 socket head ISO 4762", screw_F11="M2x6 thread-forming pan head"),
    # ---- crank
    CRANK=dict(spline=dict(n=21, d_major=4.84, d_minor=4.44, x=(-15.5, -12.7)), screw="M2.5x6 countersunk ISO 10642",
               pin_hole_d=1.98, pin_len=5.4),
    # ---- ear / foot / tongue
    EAR=dict(flange_y=(9.8, 12.4), plate_y0=10.2, slot_y=(11.6, 24.3),   # slot 2.2 x 12.7: front end +0.5 (EAR slot_y 12.1: the pin
             #          had 0.1 to the slot end at mid stroke, less than the 0.17 float of the neck in the well)
             dowel=dict(x=-15.5, zrel=-4.75, d=1.5, length=5.0),
             screw=dict(x=-10.0, zrel=-4.3, size="M2x8 thread-forming pan head")),
    FOOT=dict(corner_r=0.8, slot=dict(x=(11.6, 15.0), y=(-7.2, 2.6)), pocket=dict(x=(11.0, 20.6), y=(-7.6, 5.6), depth=1.0),
              channel=dict(y=(-1.8, 1.8), depth=0.3), key=dict(x=(21.3, 22.3), y=(-2.6, 2.6), z=(-39.0, -37.6), gap_y=1.1),   # 2 prongs 1.5 wide beside the D1.8 hole
             
              tongue_pilot=dict(y=0.0, z=-38.0, d=1.3, x_end=17.5),
              opt_screws=((-10.0, -5.0), (7.5, -5.0)), ear_pilot=dict(d=1.7, depth=6.5), ear_dowel=dict(d=1.48, depth=3.2)),
    TONGUE=dict(x=(22.3, 27.9), y=(-3.5, 3.5), z=(-40.5, -38.0), block=dict(x=(22.7, 27.9), y=(-2.2, 2.2), z_top=-35.5, chamfer=0.8),
                r_max=28.15, screw="M1.6x10 countersunk DIN 965, along -X, self-tapping in the D1.3 pilot", recess=dict(x=(25.0, 27.9), y=(-3.5, 1.8))),
    # ---- FPC (3.0 x 0.12)
    FPC=dict(w=3.0, t=0.12, lift_x=(25.2, 28.2), y_move=-3.5, y_fix=4.5, z_move0=-38.0, z_fix=-41.76, z_tail=-40.26,
             zc0=-27.5, R=4.0, paddle=dict(x=(15.6, 19.0), y=(-5.2, 5.2), z=-39.56, ramp_x=(19.0, 20.5)),
             trunk=dict(az=14.0, r=(15.9, 27.2)), w_piece=dict(y=(4.4, 7.6)), branch=dict(x=(17.8, 20.8), y0=4.0, z_top=-36.65),
             riser=dict(bend_r=0.56, rho=15.76), pan=dict(r_in=15.76, r_out=23.44, z=(-45.9, -42.9), u0=92.0, k=0.402,
             static_end_az=24.5, tail=dict(az=(44.5, 51.5), z_bot=-51.0)), free_len_lift=37.27),
    JUNCTION=dict(board=dict(x=(16.6, 22.0), y=(12.72, 13.32), z=(-41.0, -36.65)), pins_x=(18.0, 19.27, 20.54), pin_z=-37.85,
                  pin_y=(13.32, 16.3), socket=dict(x=(17.3, 21.25), y=(14.0, 18.3), z=(-38.95, -36.75))),
    LIFT_LOOP_ENV=dict(x=(25.2, 28.2), y=(-3.62, 4.56), z=(-41.9, -13.5)),     # replaces FPC_LIFT (U top -13.5 at lift 20)
)
# <<< end of additions by pan


# =====================================================================================================================
# >>> additions by integrator   (build_all.py / checks.py) - nothing above this block was edited by the integrator
#     unless listed in INTEG["changes"].  The module caches hash the text ABOVE the first "additions" block only.
# =====================================================================================================================
# densities prescribed for parts.json / K11: resin 1.15, PETG 1.27, POM 1.41, brass 8.5, steel 7.85 (g/cm3)
DENS.update(resin_white=1.15e-3, resin_black=1.15e-3, resin_clear=1.15e-3, resin_grey=1.15e-3,
            petg=1.27e-3, pom=1.41e-3, brass=8.5e-3, steel=7.85e-3)
INTEG = dict(
    DENS_RESIN=1.15e-3,                 # was 1.18e-3 in section 1.12 (task of the integrator: resin 1.15)
    STEP_MAX_MB=12.0,                   # STEP is a courtesy export: written only below this size, else step = null
    STL=dict(deflection_mm=0.01, angular_rad=0.1, relative=False),     # every module is exported with t4_obal.export_abs
    # ---- K9: tilt-vs-lift table of variant B (B/montaz.txt, section D).  T4 lift: 0 = rest .. 20 = extended
    TILT_AXIS_Z=-3.5,                   # hinge axis of the head: X axis through (y 0, z -3.5 + lift)
    B_TILT_TABLE={20.0: (40.0, 40.0), 12.5: (30.0, 40.0), 7.5: (20.0, 30.0), 0.0: (5.0, 10.0)},   # lift: (down +, up -)
    HEAD_CLEAR=0.5,                     # brief 5.3: head <-> torso top >= 0.5, otherwise a pan-dependent tilt limit
    MOVE_CLEAR=1.0,                     # K3
    changes=[                           # one line per edit of a module / constant made by the integrator
        "DENS: resin 1.18 -> 1.15 g/cm3 (prescribed for parts.json / K11)",
        "PAN['GEAR']['lip']['z'] (-42.6, -42.2) -> (-42.6, -42.0): retaining lip of P_koleso 0.6 thick (K10 min feature; was 0.4); "
        "its top is 0.1 below the back-sector floor of P_sachta, which turns with it",
        "t4_pan.mk_koleso: blind dowel holes 0.05 (was 0.15) deeper than the dowels -> floor 0.6 (was 0.5)",
        "t4_pan.mk_sachta: FPC groove under the apron runs out to the apron edge (removes a 0.3 x 0.2 rim and a feather edge)",
        "t4_ram.mk_ram / _column: pilots of F7 and F14 and the 4 cradle F2 insert seats are through holes (were 0.4 .. 0.5 floors)",
        "t4_obal._pad / _door_magnets: frame magnet pocket + magnet of the two upper pads 0.5 further out along the wall, band-step "
        "fin removed (0.46 .. 0.50 of resin beside the pocket -> >= 0.6); 0.5 lateral offset to the door magnet",
        "export: every module through t4_obal.export_abs (absolute deflection 0.01); the RAM STLs were relative-deflection before",
        "RAM['DUMMY'] / t4_ram.mk_naboj: Z_naboj_test without the 4 feet - plate flat on the bed (z -113.5 .. -108.5) + pedestal r 22.5 "
        "up to z -104 (old plate top), counterbore widened to r 10.5 below z -109.2 with a 45 deg run-out (13 mm socket on the M8 head); "
        "FDM overhang 9340 -> about 190 mm2 (ceiling of the counterbore only)",
    ],
)
# <<< end of additions by integrator


# =====================================================================================================================
# >>> rev2 (architect)  - REV. 2 of the torso (T4_spec.md section 17).  Binding for the rev. 2 builders.
#     Nothing above this block was edited.  Old names stay valid for rev. 1 code; rev. 2 code reads R2 / the *_R2 names.
#     PAN_ENV is re-bound to the rev. 2 table below (rev. 1 table kept as PAN_ENV_REV1).
#     Quick numeric self-check:  /opt/venv/cad/bin/python -c "import t4_common as C; C.rev2_check()"
# =====================================================================================================================
PAN_ENV_REV1 = PAN_ENV
envelopes_rev1 = envelopes

R2 = dict(
    # ---- frame / stack on the axis (rest, lift 0, pan 0) -------------------------------------------------------------
    STACK=dict(neck_bot=-36.50, foot=(-40.50, -36.50), rest_gap=0.15, rest_gap_range=(0.10, 0.20),
               hub_disc=(-41.90, -40.65), hub_disc_r=(6.50, 12.60), gear=(-45.90, -41.90), ptfe=(-46.20, -45.90),
               deck=(-48.20, -46.20), shim=(-48.30, -48.20), j1_case=(-83.30, -48.30), j1_pads=(-84.50, -83.30)),
    # ---- upper bearing (OBAL bore, PAN journal) ----------------------------------------------------------------------
    BORE=dict(r=26.65, z=(-10.50, -2.00), shoulder_z=-2.00, ring_seat_r=28.35, ring_seat_z=(-2.00, 4.00), tube_r=30.60,
              chamfer=0.5, add_tube=(28.40, 26.65, -10.50, -2.00), tol=(0.0, 0.05)),
    JOURNAL=dict(r_resin=26.37, tape=0.13, r=26.50, z=(-10.00, -3.00), fit=0.15, lead_in=0.5),
    RING_R_IN=26.748,                         # measured (a01 / zjednodusenie m01)
    STAGE_R_MAX=26.50,                        # every permanent stage part
    # ---- pan gears (A3 / A4) -------------------------------------------------------------------------------------------
    GEAR_PAN=dict(m=0.8, z=(18, 36), C=21.600, ax=(-5.85, -20.793), face=4.0, plane=(-45.90, -41.90),
                  pinion=dict(d=14.4, da=16.0, bore=5.00, hub_max_d=12.0, fix="Loctite 638 on the STS3032 spline, no screw"),
                  gear=dict(d=28.8, da=30.4, df=26.8, bore=8.00, type="plain brass/steel, bore 8 H7, bonded under the hub disc"),
                  backlash=(0.04, 0.08)),
    PAN_SERVO=dict(boss_top=-46.20, case_z=(-72.70, -49.70), tab_z=(-56.50, -54.00), post_top=-56.50,
                   note="plain pinion; a pinion hub of length h lowers all by h (washers under the tabs)"),
    DRUM=dict(r_in=15.50, r_out=16.70, az=(8.0, 140.0), z=(-45.60, -41.90), lip_r=(16.70, 17.50), lip_z=(-42.50, -41.90)),
    # ---- pivot (A7) ----------------------------------------------------------------------------------------------------
    PIVOT=dict(boss_d=7.70, tape=0.13, run_d=7.96, boss_z=(-46.20, -41.80), boss_hole=3.4, root_r=1.0,
               washer="DIN 9021 M3 3.2x9x0.8", washer_z=(-41.80, -41.00), axial_play=0.10, axial_play_range=(0.05, 0.20),
               screw="ISO 7380 M3x6", head_z=(-41.00, -39.35), tip_z=-47.00, foot_hole_d=11.0),
    MOST=dict(mat="Al 5754-H22 / 6061-T6 sheet 2.0", x=(-6.0, 12.0), y=(-18.0, 18.0), z=(-48.20, -46.20), corner_r=2.0,
              tap="M3 at (0, 0)", holes=[(6.0, 15.95), (6.0, -15.95)], hole_d=2.8, deck_slot=dict(x=(-6.1, 12.1), y=(-18.1, 18.1))),
    PTFE_WASHER=dict(od=24.0, id=10.0, t=0.30),
    # ---- pan hard stop (A6) --------------------------------------------------------------------------------------------
    STOP=dict(pin_d=3.0, pin_len=12.0, pin_bond=6.0, pin_r=30.0, pin_az=(25.43, 224.57),
              pin_xy=[(27.09, 12.89), (-21.37, -21.06)], pin_top=-44.60, post_d=7.0, post_top=-50.60,
              lug=dict(r=(27.60, 31.60), az=(118.3, 131.7), z=(-47.20, -41.90), root_r=1.5),
              bridge=dict(r=(27.60, 31.60), az=(106.5, 118.3), z=(-43.60, -39.90)), engagement=2.60, stops=(-90.0, 90.0)),
    DECK_TRIM=dict(r=26.6, az=(16.0, 232.0)),
    # ---- slim stage (PAN) ----------------------------------------------------------------------------------------------
    WELL=dict(inner=(47.0, 22.0), corner_r=2.5, wall=1.6, back_wall=(11.0, 13.0), back_wall_x=(-6.0, 20.0),
              edge_z_front=-40.90, edge_z_back=-41.90, back_sector=(5.0, 140.0), top_plate=(-3.50, -2.00)),
    WIN_BACK=dict(x=(-20.9, -6.5), y=(11.0, 13.0), z=(-40.9, -10.9)),
    WIN_END=dict(x=(23.4, 25.1), y=(-6.5, 6.5), z=(-40.9, -15.0)),
    F10_PADS=[dict(x=19.5, z=-31.7), dict(x=8.0, z=-14.5)], F10_PAD=dict(face_y=15.10, r=3.5, root_r=1.0),
    F10_DOWEL=dict(x=19.5, z=-27.7, d=2.0, hole=2.05, depth=3.5),
    # ---- lift module (PAN) ---------------------------------------------------------------------------------------------
    LIFT_POCKET=dict(turret_wall=dict(x=(-8.5, -6.5), y=(15.1, 29.3), z=(-41.9, -16.3),
                                      keyhole=[(6.05, (23.2, -24.2)), (3.05, (23.2, -29.8))]),
                     end_wall=dict(x=(16.0, 18.0), y=(15.1, 26.5), z=(-41.9, -18.3), foam=0.5),
                     back_plate=dict(x=(-8.5, 18.0), y=(15.1, 17.1), z=(-41.9, -13.0)),
                     post=dict(x=(0.0, 8.0), y=(17.1, 26.2), z=(-18.0, -12.3), nut_slot_x=(5.0, 6.3)), root_r=1.0),
    CRANK=dict(r=10.00, r_tol=0.05, arm_x=(-17.5, -15.5), pin="ISO 8734 2 m6 x 8", pin_x=(-20.4, -12.4)),
    EAR=dict(mat="304 stainless 1.5 (or 6061-T6 2.0)", plate_x=(-19.9, -17.9), plate_y=(9.9, 25.1), plate_z=(-40.5, -31.9),
             chamfer=1.5, slot_w=2.20, slot_y=(11.6, 24.3), slot_z=(-35.30, -33.10),
             flange=dict(x=(-19.9, -7.5), y=(9.9, 11.9), z=(-40.5, -36.5)), bend_r=(2.0, 1.5)),
    FOOT=dict(mat="Al flat bar 20x4 (6060/6061/5754)", x=(-22.3, 22.3), y=(-9.8, 9.8), z=(-40.5, -36.5), corner_r=0.8,
              hole_d=11.0, slot=dict(x=(9.0, 22.3), y=(-7.4, 6.4)),
              taps=[(-15.0, -38.5), (-9.0, -38.5)], tap="M2, drill 1.6 x 7, thread 5"),
    # ---- J1 / T_spodok (RAM) -------------------------------------------------------------------------------------------
    J1=dict(gear_plane=(-90.00, -86.00), pinion_bore=6.00, face=4.0, fix="Loctite 638 on the STS3215 spline, no screw",
            pads=dict(size=(5.0, 5.0), top=-83.30), window="case footprint minus the 4 corner pads",
            screws="4 x M2 x 6 through the pads into the case holes (positions UNVERIFIED)", c_shim=0.2,
            stop_lug=dict(w=4.0, r=(17.0, 21.0), z=(-102.0, -98.0), az=90.0, root_r=1.0), base_stop=dict(az=270.0, half=19.0)),
    SEAT_6805_D=37.15,
    CRADLE=dict(wall=2.5, y_in=12.55, y_out=15.05, x=(-32.2, 25.8), end_wall_x=(-32.2, -29.7), z=(-82.3, -48.2), root_r=2.0),
    COLUMN=dict(web_x=(34.4, 37.4), y=(-9.0, 15.0), ribs_y=((-9.0, -6.5), (12.5, 15.0)), rib_x=42.0,
                box=dict(x=(40.0, 42.0), z=(-52.0, -34.0)), foot_x=(33.0, 37.6), root_r=2.0,
                f8_az=(60.0, 180.0, 300.0), key_az=0.0),
    PAN_POSTS=dict(x=((11.25, 17.25), (-17.25, -11.25)), y=(-24.6, -17.1), top=-56.50, nut="DIN 562 M2"),
    F3A=[(20.0, 13.8), (20.0, -13.8), (-33.5, 10.0), (-33.5, -10.0)], F3B=[(6.0, 15.95), (6.0, -15.95)],
    F7=[(19.0, -62.5), (-19.0, -62.5)], F7_FACE_Y=16.50,
    CAP470=dict(axis="x", x=(6.0, 19.0), y=20.2, z=-77.0, saddle_r=5.1, tie_slot=(2.8, 1.2)),
    BASE_FFC_SLOT=dict(x=(-6.0, 6.0), y=(21.2, 22.5)),
    SPIGOT_NOTCH_W=7.8,
    BUCK_X=(-47.7, -38.9), AMP_X=(38.9, 41.9), BOARD_AIR=1.5,
    # ---- cables / electronics ------------------------------------------------------------------------------------------
    FFC=dict(pitch=0.5, poles=5, w=3.0, t=0.10, t_end=0.3, length=203.0, n=2, contacts="Type A (same side)",
             z=(-46.10, -43.10), wall=(23.50, 25.10), wall_top=-43.00, wall_az=(15.0, 165.0),
             deck_slot=dict(r=(22.4, 23.6), az=(26.0, 34.0)), cradle_slot=dict(x=(17.0, 24.0), z=(-51.0, -50.0)),
             drum_r=16.70, uturn_R=3.2, k=0.415, u0=84.0, static_anchor_az=30.0, rot_anchor_az=14.0, free_len=52.6),
    FFC_LIFT2=dict(x=(25.1, 31.3), y=(-3.5, 3.5), z=(-41.5, -13.5), r_max=31.7, R=3.0),
    PIGTAIL=dict(x=(25.1, 30.0), y=(4.0, 7.0), z=(-41.0, -14.0), plug="Dupont 1x3 2.54"),
    DPS_KRK=dict(pcb=(13.0, 13.4, 0.8), x=(9.2, 22.2), y=(-6.9, 6.5), top_z=-37.00,
                 zif="Hirose FH19SC-5S-0.5SH (x2)", zif_mouth_x=22.2, zif_z=(-38.00, -37.00),
                 zif_y=((-6.4, -1.2), (0.2, 5.4))),
    CTRL2=dict(pcb=(46.0, 18.0, 1.6), x=(-23.0, 23.0), y=(16.50, 18.10), parts_y_max=23.5, z=(-71.5, -53.5),
               module=dict(x=(-0.5, 23.0), usb_mouth=(-0.5, 20.2, -62.5), usb_dir="-X"),
               plug_env=dict(x=(-21.0, -0.5), y=(17.0, 24.0), z=(-66.5, -58.5)),
               zif_pan=[(-22.5, -16.4), (-15.4, -9.3)], zif_pan_z=(-57.5, -53.5),
               bus_v=dict(x=(-8.5, -1.0), z=(-58.0, -53.5)), zif_j1=dict(x=(-22.5, -8.0), z=(-71.5, -67.0)),
               bus_5=dict(x=(-7.5, -0.5), z=(-71.5, -67.0))),
    # ---- shells (OBAL) -------------------------------------------------------------------------------------------------
    F1_BOSS_R=3.4,
    DOOR_TONGUE=dict(x=(-20.6, 20.6), inset=(1.1, 2.2), z=(-12.75, -11.75), door_inner_top=-13.00, door_outer_top=-12.00),
    KLB=dict(neck_x=(38.6, 40.6), step_r=0.5, f8_az=(60.0, 180.0, 300.0), magnet_az=(0.0, 120.0, 240.0)),
    REPRO_RING_T=2.0,
    # ---- fasteners / torque --------------------------------------------------------------------------------------------
    SCREW_KINDS=("ISO 7380 M2x6", "ISO 7380 M2x10", "ISO 7380 M2.5x6", "ISO 7380 M2.5x8", "ISO 7380 M3x6",
                 "M2x6 thread-forming for plastics (one-time)"),
    INSERT_HOLES=dict(M2=dict(od=3.2, l=3.0, hole=3.3, depth=3.3, boss_r=3.25), M25=dict(od=3.5, l=4.0, hole=3.6, depth=4.3, boss_r=3.4)),
    TORQUE=dict(M2_insert=0.05, M25_insert=0.09, M2_nut_on_resin=0.05, M2_thread_forming=0.04, M2_metal=0.15,
                M3_pivot=0.12, J1_pads=0.05),
    WASHERS=dict(M2="DIN 125 2.2x5x0.3", M25="DIN 125 2.7x6x0.5", M3_pivot="DIN 9021 3.2x9x0.8"),
    # ---- ownership (rev. 2) --------------------------------------------------------------------------------------------
    OWNER=dict(
        obal=["T_stred", "T_bok_L", "T_bok_P", "T_dvere", "T_klb_L", "T_klb_P", "T_svetlovod", "T_mriezka",
              "T_drziak_led", "T_drziak_repro"],
        ram=["T_spodok", "T_paluba", "T_cap", "T_most", "Z_naboj_test", "servo_J1", "pastorok_J1", "servo_pan",
             "pastorok_pan", "koliky_dorazu", "DPS_riadenie", "menic", "zosilnovac", "kondenzator", "ptfe_podlozka"],
        pan=["P_sachta", "P_drziak_serva", "koleso_pan", "rameno_zdvih", "cap_kluky", "servo_zdvih", "L_ucho", "L_pata",
             "DPS_krk", "ffc_A", "ffc_B", "pigtail_zdvih", "kolik_F10"],
        deleted=["T_ram", "T_prichytka_fpc", "T_puzdro_L", "T_puzdro_P", "P_koleso", "P_kluka", "L_jazyk", "fpc_pan",
                 "spoj_zdvih", "cap_pan", "kolik_dorazu", "kolik_kolesa_1", "kolik_kolesa_2", "kolik_ucha"]),
)

# rev. 2 swept-radius table of the pan stage (stage frame): (z0, z1, r_max); special sectors in PAN_ENV2_SECTORS
PAN_ENV2 = [(-47.20, -41.90, 17.50), (-41.90, -40.90, 12.60), (-40.90, -17.00, 33.40), (-17.00, -11.50, 32.20),
            (-11.50, 4.00, 26.50)]
PAN_ENV2_SECTORS = [dict(z=(-47.20, -39.90), r=31.60, az=(106.5, 131.7), what="stop lug + bridge (lift module)"),
                    dict(z=(-41.90, -40.90), r=26.50, az=(5.0, 140.0), what="back floor"),
                    dict(z=(-41.90, -40.90), r=33.40, az=(35.0, 140.0), what="lift module bottom")]
PAN_ENV = PAN_ENV2                       # rev. 2 binding; rev. 1 code that needs the old table: PAN_ENV_REV1

# rev. 2 aliases (old names -> rev. 2 values) for code that reads single constants
R_BORE_JOURNAL = R2["BORE"]["r"]          # 26.65 (R_BORE 28.35 stays = ring seat radius)
R_JOURNAL_R2 = R2["JOURNAL"]["r"]         # 26.50 (R_JOURNAL 28.20 is rev. 1)
FOOT_GAP_R2 = R2["STACK"]["rest_gap"]     # 0.15 (FOOT_GAP 0.5 is rev. 1)
Z_DECK_R2 = R2["STACK"]["deck"]           # (-48.20, -46.20)
Z_PTFE_R2 = R2["STACK"]["ptfe"]
Z_GEAR_PAN_R2 = R2["GEAR_PAN"]["plane"]
Z_J1_GEAR_R2 = R2["J1"]["gear_plane"]
PAN_STOP_R2 = R2["STOP"]
FPC_PAN_R2 = R2["FFC"]
FPC_LIFT_R2 = R2["FFC_LIFT2"]
WIN_END_R2 = R2["WIN_END"]
CTRL_R2 = R2["CTRL2"]


def envelopes_rev2():
    """rev. 2 space reservation: rev. 1 list minus deleted / replaced zones, plus the rev. 2 zones (B frame, rest)."""
    drop = {"sukna", "cap_pan", "fpc_pan", "fpc_zdvih", "pata_jazyk", "cap_otocny", "vrch_stola", "koleso_pan",
            "kluka_naboj", "kluka_obalka", "drziak_serva", "drziak_serva_dno", "ucho", "ucho_koniec", "ucho_priruba",
            "ucho_priruba_nizka", "ptfe", "paluba", "paluba_zad", "kanal_fpc_pan", "DPS_riadenie", "servo_pan",
            "servo_pan_tabs", "servo_pan_boss", "servo_pan_plug", "pastorok_pan", "pastorok_pan_naboj", "pastorok_J1",
            "Z_koleso_J1", "stlp_L", "stlp_P", "menic", "zosilnovac", "kondenzator", "sachta", "sachta_naboj",
            "sachta_dno_zad", "pata"}
    E = [e for e in envelopes_rev1() if e["name"] not in drop]
    S, G, P2, St = R2["STACK"], R2["GEAR_PAN"], R2["PAN_SERVO"], R2["STOP"]
    ax = G["ax"]
    E += [
        _b("paluba", "ram", "T", (-36.9, 31.6), (-18.1, 25.1), S["deck"], "deck lid 2.0 (C-shape, trimmed r <= 26.6 in B az 16..232)"),
        _b("T_most", "ram", "T", R2["MOST"]["x"], R2["MOST"]["y"], R2["MOST"]["z"], "Al pivot bridge"),
        _c("T_cap", "ram", "T", "z", (0, 0), R2["PIVOT"]["run_d"] / 2, R2["PIVOT"]["boss_z"], note="pivot boss + tape"),
        _c("pivot_washer", "ram", "T", "z", (0, 0), 4.5, (R2["PIVOT"]["washer_z"][0], R2["PIVOT"]["head_z"][1]), note="washer + F15 head"),
        _c("ptfe", "ram", "T", "z", (0, 0), 12.0, S["ptfe"], 5.0),
        _c("kanal_fpc_pan", "ram", "T", "z", (0, 0), R2["FFC"]["wall"][1], (S["deck"][1], R2["FFC"]["wall_top"]),
           R2["FFC"]["wall"][0], "static FFC wall, B az 15..165"),
        _b("servo_pan", "ram", "T", STS3032["x"], STS3032["y"], P2["case_z"], "STS3032 (plain pinion)"),
        _b("servo_pan_tabs", "ram", "T", STS3032["tab"]["x"], STS3032["y"], P2["tab_z"]),
        _c("servo_pan_boss", "ram", "T", "z", ax, STS3032["boss_r"], (P2["case_z"][1], P2["boss_top"])),
        _c("pastorok_pan", "ram", "T", "z", ax, 8.0, G["plane"], note="18T m0.8, on the spline"),
        _c("pastorok_J1", "ram", "T", "z", J1_AX, 10.0, R2["J1"]["gear_plane"]),
        _c("Z_koleso_J1", "ram", "Z", "z", (0, 0), 10.0, R2["J1"]["gear_plane"]),
        _c("kolik_dorazu_1", "ram", "T", "z", St["pin_xy"][0], 1.5, (St["post_top"], St["pin_top"])),
        _c("kolik_dorazu_2", "ram", "T", "z", St["pin_xy"][1], 1.5, (St["post_top"], St["pin_top"])),
        _c("stlpik_dorazu_1", "ram", "T", "z", St["pin_xy"][0], 3.5, (Z_FLOOR, St["post_top"])),
        _c("stlpik_dorazu_2", "ram", "T", "z", St["pin_xy"][1], 3.5, (-57.6, St["post_top"])),
        _b("stlp_L", "ram", "T", (X_COL_IN, 42.0), R2["COLUMN"]["y"], (-78.0, -30.0), "column web 3.0 + box z -52..-34"),
        _b("stlp_P", "ram", "T", (-42.0, -X_COL_IN), R2["COLUMN"]["y"], (-78.0, -30.0)),
        _b("menic", "ram", "T", R2["BUCK_X"], BUCK["y"], BUCK["z"], "1.5 air to the web"),
        _b("zosilnovac", "ram", "T", R2["AMP_X"], AMP["y"], AMP["z"]),
        _c("kondenzator", "ram", "T", "x", (R2["CAP470"]["y"], R2["CAP470"]["z"]), 5.0, R2["CAP470"]["x"], note="saddle + tie"),
        _b("DPS_riadenie", "ram", "T", R2["CTRL2"]["x"], (R2["CTRL2"]["y"][0], R2["CTRL2"]["parts_y_max"]), R2["CTRL2"]["z"]),
        _b("usb_zastrcka", "ram", "T", R2["CTRL2"]["plug_env"]["x"], R2["CTRL2"]["plug_env"]["y"], R2["CTRL2"]["plug_env"]["z"],
           "USB-C plug envelope - keep free"),
        # ---- pan (P, stage frame) / lift (L, rest)
        _b("sachta", "pan", "P", (-25.1, 25.1), (-12.6, 13.0), (-41.9, -2.0), "slim well, r <= 26.5"),
        _c("vrch_stola", "pan", "P", "z", (0, 0), R2["STAGE_R_MAX"], (R2["JOURNAL"]["z"][0], -2.0), note="journal + top plate"),
        _c("sachta_naboj", "pan", "P", "z", (0, 0), 12.6, S["hub_disc"], 6.5),
        _c("koleso_pan", "pan", "P", "z", (0, 0), 15.2, G["plane"], 4.0, "36T brass"),
        _c("buben", "pan", "P", "z", (0, 0), R2["DRUM"]["lip_r"][1], R2["DRUM"]["z"], R2["DRUM"]["r_in"], "drum shroud az 8..140"),
        _b("drziak_serva", "pan", "P", (-8.5, 18.0), (15.1, 29.3), (-41.9, -12.3), "lift pocket"),
        _b("fpc_zdvih", "pan", "P", R2["FFC_LIFT2"]["x"], R2["FFC_LIFT2"]["y"], R2["FFC_LIFT2"]["z"]),
        _b("pigtail_zdvih", "pan", "P", R2["PIGTAIL"]["x"], R2["PIGTAIL"]["y"], R2["PIGTAIL"]["z"]),
        _b("pata", "pan", "L", R2["FOOT"]["x"], R2["FOOT"]["y"], R2["FOOT"]["z"], "Al foot"),
        _b("ucho", "pan", "L", R2["EAR"]["plate_x"], R2["EAR"]["plate_y"], R2["EAR"]["plate_z"], "metal ear plate"),
        _b("ucho_priruba", "pan", "L", R2["EAR"]["flange"]["x"], R2["EAR"]["flange"]["y"], R2["EAR"]["flange"]["z"]),
        _b("DPS_krk", "pan", "L", R2["DPS_KRK"]["x"], R2["DPS_KRK"]["y"], (R2["DPS_KRK"]["zif_z"][0], R2["DPS_KRK"]["top_z"])),
    ]
    return E


def rev2_check(verbose=True):
    """numeric self-check of the rev. 2 numbers (no CAD).  Returns a dict; prints a short report."""
    out = {}
    S = R2["STACK"]
    stack = (S["foot"][1] - S["foot"][0]) + S["rest_gap"] + (S["hub_disc"][1] - S["hub_disc"][0]) + \
            (S["gear"][1] - S["gear"][0]) + (S["ptfe"][1] - S["ptfe"][0]) + (S["deck"][1] - S["deck"][0]) + \
            (S["shim"][1] - S["shim"][0]) + (S["j1_case"][1] - S["j1_case"][0]) + (S["j1_pads"][1] - S["j1_pads"][0])
    out["stack_sum"] = round(stack, 3); out["stack_target"] = round(Z_NECK_BOT - Z_BOT, 3)
    out["stage_vs_ring"] = round(R2["RING_R_IN"] - R2["STAGE_R_MAX"], 3)
    out["journal_radial"] = round(R2["BORE"]["r"] - R2["JOURNAL"]["r"], 3)
    out["tube_wall"] = round(R2["BORE"]["tube_r"] - R2["BORE"]["r"], 3)
    G = R2["GEAR_PAN"]
    out["C_pan_from_ax"] = round(math.hypot(*G["ax"]), 3)
    out["pivot_radial_clear"] = round((G["gear"]["bore"] - R2["PIVOT"]["run_d"]) / 2, 3)
    out["washer_overlap"] = round(9.0 / 2 - G["gear"]["bore"] / 2, 3)
    # stop: contact angles from lug faces and pin size
    St = R2["STOP"]; half_pin = math.degrees(St["pin_d"] / 2 / St["pin_r"])
    out["stop_pin_az_expected"] = (round(St["lug"]["az"][0] - 90.0 - half_pin, 2), round(St["lug"]["az"][1] + 90.0 + half_pin, 2))
    out["stop_pin_xy"] = [(round(St["pin_r"] * math.cos(math.radians(a)), 2), round(St["pin_r"] * math.sin(math.radians(a)), 2))
                          for a in St["pin_az"]]
    out["stop_engagement"] = round(St["pin_top"] - St["lug"]["z"][0], 2)
    out["stop_bridge_over_pin"] = round(St["bridge"]["z"][0] - St["pin_top"], 2)
    out["lug_over_cradle"] = round(St["lug"]["z"][0] - R2["CRADLE"]["z"][1], 2)
    # pinion zone vs drum shroud
    C = G["C"]; r = R2["DRUM"]["lip_r"][1]; ra = G["pinion"]["da"] / 2
    th = math.degrees(math.acos((r * r + C * C - ra * ra) / (2 * r * C)))
    out["pinion_halfangle_at_drum_r"] = round(th, 2)
    paz = math.degrees(math.atan2(G["ax"][1], G["ax"][0])) % 360.0            # 254.3
    out["drum_margin_deg"] = (round(R2["DRUM"]["az"][0] - (paz + 90.0 + th - 360.0), 2),      # start side (pan -90)
                              round((paz - 90.0 - th) - R2["DRUM"]["az"][1], 2))             # end side (pan +90)
    out["drum_margin_mm"] = tuple(round(math.radians(a) * r, 2) for a in out["drum_margin_deg"])
    # rolling loop
    F = R2["FFC"]; k = F["drum_r"] / (F["drum_r"] + F["wall"][0])
    out["loop_k"] = round(k, 3); out["uturn_B_az"] = (round(F["u0"] - 90 * k, 1), round(F["u0"] + 90 * k, 1))
    out["uturn_stage_az"] = (round(F["u0"] - 90 * (1 - k), 1), round(F["u0"] + 90 * (1 - k), 1))
    out["uturn_R"] = round((F["wall"][0] - F["drum_r"] - 2 * F["t"]) / 2, 2)
    out["duct_height"] = round(S["hub_disc"][0] - S["deck"][1], 2)
    out["ffc_wall_to_floor"] = round(S["hub_disc"][0] - F["wall_top"], 2)
    # shell margins of PAN_ENV2
    mar = []
    for z0, z1, rr in PAN_ENV2:
        b = min(inner_half(z0)[1], inner_half(z1)[1]) if z1 < 1.0 else inner_half(1.75)[1]
        mar.append((z0, z1, rr, round(b, 2), round(b - rr, 2)))
    out["pan_env_shell_margin"] = mar
    out["column_vs_env"] = round(X_COL_IN - 33.40, 2)
    # stop posts / carrier inside the white lip outline (z -81) - 0.5
    L = lip_outline(); th_ = np.arctan2(L[:, 1], L[:, 0]); rl = np.hypot(L[:, 0], L[:, 1])
    def lip_r(x, y):
        a = math.atan2(y, x); i = int(np.argmin(np.abs(np.angle(np.exp(1j * (th_ - a))))))
        return float(rl[i])
    pts = {"post1_far": (St["pin_xy"][0][0] + 3.5 * math.cos(math.radians(St["pin_az"][0])), St["pin_xy"][0][1] + 3.5 * math.sin(math.radians(St["pin_az"][0]))),
           "post2_far": (St["pin_xy"][1][0] + 3.5 * math.cos(math.radians(St["pin_az"][1])), St["pin_xy"][1][1] + 3.5 * math.sin(math.radians(St["pin_az"][1]))),
           "carrier_corner": (23.0, 23.5), "f3a_head": (-33.5 - 2.35, 10.0)}
    out["lip_margin"] = {k_: round(lip_r(*p) - math.hypot(*p), 2) for k_, p in pts.items()}
    out["f3a_head_vs_lug_r"] = round(math.hypot(-33.5, 10.0) - 2.35 - St["lug"]["r"][1], 2)
    if verbose:
        for k_, v in out.items():
            print(f"{k_}: {v}")
    return out
# <<< end of rev2 (architect)
