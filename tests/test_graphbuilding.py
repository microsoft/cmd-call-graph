import os
import unittest

from callgraph import callgraph
CodeLine = callgraph.CodeLine

class CallGraphTest(unittest.TestCase):
    def setUp(self):
        self.devnull = open(os.devnull, "w")
    
    def tearDown(self):
        self.devnull.close()

class BasicBuildTests(CallGraphTest):
    def test_empty(self):
        call_graph = callgraph.BuildCallGraph("", False, self.devnull)
        self.assertEqual(1, len(call_graph.nodes))
        self.assertIn("__begin__", call_graph.nodes.keys())
    
    def test_simple_call(self):
        code = """
        call :foo
        exit 
        :foo
        goto :eof
        """.split("\n")

        call_graph = callgraph.BuildCallGraph(code, False, self.devnull)
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

    def test_simple_terminating(self):
        code = """
        goto :foo
        :foo
        something
        something
        """.split("\n")

        call_graph = callgraph.BuildCallGraph(code, False, self.devnull)
        self.assertEqual(2, len(call_graph.nodes))
        self.assertIn("foo", call_graph.nodes.keys())

        foo_node = call_graph.nodes["foo"]
        begin_node = call_graph.nodes["__begin__"]

        self.assertTrue(foo_node.is_exit_node)
        self.assertFalse(begin_node.is_exit_node)

    def test_code_in_nodes(self):
        code = """
        call :foo
        exit 
        :foo
        goto :eof
        """.split("\n")
        call_graph = callgraph.BuildCallGraph(code, False, self.devnull)
        begin = call_graph.nodes["__begin__"]
        foo = call_graph.nodes["foo"]
        self.assertEqual(begin.code, [
            CodeLine(1, ""), 
            CodeLine(2, "call :foo"),
            CodeLine(3, "exit"),
        ])
        self.assertEqual(foo.code, [
            CodeLine(4, ":foo"),
            CodeLine(5, "goto :eof"),
            CodeLine(6, ""),
        ])
    
class AllGraphTest(CallGraphTest):
    def setUp(self):
        CallGraphTest.setUp(self)
        # Code contains a double call to the same label.
        # If allgraph is set to False, it should count as a single call,
        # while if it's set to True it should count as a double call.
        self.code ="""
        call :foo
        call :foo
        exit
        :foo
        goto :eof
        """.split("\n")

    def test_duplicate_no_allgraph(self):
        call_graph = callgraph.BuildCallGraph(self.code, False, self.devnull)
        begin = call_graph.nodes["__begin__"]
        self.assertEqual(1, len(begin.connections))

    def test_duplicate_allgraph(self):
        call_graph = callgraph.BuildCallGraph(self.code, True, self.devnull)
        begin = call_graph.nodes["__begin__"]
        self.assertEqual(2, len(begin.connections))

if __name__ == "__main__":
    unittest.main()