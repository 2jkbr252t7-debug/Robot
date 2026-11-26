#!/bin/bash
cd /tmp/claude-0/gapwf/fin/R2c/vyber
while [ ! -f run_chk.done ]; do sleep 5; done
cd B2c
/opt/venv/cad/bin/python colroom_b1merge.py L > J_colroom_b1merge_L.log 2>&1
/opt/venv/cad/bin/python colroom_b1merge.py R > J_colroom_b1merge_R.log 2>&1
cd ..
/opt/venv/cad/bin/python armgap_top.py rec1 -1.0 > armgap_top.log 2>&1
echo done > run2.done
