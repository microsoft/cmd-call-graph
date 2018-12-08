@echo off
call :foo
goto :eof
:bar
    echo "in bar"
    call :baz
    call :baz
:baz
    echo "in baz"

:foo
    echo "In foo"
    goto :bar
