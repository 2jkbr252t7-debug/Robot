#!/bin/bash
cd /tmp/claude-0/gapwf/fin/T1/k2
P=/opt/venv/cad/bin/python
$P gen_layout.py > /dev/null
$P check_static.py > static.log 2>&1
$P fix_checks.py > fix_checks.log 2>&1
$P envelope.py > envelope.log 2>&1
$P cog.py > cog.log 2>&1
echo CHAIN5_DONE >> cog.log
