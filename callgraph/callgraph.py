# Core functionality of cmd-call-graph.

from __future__ import print_function

import argparse
import collections
import sys

Connection = collections.namedtuple("Connection", ["dst", "kind", "line_number"])

NO_LINE_NUMBER = -1

class Node:
    def __init__(self, name):
        self.name = name
        self.connections = set()
        self.line_number = NO_LINE_NUMBER
        self.original_name = ""
        self.is_exit_node = False

    def AddConnection(self, dst, kind, line_number):
        self.connections.add(Connection(dst, kind, line_number))

class CallGraph:
    def __init__(self):
        self.nodes = {}

    def GetNode(self, name):
        if name in self.nodes:
            return self.nodes[name]
        
        node = Node(name)
        self.nodes[name] = node
        return node

    def PrintDot(self, out_file=sys.stdout):
        kind_colors = {
            "goto": "red3",
            "nested": "blue3",
            "call": "green3",
        }
        # Output the DOT code.
        print("digraph g {", file=out_file)

        for node in self.nodes.values():
            name = node.name
            pretty_name = name
            if node.original_name != "":
                pretty_name = node.original_name

            attributes = []

            if node.line_number > 0:
                attributes.append("label=<<b>{}</b><br />(line {})>".format(pretty_name, node.line_number))
            if node.is_exit_node:
                attributes.append("color=red")
                attributes.append("penwidth=2")
            if attributes:
                print("{} [{}]".format(name, ",".join(attributes)), file=out_file)

            for c in node.connections:
                label = c.kind
                if c.line_number != NO_LINE_NUMBER:
                    label = "<<b>{}</b><br />(line {})>".format(c.kind, c.line_number)
                print("{} -> {} [label={},color={}]".format(name, c.dst.name, label, kind_colors[c.kind]), file=out_file)

        print("}", file=out_file)

def BuildCallGraph(input_file, all_calls, log_file=sys.stderr):
    call_graph = CallGraph()
    cur_node = call_graph.GetNode("__begin__")
    cur_node.line_number = 1

    # Set of line numbers that contain instructions that are potentially terminating.
    # Used to keep track of labels whose instructions "flow" into another label's
    # instructions. (Called "nested" connection)
    terminating_line_numbers = set()
    for line_number, orig_line in enumerate(input_file):
        # Keep the original line as well as the lowercase version to keep track of the original
        # name of labels (typically in some form of camelcase for readability).
        orig_line = orig_line.strip()
        line = orig_line.lower()

        # If all_calls is true, we want to keep connections unique by line number
        # (showing all of them), otherwise we don't want to consider the line number
        # when creating connections.
        line_number_to_store = line_number if all_calls else NO_LINE_NUMBER

        # Skip empty lines and comments.
        if not line or line.startswith("::") or line.startswith("rem"):
            # If line number N is terminating, and line N+1 is a statement or an empty space,
            # we need to consider line N+1 as terminating as well, since no real statements
            # are present between the terminating line number and the current one.
            if line_number-1 in terminating_line_numbers:
                terminating_line_numbers.add(line_number)
            continue

        if line.startswith(":"):
            # In the off chance that there are multiple words, cmd considers the first word the label name.
            block_name = line[1:].split()[0].strip()
            print("Line {} defines a new block: <{}>".format(line_number, block_name), file=log_file)
            if not block_name:
                continue

            next_node = call_graph.GetNode(block_name)
            next_node.line_number = line_number+1  # Correct starting at 0.
            next_node.original_name = orig_line[1:].split()[0].strip()
            if line_number-1 not in terminating_line_numbers:
                cur_node.AddConnection(next_node, "nested", line_number_to_store)

            cur_node = next_node
            continue
        
        tokens = line.split()

        interesting_commands = []

        for i, token in enumerate(tokens):
            if token == "::" or token == "rem":
                break

            if token == "goto" or token == "@goto":
                block_name = tokens[i+1][1:]
                if not block_name:
                    continue
                interesting_commands.append(("goto", block_name))
                continue

            if token == "call" or token == "@call":
                target = tokens[i+1]
                if target[0] != ":":
                    # Calling an external command. Not interesting.
                    continue
                block_name = target[1:]
                if not block_name:
                    continue
                interesting_commands.append(("call", block_name))
                continue
            
            if token == "exit" or token == "@exit":
                target = ""
                if i+1 < len(tokens):
                    target = tokens[i+1]
                interesting_commands.append(("exit", target))
        
        for command, target in interesting_commands:
            if command == "call" or command == "goto":
                next_node = call_graph.GetNode(target)
                cur_node.AddConnection(next_node, command, line_number_to_store)
                print("Line {} has a goto towards: <{}>. Current block: {}".format(line_number, target, cur_node.name), file=log_file)
            
            if (command == "goto" and target == "eof") or command == "exit":
                terminating_line_numbers.add(line_number)

            if command == "exit" and target == "":
                cur_node.is_exit_node = True

    # If we reached EOF, this means that the current node will cause the program to finish.
    cur_node.is_exit_node = True
    return call_graph


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--show-all-calls", type=bool,
                        help="Set to true to show all calls in the graph.", default=False,
                        dest="allcalls")
    args = parser.parse_args()

    call_graph = BuildCallGraph(sys.stdin, args.allcalls)
    call_graph.PrintDot()