#!/bin/bash
cd /tmp/claude-0/gapwf/fin/R2c/B2_max_tlac
for v in B2 B2col; do for s in L R; do
  /opt/venv/cad/bin/python paths.py $v $s > paths_${v}_$s.log 2>&1
done; done
echo ALLDONE > run3.done
