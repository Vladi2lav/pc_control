@echo off
setlocal

if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe init.py
) else (
    python init.py
)
