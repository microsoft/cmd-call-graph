@echo off
dir
echo "starting.."
goto :hello

:hi
    echo "hi"
    goto :goodbye

:hello
    echo "hello"
    goto :hi


:goodbye
    echo "goodbye"

pause