import json, sys
for f in sys.argv[1:]:
    d = json.load(open(f))
    for v, r in d.items():
        print(f"{v:3s} T {r['thickness_max']:5.2f} W {r['width_max']:5.2f} | rest {r['gap_rest']:.3f} at {r['gap_rest_at']} | min {r['gap_min_-45_135']:.3f} @{r['gap_min_angle']} "
              f"| 140.5 {r['gap_at_140.5']:.3f} | robot {r['robot_width_over_arms']} | inner x {r['innermost_world_x']} | out of B0 {r['max_outside_approved_mm']} x>={r.get('outside_world_x_min')}")
