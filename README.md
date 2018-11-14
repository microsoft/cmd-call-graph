# cmd-call-graph
A simple tool to generate a call graph for Windows CMD (batch) files.

It takes the input file as stdin and outputs the resulting file to stdout,
outputting logs and errors to stderr.

Usage example from WSL (Windows Subsystem for Linux):

    $ python3 cmd-call-graph.py < your-file.cmd > your-file-call-graph.dot 2>log

The resulting `dot` file can be rendered with any `dot` renderer. Example with
graphviz:

    $ sudo apt install graphviz
    $ dot -Tpng your-file-call-graph.dot > your-file-call-graph.png
    $ explorer.exe your-file-call-graph.png

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
