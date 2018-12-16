#!/bin/bash

echo "example1.cmd, --show-all-calls"
python3 cmd-call-graph.py --show-all-calls < examples/example1.cmd > examples/example1.dot
echo
echo "example1.cmd, without --show-all-calls"
python3 cmd-call-graph.py < examples/example1.cmd > examples/example1-noshowall.dot
echo
echo "loc.cmd, with --show-node-status and without --show-all-calls"
python3 cmd-call-graph.py --show-node-stats < examples/loc.cmd > examples/loc.dot

dot -Tpng examples/example1.dot > examples/example1.png
dot -Tpng examples/example1-noshowall.dot > examples/example1-noshowall.png
dot -Tpng examples/loc.dot > examples/loc.png
