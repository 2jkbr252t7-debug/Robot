"""self-test of pv_lib on known shapes (analytic) and first look at the column sections of T_ram"""
import numpy as np, pv_lib as L
log = L.Log("p00_selftest")
# analytic: dowel D6 x 6.5 (cap_pan): area pi*9 = 28.274, I = pi*81/4 = 63.617
r = L.sec("cap_pan", "z", -44.0, h=0.005)
log("cap_pan section: A %.3f (28.274)  Iu %.3f Iw %.3f (63.617)" % (r["A"], r["Iu"], r["Iw"]))
log("cap_pan chord through the axis:", L.chords("cap_pan", (-10, 0, -44), (1, 0, 0)))
log("volume cap_pan %.2f (183.8)" % L.volume(L.load("cap_pan")))
# column of T_ram (left, +X) at several heights; window x 33..44, y -12..18
for z in (-76.0, -70.013, -55.013, -45.013, -35.013, -31.013, -29.513, -28.013, -26.013, -24.013, -22.513):
    r = L.sec("T_ram", "z", z, window=(33.0, 44.5, -12.0, 18.0))
    if r["A"] == 0:
        log(z, "empty"); continue
    zm = L.zmods(r)
    log("T_ram left column z %7.3f: A %6.2f  x %.2f..%.2f (cx %.2f)  y %.2f..%.2f  I_about_y(bend in x) %7.1f  Z %6.1f / %6.1f   I_about_x %8.1f"
        % (z, r["A"], r["umin"], r["umax"], r["cu"], r["wmin"], r["wmax"], r["Iw"], zm["Zw_p"], zm["Zw_m"], r["Iu"]))
    if z in (-45.013, -29.513, -26.013):
        L.picture(r, L.OUT + "/col_z%g.png" % z, scale=30)
