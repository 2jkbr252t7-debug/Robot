"""K3 'J1 in the base' – layout generator for t1lib.  Writes layout.json next to this file.
World mm, Z up, floor z=0, FRONT=-Y, robot RIGHT=-X.  Run: /opt/venv/cad/bin/python gen_layout.py

Concept summary (details in koncept.md):
  * BASE: soft pebble 148 x 118 x 34 (z 6..40).  2 x N20 coaxial on y=0, wheels D30 at x +-56.5, 4 ball casters.
    4 x 18650 split into two 1S2P packs (front / rear, cells along X) at |y| >= 13.4 on the floor (bottom hatches).
    J1 STS3215 STANDING on the J1 axis, direct drive, body along +X, sitting on a bridge ABOVE the left N20 motor
    (z 21.9..56.9).  Its top 17 mm rise above the base top inside a dark static PLINTH drum r 37.5 that carries the
    6806 J1 bearing at z 57.3..64.3.  J1 rolling loop (4 wires) in the annulus r 24..33.5 on top of the plinth.
  * TORSO: open-bottom soft shell 92 x 84 x 90.6 (z 42..Z_TT) swallowing the plinth; deck at z 64.6.
    PAN stage on the axis (pivot in the deck, PTFE thrust under the collar disc), driven by an STS3032 (360 deg)
    inverted at the +X side through an idler, 2:1.  LIFT = MG90S crank (scotch yoke) under the neck, tongue at -X.
    ARMS: nano servo (HS-35HD class) inside 21 mm paddles, spline into a torso shoulder boss.
"""
import json, os, math

HERE = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ master numbers
Z_TT = 127.8                       # torso top = collar disc top (crank centre 80.2 + 47.6)
ZC_LIFT = Z_TT - 47.6              # lift servo shaft (crank centre) z
SH = [0.0, round(Z_TT - 18.0, 2)]  # shoulder axis (y, z)
# base
BA, BB, BN, BZ0, BZ1, BRF, BW = 74.0, 59.0, 2.4, 6.0, 40.0, 10.0, 2.0
FLOOR = BZ0 + BW                   # 8.0 inner floor
WHX, WHR, WHW, WHZ = 56.5, 15.0, 9.0, 15.0           # wheel centre x, radius, width, axle z
MOT_IN, MOT_OUT = 16.5, 50.5                          # N20 body |x| range (gearbox face at 50.5)
CAST = [(46.0, 30.0), (-46.0, 30.0), (46.0, -30.0), (-46.0, -30.0)]
PACK_L, PACK_D, PACK_H = 66.5, 38.8, 19.4
PACK_Y0 = 13.4                                        # inner face |y|
PACK_Z0 = FLOOR + 0.3
# J1 servo STS3215 (case 45.2 x 24.7 x 35, shaft 11.5 from the -X end on the centre line)
S_L, S_W, S_H, S_SH = 45.2, 24.7, 35.0, 11.5
S_Z0 = 21.9
S_Z1 = S_Z0 + S_H                                     # 56.9
DECK_Z0, DECK_Z1 = 29.0, 31.0                         # base deck
PL_R, PL_RI = 37.5, 36.0                              # plinth drum
PL_Z0 = 34.5
PL_TOP0, PL_TOP1 = 57.1, 58.6                         # plinth top plate
BRG_Z0, BRG_Z1 = 57.9, 64.9                           # 6806 J1 bearing (inner ring 1.0 above the servo top)
TDECK_Z0, TDECK_Z1 = 65.2, 67.2                       # torso deck (2.0, ribbed)
GEAR_Z0, GEAR_Z1 = 67.5, 70.0                         # pan gear plane (2.5 wide)
CUP_Z0, CUP_Z1 = 71.0, 72.2                           # pan cup bottom plate (notched under crank + tongue)
WELL_Z0, WELL_Z1 = Z_TT - 40.6, Z_TT - 6.0            # well (neck bottom at rest = Z_TT - 40.5)
# torso shell
TA, TB, TN, TZ0, TRF, TW = 46.0, 42.0, 2.35, 42.0, 16.0, 2.2

C = []
ALLOW = []


def add(**k):
    C.append(k)
    return k


def box(sx, sy, sz, at, **k):
    return dict(kind="box", size=[sx, sy, sz], at=[round(v, 3) for v in at], **k)


def cyl(r, h, at, axis="z", **k):
    return dict(kind="cyl", r=r, h=h, axis=axis, at=[round(v, 3) for v in at], **k)


def tube(r, ri, h, at, axis="z", **k):
    return dict(kind="tube", r=r, ri=ri, h=h, axis=axis, at=[round(v, 3) for v in at], **k)


def zr(z0, z1):
    return (z0 + z1) / 2.0, z1 - z0


def allow(a, b):
    ALLOW.append([a, b])


# =================================================================== BASE (group B, static)
add(name="Z_shell", kind="sshell", a=BA, b=BB, n=BN, h=BZ1 - BZ0, rf=BRF, wall=BW, at=[0, 0, (BZ0 + BZ1) / 2],
    group="B", mat="resin", color="white",
    label="podstavec – mäkký „kamienok“ 148×118×34 (zástupný tvar n 2.4, R10)",
    cuts=[cyl(38.3, 6, [0, 0, BZ1 - 1]),                                           # plinth opening in the top
          box(12, 30, 6, [WHX, 0, BZ0 + 1]), box(12, 30, 6, [-WHX, 0, BZ0 + 1]),    # wheel slots in the floor
          *[cyl(7.0, 6, [x, y, BZ0 + 1]) for x, y in CAST],                         # caster holes
          *[cyl(2.5, 6, [x, y, BZ0 + 1]) for x, y in [(44, 41), (-44, 41), (44, -41), (-44, -41)]],  # cliff IR
          box(20, 8, 15, [0, -BB + 1, 19.5]),                                       # ToF window (dark)
          box(40, 8, 3.2, [0, -BB + 1, 29.75]),                                     # front light bar slot
          box(10, 8, 4.0, [14, BB - 1, 33.1]),                                      # USB-C
          box(5, 8, 2.5, [-22, BB - 1, 33.5])])                                     # power switch lever slot

for s, nm in ((-1, "R"), (1, "L")):
    add(name=f"Z_koleso_{nm}", **cyl(WHR, WHW, [s * WHX, 0, WHZ], "x"), group="B", mass=7, color="rubber",
        label=f"koleso Ø30×9 (náboj PETG + pneumatika TPU) – {'pravé' if s < 0 else 'ľavé'}")
    xc = s * (MOT_IN + MOT_OUT) / 2
    add(name=f"Z_motor_{nm}", **box(MOT_OUT - MOT_IN, 12, 10, [xc, 0, WHZ]), group="B", mass=12, color="motor",
        label="motor N20 + magnetický enkodér (12×10, telo 34 bez hriadeľa)",
        adds=[cyl(1.5, WHX - WHW / 2 - MOT_OUT + 0.4, [s * (MOT_OUT + (WHX - WHW / 2 - MOT_OUT) / 2), 0, WHZ], "x"),
              box(4.5, 6, 8, [s * (MOT_IN - 2.25), 9, 15])])                     # encoder cable exit (bent to +y)
    allow(f"Z_koleso_{nm}", f"Z_motor_{nm}")
    add(name=f"Z_drziak_motora_{nm}", **box(26, 13.0, 3.0, [s * 34.0, 0, FLOOR + 1.5]), group="B", mat="petg",
        color="grey", label="kolíska motora N20 (PETG) + strmeň",
        adds=[box(4, 13.0, 9.5, [s * 23, 0, FLOOR + 4.75]), box(4, 13.0, 9.5, [s * 45, 0, FLOOR + 4.75])],
        cuts=[box(MOT_OUT - MOT_IN + 0.4, 12.4, 10.4, [xc, 0, WHZ])])

for i, (x, y) in enumerate(CAST):
    add(name=f"Z_koliesko_{i + 1}", **cyl(6.5, 6.0, [x, y, 8.0]), group="B", mass=4, color="black",
        label="guľové koliesko Pololu 3/8\" (guľa Ø9.5, 0.5 mm nad podlahou)",
        adds=[dict(kind="sphere", r=4.75, at=[x, y, 5.25])])
    allow(f"Z_koliesko_{i + 1}", "Z_shell")

for s, nm in ((-1, "A"), (1, "B")):
    yc = s * (PACK_Y0 + PACK_D / 2)
    yi, yo = s * (PACK_Y0 + PACK_D / 4), s * (PACK_Y0 + 3 * PACK_D / 4)       # inner / outer cell axis
    add(name=f"Z_baterie_{nm}", **cyl(PACK_H / 2, PACK_L, [0, yi, PACK_Z0 + PACK_H / 2], "x"), group="B",
        mass=98, color="battery", adds=[cyl(PACK_H / 2, PACK_L, [0, yo, PACK_Z0 + PACK_H / 2], "x"),
                                        box(PACK_L, PACK_D / 2, PACK_H * 0.7, [0, yc, PACK_Z0 + PACK_H / 2])],
        label=f"blok batérie {'A (predný)' if s < 0 else 'B (zadný)'} 1S2P – 2× 18650 bodovo zvarené (2×47 g + 4 g)")
    add(name=f"Z_vodice_bat_{nm}", **box(3.5, 24, 14, [-35.3, s * 31, PACK_Z0 + 8]), group="B", mass=3,
        color="cable", label="vývody bloku (hlavný + balans) – ohyb 5 mm")

# J1 servo + cradle
sx0 = -S_SH
add(name="Z_J1_servo", **box(S_L, S_W, S_H, [sx0 + S_L / 2, 0, S_Z0 + S_H / 2]), r=2.0, group="B", mass=55,
    color="servo_bus", label="servo J1 Feetech STS3215 7.4 V (stojí, hriadeľ HORE v osi J1, priamy pohon)",
    adds=[cyl(4.5, 3.0, [0, 0, S_Z1 + 1.5]),                          # output boss + 25T spline
          cyl(4.0, 1.5, [0, 0, S_Z0 - 0.75]),                          # passive rear hub
          box(12, 16, 10, [sx0 + S_L + 6, 0, S_Z0 + 7])])               # 2x 5264 plugs + 5 mm bend (end face, low)
add(name="Z_J1_koliska", **box(46.4, 24.0, 1.6, [sx0 + S_L / 2, 0, S_Z0 - 0.8]), group="B", mat="petg",
    color="grey", label="kolíska serva J1 – most nad ľavým motorom (PETG)",
    adds=[box(20, 22, S_Z0 - 1.6 - FLOOR, [0, 0, FLOOR + (S_Z0 - 1.6 - FLOOR) / 2]),
          box(6, 5.0, S_Z0 - 1.6 - FLOOR, [31.0, 9.4, FLOOR + (S_Z0 - 1.6 - FLOOR) / 2]),
          box(6, 5.0, S_Z0 - 1.6 - FLOOR, [31.0, -9.4, FLOOR + (S_Z0 - 1.6 - FLOOR) / 2])],
    cuts=[cyl(4.3, 4, [0, 0, S_Z0 - 1])])
allow("Z_J1_koliska", "Z_J1_servo")

# base deck (electronics shelf) on posts, cut around servo / wheels
add(name="Z_paluba", kind="sblock", a=70.0, b=50.0, n=2.4, h=DECK_Z1 - DECK_Z0, at=[0, 0, (DECK_Z0 + DECK_Z1) / 2],
    group="B", mat="petg", color="grey", label="paluba elektroniky v podstavci (PETG, na stĺpikoch)",
    cuts=[box(48.6, 27.0, 4, [sx0 + S_L / 2, 0, 30]), box(15, 18, 4, [sx0 + S_L + 7, 0, 30]),
          box(18, 36, 4, [WHX, 0, 30]), box(18, 36, 4, [-WHX, 0, 30]),
          cyl(4.0, 4, [-35.3, 31, 30]), cyl(4.0, 4, [-35.3, -31, 30])])

# plinth (static, dark) + J1 bearing + J1 rolling loop
add(name="Z_sokel", **tube(PL_R, PL_RI, PL_TOP0 - PL_Z0, [0, 0, (PL_Z0 + PL_TOP0) / 2]), group="B", mat="petg",
    color="black", label="tmavý sokel J1 (pevný) – obopína vrch serva, nesie ložisko 6806",
    adds=[tube(42.0, PL_R, 2.0, [0, 0, 37.0]),                                  # flange under the base top
          tube(PL_R, 23.5, PL_TOP1 - PL_TOP0, [0, 0, (PL_TOP0 + PL_TOP1) / 2]),    # top plate
          tube(23.5, 21.0, BRG_Z1 - PL_TOP0, [0, 0, (PL_TOP0 + BRG_Z1) / 2])])     # bearing seat
allow("Z_sokel", "Z_shell")
add(name="Z_J1_lozisko", **tube(21.0, 17.4, BRG_Z1 - BRG_Z0, [0, 0, (BRG_Z0 + BRG_Z1) / 2]), group="B", mass=14,
    color="metal", label="ložisko J1 6806-2RS 30×42×7 – vonkajší krúžok + guľky (pevné, v sokli)")
allow("Z_J1_lozisko", "Z_sokel")
add(name="T_J1_lozisko_vnutro", **tube(17.3, 15.0, BRG_Z1 - BRG_Z0, [0, 0, (BRG_Z0 + BRG_Z1) / 2]), group="T", mass=8,
    color="metal", label="ložisko J1 6806-2RS – vnútorný krúžok (na náboji trupu)")
allow("T_J1_lozisko_vnutro", "Z_J1_lozisko"); allow("T_J1_lozisko_vnutro", "T_J1_naboj"); allow("T_J1_lozisko_vnutro", "T_paluba")
add(name="Z_J1_slucka", **tube(36.0, 24.0, 5.0, [0, 0, 62.2]), group="B", mass=3, color="cable",
    label="valivá slučka J1: 2-vrstvový FPC 5 mm na hrane (VBAT, GND, zbernica, GND), 140 mm, ohyb R6.3, ±150°")
allow("Z_J1_slucka", "Z_sokel")

# base electronics
add(name="Z_doska_zakladne", **box(36, 22, 5, [-31.0, 0, 24.0]), group="B", mass=7, color="pcb",
    label="doska uzla podstavca (STM32G030 + DRV8833 + 5 V/2 A TPS563201 + 3.3 V, JST-GH)")
add(name="Z_BMS", **box(16, 30, 3.5, [-46, 24, DECK_Z1 + 1.75]), group="B", mass=4, color="pcb",
    label="2S BMS 5 A s balansovaním")
add(name="Z_nabijacka", **box(23, 17, 3.5, [14, 42.5, DECK_Z1 + 1.75]), group="B", mass=5, color="pcb",
    label="nabíjačka IP2326 (USB-C 5 V → 2S, 1.5 A) + LED nabíjania",
    adds=[box(9.0, 3.2, 3.2, [14, 52.6, DECK_Z1 + 1.9])])
add(name="Z_vypinac", **box(9, 6, 4, [-22, 50.5, DECK_Z1 + 2]), group="B", mass=1, color="black",
    label="posuvný vypínač (spína hradlo P-MOSFET AO4407A)", adds=[box(2, 4, 2, [-22, 54.5, DECK_Z1 + 2.5])])
add(name="Z_ToF", **box(18, 2.5, 13, [0, -54.45, 19.5]), group="B", mass=1, color="pcb",
    label="ToF VL53L1X (doska 13×18) za tmavým okienkom")
add(name="Z_okno_ToF", **box(18, 1.6, 13, [0, -BB + 1.6, 19.5]), group="B", mass=0.5, color="glass",
    label="tmavé (dymové) okienko ToF, PMMA 1.5")
allow("Z_okno_ToF", "Z_shell")
add(name="Z_svetlo_predne", **box(40, 1.6, 3.5, [0, -53.6, 29.75]), group="B", mass=1.5, color="glow",
    label="predná svetelná lišta – 6× WS2812B-2020 na flexe + svetlovod PMMA",
    adds=[box(38, 3.2, 3.0, [0, -55.9, 29.75])])
allow("Z_svetlo_predne", "Z_shell")
for i, (x, y) in enumerate([(44, 41), (-44, 41), (44, -41), (-44, -41)]):
    add(name=f"Z_IR_{i + 1}", **box(8, 6, 3.5, [x, y, 13.0]), group="B", mass=0.5, color="pcb",
        label="snímač pádu ITR8307 na mini DPS (pozerá dolu cez otvor Ø5)")

# =================================================================== TORSO (group T, turns with J1)
TOPD = 1.5                         # shell top 1.5 below Z_TT; raised collar plateau ring r 28.35..29.8 up to Z_TT
th = Z_TT - TOPD - TZ0
add(name="T_shell", kind="sshell", a=TA, b=TB, n=TN, h=th, rf=TRF, wall=TW, at=[0, 0, (TZ0 + Z_TT - TOPD) / 2],
    adds=[tube(29.8, 27.0, TOPD + 0.2, [0, 0, Z_TT - TOPD / 2 - 0.1])],
    group="T", mat="resin", color="white",
    label="trup – mäkká škrupina 92×84×90 (zástupný tvar n 2.35, R16), plošina goliera r29.8, otvorené dno nad soklom",
    cuts=[cyl(28.35, 10, [0, 0, Z_TT]),                                       # collar recess
          cyl(38.8, TDECK_Z0 - 40.0, [0, 0, (40.0 + TDECK_Z0) / 2], rot=[0, 0, 7]),   # open bottom (seam rotated: OCC)
          cyl(4.0, 6, [44.5, SH[0], SH[1]], "x"), cyl(4.0, 6, [-44.5, SH[0], SH[1]], "x"),   # spline holes
          box(34, 8, 3.2, [0, -TB + 1, 100.5]),                               # chest light bar slot
          box(28, 8, 2.6, [0, -TB + 1, 91.0])])                               # speaker grille slot (grey slot)
allow("T_shell", "B_golier_prstenec")

add(name="T_paluba", kind="sblock", a=TA - TW - 0.6, b=TB - TW - 0.6, n=TN, h=TDECK_Z1 - TDECK_Z0,
    at=[0, 0, (TDECK_Z0 + TDECK_Z1) / 2], group="T", mat="petg", color="grey",
    label="paluba trupu (PETG) – nosná doska nad soklom",
    cuts=[cyl(2.6, 4, [0, 0, 65.85]), tube(24.5, 16.3, 1.6, [0, 0, TDECK_Z0])])   # relief over the static 6806 outer ring + seat
allow("T_paluba", "T_shell")
add(name="T_J1_naboj", **tube(15.0, 10.5, TDECK_Z0 - 58.1, [0, 0, (58.1 + TDECK_Z0) / 2]), group="T", mat="petg",
    color="grey", label="náboj J1 v ložisku 6806 – 2 kolíky do ramienka (len krútiaci moment, bez axiálnej sily na servo)")
allow("T_J1_naboj", "T_paluba"); allow("T_J1_naboj", "Z_J1_lozisko")
add(name="T_J1_ramienko", **cyl(10.0, 3.0, [0, 0, 61.5]), group="T", mass=3, color="metal",
    label="hliníkové ramienko STS3215 Ø20 (25T)")
allow("T_J1_ramienko", "Z_J1_servo")
add(name="T_J1_sukna", **tube(37.6, 36.5, TDECK_Z0 - 59.6, [0, 0, (59.6 + TDECK_Z0) / 2]), group="T", mat="petg",
    color="grey", label="otočná stena kanála slučky J1 (vonkajšia dráha pásu)")
allow("T_J1_sukna", "T_paluba"); allow("T_J1_sukna", "Z_J1_slucka")
add(name="T_puzdro_pan", **tube(2.6, 2.0, TDECK_Z1 - TDECK_Z0, [0, 0, (TDECK_Z0 + TDECK_Z1) / 2]), group="T",
    mass=0.3, color="metal", label="bronzové puzdro čapu pan Ø4 (radiálne vedenie dole)")
allow("T_puzdro_pan", "T_paluba")

# --- PAN drive: STS3032 inverted at +X, pinion 18T -> idler 20T -> pan gear 36T (m0.8, ratio 2:1)
R_PG, R_ID, R_PI = 14.4, 8.0, 7.2
PS = (34.1, 5.0)                                        # pan servo shaft (pinion) centre
rs = math.hypot(*PS)
ca = (22.4 ** 2 + rs ** 2 - 15.2 ** 2) / (2 * 22.4 * rs)
ang = math.atan2(PS[1], PS[0]) + math.acos(ca)
ID = (22.4 * math.cos(ang), 22.4 * math.sin(ang))       # idler centre (behind, +Y side)
gz, gh = zr(GEAR_Z0, GEAR_Z1)
add(name="T_pastorok_pan", **cyl(R_PI + 0.8, gh, [PS[0], PS[1], gz]), group="T", mat="pom", color="black",
    label="pastorok pan m0.8 18z (POM) na drážkovaní STS3032")
add(name="T_medzikoleso_pan", **cyl(R_ID + 0.8, gh, [ID[0], ID[1], gz]), group="T", mat="pom", color="black",
    label="medzikoleso pan m0.8 20z na čape Ø3 v palube", adds=[cyl(1.5, 3.9, [ID[0], ID[1], 68.05])])          # pin z 66.1..70.0 (above the deck relief)
allow("T_medzikoleso_pan", "T_paluba"); allow("T_medzikoleso_pan", "T_pastorok_pan")
case_z0 = GEAR_Z0 + 5.8                               # inverted: spline face 5.8 above the pinion bottom
add(name="T_servo_pan", **box(12.1, 23.2, 22.7, [PS[0], PS[1] - 17.2 + 11.6, case_z0 + 11.35]), group="T", mass=20,
    color="servo_bus", label="servo pan Feetech STS3032 (360° magnetický snímač, zbernica) – obrátené, hriadeľ dole",
    adds=[box(12.1, 32.0, 2.5, [PS[0], PS[1] - 17.2 + 11.6, case_z0 + 22.7 - 17.25]),        # tabs
          cyl(6.0, 2.8, [PS[0], PS[1], case_z0 - 1.4]),                                     # boss
          cyl(2.4, 3.0, [PS[0], PS[1], case_z0 - 4.3]),                                     # spline
          box(10, 9, 6, [PS[0], PS[1] - 6.0, case_z0 + 22.7 + 3.0])])                        # 2 plugs + bend on top
allow("T_servo_pan", "T_pastorok_pan")
add(name="T_drziak_serva_pan", **box(2.4, 26, 22, [PS[0] + 7.25, PS[1] - 0.6, 86.0]), group="T", mat="petg",
    color="grey", label="držiak serva pan (PETG, skrutky do úchytov)")
allow("T_drziak_serva_pan", "T_servo_pan"); allow("T_drziak_serva_pan", "T_paluba"); allow("T_drziak_serva_pan", "T_shell")

# pan cable rolling loop (static part of the envelope) at -X
add(name="T_slucka_pan", **box(11, 42, 9, [-33.0, 0, 77.0]), group="T", mass=3, color="cable",
    label="slučka kábla PAN (10 vodičov: hlava 4, náklon 3, zdvih 3) ±85°, 160 mm, v žľabe na -X strane")
add(name="T_zlab_pan", **box(1.6, 44, 11, [-39.3, 0, 77.0]), group="T", mat="petg", color="grey",
    label="žľab slučky pan (PETG)")
allow("T_zlab_pan", "T_slucka_pan"); allow("T_zlab_pan", "T_shell"); allow("T_slucka_pan", "T_shell")

# speaker + chest light bar
add(name="T_reproduktor", **cyl(14.5, 9.0, [0, -33.7, 82.0], "y"), group="T", mass=8, color="black",
    label="reproduktor Ø28 8 Ω 1–2 W (plochý 5.5) + uzavretá komôrka, za sivou štrbinou")
add(name="T_svetlo_hrud", **box(34, 1.6, 4.0, [0, -36.6, 100.5]), group="T", mass=1.5, color="glow",
    label="hrudná svetelná lišta 6× WS2812B-2020 + svetlovod", adds=[box(32, 3.0, 3.0, [0, -39.2, 100.5])])
allow("T_svetlo_hrud", "T_shell")

# torso controller board (back)
add(name="T_doska", **box(40, 1.6, 34, [0, 30.3, 87.0]), group="T", mass=4, color="pcb",
    label="nosná DPS trupu 40×30 (riadenie, zbernica, konektory serv)")
add(name="T_ESP32S3", **box(18, 4.5, 25, [-10.0, 33.35, 90.5]), group="T", mass=3, color="elec",
    label="ESP32-S3-Zero 25×18 (UART hlava, zbernica, PWM, I2S)")
add(name="T_menic5V", **box(17.8, 6.0, 17.8, [10.0, 34.1, 93.9]), group="T", mass=2.5, color="elec",
    label="menič 5 V Pololu D36V28F5 (3.2 A) – servá, hlava, LED, zosilňovač")
add(name="T_zosilnovac", **box(3.0, 19, 17.8, [-31.5, -12.0, 91.0]), group="T", mass=2, color="elec",
    label="I2S zosilňovač MAX98357A 17.8×19")
add(name="T_kondenzator", **cyl(4.0, 6.2, [12.0, 34.2, 76.0], "y"), group="T", mass=1.5, color="metal",
    label="470 µF / 10 V pri konektoroch serv")
add(name="T_konektory", **box(34, 6.5, 9, [0, 33.0, 108.5]), group="T", mass=3, color="black",
    label="konektory serv / hlavy (JST-PH) + 5 mm na ohyb")
for nm in ("T_ESP32S3", "T_menic5V", "T_kondenzator", "T_konektory"):
    allow(nm, "T_doska")

# shoulder bosses + arm cable loops (torso side)
for s, nm in ((-1, "R"), (1, "L")):
    add(name=f"T_rameno_{nm}_puzdro", **cyl(7.0, 6.2, [s * 40.9, SH[0], SH[1]], "x"), group="T", mat="petg",
        color="black", label="náboj ramena v trupe – drží ramienko nano serva (trecia poistka)")
    allow(f"T_rameno_{nm}_puzdro", "T_shell")
    add(name=f"T_kabel_ramena_{nm}", **box(5, 20, 12, [s * 33.5, 0, SH[1]]), group="T", mass=1,
        color="cable", label="servisná slučka kábla ramena (3 vodiče AWG30)")

# =================================================================== PAN STAGE (group P)
add(name="P_koleso_pan", **cyl(R_PG + 0.8, gh, [0, 0, gz]), group="P", mat="pom", color="black",
    label="ozubené koleso pan m0.8 36z (POM) + PTFE podložka",
    adds=[cyl(2.0, TDECK_Z1 - TDECK_Z0 + 0.3, [0, 0, (TDECK_Z0 + GEAR_Z0) / 2])])          # pivot pin D4
allow("P_koleso_pan", "T_medzikoleso_pan"); allow("P_koleso_pan", "T_puzdro_pan"); allow("P_koleso_pan", "T_paluba")
cz, ch = zr(CUP_Z0, CUP_Z1)
add(name="P_dno", **cyl(22.0, ch, [0, 0, cz]), group="P", mat="petg", color="grey",
    label="dno otočného kalicha pan (PETG) s výrezom pod kľukou a jazykom",
    cuts=[box(8.0, 25.0, 3.0, [-20.5, 0, cz])])
allow("P_dno", "P_koleso_pan")
post_h = WELL_Z0 - CUP_Z1
posts = [(19.5, 12.9), (19.5, -12.9), (-12.0, 19.5), (-12.0, -19.5)]
add(name="P_ram", **cyl(1.5, post_h, [posts[0][0], posts[0][1], CUP_Z1 + post_h / 2]), group="P", mat="petg",
    color="grey", label="stĺpiky rámu zdvihu (spájajú dno s šachtou)",
    adds=[cyl(1.5, post_h, [x, y, CUP_Z1 + post_h / 2]) for x, y in posts[1:]])
allow("P_ram", "P_dno")
# well 47x22 inside, walls 1.6, with tongue relief at -X end
add(name="P_sachta", **box(50.2, 25.2, WELL_Z1 - WELL_Z0, [0, 0, (WELL_Z0 + WELL_Z1) / 2]), r=3.0, group="P",
    mat="resin", color="black", label="šachta krku 47×22 (vedenie zdvihu, otáča sa s pan)",
    cuts=[box(47.0, 22.0, WELL_Z1 - WELL_Z0 + 1, [0, 0, (WELL_Z0 + WELL_Z1) / 2], r=1.5),
          box(5.0, 24.6, 10.5, [-21.0, 0, WELL_Z0 + 4.75])],
    adds=[box(5.0, 27.2, 10.0, [-21.0, 0, WELL_Z0 + 5.0])])      # local wall thickening around the tongue relief
allow("P_sachta", "B_golier_kotuc"); allow("P_sachta", "P_ram")
# lift servo MG90S: shaft along -X, at y 0, z ZC_LIFT; case x -12.2..10.5, y -16.8..6, z +-6.1
add(name="P_servo_zdvih", **box(22.7, 22.8, 12.2, [-0.85, -5.4, ZC_LIFT]), group="P", mass=13.4, color="servo",
    label="servo zdvihu MG90S (hriadeľ v osi X) – kľuka r10, mŕtve body v oboch krajných polohách",
    adds=[box(2.5, 32.5, 12.2, [-6.75, -5.4, ZC_LIFT]),                     # tabs
          cyl(6.0, 4.0, [-14.2, 0, ZC_LIFT], "x"),                         # boss
          cyl(2.4, 1.2, [-16.8, 0, ZC_LIFT], "x"),                         # spline
          box(7.5, 4.5, 3.0, [6.75, 8.25, ZC_LIFT - 2.0])])                # cable boot at the shaft-end face
allow("P_servo_zdvih", "P_ram")
add(name="P_klika", **box(1.8, 5.0, 15.5, [-18.1, 0, ZC_LIFT - 4.25]), group="P", mass=1.5, color="metal",
    label="kľuka zdvihu r10 (oceľ) v polohe pokoj (dole) + čap Ø2",
    adds=[cyl(3.5, 1.8, [-18.1, 0, ZC_LIFT], "x"), cyl(1.0, 3.5, [-20.75, 0, ZC_LIFT - 10.0], "x")])
allow("P_klika", "P_servo_zdvih")
add(name="P_kabel_zdvih", **box(6, 12, 7.6, [14.0, -3.0, CUP_Z1 + 0.5 + 3.8]), group="P", mass=1.5, color="cable",
    label="U-slučka vodičov krku pre zdvih 20 mm (4+3 vodiče) + kábel serva zdvihu",
    adds=[box(6, 13.0, 3.0, [14.0, 9.5, CUP_Z1 + 2.0]), box(33, 3.0, 3.0, [0.5, 14.5, CUP_Z1 + 2.0])])
allow("P_kabel_zdvih", "P_dno")

# =================================================================== LIFT (group L)
tz_top = Z_TT - 40.5
tz_bot = ZC_LIFT - 11.9
add(name="L_jazyk", **box(2.9, 18.0, tz_top - tz_bot, [-21.05, 0, (tz_top + tz_bot) / 2]), group="L", mat="petg",
    color="black", label="jazyk pod krkom (nový diel, 2× M2 do vložiek v spodku krku) s drážkou 20.2×2.2",
    adds=[box(2.9, 22.6, 6.0, [-21.05, 0, tz_bot + 3.0])],
    cuts=[box(4.0, 20.2, 2.2, [-21.05, 0, ZC_LIFT - 10.0])])
allow("L_jazyk", "B_krk"); allow("L_jazyk", "P_klika")

# =================================================================== ARMS (AR right -X, AL left +X)
ARM_X0, ARM_T, ARM_W, ARM_UP, ARM_DN = 47.5, 21.0, 30.0, 14.0, 66.0
for s, nm, g in ((-1, "R", "AR"), (1, "L", "AL")):
    xc = s * (ARM_X0 + ARM_T / 2)
    zc = SH[1] + (ARM_UP - ARM_DN) / 2
    add(name=f"A_{nm}_skrupina", kind="sshell", a=ARM_T / 2, b=ARM_W / 2, n=2.5, h=ARM_UP + ARM_DN, rf=10.0,
        wall=1.8, at=[xc, SH[0], zc], group=g, mat="resin", color="white",
        label=f"rameno {'pravé' if s < 0 else 'ľavé'} – mäkká lopatka 30×21×82 (zástupný tvar)",
        cuts=[cyl(3.6, 4, [s * (ARM_X0 + 0.9), SH[0], SH[1]], "x")])
    add(name=f"A_{nm}_servo", **box(15.5, 7.6, 18.6, [s * (ARM_X0 + 2.0 + 7.75), SH[0], SH[1] + 4.5 - 9.3]), group=g,
        mass=4.5, color="servo", label="nano servo ramena (Hitec HS-35HD trieda, 18.6×7.6×15.5, 0.8 kg·cm)",
        adds=[box(1.2, 7.6, 25.0, [s * (ARM_X0 + 2.0 + 4.0), SH[0], SH[1] + 4.5 - 9.3]),          # tabs
              cyl(3.0, 2.0, [s * (ARM_X0 + 1.0), SH[0], SH[1]], "x"),                              # boss
              cyl(2.0, 5.0, [s * (ARM_X0 - 2.5), SH[0], SH[1]], "x"),                              # spline + horn hub
              box(5.0, 3.0, 4.0, [s * (ARM_X0 + 12.5), SH[0], SH[1] + 6.5])])                      # cable boot
    allow(f"A_{nm}_servo", f"A_{nm}_skrupina"); allow(f"A_{nm}_servo", f"T_rameno_{nm}_puzdro")
    allow(f"A_{nm}_servo", "T_shell")
    add(name=f"A_{nm}_kabel", **box(6, 3.0, 4.0, [s * (ARM_X0 + 6.0), SH[0] + 4.5, SH[1] + 7.0]), group=g, mass=0.5,
        color="cable", label="kábel serva ramena → oblúková štrbina pod krytkou ramena")
    add(name=f"A_{nm}_krytka", **cyl(12.0, 1.2, [s * (ARM_X0 + 0.4), SH[0], SH[1]], "x"), group=g, mat="resin",
        color="black", label="čierna krytka ramena Ø24")
    allow(f"A_{nm}_krytka", f"A_{nm}_skrupina"); allow(f"A_{nm}_krytka", f"A_{nm}_servo")
    allow(f"A_{nm}_kabel", f"A_{nm}_servo")

contacts = [[WHX, 0], [-WHX, 0]] + [[x, y] for x, y in CAST]
layout = {"name": "K3 – J1 v podstavci (STS3215 stojí v osi nad ľavým motorom, sokel)", "Z_TT": Z_TT, "SH": SH,
          "contacts": contacts, "comps": C, "allow": ALLOW,
          "meta": {"ZC_LIFT": ZC_LIFT, "pan_servo_shaft": PS, "idler": [round(ID[0], 2), round(ID[1], 2)],
                   "notes": "casters 0.5 mm above the wheel contact plane (robot rocks on the wheel axle)"}}
json.dump(layout, open(os.path.join(HERE, "layout.json"), "w"), indent=1, ensure_ascii=False)
print("written", len(C), "comps; Z_TT", Z_TT, "SH", SH, "idler", ID)
