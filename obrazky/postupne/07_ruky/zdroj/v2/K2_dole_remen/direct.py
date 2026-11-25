"""Why no direct drive (servo shaft = arm axis inside the torso): free length along the shoulder axis inside the torso.
Inner limit = pan / lift sweep r 33.40 (PAN_ENV2, z -40.9..-17) + 1.0 moving clearance; outer limit = inner face of the
side-cap wall on the axis (true 2.2 offset of the approved outer surface).  Writes direct.json"""
import sys, os, json, math
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4"); os.chdir("/tmp/claude-0/gapwf/fin/T4"); import t4_common as C
x_out = C.x_surface(3.0, -17.0)
lo, hi = 40.0, x_out
for _ in range(40):
    m = 0.5 * (lo + hi)
    if C.clearance_to_shell(np.array([[m, 3.0, -17.0]]), wall=2.2)[0] > 0: lo = m
    else: hi = m
x_wall = lo
x_in = math.sqrt((33.40 + 1.0) ** 2 - 0.0 ** 2)          # worst azimuth y = 0 (column inner face x 34.4)
res = dict(outer_surface_x=round(x_out, 3), inner_wall_x=round(x_wall, 2), sweep_limit_x=round(x_in, 2),
           free_length=round(x_wall - x_in, 2), servos={})
for nm, case, spl in (("SCS0009 (case 21.5 opt.)", 21.5, 3.75), ("SCS0009 (case 25.25)", 25.25, 3.75), ("MG90S", 22.7, 5.7),
                      ("STS3032", 23.0, 7.0), ("KST X06", 16.6, 3.0)):
    face = x_in + case
    res["servos"][nm] = dict(case_depth=case, output_face_x=round(face, 2), sticks_out_of_surface=round(face - x_out, 2),
                             spline_top_x=round(face + spl, 2))
print(json.dumps(res, indent=1))
json.dump(res, open("/tmp/claude-0/gapwf/fin/R1/K2_dole_remen/direct.json", "w"), indent=1)
