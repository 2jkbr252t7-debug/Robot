import sys; sys.dont_write_bytecode=True
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie3")
import vlib, os, numpy as np
d="/tmp/claude-0/gapwf/fin/B/stl"
for f in sorted(os.listdir(d)):
    T=vlib.load_stl(os.path.join(d,f)); b=vlib.bbox(T)
    print("%-28s ntri %8d vol %10.1f bb %s"%(f,len(T),vlib.volume(T),np.round(b,2)))
for n in ("T_klb_L","T_bok_L","T_stred","T_spodok","T_cap","T_most","T_paluba"):
    T=vlib.load_stl(f"/tmp/claude-0/gapwf/fin/T4/stl/{n}.stl"); print(n,len(T),round(vlib.volume(T),1),np.round(vlib.bbox(T),3))
