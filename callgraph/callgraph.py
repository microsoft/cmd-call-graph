# Core functionality of cmd-call-graph.

from __future__ import print_function

import argparse
import collections
import itertools
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

    def __repr__(self):
        return "[{0} (terminating: {1}, noop: {2})] {3}".format(self.number, self.terminating, self.noop, self.text)
    
    def __eq__(self, other):
        return other is not None and self.number == other.number and self.text == other.text and self.terminating == other.terminating

# Connection between two nodes.
Connection = collections.namedtuple("Connection", ["dst", "kind", "line_number"])

# Node in the call graph.
class Node:
    def __init__(self, name):
        self.name = name
        self.connections = set()
        self.line_number = NO_LINE_NUMBER
        self.original_name = ""
        self.is_exit_node = False
        self.code = []

    def AddConnection(self, dst, kind, line_number=NO_LINE_NUMBER):
        self.connections.add(Connection(dst, kind, line_number))
    
    def AddCodeLine(self, line_number, code):
        self.code.append(CodeLine(line_number, code.strip().lower(), False))

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
                if token == "::" or token == "rem":
                    line.noop = True
                    break

                if token == "goto" or token == "@goto":
                    block_name = tokens[i+1][1:]
                    if not block_name:
                        continue
                    line.commands.append(Command("goto", block_name))
                    continue

                if token == "call" or token == "@call":
                    target = tokens[i+1]
                    if target[0] != ":":
                        # Calling an external command. Not represented in the call graph by design.
                        continue
                    block_name = target[1:]
                    if not block_name:
                        continue
                    line.commands.append(Command("call", block_name))
                    continue
                
                if token == "exit" or token == "@exit":
                    target = ""
                    if i+1 < len(tokens):
                        target = tokens[i+1]
                    line.commands.append(Command("exit", target))
            
            for command, target in line.commands:
                if command == "call" or command == "goto":
                    target_node = self.nodes[target]
                    node.AddConnection(target_node, command, line_number)
                    print(u"Line {} has a goto towards: <{}>. Current block: {}".format(line_number, target, node.name), file=self.log_file)
                
                if (command == "goto" and target == "eof") or command == "exit":
                    line.terminating = True

                if command == "exit" and target == "":
                    line.terminating = True
                    node.is_exit_node = True

    def PrintDot(self, out_file=sys.stdout, show_all_calls=True, show_node_stats=False):
        kind_colors = {
            "goto": "red3",
            "nested": "blue3",
            "call": "green3",
        }
        # Output the DOT code.
        print(u"digraph g {", file=out_file)

        for node in sorted(self.nodes.values()):
            name = node.name
            pretty_name = name
            if node.original_name != "":
                pretty_name = node.original_name

            attributes = []
            label_lines = ["<b>{}</b>".format(pretty_name)]

            if node.line_number > 0:
                label_lines.append("(line {})".format(node.line_number))

            if show_node_stats:
                label_lines.append("<sub>[{} LOC]</sub>".format(len(node.code)))
               
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
                label = c.kind
                if c.line_number != NO_LINE_NUMBER:
                    label = "<<b>{}</b><br />(line {})>".format(c.kind, c.line_number)
                print(u"\"{}\" -> \"{}\" [label={},color={}]".format(name, c.dst.name, label, kind_colors[c.kind]), file=out_file)

        print(u"}", file=out_file)

    @staticmethod
    def Build(input_file, log_file=sys.stderr):
        call_graph = CallGraph._ParseSource(input_file, log_file)
        for node in call_graph.nodes.values():
            call_graph._AnnotateNode(node)
        
        # Find exit nodes.
        last_node = max(call_graph.nodes.values(), key=lambda x: x.line_number)
        print("{0} is the last node, therefore it's an exit node.".format(last_node.name), file=log_file)
        last_node.is_exit_node = True

        # Prune away EOF if it is a virtual node (no line number) and there are no connections to it.
        eof = call_graph.GetOrCreateNode("eof")
        if eof.line_number == NO_LINE_NUMBER:
            all_connections = itertools.chain.from_iterable(n.connections for n in call_graph.nodes.values())
            destinations = set(c.dst.name for c in all_connections)
            if "eof" not in destinations:
                print("Removing the eof node, since there are no connections to it and it's not a real node", file=log_file)
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
                print("Adding nested connection between {0} and {1} because all_noop ({2}) or empty code ({3})".format(
                    prev_node.name, cur_node.name, all_noop, not prev_node.code), file=log_file)
                prev_node.AddConnection(cur_node, "nested")
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
                    print("Adding nested connection between {0} and {1} because there is a non-exit or non-goto command.".format(
                        prev_node.name, cur_node.name), file=log_file)
                    prev_node.AddConnection(cur_node, "nested")

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
    parser.add_argument("--show-all-calls", type=bool,
                        help="Set to true to show all calls in the graph.", default=False,
                        dest="allcalls")
    parser.add_argument("--show-node-stats", type=bool,
                        help="Set to true to show statistics about the nodes in the graph.",
                        default=False, dest="nodestats")
    args = parser.parse_args()

    call_graph = CallGraph.Build(sys.stdin)
    call_graph.PrintDot(sys.stdout, args.allcalls, args.nodestats)