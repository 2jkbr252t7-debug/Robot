import sys, json, time
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T1")
import t1lib as T
L = T.Layout("/tmp/claude-0/gapwf/fin/T1/k3/layout.json")
poses = T.STD_POSES if sys.argv[1] == "std" else json.load(open(sys.argv[1]))
out = {}
for i, p in enumerate(poses):
    t = time.time()
    cl = L.clashes(p, only_moving=True)
    out[i] = {"pose": p, "clashes": cl}
    print(i, p, cl, round(time.time() - t, 1), flush=True)
json.dump(out, open(sys.argv[2], "w"), indent=1)
