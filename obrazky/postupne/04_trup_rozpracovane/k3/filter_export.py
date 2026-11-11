"""make a filtered copy of an export dir (parts.json only; STL paths are absolute)"""
import json, os, sys
src, dst, mode = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(os.path.join(src, "parts.json")))
keep = []
for p in d["parts"]:
    n, g = p["name"], p["group"]
    if mode == "noarms" and g in ("AR", "AL"):
        continue
    if mode == "baseplan" and (g != "B" or n in ("Z_shell", "Z_sokel", "Z_paluba", "Z_J1_slucka", "Z_J1_lozisko")):
        continue
    if mode == "torsoplan" and (g not in ("T", "P", "L") or n in ("T_shell", "B_golier_prstenec") or n.startswith("B_")):
        continue
    keep.append(p)
d["parts"] = keep
os.makedirs(dst, exist_ok=True)
json.dump(d, open(os.path.join(dst, "parts.json"), "w"), indent=1)
print(dst, len(keep))
