# cmd-call-graph

[![Build Status](https://api.travis-ci.org/Microsoft/cmd-call-graph.svg?branch=master)](http://travis-ci.org/Microsoft/cmd-call-graph)
[![PyPI](https://img.shields.io/pypi/v/cmd-call-graph.svg)](https://pypi.org/project/cmd-call-graph/)


A simple tool to generate a call graph for calls within Windows CMD (batch) files.

The tool is available on PyPI: https://pypi.org/project/cmd-call-graph/

It takes the input file as stdin and outputs the resulting file to stdout,
outputting logs and errors to stderr.

## Usage Examples

Usage example for Ubuntu Linux and WSL (Windows Subsystem for Linux), assumes
Python and `pip` are installed:

```bash
    $ pip install cmd-call-graph
    $ cmd-call-graph < your-file.cmd > your-file-call-graph.dot 2>log
```

The resulting `dot` file can be rendered with any `dot` renderer. Example with
graphviz (`VIEWER` could be `explorer.exe` under Windows:

```bash
    $ sudo apt install graphviz
    $ dot -Tpng your-file-call-graph.dot > your-file-call-graph.png
    $ $VIEWER your-file-call-graph.png
```

Example with PowerShell:

```powershell
    PS C:\> choco install graphviz python3 pip
    PS C:\> cmd-call-graph.exe -i your-file.cmd -o your-file-call-graph.dot
    PS C:\> dot.exe -Tpng your-file-call-graph.dot
    PS C:\> explorer.exe your-file-call-graph.dot.png
```

## Output Examples

Here is an example CMD script:

    @echo off
    call :foo
    goto :eof
    :bar
        echo "in bar"
        call :baz
        call :baz
    :baz
        echo "in baz"
    :foo
        echo "In foo"
        goto :bar

This script would generate the following graph:

![call graph](https://github.com/Microsoft/cmd-call-graph/raw/master/examples/example1-noshowall.png)

If the `--show-all-calls` option is enabled, then the following graph would be generated:

![call graph showall](https://github.com/Microsoft/cmd-call-graph/raw/master/examples/example1.png)

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

## Legend for Output Graphs

The graphs are self-explanatory: all information is codified with descriptive labels, and there is no
information conveyed only with color or other types of non-text graphical hint.

Colors are used to make the graph easier to follow, but no information is conveyed only with color.

Here is what each color means in the graph:

 * Orange: `goto` connection;
 * Blue: `call` connection;
 * Greeen: `nested` connection;
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
Run unit tests from the project root by running:

    python -m unittest discover
