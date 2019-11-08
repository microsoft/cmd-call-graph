# cmd-call-graph

[![Build Status](https://dev.azure.com/cmd-call-graph/cmd-call-graph/_apis/build/status/Microsoft.cmd-call-graph?branchName=master)](https://dev.azure.com/cmd-call-graph/cmd-call-graph/_build/latest?definitionId=1?branchName=master)
[![PyPI](https://img.shields.io/pypi/v/cmd-call-graph.svg)](https://pypi.org/project/cmd-call-graph/)

A simple tool to generate a call graph for calls within Windows CMD (batch) files.

The tool is available on PyPI: https://pypi.org/project/cmd-call-graph/

By default, it takes the input file as stdin and outputs the resulting file
to stdout, outputting logs and errors to stderr.

## Output Examples

Given the following CMD script:

```
@echo off
call :foo
goto :eof
:bar
    echo "in bar"
    call :baz
    call :baz
:baz
    echo "in baz"
    call powershell.exe Write-Host "Hello World from PowerShell"

:foo
    echo "In foo"
    goto :bar
```

This script would generate the following graph:

![call graph](https://github.com/Microsoft/cmd-call-graph/raw/master/examples/example1-nodestats.png)

If the `--hide-node-stats` option is enabled, then the following graph would be generated:

![call graph showall](https://github.com/Microsoft/cmd-call-graph/raw/master/examples/example1.png)

## Invocation Examples

Invocation example for Ubuntu Linux and WSL (Windows Subsystem for Linux), assumes
Python and `pip` are installed:

```bash
$ pip install cmd-call-graph
$ cmd-call-graph < your-file.cmd > your-file-call-graph.dot 2>log
```

The resulting `dot` file can be rendered with any `dot` renderer. Example with
graphviz (`VIEWER` could be `explorer.exe` under Windows):

```bash
$ sudo apt install graphviz
$ dot -Tpng your-file-call-graph.dot > your-file-call-graph.png
$ $VIEWER your-file-call-graph.png
```

Example with PowerShell:

```powershell
PS C:\> choco install graphviz python3 pip
PS C:\> cmd-call-graph.exe -i your-file.cmd -o your-file-call-graph.dot
PS C:\> dot.exe -Tpng your-file-call-graph.dot -O
PS C:\> explorer.exe your-file-call-graph.dot.png
```

## Types of entities represented

The script analyzes CMD scripts, and represents each block of text under a given label as a *node* in
the call graph.

### Node properties

Each node always contains the line number where it starts, except if the node is never defined in the code,
which can happen in case of programming errors, dynamic node names (e.g., `%command%`) and the `eof` pseudo-node.

If a node causes the program to exit, it is marked as `terminating`.

If `--show-node-stats` is set, extra stats about each node are displayed, if present:

* number of lines of code (`LOC`);
* number of external calls.

### Special nodes

There are 2 special nodes:

* `_begin_` is a pseudo-node inserted at the start of each call graph, which represents the start of the
  script, which is by definition without a label;
* `eof`, which may or may not be a pseudo-node. In CMD, `eof` is a special node that is used as target
  of `goto` to indicate that the current "subroutine" should terminate, or the whole program should
  terminate if the call stack is empty.

The `eof` node is automatically removed if it's a pseudo-node and it's not reached via `call` or `nested`
connections.

The `_begin_` pseudo-node is removed if there is another node starting at line 1.

### Types of connections

 * `goto`: if an edge of type `goto` goes from `A` to `B`, it means that in the code within the label `A`
   there is an instruction in the form `goto :B`.
 * `call`: if an edge of type `call` goes from `A` to `B`, it means that in the code within the label `A`
   there is an instruction in the form `call :B`.
 * `nested`: if an edge of type `nested` goes from `A` to `B`, it means that in the code within the label `A`
   ends directly where `B` starts, and there is no `goto` or `exit` statement at the end of `A` which would
   prevent the execution from not going into `B` as `A` ends.

Example of a `nested` connection:

```
A:
  echo "foo"
  echo "bar"
B:
  echo "baz"
```

The above code would lead to a `nested` connection between `A` and `B`.

## Command-line options

The input file needs to be passed as an argument.

* `--simplify-calls`: create one edge for each type of connection instead of creating one for each
  individual `call`/`goto` (which is the default). Leads to a simpler but less accurate graph;
* `--hide-node-stats`: removes from each node additional information about itself (i.e., number
  of lines of code, number of external calls);
* `--nodes-to-hide`: hides the list of nodes passed as a space-separated list after this parameter.
* `-v` or `--verbose`: enable debug output, which will be sent to the log file;
* `-l` or `--log-file`: name of the log file. If not specified, the standard error file is used;
* `-o` or `--output`: name of the output file. If not specified, the standard output file is used.

## Legend for Output Graphs

The graphs are self-explanatory: all information is codified with descriptive labels, and there is no
information conveyed only with color or other types of non-text graphical hint.

Colors are used to make the graph easier to follow, but no information is conveyed only with color.

Here is what each color means in the graph:

 * Orange: `goto` connection;
 * Blue: `call` connection;
 * Teal: `nested` connection;
 * Light gray: background for terminating nodes

## Why?
Sometimes legacy code bases may contain old CMD files. This tool allows to
generate a visual representation of the internal calls within the script.

## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.microsoft.com.

When you submit a pull request, a CLA-bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., label, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Unit tests
Run unit tests from the project root either with the built-in `unittest` module:

    python -m unittest discover

Or by using `pytests`, which can produce reports both for unit test success and for code coverage, by
using the following invocation:

    pip install pytest
    pip install pytest-cov
    pytest tests --doctest-modules --junitxml=junit/test-results.xml --cov=callgraph --cov-report=xml --cov-report=html
