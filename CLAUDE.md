# NOVA robot – CAD + render pipeline

Goal: a consistent, buildable design of the desktop robot "NOVA" delivered as images (multi-view sheets,
exploded views, sections, dimensioned drawings) plus STEP/STL exports. User language: Slovak (texts on
images in Slovak with diacritics).

## Source of truth
* `nova/spec.py` – every shared dimension (mm), coordinate system, materials, joints. Read it first.
  Coordinate system: mm, Z up, origin on the floor at the centre of the base; robot FRONT = −Y;
  robot RIGHT = −X (shown on the left in a front view).
* `docs/SPEC.md` – design intent, part numbers, electronics BOM.
* `referencie/` – the user's images. `R01_celok_zadanie.png` is THE target look. R02–R11 are AI concept
  sheets (inspiration, internally inconsistent). R12 = previous attempt.

## Environments (already installed)
* CAD: `/opt/venv/cad/bin/python` (build123d 0.13, OCP, Pillow, cairosvg)
* Render: `/opt/venv/bl/bin/python` (bpy 5.2 = Blender as a module, Cycles CPU only; EEVEE does NOT work)

## Pipeline
1. CAD modules `nova/cad/<sub>.py` (sub = base, torso, neck, head, arms, internals). Each defines
   `build() -> list[PartRec]` (see `nova/cad/common.py`) with every part already in ASSEMBLY position,
   and ends with `if __name__ == "__main__": run_module(build, "<sub>")`.
   Run from the repo root: `/opt/venv/cad/bin/python -m nova.cad.<sub>` → writes `build/stl/<ID>.stl`,
   `build/step/<ID>.step`, `build/manifest/<sub>.json` (build/ is git-ignored).
2. Render: `/opt/venv/bl/bin/python nova/render/render.py --job '<json>'` (job keys documented at the top
   of render.py: parts/subs/exclude/internal/views/res/samples/pose/explode/section/xray…). Output: one PNG
   per view (transparent background) + views.json (camera data for overlays).
3. Sheets: `nova/render/sheet.py` (`six_view_sheet`, `matrix_sheet`, `project`, `bg_composite`).

## Modeling rules (build123d / OCC)
* Robust recipe for rounded shells: `extrude` or `Box` → `fillet` edges (biggest radii first) →
  `offset(solid, amount=-wall, openings=[faces])` for the shell → THEN boolean cuts/holes.
  Fillet before booleans; fillets after complex booleans often fail.
  ⚠ `offset(..., openings=face)` silently returns the UNCHANGED solid when the opening face borders a
  fillet – always check the volume. Fallback: `body - offset(body, amount=-wall)` then cut the opening
  with a box/slab.
* Torso: `superellipse_wire(a, b, n, z)` → `Face` → `extrude` → fillet top/bottom loops (tested, works).
* Lofts: use many evenly spaced sections (≤4 mm apart) or the B-spline overshoots (wavy surfaces).
* Splitting a shell into parts: intersect (`&`) / subtract (`-`) with boxes or extruded sketches; create the
  0.6 mm seam by subtracting a thin slab/offset band from one side.
* Check `shape.is_valid` and print bounding boxes; compare with spec numbers.
* Every part must be a valid solid, sit exactly at its spec position, and not overlap neighbours.
* Do NOT edit `nova/spec.py` from a parallel sub-task; use local constants and report deviations.
* Joint tags: base parts "" ; torso parts + N01 + A05 "J1"; N02/N06 "J2"; N07 + all head parts "J3";
  right arm (A01–A04 "-R") "J4"; left arm ("-L") "J5". Internal parts: `internal=True` (same joint tags).

## Rendering tips
* 4 CPU cores shared – previews ≤ 700 px and ≤ 24 samples; finals 1200–1800 px, 64–128 samples.
* Ortho views use camera-relative lighting (consistent between views); perspective views use a fixed rig.
* Exposure default −1.5 (white plastic must not clip; check that shading is visible).
