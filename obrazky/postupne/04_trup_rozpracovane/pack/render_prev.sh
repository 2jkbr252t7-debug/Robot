#!/bin/bash
# previews <= 600 px, <= 16 spp (shared CPU)
cd /tmp/claude-0/gapwf/fin/T1/pack
BL=/opt/venv/bl/bin/python
PV=/tmp/claude-0/gapwf/fin/T1/t1_preview.py
ALL=$(cat judge/cutnames.txt)
for k in rest awake; do
  $BL $PV --dir exp_$k --out prev_$k --real-head --res 500 --samples 12 --views iso,front,side,cut --cut-names T_shell,Z_shell,A_R_ruka
  $BL $PV --dir exp_$k --out prev_${k}_rez --real-head --res 600 --samples 12 --views cut_side --cut-names $ALL --cut-axis x --cut-keep neg
  $BL $PV --dir exp_$k --out prev_${k}_rezY --real-head --res 600 --samples 12 --views cut_front --cut-names $ALL --cut-axis y --cut-keep pos
done
$BL $PV --dir exp_base_plan --out prev_base_plan --res 500 --samples 12 --views top,iso
$BL $PV --dir exp_torso_plan --out prev_torso_plan --res 500 --samples 12 --views top,iso
echo RENDER_DONE
