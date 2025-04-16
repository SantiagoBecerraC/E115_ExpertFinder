@echo off
setlocal enabledelayedexpansion

echo Container is running!!!

:: Set Python path
set PATH=C:\Python39;C:\Python39\Scripts;%PATH%
set PYTHONPATH=C:\app;%PYTHONPATH%

:: Verify secrets directory and file
echo Checking secrets directory...
if not exist "C:\secrets" (
    echo Error: C:\secrets directory not found!
    exit /b 1
)

dir C:\secrets || echo Directory listing failed

if not exist "C:\secrets\llm-service-account.json" (
    echo Error: Service account file not found at C:\secrets\llm-service-account.json
    echo Current directory contents:
    dir C:\secrets || echo Directory listing failed
    exit /b 1
)

echo Service account file found!

:: Get all arguments
set "args="
:loop
if "%1"=="" goto :done
set "args=%args% %1"
shift
goto :loop
:done

if "%args%"=="" (
    :: If no arguments provided, start an interactive shell
    echo Starting interactive shell...
    cmd /k
) else (
    :: If arguments provided, run them with Python
    echo Running Python command...
    python %args%
) 