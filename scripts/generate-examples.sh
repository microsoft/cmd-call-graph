#!/bin/bash

# Ugly way to get any python interpreter. This is necessary because the script will run
# both with Python 2.7 and Python 3.x under Travis.
PYTHONS=$(which python3 python2.7 python)
PYTHON=$(echo $PYTHONS | cut -d" " -f1)

if [ -z "${PYTHON}" ]; then
    echo "ERROR: no Python interpreter found."
    exit 1
fi
echo "Using Python interpreter ${PYTHON}"

# Return an error if any of the following commands fails.
set -e
echo "example1.cmd, --show-all-calls"
${PYTHON} cmd-call-graph.py --show-all-calls < examples/example1.cmd > examples/example1.dot
echo
echo "example1.cmd, --show-all-calls --show-node-stats"
${PYTHON} cmd-call-graph.py --show-all-calls --show-node-stats < examples/example1.cmd > examples/example1-nodestats.dot
echo
echo "example1.cmd, without --show-all-calls"
${PYTHON} cmd-call-graph.py < examples/example1.cmd > examples/example1-noshowall.dot
echo
echo "loc.cmd, with --show-node-status and without --show-all-calls"
${PYTHON} cmd-call-graph.py --show-node-stats < examples/loc.cmd > examples/loc.dot

dot -Tpng examples/example1.dot > examples/example1.png
dot -Tpng examples/example1-nodestats.dot > examples/example1-nodestats.png
dot -Tpng examples/example1-noshowall.dot > examples/example1-noshowall.png
dot -Tpng examples/loc.dot > examples/loc.png
