import sys, numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie3")
import vlib
for n in ("T_spodok", "T_klb_L", "T_bok_L"):
    M = vlib.Mesh(vlib.load_stl(f"/tmp/claude-0/gapwf/fin/T4/stl/{n}.stl"))
    rows = []
    for x in np.arange(33.0, 60.01, 0.5):
        rr = []
        for r in (0.0, 2.0, 3.5, 4.5, 5.0, 5.5, 7.5, 9.0, 10.5, 11.5, 13.0):
            P = np.array([[x, 3.0 + r * np.cos(a), -17.0 + r * np.sin(a)] for a in np.linspace(0, 2 * np.pi, 12, endpoint=False)])
            rr.append(int(M.inside(P).sum()))
        rows.append((x, rr))
    print("==", n, "inside counts of 12 points at r = 0 2 3.5 4.5 5 5.5 7.5 9 10.5 11.5 13")
    for x, rr in rows:
        if any(rr): print(f"  x {x:5.1f}: {rr}")
