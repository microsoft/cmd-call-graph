@echo off

:a
    rem second line

:b
    rem second line
    rem third line
    call c:\dev\cmd-call-graph\examples\foo.cmd
    rem second line
    rem third line
    call powershell.exe foo.ps1
:c
    rem second line
    rem third line
    call powershell.exe foo.ps1
    call powershell.exe foo.ps1