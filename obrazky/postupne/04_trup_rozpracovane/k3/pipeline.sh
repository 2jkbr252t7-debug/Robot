#!/bin/bash
cd /tmp/claude-0/gapwf/fin/T1/k3
PY=/opt/venv/cad/bin/python
$PY check_static.py > static.log 2>&1
$PY sweep_std.py std sweep_std.json > sweep_std.log 2>&1 &
$PY check.py extra > extra.log 2>&1 &
wait
$PY check.py gaps > gaps.log 2>&1 &
$PY envelope.py > envelope.log 2>&1 &
$PY check.py cog > cog.log 2>&1
$PY head_real.py > head_real.log 2>&1
wait
$PY merge_check.py > merge.log 2>&1
rm -rf exp_rest exp_awake exp_rest_noarms exp_awake_noarms exp_base_plan exp_torso_plan
./render_all.sh > render.log 2>&1
echo PIPELINE_DONE >> merge.log
