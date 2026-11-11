"""sweep STD_POSES + K2 extra poses -> sweep_raw.json"""
import sys, json, time
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T1")
import t1lib as T

EXTRA = [
    {"pan": 85, "lift": 20, "tilt": -40}, {"pan": -85, "lift": 20, "tilt": 40},
    {"pan": 85, "lift": 12.5, "tilt": 30}, {"pan": -85, "lift": 12.5, "tilt": -40},
    {"pan": 85, "lift": 0, "tilt": 5}, {"pan": -85, "lift": 0, "tilt": -10},
    {"pan": 85, "lift": 5}, {"pan": -85, "lift": 10}, {"pan": 60, "lift": 15}, {"pan": -45, "lift": 20},
    {"pan": 30, "lift": 2.5}, {"pan": -30, "lift": 17.5},
    {"lift": 12.5, "tilt": 10, "pan": 30, "armR": 60, "armL": -20},          # awake pose
    {"armR": -45, "armL": -45, "lift": 20, "tilt": 40},
    {"armR": 100, "armL": 100}, {"armR": 100, "armL": 100, "lift": 20, "tilt": 40},
    {"armR": 180, "armL": 180, "pan": 85, "lift": 20}, {"armR": 180, "armL": 180, "pan": -85, "lift": 20},
    {"armR": 45, "armL": 45, "pan": 85, "lift": 20, "tilt": 40},
    {"j1": 150, "armR": 100, "armL": 100, "pan": 85, "lift": 20},
    {"j1": -150, "armR": 180, "armL": 180, "pan": -85},
    {"j1": 75, "armR": -45, "armL": 90, "pan": -60, "lift": 12.5, "tilt": 30},
    {"j1": -75, "armR": 0, "armL": 0},
]
if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "std"
    poses = T.STD_POSES if which == "std" else EXTRA
    L = T.Layout("/tmp/claude-0/gapwf/fin/T1/k2/layout.json")
    t0 = time.time()
    res = {}
    for i, p in enumerate(poses):
        cl = L.clashes(p, 0.5, only_moving=True)
        res[i] = {"pose": p, "clashes": cl}
        print(i, p, cl, round(time.time() - t0), flush=True)
    json.dump(res, open(f"/tmp/claude-0/gapwf/fin/T1/k2/sweep_{which}.json", "w"), indent=1)
