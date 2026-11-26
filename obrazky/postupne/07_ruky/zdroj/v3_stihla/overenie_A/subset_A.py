"""Verifier: is variant A a subset of the approved arm (variant 0)?  Level of the approved section at A's surface points."""
import sys, numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/overenie_A")
import geomA as G
P, H = G.surface(0.0, 1.0, 0.05, 0.62, 0.95)
lv = G.level(P[:-2], 1.0, 1.0)
k = int(np.argmax(lv))
print("A surface points", len(P), " max approved-level", float(lv.max()), "at local", P[k].round(3))
print("points with level > 1 + 1e-9:", int((lv > 1 + 1e-9).sum()))
# distance by which the inner face recedes at y/w = 0.55 (critical point at +135 deg, u 0.045)
u = 0.045; hw, ht = G.prof(u)
for f in (0.0, 0.3, 0.55, 0.8):
    y = f * 0.95 * hw
    x0 = ht * (1 - (y / hw) ** 2.3) ** (1 / 2.3); xA = ht * (1 - (y / (0.95 * hw)) ** 2.3) ** (1 / 2.3)
    print(f"u {u} y/wA {f}: inner face approved {-x0:.3f}  A {-xA:.3f}  recedes {x0 - xA:.3f} mm")
