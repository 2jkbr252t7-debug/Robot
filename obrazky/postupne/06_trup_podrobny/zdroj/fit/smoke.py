"""smoke test of the t4_common CAD helpers on the cached blanks (timings for the builders)"""
import sys, time, json
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4")
import t4_common as C
bd = C._bd()
R = {}
def T(name, fn):
    t = time.time(); s = fn(); dt = time.time() - t
    try:
        n = len(s.solids()); v = s.volume; ok = bool(s.is_valid)
    except Exception as ex:
        n, v, ok = -1, 0, False
    R[name] = dict(time_s=round(dt, 1), solids=n, volume=round(v, 1), valid=ok)
    print(f"{name:34s} {dt:6.1f} s  solids {n}  vol {v:10.1f}  valid {ok}", flush=True)
    return s
st = C.stred_blank()
s1 = T("stred + collar tube", lambda: st + C.tube_z(C.R_TUBE, C.R_BORE - 1.0, C.Z_BORE_BOT, C.Z_IN_TOP))
s2 = T("stred - bore", lambda: s1 - C.cyl_z(C.R_BORE, C.Z_BORE_BOT - 0.1, C.TOP + 0.1))
s3 = T("stred - door opening", lambda: s2 - C.door_prism(C.SEAM / 2))
s4 = T("stred - light bar - grille", lambda: s3 - C.pill_prism_y(*C.BAR, 0, C.Z_BAR, -60, -30) - C.pill_prism_y(*C.SLOT, 0, C.Z_SLOT, -60, -30))
s5 = T("stred - lip relief", lambda: s4 - C.box(C.LIP_RELIEF["x"][0], C.LIP_RELIEF["x"][1], -C.LIP_RELIEF["y_min"], -20, C.Z_WHITE - 0.1, -79.5))
dv = T("door = shell & door prism", lambda: C._one(C.shell_white() & C.door_prism(0.0)))
bb = dv.bounding_box(); print("   door bbox x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % (bb.min.X, bb.max.X, bb.min.Y, bb.max.Y, bb.min.Z, bb.max.Z))
bk = C.bok_blank(1)
b1 = T("bok_L - socket hole", lambda: bk - C.cyl_x(C.R_SOCKET, C.X_SEAT, 60, C.SH_Y, C.SH_Z))
tube = T("socket tube & outer", lambda: (C.cyl_x(16.0, C.X_COL_STOP, C.X_SH + 3, C.SH_Y, C.SH_Z) & C.outer_solid()))
b2 = T("bok_L + tube - bore - seat hole", lambda: C._one(b1 + tube - C.cyl_x(C.R_SOCKET, C.X_SEAT, 60, C.SH_Y, C.SH_Z) - C.cyl_x(C.R_SEAT_HOLE, 30, 60, C.SH_Y, C.SH_Z)))
cp = C.cap_blank()
c1 = T("cap + spigot", lambda: cp + (C.se_prism(*C.SPIGOT_SE, C.Z_CAP_TOP - 0.3, C.SPIGOT["z"][1]) - C.se_prism(*C.TUB_SE, C.Z_CAP_TOP - 1.0, C.SPIGOT["z"][1] + 0.1)))
c2 = T("cap - tub - pocket", lambda: c1 - C.se_prism(*C.TUB_SE, C.Z_FLOOR, -77) - C.box(-30.0, 16.2, -12.55, 12.55, C.Z_J1[0], C.Z_FLOOR + 0.1))
c3 = T("cap + plinth + skirt", lambda: c2 + C.tube_z(C.R_PLINTH, C.R_FOOT_SHOULDER, C.Z_BRG[1], C.Z_BOT + 0.3) + C.tube_z(C.R_FOOT_LOW, C.R_FOOT_SEAT, C.Z_BRG[0], C.Z_BRG[1])
       + C.tube_z(C.SKIRT["r"], C.R_PLINTH - 0.5, *C.SKIRT["z"]))
c4 = T("cap - pinion notch - screw holes", lambda: c3 - C.cyl_z(C.R_J1_NOTCH, -90.6, C.Z_BOT - 0.1, *C.J1_AX) - C.cyl_z(7.2, -90, -80, *C.J1_AX)
       - sum((C.screw_hole("M2.5c", 8, (x, y, C.Z_BOT), "z", 1) for x, y in C.SCR_STRED[1:]), C.screw_hole("M2.5c", 8, (*C.SCR_STRED[0], C.Z_BOT), "z", 1)))
i4 = T("inner_solid(4.0) (door ledge)", lambda: C.inner_solid(4.0))
T("screw M2.5c + insert + magnet", lambda: C.screw("M2.5c", 8, (0, 0, 0)) + C.insert("M2.5", (5, 0, 0)) + C.magnet(5, 2, (10, 0, 0)))
print("mesh volumes: stred_final %.0f  bok_L %.0f  cap %.0f" % (C.mesh_volume(s5), C.mesh_volume(b2), C.mesh_volume(c4)))
json.dump(R, open("/tmp/claude-0/gapwf/fin/T4/fit/smoke.json", "w"), indent=1)
