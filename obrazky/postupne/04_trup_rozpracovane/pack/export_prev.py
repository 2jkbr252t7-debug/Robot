import sys
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T1")
import t1lib as T
L = T.Layout("/tmp/claude-0/gapwf/fin/T1/pack/layout.json")
POSES = {"rest": {}, "awake": {"lift": 12.5, "tilt": 10, "pan": 30, "armR": 60, "armL": -20}}
for k in (sys.argv[1:] or POSES):
    L.export(POSES[k], f"/tmp/claude-0/gapwf/fin/T1/pack/exp_{k}")
    print("exported", k)
