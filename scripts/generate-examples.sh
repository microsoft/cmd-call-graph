#!/bin/bash


python3 cmd-call-graph.py --show-all-calls=True < examples/example1.cmd > examples/example1.dot
python3 cmd-call-graph.py < examples/example1.cmd > examples/example1-noshowall.dot

dot -Tpng examples/example1.dot > examples/example1.png
dot -Tpng examples/example1-noshowall.dot > examples/example1-noshowall.png
