import io
import os
import unittest

from callgraph.render import PrintDot
from callgraph.core import CallGraph

class RenderTest(unittest.TestCase):
    def setUp(self):
        self.devnull = open(os.devnull, "w")
    
    def tearDown(self):
        self.devnull.close()

# The code contains a double call to the same label (foo).
# If allgraph is set to False, it should count as a single call,
# and no line annotations should appear in the graph,
# while if it's set to True it should count as a double call.
class PrintOptionsGraphTest(RenderTest):
    def setUp(self):
        RenderTest.setUp(self)
        code = """
        call :foo
        call :foo
        call powershell.exe something.ps1
        call powershell.exe something.ps1
        exit
        :foo
        call powershell.exe something.ps1
        goto :%command%
        goto :eof
        """.split("\n")

        self.call_graph = CallGraph.Build(code, self.devnull)
        begin = self.call_graph.nodes["__begin__"]

        # There should only be two connections of type call in __begin__.
        self.assertEqual(2, len(begin.connections))
        kinds = set(c.kind for c in begin.connections)
        self.assertEqual(1, len(kinds))
        self.assertEqual("call", kinds.pop())

    def test_duplicate_no_allgraph(self):
        f = io.StringIO()
        PrintDot(self.call_graph, f, show_all_calls=False, log_file=self.devnull)
        dot = f.getvalue()
        self.assertEqual(1, dot.count('"__begin__" -> "foo"'), "No connection found in the dot document: " + dot)

        # Test that no connections have line number annotations,
        # since connections are de-duplicated by line.
        self.assertEqual(0, dot.count("line 2"))
        self.assertEqual(0, dot.count("line 3"))

    def test_loc(self):
        f = io.StringIO()
        PrintDot(self.call_graph, f, show_node_stats=True, log_file=self.devnull)
        dot = f.getvalue()

        # Check the number of lines of code.
        self.assertEqual(1, dot.count('5 LOC'))
        self.assertEqual(1, dot.count('6 LOC'))

    def test_external_call(self):
        f = io.StringIO()
        PrintDot(self.call_graph, f, show_node_stats=True, log_file=self.devnull)
        dot = f.getvalue()

        self.assertEqual(1, dot.count('2 external calls]'))
        self.assertEqual(1, dot.count('1 external call]'))

    def test_duplicate_allgraph(self):
        f = io.StringIO()
        PrintDot(self.call_graph, f, show_all_calls=True, log_file=self.devnull)
        dot = f.getvalue()
        self.assertEqual(2, dot.count('"__begin__" -> "foo"'))

        # Test that connections do have line number annotations.
        self.assertEqual(1, dot.count("line 2"))
        self.assertEqual(1, dot.count("line 3"))
    
    def test_hide_eof(self):
        f = io.StringIO()
        PrintDot(self.call_graph, f, log_file=self.devnull, nodes_to_hide=set(["eof"]))
        dot = f.getvalue()
        self.assertEqual(0, dot.count("eof"))
    
    def test_percent(self):
        f = io.StringIO()
        PrintDot(self.call_graph, f, log_file=self.devnull)
        dot = f.getvalue()
        self.assertEqual(1, dot.count(r"\%command\%"), dot)


# Regression test for issue #44: calls/goto in sub-expressions (nested within parentheses)
# should be represented correctly in the rendered graph
class ParenthesisLabelRenderTest(RenderTest):
    def setUp(self):
        RenderTest.setUp(self)
        # Code with goto and call statements nested in parentheses
        code = """
        if foo==bar (call :foo) ELSE (goto :bar)
        exit
        :foo
        echo "in foo"
        goto :eof
        :bar
        echo "in bar"
        goto :eof
        """.split("\n")
        
        self.call_graph = CallGraph.Build(code, self.devnull)
    
    def test_parenthesis_labels_in_rendered_graph(self):
        """Verify that calls to labels in sub-expressions are rendered with correct label names (without parentheses)"""
        f = io.StringIO()
        PrintDot(self.call_graph, f, show_all_calls=True, log_file=self.devnull)
        dot = f.getvalue()
        
        # Verify that connections point to correct labels (without trailing parenthesis)
        self.assertIn('"__begin__" -> "foo"', dot, "Connection to 'foo' should be present")
        self.assertIn('"__begin__" -> "bar"', dot, "Connection to 'bar' should be present")
        
        # Verify that incorrect labels (with parenthesis) are NOT in the graph
        self.assertNotIn('"foo)"', dot, "Label 'foo)' should not be present")
        self.assertNotIn('"bar)"', dot, "Label 'bar)' should not be present")
        self.assertNotIn('-> "foo)"', dot, "Connection to 'foo)' should not be present")
        self.assertNotIn('-> "bar)"', dot, "Connection to 'bar)' should not be present")
        
        # Verify the actual node definitions use correct names
        self.assertIn('"foo"', dot, "Node 'foo' should be defined")
        self.assertIn('"bar"', dot, "Node 'bar' should be defined")


if __name__ == "__main__":
    unittest.main()