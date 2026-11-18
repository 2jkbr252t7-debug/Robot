"""variant: gear bond only inside the gear root circle (r <= 13.35) - the epoxy on the 0.2 mm tooth top lands under the rail /
back floor is not counted.  Same loads as fe_cases.py; results in res_v/."""
import sys, os, numpy as np
import fe_build as FB
_orig = FB.bond_mask_fn
def bond_mask_fn():
    f = _orig()
    return lambda p: f(p) & (np.hypot(p[:, 0], p[:, 1]) <= 13.35)
FB.bond_mask_fn = bond_mask_fn
src = open("fe_cases.py").read().replace('os.makedirs("res", exist_ok=True)', 'os.makedirs("res_v", exist_ok=True)').replace('f"res/{name}', 'f"res_v/{name}')
exec(compile(src, "fe_cases_v", "exec"))
