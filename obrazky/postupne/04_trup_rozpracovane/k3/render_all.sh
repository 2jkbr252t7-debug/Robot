#!/bin/bash
cd /tmp/claude-0/gapwf/fin/T1/k3
/opt/venv/cad/bin/python export_prev.py rest awake
/opt/venv/cad/bin/python filter_export.py exp_rest exp_rest_noarms noarms
/opt/venv/cad/bin/python filter_export.py exp_awake exp_awake_noarms noarms
/opt/venv/cad/bin/python filter_export.py exp_rest exp_base_plan baseplan
/opt/venv/cad/bin/python filter_export.py exp_rest exp_torso_plan torsoplan
PV="/opt/venv/bl/bin/python ../t1_preview.py --real-head --res 600 --samples 16"
$PV --dir exp_rest --out prev_rest --views iso,front,side,cut --cut-names T_shell,Z_shell
$PV --dir exp_awake --out prev_awake --views iso,front,side,cut --cut-names T_shell,Z_shell
$PV --dir exp_rest_noarms --out prev_rest_noarms --views cut_side,cut_front --cut-names T_shell,Z_shell,Z_paluba,T_paluba
/opt/venv/bl/bin/python ../t1_preview.py --dir exp_base_plan --out prev_base_plan --res 600 --samples 16 --views top,iso
/opt/venv/bl/bin/python ../t1_preview.py --dir exp_torso_plan --out prev_torso_plan --res 600 --samples 16 --views top,iso
echo RENDER_ALL_DONE
