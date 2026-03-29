@echo off
echo Running tests...
pytest tests/ -v
if errorlevel 1 (
    echo Tests failed!
    pause
    exit /b 1
) else (
    echo All tests passed!
    pause
)
