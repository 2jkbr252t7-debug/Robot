"""m02 - real space for the pan cable crossing (rolling loop) between the static deck and the rotating stage.
For every polar cell (r, azimuth, torso frame) between z -49 and -36:
  floor   = highest static surface below z -43.5 (deck top, bosses, pinion ...; the present FPC channel wall, clamp,
            clamp screw and FPC itself are IGNORED because they would be replaced)
  ceiling = lowest point of any pan-stage / lift part over the sweep pan -85..+85 (lift parts at rest = lowest),
            or of a static part above the floor
  height  = ceiling - floor   (free duct height for a flat cable standing on edge)
Also the free radial extent of the back half and the space at the deck pivot (screw head / counterbore).
Run: /opt/venv/cad/bin/python m02_pan_duct.py  (about 30 s)"""
import numpy as np, math
from zj_lib import read_stl, sample, dump, say, bbox

DR, DA = 0.5, 2.0
RB = np.arange(10.0, 36.01, DR)
AB = np.arange(0.0, 360.0, DA)
NR, NA = len(RB) - 1, len(AB)

static = ["T_paluba", "T_ram", "T_spodok", "T_stred", "T_bok_L", "T_bok_P", "servo_pan", "pastorok_pan",
          "skr_pastorok_pan", "cap_pan", "ptfe_podlozka", "skr_F3_1", "skr_F3_2", "skr_F3_3", "skr_F3_4",
          "kondenzator", "DPS_riadenie", "menic", "zosilnovac", "skr_F4_1", "skr_F4_2", "T_drziak_led",
          "reproduktor", "T_drziak_repro"]
rot = ["P_sachta", "P_koleso", "P_drziak_serva", "P_kluka", "servo_zdvih", "L_pata", "L_jazyk", "L_ucho",
       "spoj_zdvih", "kabel_zdvih", "cap_kluky", "kolik_dorazu", "skr_F10_1", "vl_F10_1", "skr_F10_2", "skr_F11",
       "skr_kluky", "skr_F12", "skr_jazyka", "kolik_ucha", "kolik_kolesa_1", "kolik_kolesa_2"]
ZLO, ZHI, ZSPLIT = -49.0, -36.0, -43.5


def cells(P):
    r = np.hypot(P[:, 0], P[:, 1]); a = np.degrees(np.arctan2(P[:, 1], P[:, 0])) % 360
    ir = np.floor((r - RB[0]) / DR).astype(int); ia = np.floor(a / DA).astype(int) % NA
    ok = (ir >= 0) & (ir < NR)
    return ir[ok], ia[ok], P[ok, 2]


floor = np.full((NR, NA), -60.0)      # highest static z below ZSPLIT
sceil = np.full((NR, NA), 99.0)       # lowest static z above ZSPLIT
for n in static:
    P = sample(read_stl(n), 0.3)
    P = P[(P[:, 2] > ZLO) & (P[:, 2] < ZHI)]
    if n == "T_paluba":   # drop the present FPC channel wall (r 23.4..25.2, z > -45.95) - it is replaced
        r = np.hypot(P[:, 0], P[:, 1])
        P = P[~((r > 23.3) & (r < 25.3) & (P[:, 2] > -45.95))]
    if len(P) == 0:
        continue
    ir, ia, z = cells(P)
    lo = z <= ZSPLIT
    np.maximum.at(floor, (ir[lo], ia[lo]), z[lo])
    np.minimum.at(sceil, (ir[~lo], ia[~lo]), z[~lo])
    say("static", n, len(P))

rmin = np.full((NR, NA), 99.0)        # stage frame: lowest rotating z per cell
for n in rot:
    P = sample(read_stl(n), 0.3)
    P = P[(P[:, 2] > ZLO) & (P[:, 2] < ZHI)]
    if len(P) == 0:
        continue
    ir, ia, z = cells(P)
    np.minimum.at(rmin, (ir, ia), z)
    say("rot", n, len(P))
# sweep pan -85..85: torso cell A sees stage cell A - phi
K = int(round(85 / DA))
sweep = np.full((NR, NA), 99.0)
for k in range(-K, K + 1):
    sweep = np.minimum(sweep, np.roll(rmin, k, axis=1))
ceil = np.minimum(sweep, sceil)
height = ceil - floor

res = {"method": __doc__, "grid": dict(dr=DR, da=DA)}
# table: radial profile of the free height at several azimuths of the back half and the front
rows = []
for az in (0, 20, 45, 60, 90, 120, 135, 160, 180, 200, 230, 254, 270, 300, 330):
    ia = int(az / DA)
    row = dict(az=az)
    for r0 in (13, 15, 16, 18, 20, 22, 24, 26, 28, 30, 31, 32, 33, 34):
        ir = int((r0 - RB[0]) / DR)
        row[f"r{r0}"] = (round(float(floor[ir, ia]), 2), round(float(ceil[ir, ia]), 2), round(float(height[ir, ia]), 2))
    rows.append(row)
res["floor_ceiling_height_by_az_r"] = rows

# minimum free height over an annulus and an azimuth sector
def annulus(r0, r1, a0, a1):
    i0, i1 = int((r0 - RB[0]) / DR), int((r1 - RB[0]) / DR)
    j0, j1 = int(a0 / DA), int(a1 / DA)
    H = height[i0:i1, j0:j1]; F = floor[i0:i1, j0:j1]; C = ceil[i0:i1, j0:j1]
    k = np.unravel_index(np.argmin(H), H.shape)
    return dict(r=(r0, r1), az=(a0, a1), h_min=round(float(H.min()), 2), h_median=round(float(np.median(H)), 2),
                floor_max=round(float(F.max()), 2), ceil_min=round(float(C.min()), 2),
                where_min=(round(RB[i0 + k[0]] + DR / 2, 2), round(AB[j0 + k[1]] + DA / 2, 1)))


res["annuli"] = [annulus(*a) for a in [(16, 23.5, 10, 170), (16, 25, 10, 170), (16, 28, 10, 170), (16, 30, 10, 170),
                                         (16, 31, 10, 170), (16, 32, 10, 170), (16, 30, 20, 160), (16, 30, 0, 180),
                                         (25, 30, 10, 170), (16, 28, 200, 340)]]
for a in res["annuli"]:
    say(a)

# outer static wall limit in the back half at z -46..-42: nearest static material outside r 16 (T_ram, T_stred ...)
outer = []
for az in range(0, 181, 15):
    ia = int(az / DA) % NA
    # first radius where something static rises above -45.5 (i.e. a wall in the duct)
    col = sceil[:, ia]
    fl = floor[:, ia]
    hit = [RB[i] for i in range(NR) if (RB[i] > 16 and (col[i] < -40.0 or fl[i] > -45.5))]
    outer.append((az, round(float(hit[0]), 2) if hit else None))
res["first_static_obstacle_r_by_az(back half, above -45.5)"] = outer
say("outer", outer)

# ---- deck pivot zone: deck boss, pin, hub, foot underside, gear bore ------------------------------------------------
piv = {}
for n in ("T_paluba", "cap_pan", "P_koleso", "P_sachta", "L_pata", "ptfe_podlozka"):
    P = sample(read_stl(n), 0.2)
    r = np.hypot(P[:, 0], P[:, 1])
    s = r < 8.0
    if s.any():
        piv[n] = dict(z=(round(float(P[s, 2].min()), 3), round(float(P[s, 2].max()), 3)),
                      r_min=round(float(r[s].min()), 3))
# L_pata material near the axis: thickness under the neck (z range at r < 6)
P = sample(read_stl("L_pata"), 0.2); r = np.hypot(P[:, 0], P[:, 1])
piv["L_pata_r<6_z"] = (round(float(P[r < 6, 2].min()), 3), round(float(P[r < 6, 2].max()), 3))
P = sample(read_stl("P_sachta"), 0.2); r = np.hypot(P[:, 0], P[:, 1])
for rr in (3.5, 5.0, 6.0, 8.0, 10.0, 12.6):
    s = (r > rr - 0.25) & (r < rr + 0.25)
    if s.any():
        piv[f"P_sachta_at_r{rr}_z"] = (round(float(P[s, 2].min()), 3), round(float(P[s, 2].max()), 3))
res["pivot_zone"] = piv
say(piv)

# ---- J1 axis: what occupies x=y=0 between the cap floor and the deck (capsule slip ring?) ----------------------
ax = {}
for n in ("servo_J1", "T_spodok", "T_paluba", "pastorok_J1", "Z_naboj_test", "lozisko_6805", "Z_koleso_J1",
          "Z_skrutka_M8"):
    P = sample(read_stl(n), 0.3)
    r = np.hypot(P[:, 0], P[:, 1])
    s = r < 7.0
    if s.any():
        ax[n] = (round(float(P[s, 2].min()), 2), round(float(P[s, 2].max()), 2))
res["axis_r<7_occupied_z"] = ax
say(ax)
np.savez_compressed("/tmp/claude-0/gapwf/fin/T4/zjednodusenie/m02_grid.npz", floor=floor, ceil=ceil, RB=RB, AB=AB)
dump("m02_pan_duct.json", res)
