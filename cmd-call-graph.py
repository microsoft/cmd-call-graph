# cmd-call-graph.py
#
# Outputs a call graph for the given CMD / batch file in DOT (https://en.wikipedia.org/wiki/DOT_(graph_description_language)).

import argparse
import sys

from callgraph import callgraph
    
if  __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--show-all-calls", type=bool,
                        help="Set to true to show all calls in the graph.", default=False,
                        dest="allcalls")
    args = parser.parse_args()

    call_graph = callgraph.BuildCallGraph(sys.stdin, args.allcalls)
    call_graph.PrintDot()
