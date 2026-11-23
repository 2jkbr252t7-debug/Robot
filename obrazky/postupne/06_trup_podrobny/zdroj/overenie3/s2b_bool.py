# exact BREP common of pairs from the STEP files (independent of the STL sampling)
import sys, os, time
import build123d as bd
T4 = "/tmp/claude-0/gapwf/fin/T4"
_c = {}
def S(n):
    if n not in _c:
        s = bd.import_step(f"{T4}/step/{n}.step"); _c[n] = s
    return _c[n]
pairs = [a.split(":") for a in sys.argv[1:]]
for a, b in pairs:
    t = time.time()
    try:
        A, B = S(a), S(b)
        c = A & B
        sol = c.solids() if c is not None else []
        v = sum(s.volume for s in sol)
        print(f"{a} & {b}: common volume {v:.4f} mm3 in {len(sol)} solids  ({time.time()-t:.1f}s)")
        for s in sorted(sol, key=lambda s: -s.volume)[:12]:
            bb = s.bounding_box()
            print(f"    v {s.volume:.4f}  x {bb.min.X:.2f}..{bb.max.X:.2f}  y {bb.min.Y:.2f}..{bb.max.Y:.2f}  z {bb.min.Z:.2f}..{bb.max.Z:.2f}  min size {min(bb.size.X, bb.size.Y, bb.size.Z):.3f}")
    except Exception as e:
        print(f"{a} & {b}: ERROR {type(e).__name__} {e}")
