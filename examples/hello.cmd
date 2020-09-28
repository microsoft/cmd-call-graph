@echo off
dir
echo "starting.."
goto :hello

:hi
    echo "hi"
    goto :goodbye

:hello
    echo "hello"
    call c:\dev\cmd-call-graph\examples\a.cmd  
    goto :hi


:goodbye
    echo "goodbye"

pause