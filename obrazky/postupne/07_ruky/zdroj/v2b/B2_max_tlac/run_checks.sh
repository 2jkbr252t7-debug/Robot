#!/bin/bash
cd /tmp/claude-0/gapwf/fin/R2c/B2_max_tlac
for s in L R; do
  /opt/venv/cad/bin/python chk.py B2 $s > chk_B2_$s.log 2>&1
  /opt/venv/cad/bin/python paths.py B2 $s > paths_B2_$s.log 2>&1
done
/opt/venv/cad/bin/python chk.py B2lift L > chk_B2lift_L.log 2>&1
echo ALLDONE >> chk_B2_R.log
