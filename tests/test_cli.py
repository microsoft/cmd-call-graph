import io
import os
import sys
import unittest
from unittest.mock import patch

from callgraph.callgraph import main
from callgraph import __version__


class CLITest(unittest.TestCase):
    """Tests for command-line interface functionality."""

    def test_version_flag(self):
        """Test that --version flag outputs the correct version."""
        with patch('sys.argv', ['cmd-call-graph', '--version']):
            with patch('sys.stdout', new=io.StringIO()) as mock_stdout:
                with self.assertRaises(SystemExit) as cm:
                    # argparse exits with code 0 when --version is used
                    main()
                
                # SystemExit with code 0 is expected for --version
                self.assertEqual(cm.exception.code, 0)
                
                # Verify the output contains the version from __version__
                output = mock_stdout.getvalue()
                self.assertIn(__version__, output, 
                             f"Version output should contain {__version__}, got: {output}")

    def test_version_in_module(self):
        """Test that __version__ is defined and has correct format."""
        self.assertIsNotNone(__version__)
        self.assertIsInstance(__version__, str)
        # Basic version format check (e.g., "1.2.1")
        parts = __version__.split('.')
        self.assertGreaterEqual(len(parts), 2)
        for part in parts:
            self.assertTrue(part.isdigit(), f"Version part '{part}' should be numeric")


if __name__ == '__main__':
    unittest.main()
