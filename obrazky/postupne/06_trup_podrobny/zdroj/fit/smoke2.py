"""smoke test 2: other insets, the door-ledge recipe of T4_spec 4.3 (overlap version), helper primitives"""
import sys, time, json
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4")
import t4_common as C
def T(name, fn):
    t = time.time(); s = fn(); dt = time.time() - t
    print(f"{name:44s} {dt:6.1f} s  solids {len(s.solids())}  vol {s.volume:10.1f}  valid {s.is_valid}", flush=True)
    return s
print("inner z range 2.2:", C.inner_z_range(2.2), " 4.0:", C.inner_z_range(4.0))
i20 = T("inner_solid(2.0)", lambda: C.inner_solid(2.0))
i24 = T("inner_solid(2.4)", lambda: C.inner_solid(2.4))
i40 = T("inner_solid(4.0)", lambda: C.inner_solid(4.0))
ins = T("ledge inside  (2.4..4.0, behind the door)", lambda: (i24 - i40) & (C.door_prism(0.25) - C.door_prism(-1.75)))
out = T("ledge outside (2.0..4.0, on the wall)", lambda: (i20 - i40) & (C.door_prism(2.25) - C.door_prism(0.25)))
st = C.stred_blank() - C.door_prism(C.SEAM / 2)
r = T("stred(open) + ledge", lambda: st + ins + out)
print("   mesh volume", round(C.mesh_volume(r)), flush=True)
T("screw M2.5c + insert + magnet", lambda: C.screw("M2.5c", 8, (0, 0, 0)) + C.insert("M2.5", (5, 0, 0)) + C.magnet(5, 2, (10, 0, 0)))
T("screw_hole + insert_hole + magnet_hole", lambda: C.box(-5, 15, -5, 5, -12, 2) - C.screw_hole("M2", 6, (0, 0, 0), "z", -1) - C.insert_hole("M2.5", (5, 0, 2), "z", -1) - C.magnet_hole(5, 2, (10, -5, -5), "y", 1))
T("rbox + pill + rrect", lambda: C.rbox(0, 10, 0, 6, 0, 4, 1.0, "z") + C.pill_prism_y(8, 3, 20, 0, 0, 2) + C.rrect_prism_y(10, 8, 2, 40, 0, 0, 2))
