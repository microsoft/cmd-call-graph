@echo off
echo "loc.."
goto :one
:one
    dir
     
:two
    rem second line
:three
    rem second line
    rem third line
:four
    rem second line
    rem third line
    call powershell.exe foo.ps1
:five
    rem second line
    rem third line
    call powershell.exe foo.ps1
    call powershell.exe foo.ps1