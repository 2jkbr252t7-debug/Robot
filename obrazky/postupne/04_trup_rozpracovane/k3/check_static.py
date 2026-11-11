import sys, json, time
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T1")
import t1lib as T

L = T.Layout("/tmp/claude-0/gapwf/fin/T1/k3/layout.json")
t = time.time()
bad = []
for c in L.comps:
    s = L.raw(c["name"])
    bb = s.bounding_box()
    v = s.volume
    if not s.is_valid or v <= 0:
        bad.append(c["name"])
    if c["name"] in ("T_shell", "Z_shell", "A_R_skrupina", "P_sachta", "Z_sokel", "T_paluba", "Z_paluba"):
        print(f"{c['name']:22s} valid={s.is_valid} vol={v:9.0f} bb x[{bb.min.X:.1f},{bb.max.X:.1f}] "
              f"y[{bb.min.Y:.1f},{bb.max.Y:.1f}] z[{bb.min.Z:.1f},{bb.max.Z:.1f}] m={L.mass_of(c):.1f}")
print("invalid/empty:", bad)
cl = L.clashes({})
print("static clashes:", len(cl)); json.dump({"count": len(cl), "pairs": cl}, open("/tmp/claude-0/gapwf/fin/T1/k3/check_parts/static.json", "w"))
for a in cl:
    print("  ", a)
print("time", round(time.time() - t, 1))
M, cog, rows = L.cog({})
print("mass", round(M, 1), "cog", [round(v, 1) for v in cog])
print(L.tipping({}, accel_g=0.15))
