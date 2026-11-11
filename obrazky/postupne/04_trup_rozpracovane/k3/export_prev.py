import sys, json
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T1")
import t1lib as T
L = T.Layout("/tmp/claude-0/gapwf/fin/T1/k3/layout.json")
poses = {"rest": {}, "awake": {"lift": 12.5, "tilt": 10, "pan": 30, "armR": 60, "armL": -20}}
for k in sys.argv[1:]:
    L.export(poses[k], f"/tmp/claude-0/gapwf/fin/T1/k3/exp_{k}")
    print("exported", k)
