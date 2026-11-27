import sys, time, cProfile, pstats
sys.argv = ["chk_klb.py", "K0"]
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/klb")
import numpy as np
t=time.time()
import importlib.util
src = open("/tmp/claude-0/gapwf/fin/R4/klb/chk_klb.py").read()
src = src.replace("ANG = np.unique(", "ANG = np.array([-45.0, 0.0, 135.0, 140.5]) if 1 else np.unique(")
pr = cProfile.Profile(); pr.enable()
exec(compile(src, "chk", "exec"), {"__name__": "x", "__file__": "/tmp/claude-0/gapwf/fin/R4/klb/chk_klb.py"})
pr.disable()
pstats.Stats(pr).sort_stats("cumtime").print_stats(18)
