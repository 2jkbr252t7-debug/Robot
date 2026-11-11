#!/bin/bash
cd /tmp/claude-0/gapwf/fin/T1/k2
P=/opt/venv/cad/bin/python
$P gen_layout.py > /dev/null
$P check_static.py > static.log 2>&1
$P run_sweep.py extra > sweep_extra.log 2>&1
$P run_gaps.py > gaps.log 2>&1
$P arm_limits.py > arm_limits.log 2>&1
$P envelope.py > envelope.log 2>&1
$P run_sweep.py std > sweep_std.log 2>&1
echo CHAIN_DONE >> envelope.log
