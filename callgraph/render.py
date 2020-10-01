from __future__ import print_function

import sys

from . import core

def _Escape(input_string):
    return input_string.replace("%", r"\%")


COLORS = {
    'goto':             '"#d83b01"',  # Orange
    'nested':           '"#008575"',  # Teal
    'call':             '"#0078d4"',  # Blue
    'terminating':      '"#e6e6e6"',  # Light gray
    'external_call':    '"#850085"',  # Purple # cgreen - external calls enhancements - to another cmd/bat file
    'external_program': '"#358500"',  # Green # cgreen - external calls enhancements - to an exe ..
    'folder_start':     '"#ffec8b"',  # Light gold
    'folder_end':       '"#b8860b"'   # Dark gold
}

def PrintDot(call_graph, out_file=sys.stdout, log_file=sys.stderr, show_all_calls=True, show_node_stats=False, nodes_to_hide=None, represent_node_size=False, min_node_size=3, max_node_size=7, font_scale_factor=7):
    # Output the DOT header.
    print(u"digraph g {", file=out_file)
    
    # Output the DOT body for the initial graph nodes
    PrintDotContents(call_graph, out_file, log_file, True, False, None, False, 3, 7, 7)
  
    # Recursively look for nested command dictionaries belonging to build out the entire graph
    RecurseCmdDict(call_graph, out_file, log_file)

    # Output the DOT footer
    print(u"}", file=out_file)

def RecurseCmdDict(cg, out_file=sys.stdout, log_file=sys.stderr): 
    for k in cg.cmddict:
        gd = cg.cmddict.get(k)
        if isinstance(gd.cmddict, dict):
            PrintDotContents(gd, out_file, log_file, True, False, None, False, 3, 7, 7)
            RecurseCmdDict(gd, out_file, log_file)

def PrintDotContents(call_graph, out_file=sys.stdout, log_file=sys.stderr, show_all_calls=True, show_node_stats=False, nodes_to_hide=None, represent_node_size=False, min_node_size=3, max_node_size=7, font_scale_factor=7):
    if min_node_size > max_node_size:
        min_node_size, max_node_size = max_node_size, min_node_size

    if max_node_size < 1:
        max_node_size = min_node_size = 1

    if min_node_size < 1:
        min_node_size = 1

    max_node_loc = 0

    for node in sorted(call_graph.nodes.values()):
        if nodes_to_hide and (node.name in nodes_to_hide):
            continue
        
        if node.loc > max_node_loc:
            max_node_loc = node.loc

    for node in sorted(call_graph.nodes.values()):
        if nodes_to_hide and (node.name in nodes_to_hide):
            print(u"Skipping node {0}".format(node.name), file=log_file)
            continue

        name = node.name
        pretty_name = name
 
        # cgreen - handling reference from external called script 
        #  to the begin node of that script contents
        if "__begin__" in name: 
            pretty_name = "__begin__"
        elif node.original_name != "":
            pretty_name = node.original_name  

        print(u"Processing node {0} (using name: {1})".format(node.name, pretty_name), file=log_file)

        attributes = []
        label_lines = ["<b>{}</b>".format(pretty_name)]

        if node.line_number < 0:
            attributes.append("style=filled,fillcolor={},shape=folder,margin=.3".format(COLORS["folder_start"])) 
        elif node.line_number > 0:
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

        # Minimum width and height of each node proportional to the number of lines contained (self.loc)
        if represent_node_size:
            nw = round((node.loc / max_node_loc) * (max_node_size - min_node_size) + min_node_size, 1) 
            nh = round(nw / 2, 1)
            attributes.append("width={}".format(nw))
            attributes.append("height={}".format(nh))

            # Font size set to be 7 times node width
            attributes.append("fontsize={}".format(nw * font_scale_factor))

        if attributes:
            print(u"\"{}\" [{}]".format(name, ",".join(attributes)), file=out_file)

        # De-duplicate connections by line number if show_all_calls is set to
        # False.
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
            if c.kind == "external_program":
                # represent external program a grey folder shape
                print(u"\"{}\" [style=filled,shape=folder]".format(dst_escaped_name), file=out_file)
            elif (c.kind == "external_call") and (c.line_number > 0): 
                # any other external cmd files at this point haven't been parsed (due to max call depth)
                #  so just render as a dark folder shape
                #  & there was a bug here where rendering the name without the label attribute was
                #   causing the name in the shape to appear to need to be escaped
                print(u"\"{0}\" [style=filled,shape=folder,margin=.3,fillcolor={1},label=<<b>{0}</b><br/>End Parsing>]".format(dst_escaped_name, COLORS["folder_end"]), file=out_file)

            print(u"\"{}\" -> \"{}\" [label={},color={}]".format(src_escaped_name, dst_escaped_name, label, COLORS[c.kind]), file=out_file)

