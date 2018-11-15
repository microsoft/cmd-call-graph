import os
import unittest

from callgraph import callgraph

class BasicBuildTests(unittest.TestCase):
    def setUp(self):
        self.devnull = open(os.devnull, "w")
    
    def tearDown(self):
        self.devnull.close()

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
    
if __name__ == "__main__":
    unittest.main()