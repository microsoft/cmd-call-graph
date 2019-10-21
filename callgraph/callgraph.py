# Core functionality of cmd-call-graph.

from __future__ import print_function

import argparse
import io
import os
import sys

from . import core
from . import render

DEFAULT_MIN_NODE_SIZE = 3
DEFAULT_MAX_NODE_SIZE = 7
DEFAULT_FONT_SCALE_FACTOR = 7

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--show-all-calls",
                        help="Set to show all calls in the graph.",
                        dest="allcalls", action="store_true")
    parser.add_argument("--show-node-stats",
                        help="Set to show statistics about the nodes in the graph.",
                        dest="nodestats", action="store_true")
    parser.add_argument("--nodes-to-hide", type=str, nargs="+", dest="nodestohide",
                        help="List of space-separated nodes to hide.")
    parser.add_argument("-v", "--verbose", action="store_true", dest="verbose",
                        help="Output extra information about what the program does.")
    parser.add_argument("-i", "--input", help="Input file. If it's not set, stdin is used.",
                        type=str)
    parser.add_argument("-o", "--output", help="Output file. If it's not set, stdout is used.",
                        type=str)
    parser.add_argument("-l", "--log-file", help="Log file. If it's not set, stderr is used.",
                        type=str, dest="logfile")
    parser.add_argument("--represent-node-size",
                        help="Nodes' size will be proportional to the number of lines they contain.",
                        action="store_true", dest="nodesize")
    parser.add_argument("--min-node-size", help="Set minimum rendered node size.", 
                        dest="min_node_size", action="store", type=int, default=None)
    parser.add_argument("--max-node-size", help="Set maximum rendered node size.", 
                        dest="max_node_size", action="store", type=int, default=None)

    args = parser.parse_args()

    nodes_to_hide = None
    if args.nodestohide:
        nodes_to_hide = set(x.lower() for x in args.nodestohide)

    log_file = sys.stderr
    if args.logfile:
        try:
            log_file = open(args.logfile, 'w')
        except IOError as e:
            print(u"Error opening {}: {}".format(args.logfile, e), file=sys.stderr)
            sys.exit(1)

    if not args.verbose:
        log_file = io.StringIO()  # will just be ignored

    input_file = sys.stdin
    if args.input:
        try:
            input_file = open(args.input, 'r')
        except IOError as e:
            print(u"Error opening {}: {}".format(args.input, e), file=sys.stderr)
            sys.exit(1)

    output_file = sys.stdout
    if args.output:
        try:
            output_file = open(args.output, 'w')
        except IOError as e:
            print(u"Error opening {}: {}".format(args.output, e), file=sys.stderr)
            sys.exit(1)

    if args.min_node_size == None:
        args.min_node_size = DEFAULT_MIN_NODE_SIZE

    if args.max_node_size == None:
        args.max_node_size = DEFAULT_MAX_NODE_SIZE

    if args.min_node_size > args.max_node_size:
        print("Minimum node size should be less than maximum node size")
        sys.exit(1)

    try:
        call_graph = core.CallGraph.Build(input_file, log_file=log_file)
        render.PrintDot(call_graph, out_file=output_file, log_file=log_file, show_all_calls=args.allcalls,          
                        show_node_stats=args.nodestats, nodes_to_hide=nodes_to_hide, represent_node_size=args.nodesize, 
                        min_node_size=args.min_node_size, max_node_size=args.max_node_size, 
                        font_scale_factor=DEFAULT_FONT_SCALE_FACTOR)
    except Exception as e:
        print(u"Error processing the call graph: {}".format(e))

    finally:
        if args.input:
            input_file.close()
        if args.output:
            output_file.close()
        if args.logfile:
            log_file.close()
