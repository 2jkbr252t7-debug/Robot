#!/bin/bash
cd /tmp/claude-0/gapwf/fin/R2c/B2_max_tlac
/opt/venv/cad/bin/python colroom.py L > colroom_L.log 2>&1
/opt/venv/cad/bin/python colroom.py R > colroom_R.log 2>&1
for s in L R; do
  /opt/venv/cad/bin/python paths.py B2 $s > paths_B2_$s.log 2>&1
  /opt/venv/cad/bin/python chk.py B2col $s > chk_B2col_$s.log 2>&1
  /opt/venv/cad/bin/python paths.py B2col $s > paths_B2col_$s.log 2>&1
done
echo ALLDONE > run2.done
