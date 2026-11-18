"""bounding boxes of every part that matters for the well bottom (T4 STL + B STL)"""
import sys, numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4")
import t4_mesh as M
T4 = "/tmp/claude-0/gapwf/fin/T4/stl"; B = "/tmp/claude-0/gapwf/fin/B/stl"
names = ["P_sachta", "koleso_pan", "T_cap", "T_most", "skr_F15", "pd_F15", "ptfe_cap", "ptfe_podlozka", "ptfe_pas_capu",
         "P_drziak_serva", "L_pata", "L_ucho", "vl_F10_A", "vl_F10_B", "kolik_F10", "skr_F10_A", "skr_F10_B", "podl_F10_A",
         "T_paluba", "T_spodok", "lozisko_6805", "servo_J1", "servo_zdvih", "pastorok_pan", "kolik_dorazu_1", "kolik_dorazu_2", "T_stred"]
for n in names:
    try:
        T = M.read_stl(f"{T4}/{n}.stl")
    except Exception as e:
        print(n, "missing", e); continue
    lo, hi = T.reshape(-1, 3).min(0), T.reshape(-1, 3).max(0)
    print(f"{n:16s} tris {len(T):6d}  x {lo[0]:8.3f} {hi[0]:8.3f}  y {lo[1]:8.3f} {hi[1]:8.3f}  z {lo[2]:8.3f} {hi[2]:8.3f}")
for n in ["krk_predna_polovica", "krk_zadna_polovica", "golier_kotuc", "golier_prstenec", "hlava_skrupina", "CELOK_pokoj", "klzny_kruzok"]:
    T = M.read_stl(f"{B}/{n}.stl")
    lo, hi = T.reshape(-1, 3).min(0), T.reshape(-1, 3).max(0)
    print(f"B {n:20s} tris {len(T):6d}  x {lo[0]:8.3f} {hi[0]:8.3f}  y {lo[1]:8.3f} {hi[1]:8.3f}  z {lo[2]:8.3f} {hi[2]:8.3f}")
