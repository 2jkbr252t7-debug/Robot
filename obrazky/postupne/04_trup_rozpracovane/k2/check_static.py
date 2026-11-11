import sys, json, time
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T1")
import t1lib as T
t0 = time.time()
L = T.Layout("/tmp/claude-0/gapwf/fin/T1/k2/layout.json")
for c in L.comps:
    s = L.raw(c["name"])
    if not s.is_valid:
        print("INVALID", c["name"])
print("built", round(time.time() - t0, 1), "s")
bb = L.raw("T_shell").bounding_box(); print("T_shell bb", bb.min, bb.max, "vol", round(L.raw("T_shell").volume))
bb = L.raw("Z_shell").bounding_box(); print("Z_shell bb", bb.min, bb.max, "vol", round(L.raw("Z_shell").volume))
cl = L.clashes({})
print("static clashes:", len(cl))
for c in cl:
    print("  ", c)
print("t", round(time.time() - t0, 1))
