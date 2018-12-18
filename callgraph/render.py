from __future__ import print_function

import sys

from . import core

def _Escape(input_string):
    return input_string.replace("%", r"\%")


COLORS = {
    'goto':         '"#d83b01"', # Orange
    'nested':       '"#008575"', # Teal
    'call':         '"#0078d4"', # Blue
    'terminating':  '"#e6e6e6"', # Light gray
}

def PrintDot(call_graph, out_file=sys.stdout, log_file=sys.stderr, show_all_calls=True, show_node_stats=False, nodes_to_hide=None):
    # Output the DOT code.
    print(u"digraph g {", file=out_file)

    for node in sorted(call_graph.nodes.values()):
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
            
        if node.is_exit_node:
            attributes.append("color={}".format(COLORS["terminating"]))
            attributes.append("style=filled")
            label_lines.append("<sub>[terminating]</sub>")

        attributes.append("label=<{}>".format("<br/>".join(label_lines)))

        if attributes:
            print(u"\"{}\" [{}]".format(name, ",".join(attributes)), file=out_file)

        # De-duplicate connections by line number if show_all_calls is set to False.
        connections = node.connections
        if not show_all_calls:
            connections = list(set(core.Connection(c.dst, c.kind, core.NO_LINE_NUMBER) for c in connections))
        
        for c in sorted(connections):
            # Remove EOF connections if necessary.
            if nodes_to_hide and (c.dst in nodes_to_hide):
                print(u"Skipping connection to node {0}".format(c.dst), file=log_file)
                continue
            label = "\" {}\"".format(c.kind)
            if c.line_number != core.NO_LINE_NUMBER:
                label = "<<b>{}</b><br />(line {})>".format(c.kind, c.line_number)
            src_escaped_name = _Escape(name)
            dst_escaped_name = _Escape(c.dst)
            print(u"\"{}\" -> \"{}\" [label={},color={}]".format(src_escaped_name, dst_escaped_name, label, COLORS[c.kind]), file=out_file)

    print(u"}", file=out_file)
