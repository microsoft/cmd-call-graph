# Core functionality of cmd-call-graph.

from __future__ import print_function

import argparse
import collections
import itertools
import io
import os
import sys

NO_LINE_NUMBER = -1

Command = collections.namedtuple("Command", ["command", "target"])

# Line of code. Not a namedtuple because we need mutability.
class CodeLine:
    def __init__(self, number, text, terminating=False, noop=False):
        self.number = number
        self.text = text
        self.terminating = terminating
        self.noop = noop
        self.commands = []
        self.commands_counter = collections.Counter()

    def AddCommand(self, command):
        self.commands.append(command)
        self.commands_counter[command.command] += 1

    def __repr__(self):
        return "[{0} (terminating: {1}, noop: {2})] {3}".format(self.number, self.terminating, self.noop, self.text)
    
    def __eq__(self, other):
        return other is not None and self.number == other.number and self.text == other.text and self.terminating == other.terminating

# Connection between two nodes.
# dst is the name of the target node, kind is the type of connection, line_number is the line where the call/goto happens.
Connection = collections.namedtuple("Connection", ["dst", "kind", "line_number"])

# Node in the call graph.
class Node:
    def __init__(self, name):
        self.name = name
        self.connections = set()
        self.line_number = NO_LINE_NUMBER
        self.original_name = name
        self.is_exit_node = False
        self.code = []
        self.loc = 0

    def AddConnection(self, dst, kind, line_number=NO_LINE_NUMBER):
        self.connections.add(Connection(dst, kind, line_number))
    
    def AddCodeLine(self, line_number, code):
        self.code.append(CodeLine(line_number, code.strip().lower(), False))
        self.loc += 1
    
    def GetCommandCount(self):
        node_counter = collections.Counter()

        for line in self.code:
            for command, count in line.commands_counter.items():
                node_counter[command] += count
        
        return node_counter
    
    def __repr__(self):
        return "{0}. {1}, {2}".format(self.name, self.code, self.connections)

    def __lt__(self, other):
        if other == None:
            return False
        return self.name < other.name

class CallGraph:
    def __init__(self, log_file=sys.stderr):
        self.nodes = {}
        self.log_file = log_file
    
    def GetOrCreateNode(self, name):
        if name in self.nodes:
            return self.nodes[name]
        
        node = Node(name)
        self.nodes[name] = node
        return node

    # Adds to each node information depending on the contents of the code, such as connections
    # deriving from goto/call commands and whether the node is terminating or not.
    def _AnnotateNode(self, node):
        print(u"Annotating node {0} (line {1})".format(node.original_name, node.line_number), file=self.log_file)
        for i in range(len(node.code)):
            line = node.code[i]
            line_number = line.number
            text = line.text

            # Tokenize the line of code, and store all elements that warrant augmenting the
            # node in a list (interesting_commands), which will then be processed later.
            tokens = text.strip().lower().split()
            if not tokens:
                line.noop = True
                continue

            for i, token in enumerate(tokens):
                # Comment; stop processing the rest of the line.
                if token.startswith("::") or token == "rem" or token.startswith("@::") or token == "@rem":
                    line.noop = True
                    break

                if token == "goto" or token == "@goto":
                    block_name = tokens[i+1][1:]
                    if not block_name:
                        continue
                    line.AddCommand(Command("goto", block_name))
                    continue

                if token == "call" or token == "@call":
                    target = tokens[i+1]
                    if target[0] != ":":
                        line.AddCommand(Command("external_call", target))
                        continue
                    block_name = target[1:]
                    if not block_name:
                        continue
                    line.AddCommand(Command("call", block_name))
                    continue
                
                if token == "exit" or token == "@exit":
                    target = ""
                    if i+1 < len(tokens):
                        target = tokens[i+1]
                    line.AddCommand(Command("exit", target))
            
            for command, target in line.commands:
                if command == "call" or command == "goto":
                    node.AddConnection(target, command, line_number)
                    print(u"Line {} has a goto towards: <{}>. Current block: {}".format(line_number, target, node.name), file=self.log_file)
                
                if (command == "goto" and target == "eof") or command == "exit":
                    line.terminating = True

                if command == "exit" and target == "":
                    line.terminating = True
                    node.is_exit_node = True
    
    @staticmethod
    def _Escape(input_string):
        return input_string.replace("%", r"\%")

    def PrintDot(self, out_file=sys.stdout, log_file=sys.stderr, show_all_calls=True, show_node_stats=False, nodes_to_hide=None):
        kind_colors = {
            "goto": "red3",
            "nested": "blue3",
            "call": "green3",
        }
        # Output the DOT code.
        print(u"digraph g {", file=out_file)

        for node in sorted(self.nodes.values()):
            if nodes_to_hide and (node.name in nodes_to_hide):
                print(u"Skipping node {0}".format(node.name), file=log_file)
                continue

            name = node.name
            pretty_name = name
            if node.original_name != "":
                pretty_name = node.original_name
            
            print(u"Processing node {0} (using name: {1})".format(node.name, pretty_name), file=log_file)

            attributes = []
            label_lines = ["<b>{}</b>".format(pretty_name)]

            if node.line_number > 0:
                label_lines.append("(line {})".format(node.line_number))

            if show_node_stats:
                label_lines.append("<sub>[{} LOC]</sub>".format(node.loc))
                command_count = node.GetCommandCount()
                external_call_count = command_count["external_call"]

                if external_call_count > 0:
                    text = "call" if external_call_count == 1 else "calls"
                    label_lines.append("<sub>[{} external {}]</sub>".format(external_call_count, text))
               
            attributes.append("label=<{}>".format("<br/>".join(label_lines)))

            if node.is_exit_node:
                attributes.append("color=red")
                attributes.append("penwidth=2")
            if attributes:
                print(u"\"{}\" [{}]".format(name, ",".join(attributes)), file=out_file)

            # De-duplicate connections by line number if show_all_calls is set to False.
            connections = node.connections
            if not show_all_calls:
                connections = list(set(Connection(c.dst, c.kind, NO_LINE_NUMBER) for c in connections))
            
            for c in sorted(connections):
                # Remove EOF connections if necessary.
                if nodes_to_hide and (c.dst in nodes_to_hide):
                    print(u"Skipping connection to node {0}".format(c.dst), file=log_file)
                    continue
                label = c.kind
                if c.line_number != NO_LINE_NUMBER:
                    label = "<<b>{}</b><br />(line {})>".format(c.kind, c.line_number)
                src_escaped_name = self._Escape(name)
                dst_escaped_name = self._Escape(c.dst)
                print(u"\"{}\" -> \"{}\" [label={},color={}]".format(src_escaped_name, dst_escaped_name, label, kind_colors[c.kind]), file=out_file)

        print(u"}", file=out_file)

    @staticmethod
    def Build(input_file, log_file=sys.stderr):
        call_graph = CallGraph._ParseSource(input_file, log_file)
        for node in call_graph.nodes.values():
            call_graph._AnnotateNode(node)
        
        # Find exit nodes.
        last_node = max(call_graph.nodes.values(), key=lambda x: x.line_number)
        print(u"{0} is the last node, marking it as exit node.".format(last_node.name), file=log_file)
        last_node.is_exit_node = True

        # If the last node's last statement is a goto not going towards eof, then
        # it's not an exit node.
        for line in reversed(last_node.code):
            if line.noop:
                continue

            for command, target in line.commands:
                if command == "goto" and target and target != "eof":
                    last_node.is_exit_node = False
                    break

        # Prune away EOF if it is a virtual node (no line number) and there are no connections to it.
        eof = call_graph.GetOrCreateNode("eof")
        if eof.line_number == NO_LINE_NUMBER:
            all_connections = itertools.chain.from_iterable(n.connections for n in call_graph.nodes.values())
            destinations = set(c.dst for c in all_connections)
            if "eof" not in destinations:
                print(u"Removing the eof node, since there are no connections to it and it's not a real node", file=log_file)
                del call_graph.nodes["eof"]

        # Find and mark the "nested" connections.
        nodes = [n for n in call_graph.nodes.values() if n.line_number != NO_LINE_NUMBER]
        nodes_by_line_number = sorted(nodes, key=lambda x: x.line_number)
        for i in range(1, len(nodes_by_line_number)):
            cur_node = nodes_by_line_number[i]
            prev_node = nodes_by_line_number[i-1]

            # Special case: the previous node has no code or all lines are comments / empty lines.
            all_noop = all(line.noop for line in prev_node.code)
            if not prev_node.code or all_noop:
                print(u"Adding nested connection between {0} and {1} because all_noop ({2}) or empty code ({3})".format(
                    prev_node.name, cur_node.name, all_noop, not prev_node.code), file=log_file)
                prev_node.AddConnection(cur_node.name, "nested")
                break

            # Heuristic for "nested" connections:
            # iterate the previous node's commands, and create a nested connection
            # only if the command that logically precedes the current node does not
            # contain a goto or an exit (which would mean that the current node is not reached
            # by "flowing" from the previous node to the current node.)
            for line in reversed(prev_node.code):
                # Skip comments and empty lines.
                if line.noop:
                    continue
                
                commands = set(c.command for c in line.commands)
                if "exit" not in commands and "goto" not in commands:
                    print(u"Adding nested connection between {0} and {1} because there is a non-exit or non-goto command.".format(
                        prev_node.name, cur_node.name), file=log_file)
                    prev_node.AddConnection(cur_node.name, "nested")

                break

        return call_graph

    # Creates a call graph from an input file, parsing the file in blocks and creating
    # one node for each block. Note that the nodes don't contain any information that
    # depend on the contents of the node, as this is just the starting point for the
    # processing.
    @staticmethod
    def _ParseSource(input_file, log_file=sys.stderr):
        call_graph = CallGraph(log_file)
        # Special node to signal the start of the script.
        cur_node = call_graph.GetOrCreateNode("__begin__")
        cur_node.line_number = 1

        # Special node used by cmd to signal the end of the script.
        eof = call_graph.GetOrCreateNode("eof")
        eof.is_exit_node = True

        for line_number, line in enumerate(input_file, 1):
            line = line.strip()

            # Start of new block.
            if line.startswith(":") and not line.startswith("::"):
                # In the off chance that there are multiple words, cmd considers the first word the label name.
                original_block_name = line[1:].split()[0].strip()

                # Since cmd is case-insensitive, let's convert block names to lowercase.
                block_name = original_block_name.lower()

                print(u"Line {} defines a new block: <{}>".format(line_number, block_name), file=log_file)
                if block_name:
                    next_node = call_graph.GetOrCreateNode(block_name)
                    next_node.line_number = line_number
                    next_node.original_name = original_block_name

                    # If this node is defined on line one, remove __begin__, so we avoid having two
                    # nodes with the same line number.
                    if line_number == 1:
                        del call_graph.nodes["__begin__"]

                    cur_node = next_node
            
            cur_node.AddCodeLine(line_number, line)

        return call_graph


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

    try:
        call_graph = CallGraph.Build(input_file, log_file=log_file)
        call_graph.PrintDot(output_file, log_file=log_file,
                            show_all_calls=args.allcalls, show_node_stats=args.nodestats, nodes_to_hide=nodes_to_hide)
    except Exception as e:
        print(u"Error processing the call graph: {}".format(e))

    finally:
        if args.input:
            input_file.close()
        if args.output:
            output_file.close()
        if args.logfile:
            log_file.close()
