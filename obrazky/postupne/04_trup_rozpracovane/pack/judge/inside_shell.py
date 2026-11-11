"""volume of every internal part that lies OUTSIDE the outer envelope of its shell (rest pose) + min wall distance"""
import sys, json
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T1"); import t1lib as T
from build123d import Pos
L = T.Layout(sys.argv[1])
def outer(name):
    c = dict(L.comp(name)); c["kind"] = "sblock"; c.pop("cuts", None); c.pop("adds", None)
    return T.raw_shape(c)
TS = outer(sys.argv[2]); ZS = outer(sys.argv[3])
for c in L.comps:
    n = c["name"]
    if n in (sys.argv[2], sys.argv[3]) or n.startswith("B_") or c["group"] in ("AR", "AL", "H", "L"):
        continue
    sh = L.shape(n, {})
    env = ZS if c["group"] == "B" else TS
    try:
        out = sh.volume - (sh & env).volume
    except Exception as e:
        out = -1
    if out > 0.5:
        print(f"{n:26s} {c['group']:2s} outside {out:8.1f} mm3 of {sh.volume:8.1f}  bb {[round(v,1) for v in (sh.bounding_box().min.X, sh.bounding_box().max.X, sh.bounding_box().min.Y, sh.bounding_box().max.Y, sh.bounding_box().min.Z, sh.bounding_box().max.Z)]}")
