@echo off
echo "file a"
goto :awork

:awork
    call c:\dev\cmd-call-graph\examples\b.cmd 
 
 pause
