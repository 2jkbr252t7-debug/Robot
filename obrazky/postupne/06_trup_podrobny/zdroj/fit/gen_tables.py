import sys, json, math, numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4")
import t4_common as C
out = []
def W(s=""): out.append(s)
E = C.envelopes()
def fmt_rng(r): return f"{r[0]:.2f} … {r[1]:.2f}".replace(".00", ".0")
for owner, title in (("obal", "OBAL (t4_obal.py) – shell-mounted volumes"), ("ram", "RAM (t4_ram.py) – static tower, wings, parts under the cap, dummy"),
                     ("pan", "PAN (t4_pan.py) – pan stage (P, pan frame) and lift parts (L, rest pose)")):
    W(f"**{title}**"); W()
    W("| zone | grp | shape | x | y | z | note |"); W("|---|---|---|---|---|---|---|")
    for e in E:
        if e["owner"] != owner: continue
        if e["kind"] == "box":
            W(f"| {e['name']} | {e['group']} | box | {fmt_rng(e['x'])} | {fmt_rng(e['y'])} | {fmt_rng(e['z'])} | {e['note']} |")
        else:
            ax = e["axis"]; c = e["c"]; r = f"r {e['r']:.2f}" + (f" (bore r {e['ri']:.2f})" if e.get("ri") else "")
            if ax == "z":
                W(f"| {e['name']} | {e['group']} | cyl ‖Z, {r} | axis x {c[0]:.2f} | axis y {c[1]:.3f} | {fmt_rng(e['rng'])} | {e['note']} |")
            elif ax == "x":
                W(f"| {e['name']} | {e['group']} | cyl ‖X, {r} | {fmt_rng(e['rng'])} | axis y {c[0]:.2f} | axis z {c[1]:.2f} | {e['note']} |")
            else:
                W(f"| {e['name']} | {e['group']} | cyl ‖Y, {r} | axis x {c[0]:.2f} | {fmt_rng(e['rng'])} | axis z {c[1]:.2f} | {e['note']} |")
    W()
W("**PAN_ENV – swept radius limit of everything on the pan stage (r about the Z axis, pan frame)**"); W()
W("| z from | z to | r max | shell inner half depth b_i at both ends | margin |"); W("|---|---|---|---|---|")
for z0, z1, rm in C.PAN_ENV:
    b0 = C.inner_half(max(min(z0, C.Z_IN_TOP), -82))[1]; b1 = C.inner_half(max(min(z1, C.Z_IN_TOP), -82))[1]
    W(f"| {z0} | {z1} | {rm} | {b0:.2f} / {b1:.2f} | {min(b0, b1) - rm:.2f} |")
W()
# key derived numbers
W("**Derived numbers (true offsets)**"); W()
W("| quantity | value |"); W("|---|---|")
W(f"| X_SH (outer surface on the shoulder axis) | {C.X_SH:.3f} |")
W(f"| X_KLB_END (arm interface plane) | {C.X_KLB_END:.3f} |")
for nm, z in (("light bar z -32.5", C.Z_BAR), ("grille z -48", C.Z_SLOT), ("speaker centre z -51", C.SPEAKER["z"])):
    yo = C.y_surface(0, z); P = C.inner_section(z, C.WALL, 720); yi = P[np.abs(P[:, 0]).argmin() if False else np.argmin(np.abs(P[:, 0]) + (P[:, 1] > 0) * 1e3)][1]
    W(f"| front surface at x 0, {nm}: outer y / inner y | {yo:.2f} / {yi:.2f} |")
for z in (-12.0, -24.0, -42.0, -60.0, -72.0):
    yo = C.y_surface(0, z, 1); _, bi = C.inner_half(z)
    W(f"| back surface at x 0, z {z}: outer y / inner y | {yo:.2f} / {bi:.2f} |")
for z in (-10.5, -4.5, -2.0, 1.75):
    ai, bi = C.inner_half(z); W(f"| inner half width a_i / half depth b_i at z {z} | {ai:.2f} / {bi:.2f} |")
L = C.lip_outline(C.Z_WHITE, C.WALL, 720)
for x in (0, 10, 16.75, 20, 25, 30, 33.05):
    m = (np.abs(L[:, 0] - x) < 0.25) & (L[:, 1] < 0); W(f"| white lip inner half depth at x {x} (z -81) | {np.abs(L[m, 1]).mean():.2f} |")
for z in (-81.0, -80.5, -80.0, -79.0, -78.0):
    P = C.inner_section(z, C.WALL, 720); m = (np.abs(P[:, 0] - 16.25) < 0.3) & (P[:, 1] < 0)
    W(f"| lip inner half depth at x 16.25, z {z} (pan-servo tab corner needs 27.55) | {np.abs(P[m, 1]).mean():.2f} |")
# door hook / ledge radial positions
for x in (12.0, 20.0):
    yo = C.y_surface(x, -12.0, 1); W(f"| door hook tab at x {x}, z -12: outer y {yo:.2f} -> inner corner radius (inset 3.6) | {math.hypot(x, yo) - 3.6:.2f} |")
for (x, z) in C.DOOR_MAGNETS["xz"][::2]:
    yo = C.y_surface(x, z, 1); W(f"| door magnet pad at x {x}, z {z}: outer y {yo:.2f} -> pad inner radius (inset 7.2) | {math.hypot(x, yo) - 7.2:.2f} |")
open("/tmp/claude-0/gapwf/fin/T4/fit/spec_tables.md", "w").write("\n".join(out) + "\n")
print("\n".join(out[-45:]))
