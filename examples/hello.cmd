@echo off
dir
echo "starting.."
goto :hello

:hi
    echo "hi"
    goto :goodbye

:hello
    echo "hello"
    call c:\dev\cmd-call-graph\examples\loc.cmd  
    goto :hi


:goodbye
    echo "goodbye"

pause