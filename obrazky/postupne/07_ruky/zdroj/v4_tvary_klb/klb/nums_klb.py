"""R4/klb: summary numbers for the image agent (CAD venv).  Reads chk_klb.json, chk_merged.json, build_klb.json and the
front close-up renders (prev500/front_<vid>.png, camera prev500/front_cam.json) -> klb_summary.json.
Front-view band: dark pixels (joint parts are black; the white torso / arm are light) in the shoulder window
x 43 .. 56 mm, z -33 .. -1 of the ortho front close-up -> band height (z extent) and width at the axis row."""
import os, sys, json, math
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import klb as K

CH = json.load(open(os.path.join(HERE, "chk_klb.json")))
MG = json.load(open(os.path.join(HERE, "chk_merged.json")))
BL = json.load(open(os.path.join(HERE, "build_klb.json")))
PV = os.path.join(HERE, "prev500")
cam = json.load(open(os.path.join(PV, "front_cam.json")))
W, H = cam["res"]; k = W / cam["ortho_scale"]
cx, cz = cam["matrix"][0][3], cam["matrix"][2][3]


def band(vid):
    p = os.path.join(PV, f"front_{vid}.png")
    if not os.path.exists(p):
        return None
    a = np.asarray(Image.open(p).convert("RGBA")).astype(float)
    lum = a[..., :3].mean(2)
    dark = (lum < 60) & (a[..., 3] > 200)
    xs = cx + (np.arange(W) + 0.5 - W / 2) / k
    zs = cz - (np.arange(H) + 0.5 - H / 2) / k
    mx = (xs > 43.0) & (xs < 56.0)
    rows = []
    for i, z in enumerate(zs):
        if -33 < z < -1:
            n = dark[i, mx].sum() / k
            rows.append((z, n))
    rows = np.array(rows)
    has = rows[rows[:, 1] > 0.8]
    i0 = int(np.argmin(np.abs(rows[:, 0] + 17.0)))
    area = float(rows[:, 1].sum() / k)
    return dict(band_height_mm=round(float(has[:, 0].max() - has[:, 0].min()), 1) if len(has) else 0.0,
                band_z=[round(float(has[:, 0].min()), 1), round(float(has[:, 0].max()), 1)] if len(has) else None,
                width_at_axis_mm=round(float(rows[i0, 1]), 1), black_area_mm2=round(area, 0))


OUT = {}
for vid in K.VIDS:
    v = K.variant(vid); c = CH[vid]
    s = dict(name_sk=v["name_sk"], idea_sk=v["idea_sk"], visible_d=v["visible_d"], dx=v["dx"], rotates_with=v["rotates_with"],
             arm_opening_d=round(2 * v["arm_hole_r"], 1), arm_inner_half_stl=v.get("arm_inner_half_stl"),
             parts=[dict(id=p["id"], name_sk=p["name_sk"], role=p["role"], mat=p["mat"], stl=p["stl"],
                         **({"print_stl": p["print_stl"]} if "print_stl" in p else {})) for p in v["parts"]],
             gap_white_arm_torso=dict(rest=c["B_sweep_white_T_bok_L_only"]["rest"], min_m45_135=c["B_sweep"]["min_m45_135"] if vid != "K3v" else c["B_sweep_white_T_bok_L_only"]["at_135"],
                                      at_135=c["B_sweep_white_T_bok_L_only"]["at_135"], at_140_5=c["B_sweep_white_T_bok_L_only"]["at_140_5"]),
             look=c["D_look"], look_at_r=c["D_look_at_r"], front_band=band(vid))
    for kk, vv in c.items():
        if kk.startswith("A_") and isinstance(vv, dict):
            s.setdefault("rotating_part_gaps", {})[kk[2:]] = {n: dict(min=x["min"], visible=x.get("min_outside_bore")) for n, x in vv.items()}
        elif kk.startswith("A_") and kk.endswith("_profile"):
            s["ring_to_cover_profile_gap"] = vv
        elif kk.startswith("B_arm_vs_"):
            s["arm_to_cover_gap_pose_independent"] = vv["min"]
        elif kk.startswith("C_") and kk.endswith("_vs_M2b"):
            s["vs_M2b_min"] = {r["part"]: r["dist"] for r in vv if r["dist"] < 1.0}
        elif kk.startswith("C_") and kk.endswith("_back_rim_depth_in_arm"):
            s["back_rim_depth_in_arm"] = vv["min"]
    if vid in MG:
        s["printed_hub_part_vs_M2b_static_drive_min"] = min(r[2] for r in MG[vid])
    if vid in ("K2", "K3", "K3v"):
        sh = v["dx"] - K.DX0
        s["cover_visible_mm"] = {n: round(K.COVER["x_end"] + sh - c["D_look"][n]["torso_rim_x"], 2) for n in c["D_look"]}
    s["robot_width_over_arms"] = round(144.42 + 2 * (v["dx"] - K.DX0), 2)
    s["meshes"] = {kk.split("/")[1]: vv for kk, vv in BL.items() if kk.startswith(vid + "/")}
    OUT[vid] = s
    print(vid, s["front_band"], s.get("cover_visible_mm"))
json.dump(OUT, open(os.path.join(HERE, "klb_summary.json"), "w"), indent=1, ensure_ascii=False)
print("written klb_summary.json")
