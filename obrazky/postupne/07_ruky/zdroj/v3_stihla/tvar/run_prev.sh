#!/bin/bash
# usage: run_prev.sh OUTDIR VIDS SHOTS...
cd /tmp/claude-0/gapwf/fin/R3/tvar
OUT=$1; VIDS=$2; shift 2
for sh in "$@"; do
  /opt/venv/bl/bin/python -B scene_tvar.py -- --shot $sh --res ${RES:-420} --samples ${SAMP:-12} --vids $VIDS --out $OUT 2>&1 | grep -E "SHOT|rror|failed"
done
