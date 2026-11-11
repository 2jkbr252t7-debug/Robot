import sys, json
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T1"); import t1lib as T
L = T.Layout(sys.argv[1])
poses = [{}, {"armR": 90, "armL": 90}, {"armR": 180, "armL": 180}, {"armR": -45, "armL": -45},
         {"pan": 85, "lift": 20}, {"pan": -85}, {"j1": 150}]
out = {}
for pr in sorted(L.allow, key=lambda p: sorted(p)):
    a, b = sorted(pr)
    try:
        ca, cb = L.comp(a), L.comp(b)
    except StopIteration:
        continue
    vols = []
    for p in poses:
        try:
            v = (L.shape(a, p) & L.shape(b, p)).volume
        except Exception as e:
            v = -1
        vols.append(round(v, 1))
    out[f"{a} x {b}"] = {"groups": [ca["group"], cb["group"]], "vols": vols}
    print(f"{a:24s} {b:24s} {ca['group']:3s}{cb['group']:3s} {vols}", flush=True)
json.dump(out, open(sys.argv[2], "w"), indent=1)
