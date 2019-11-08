#!/bin/bash
set -e

echo "example1.cmd, shows all calls"
python cmd-call-graph.py --hide-node-stats examples/example1.cmd > examples/example1.dot
echo
echo "example1.cmd, shows all calls and the node stats"
python cmd-call-graph.py examples/example1.cmd > examples/example1-nodestats.dot
echo
echo "example1.cmd, simplify calls and no node stats"
python cmd-call-graph.py --simplify-calls --hide-node-stats examples/example1.cmd > examples/example1-noshowall.dot
echo
echo "loc.cmd, with simplified calls and node stats"
python cmd-call-graph.py --simplify-calls examples/loc.cmd > examples/loc.dot

dot -Tpng examples/example1.dot > examples/example1.png
dot -Tpng examples/example1-nodestats.dot > examples/example1-nodestats.png
dot -Tpng examples/example1-noshowall.dot > examples/example1-noshowall.png
dot -Tpng examples/loc.dot > examples/loc.png
