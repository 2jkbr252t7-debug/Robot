"""T1 PACK – final internal packaging = K2 'off-axis gears, compact' + judge grafts/must-fixes (see pack.md).
layout generator for t1lib.  Writes layout.json next to this file.
World mm, Z up, floor z=0, FRONT=-Y, robot RIGHT=-X.  Run: /opt/venv/cad/bin/python gen_layout.py"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
Z_TT = 133.0                     # torso top = collar disc top (head top 215)
SH = [2.0, 112.0]                # shoulder axis (y, z)
TZ0, TZ1 = 43.0, Z_TT - 1.0      # torso body z range (89) + 1 mm raised collar plateau r 30 to Z_TT
BZ0, BZ1 = 6.0, 40.0             # base shell z range (34 tall, ground clearance 6)
TA, TB = 44.5, 40.0              # torso half width / half depth (89 x 80)
BA, BB = 71.0, 55.0              # base half width / half depth (142 x 110)

C = []
ALLOW = []


def add(**k):
    C.append(k)
    return k


def box(sx, sy, sz, at, **k):
    return dict(kind="box", size=[sx, sy, sz], at=list(at), **k)


def cyl(r, h, at, axis="z", **k):
    return dict(kind="cyl", r=r, h=h, axis=axis, at=list(at), **k)


def tube(r, ri, h, at, axis="z", **k):
    return dict(kind="tube", r=r, ri=ri, h=h, axis=axis, at=list(at), **k)


def zc(z0, z1):
    return (z0 + z1) / 2.0, z1 - z0


# =============================================================== TORSO  (group T, turns with J1)
add(name="T_shell", kind="sshell", a=TA, b=TB, n=2.35, h=TZ1 - TZ0, rf=16.0, wall=2.2, at=[0, 0, (TZ0 + TZ1) / 2],
    group="T", mat="resin", color="white", label="trup – mäkká škrupina (zástupný tvar n 2.35, R16) + plošina goliera r30",
    adds=[tube(30.0, 28.4, 3.5, [0, 0, 129.75]), cyl(29.8, 2.0, [0, 0, Z_TT - 1.0])],                     # thickened collar seat under the top wall
    cuts=[cyl(28.35, 8, [0, 0, 132.5]),                                # collar recess / well opening
          cyl(13.5, 9.0, [42.0, SH[0], SH[1]], "x"), cyl(13.5, 9.0, [-42.0, SH[0], SH[1]], "x"),   # shoulder pockets
          cyl(7.0, 6, [-18, 0, 44.0]),                                  # J1 servo spline through the floor
          box(36, 8, 4.5, [0, -39, 101.5]),                             # light bar slot
          box(30, 8, 3.0, [0, -39, 83.5])])                             # speaker grille slot (grey slot of R01)
ALLOW.append(["T_shell", "B_golier_prstenec"])

# --- J1 drive: STS3215 shaft DOWN, off-axis by C=18, 1:1 spur pair m1.0 18T/18T, sun gear fixed on the base hub
add(name="T_STS3215", **box(45.2, 24.7, 35.0, [-6.9, 0, 63.0]), group="T", mass=55, color="servo_bus",
    label="servo J1 Feetech STS3215 (hriadeľ dole, mimo osi o 18)",
    adds=[cyl(6.0, 2.6, [-18, 0, 44.2]),                                # spline boss through the floor
          box(11.3, 16, 18, [21.35, 0, 71.0])])                         # 2x 5264 plugs + 5 mm bend space
add(name="T_J1_pastorok", **cyl(10.0, 3.2, [-18, 0, 40.4]), group="T", mat="brass", color="metal",
    label="pastorok J1 m1 18z (mosadz, na drážkovaní 25T)", adds=[cyl(5.0, 0.9, [-18, 0, 42.45])])
ALLOW += [["T_J1_pastorok", "T_STS3215"], ["T_J1_pastorok", "Z_J1_koleso"]]
add(name="T_J1_noha", **tube(20.5, 18.5, 12.2, [0, 0, 36.9]), group="T", mat="petg", color="black",
    label="otočná pätka trupu (drží vonk. krúžok ložiska)", cuts=[cyl(10.8, 6.0, [-18, 0, 40.5])])
add(name="T_J1_lozisko", **tube(18.5, 12.5, 7.0, [0, 0, 34.3]), group="T", mass=22, color="metal",
    label="ložisko J1 6805-2RS 25×37×7")
ALLOW += [["T_J1_lozisko", "Z_J1_hub"], ["T_J1_lozisko", "T_J1_noha"]]
add(name="T_J1_sukna", **tube(34.0, 20.5, 1.4, [0, 0, 41.7]), group="T", mat="petg", color="black",
    label="tmavý sokel / prachová sukňa (otočná)", cuts=[cyl(10.8, 3, [-18, 0, 41.7])])
add(name="T_ram_J1", **box(46, 1.4, 34.0, [-7, 13.3, 64.0]), group="T", mat="petg", color="grey",
    label="kolíska serva J1 (PETG)", adds=[box(46, 1.4, 34.0, [-7, -13.3, 64.0])])

# --- deck + PAN drive: STS3032 (360 deg magnetic) at the front, 18T pinion -> 36T pan gear (2:1), m0.8
add(name="T_paluba", kind="sblock", a=37.0, b=30.5, n=2.35, h=1.8, at=[0, 0, 81.9], group="T", mat="petg",
    color="grey", label="paluba nad servom J1 (nesie pan)", cuts=[cyl(7.0, 3, [0, -21.6, 81.9]), cyl(3.0, 3, [0, 0, 81.9])])
add(name="T_cap", **cyl(3.0, 6.0, [0, 0, 84.0]), group="T", mat="steel", color="metal",
    label="čap pan Ø6 (oceľ, pevný v palube)")
add(name="T_ptfe", **tube(13.0, 5.2, 0.3, [0, 0, 82.95]), group="T", mass=0.1, color="metal",
    label="axiálna PTFE podložka pan")
ALLOW.append(["T_ptfe", "P_koleso_pan"])
add(name="T_pan_servo", **box(23.5, 12.5, 23.0, [5.85, -21.6, 66.0]), group="T", mass=21, color="servo_bus",
    label="servo pan Feetech STS3032 (360°, zbernica)",
    adds=[box(32.5, 12.5, 2.5, [5.85, -21.6, 71.95]),                  # tabs
          cyl(6.2, 3.5, [0, -21.6, 79.25]),                             # boss
          box(7, 8, 8, [21.1, -21.6, 60.0])])                           # plug + bend
add(name="T_pan_pastorok", **cyl(8.0, 3.2, [0, -21.6, 84.8]), group="T", mat="pom", color="black",
    label="pastorok pan m0.8 18z", adds=[cyl(4.0, 2.2, [0, -21.6, 82.1])])
ALLOW += [["T_pan_pastorok", "T_pan_servo"], ["T_pan_pastorok", "P_koleso_pan"]]
add(name="T_kanal_pan", **tube(28.0, 26.6, 3.7, [0, 0, 84.65]), group="T", mat="petg", color="grey",
    label="žľab valivej slučky pan (zadná polovica)", cuts=[box(60, 30, 6, [0, -17, 84.85])])
add(name="T_kabel_pan", **tube(26.3, 15.6, 3.6, [0, 0, 84.7]), group="T", mass=3, color="cable",
    label="valivá slučka pan: plochý FPC 8 vodičov (2-vrstvový, 0,12 mm, 3,4 mm)", cuts=[box(60, 30, 6, [0, -15, 84.85])])

# --- frame: columns deck -> top ring, shoulder hubs
for sx, nm in ((1, "L"), (-1, "P")):
    add(name=f"T_stlpik_predny_{nm}", **box(4, 4, 35.7, [sx * 18, -27, 100.65]), group="T", mat="petg", color="grey",
        label="stĺpik rámu")
for sx, nm, side in ((1, "L", "ľavý"), (-1, "R", "pravý")):
    add(name=f"T_stlpik_{nm}", **box(4, 8, 35.7, [sx * 39, 2, 100.65]), group="T", mat="petg", color="grey",
        label=f"bočný stĺpik + čap ramena ({side})", adds=[cyl(7.0, 4.0, [sx * 39.5, SH[0], SH[1]], "x")])
    add(name=f"T_paka_{nm}", **cyl(7.0, 1.5, [sx * 42.25, SH[0], SH[1]], "x"), group="T", mat="pom", color="black",
        label="drážkové puzdro serva ramena s trecou spojkou ≈0,25 N·m (pevné v trupe)")
    add(name=f"T_kabel_ramena_{nm}", **tube(12.5, 7.5, 2.0, [sx * 42.2, SH[0], SH[1]], "x"), group="T", mass=0.5,
        color="cable", label="špirála 3 vodičov serva ramena")
    ALLOW.append([f"A_{nm}_servo", f"T_paka_{nm}"])
add(name="T_horny_kruh", **tube(31.5, 28.6, 7.0, [0, 0, 122.0]), group="T", mat="petg", color="grey",
    label="horný krúžok – klzné ložisko čapu pan (POM vložka)")
ALLOW.append(["T_horny_kruh", "P_sachta"])

# --- electronics / audio / light
add(name="T_riadenie", **box(48, 7, 22, [0, 26.5, 64.0]), group="T", mass=8, color="pcb",
    label="riadiaca DPS trupu: ESP32-S3-Zero + budič zbernice + JST-GH")
add(name="T_menic", **box(5, 17.8, 17.8, [-35, 0, 66.0]), group="T", mass=3, color="pcb",
    label="menič 5 V / ≈3 A Pololu D36V28F5")
add(name="T_zosilnovac", **box(19.3, 3, 17.8, [-19, -25.5, 61.0]), group="T", mass=1.5, color="pcb",
    label="zosilňovač I2S MAX98357A")
add(name="T_kondenzator", **cyl(5.0, 13.0, [32, 10, 62.0]), group="T", mass=2, color="elec",
    label="470 µF / 10 V na koľajnici serv")
add(name="T_reproduktor", **cyl(14.0, 5.0, [0, -34.1, 83.5], "y"), group="T", mass=6, color="grey",
    label="reproduktor Ø28 8 Ω 1.5 W za sivou štrbinou")
add(name="T_svetlo", **box(36, 4.5, 5, [0, -35.6, 101.5]), group="T", mass=2, color="glow",
    label="svetelná lišta hrude: WS2812B-2020 + PMMA svetlovod")
ALLOW.append(["T_svetlo", "T_shell"])

# =============================================================== PAN STAGE (group P)
add(name="P_sachta", **box(50.2, 25.2, 39.5, [0, 0, 107.25]), group="P", mat="resin", color="black",
    label="šachta krku 47×22 + čap Ø56.4 (otočná)",
    adds=[tube(28.2, 24.0, 6.0, [0, 0, 121.5])],                       # journal z 118.5..124.5
    cuts=[dict(kind="box", size=[47, 22, 40], r=1.5, at=[0, 0, 108.5]),  # inner well z 88.5..128.5
          tube(40, 26.5, 1.6, [0, 0, 126.8]),                           # clip corners under the collar disc
          box(4.5, 3.5, 30, [-16.75, 11.75, 103.5]),                    # back-wall window for the ear
          box(4.0, 8, 26, [24.0, 0, 101.0]),                            # end-wall window for the neck wires
          box(3.5, 8, 3, [13.9, -3.0, 88.0])])                          # floor hole under the neck wire exit
add(name="P_koleso_pan", **cyl(15.2, 3.5, [0, 0, 84.95]), group="P", mat="pom", color="black",
    label="koleso pan m0.8 36z (POM)", adds=[cyl(10.0, 0.8, [0, 0, 87.1])],
    cuts=[cyl(3.1, 6, [0, 0, 85.0])])
zc_l = 104.8                                                            # lift crank centre
add(name="P_servo_zdvih", **box(22.8, 12.2, 22.8, [3.6, 19.1, zc_l - 5.5]), group="P", mass=13.4, color="servo",
    label="servo zdvihu MG90S (spodné ucho odrezané)",
    adds=[cyl(6.1, 4.0, [-9.8, 19.1, zc_l], "x"), cyl(3.3, 1.7, [-12.65, 19.1, zc_l], "x"),
          cyl(3.2, 3.5, [-9.55, 19.1, zc_l - 9.0], "x"),
          box(2.5, 12.2, 4.85, [-2.25, 19.1, zc_l + 5.9 + 2.425]),       # remaining top tab
          box(5, 5, 5, [11.5, 19.1, zc_l + 5.9 + 2.5])])                # cable exit + bend
add(name="P_kluka", **cyl(13.0, 1.8, [-14.5, 19.1, zc_l], "x"), group="P", mat="pom", color="black",
    label="kľuka r10 + čap Ø2 (obálka pohybu)", cuts=[box(4, 20, 40, [-14.5, 6.1, zc_l])])
add(name="P_kabel_zdvih", **box(3.1, 8, 23.5, [26.85, 0, 101.25]), group="P", mass=1, color="cable",
    label="slučka FPC krku pre zdvih 20 mm (FPC 3,0 mm na hrane, ohyb R≈3,5 v rovine YZ)")  # PACK: 2.5 -> 3.1 wide (FPC on edge)

# =============================================================== LIFT (group L)
add(name="L_noha", **box(45, 20, 3, [0, 0, 91.0]), r=1.0, group="L", mat="pom", color="black",
    label="pätka krku 45×20 (POM) + ucho s drážkou pre čap kľuky",
    adds=[box(2.5, 21.0, 7.6, [-16.75, 20.5, 93.3])])
ALLOW += [["L_noha", "B_kabel_krk"], ["P_kluka", "L_noha"], ["P_koleso_pan", "B_kabel_krk"], ["P_sachta", "B_kabel_krk"],
          ["T_kabel_pan", "B_kabel_krk"]]

# =============================================================== ARMS (AR = right -X, AL = left +X)
for sx, g, nm in ((-1, "AR", "R"), (1, "AL", "L")):
    add(name=f"A_{nm}_ruka", **box(23, 30, 83, [sx * 58.0, SH[0], 86.5]), rf=11.4, group=g, mat="resin",
        color="white", label="rameno – mäkká lopatka (zástupný tvar)",
        cuts=[dict(kind="box", size=[19.0, 26.0, 79.0], rf=9.4, at=[sx * 58.0, SH[0], 86.5]),   # PACK: wall 2.0 (K2: 1.4)
              box(3, 12.4, 21.5, [sx * 47.5, SH[0], 107.0])])
    add(name=f"A_{nm}_servo", **box(21, 9.4, 20.5, [sx * 57.0, SH[0], 107.0]), group=g, mass=6, color="servo",   # PACK: 0.35 inward
        label="servo ramena EMAX ES9052MD (v lopatke, puzdro prilepené k vonkajšej stene)",
        adds=[cyl(5.5, 3.85, [sx * 44.575, SH[0], SH[1]], "x")])
    ALLOW.append([f"A_{nm}_servo", f"A_{nm}_ruka"])        # case bonded against the outer wall (0 gap by design)
    add(name=f"A_{nm}_kabel", **box(8, 6, 5, [sx * 60.0, SH[0], 94.2]), group=g, mass=0.5, color="cable",
        label="výstup kábla serva ramena")
    add(name=f"A_{nm}_kryt", **tube(12.5, 6.0, 2.3, [sx * 45.35, SH[0], SH[1]], "x"), group=g, mat="resin",
        color="black", label="čierna krytka ramena Ø25")

# =============================================================== BASE (group B, static)
add(name="Z_shell", kind="sshell", a=BA, b=BB, n=2.35, h=BZ1 - BZ0, rf=10.0, wall=2.2, at=[0, 0, (BZ0 + BZ1) / 2],
    group="B", mat="resin", color="white", label="podstavec – mäkká škrupina (zástupný tvar)",
    cuts=[cyl(29.0, 6, [0, 0, 39.0]),
          box(11, 34, 6, [54, 0, 6]), box(11, 34, 6, [-54, 0, 6]),
          cyl(7.0, 6, [0, 34, 6]), cyl(7.0, 6, [0, -34, 6]),
          box(20, 6, 12, [0, -53.5, 28.5]), box(44, 6, 4, [0, -53.5, 20.0]),
          box(10, 6, 4, [0, 53.5, 33.2]), box(8, 6, 8, [18, 52.5, 27.5])]
          + [box(9, 7, 6, [sx * 40, sy * 31, 6]) for sx in (-1, 1) for sy in (-1, 1)])   # PACK: cliff windows
add(name="Z_J1_hub", **cyl(12.5, 7.0, [0, 0, 34.3]), group="B", mat="petg", color="black",
    label="pevný náboj J1 (oceľové jadro M8)",
    adds=[cyl(6.0, 5.8, [0, 0, 27.9]), cyl(6.0, 1.0, [0, 0, 38.3]), box(60, 13, 6, [0, 0, 26.0])])                      # PACK: bridge = 13 x 6 beam (K2: 2 mm plate)
add(name="Z_J1_koleso", **cyl(10.0, 3.2, [0, 0, 40.4]), group="B", mat="brass", color="metal",
    label="pevné koleso J1 m1 18z (mosadz) na trecej spojke")
add(name="Z_J1_kanal", **tube(34.0, 32.5, 7.6, [0, 0, 34.0]), group="B", mat="petg", color="grey",
    label="žľab valivej slučky J1", adds=[tube(34.0, 21.5, 0.4, [0, 0, 30.4])])
add(name="Z_J1_kabel", **tube(32.3, 21.5, 6.6, [0, 0, 33.9]), group="B", mass=4, color="cable",
    label="valivá slučka J1: FPC 6 vodičov, dĺžka pre ±170°")
for sy, nm in ((-1, "P"), (1, "Z")):
    for k, yc in ((1, 16.45), (2, 35.35)):
        add(name=f"Z_clanok_{nm}{k}", **cyl(9.45, 66.5, [0, sy * yc, 20.25], "x"), group="B", mass=49,
            color="battery", label="článok 18650 (2S2P, 47 g + pásky)")
add(name="Z_BMS", **box(30, 10, 3.5, [0, -40.5, 32.5]), group="B", mass=4, color="pcb", label="2S BMS s vyvažovaním")
add(name="Z_nabijacka", **box(24, 12, 5, [0, 41.0, 33.1]), group="B", mass=5, color="pcb",
    label="nabíjačka 2S z USB-C (IP2326)")
add(name="Z_USB_C", **box(9, 7.5, 3.3, [0, 49.0, 33.2]), group="B", mass=1, color="metal", label="USB-C vzadu")
add(name="Z_vypinac", **box(7, 6.5, 7, [18, 47.75, 27.5]), group="B", mass=1, color="black", label="vypínač vzadu")
ALLOW += [["Z_USB_C", "Z_shell"], ["Z_vypinac", "Z_shell"], ["Z_USB_C", "Z_nabijacka"]]
add(name="Z_uzol", **box(4, 23.5, 18, [38, -26, 21]), group="B", mass=3, color="pcb",
    label="uzol základne RP2040-Zero (enkodéry PIO, zbernica)")
add(name="Z_driver", **box(3, 20.3, 15.2, [-37.5, -26, 21]), group="B", mass=2, color="pcb", label="driver DRV8833")
add(name="Z_menic", **box(3, 17.8, 15.2, [37.5, 26, 21]), group="B", mass=2, color="pcb",
    label="menič 5 V / 1 A (D24V10F5) pre senzory a LED")
add(name="Z_ToF", **box(18, 4, 11, [0, -49.5, 28.5]), group="B", mass=1, color="pcb", label="ToF VL53L1X za tmavým oknom")
add(name="Z_svetlo", **box(44, 5, 4, [0, -50.0, 20.0]), group="B", mass=2, color="glow",
    label="svetelná lišta podstavca + svetlovod")
ALLOW += [["Z_svetlo", "Z_shell"], ["Z_ToF", "Z_shell"]]
for sx, nm in ((-1, "R"), (1, "L")):
    add(name=f"Z_motor_{nm}", **box(34, 10, 12, [sx * 31.5, 0, 16]), group="B", mass=10, color="motor",
        label="motor N20 6 V 1:150")
    add(name=f"Z_enkoder_{nm}", **box(8, 13, 13, [sx * 10.5, 0, 16]), group="B", mass=2, color="pcb",
        label="magnetický enkodér + konektor", adds=[box(5, 8, 8, [sx * 4.0, 0, 16])])
    add(name=f"Z_koleso_{nm}", **cyl(16.0, 9.0, [sx * 54.0, 0, 16.0], "x"), group="B", mass=7, color="rubber",
        label="koleso Ø32×9 s gumou")
for sy, nm in ((-1, "P"), (1, "Z")):
    add(name=f"Z_kolieska_{nm}", kind="sphere", r=5.0, at=[0, sy * 34, 5.0], group="B", mass=4, color="metal",
        label="guľôčkové koliesko 3/8\" (v kryte šachty batérie)", adds=[cyl(6.5, 4.3, [0, sy * 34, 8.35])])
    for sx in (-1, 1):
        add(name=f"Z_utes_{nm}{'R' if sx < 0 else 'L'}", **box(8, 6, 2.4, [sx * 40, sy * 31, 9.4]), group="B", mass=0.5,
            color="pcb", label="senzor okraja ITR8307 (rohová kapsa, mimo šachty batérie)")   # PACK: moved from (±14, ±40)

layout = {"name": "T1 PACK (K2 off-axis gears compact + grafts)", "Z_TT": Z_TT, "SH": SH,
          "contacts": [[-54, 0], [54, 0], [0, -34], [0, 34]], "comps": C, "allow": ALLOW}
json.dump(layout, open(os.path.join(HERE, "layout.json"), "w"), indent=1, ensure_ascii=False)
print("components:", len(C))
