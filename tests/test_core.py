import io
import os
import unittest

from callgraph.core import CallGraph, CodeLine, Command


class CodeLineTest(unittest.TestCase):
    def test_command_counters(self):
        line = CodeLine(0, "foo")
        line.AddCommand(Command("goto", ""))
        line.AddCommand(Command("goto", ""))
        line.AddCommand(Command("external_call", ""))

        self.assertEqual(2, line.commands_counter["goto"])
        self.assertEqual(1, line.commands_counter["external_call"])

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
        call_graph = CallGraph._ParseSource(code, self.devnull)
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
        call_graph = CallGraph._ParseSource(code, self.devnull)
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
        @:: do something else
        rem do something
        @rem do something else
        :foo
        exit
        """.split("\n")
        call_graph = CallGraph._ParseSource(code, self.devnull)
        self.assertEqual(3, len(call_graph.nodes))
        self.assertIn("__begin__", call_graph.nodes.keys())
        self.assertIn("foo", call_graph.nodes.keys())
        
        begin_node = call_graph.nodes["__begin__"]
        self.assertEqual(0, len(begin_node.connections))
        self.assertEqual(1, begin_node.line_number)

        call_graph._AnnotateNode(begin_node)
        for line in begin_node.code:
            self.assertTrue(line.noop)

        foo_node = call_graph.nodes["foo"]
        self.assertEqual(0, len(foo_node.connections))
        self.assertEqual(6, foo_node.line_number)

class BasicBuildTests(CallGraphTest):
    def test_empty(self):
        call_graph = CallGraph.Build("", self.devnull)
        self.assertEqual(1, len(call_graph.nodes))
        self.assertIn("__begin__", call_graph.nodes.keys())

    def test_eof_defined_once(self):
        call_graph = CallGraph.Build([":eof"], self.devnull)
        self.assertEqual(1, len(call_graph.nodes))
        self.assertIn("eof", call_graph.nodes.keys())
    
    def test_simple_call(self):
        code = """
        call :foo
        exit 
        :foo
        goto :eof
        """.split("\n")

        call_graph = CallGraph.Build(code, self.devnull)
        self.assertEqual(2, len(call_graph.nodes))
        self.assertIn("__begin__", call_graph.nodes.keys())
        self.assertIn("foo", call_graph.nodes.keys())

        begin = call_graph.nodes["__begin__"]
        self.assertTrue(begin.is_exit_node)
        self.assertEqual(1, len(begin.connections))
        self.assertFalse(begin.is_last_node)

        connection = begin.connections.pop()
        self.assertEqual("call", connection.kind)
        self.assertEqual("foo", connection.dst)

        foo = call_graph.nodes["foo"]
        self.assertTrue(foo.is_last_node)

    def test_handle_nonexisting_target(self):
        code = """
        goto :nonexisting
        """.split("\n")
        call_graph = CallGraph.Build(code, self.devnull)
        self.assertEqual(1, len(call_graph.nodes))
        self.assertIn("__begin__", call_graph.nodes.keys())
        begin_node = call_graph.nodes["__begin__"]
        self.assertEqual(1, len(begin_node.connections))
        self.assertEqual("nonexisting", begin_node.connections.pop().dst)


    def test_exit_terminating(self):
        code = """
        :foo
        exit
        """.split("\n")

        call_graph = CallGraph.Build(code, self.devnull)
        self.assertEqual(2, len(call_graph.nodes))
        self.assertIn("foo", call_graph.nodes.keys())

        foo_node = call_graph.nodes["foo"]
        begin_node = call_graph.nodes["__begin__"]

        self.assertTrue(foo_node.is_exit_node)
        self.assertFalse(begin_node.is_exit_node)

        self.assertTrue(foo_node.is_last_node)
        self.assertFalse(begin_node.is_last_node)

    def test_simple_terminating(self):
        code = """
        goto :foo
        :foo
        something
        something
        """.split("\n")

        call_graph = CallGraph.Build(code, self.devnull)
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
        call_graph = CallGraph.Build(code, self.devnull)
        self.assertIn("bar", call_graph.nodes.keys())
        bar_node = call_graph.nodes["bar"]
        self.assertFalse(bar_node.is_exit_node)

    def test_last_node_goto_eof_terminating(self):
        code = """
        :foo
        goto :eof
        """.split("\n")
        call_graph = CallGraph.Build(code, self.devnull)
        self.assertIn("foo", call_graph.nodes.keys())
        foo_node = call_graph.nodes["foo"]
        self.assertTrue(foo_node.is_exit_node)

    def test_simple_nested(self):
        code = """
        something
        :bar
        something
        """.split("\n")
        call_graph = CallGraph.Build(code, self.devnull)
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
        call_graph = CallGraph.Build(code, self.devnull)
        begin_node = call_graph.nodes["__begin__"]
        self.assertEqual(0, len(begin_node.connections))

    def test_code_in_nodes(self):
        code = """
        call :foo
        exit 
        :foo
        goto :eof
        """.split("\n")
        call_graph = CallGraph.Build(code, self.devnull)
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
        call_graph = CallGraph.Build(code, self.devnull)
        begin = call_graph.nodes["__begin__"]

        self.assertEqual(1, len(begin.connections), begin.code)
        self.assertEqual("nested", begin.connections.pop().kind)

    def test_empty_node_nested(self):
        code = """:foo
        :bar
        """.split("\n")
        call_graph = CallGraph.Build(code, self.devnull)
        begin = call_graph.nodes["foo"]

        self.assertEqual(1, len(begin.connections))
        self.assertEqual("nested", begin.connections.pop().kind)
        self.assertFalse(begin.is_exit_node)
        self.assertFalse(begin.is_last_node)

        bar = call_graph.nodes["bar"]
        self.assertTrue(bar.is_exit_node)
        self.assertTrue(bar.is_last_node)

        # There should be no __begin__ node, only foo and bar.
        self.assertEqual(2, len(call_graph.nodes))
    
    def test_call_nested_eof(self):
        code = """
        echo "yo"
        call :eof
        :eof
        echo "eof"
        """.split("\n")
        call_graph = CallGraph.Build(code, self.devnull)
        self.assertEqual(2, len(call_graph.nodes))

        begin = call_graph.nodes["__begin__"]
        self.assertEqual(2, len(begin.connections))
        self.assertFalse(begin.is_exit_node)
        self.assertFalse(begin.is_last_node)

        eof = call_graph.nodes["eof"]
        self.assertTrue(eof.is_exit_node)
        self.assertTrue(eof.is_last_node)
    
    def test_multiple_exit_nodes(self):
        code = """
        exit
        :foo
        exit
        """.split("\n")
        call_graph = CallGraph.Build(code, self.devnull)
        self.assertEqual(2, len(call_graph.nodes))

        begin = call_graph.nodes["__begin__"]
        self.assertTrue(begin.is_exit_node)
        self.assertFalse(begin.is_last_node)

        foo = call_graph.nodes["foo"]
        self.assertTrue(foo.is_exit_node)
        self.assertTrue(foo.is_last_node)
    
    def test_no_nested_with_inline_if(self):
        code = """
        call :Filenotempty foo
        echo %ERRORLEVEL%
        exit
        :filenotempty 
        If %~z1 EQU 0 (Exit /B 1) Else (Exit /B 0)
        :unused
        echo Will never run.
        """.split("\n")
        call_graph = CallGraph.Build(code, self.devnull)
        self.assertEqual(3, len(call_graph.nodes))

        file_not_empty = call_graph.nodes["filenotempty"]
        self.assertEqual(0, len(file_not_empty.connections), file_not_empty.code)
    

if __name__ == "__main__":
    unittest.main()