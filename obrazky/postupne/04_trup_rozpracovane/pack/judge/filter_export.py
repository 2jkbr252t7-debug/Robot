"""make a filtered export dir (parts.json only) for internal-only plan renders"""
import json, os, sys
src, dst, mode = sys.argv[1], sys.argv[2], sys.argv[3]
m = json.load(open(os.path.join(src, "parts.json")))
if mode == "base":
    keep = lambda p: p["group"] == "B" and p["name"] != "Z_shell"
else:  # torso internals
    keep = lambda p: p["group"] in ("T", "P", "L") and p["name"] not in ("T_shell",) and not p["name"].startswith("B_")
m["parts"] = [p for p in m["parts"] if keep(p)]
os.makedirs(dst, exist_ok=True)
json.dump(m, open(os.path.join(dst, "parts.json"), "w"), indent=1)
print(len(m["parts"]), "parts")
