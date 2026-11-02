"""Context render for the head-shell review: the shell + placeholder neighbours (ball neck, front frame with
display glass, ears) so the user sees the finished look.  Neighbours are PLACEHOLDERS (later parts)."""
import json, os, subprocess, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from build123d import Cylinder, Pos, Solid, import_step, fillet, Axis  # noqa: E402
from nova.cad.common import PartRec, export_parts  # noqa: E402
from nova_mini import hlava_skrupina as HS  # noqa: E402

V = sys.argv[1] if len(sys.argv) > 1 else "navrh3"
D = os.path.join(ROOT, "obrazky", "postupne", "01_hlava_skrupina")
B = f"/tmp/claude-0/ctx_{V}"


def build():
    shell = import_step(os.path.join(D, f"NOVA_mini_01_hlava_skrupina_{V}.step"))
    from nova_mini import krk as KR
    neck, ball, _c = KR.build()
    collar = Pos(0, 0, KR.NECK_Z0 - 1.8) * Cylinder(22, 3.6)
    collar = fillet(collar.edges().group_by(Axis.Z)[-1], 1.2)
    parts = [PartRec("HS", "Škrupina hlavy", shell, "white", "head", "J3"),
             PartRec("NB", "Guľa krku", ball, "black_gloss", "neck", "J2"),
             PartRec("NC", "Krk", neck, "black", "neck", "J2"),
             PartRec("NK", "Golier", collar, "black", "neck", "J1")]
    export_parts(parts, "ctx", step=False, out_dir=B)


def render(out, views, pose=None, res=(800, 700), samples=40):
    job = dict(out=out, glb_dir=B, manifest_dir=f"{B}/manifest", internal=False, res=list(res), samples=samples,
               extra=[{"manifest_dir": f"{ROOT}/build_v8/manifest", "glb_dir": f"{ROOT}/build_v8"}],
               parts=["HS", "NB", "NC", "NK", "H03", "H04", "H04E", "H05-R", "H05-L", "H06-R", "H06-L"],
               xforms=[{"ids": ["H03", "H04", "H04E", "H05-R", "H05-L", "H06-R", "H06-L"], "move": [0, 0, -117.0]}],
               joint_axes={"J3": [[1, 0, 0], [0, HS.TILT_Y, HS.TILT_Z]], "J2": [[0, 0, 1], [0, 0, 0]]},
               views=views, shadow=False, exposure=-1.7, margin=0.1)
    if pose:
        job["pose"] = pose
    r = subprocess.run(["/opt/venv/bl/bin/python", f"{ROOT}/nova/render/render.py", "--job", json.dumps(job)],
                       capture_output=True, text=True)
    if r.returncode:
        print(r.stdout[-1500:], r.stderr[-1500:])
    return out


if __name__ == "__main__":
    build()
    print("built", B)
