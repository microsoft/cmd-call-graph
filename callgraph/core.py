from __future__ import print_function

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
        self.commands_counter = collections.Counter()

    def AddCommand(self, command):
        self.commands.append(command)
        self.commands_counter[command.command] += 1

    def __repr__(self):
        return "[{0} (terminating: {1}, noop: {2}, commands: {3})] {4}".format(self.number, self.terminating, self.noop, self.commands, self.text)

    def __eq__(self, other):
        return other is not None and self.number == other.number and self.text == other.text and self.terminating == other.terminating

# Connection between two nodes.
# dst is the name of the target node, kind is the type of connection,
# line_number is the line where the call/goto happens.
Connection = collections.namedtuple("Connection", ["dst", "kind", "line_number"])

# Node in the call graph.


class Node:
    def __init__(self, name):
        self.name = name
        self.connections = set()
        self.line_number = NO_LINE_NUMBER
        self.original_name = name
        self.is_exit_node = False
        self.is_last_node = False
        self.code = []
        self.loc = 0
        self.node_width = 0
        self.node_height = 0

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
        if other is None:
            return False
        return self.name < other.name


class CallGraph:
    def __init__(self, log_file=sys.stderr):
        self.nodes = {}
        self.log_file = log_file
        self.first_node = None

    def GetOrCreateNode(self, name):
        if name in self.nodes:
            return self.nodes[name]

        node = Node(name)
        self.nodes[name] = node
        return node

    def _MarkExitNodes(self):
        # A node is an exit node if:
        # 1. it contains an "exit" command with no target
        # or
        # 2. it's reached from the starting node via "goto" or
        # "nested" connections
        #    and it contains an exit command or a "goto eof" command.

        # Identify all nodes with an exit command with no targets.
        for node in self.nodes.values():
            all_commands = set(itertools.chain.from_iterable(line.commands for line in node.code))
            exit_cmd = Command("exit", "")
            if exit_cmd in all_commands:
                node.is_exit_node = True

        # Visit the call graph to find nodes satisfying condition #2.
        q = [self.first_node]
        visited = set()   # Used to avoid loops, since the call graph is not acyclic.

        while q:
            cur = q.pop()
            visited.add(cur.name)

            # Evaluate condition for marking exit node.
            if cur.is_last_node:
                cur.is_exit_node = True
            else:
                all_commands = itertools.chain.from_iterable(line.commands for line in cur.code)
                for command in all_commands:
                    if command[0] == "exit" or (command[0] == "goto" and command[1] == "eof"):
                        cur.is_exit_node = True
                        break

            for connection in cur.connections:
                if connection.dst not in self.nodes or connection.dst in visited:
                    continue
                if connection.kind == "nested" or connection.kind == "goto":
                    q.append(self.nodes[connection.dst])

    # Adds to each node information depending on the
    # contents of the code, such as connections
    # deriving from goto/call commands and
    # whether the node is terminating or not.
    def _AnnotateNode(self, node):
        print(u"Annotating node {0} (line {1})".format(node.original_name, node.line_number), file=self.log_file)
        for i in range(len(node.code)):
            line = node.code[i]
            line_number = line.number
            text = line.text

            # Tokenize the line of code, and store all elements that
            #  warrant augmenting the
            # node in a list (interesting_commands), which will then
            # be processed later.
            tokens = text.strip().lower().split()
            if not tokens:
                line.noop = True
                continue

            for i, token in enumerate(tokens):
                # Remove open/close parenthesis from the start/end of the command, to deal with inline commands
                # enclosed in parentheses.
                token = token.lstrip("(").rstrip(")")

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

    @staticmethod
    def Build(input_file, log_file=sys.stderr):
        call_graph = CallGraph._ParseSource(input_file, log_file)
        for node in call_graph.nodes.values():
            call_graph._AnnotateNode(node)

        # Prune away EOF if it is a virtual node (no line number) and
        # there are no call/nested connections to it.
        eof = call_graph.GetOrCreateNode("eof")
        all_connections = itertools.chain.from_iterable(n.connections for n in call_graph.nodes.values())
        destinations = set((c.dst, c.kind) for c in all_connections)
        if eof.line_number == NO_LINE_NUMBER and ("eof", "call") not in destinations and ("eof", "nested") not in destinations:
            print(u"Removing the eof node, since there are no call/nested connections to it and it's not a real node", file=log_file)
            del call_graph.nodes["eof"]
            for node in call_graph.nodes.values():
                eof_connections = [c for c in node.connections if c.dst == "eof"]
                print(u"Removing {} eof connections in node {}".format(len(eof_connections), node.name), file=log_file)
                for c in eof_connections:
                    node.connections.remove(c)

        # Warn the user if there are goto connections to eof
        # which will not be executed by CMD.
        if eof.line_number != NO_LINE_NUMBER and ("eof", "goto") in destinations:
            print(u"WARNING: there are goto connections to eof, but CMD will not execute that code via goto.", file=log_file)

        # Find and mark the "nested" connections.
        nodes = [n for n in call_graph.nodes.values() if n.line_number != NO_LINE_NUMBER]
        nodes_by_line_number = sorted(nodes, key=lambda x: x.line_number)
        for i in range(1, len(nodes_by_line_number)):
            cur_node = nodes_by_line_number[i]
            prev_node = nodes_by_line_number[i-1]

            # Special case: the previous node has no code or all lines are
            # comments / empty lines.
            all_noop = all(line.noop for line in prev_node.code)
            if not prev_node.code or all_noop:
                print(u"Adding nested connection between {0} and {1} because all_noop ({2}) or empty code ({3})".format(
                    prev_node.name, cur_node.name, all_noop, not prev_node.code), file=log_file)
                prev_node.AddConnection(cur_node.name, "nested")
                break

            # Heuristic for "nested" connections:
            # iterate the previous node's commands, and create a nested
            # connection only if the command that logically precedes the
            # current node does not contain a goto or an exit (which would mean
            # that the current node is not reached by "flowing" from the
            # previous node to the current node.)
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

        # Mark all exit nodes.
        last_node = max(call_graph.nodes.values(), key=lambda x: x.line_number)
        print(u"{0} is the last node, marking it as exit node.".format(last_node.name), file=log_file)
        last_node.is_last_node = True
        call_graph._MarkExitNodes()

        return call_graph

    # Creates a call graph from an input file, parsing the file in blocks and
    # creating one node for each block. Note that the nodes don't contain any
    # information that depend on the contents of the node, as this is just the
    # starting point for the processing.
    @staticmethod
    def _ParseSource(input_file, log_file=sys.stderr):
        call_graph = CallGraph(log_file)
        # Special node to signal the start of the script.
        cur_node = call_graph.GetOrCreateNode("__begin__")
        cur_node.line_number = 1
        call_graph.first_node = cur_node

        # Special node used by cmd to signal the end of the script.
        eof = call_graph.GetOrCreateNode("eof")
        eof.is_exit_node = True

        for line_number, line in enumerate(input_file, 1):
            line = line.strip()

            # Start of new block.
            if line.startswith(":") and not line.startswith("::"):
                # In the off chance that there are multiple words,
                # cmd considers the first word the label name.
                original_block_name = line[1:].split()[0].strip()

                # Since cmd is case-insensitive, let's convert block names to
                # lowercase.
                block_name = original_block_name.lower()

                print(u"Line {} defines a new block: <{}>".format(line_number, block_name), file=log_file)
                if block_name:
                    next_node = call_graph.GetOrCreateNode(block_name)
                    next_node.line_number = line_number
                    next_node.original_name = original_block_name

                    # If this node is defined on line one, remove __begin__,
                    # so we avoid having two
                    # nodes with the same line number.
                    if line_number == 1:
                        del call_graph.nodes["__begin__"]
                        call_graph.first_node = next_node

                    cur_node = next_node

            cur_node.AddCodeLine(line_number, line)

        return call_graph
