@echo off

:x
    rem second line

    call c:\dev\cmd-call-graph\examples\a.cmd  
:y
    rem second line
    rem third line 
    rem second line
    rem third line
    call powershell.exe foo.ps1
:z
    rem second line
    rem third line
    call powershell.exe foo.ps1
    call powershell.exe foo.ps1