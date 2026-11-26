#!/bin/bash
# usage: run_rez.sh OUT PPM SAMPLES
cd /tmp/claude-0/gapwf/fin/R3/img/work
for a in "0 M1" "A M2b" "B M2b" "C M2b"; do set -- $a
  for pl in v h; do
    /opt/venv/bl/bin/python -B scene_v3.py -- --shot rezv --vids $1 --opt $2 --plane $pl --ppm $PPM --samples $SAMP --exposure ${EXPO:--0.2} --out $OUT 2>&1 | grep -E "SHOT|FAST|rror|failed"
  done
done
