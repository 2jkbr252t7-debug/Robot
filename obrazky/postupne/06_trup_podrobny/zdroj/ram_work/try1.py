import sys, time
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4")
import t4_common as C, t4_ram as M
def show(name, s, t):
    bb = s.bounding_box()
    print(f"{name:18s} {time.time()-t:5.1f}s valid {s.is_valid} solids {len(s.solids())} vol {s.volume:9.1f} bbox x {bb.min.X:.2f}..{bb.max.X:.2f} y {bb.min.Y:.2f}..{bb.max.Y:.2f} z {bb.min.Z:.2f}..{bb.max.Z:.2f}", flush=True)
for nm in sys.argv[1:]:
    t = time.time()
    fn = getattr(M, nm)
    s = fn()
    show(nm, s, t)
