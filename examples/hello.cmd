@echo off
dir
echo "starting.."
goto :hello

:hi
    echo "hi"
    goto :baz
    goto :goodbye

:hello
    echo "hello"
    call c:\dev\cmd-call-graph\examples\loc.cmd  
    goto :hi

:baz
    echo "in baz"

:goodbye
    echo "goodbye"

pause