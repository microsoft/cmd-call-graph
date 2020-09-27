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
    call c:\dev\cmd-call-graph\examples\x.cmd 
    call c:\dev\cmd-call-graph\examples\hello.cmd  
    goto :bar
