import io
import os
import unittest

from callgraph import callgraph
CodeLine = callgraph.CodeLine

class CallGraphTest(unittest.TestCase):
    def setUp(self):
        self.devnull = open(os.devnull, "w")
    
    def tearDown(self):
        self.devnull.close()

class ParseSourceTests(CallGraphTest):
    def test_one_block(self):
        code = """
        do something
        do something else
        exit
        """.split("\n")
        call_graph = callgraph.CallGraph._ParseSource(code, self.devnull)
        self.assertEqual(2, len(call_graph.nodes))
        self.assertIn("__begin__", call_graph.nodes.keys())
        
        begin_node = call_graph.nodes["__begin__"]
        self.assertEqual(0, len(begin_node.connections))
        self.assertEqual(1, begin_node.line_number)

    def test_two_blocks(self):
        code = """
        do something
        :foo
        exit
        """.split("\n")
        call_graph = callgraph.CallGraph._ParseSource(code, self.devnull)
        self.assertEqual(3, len(call_graph.nodes))
        self.assertIn("__begin__", call_graph.nodes.keys())
        self.assertIn("foo", call_graph.nodes.keys())
        
        begin_node = call_graph.nodes["__begin__"]
        self.assertEqual(0, len(begin_node.connections))
        self.assertEqual(1, begin_node.line_number)

        foo_node = call_graph.nodes["foo"]
        self.assertEqual(0, len(foo_node.connections))
        self.assertEqual(3, foo_node.line_number)

    def test_comment_ignore(self):
        code = """
        ::do something
        :foo
        exit
        """.split("\n")
        call_graph = callgraph.CallGraph._ParseSource(code, self.devnull)
        self.assertEqual(3, len(call_graph.nodes))
        self.assertIn("__begin__", call_graph.nodes.keys())
        self.assertIn("foo", call_graph.nodes.keys())
        
        begin_node = call_graph.nodes["__begin__"]
        self.assertEqual(0, len(begin_node.connections))
        self.assertEqual(1, begin_node.line_number)

        foo_node = call_graph.nodes["foo"]
        self.assertEqual(0, len(foo_node.connections))
        self.assertEqual(3, foo_node.line_number)

class BasicBuildTests(CallGraphTest):
    def test_empty(self):
        call_graph = callgraph.CallGraph.Build("", self.devnull)
        self.assertEqual(1, len(call_graph.nodes))
        self.assertIn("__begin__", call_graph.nodes.keys())

    def test_eof_defined_once(self):
        call_graph = callgraph.CallGraph.Build([":eof"], self.devnull)
        self.assertEqual(1, len(call_graph.nodes))
        self.assertIn("eof", call_graph.nodes.keys())
    
    def test_simple_call(self):
        code = """
        call :foo
        exit 
        :foo
        goto :eof
        """.split("\n")

        call_graph = callgraph.CallGraph.Build(code, self.devnull)
        self.assertEqual(3, len(call_graph.nodes))
        self.assertIn("__begin__", call_graph.nodes.keys())
        self.assertIn("foo", call_graph.nodes.keys())
        self.assertIn("eof", call_graph.nodes.keys())

        begin = call_graph.nodes["__begin__"]
        self.assertTrue(begin.is_exit_node)
        self.assertEqual(1, len(begin.connections))

        connection = begin.connections.pop()
        self.assertEqual("call", connection.kind)
        self.assertEqual("foo", connection.dst.name)

    def test_exit_terminating(self):
        code = """
        :foo
        exit
        """.split("\n")

        call_graph = callgraph.CallGraph.Build(code, self.devnull)
        self.assertEqual(2, len(call_graph.nodes))
        self.assertIn("foo", call_graph.nodes.keys())

        foo_node = call_graph.nodes["foo"]
        begin_node = call_graph.nodes["__begin__"]

        self.assertTrue(foo_node.is_exit_node)
        self.assertFalse(begin_node.is_exit_node)

    def test_simple_terminating(self):
        code = """
        goto :foo
        :foo
        something
        something
        """.split("\n")

        call_graph = callgraph.CallGraph.Build(code, self.devnull)
        self.assertEqual(2, len(call_graph.nodes))
        self.assertIn("foo", call_graph.nodes.keys())

        foo_node = call_graph.nodes["foo"]
        begin_node = call_graph.nodes["__begin__"]

        self.assertTrue(foo_node.is_exit_node)
        self.assertFalse(begin_node.is_exit_node)

    def test_last_node_goto_not_terminating(self):
        code = """
        :foo
        goto :eof
        :bar
        goto :foo
        """.split("\n")
        call_graph = callgraph.CallGraph.Build(code, self.devnull)
        self.assertIn("bar", call_graph.nodes.keys())
        bar_node = call_graph.nodes["bar"]
        self.assertFalse(bar_node.is_exit_node)

    def test_last_node_goto_eof_terminating(self):
        code = """
        :foo
        goto :eof
        """.split("\n")
        call_graph = callgraph.CallGraph.Build(code, self.devnull)
        self.assertIn("foo", call_graph.nodes.keys())
        foo_node = call_graph.nodes["foo"]
        self.assertTrue(foo_node.is_exit_node)



    def test_simple_nested(self):
        code = """
        something
        :bar
        something
        """.split("\n")
        call_graph = callgraph.CallGraph.Build(code, self.devnull)
        self.assertEqual(2, len(call_graph.nodes))
        self.assertIn("bar", call_graph.nodes.keys())

        begin_node = call_graph.nodes["__begin__"]
        self.assertEqual(1, len(begin_node.connections))
        connection = begin_node.connections.pop()

        self.assertEqual("nested", connection.kind)

    def test_block_end_goto_no_nested(self):
        code = """
        goto :eof
        :foo
        """.split("\n")
        call_graph = callgraph.CallGraph.Build(code, self.devnull)
        begin_node = call_graph.nodes["__begin__"]
        self.assertEqual(1, len(begin_node.connections))
        connection = begin_node.connections.pop()
        self.assertEqual("goto", connection.kind)

    def test_code_in_nodes(self):
        code = """
        call :foo
        exit 
        :foo
        goto :eof
        """.split("\n")
        call_graph = callgraph.CallGraph.Build(code, self.devnull)
        begin = call_graph.nodes["__begin__"]
        foo = call_graph.nodes["foo"]
        self.assertEqual(begin.code, [
            CodeLine(1, ""), 
            CodeLine(2, "call :foo"),
            CodeLine(3, "exit", True),
        ])
        self.assertEqual(foo.code, [
            CodeLine(4, ":foo"),
            CodeLine(5, "goto :eof", True),
            CodeLine(6, ""),
        ])
        self.assertEqual(True, foo.code[2].noop)

    def test_empty_lines_nested(self):
        code = """
        :foo
        """.split("\n")
        call_graph = callgraph.CallGraph.Build(code, self.devnull)
        begin = call_graph.nodes["__begin__"]

        self.assertEqual(1, len(begin.connections), begin.code)
        self.assertEqual("nested", begin.connections.pop().kind)

    def test_empty_node_nested(self):
        code = """:foo
        :bar
        """.split("\n")
        call_graph = callgraph.CallGraph.Build(code, self.devnull)
        begin = call_graph.nodes["foo"]

        self.assertEqual(1, len(begin.connections))
        self.assertEqual("nested", begin.connections.pop().kind)
    
# The code contains a double call to the same label (foo).
# If allgraph is set to False, it should count as a single call,
# and no line annotations should appear in the graph,
# while if it's set to True it should count as a double call.
class PrintOptionsGraphTest(CallGraphTest):
    def setUp(self):
        CallGraphTest.setUp(self)
        code ="""
        call :foo
        call :foo
        call powershell.exe something.ps1
        call powershell.exe something.ps1
        exit
        :foo
        call powershell.exe something.ps1
        goto :eof
        """.split("\n")

        self.call_graph = callgraph.CallGraph.Build(code, self.devnull)
        begin = self.call_graph.nodes["__begin__"]

        # There should only be two connections of type call.
        self.assertEqual(2, len(begin.connections))
        kinds = set(c.kind for c in begin.connections)
        self.assertEqual(1, len(kinds))
        self.assertEqual("call", kinds.pop())

    def test_duplicate_no_allgraph(self):
        f = io.StringIO()
        self.call_graph.PrintDot(f, show_all_calls=False)
        dot = f.getvalue()
        self.assertEqual(1, dot.count('"__begin__" -> "foo"'), "No connection found in the dot document: " + dot)

        # Test that no connections have line number annotations,
        # since connections are de-duplicated by line.
        self.assertEqual(0, dot.count("line 2"))
        self.assertEqual(0, dot.count("line 3"))

    def test_loc(self):
        f = io.StringIO()
        self.call_graph.PrintDot(f, show_node_stats=True)
        dot = f.getvalue()

        # Check the number of lines of code.
        self.assertEqual(1, dot.count('4 LOC'))
        self.assertEqual(1, dot.count('6 LOC'))

    def test_external_call(self):
        f = io.StringIO()
        self.call_graph.PrintDot(f, show_node_stats=True)
        dot = f.getvalue()

        self.assertEqual(1, dot.count('2 external calls]'))
        self.assertEqual(1, dot.count('1 external call]'))

    def test_duplicate_allgraph(self):
        f = io.StringIO()
        self.call_graph.PrintDot(f, show_all_calls=True)
        dot = f.getvalue()
        self.assertEqual(2, dot.count('"__begin__" -> "foo"'))

        # Test that connections do have line number annotations.
        self.assertEqual(1, dot.count("line 2"))
        self.assertEqual(1, dot.count("line 3"))
    
    def test_hide_eof(self):
        f = io.StringIO()
        self.call_graph.PrintDot(f, log_file=self.devnull, nodes_to_hide=set(["eof"]))
        dot = f.getvalue()
        self.assertEqual(0, dot.count("eof"))

if __name__ == "__main__":
    unittest.main()